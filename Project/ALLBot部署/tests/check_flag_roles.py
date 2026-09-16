"""Isolated real-component tests; no QQ messages or live databases."""

import argparse
import asyncio
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

parser = argparse.ArgumentParser()
parser.add_argument("--core", type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.core))
REPO = Path(__file__).resolve().parents[1]


class Checks(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = Path.cwd()
        os.chdir(self.temp.name)
        from astrbot.api.message_components import At, Plain

        self.At, self.Plain = At, Plain
        self.ctx = SimpleNamespace(
            send_message=AsyncMock(return_value=True),
            get_config=lambda **kw: {"admins_id": ["1"]},
        )
        self.mods = []
        self.plugins = []
        for short in ("liflag", "role_call"):
            name = "astrbot_plugin_" + short
            target = Path(self.temp.name) / "data" / "plugins" / name
            shutil.copytree(REPO / "plugins" / name, target)
            spec = importlib.util.spec_from_file_location(name, target / "main.py")
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            cfg = {
                k: v["default"]
                for k, v in json.loads(
                    (target / "_conf_schema.json").read_text(encoding="utf-8")
                ).items()
            }
            self.mods.append(mod)
            self.plugins.append(mod.Main(self.ctx, cfg))
        self.flag, self.role = self.plugins
        self.fm, self.rm = self.mods

    async def asyncTearDown(self):
        for plugin in self.plugins:
            await plugin.terminate()
        os.chdir(self.old)
        self.temp.cleanup()

    def event(self, value, uid="1", scope="bot:GroupMessage:10", ats=("99",)):
        components = [self.At(qq=x) for x in ats] + [self.Plain(value)]
        return SimpleNamespace(
            get_group_id=lambda: scope.split(":")[-1],
            get_sender_id=lambda: uid,
            get_sender_name=lambda: "Edi" if uid == "1" else "Other",
            get_self_id=lambda: "99",
            get_messages=lambda: components,
            unified_msg_origin=scope,
            stop_event=lambda: None,
            plain_result=lambda x: x,
            chain_result=lambda x: x,
            send=AsyncMock(),
        )

    async def command(self, value, now=100000, **kw):
        event = self.event(value, **kw)
        with patch.object(self.fm.time, "time", return_value=now):
            await self.flag.handle(event)
        return event.send.call_args.args[0]

    async def test_start_finish_and_repeat(self):
        self.assertEqual(
            await self.command("我要学习吃饭20分钟"), "Edi开始学习吃饭20分钟，加油哦！"
        )
        self.assertIn("正在计时", await self.command("我要学习英语10分钟", now=100060))
        self.assertEqual(
            await self.command("学完了", now=100600), "本次学习了10分钟，太棒了"
        )
        self.assertIn("没有开始", await self.command("学完了", now=100610))
        self.assertEqual(
            self.flag.db.execute("select count(*) from sessions").fetchone()[0], 1
        )

    async def test_reminder_boundary_once_and_finish(self):
        await self.command("我要学习吃饭20分钟")
        await self.flag.remind_once(101799)
        self.ctx.send_message.assert_not_called()
        await self.flag.remind_once(101800)
        self.ctx.send_message.assert_awaited_once()
        chain = self.ctx.send_message.call_args.args[1]
        self.assertIn("超时10分钟", str(chain))
        await self.flag.remind_once(102000)
        self.ctx.send_message.assert_awaited_once()
        await self.command("学完了", now=102400)
        self.assertIn("40分钟", await self.command("总学习时长", now=102400))

    async def test_finished_never_reminds(self):
        await self.command("我要学习英语20分钟")
        await self.command("学完了", now=100060)
        await self.flag.remind_once(200000)
        self.ctx.send_message.assert_not_called()

    async def test_failed_delivery_retries(self):
        await self.command("我要学习英语20分钟")
        self.ctx.send_message.return_value = False
        await self.flag.remind_once(101800)
        self.assertEqual(
            self.flag.db.execute("select reminded from sessions").fetchone()[0], 0
        )
        self.ctx.send_message.return_value = True
        await self.flag.remind_once(101810)
        self.assertEqual(
            self.flag.db.execute("select reminded from sessions").fetchone()[0], 1
        )

    async def test_restart_restores_timer(self):
        await self.command("我要学习英语20分钟")
        await self.flag.terminate()
        self.flag = self.fm.Main(self.ctx, self.flag.config)
        self.plugins[0] = self.flag
        await self.flag.remind_once(101800)
        self.ctx.send_message.assert_awaited_once()

    async def test_cross_midnight_and_week(self):
        start = datetime(2026, 9, 14, 23, 50, tzinfo=self.fm.TZ).timestamp()
        await self.command("我要学习英语20分钟", now=start)
        await self.command("学完了", now=start + 1200)
        answer = await self.command("今日学习时长 Edi", now=start + 1200)
        self.assertIn("10分钟", answer)
        week = await self.command("本周学习时长 Edi", now=start + 1200)
        self.assertIn("9月14日星期一  你学习了10分钟", week)
        self.assertIn("9月15日星期二  你学习了10分钟", week)
        self.assertIn("本周你一共学习了20分钟", week)

    async def test_daily_thresholds_and_zero(self):
        self.assertIn("快去学习", await self.command("今日学习时长"))
        await self.command("我要学习英语30分钟")
        self.assertIn("继续加油", await self.command("今日学习时长", now=100900))
        self.assertIn("太厉害", await self.command("今日学习时长", now=100960))

    async def test_total_thresholds(self):
        self.assertEqual(self.fm.encouragement(119, "0 => 加油\n120 => 厉害"), "加油")
        self.assertEqual(self.fm.encouragement(121, "0 => 加油\n120 => 厉害"), "厉害")
        self.assertEqual(
            self.fm.encouragement(600, "120 => 厉害\n0 => 加油\n500 => 最棒"), "最棒"
        )

    async def test_group_person_isolation(self):
        await self.command("我要学习英语20分钟")
        self.assertIn("没有开始", await self.command("学完了", uid="2"))
        self.assertIn(
            "没有开始", await self.command("学完了", scope="bot:GroupMessage:20")
        )

    async def test_filter_does_not_wake_plain_chat(self):
        f = self.fm.StudyFilter()
        self.assertFalse(f.filter(self.event("我要学习英语20分钟", ats=()), {}))
        self.assertFalse(f.filter(self.event("今天天气不错"), {}))
        self.assertTrue(f.filter(self.event("我要学习英语20分钟"), {}))
        self.assertTrue(f.filter(self.event("学完了", ats=()), {}))
        self.flag.config["start_word"] = "我要练习"
        self.assertTrue(f.filter(self.event("我要练习英语20分钟"), {}))

    async def test_ambiguous_name(self):
        await self.command("我要学习英语20分钟")
        event = self.event("", ats=())
        event.bot = SimpleNamespace(
            call_action=AsyncMock(
                return_value=[
                    {"user_id": 1, "nickname": "Edi"},
                    {"user_id": 2, "nickname": "Edi"},
                ]
            )
        )
        self.assertIsNone(await self.flag.resolve(event, "Edi"))
        self.assertEqual((await self.flag.resolve(event, "1"))[0], "1")

    async def test_roles_set_call_replace_and_scope(self):
        await self.role.handle(self.event("设置程序员", ats=("99", "2", "3", "2")))
        event = self.event("召唤程序员 有人做程序吗", uid="5", ats=())
        await self.role.handle(event)
        chain = event.send.call_args.args[0]
        self.assertEqual(
            [str(x.qq) for x in chain if isinstance(x, self.At)], ["2", "3"]
        )
        self.assertEqual(chain[-1].text, "\n——————————\n有人做程序吗")
        await self.role.handle(self.event("设置程序员", ats=("4",)))
        self.assertEqual(
            self.role.db.execute("select uid from members").fetchall(), [("4",)]
        )
        other = self.event("召唤程序员", scope="bot:GroupMessage:20")
        await self.role.handle(other)
        self.assertIn("还没有", other.send.call_args.args[0])

    async def test_role_filter_ignores_ordinary_settings_chat(self):
        rule = self.rm.RoleFilter()
        self.assertFalse(rule.filter(self.event("设置电脑", ats=()), {}))
        self.assertTrue(rule.filter(self.event("设置程序员", ats=("2",)), {}))
        self.assertTrue(rule.filter(self.event("召唤程序员", ats=()), {}))

    async def test_role_permissions_and_custom_words(self):
        event = self.event("设置程序员", uid="2", ats=("3",))
        await self.role.handle(event)
        self.assertIn("只有", event.send.call_args.args[0])
        self.assertEqual(
            self.role.db.execute("select count(*) from members").fetchone()[0], 0
        )
        self.role.config["set_words"] = ["登记", "设置"]
        self.role.config["call_words"] = ["喊人", "召唤"]
        self.assertEqual(self.rm.parse("登记程序员", self.role.config)[1], "程序员")
        self.assertEqual(self.rm.parse("喊人程序员 正文", self.role.config)[2], "正文")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]], verbosity=2)
