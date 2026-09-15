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
args, remaining = parser.parse_known_args()
sys.path.insert(0, str(args.core))
from astrbot.api.message_components import At, Image, Plain, Reply

def load(name):
    path = args.core / "data/plugins" / name / "main.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

meme = load("astrbot_plugin_meme_library")
presence = load("astrbot_plugin_presence_reply")

class Event:
    def __init__(self, components, sender="member", stripped=None):
        self.message_obj = SimpleNamespace(message=components)
        self.message_str = stripped if stripped is not None else "".join(c.text for c in components if isinstance(c, Plain))
        self.unified_msg_origin = "test:GroupMessage:isolated"
        self.sender = sender
        self.stopped = False
        self.sent = []
    def get_messages(self): return self.message_obj.message
    def get_sender_id(self): return self.sender
    def get_self_id(self): return "bot"
    def stop_event(self): self.stopped = True
    def plain_result(self, text): return ("text", text)
    def image_result(self, path): return ("image", path)
    async def send(self, result): self.sent.append(result)

class Checks(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config = {"wake_prefix": ["丛雨", "丛雨酱", "/"], "admins_id": ["owner"]}
        context = SimpleNamespace(get_config=lambda **kw: self.config)
        self.p = presence.PresenceReplyPlugin.__new__(presence.PresenceReplyPlugin)
        self.p.context = context
        self.m = meme.MemeLibraryPlugin.__new__(meme.MemeLibraryPlugin)
        self.m.context = context
        self.m.library_root = Path(self.tmp.name)
        self.m._write_lock = asyncio.Lock()
    async def asyncTearDown(self): self.tmp.cleanup()
    async def wake(self, components, expected, stripped=None):
        event = Event(components, stripped=stripped)
        await self.p.reply_to_empty_wake(event)
        self.assertEqual(event.stopped, expected)
        self.assertEqual(event.sent, [("text", "吾辈在！")] if expected else [])
    async def test_pure_at(self): await self.wake([At(qq="bot"), Plain(" ")], True)
    async def test_name(self): await self.wake([Plain("丛雨")], True, "")
    async def test_longer_name_after_core_stripping(self): await self.wake([Plain("丛雨酱")], True, "酱")
    async def test_dynamic_prefix(self):
        self.config["wake_prefix"] = ["新名字", "/"]
        await self.wake([Plain("新名字")], True, "")
        await self.wake([Plain("丛雨")], False)
    async def test_at_with_content(self): await self.wake([At(qq="bot"), Plain("天气怎么样")], False)
    async def test_name_with_content(self): await self.wake([Plain("丛雨 今天天气怎么样")], False)
    async def test_at_with_image(self): await self.wake([At(qq="bot"), Image(file="file:///unused.png")], False, "")
    async def test_other_at(self): await self.wake([At(qq="other")], False, "")
    async def test_reply_is_content(self): await self.wake([Reply(id="1", chain=[])], False, "")
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
        with patch.object(Image, "convert_to_file_path", new=AsyncMock(return_value=str(source))):
            for expected in ["存好了。", "这张已经存过了。"]:
                event = Event([picture, Plain("/c 大肥鱼.jpg")], stripped="c 大肥鱼.jpg")
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
        with patch.object(Image, "convert_to_file_path", new=AsyncMock(return_value=str(source))):
            await self.m.handle_group_image_library(event)
        self.assertEqual(event.sent, [("text", "存好了。")])
        self.assertEqual(len(await self.m._available_images("回复图")), 1)
    async def inventory(self, request, count, exhausted=False):
        directory = self.m.library_root / "大肥鱼"
        directory.mkdir()
        for i in range(10): (directory / f"{i}.png").write_bytes(b"image")
        event = Event([Plain(request)])
        with patch.object(meme.asyncio, "sleep", new=AsyncMock()):
            await self.m.handle_group_image_library(event)
        self.assertEqual(sum(kind == "image" for kind, value in event.sent), count)
        self.assertEqual(len(event.sent), count + int(exhausted))
        if exhausted: self.assertEqual(event.sent[-1], ("text", "一张也没有了..."))
        self.assertEqual(len(list(directory.iterdir())), 10)
    async def test_send_one(self): await self.inventory("大肥鱼.jpg", 1)
    async def test_send_three_separate(self): await self.inventory("大肥鱼.jpgx3", 3)
    async def test_exhaustion_no_deletion(self): await self.inventory("大肥鱼.jpgx15", 10, True)
    def test_invalid_and_huge_counts(self):
        for text in ["鱼", "鱼.jpgx0", "鱼.jpgx-1", "鱼.jpgxabc", "../鱼.jpg"]:
            self.assertIsNone(meme.parse_fetch_request(text))
        self.assertGreater(meme.parse_fetch_request("鱼.jpgx" + "9"*5000)[1], 10)
    def test_exclusive_preserves_existing(self):
        target = Path(self.tmp.name) / "existing.png"
        target.write_bytes(b"original")
        self.assertFalse(meme.write_exclusive(target, b"replacement"))
        self.assertEqual(target.read_bytes(), b"original")
    def test_card_titles(self):
        core = (args.core / "astrbot/core/pipeline/result_decorate/stage.py").read_text(encoding="utf-8")
        report = (args.core / "data/plugins/astrbot_plugin_qq_group_daily_analysis/src/infrastructure/platform/base.py").read_text(encoding="utf-8")
        self.assertIn('name="丛雨"', core)
        self.assertIn('self_name = "丛雨"', report)

if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0], *remaining], verbosity=2)

