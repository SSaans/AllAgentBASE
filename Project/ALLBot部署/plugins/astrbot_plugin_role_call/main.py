"""Group-scoped named mention lists."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from sys import maxsize

from astrbot.api.event import filter
from astrbot.api.event.filter import CustomFilter
from astrbot.api.message_components import At, Plain
from astrbot.api.star import Star

CONFIG = {}


def text(event):
    return "".join(c.text for c in event.get_messages() if isinstance(c, Plain)).strip()


def parse(value, config):
    for key, default in [("set_words", ["设置"]), ("call_words", ["召唤"])]:
        words = config.get(key, default)
        if not isinstance(words, list):
            continue
        for word in sorted(
            (str(w).strip() for w in words if str(w).strip()), key=len, reverse=True
        ):
            if value.startswith(word):
                body = value[len(word) :].strip()
                if body:
                    parts = body.split(maxsplit=1)
                    return key, parts[0], parts[1] if len(parts) > 1 else ""
    return None


class RoleFilter(CustomFilter):
    def filter(self, event, cfg):
        command = parse(text(event), CONFIG)
        return bool(
            event.get_group_id()
            and command
            and (
                command[0] == "call_words"
                or any(isinstance(c, At) for c in event.get_messages())
            )
        )


class Main(Star):
    def __init__(self, context, config):
        super().__init__(context)
        global CONFIG
        CONFIG = config
        self.config = config
        folder = (
            Path(__file__).resolve().parents[2]
            / "plugin_data"
            / "astrbot_plugin_role_call"
        )
        folder.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(folder / "roles.sqlite3")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS members(scope TEXT, role TEXT, uid TEXT, PRIMARY KEY(scope,role,uid))"
        )

    async def terminate(self):
        self.db.close()

    @filter.custom_filter(RoleFilter, priority=maxsize)
    async def handle(self, event):
        parsed = parse(text(event), self.config)
        if not parsed:
            return
        event.stop_event()
        action, role, body = parsed
        scope = event.unified_msg_origin
        if len(role) > 40:
            await event.send(event.plain_result("名单名称最多40字，不含空格。"))
            return
        if action == "set_words":
            config = self.context.get_config(umo=scope)
            admins = {str(uid) for uid in config.get("admins_id", [])}
            if (
                self.config.get("admins_only", True)
                and str(event.get_sender_id()) not in admins
            ):
                await event.send(
                    event.plain_result("只有机器人管理员可以设置召唤名单。")
                )
                return
            users = list(
                dict.fromkeys(
                    str(c.qq)
                    for c in event.get_messages()
                    if isinstance(c, At)
                    and str(c.qq).isdigit()
                    and str(c.qq) != str(event.get_self_id())
                )
            )
            if not users:
                await event.send(
                    event.plain_result(
                        "请在设置时 @ 要加入的人，例如：设置程序员 @某人"
                    )
                )
                return
            # Replace only this group's named list, atomically.
            with self.db:
                self.db.execute(
                    "DELETE FROM members WHERE scope=? AND role=?", (scope, role)
                )
                self.db.executemany(
                    "INSERT INTO members VALUES(?,?,?)",
                    [(scope, role, uid) for uid in users],
                )
            answer = str(self.config.get("saved_text", "已设置{role}，共{count}人。"))
            await event.send(
                event.plain_result(
                    answer.replace("{role}", role).replace("{count}", str(len(users)))
                )
            )
        else:
            users = [
                row[0]
                for row in self.db.execute(
                    "SELECT uid FROM members WHERE scope=? AND role=? ORDER BY rowid",
                    (scope, role),
                )
            ]
            if not users:
                await event.send(
                    event.plain_result(
                        str(
                            self.config.get("missing_text", "还没有设置{role}名单。")
                        ).replace("{role}", role)
                    )
                )
                return
            chain = [At(qq=uid) for uid in users]
            if body:
                chain.append(
                    Plain(
                        "\n"
                        + str(self.config.get("separator", "——————————"))
                        + "\n"
                        + body
                    )
                )
            await event.send(event.chain_result(chain))
