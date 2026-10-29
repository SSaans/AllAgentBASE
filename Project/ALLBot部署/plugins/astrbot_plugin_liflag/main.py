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
    # 带触发词但缺科目或分钟数：回复格式提示，不静默
    if value.startswith(prefix):
        return "start_invalid", ""

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

    # Admin guide command - 简单处理"管理员功能"请求
    if value in ("管理员功能", "管理员帮助", "管理功能"):
        return "admin_guide", ""

    # Admin: rename skill
    rename_words = str(cfg.get("rename_words", "修改技能|改技能"))
    for rw in rename_words.replace("\n", "|").split("|"):
        rw = rw.strip()
        if rw:
            # BRD: ^/?\s*修改技能\s+(.+?)\s*改为\s*(.+?)\s*$
            pattern = r"^/?\s*" + re.escape(rw) + r"\s+(.+?)\s*改为\s*(.+?)\s*$"
            match = re.match(pattern, value)
            if match:
                return "rename", (match.group(1).strip(), match.group(2).strip())

    # Admin: adjust today duration
    adjust_words = str(cfg.get("adjust_words", "修改今日时长|改今日时长"))
    for aw in adjust_words.replace("\n", "|").split("|"):
        aw = aw.strip()
        if aw:
            # 同时支持短版本"改"和长版本"修改"
            pattern = r"^/?\s*" + re.escape(aw) + r"\s*(.+?)\s*(\d+)\s*分钟?\s*$"
            match = re.match(pattern, value)
            if match:
                subject = match.group(1).strip()
                minutes = int(match.group(2))
                return "adjust", (subject, minutes)

    # Admin: adjust week duration
    adjust_week_words = str(cfg.get("adjust_week_words", "修改本周时长|改本周时长"))
    for aw in adjust_week_words.replace("\n", "|").split("|"):
        aw = aw.strip()
        if aw:
            pattern = r"^/?\s*" + re.escape(aw) + r"\s*(.+?)\s*(\d+)\s*分钟?\s*$"
            match = re.match(pattern, value)
            if match:
                subject = match.group(1).strip()
                minutes = int(match.group(2))
                return "adjust_week", (subject, minutes)

    # Admin: adjust total duration
    adjust_total_words = str(cfg.get("adjust_total_words", "修改总时长|改总时长"))
    for aw in adjust_total_words.replace("\n", "|").split("|"):
        aw = aw.strip()
        if aw:
            pattern = r"^/?\s*" + re.escape(aw) + r"\s*(.+?)\s*(\d+)\s*分钟?\s*$"
            match = re.match(pattern, value)
            if match:
                subject = match.group(1).strip()
                minutes = int(match.group(2))
                return "adjust_total", (subject, minutes)

    # Admin: clear data
    clear_words = str(cfg.get("clear_words", "清空学习数据|清空数据"))
    for cw in clear_words.replace("\n", "|").split("|"):
        cw = cw.strip()
        if cw:
            # 可以"清空学习数据 法语"、"清空学习数据法语"（清单个）或"清空学习数据"（清所有）
            pattern = r"^/?\s*" + re.escape(cw) + r"\s*(.*?)\s*$"
            match = re.match(pattern, value)
            if match:
                subject = match.group(1).strip() if match.group(1) else None
                return "clear", subject

    # Admin management commands
    # Add admin
    add_admin_words = str(cfg.get("add_admin_words", "添加管理员"))
    for aw in add_admin_words.replace("\n", "|").split("|"):
        aw = aw.strip()
        if aw:
            # 支持有空格和无空格：「添加管理员 123456」或「添加管理员123456」
            pattern = r"^/?\s*" + re.escape(aw) + r"\s*(\d+)\s*$"
            match = re.match(pattern, value)
            if match:
                return "add_admin", match.group(1)

    # Remove admin
    remove_admin_words = str(cfg.get("remove_admin_words", "删除管理员"))
    for rw in remove_admin_words.replace("\n", "|").split("|"):
        rw = rw.strip()
        if rw:
            pattern = r"^/?\s*" + re.escape(rw) + r"\s*(\d+)\s*$"
            match = re.match(pattern, value)
            if match:
                return "remove_admin", match.group(1)

    # List admins
    list_admin_words = str(cfg.get("list_admin_words", "管理员名单"))
    for lw in list_admin_words.replace("\n", "|").split("|"):
        lw = lw.strip()
        if lw and re.match(r"^/?\s*" + re.escape(lw) + r"\s*$", value):
            return "list_admins", None

    return None


def render(template, **values):
    for key, value in values.items():
        template = template.replace("{" + key + "}", str(value))
    return template


def minutes_display(seconds):
    """将秒数转换为分钟显示，大于 1000 时添加逗号分隔"""
    minutes = round(max(0, seconds) / 60, 1)
    if minutes == int(minutes):
        minutes = int(minutes)

    # 格式化时总是先转成字符串，然后按逗号规则处理
    if isinstance(minutes, int):
        if minutes >= 1000:
            return f"{minutes:,}"
        else:
            return str(minutes)
    else:
        # 浮点数情况
        minutes_str = f"{minutes:.1f}"
        int_part_str = str(int(minutes))
        if int(minutes) >= 1000:
            # 给整数部分加逗号
            int_part_with_comma = f"{int(minutes):,}"
            decimal_part = minutes_str.split('.')[1]
            return f"{int_part_with_comma}.{decimal_part}"
        else:
            return minutes_str


def normalize_keyword(keyword, alias_map):
    """Normalize keyword using alias map."""
    result = keyword.strip()
    # Follow alias chain (max 10 hops to prevent infinite loops)
    for _ in range(10):
        if result in alias_map:
            result = alias_map[result]
        else:
            break
    return result


def parse_alias_config(config_text):
    """Parse keyword_alias config into dict."""
    alias_map = {}
    for line in str(config_text).splitlines():
        line = line.strip()
        if "=>" in line:
            left, right = line.split("=>", 1)
            alias_map[left.strip()] = right.strip()
    return alias_map


def load_alias_map(db, config_text):
    """Load alias map from both config and database (database takes priority)."""
    alias_map = parse_alias_config(config_text)

    # Load from database (overrides config)
    try:
        rows = db.execute("SELECT alias, canonical FROM aliases").fetchall()
        for row in rows:
            alias_map[row["alias"]] = row["canonical"]
    except Exception:
        pass  # Table might not exist yet

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
        # Cache for pending full clear confirmations: {(scope, uid): timestamp}
        self.pending_clear_all = {}

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

        CREATE TABLE IF NOT EXISTS aliases(
            alias TEXT PRIMARY KEY,
            canonical TEXT NOT NULL,
            updated REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS adjustments(
            id INTEGER PRIMARY KEY,
            scope TEXT NOT NULL,
            uid TEXT NOT NULL,
            date TEXT NOT NULL,
            subject TEXT NOT NULL,
            seconds INTEGER NOT NULL,
            created REAL NOT NULL,
            by_uid TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS admins(
            qq TEXT PRIMARY KEY,
            added_at REAL NOT NULL,
            added_by TEXT NOT NULL
        );
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
        self.context.register_web_api(
            "/astrbot_plugin_liflag/admins",
            self.api_get_admins,
            ["GET"],
            "获取管理员列表"
        )
        self.context.register_web_api(
            "/astrbot_plugin_liflag/admins/add",
            self.api_add_admin,
            ["POST"],
            "添加管理员"
        )
        self.context.register_web_api(
            "/astrbot_plugin_liflag/admins/remove",
            self.api_remove_admin,
            ["POST"],
            "删除管理员"
        )
        self.context.register_web_api(
            "/astrbot_plugin_liflag/stats",
            self.api_get_stats,
            ["GET"],
            "学习数据总览"
        )
        self.context.register_web_api(
            "/astrbot_plugin_liflag/stats/set",
            self.api_set_stat,
            ["POST"],
            "修改学习数据"
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

    async def api_get_admins(self):
        """Get admin list."""
        try:
            super_admins_str = str(self.config.get("super_admins", "2403232967"))
            super_admins = [qq.strip() for qq in super_admins_str.split("\n") if qq.strip()]
            rows = self.db.execute("SELECT qq, added_at FROM admins ORDER BY added_at").fetchall()
            admins = [{"qq": row["qq"], "added_at": row["added_at"]} for row in rows]
            return json_response({
                "super_admins": super_admins,
                "admins": admins
            })
        except Exception as e:
            logger.error(f"获取管理员列表失败: {e}")
            return error_response(f"获取管理员列表失败: {str(e)}", status_code=500)

    async def api_add_admin(self):
        """Add admin via web panel."""
        try:
            data = await request.json()
            qq = str(data.get("qq", "")).strip()
            if not qq or not qq.isdigit():
                return error_response("QQ号格式错误", status_code=400)

            super_admins_str = str(self.config.get("super_admins", "2403232967"))
            super_admins = [q.strip() for q in super_admins_str.split("\n") if q.strip()]
            if qq in super_admins:
                return error_response("超级管理员无需添加", status_code=400)

            existing = self.db.execute("SELECT qq FROM admins WHERE qq=?", (qq,)).fetchone()
            if existing:
                return error_response("该QQ已是管理员", status_code=400)

            count = self.db.execute("SELECT COUNT(*) as cnt FROM admins").fetchone()["cnt"]
            limit = int(self.config.get("admin_limit", 20))
            if count >= limit:
                return error_response(f"管理员数量已达上限({limit})", status_code=400)

            import time
            self.db.execute(
                "INSERT INTO admins(qq, added_at, added_by) VALUES(?,?,?)",
                (qq, time.time(), "web_panel")
            )
            self.db.commit()
            return json_response({"success": True, "message": f"已添加管理员 {qq}"})
        except Exception as e:
            logger.error(f"添加管理员失败: {e}")
            return error_response(f"添加管理员失败: {str(e)}", status_code=500)

    async def api_remove_admin(self):
        """Remove admin via web panel."""
        try:
            data = await request.json()
            qq = str(data.get("qq", "")).strip()
            if not qq:
                return error_response("QQ号不能为空", status_code=400)

            super_admins_str = str(self.config.get("super_admins", "2403232967"))
            super_admins = [q.strip() for q in super_admins_str.split("\n") if q.strip()]
            if qq in super_admins:
                return error_response("不能删除超级管理员", status_code=400)

            existing = self.db.execute("SELECT qq FROM admins WHERE qq=?", (qq,)).fetchone()
            if not existing:
                return error_response("该QQ不是管理员", status_code=400)

            self.db.execute("DELETE FROM admins WHERE qq=?", (qq,))
            self.db.commit()
            return json_response({"success": True, "message": f"已移除管理员 {qq}"})
        except Exception as e:
            logger.error(f"删除管理员失败: {e}")
            return error_response(f"删除管理员失败: {str(e)}", status_code=500)

    async def api_get_stats(self):
        """数据页总览：三个汇总数 + 按 QQ 号逐人（跨群合成一行）。"""
        try:
            now = time.time()
            tz_now = datetime.fromtimestamp(now, TZ)
            day_start = tz_now.replace(hour=0, minute=0, second=0, microsecond=0)
            monday = day_start - timedelta(days=day_start.weekday())
            today_ts = day_start.timestamp()
            week_ts = monday.timestamp()
            alias_map = load_alias_map(self.db, self.config.get("keyword_alias", ""))

            pairs = set()
            for row in self.db.execute(
                "SELECT DISTINCT scope, uid FROM sessions WHERE counted=1"
            ).fetchall():
                pairs.add((row["scope"], row["uid"]))
            for row in self.db.execute(
                "SELECT DISTINCT scope, uid FROM adjustments"
            ).fetchall():
                pairs.add((row["scope"], row["uid"]))

            users = {}
            for scope, uid in sorted(pairs):
                rec = users.setdefault(uid, {
                    "uid": uid, "name": "",
                    "today": 0, "week": 0, "total": 0,
                    "subjects": {},
                })
                if not rec["name"]:
                    row = self.db.execute(
                        """SELECT name FROM sessions
                           WHERE uid=? AND name IS NOT NULL AND name != ''
                           ORDER BY id DESC LIMIT 1""",
                        (uid,),
                    ).fetchone()
                    if row:
                        rec["name"] = row["name"]

                rec["today"] += self.seconds_total(
                    scope, uid, today_ts, today_ts + 86400, now
                )
                rec["week"] += self.seconds_total(
                    scope, uid, week_ts, week_ts + 7 * 86400, now
                )
                rec["total"] += self.seconds_total(scope, uid, 0, now, now)

                for kw, sec in self.get_keyword_stats(
                    scope, uid, today_ts, today_ts + 86400, now, alias_map
                ).items():
                    slot = rec["subjects"].setdefault(
                        kw, {"today": 0, "week": 0, "total": 0}
                    )
                    slot["today"] += sec
                for kw, sec in self.get_keyword_stats(
                    scope, uid, week_ts, week_ts + 7 * 86400, now, alias_map
                ).items():
                    slot = rec["subjects"].setdefault(
                        kw, {"today": 0, "week": 0, "total": 0}
                    )
                    slot["week"] += sec
                for kw, sec in self.get_keyword_stats(
                    scope, uid, 0, now, now, alias_map
                ).items():
                    slot = rec["subjects"].setdefault(
                        kw, {"today": 0, "week": 0, "total": 0}
                    )
                    slot["total"] += sec

            user_list = sorted(users.values(), key=lambda r: -r["total"])
            summary = {
                "today": sum(r["today"] for r in user_list),
                "week": sum(r["week"] for r in user_list),
                "all": sum(r["total"] for r in user_list),
            }
            return json_response({"summary": summary, "users": user_list})
        except Exception as e:
            logger.error(f"获取学习数据失败: {e}")
            return error_response(f"获取学习数据失败: {str(e)}", status_code=500)

    async def api_set_stat(self):
        """数据页行内改数：把某科目的今日 / 本周 / 总时长设为指定值（不叠加）。"""
        try:
            data = await request.json()
            uid = str(data.get("uid", "")).strip()
            subject = str(data.get("subject", "")).strip()
            values = data.get("values") or {}

            if not uid or not subject:
                return error_response("缺 QQ 号或科目名", status_code=400)

            ranges = {"today": "今日", "week": "本周", "total": "总"}
            parsed = {}
            for key, label in ranges.items():
                text = str(values.get(key, "")).strip()
                if text == "":
                    return error_response(
                        f"{label}时长不能是空白，没有保存", status_code=400
                    )
                try:
                    minutes = int(round(float(text)))
                except (TypeError, ValueError):
                    return error_response(
                        f"{label}时长「{text}」不是数字，没有保存", status_code=400
                    )
                if minutes < 0:
                    return error_response(
                        f"{label}时长不能是负数，没有保存", status_code=400
                    )
                if minutes > 14400:
                    return error_response(
                        f"{label}时长不能超过 14400 分钟（10 天）", status_code=400
                    )
                parsed[key] = minutes

            alias_map = load_alias_map(self.db, self.config.get("keyword_alias", ""))
            now = time.time()
            # today → week → total：week 的合计会算上 today 的记录，
            # 先设 today 再设 week，最终两个数都恰好等于填的值
            for key in ("today", "week", "total"):
                self._set_subject_value(
                    None, uid, key, subject, parsed[key], alias_map, now
                )

            return json_response({"success": True, "message": "已保存"})
        except Exception as e:
            logger.error(f"修改学习数据失败: {e}")
            return error_response(f"修改学习数据失败: {str(e)}", status_code=500)

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

        # Add adjustments from database
        try:
            start_date = datetime.fromtimestamp(start_ts, TZ).strftime("%Y-%m-%d")
            # 窗口是 [start, end)：终点减 1 秒再取日期，避免把次日的记录算进来
            end_date = datetime.fromtimestamp(end_ts - 1, TZ).strftime("%Y-%m-%d")
            adj_rows = self.db.execute(
                """SELECT subject, seconds FROM adjustments
                   WHERE scope=? AND uid=? AND date>=? AND date<=?""",
                (scope, uid, start_date, end_date)
            ).fetchall()
            for adj_row in adj_rows:
                normalized = normalize_keyword(adj_row["subject"], alias_map)
                stats[normalized] = stats.get(normalized, 0) + adj_row["seconds"]
        except Exception:
            pass  # Table might not exist yet

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

        # Add adjustments from database
        try:
            start_date = datetime.fromtimestamp(start_ts, TZ).strftime("%Y-%m-%d")
            # 窗口是 [start, end)：终点减 1 秒再取日期，避免把次日的记录算进来
            end_date = datetime.fromtimestamp(end_ts - 1, TZ).strftime("%Y-%m-%d")
            adj_rows = self.db.execute(
                """SELECT seconds FROM adjustments
                   WHERE scope=? AND uid=? AND date>=? AND date<=?""",
                (scope, uid, start_date, end_date)
            ).fetchall()
            for adj_row in adj_rows:
                total += adj_row["seconds"]
        except Exception:
            pass  # Table might not exist yet

        return total

    def _set_subject_value(self, scope, uid, range_kind, subject, target_minutes, alias_map, now, by_uid="web_panel"):
        """把某科目在某时间范围的时长设为指定值（覆盖语义，不叠加）。

        先清掉该范围内该科目的实际计时记录（sessions），再往 adjustments 插入
        差值，让最终显示值恰好等于目标值。
        scope 为 None 时跨群处理该 uid 的全部记录（数据页入口）。
        range_kind: "today" | "week" | "total"
        返回差值落到的 scope。
        """
        tz_now = datetime.fromtimestamp(now, TZ)
        day_start = tz_now.replace(hour=0, minute=0, second=0, microsecond=0)
        monday = day_start - timedelta(days=day_start.weekday())

        if range_kind == "today":
            win_start = day_start.timestamp()
            win_end = (day_start + timedelta(days=1)).timestamp()
            marker_date = day_start.strftime("%Y-%m-%d")
            adj_lo = adj_hi = marker_date
        elif range_kind == "week":
            win_start = monday.timestamp()
            win_end = (monday + timedelta(days=7)).timestamp()
            marker_date = monday.strftime("%Y-%m-%d")
            adj_lo = marker_date
            adj_hi = (monday + timedelta(days=6)).strftime("%Y-%m-%d")
        else:  # total
            win_start = 0
            win_end = now + 86400
            marker_date = "1970-01-01"
            adj_lo = adj_hi = None

        normalized = normalize_keyword(subject, alias_map)
        scope_sql = "AND scope=?" if scope is not None else ""
        scope_args = (scope,) if scope is not None else ()

        # 归一化后等于目标科目的所有原始写法，窗口内的计时记录一并清掉
        raw_names = [
            row["subject"]
            for row in self.db.execute(
                f"SELECT DISTINCT subject FROM sessions WHERE uid=? {scope_sql}",
                (uid, *scope_args),
            ).fetchall()
            if normalize_keyword(row["subject"], alias_map) == normalized
        ]
        for raw in raw_names:
            self.db.execute(
                f"""DELETE FROM sessions WHERE uid=? AND subject=?
                    AND start>=? AND start<? {scope_sql}""",
                (uid, raw, win_start, win_end, *scope_args),
            )

        # adjustments 现有合计（scope 为 None 时把所有群加在一起）；
        # 按归一化名匹配，改过名的旧记录也计入，保证设为后恰好等于目标值
        if range_kind == "total":
            adj_rows = self.db.execute(
                f"""SELECT subject, seconds FROM adjustments
                    WHERE uid=? {scope_sql}""",
                (uid, *scope_args),
            ).fetchall()
        else:
            adj_rows = self.db.execute(
                f"""SELECT subject, seconds FROM adjustments
                    WHERE uid=? AND date>=? AND date<=? {scope_sql}""",
                (uid, adj_lo, adj_hi, *scope_args),
            ).fetchall()
        existing = sum(
            row["seconds"] for row in adj_rows
            if normalize_keyword(row["subject"], alias_map) == normalized
        )
        delta = int(target_minutes) * 60 - existing

        # 差值落到哪：群命令落当前群；数据页跨群落该号最近活动的群
        if scope is not None:
            delta_scope = scope
        else:
            row = self.db.execute(
                "SELECT scope FROM sessions WHERE uid=? ORDER BY id DESC LIMIT 1",
                (uid,),
            ).fetchone()
            if not row:
                row = self.db.execute(
                    "SELECT scope FROM adjustments WHERE uid=? ORDER BY created DESC LIMIT 1",
                    (uid,),
                ).fetchone()
            delta_scope = row["scope"] if row else ""

        self.db.execute(
            """INSERT INTO adjustments(scope,uid,date,subject,seconds,created,by_uid)
               VALUES(?,?,?,?,?,?,?)""",
            (delta_scope, uid, marker_date, normalized, delta, now, by_uid),
        )
        self.db.commit()
        return delta_scope

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

    def is_super_admin(self, event):
        """Check if sender is super admin."""
        sender_qq = str(event.get_sender_id())
        super_admins_str = str(self.config.get("super_admins", "2403232967"))
        super_admins = [qq.strip() for qq in super_admins_str.split("\n") if qq.strip()]
        return sender_qq in super_admins

    def is_admin(self, event):
        """Check if sender is admin (super admin or in admins table)."""
        sender_qq = str(event.get_sender_id())

        # Super admin always has access
        super_admins_str = str(self.config.get("super_admins", "2403232967"))
        super_admins = [qq.strip() for qq in super_admins_str.split("\n") if qq.strip()]
        if sender_qq in super_admins:
            return True

        # Check admins table
        try:
            row = self.db.execute("SELECT qq FROM admins WHERE qq=?", (sender_qq,)).fetchone()
            return row is not None
        except Exception:
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
        # Build alias map from config + database
        alias_map = load_alias_map(self.db, self.config.get("keyword_alias", ""))

        async with self.lock:
            if kind == "start":
                subject, count = payload
                answer = ""

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

            elif kind == "start_invalid":
                answer = str(self.config.get(
                    "start_invalid_text",
                    "请输入学习内容和分钟数"
                ))

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

            elif kind == "admin_guide":
                if not self.is_admin(event):
                    answer = str(self.config.get(
                        "admin_denied_text",
                        "只有管理员可以使用该命令"
                    ))
                else:
                    body = str(self.config.get("admin_guide_text", "管理员功能说明"))
                    answer = body.strip()

            elif kind == "rename":
                if not self.is_admin(event):
                    answer = str(self.config.get(
                        "admin_denied_text",
                        "只有管理员可以使用该命令"
                    ))
                else:
                    old_kw, new_kw = payload
                    # Build alias map from config + database
                    alias_map = load_alias_map(self.db, self.config.get("keyword_alias", ""))

                    # Normalize both keywords
                    old_normalized = normalize_keyword(old_kw, alias_map)
                    new_normalized = normalize_keyword(new_kw, alias_map)

                    # Flatten: update all aliases pointing to old to point to new
                    self.db.execute(
                        "UPDATE aliases SET canonical=?, updated=? WHERE canonical=?",
                        (new_normalized, now, old_normalized)
                    )
                    # Insert/update the new mapping
                    self.db.execute(
                        "INSERT OR REPLACE INTO aliases(alias, canonical, updated) VALUES(?,?,?)",
                        (old_normalized, new_normalized, now)
                    )
                    self.db.commit()

                    answer = str(self.config.get(
                        "rename_success_text",
                        "已将{old}映射为{new}"
                    )).replace("{old}", old_kw).replace("{new}", new_kw)

            elif kind == "adjust":
                if not self.is_admin(event):
                    answer = str(self.config.get(
                        "adjust_denied_text",
                        "如果要改时长、请联系管理员哦！"
                    ))
                else:
                    subject, set_minutes = payload
                    # 检查上限
                    if set_minutes > 14400:
                        answer = f"改不了，一次最多改 14400 分钟（10 天）"
                    else:
                        alias_map = load_alias_map(self.db, self.config.get("keyword_alias", ""))
                        normalized = normalize_keyword(subject, alias_map)
                        self._set_subject_value(
                            scope, uid, "today", subject, set_minutes,
                            alias_map, now, by_uid=str(event.get_sender_id())
                        )
                        answer = f"修改{normalized}今日学习时长为{set_minutes}分钟"

            elif kind == "adjust_week":
                if not self.is_admin(event):
                    answer = str(self.config.get(
                        "adjust_denied_text",
                        "如果要改时长、请联系管理员哦！"
                    ))
                else:
                    subject, set_minutes = payload
                    # 检查上限
                    if set_minutes > 14400:
                        answer = f"改不了，一次最多改 14400 分钟（10 天）"
                    else:
                        alias_map = load_alias_map(self.db, self.config.get("keyword_alias", ""))
                        normalized = normalize_keyword(subject, alias_map)
                        self._set_subject_value(
                            scope, uid, "week", subject, set_minutes,
                            alias_map, now, by_uid=str(event.get_sender_id())
                        )
                        answer = f"修改{normalized}本周学习时长为{set_minutes}分钟"

            elif kind == "adjust_total":
                if not self.is_admin(event):
                    answer = str(self.config.get(
                        "adjust_denied_text",
                        "如果要改时长、请联系管理员哦！"
                    ))
                else:
                    subject, set_minutes = payload
                    # 检查上限
                    if set_minutes > 14400:
                        answer = f"改不了，一次最多改 14400 分钟（10 天）"
                    else:
                        alias_map = load_alias_map(self.db, self.config.get("keyword_alias", ""))
                        normalized = normalize_keyword(subject, alias_map)
                        self._set_subject_value(
                            scope, uid, "total", subject, set_minutes,
                            alias_map, now, by_uid=str(event.get_sender_id())
                        )
                        answer = f"修改{normalized}总学习时长为{set_minutes}分钟"

            elif kind == "clear":
                if not self.is_admin(event):
                    answer = str(self.config.get(
                        "admin_denied_text",
                        "只有管理员可以使用该命令"
                    ))
                else:
                    subject = payload  # 可能是 None（全清）或科目名
                    clear_key = (scope, uid)

                    if subject:
                        # 清单个科目：会话与补时都按归一化名匹配，改过名的旧记录一并清掉
                        alias_map = load_alias_map(self.db, self.config.get("keyword_alias", ""))
                        normalized = normalize_keyword(subject, alias_map)
                        raw_names = [
                            row["subject"]
                            for table in ("sessions", "adjustments")
                            for row in self.db.execute(
                                f"SELECT DISTINCT subject FROM {table} WHERE scope=? AND uid=?",
                                (scope, uid),
                            ).fetchall()
                            if normalize_keyword(row["subject"], alias_map) == normalized
                        ]
                        for raw in raw_names:
                            self.db.execute(
                                "DELETE FROM sessions WHERE scope=? AND uid=? AND subject=?",
                                (scope, uid, raw)
                            )
                            self.db.execute(
                                "DELETE FROM adjustments WHERE scope=? AND uid=? AND subject=?",
                                (scope, uid, raw)
                            )
                        self.db.commit()
                        answer = f"已清空{normalized}的所有学习数据"
                    else:
                        # 清全部：需要二次确认
                        pending_time = self.pending_clear_all.get(clear_key, 0)
                        if now - pending_time < 300:  # 5 分钟内的重复请求 = 第二次确认
                            # 执行清空
                            self.db.execute(
                                "DELETE FROM sessions WHERE scope=? AND uid=?",
                                (scope, uid)
                            )
                            self.db.execute(
                                "DELETE FROM adjustments WHERE scope=? AND uid=?",
                                (scope, uid)
                            )
                            self.db.commit()
                            # 清除缓存
                            self.pending_clear_all.pop(clear_key, None)
                            answer = "已清空全部学习数据"
                        else:
                            # 第一次请求：记录并提示
                            self.pending_clear_all[clear_key] = now
                            answer = str(self.config.get(
                                "clear_all_confirm_text",
                                "确定清空全部数据吗？再发一次真的重置"
                            ))

            elif kind == "add_admin":
                if not self.is_super_admin(event):
                    answer = "只有超级管理员才能改管理员名单哦"
                else:
                    target_qq = payload
                    super_admins_str = str(self.config.get("super_admins", "2403232967"))
                    super_admins = [qq.strip() for qq in super_admins_str.split("\n") if qq.strip()]
                    # Check if already admin
                    if target_qq in super_admins:
                        answer = "这位已经是超级管理员啦"
                    else:
                        existing = self.db.execute("SELECT qq FROM admins WHERE qq=?", (target_qq,)).fetchone()
                        if existing:
                            answer = "已经是管理员啦"
                        else:
                            # Check limit
                            count = self.db.execute("SELECT COUNT(*) as cnt FROM admins").fetchone()["cnt"]
                            limit = int(self.config.get("admin_limit", 20))
                            if count >= limit:
                                answer = "管理员太多了，先删几个吧"
                            else:
                                self.db.execute(
                                    "INSERT INTO admins(qq, added_at, added_by) VALUES(?,?,?)",
                                    (target_qq, now, str(event.get_sender_id()))
                                )
                                self.db.commit()
                                answer = f"已把 {target_qq} 加为管理员"

            elif kind == "remove_admin":
                if not self.is_super_admin(event):
                    answer = "只有超级管理员才能改管理员名单哦"
                else:
                    target_qq = payload
                    super_admins_str = str(self.config.get("super_admins", "2403232967"))
                    super_admins = [qq.strip() for qq in super_admins_str.split("\n") if qq.strip()]
                    if target_qq in super_admins:
                        answer = "超级管理员不能被删除哦"
                    else:
                        existing = self.db.execute("SELECT qq FROM admins WHERE qq=?", (target_qq,)).fetchone()
                        if existing:
                            self.db.execute("DELETE FROM admins WHERE qq=?", (target_qq,))
                            self.db.commit()
                            answer = f"已将 {target_qq} 移出管理员"
                        else:
                            answer = "本来就不是管理员哦"

            elif kind == "list_admins":
                if not self.is_admin(event):
                    answer = "只有管理员才能查看管理员名单哦"
                else:
                    super_admins_str = str(self.config.get("super_admins", "2403232967"))
                    super_admins = [qq.strip() for qq in super_admins_str.split("\n") if qq.strip()]
                    rows = self.db.execute("SELECT qq FROM admins ORDER BY added_at").fetchall()
                    admin_list = [row["qq"] for row in rows]

                    super_admin_display = "超级管理员：\n" + "\n".join(super_admins)
                    if admin_list:
                        answer = super_admin_display + "\n\n普通管理员：\n" + "\n".join(admin_list)
                    else:
                        answer = super_admin_display + "\n\n普通管理员：还没加过"

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
                            if day > today:
                                break
                            day_sec = self.seconds_total(
                                scope, uid, day.timestamp(),
                                (day + timedelta(days=1)).timestamp(), now
                            )
                            total += day_sec

                            # Get subject breakdown for this day
                            day_stats = self.get_keyword_stats(
                                scope, uid, day.timestamp(),
                                (day + timedelta(days=1)).timestamp(), now, alias_map
                            )

                            # 没记录的天不出现
                            if day_sec == 0 and not day_stats:
                                continue

                            # Day header
                            day_line = render(
                                str(self.config.get("week_day_text", "{month}月{day}日 周{weekday}：{minutes}分钟")),
                                month=day.month,
                                day=day.day,
                                weekday="一二三四五六日"[offset],
                                minutes=minutes_display(day_sec),
                            )
                            days.append(day_line)

                            # Subject breakdown (indented)
                            if day_stats:
                                subject_line_template = str(self.config.get("week_subject_line", "  {subject} {minutes}分钟"))
                                for kw, sec in sorted(day_stats.items(), key=lambda x: -x[1]):
                                    subject_line = subject_line_template.replace("{subject}", kw).replace("{minutes}", minutes_display(sec))
                                    days.append(subject_line)

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
