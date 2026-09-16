"""Persistent group study timers and configurable summaries."""

from __future__ import annotations

import asyncio
import contextlib
import re
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sys import maxsize

from astrbot.api import logger
from astrbot.api.event import MessageChain, filter
from astrbot.api.event.filter import CustomFilter
from astrbot.api.message_components import At, Plain
from astrbot.api.star import Star

TZ = timezone(timedelta(hours=8))
CONFIG = {}


def text(event):
    return "".join(c.text for c in event.get_messages() if isinstance(c, Plain)).strip()


def mentioned(event):
    return any(
        isinstance(c, At) and str(c.qq) == str(event.get_self_id())
        for c in event.get_messages()
    )


def parse(value, cfg):
    prefix = str(cfg.get("start_word", "我要学习"))
    match = re.fullmatch(re.escape(prefix) + r"(.+?)\s*(\d+)分钟", value)
    if match:
        return "start", (match[1].strip(), int(match[2]))
    if value == cfg.get("finish_word", "学完了"):
        return "finish", ""
    for kind, default in [
        ("day", "今日学习时长"),
        ("week", "本周学习时长"),
        ("total", "总学习时长"),
    ]:
        word = str(cfg.get(kind + "_word", default))
        if value == word or value.startswith(word + " "):
            return kind, value[len(word) :].strip()
    return None


def render(template, **values):
    for key, value in values.items():
        template = template.replace("{" + key + "}", str(value))
    return template


def minutes(seconds):
    return round(max(0, seconds) / 60, 1)


def display(value):
    return f"{value:g}"


def encouragement(value, rules):
    choices = []
    for line in str(rules).splitlines():
        left, sep, right = line.partition("=>")
        try:
            threshold = float(left.strip())
        except ValueError:
            continue
        if sep and 0 <= threshold <= value:
            choices.append((threshold, right.strip()))
    return max(choices, default=(0, "继续加油"), key=lambda row: row[0])[1]


class StudyFilter(CustomFilter):
    def filter(self, event, cfg):
        if not event.get_group_id():
            return False
        command = parse(text(event), CONFIG)
        return bool(command and (command[0] in {"finish", "total"} or mentioned(event)))


class Main(Star):
    def __init__(self, context, config):
        super().__init__(context)
        global CONFIG
        CONFIG = config
        self.config = config
        folder = (
            Path(__file__).resolve().parents[2]
            / "plugin_data"
            / "astrbot_plugin_liflag"
        )
        folder.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(folder / "study.sqlite3")
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS sessions(id INTEGER PRIMARY KEY, scope TEXT, uid TEXT,
          name TEXT, subject TEXT, start REAL, planned INTEGER, end REAL, reminded INTEGER DEFAULT 0);
        CREATE UNIQUE INDEX IF NOT EXISTS one_active ON sessions(scope,uid) WHERE end IS NULL;
        """)
        self.lock = asyncio.Lock()
        self.worker = None

    async def initialize(self):
        self.worker = asyncio.create_task(self.reminders())

    async def terminate(self):
        if self.worker:
            self.worker.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.worker
        self.db.close()

    async def remind_once(self, now):
        async with self.lock:
            delay = max(0, int(self.config.get("remind_after_minutes", 10)))
            rows = self.db.execute(
                "SELECT * FROM sessions WHERE end IS NULL AND reminded=0"
            ).fetchall()
            for row in rows:
                if now < row["start"] + (row["planned"] + delay) * 60:
                    continue
                message = render(
                    self.config["reminder_text"],
                    name=row["name"],
                    subject=row["subject"],
                    minutes=row["planned"],
                    overdue=display(minutes(now - row["start"] - row["planned"] * 60)),
                )
                try:
                    sent = await self.context.send_message(
                        row["scope"], MessageChain([At(qq=row["uid"]), Plain(message)])
                    )
                    if sent is False:
                        continue
                except Exception as exc:  # noqa: BLE001
                    logger.warning("立flag提醒发送失败，将重试: %s", exc)
                    continue
                self.db.execute(
                    "UPDATE sessions SET reminded=1 WHERE id=?", (row["id"],)
                )
                self.db.commit()

    async def reminders(self):
        while True:
            try:
                await self.remind_once(time.time())
            except Exception as exc:  # noqa: BLE001
                logger.exception("立flag定时检查失败: %s", exc)
            await asyncio.sleep(10)

    def seconds(self, scope, uid, start, end, now):
        rows = self.db.execute(
            "SELECT start,end FROM sessions WHERE scope=? AND uid=?", (scope, uid)
        )
        return sum(
            max(
                0,
                min(row["end"] if row["end"] is not None else now, end)
                - max(row["start"], start),
            )
            for row in rows
        )

    async def resolve(self, event, target):
        if not target:
            return str(event.get_sender_id()), event.get_sender_name()
        rows = self.db.execute(
            "SELECT uid,name FROM sessions WHERE scope=? ORDER BY id DESC",
            (event.unified_msg_origin,),
        ).fetchall()
        names = {}
        for row in rows:
            names.setdefault(row["uid"], row["name"])
        candidates = {uid: name for uid, name in names.items() if target in {uid, name}}
        call = getattr(getattr(event, "bot", None), "call_action", None)
        if callable(call):
            try:
                members = await call(
                    "get_group_member_list", group_id=int(event.get_group_id())
                )
                candidates = {
                    str(m["user_id"]): str(
                        m.get("card") or m.get("nickname") or m["user_id"]
                    )
                    for m in members
                    if target
                    in {
                        str(m["user_id"]),
                        str(m.get("card", "")),
                        str(m.get("nickname", "")),
                    }
                }
            except Exception as exc:  # noqa: BLE001
                logger.debug("立flag查询群成员失败，使用已有记录: %s", exc)
        if len(candidates) != 1:
            return None
        return next(iter(candidates.items()))

    @filter.custom_filter(StudyFilter, priority=maxsize)
    async def handle(self, event):
        command = parse(text(event), self.config)
        if not command:
            return
        event.stop_event()
        kind, payload = command
        scope, uid, name = (
            event.unified_msg_origin,
            str(event.get_sender_id()),
            event.get_sender_name(),
        )
        now = time.time()
        async with self.lock:
            if kind == "start":
                subject, count = payload
                if not subject or len(subject) > 100 or not 1 <= count <= 10080:
                    answer = "请输入学习内容和 1～10080 分钟，例如：我要学习英语20分钟"
                elif self.db.execute(
                    "SELECT 1 FROM sessions WHERE scope=? AND uid=? AND end IS NULL",
                    (scope, uid),
                ).fetchone():
                    answer = "你还有一项学习正在计时，先说学完了再开始新的吧！"
                else:
                    self.db.execute(
                        "INSERT INTO sessions(scope,uid,name,subject,start,planned) VALUES(?,?,?,?,?,?)",
                        (scope, uid, name, subject, now, count),
                    )
                    self.db.commit()
                    answer = render(
                        self.config["start_text"],
                        name=name,
                        subject=subject,
                        minutes=count,
                    )
            elif kind == "finish":
                row = self.db.execute(
                    "SELECT * FROM sessions WHERE scope=? AND uid=? AND end IS NULL",
                    (scope, uid),
                ).fetchone()
                if not row:
                    answer = "你还没有开始学习计时哦！"
                else:
                    self.db.execute(
                        "UPDATE sessions SET end=? WHERE id=?", (now, row["id"])
                    )
                    self.db.commit()
                    answer = render(
                        self.config["finish_text"],
                        name=name,
                        subject=row["subject"],
                        minutes=display(minutes(now - row["start"])),
                    )
            else:
                person = await self.resolve(event, payload)
                if not person:
                    answer = "没有找到唯一匹配的群成员，请使用 QQ 号查询（同名也用 QQ 号区分）。"
                else:
                    uid, name = person
                    today = datetime.fromtimestamp(now, TZ).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    if kind == "day":
                        value = minutes(
                            self.seconds(
                                scope,
                                uid,
                                today.timestamp(),
                                (today + timedelta(days=1)).timestamp(),
                                now,
                            )
                        )
                        praise = (
                            self.config["day_zero"]
                            if value == 0
                            else self.config["day_high"]
                            if value > 15
                            else self.config["day_low"]
                        )
                        answer = render(
                            self.config["day_text"],
                            name=name,
                            minutes=display(value),
                            praise=praise,
                        )
                    elif kind == "total":
                        value = minutes(self.seconds(scope, uid, 0, now, now))
                        answer = render(
                            self.config["total_text"],
                            name=name,
                            minutes=display(value),
                            praise=encouragement(value, self.config["total_rules"]),
                        )
                    else:
                        monday = today - timedelta(days=today.weekday())
                        days = []
                        total = 0
                        for offset in range(7):
                            day = monday + timedelta(days=offset)
                            sec = self.seconds(
                                scope,
                                uid,
                                day.timestamp(),
                                (day + timedelta(days=1)).timestamp(),
                                now,
                            )
                            total += sec
                            days.append(
                                render(
                                    self.config["week_day_text"],
                                    month=day.month,
                                    day=day.day,
                                    weekday="一二三四五六日"[offset],
                                    minutes=display(minutes(sec)),
                                )
                            )
                        answer = render(
                            self.config["week_text"],
                            name=name,
                            year=today.year,
                            month=today.month,
                            day=today.day,
                            days="\n\n".join(days),
                            minutes=display(minutes(total)),
                        )
        await event.send(event.plain_result(answer))
