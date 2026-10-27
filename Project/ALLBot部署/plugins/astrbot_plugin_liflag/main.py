"""Persistent group study timers with keyword grouping and configurable summaries."""

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
from astrbot.api.web import error_response, json_response, request

TZ = timezone(timedelta(hours=8))
CONFIG = {}


def text(event):
    return "".join(c.text for c in event.get_messages() if isinstance(c, Plain)).strip()


def parse(value, cfg):
    """Parse message text into command type and payload."""
    value = value.strip()

    # Start command
    prefix = str(cfg.get("start_word", "我要学习"))
    match = re.fullmatch(re.escape(prefix) + r"(.+?)\s*(\d+)分钟", value)
    if match:
        return "start", (match[1].strip(), int(match[2]))

    # Finish command
    if re.fullmatch(re.escape(str(cfg.get("finish_word", "学完了"))), value):
        return "finish", ""

    # Pause command
    pause_words = str(cfg.get("pause_words", "暂停学习|暂停"))
    for pw in pause_words.replace("\n", "|").split("|"):
        pw = pw.strip()
        if pw and re.fullmatch(re.escape(pw), value):
            return "pause", ""

    # Resume command
    resume_words = str(cfg.get("resume_words", "继续学习|继续"))
    for rw in resume_words.replace("\n", "|").split("|"):
        rw = rw.strip()
        if rw and re.fullmatch(re.escape(rw), value):
            return "resume", ""

    # Quit command
    quit_words = str(cfg.get("quit_words", "不学了|放弃"))
    for qw in quit_words.replace("\n", "|").split("|"):
        qw = qw.strip()
        if qw and re.fullmatch(re.escape(qw), value):
            return "quit", ""

    # Rest response (only numbers 5/15/30)
    if re.fullmatch(r"(5|15|30)", value):
        return "rest_reply", int(value)

    # Query commands
    for kind, default in [
        ("day", "今日学习时长"),
        ("week", "本周学习时长"),
        ("total", "总学习时长"),
    ]:
        word = str(cfg.get(kind + "_word", default))
        if re.fullmatch(re.escape(word) + r"(\s+.+)?", value):
            return kind, value[len(word):].strip()

    # Guide command
    guide_words = str(cfg.get("guide_words", "打卡说明|学习说明|打卡帮助"))
    for gw in guide_words.replace("\n", "|").split("|"):
        gw = gw.strip()
        if gw and re.fullmatch(re.escape(gw), value):
            return "guide", ""

    # Admin: rename skill
    rename_words = str(cfg.get("rename_words", "修改技能|改技能"))
    for rw in rename_words.replace("\n", "|").split("|"):
        rw = rw.strip()
        if rw:
            match = re.fullmatch(re.escape(rw) + r"\s+(.+?)改为(.+)", value)
            if match:
                return "rename", (match[1].strip(), match[2].strip())

    # Admin: adjust today duration
    adjust_words = str(cfg.get("adjust_words", "修改今日时长|改今日时长"))
    for aw in adjust_words.replace("\n", "|").split("|"):
        aw = aw.strip()
        if aw:
            match = re.fullmatch(re.escape(aw) + r"\s+(.+?)\s+(\d+)分钟", value)
            if match:
                return "adjust", (match[1].strip(), int(match[2]))

    return None


def render(template, **values):
    for key, value in values.items():
        template = template.replace("{" + key + "}", str(value))
    return template


def minutes_display(seconds):
    return f"{round(max(0, seconds) / 60, 1):g}"


def normalize_keyword(keyword, alias_map):
    """Normalize keyword using alias map."""
    return alias_map.get(keyword.strip(), keyword.strip())


def parse_alias_config(config_text):
    """Parse keyword_alias config into dict."""
    alias_map = {}
    for line in str(config_text).splitlines():
        line = line.strip()
        if "=>" in line:
            left, right = line.split("=>", 1)
            alias_map[left.strip()] = right.strip()
    return alias_map


class StudyFilter(CustomFilter):
    def filter(self, event, cfg):
        if not event.get_group_id():
            return False
        command = parse(text(event), CONFIG)
        return bool(command)


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
        self._migrate_db()
        self.lock = asyncio.Lock()
        self.worker = None

    def _migrate_db(self):
        """Create tables and migrate schema if needed."""
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS sessions(
            id INTEGER PRIMARY KEY,
            scope TEXT,
            uid TEXT,
            name TEXT,
            subject TEXT,
            start REAL,
            planned INTEGER,
            end REAL,
            reminded INTEGER DEFAULT 0
        );
        CREATE UNIQUE INDEX IF NOT EXISTS one_active ON sessions(scope,uid) WHERE end IS NULL;
        """)

        # Check if duration and counted columns exist
        cols = {row[1] for row in self.db.execute("PRAGMA table_info(sessions)")}
        if "duration" not in cols:
            self.db.execute("ALTER TABLE sessions ADD COLUMN duration INTEGER")
        if "counted" not in cols:
            self.db.execute("ALTER TABLE sessions ADD COLUMN counted INTEGER DEFAULT 1")
        if "paused" not in cols:
            self.db.execute("ALTER TABLE sessions ADD COLUMN paused INTEGER DEFAULT 0")
        if "paused_at" not in cols:
            self.db.execute("ALTER TABLE sessions ADD COLUMN paused_at REAL")
        if "pause_total" not in cols:
            self.db.execute("ALTER TABLE sessions ADD COLUMN pause_total REAL DEFAULT 0")
        if "resting" not in cols:
            self.db.execute("ALTER TABLE sessions ADD COLUMN resting INTEGER DEFAULT 0")
        if "rest_until" not in cols:
            self.db.execute("ALTER TABLE sessions ADD COLUMN rest_until REAL")
        self.db.commit()

    async def initialize(self):
        self.worker = asyncio.create_task(self.reminders())
        # Register Web API routes
        self.context.register_web_api(
            "/astrbot_plugin_liflag/config",
            self.api_get_config,
            ["GET"],
            "学习打卡配置读取"
        )
        self.context.register_web_api(
            "/astrbot_plugin_liflag/config",
            self.api_save_config,
            ["POST"],
            "学习打卡配置保存"
        )

    async def api_get_config(self):
        """Get current plugin config."""
        try:
            return json_response(self.config)
        except Exception as e:
            logger.error(f"读取配置失败: {e}")
            return error_response(f"读取配置失败: {str(e)}", status_code=500)

    async def api_save_config(self):
        """Save plugin config."""
        try:
            data = await request.json()
            # Update config
            self.config.update(data)
            # Save to file
            await asyncio.to_thread(self.config.save_config)
            return json_response({"success": True, "message": "配置已保存"})
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return error_response(f"保存配置失败: {str(e)}", status_code=400)

    async def terminate(self):
        if self.worker:
            self.worker.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.worker
        self.db.close()

    async def remind_once(self, now):
        """Check for hard stop (180min) and overdue reminders."""
        async with self.lock:
            # Auto-end expired rest sessions
            rest_rows = self.db.execute(
                "SELECT * FROM sessions WHERE resting=1 AND rest_until <= ?",
                (now,)
            ).fetchall()
            for rest_row in rest_rows:
                self.db.execute(
                    "UPDATE sessions SET end=?, duration=?, resting=0 WHERE id=?",
                    (rest_row["rest_until"], int(rest_row["rest_until"] - rest_row["start"]), rest_row["id"])
                )
                # Send rest end message
                try:
                    message = str(self.config.get("rest_end_text", "休息完毕，可以继续学习啦！"))
                    await self.context.send_message(
                        rest_row["scope"],
                        MessageChain([At(qq=rest_row["uid"]), Plain(" " + message)])
                    )
                except Exception as exc:
                    logger.warning("休息结束提示发送失败: %s", exc)

            if rest_rows:
                self.db.commit()

            # Clean up expired REST_ASK states (older than 5 minutes)
            self.db.execute(
                "DELETE FROM sessions WHERE resting=2 AND subject='REST_ASK' AND start < ?",
                (now - 300,)
            )
            self.db.commit()

            max_minutes = int(self.config.get("max_minutes", 180))
            delay = max(0, int(self.config.get("remind_after_minutes", 10)))

            rows = self.db.execute(
                "SELECT * FROM sessions WHERE end IS NULL AND resting=0"
            ).fetchall()

            for row in rows:
                # Calculate elapsed time excluding pause duration
                pause_total = row["pause_total"] or 0
                if row["paused"]:
                    # Currently paused, add current pause duration
                    pause_total += (now - row["paused_at"])

                elapsed = now - row["start"] - pause_total

                # Skip checks if paused
                if row["paused"]:
                    continue

                # Hard stop at max_minutes
                if elapsed >= max_minutes * 60:
                    self.db.execute(
                        "UPDATE sessions SET end=?, duration=?, counted=1 WHERE id=?",
                        (row["start"] + max_minutes * 60, max_minutes * 60, row["id"])
                    )
                    self.db.commit()

                    message = str(self.config.get(
                        "hard_stop_text",
                        "已经到{max_minutes}分钟时长上限了哦！快去休息一下吧！"
                    )).replace("{max_minutes}", str(max_minutes))

                    try:
                        await self.context.send_message(
                            row["scope"],
                            MessageChain([At(qq=row["uid"]), Plain(" " + message)])
                        )
                    except Exception as exc:
                        logger.warning("学习打卡硬停提示发送失败: %s", exc)
                    continue

                # Overdue reminder
                if row["reminded"] == 0 and elapsed >= (row["planned"] + delay) * 60:
                    message = render(
                        self.config.get("reminder_text", "{name}，{subject}已经学了{overdue}分钟超时啦！"),
                        name=row["name"],
                        subject=row["subject"],
                        minutes=row["planned"],
                        overdue=minutes_display(elapsed - row["planned"] * 60),
                    )
                    try:
                        sent = await self.context.send_message(
                            row["scope"], MessageChain([At(qq=row["uid"]), Plain(" " + message)])
                        )
                        if sent is not False:
                            self.db.execute(
                                "UPDATE sessions SET reminded=1 WHERE id=?", (row["id"],)
                            )
                            self.db.commit()
                    except Exception as exc:
                        logger.warning("学习打卡提醒发送失败: %s", exc)

    async def reminders(self):
        while True:
            try:
                await self.remind_once(time.time())
            except Exception as exc:
                logger.exception("学习打卡定时检查失败: %s", exc)
            await asyncio.sleep(10)

    def get_keyword_stats(self, scope, uid, start_ts, end_ts, now, alias_map):
        """Get keyword-grouped statistics for a time range."""
        rows = self.db.execute(
            """SELECT subject, start, end, duration, counted
               FROM sessions
               WHERE scope=? AND uid=? AND counted=1""",
            (scope, uid)
        ).fetchall()

        stats = {}
        for row in rows:
            # Calculate effective seconds in range
            row_start = max(row["start"], start_ts)
            row_end = min(row["end"] if row["end"] else now, end_ts)
            if row_end <= row_start:
                continue

            seconds = row_end - row_start
            normalized = normalize_keyword(row["subject"], alias_map)
            stats[normalized] = stats.get(normalized, 0) + seconds

        return stats

    def seconds_total(self, scope, uid, start_ts, end_ts, now):
        """Get total seconds in range (for week total, etc.)."""
        rows = self.db.execute(
            """SELECT start, end, counted
               FROM sessions
               WHERE scope=? AND uid=? AND counted=1""",
            (scope, uid)
        ).fetchall()

        total = 0
        for row in rows:
            row_start = max(row["start"], start_ts)
            row_end = min(row["end"] if row["end"] else now, end_ts)
            if row_end > row_start:
                total += row_end - row_start
        return total

    async def resolve(self, event, target):
        """Resolve target to (uid, name), or None if ambiguous."""
        if not target:
            return str(event.get_sender_id()), event.get_sender_name()

        rows = self.db.execute(
            "SELECT uid, name FROM sessions WHERE scope=? ORDER BY id DESC",
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
                    if target in {
                        str(m["user_id"]),
                        str(m.get("card", "")),
                        str(m.get("nickname", "")),
                    }
                }
            except Exception as exc:
                logger.debug("学习打卡查询群成员失败: %s", exc)

        if len(candidates) != 1:
            return None
        return next(iter(candidates.items()))

    def is_admin(self, event):
        """Check if sender is admin with exception handling."""
        try:
            platform = self.context.get_using_platform()
            if not platform:
                return False
            admin_ids = platform.get_admin_ids()
            return str(event.get_sender_id()) in admin_ids
        except Exception as e:
            logger.warning(f"is_admin检查失败: {e}")
            return False

    @filter.custom_filter(StudyFilter, priority=maxsize)
    async def handle(self, event):
        command = parse(text(event), self.config)
        if not command:
            return
        event.stop_event()

        kind, payload = command
        scope = event.unified_msg_origin
        uid = str(event.get_sender_id())
        name = event.get_sender_name()
        now = time.time()

        min_minutes = int(self.config.get("min_minutes", 5))
        max_minutes = int(self.config.get("max_minutes", 180))
        alias_map = parse_alias_config(self.config.get("keyword_alias", ""))

        async with self.lock:
            if kind == "start":
                subject, count = payload

                # Check if resting (resting=1 means actually resting, resting=2 is REST_ASK)
                rest_row = self.db.execute(
                    "SELECT * FROM sessions WHERE scope=? AND uid=? AND resting=1",
                    (scope, uid)
                ).fetchone()

                if rest_row and rest_row["rest_until"] > now:
                    remaining = max(0, int((rest_row["rest_until"] - now) / 60))
                    answer = str(self.config.get(
                        "start_resting_text",
                        "你正在休息中，还剩{remaining}分钟，暂时不能开始学习"
                    )).replace("{remaining}", str(remaining))

                # Clear any REST_ASK state when starting new session
                elif self.db.execute(
                    "SELECT 1 FROM sessions WHERE scope=? AND uid=? AND resting=2 AND subject='REST_ASK'",
                    (scope, uid)
                ).fetchone():
                    self.db.execute(
                        "DELETE FROM sessions WHERE scope=? AND uid=? AND resting=2 AND subject='REST_ASK'",
                        (scope, uid)
                    )
                    self.db.commit()
                    # Continue to normal start logic below

                if not answer and (not subject or len(subject) > 100):
                    answer = str(self.config.get(
                        "start_invalid_text",
                        "请输入学习内容和分钟数"
                    ))
                elif not (min_minutes <= count <= max_minutes):
                    answer = str(self.config.get(
                        "start_out_of_range_text",
                        "时长必须在{min}到{max}分钟之间"
                    )).replace("{min}", str(min_minutes)).replace("{max}", str(max_minutes))
                elif self.db.execute(
                    "SELECT 1 FROM sessions WHERE scope=? AND uid=? AND end IS NULL",
                    (scope, uid),
                ).fetchone():
                    answer = str(self.config.get(
                        "start_already_active_text",
                        "你还有一项学习正在计时，先说学完了再开始新的吧！"
                    ))
                else:
                    self.db.execute(
                        "INSERT INTO sessions(scope,uid,name,subject,start,planned) VALUES(?,?,?,?,?,?)",
                        (scope, uid, name, subject, now, count),
                    )
                    self.db.commit()
                    answer = render(
                        str(self.config.get("start_text", "{name}开始学习{subject}，计划{minutes}分钟")),
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
                    # Silent when no active session (per BRD: avoid noise after removing @)
                    return

                elapsed = now - row["start"]
                if elapsed < min_minutes * 60:
                    # Too short, mark as uncounted
                    self.db.execute(
                        "UPDATE sessions SET end=?, duration=?, counted=0 WHERE id=?",
                        (now, int(elapsed), row["id"])
                    )
                    self.db.commit()
                    answer = str(self.config.get(
                        "finish_too_short_text",
                        "这次不到{min}分钟，将不计入时长，多坚持一下哦！"
                    )).replace("{min}", str(min_minutes))
                else:
                    self.db.execute(
                        "UPDATE sessions SET end=?, duration=?, counted=1 WHERE id=?",
                        (now, int(elapsed), row["id"])
                    )
                    self.db.commit()

                    # Mark user as in REST_ASK state
                    self.db.execute(
                        "INSERT INTO sessions(scope,uid,name,subject,start,planned,resting,rest_until,counted) VALUES(?,?,?,?,?,?,2,?,0)",
                        (scope, uid, name, "REST_ASK", now, 0, now)
                    )
                    self.db.commit()

                    finish_msg = render(
                        str(self.config.get("finish_text", "{name}完成了{subject}，学习了{minutes}分钟")),
                        name=name,
                        subject=row["subject"],
                        minutes=minutes_display(elapsed),
                    )
                    rest_ask_msg = str(self.config.get("rest_ask_text", "要休息一下吗？回复5、15或30分钟"))
                    answer = finish_msg + "\n" + rest_ask_msg

            elif kind == "pause":
                row = self.db.execute(
                    "SELECT * FROM sessions WHERE scope=? AND uid=? AND end IS NULL",
                    (scope, uid),
                ).fetchone()
                if not row:
                    answer = str(self.config.get("pause_no_session_text", "当前没有正在进行的学习"))
                elif row["paused"]:
                    answer = str(self.config.get("pause_already_text", "学习已经处于暂停状态"))
                else:
                    self.db.execute(
                        "UPDATE sessions SET paused=1, paused_at=? WHERE id=?",
                        (now, row["id"])
                    )
                    self.db.commit()
                    answer = render(
                        str(self.config.get("pause_text", "{name}暂停了{subject}的学习")),
                        name=name,
                        subject=row["subject"]
                    )

            elif kind == "resume":
                row = self.db.execute(
                    "SELECT * FROM sessions WHERE scope=? AND uid=? AND end IS NULL",
                    (scope, uid),
                ).fetchone()
                if not row:
                    answer = str(self.config.get("resume_no_session_text", "当前没有正在进行的学习"))
                elif not row["paused"]:
                    answer = str(self.config.get("resume_not_paused_text", "学习并未暂停"))
                else:
                    pause_duration = now - row["paused_at"]
                    new_pause_total = (row["pause_total"] or 0) + pause_duration
                    self.db.execute(
                        "UPDATE sessions SET paused=0, paused_at=NULL, pause_total=? WHERE id=?",
                        (new_pause_total, row["id"])
                    )
                    self.db.commit()
                    answer = render(
                        str(self.config.get("resume_text", "{name}继续学习{subject}")),
                        name=name,
                        subject=row["subject"]
                    )

            elif kind == "quit":
                row = self.db.execute(
                    "SELECT * FROM sessions WHERE scope=? AND uid=? AND end IS NULL",
                    (scope, uid),
                ).fetchone()
                if not row:
                    answer = str(self.config.get("quit_no_session_text", "当前没有正在进行的学习"))
                else:
                    # Mark as ended with counted=0
                    self.db.execute(
                        "UPDATE sessions SET end=?, duration=0, counted=0 WHERE id=?",
                        (now, row["id"])
                    )
                    self.db.commit()
                    answer = render(
                        str(self.config.get("quit_text", "{name}放弃了{subject}的学习")),
                        name=name,
                        subject=row["subject"]
                    )

            elif kind == "rest_reply":
                rest_minutes = payload
                # Check if in REST_ASK state
                ask_row = self.db.execute(
                    "SELECT * FROM sessions WHERE scope=? AND uid=? AND resting=2 AND subject='REST_ASK'",
                    (scope, uid)
                ).fetchone()

                if not ask_row:
                    # Not in REST_ASK state, ignore
                    return

                # Remove REST_ASK marker
                self.db.execute(
                    "DELETE FROM sessions WHERE id=?",
                    (ask_row["id"],)
                )

                # Start rest
                rest_until = now + rest_minutes * 60
                self.db.execute(
                    """INSERT INTO sessions(scope,uid,name,subject,start,planned,resting,rest_until,counted)
                       VALUES(?,?,?,?,?,?,1,?,0)""",
                    (scope, uid, name, "休息", now, rest_minutes, rest_until)
                )
                self.db.commit()
                answer = str(self.config.get(
                    "rest_start_text",
                    "好的，休息{minutes}分钟，期间不能开始新的学习"
                )).replace("{minutes}", str(rest_minutes))

            elif kind == "guide":
                header = str(self.config.get("guide_header", ""))
                body = str(self.config.get("guide_text", "打卡说明\n..."))
                answer = (header + "\n" + body if header else body).strip()

            elif kind == "rename":
                if not self.is_admin(event):
                    answer = str(self.config.get(
                        "admin_denied_text",
                        "只有管理员可以使用该命令"
                    ))
                else:
                    old_kw, new_kw = payload
                    # Add to alias map
                    current = str(self.config.get("keyword_alias", ""))
                    new_line = f"{old_kw} => {new_kw}"
                    updated = (current + "\n" + new_line if current else new_line).strip()
                    self.config["keyword_alias"] = updated
                    # Note: config changes don't auto-persist in AstrBot, but user can save in WebUI
                    answer = str(self.config.get(
                        "rename_success_text",
                        "已将{old}映射为{new}"
                    )).replace("{old}", old_kw).replace("{new}", new_kw)

            elif kind == "adjust":
                if not self.is_admin(event):
                    answer = str(self.config.get(
                        "admin_denied_text",
                        "只有管理员可以使用该命令"
                    ))
                else:
                    subject, add_minutes = payload
                    normalized = normalize_keyword(subject, alias_map)
                    today = datetime.fromtimestamp(now, TZ).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    # Insert a manual entry for today
                    self.db.execute(
                        """INSERT INTO sessions(scope,uid,name,subject,start,planned,end,duration,counted)
                           VALUES(?,?,?,?,?,?,?,?,1)""",
                        (scope, uid, name, normalized, today.timestamp(), add_minutes,
                         today.timestamp() + add_minutes * 60, add_minutes * 60)
                    )
                    self.db.commit()
                    answer = str(self.config.get(
                        "adjust_success_text",
                        "已为{subject}添加{minutes}分钟"
                    )).replace("{subject}", normalized).replace("{minutes}", str(add_minutes))

            else:  # day / week / total
                person = await self.resolve(event, payload)
                if not person:
                    answer = str(self.config.get(
                        "resolve_failed_text",
                        "没有找到唯一匹配的群成员"
                    ))
                else:
                    uid, name = person
                    today = datetime.fromtimestamp(now, TZ).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )

                    if kind == "day":
                        stats = self.get_keyword_stats(
                            scope, uid, today.timestamp(),
                            (today + timedelta(days=1)).timestamp(), now, alias_map
                        )
                        if not stats:
                            answer = str(self.config.get(
                                "day_empty_text",
                                "今天还没学习哦，先来一个？"
                            ))
                        else:
                            header = str(self.config.get("day_header", "今天{name}学习了："))
                            line_template = str(self.config.get("day_line", "{subject} {minutes}分钟！"))
                            lines = [
                                line_template.replace("{subject}", kw).replace("{minutes}", minutes_display(sec))
                                for kw, sec in sorted(stats.items(), key=lambda x: -x[1])
                            ]
                            answer = render(header, name=name) + "\n" + "\n".join(lines)

                    elif kind == "total":
                        stats = self.get_keyword_stats(
                            scope, uid, 0, now, now, alias_map
                        )
                        total_sec = sum(stats.values())

                        if not stats:
                            answer = str(self.config.get(
                                "total_empty_text",
                                "还没有学习记录哦"
                            ))
                        else:
                            header = str(self.config.get(
                                "total_header",
                                "你的总学习时长为：{minutes}分钟，数据如下："
                            ))
                            line_template = str(self.config.get(
                                "total_line",
                                "一共学习了{subject} {minutes}分钟！"
                            ))
                            limit = int(self.config.get("total_limit", 20))

                            # Sort by minutes desc, then by first occurrence
                            sorted_items = sorted(stats.items(), key=lambda x: -x[1])[:limit]
                            lines = [
                                line_template.replace("{subject}", kw).replace("{minutes}", minutes_display(sec))
                                for kw, sec in sorted_items
                            ]
                            answer = render(header, minutes=minutes_display(total_sec)) + "\n" + "\n".join(lines)

                    else:  # week
                        monday = today - timedelta(days=today.weekday())
                        days = []
                        total = 0
                        for offset in range(7):
                            day = monday + timedelta(days=offset)
                            sec = self.seconds_total(
                                scope, uid, day.timestamp(),
                                (day + timedelta(days=1)).timestamp(), now
                            )
                            total += sec
                            days.append(
                                render(
                                    str(self.config.get("week_day_text", "{month}月{day}日 周{weekday}：{minutes}分钟")),
                                    month=day.month,
                                    day=day.day,
                                    weekday="一二三四五六日"[offset],
                                    minutes=minutes_display(sec),
                                )
                            )
                        answer = render(
                            str(self.config.get("week_text", "{name}本周学习时长：\n{days}\n\n本周共{minutes}分钟")),
                            name=name,
                            year=today.year,
                            month=today.month,
                            day=today.day,
                            days="\n".join(days),
                            minutes=minutes_display(total),
                        )

        await event.send(event.plain_result(answer))
