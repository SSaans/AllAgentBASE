"""Exercise installed plugins with real AstrBot components and isolated events.
No QQ messages, providers, or running instance are contacted.
"""

import argparse
import asyncio
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

parser = argparse.ArgumentParser()
parser.add_argument("--core", type=Path, required=True)
parser.add_argument("--presence-main", type=Path, help="暂停的纯唤醒插件源码路径")
parser.add_argument("--keep-artifacts", type=Path, help="保留本轮合成测试文件，不做清理")
args, remaining = parser.parse_known_args()
sys.path.insert(0, str(args.core))
from astrbot.api.message_components import At, Image, Plain, Reply


def load(name, source=None):
    path = source or args.core / "data/plugins" / name / "main.py"
    spec = importlib.util.spec_from_file_location(
        name, path, submodule_search_locations=[str(path.parent)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


meme = load("astrbot_plugin_meme_library")
presence = load("astrbot_plugin_presence_reply", args.presence_main)


class Event:
    def __init__(self, components, sender="member", stripped=None):
        self.message_obj = SimpleNamespace(message=components)
        self.message_str = (
            stripped
            if stripped is not None
            else "".join(c.text for c in components if isinstance(c, Plain))
        )
        self.unified_msg_origin = "test:GroupMessage:isolated"
        self.sender = sender
        self.stopped = False
        self.sent = []

    def get_messages(self):
        return self.message_obj.message

    def get_sender_id(self):
        return self.sender

    def get_self_id(self):
        return "bot"

    def stop_event(self):
        self.stopped = True

    def plain_result(self, text):
        return ("text", text)

    def image_result(self, path):
        return ("image", path)

    async def send(self, result):
        self.sent.append(result)


class Checks(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config = {"wake_prefix": ["丛雨", "丛雨酱", "/"], "admins_id": ["owner"]}
        context = SimpleNamespace(get_config=lambda **kw: self.config)
        self.p = presence.PresenceReplyPlugin.__new__(presence.PresenceReplyPlugin)
        self.p.context = context
        self.p.config = {}
        self.m = meme.MemeLibraryPlugin.__new__(meme.MemeLibraryPlugin)
        self.m.context = context
        self.m.config = {}
        self.m.library_root = Path(self.tmp.name)
        self.m._write_lock = asyncio.Lock()
        self.m._last_sent = {}

    async def asyncTearDown(self):
        self.tmp.cleanup()

    async def wake(self, components, expected, stripped=None):
        event = Event(components, stripped=stripped)
        await self.p.reply_to_empty_wake(event)
        self.assertEqual(event.stopped, expected)
        self.assertEqual(event.sent, [("text", "吾辈在！")] if expected else [])

    async def test_pure_at(self):
        await self.wake([At(qq="bot"), Plain(" ")], True)

    async def test_name(self):
        await self.wake([Plain("丛雨")], True, "")

    async def test_longer_name_after_core_stripping(self):
        await self.wake([Plain("丛雨酱")], True, "酱")

    async def test_dynamic_prefix(self):
        self.config["wake_prefix"] = ["新名字", "/"]
        await self.wake([Plain("新名字")], True, "")
        await self.wake([Plain("丛雨")], False)

    async def test_at_with_content(self):
        await self.wake([At(qq="bot"), Plain("天气怎么样")], False)

    async def test_name_with_content(self):
        await self.wake([Plain("丛雨 今天天气怎么样")], False)

    async def test_at_with_image(self):
        await self.wake([At(qq="bot"), Image(file="file:///unused.png")], False, "")

    async def test_other_at(self):
        await self.wake([At(qq="other")], False, "")

    async def test_reply_is_content(self):
        await self.wake([Reply(id="1", chain=[])], False, "")

    async def test_plain_keyword_silent(self):
        event = Event([Plain("大肥鱼")])
        await self.m.handle_group_image_library(event)
        self.assertEqual(event.sent, [])
        self.assertFalse(event.stopped)

    async def test_missing_member(self):
        event = Event([Plain("不存在.jpg")])
        await self.m.handle_group_image_library(event)
        self.assertEqual(event.sent, [("text", "换个关键词逝世吧...")])

    async def test_missing_owner(self):
        event = Event([Plain("不存在.jpg")], sender="owner")
        await self.m.handle_group_image_library(event)
        self.assertEqual(event.sent, [("text", "主人换个关键词逝世吧...")])

    async def test_store_same_message_and_dedup(self):
        source = Path(self.tmp.name) / "source.png"
        source.write_bytes(b"\x89PNG\r\n\x1a\nexample")
        picture = Image(file=str(source))
        with patch.object(
            Image, "convert_to_file_path", new=AsyncMock(return_value=str(source))
        ):
            for expected in ["存好了", "这张已经存过了"]:
                event = Event(
                    [picture, Plain("/c 大肥鱼.jpg")], stripped="c 大肥鱼.jpg"
                )
                await self.m.handle_group_image_library(event)
                self.assertEqual(event.sent, [("text", expected)])
        images = await self.m._available_images("大肥鱼")
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0].read_bytes(), source.read_bytes())

    async def test_store_reply(self):
        source = Path(self.tmp.name) / "source.png"
        source.write_bytes(b"image")
        picture = Image(file=str(source))
        event = Event([Reply(id="1", chain=[picture]), Plain("/c 回复图.jpg")])
        with patch.object(
            Image, "convert_to_file_path", new=AsyncMock(return_value=str(source))
        ):
            await self.m.handle_group_image_library(event)
        self.assertEqual(event.sent, [("text", "存好了")])
        self.assertEqual(len(await self.m._available_images("回复图")), 1)

    async def test_store_multiple_images_with_add_alias(self):
        first = Path(self.tmp.name) / "first.png"
        second = Path(self.tmp.name) / "second.png"
        first.write_bytes(b"first-image")
        second.write_bytes(b"second-image")
        pictures = [Image(file=str(first)), Image(file=str(second))]
        event = Event([pictures[0], pictures[1], Plain("加图 测试鱼.jpg")])
        with patch.object(
            Image,
            "convert_to_file_path",
            new=AsyncMock(side_effect=[str(first), str(second)]),
        ):
            await self.m.handle_group_image_library(event)
        self.assertEqual(event.sent, [("text", "2 张都存好了")])
        saved = await self.m._available_images("测试鱼")
        self.assertEqual(len(saved), 2)
        self.assertEqual({path.read_bytes() for path in saved}, {b"first-image", b"second-image"})

    async def test_store_count_uses_new_images_only(self):
        existing = Path(self.tmp.name) / "existing.png"
        new = Path(self.tmp.name) / "new.png"
        existing.write_bytes(b"already-there")
        new.write_bytes(b"new-image")
        await self.m._store_bytes("计数", existing.read_bytes())
        event = Event([Image(file=str(existing)), Image(file=str(new)), Plain("加图 计数.jpg")])
        with patch.object(
            Image,
            "convert_to_file_path",
            new=AsyncMock(side_effect=[str(existing), str(new)]),
        ):
            await self.m.handle_group_image_library(event)
        self.assertEqual(
            event.sent,
            [("text", "存好了"), ("text", "第 1 张：这张已经存过了")],
        )
        self.assertEqual(len(await self.m._available_images("计数")), 2)

    async def inventory(self, request, count, exhausted=False):
        directory = self.m.library_root / "大肥鱼"
        directory.mkdir()
        for i in range(10):
            (directory / f"{i}.png").write_bytes(b"image")
        event = Event([Plain(request)])
        with patch.object(meme.asyncio, "sleep", new=AsyncMock()):
            await self.m.handle_group_image_library(event)
        self.assertEqual(sum(kind == "image" for kind, value in event.sent), count)
        self.assertEqual(len(event.sent), count + int(exhausted))
        if exhausted:
            self.assertEqual(event.sent[-1], ("text", "一张也没有了..."))
        self.assertEqual(len(list(directory.iterdir())), 10)

    async def test_send_one(self):
        await self.inventory("大肥鱼.jpg", 1)

    async def test_send_three_separate(self):
        await self.inventory("大肥鱼.jpgx3", 3)

    async def test_exhaustion_no_deletion(self):
        await self.inventory("大肥鱼.jpgx15", 10, True)

    def test_invalid_and_huge_counts(self):
        for text in ["鱼", "鱼.jpgx0", "鱼.jpgx-1", "鱼.jpgxabc", "../鱼.jpg"]:
            self.assertIsNone(meme.parse_fetch_request(text))
        self.assertGreater(meme.parse_fetch_request("鱼.jpgx" + "9" * 5000)[1], 10)

    def test_exclusive_preserves_existing(self):
        target = Path(self.tmp.name) / "existing.png"
        target.write_bytes(b"original")
        self.assertFalse(meme.write_exclusive(target, b"replacement"))
        self.assertEqual(target.read_bytes(), b"original")

    async def test_custom_responses_and_live_changes(self):
        self.m.config["missing_reply"] = "暂时没找到"
        first = Event([Plain("不存在.jpg")])
        await self.m.handle_group_image_library(first)
        self.assertEqual(first.sent, [("text", "暂时没找到")])
        self.m.config["missing_reply"] = "换一个吧"
        second = Event([Plain("不存在.jpg")])
        await self.m.handle_group_image_library(second)
        self.assertEqual(second.sent, [("text", "换一个吧")])

    async def test_custom_store_and_fetch_syntax(self):
        self.m.config.update(
            store_command="/保存",
            image_suffix=".png",
            count_marker="*",
            stored_reply="我存好了",
            duplicate_reply="这个有了",
        )
        source = self.m.library_root / "source.png"
        source.write_bytes(b"image")
        image = Image(file=str(source))
        with patch.object(
            Image, "convert_to_file_path", new=AsyncMock(return_value=str(source))
        ):
            for reply in ["我存好了", "这个有了"]:
                event = Event([Plain("/保存 自定义.png"), image])
                await self.m.handle_group_image_library(event)
                self.assertEqual(event.sent, [("text", reply)])
        event = Event([Plain("自定义.png*2")])
        await self.m.handle_group_image_library(event)
        self.assertEqual(event.sent[-1], ("text", "一张也没有了..."))
        self.assertEqual(event.sent[0][0], "image")
        old = Event([Plain("自定义.jpg")])
        await self.m.handle_group_image_library(old)
        self.assertFalse(old.stopped)

    def test_random_without_batch_or_consecutive_duplicates(self):
        images = [Path(str(i)) for i in range(10)]
        with patch.object(meme.random, "sample", wraps=meme.random.sample) as sample:
            selection = self.m._choose_images("group", "fish", images, 3)
            sample.assert_called_once()
            self.assertEqual(len(set(selection)), 3)
        previous = None
        for _ in range(30):
            selected = self.m._choose_images("group", "fish", images, 1)[0]
            self.assertNotEqual(selected, previous)
            previous = selected

    async def test_gallery_rename_and_move_preserve_image(self):
        await self.m._store_bytes("鱼", b"image")
        source = (await self.m._available_images("鱼"))[0]
        await self.m._rename_keyword("鱼", "大鱼")
        await self.m._move_image("大鱼", source.name, "另一条鱼")
        target = (await self.m._available_images("另一条鱼"))[0]
        self.assertEqual(target.read_bytes(), b"image")
        self.assertEqual(await self.m._available_images("大鱼"), [])

    async def test_gallery_conflict_does_not_overwrite(self):
        await self.m._store_bytes("鱼", b"same")
        await self.m._store_bytes("另一个", b"same")
        source = (await self.m._available_images("鱼"))[0]
        with self.assertRaises(ValueError):
            await self.m._move_image("鱼", source.name, "另一个")
        self.assertEqual(source.read_bytes(), b"same")
        with self.assertRaises(ValueError):
            await self.m._rename_keyword("鱼", "另一个")

    async def test_delete_retains_recoverable_original(self):
        await self.m._store_bytes("鱼", b"original")
        source = (await self.m._available_images("鱼"))[0]
        await self.m._delete_image("鱼", source.name)
        self.assertEqual(await self.m._available_images("鱼"), [])
        saved = list((self.m.library_root / ".trash").rglob(source.name))
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].read_bytes(), b"original")

    def test_gallery_rejects_path_escape(self):
        for keyword in ["../outside", "..", "C:/outside", "CON.name"]:
            with self.assertRaises(ValueError):
                self.m._keyword_dir(keyword)

    def test_card_titles(self):
        core = (args.core / "astrbot/core/pipeline/result_decorate/stage.py").read_text(
            encoding="utf-8"
        )
        report = (
            args.core
            / "data/plugins/astrbot_plugin_qq_group_daily_analysis/src/infrastructure/platform/base.py"
        ).read_text(encoding="utf-8")
        self.assertIn('name="丛雨"', core)
        self.assertIn('self_name = "丛雨"', report)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0], *remaining], verbosity=2)
