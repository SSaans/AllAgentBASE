"""隔离用例：关键词回复 / 入群欢迎 / 禁言 / 使用说明。

不连 QQ、不启 AstrBot、不调真实 LLM、不改运行配置；只用真实的 AstrBot 组件
（`RegexFilter`、`CustomFilter`、`EventMessageTypeFilter` 等）配合合成事件跑。

用法：
    python tests/check_new_plugins.py --core <实例 core 绝对路径>
    python tests/check_new_plugins.py --core <core> --deploy-dir <core>/data/plugins
"""

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from sys import maxsize
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

parser = argparse.ArgumentParser()
parser.add_argument("--core", type=Path, required=True)
parser.add_argument(
    "--deploy-dir", type=Path, help="运行目录 data/plugins，用于校验部署副本一致"
)
args, remaining = parser.parse_known_args()

# ⚠️ 必须放在导入 astrbot 之前：AstrBot 核心会按「当前工作目录」生成 data/
# （内含一份默认 cmd_config.json）。实测过一次把 data/ 落进子项目目录，
# 而该路径不在 .gitignore 覆盖范围内，有被 git add 带进仓库的风险。
# 把所有测试产物一律赶到临时目录，绝不落在仓库内。
_CWD_SANDBOX = tempfile.mkdtemp(prefix="astrbot_test_cwd_")
os.chdir(_CWD_SANDBOX)

sys.path.insert(0, str(args.core))

from astrbot.api.message_components import At, Plain
from astrbot.core.star.filter.custom_filter import CustomFilter
from astrbot.core.star.filter.regex import RegexFilter
from astrbot.core.star.star_handler import star_handlers_registry

PLUGIN_ROOT = Path(__file__).resolve().parent.parent / "plugins"
NEW_PLUGINS = (
    "astrbot_plugin_keyword_reply",
    "astrbot_plugin_group_welcome",
    "astrbot_plugin_mute",
    "astrbot_plugin_usage_guide",
)

KEYWORD_HANDLER = "astrbot_plugin_keyword_reply_handle_keywords"
WELCOME_HANDLER = "astrbot_plugin_group_welcome_welcome_new_member"
MUTE_HANDLER = "astrbot_plugin_mute_guard"
GUIDE_HANDLER = "astrbot_plugin_usage_guide_send_guide"


def load(name):
    path = PLUGIN_ROOT / name / "main.py"
    spec = importlib.util.spec_from_file_location(
        name, path, submodule_search_locations=[str(path.parent)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


keyword = load("astrbot_plugin_keyword_reply")
welcome = load("astrbot_plugin_group_welcome")
mute = load("astrbot_plugin_mute")
guide = load("astrbot_plugin_usage_guide")


def handler_meta(full_name):
    md = star_handlers_registry.get_handler_by_full_name(full_name)
    assert md is not None, f"处理器 {full_name} 没有注册"
    return md


def regex_filters_of(full_name):
    md = handler_meta(full_name)
    return [f for f in md.event_filters if isinstance(f, RegexFilter)]


class Bot:
    """假的协议端，只实现取群名片。"""

    def __init__(self, card="小明", fail=False):
        self.card = card
        self.fail = fail

    async def call_action(self, action, **kwargs):
        if self.fail:
            raise RuntimeError("protocol error")
        return {"card": self.card, "nickname": self.card}


class Event:
    def __init__(
        self,
        text="",
        group_id="1000",
        sender="member",
        raw=None,
        private=False,
        admin=False,
        bot=None,
        nickname="成员昵称",
    ):
        self.message_obj = SimpleNamespace(message=[], raw_message=raw)
        self.message_str = text
        self.group_id = group_id
        self.sender = sender
        self.private = private
        self.admin = admin
        self.bot = bot
        self.nickname = nickname
        self.unified_msg_origin = (
            f"test:FriendMessage:{sender}"
            if private
            else f"test:GroupMessage:{group_id}"
        )
        self.session_id = str(sender) if private else str(group_id)
        self.stopped = False
        self.sent = []

    def get_message_str(self):
        return self.message_str

    def get_messages(self):
        return self.message_obj.message

    def get_group_id(self):
        return "" if self.private else self.group_id

    def get_self_id(self):
        return "bot"

    def get_sender_id(self):
        return self.sender

    def get_sender_name(self):
        return self.nickname

    def is_admin(self):
        return self.admin

    def is_private_chat(self):
        return self.private

    def stop_event(self):
        self.stopped = True

    def is_stopped(self):
        return self.stopped

    def plain_result(self, text):
        return ("text", text)

    def chain_result(self, chain):
        return ("chain", chain)

    async def send(self, result):
        self.sent.append(result)
        return True


def keyword_config(**overrides):
    config = {
        "enable": True,
        "rules_text": (
            "# 注释行会被跳过\n"
            "我是笨蛋吗 => 是|不是|不知道|钝角\n"
            "早上好 => 早啊\n"
            "qq:10001: 我是笨蛋吗 => =是\n"
            "group:20002: 早上好 => =早上好呀\n"
            "这句写坏了没有箭头\n"
        ),
        "group_whitelist": [],
    }
    config.update(overrides)
    return config


class KeywordReplyChecks(unittest.IsolatedAsyncioTestCase):
    """任务 27：关键词自动回复。"""

    async def asyncSetUp(self):
        self.plugin = keyword.KeywordReplyPlugin(SimpleNamespace(), keyword_config())

    def build(self, **overrides):
        self.plugin = keyword.KeywordReplyPlugin(
            SimpleNamespace(), keyword_config(**overrides)
        )
        return self.plugin

    def test_parse_rules_structure(self):
        default_rules, targeted_rules = keyword.parse_rules(
            keyword_config()["rules_text"]
        )
        self.assertEqual(
            [r["trigger"] for r in default_rules], ["我是笨蛋吗", "早上好"]
        )
        self.assertEqual(default_rules[0]["replies"], ["是", "不是", "不知道", "钝角"])
        self.assertEqual(default_rules[0]["kind"], "")
        self.assertEqual([r["kind"] for r in targeted_rules], ["qq", "group"])
        self.assertEqual(targeted_rules[0]["replies"], ["是"])

    def test_fixed_reply_keeps_pipe(self):
        default_rules, _ = keyword.parse_rules("测试 => =a|b")
        self.assertEqual(default_rules[0]["replies"], ["a|b"])

    def test_regex_trigger(self):
        default_rules, _ = keyword.parse_rules("/^晚安$/ => 晚安")
        self.assertIsNotNone(default_rules[0]["regex"].search("晚安"))
        self.assertIsNone(default_rules[0]["regex"].search("早点晚安哟"))

    def test_broken_rule_is_skipped(self):
        default_rules, targeted_rules = keyword.parse_rules(
            "没箭头\n=> 只有回复\n只有触发词 =>\n正常 => 好"
        )
        self.assertEqual([r["trigger"] for r in default_rules], ["正常"])
        self.assertEqual(targeted_rules, [])

    def test_targeted_rule_wins_over_default(self):
        rules = (self.plugin.default_rules, self.plugin.targeted_rules)
        hit = keyword.match_rule(rules, "我是笨蛋吗", "10001", "3000")
        self.assertEqual(hit["replies"], ["是"])
        fallback = keyword.match_rule(rules, "我是笨蛋吗", "10002", "3000")
        self.assertEqual(len(fallback["replies"]), 4)
        by_group = keyword.match_rule(rules, "早上好", "10003", "20002")
        self.assertEqual(by_group["replies"], ["早上好呀"])

    def test_extra_text_still_matches(self):
        rules = (self.plugin.default_rules, self.plugin.targeted_rules)
        self.assertIsNotNone(
            keyword.match_rule(rules, "喂 我是笨蛋吗 快回答", "9", "3000")
        )
        self.assertIsNotNone(keyword.match_rule(rules, "我是笨蛋吗哈哈", "9", "3000"))
        self.assertIsNone(keyword.match_rule(rules, "我真的是笨蛋吗哈哈", "9", "3000"))
        self.assertIsNone(keyword.match_rule(rules, "今天中午吃什么", "9", "3000"))

    async def test_random_reply_and_stop_event(self):
        with patch.object(
            keyword.random, "choice", side_effect=lambda items: items[-1]
        ):
            event = Event("我是笨蛋吗")
            await self.plugin.handle_keywords(event)
        self.assertEqual(event.sent, [("text", "钝角")])
        self.assertTrue(event.stopped)

    async def test_fixed_reply_for_targeted_user(self):
        event = Event("我是笨蛋吗", sender="10001")
        await self.plugin.handle_keywords(event)
        self.assertEqual(event.sent, [("text", "是")])
        self.assertTrue(event.stopped)

    async def test_unmatched_text_is_left_alone(self):
        event = Event("今天天气不错啊")
        await self.plugin.handle_keywords(event)
        self.assertEqual(event.sent, [])
        self.assertFalse(event.stopped)

    async def test_self_message_ignored(self):
        event = Event("我是笨蛋吗", sender="bot")
        await self.plugin.handle_keywords(event)
        self.assertEqual(event.sent, [])
        self.assertFalse(event.stopped)

    async def test_placeholder_rendering(self):
        plugin = self.build(rules_text="问好 => 你好{nickname}")
        event = Event("问好", nickname="小绿")
        await plugin.handle_keywords(event)
        self.assertEqual(event.sent, [("text", "你好小绿")])

    async def test_group_whitelist_blocks_other_group(self):
        plugin = self.build(group_whitelist=["1000"])
        blocked = Event("我是笨蛋吗", group_id="9999")
        await plugin.handle_keywords(blocked)
        self.assertEqual(blocked.sent, [])
        allowed = Event("我是笨蛋吗", group_id="1000")
        await plugin.handle_keywords(allowed)
        self.assertTrue(allowed.stopped)

    def test_regex_filter_is_built_from_config(self):
        filters = regex_filters_of(KEYWORD_HANDLER)
        self.assertEqual(len(filters), 1)
        self.assertTrue(filters[0].filter(Event("我是笨蛋吗"), {}))
        self.assertTrue(filters[0].filter(Event("早上好呀"), {}))
        self.assertFalse(filters[0].filter(Event("晚上吃什么"), {}))
        self.assertEqual(handler_meta(KEYWORD_HANDLER).extras_configs["priority"], 10)

    def test_disabled_plugin_never_matches(self):
        self.build(enable=False)
        filters = regex_filters_of(KEYWORD_HANDLER)
        self.assertFalse(filters[0].filter(Event("我是笨蛋吗"), {}))
        self.assertEqual(keyword.build_pattern([]), keyword.NEVER_MATCH)


class GroupWelcomeChecks(unittest.IsolatedAsyncioTestCase):
    """任务 28：入群欢迎。"""

    def setUp(self):
        self.filter = welcome.GroupIncreaseFilter()
        self.config = {
            "enable": True,
            "welcome_text": "欢迎 {nickname} 加入本群～（群号 {group_id}）",
            "at_new_member": True,
            "group_texts": "# 注释\n20002 => 欢迎 {nickname} 进入二号群",
        }
        self.plugin = welcome.GroupWelcomePlugin(SimpleNamespace(), dict(self.config))

    def notice(self, group_id="1000", user_id="777"):
        return Event(
            raw={
                "notice_type": "group_increase",
                "user_id": user_id,
                "group_id": group_id,
            },
            group_id=group_id,
        )

    def test_filter_only_passes_group_increase(self):
        self.assertTrue(self.filter.filter(self.notice(), {}))
        self.assertFalse(
            self.filter.filter(
                Event(raw={"post_type": "message", "message_type": "group"}), {}
            )
        )
        self.assertFalse(
            self.filter.filter(Event(raw={"notice_type": "group_decrease"}), {})
        )
        self.assertFalse(self.filter.filter(Event(raw={"notice_type": "poke"}), {}))
        self.assertFalse(self.filter.filter(Event(raw=None), {}))
        self.assertFalse(self.filter.filter(Event(raw=["not", "a", "dict"]), {}))

    def test_filter_is_a_custom_filter(self):
        self.assertIsInstance(self.filter, CustomFilter)
        md = handler_meta(WELCOME_HANDLER)
        self.assertTrue(any(isinstance(f, CustomFilter) for f in md.event_filters))
        self.assertGreater(md.extras_configs["priority"], maxsize + 1)

    async def test_welcome_sends_at_and_text(self):
        event = self.notice()
        event.bot = Bot(card="小明")
        await self.plugin.welcome_new_member(event)
        self.assertTrue(event.stopped)
        self.assertEqual(len(event.sent), 1)
        kind, chain = event.sent[0]
        self.assertEqual(kind, "chain")
        self.assertEqual(len(chain), 2)
        self.assertIsInstance(chain[0], At)
        self.assertEqual(str(chain[0].qq), "777")
        self.assertEqual(chain[0].name, "小明")
        self.assertIsInstance(chain[1], Plain)
        self.assertEqual(chain[1].text, "欢迎 小明 加入本群～（群号 1000）")

    async def test_placeholder_falls_back_to_user_id(self):
        event = self.notice()
        event.bot = Bot(fail=True)
        await self.plugin.welcome_new_member(event)
        self.assertEqual(event.sent[0][1][1].text, "欢迎 777 加入本群～（群号 1000）")

    async def test_no_bot_still_welcomes(self):
        event = self.notice()
        await self.plugin.welcome_new_member(event)
        self.assertEqual(len(event.sent), 1)

    async def test_per_group_text_and_no_at(self):
        self.plugin.config["at_new_member"] = False
        event = self.notice()
        event.bot = Bot(card="小红")
        await self.plugin.welcome_new_member(event)
        chain = event.sent[0][1]
        self.assertEqual(len(chain), 1)
        self.assertEqual(chain[0].text, "欢迎 小红 加入本群～（群号 1000）")

        group_event = self.notice(group_id="20002", user_id="888")
        group_event.bot = Bot(card="小紫")
        await self.plugin.welcome_new_member(group_event)
        self.assertEqual(group_event.sent[0][1][-1].text, "欢迎 小紫 进入二号群")

    async def test_disabled_sends_nothing(self):
        self.plugin.config["enable"] = False
        event = self.notice()
        await self.plugin.welcome_new_member(event)
        self.assertEqual(event.sent, [])
        self.assertFalse(event.stopped)

    async def test_empty_text_only_stops(self):
        self.plugin.config["welcome_text"] = "   "
        self.plugin.group_texts = {}
        event = self.notice()
        await self.plugin.welcome_new_member(event)
        self.assertEqual(event.sent, [])
        self.assertTrue(event.stopped)

    async def test_no_user_id_is_ignored(self):
        event = Event(
            raw={"notice_type": "group_increase", "group_id": "1000"}, group_id="1000"
        )
        await self.plugin.welcome_new_member(event)
        self.assertEqual(event.sent, [])


class MuteChecks(unittest.IsolatedAsyncioTestCase):
    """任务 26：禁言。"""

    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_file = Path(self.tmp.name) / "mute_state.json"
        self.patcher = patch.object(mute, "STATE_FILE", self.state_file)
        self.patcher.start()
        self.plugins = []

    async def asyncTearDown(self):
        for plugin in self.plugins:
            await plugin.terminate()
        self.patcher.stop()
        self.tmp.cleanup()

    def build(self, **overrides):
        config = {
            "enable": True,
            "command_words": ["闭嘴"],
            "default_minutes": 30,
            "max_minutes": 1440,
            "scope": "group",
            "start_reply": "好的，接下来我会闭嘴{duration}",
            "resume_reply": "",
            "admins_only": False,
        }
        config.update(overrides)
        plugin = mute.MutePlugin(SimpleNamespace(), config)
        self.plugins.append(plugin)
        return plugin

    def test_parse_duration_units(self):
        cases = {
            "闭嘴 30分钟": (1800, "30分钟"),
            "闭嘴 5分": (300, "5分"),
            "闭嘴 90秒": (90, "90秒"),
            "闭嘴 2小时": (7200, "2小时"),
            "闭嘴 1h": (3600, "1h"),
            "闭嘴10": (600, "10分钟"),
        }
        for text, (seconds, duration) in cases.items():
            request = mute.parse_mute_request(text, ["闭嘴"], 30, 1440)
            self.assertIsNotNone(request, text)
            self.assertAlmostEqual(request["seconds"], seconds, delta=1, msg=text)
            self.assertEqual(request["duration"], duration, text)

    def test_parse_duration_defaults_and_cap(self):
        request = mute.parse_mute_request("闭嘴", ["闭嘴"], 15, 1440)
        self.assertAlmostEqual(request["seconds"], 900, delta=1)
        capped = mute.parse_mute_request("闭嘴 99999分钟", ["闭嘴"], 30, 1440)
        self.assertTrue(capped["capped"])
        self.assertAlmostEqual(capped["seconds"], 1440 * 60, delta=1)

    def test_no_command_word_means_none(self):
        self.assertIsNone(mute.parse_mute_request("今天天气不错", ["闭嘴"], 30, 1440))
        self.assertIsNone(mute.parse_mute_request("", ["闭嘴"], 30, 1440))

    def test_priority_beats_presence_reply(self):
        md = handler_meta(MUTE_HANDLER)
        self.assertEqual(md.extras_configs["priority"], maxsize + 100)

    async def test_command_replies_and_silences_same_group(self):
        plugin = self.build()
        command = Event("丛雨闭嘴 30分钟", group_id="1000")
        await plugin.guard(command)
        self.assertEqual(command.sent, [("text", "好的，接下来我会闭嘴30分钟")])
        self.assertTrue(command.stopped)

        silent = Event("大家好啊", group_id="1000")
        await plugin.guard(silent)
        self.assertEqual(silent.sent, [])
        self.assertTrue(silent.stopped)

        other = Event("大家好啊", group_id="9999")
        await plugin.guard(other)
        self.assertEqual(other.sent, [])
        self.assertFalse(other.stopped)

    async def test_default_duration_when_bare_command(self):
        plugin = self.build()
        event = Event("闭嘴", group_id="1000")
        await plugin.guard(event)
        self.assertEqual(event.sent, [("text", "好的，接下来我会闭嘴30分钟")])

    async def test_global_scope_silences_private_too(self):
        plugin = self.build(scope="global")
        await plugin.guard(Event("闭嘴 2分钟", group_id="1000"))
        private = Event("在吗", private=True, sender="someone")
        await plugin.guard(private)
        self.assertTrue(private.stopped)

    async def test_second_command_resets_timer(self):
        plugin = self.build()
        await plugin.guard(Event("闭嘴 30分钟", group_id="1000"))
        first = plugin.store.deadline("group:1000")
        await plugin.guard(Event("闭嘴 1分钟", group_id="1000"))
        second = plugin.store.deadline("group:1000")
        self.assertLess(second, first)

    async def test_expired_mute_restores_speaking(self):
        plugin = self.build()
        await plugin.guard(Event("闭嘴 30分钟", group_id="1000"))
        plugin.store.targets["group:1000"]["deadline"] = time.time() - 5
        after = Event("大家好啊", group_id="1000")
        await plugin.guard(after)
        self.assertFalse(after.stopped)
        self.assertNotIn("group:1000", plugin.store.targets)

    async def test_timer_is_armed_and_cancelled(self):
        plugin = self.build()
        await plugin.guard(Event("闭嘴 30分钟", group_id="1000"))
        self.assertIn("group:1000", plugin._timers)
        self.assertFalse(plugin._timers["group:1000"].done())

    async def test_state_persists_across_reload(self):
        plugin = self.build()
        await plugin.guard(Event("闭嘴 45分钟", group_id="1000"))
        self.assertTrue(self.state_file.exists())
        saved = json.loads(self.state_file.read_text(encoding="utf-8"))
        self.assertEqual(
            saved["targets"]["group:1000"]["umo"], "test:GroupMessage:1000"
        )

        revived = mute.MutePlugin(SimpleNamespace(), plugin.config)
        self.plugins.append(revived)
        self.assertGreater(revived.store.deadline("group:1000"), time.time())
        await revived.initialize()
        self.assertTrue(revived._timers)

    async def test_initialize_drops_expired_state(self):
        self.state_file.write_text(
            json.dumps(
                {"targets": {"group:1000": {"deadline": time.time() - 1, "umo": "x"}}}
            ),
            encoding="utf-8",
        )
        plugin = self.build()
        await plugin.initialize()
        self.assertEqual(plugin.store.targets, {})
        self.assertEqual(plugin._timers, {})

    async def test_admins_only_blocks_member(self):
        plugin = self.build(admins_only=True)
        member = Event("闭嘴 5分钟", group_id="1000", admin=False)
        await plugin.guard(member)
        self.assertEqual(member.sent, [])
        self.assertFalse(member.stopped)
        owner = Event("闭嘴 5分钟", group_id="1000", admin=True, sender="owner")
        await plugin.guard(owner)
        self.assertTrue(owner.stopped)

    async def test_disabled_plugin_does_nothing(self):
        plugin = self.build(enable=False)
        event = Event("闭嘴 5分钟", group_id="1000")
        await plugin.guard(event)
        self.assertEqual(event.sent, [])
        self.assertFalse(event.stopped)

    async def test_resume_reply_is_sent_once(self):
        plugin = self.build(resume_reply="我回来了")
        plugin.context = SimpleNamespace(send_message=AsyncMock(return_value=True))
        await plugin.guard(Event("闭嘴 5分钟", group_id="1000"))
        # 到点触发：手动把 deadline 拨到过去，模拟定时器到期
        plugin.store.targets["group:1000"]["deadline"] = time.time() - 1
        await plugin._on_resume("group:1000")
        plugin.context.send_message.assert_awaited_once()
        umo, chain = plugin.context.send_message.await_args.args
        self.assertEqual(umo, "test:GroupMessage:1000")
        self.assertEqual(chain.chain[0].text, "我回来了")
        self.assertNotIn("group:1000", plugin.store.targets)

    async def test_resume_keeps_newer_deadline(self):
        """还没到点就被叫起来时，不能误报「我回来了」，得按新时间重排。"""
        plugin = self.build(resume_reply="我回来了")
        plugin.context = SimpleNamespace(send_message=AsyncMock(return_value=True))
        await plugin.guard(Event("闭嘴 5分钟", group_id="1000"))
        await plugin._on_resume("group:1000")
        plugin.context.send_message.assert_not_awaited()
        self.assertIn("group:1000", plugin.store.targets)
        self.assertIn("group:1000", plugin._timers)

    async def test_resume_without_reply_text_is_silent(self):
        plugin = self.build(resume_reply="   ")
        plugin.context = SimpleNamespace(send_message=AsyncMock(return_value=True))
        await plugin.guard(Event("闭嘴 5分钟", group_id="1000"))
        plugin.store.targets["group:1000"]["deadline"] = time.time() - 1
        await plugin._on_resume("group:1000")
        plugin.context.send_message.assert_not_awaited()
        self.assertNotIn("group:1000", plugin.store.targets)

    async def test_manual_resume_clears_state_timer_and_prevents_second_reply(self):
        plugin = self.build(resume_reply="自动恢复")
        plugin.context = SimpleNamespace(send_message=AsyncMock())
        await plugin.guard(Event("闭嘴 30分钟"))
        timer = plugin._timers["group:1000"]
        event = Event("可以说话了")
        await plugin.guard(event)
        self.assertEqual(event.sent, [("text", "好啦，我回来了")])
        self.assertTrue(event.stopped)
        self.assertEqual(plugin.store.targets, {})
        self.assertEqual(plugin._timers, {})
        self.assertTrue(timer.cancelling() or timer.cancelled())
        self.assertEqual(json.loads(self.state_file.read_text())["targets"], {})
        await plugin._on_resume("group:1000")
        plugin.context.send_message.assert_not_awaited()
        following = Event("我是笨蛋吗")
        await plugin.guard(following)
        self.assertFalse(following.stopped)

    async def test_unmute_wins_when_command_contains_mute_word(self):
        plugin = self.build(unmute_words=["别闭嘴了"], unmute_reply="我在")
        await plugin.guard(Event("闭嘴"))
        event = Event("别闭嘴了")
        await plugin.guard(event)
        self.assertEqual(event.sent, [("text", "我在")])
        self.assertEqual(plugin.store.targets, {})

    async def test_name_unmute_survives_wake_prefix_stripping(self):
        plugin = self.build()
        await plugin.guard(Event("闭嘴"))
        event = Event("说话")
        event.message_obj.message = [At(qq="bot"), Plain("丛雨说话")]
        await plugin.guard(event)
        self.assertEqual(event.sent, [("text", "好啦，我回来了")])
        self.assertEqual(plugin.store.targets, {})

    async def test_unmute_keeps_other_groups_silenced(self):
        plugin = self.build()
        await plugin.guard(Event("闭嘴", group_id="1000"))
        await plugin.guard(Event("闭嘴", group_id="2000"))
        await plugin.guard(Event("解除禁言", group_id="1000"))
        self.assertNotIn("group:1000", plugin.store.targets)
        self.assertIn("group:2000", plugin.store.targets)

    async def test_manual_resume_clears_global_mute(self):
        plugin = self.build(scope="global")
        await plugin.guard(Event("闭嘴", group_id="1000"))
        await plugin.guard(Event("解除禁言", group_id="2000"))
        private = Event("在吗", private=True)
        await plugin.guard(private)
        self.assertFalse(private.stopped)
        self.assertEqual(plugin.store.targets, {})

    async def test_admins_only_also_applies_to_manual_resume(self):
        plugin = self.build(admins_only=True)
        await plugin.guard(Event("闭嘴", admin=True))
        member = Event("解除禁言", admin=False)
        await plugin.guard(member)
        self.assertEqual(member.sent, [])
        self.assertTrue(member.stopped)
        self.assertIn("group:1000", plugin.store.targets)
        owner = Event("解除禁言", admin=True)
        await plugin.guard(owner)
        self.assertEqual(owner.sent, [("text", "好啦，我回来了")])

    async def test_manual_resume_can_be_silent(self):
        plugin = self.build(unmute_reply="")
        await plugin.guard(Event("闭嘴"))
        event = Event("解除禁言")
        await plugin.guard(event)
        self.assertEqual(event.sent, [])
        self.assertTrue(event.stopped)
        self.assertEqual(plugin.store.targets, {})

    async def test_repeated_mute_resets_time_without_speaking(self):
        plugin = self.build()
        await plugin.guard(Event("闭嘴 30分钟"))
        before = plugin.store.deadline("group:1000")
        event = Event("闭嘴 1分钟")
        await plugin.guard(event)
        self.assertLess(plugin.store.deadline("group:1000"), before)
        self.assertEqual(event.sent, [])
        self.assertTrue(event.stopped)

    def test_duration_ignores_mention_number_and_reports_cap(self):
        request = mute.parse_mute_request(
            "[At:123456789] 丛雨闭嘴 10秒", ["闭嘴"], 30, 1440
        )
        self.assertEqual(request["seconds"], 10)
        capped = mute.parse_mute_request("闭嘴 9999分钟", ["闭嘴"], 30, 60)
        self.assertEqual(capped["duration"], "60分钟")
        self.assertEqual(capped["seconds"], 3600)

    async def test_expired_state_is_removed_from_disk_on_initialize(self):
        self.state_file.write_text(
            json.dumps({"targets": {"group:1000": {"deadline": 1}}})
        )
        plugin = self.build()
        await plugin.initialize()
        self.assertEqual(json.loads(self.state_file.read_text())["targets"], {})


class UsageGuideChecks(unittest.IsolatedAsyncioTestCase):
    """任务 29：使用说明。"""

    async def asyncSetUp(self):
        self.config = {
            "enable": True,
            "triggers": "使用说明\n帮助",
            "guide_text": "我是丛雨，能帮你做群分析、群漫画、存表情包～",
            "draft_triggers": "生成使用说明",
            "draft_prompt": "",
        }
        self.provider = SimpleNamespace(
            text_chat=AsyncMock(
                return_value=SimpleNamespace(completion_text="这是模型写的草稿")
            )
        )
        self.context = SimpleNamespace(
            get_using_provider=lambda umo=None: self.provider
        )
        self.plugin = guide.UsageGuidePlugin(self.context, dict(self.config))

    async def test_trigger_sends_guide_and_stops(self):
        event = Event("使用说明")
        await self.plugin.send_guide(event)
        self.assertEqual(event.sent, [("text", self.config["guide_text"])])
        self.assertTrue(event.stopped)

    async def test_trigger_inside_sentence(self):
        event = Event("丛雨 帮助一下")
        await self.plugin.send_guide(event)
        self.assertEqual(len(event.sent), 1)

    async def test_unrelated_text_is_left_alone(self):
        event = Event("今天群里聊了啥")
        await self.plugin.send_guide(event)
        self.assertEqual(event.sent, [])
        self.assertFalse(event.stopped)

    async def test_draft_does_not_overwrite_guide(self):
        event = Event("生成使用说明")
        await self.plugin.send_guide(event)
        self.provider.text_chat.assert_awaited_once()
        body = event.sent[0][1]
        self.assertIn("这是模型写的草稿", body)
        self.assertEqual(self.plugin.config["guide_text"], self.config["guide_text"])
        self.assertTrue(event.stopped)

    async def test_draft_without_provider_falls_back(self):
        self.context.get_using_provider = lambda umo=None: None
        event = Event("生成使用说明")
        await self.plugin.send_guide(event)
        self.assertIn(self.config["guide_text"], event.sent[0][1])

    async def test_draft_failure_falls_back(self):
        self.provider.text_chat = AsyncMock(side_effect=RuntimeError("boom"))
        event = Event("生成使用说明")
        await self.plugin.send_guide(event)
        self.assertIn(self.config["guide_text"], event.sent[0][1])

    async def test_empty_guide_text(self):
        self.plugin.config["guide_text"] = ""
        event = Event("帮助")
        await self.plugin.send_guide(event)
        self.assertIn("插件配置", event.sent[0][1])

    async def test_disabled_plugin_does_nothing(self):
        self.plugin = guide.UsageGuidePlugin(
            self.context, {**self.config, "enable": False}
        )
        event = Event("使用说明")
        await self.plugin.send_guide(event)
        self.assertEqual(event.sent, [])

    def test_regex_filter_matches_configured_triggers(self):
        filters = regex_filters_of(GUIDE_HANDLER)
        self.assertEqual(len(filters), 1)
        self.assertTrue(filters[0].filter(Event("使用说明"), {}))
        self.assertTrue(filters[0].filter(Event("生成使用说明"), {}))
        self.assertFalse(filters[0].filter(Event("今天吃什么"), {}))

    def test_trigger_list_parsing(self):
        self.assertEqual(
            guide.parse_trigger_list("# 注释\n帮助|help\n\n能干什么"),
            ["帮助", "help", "能干什么"],
        )
        self.assertEqual(guide.build_pattern([]), guide.NEVER_MATCH)


class DeployedCopyChecks(unittest.TestCase):
    """仓库里的插件源码必须和运行目录里加载的一致（防止两份代码走偏）。"""

    def test_deployed_copies_match(self):
        if not args.deploy_dir:
            self.skipTest("未提供 --deploy-dir")
        for name in NEW_PLUGINS:
            source_dir = PLUGIN_ROOT / name
            target_dir = args.deploy_dir / name
            self.assertTrue(target_dir.is_dir(), f"运行目录缺少 {name}")
            for path in sorted(source_dir.iterdir()):
                if path.is_dir() or path.suffix == ".pyc":
                    continue
                target = target_dir / path.name
                self.assertTrue(target.is_file(), f"运行目录缺少 {name}/{path.name}")
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    hashlib.sha256(target.read_bytes()).hexdigest(),
                    f"{name}/{path.name} 仓库与运行目录不一致",
                )


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0], *remaining], verbosity=2)
