"""禁言插件：让丛雨闭嘴一段时间，期间什么都不理，到点自己恢复。

规格见 BRD 4.12。三条技术前提：
1. 用 ``@filter.event_message_type(...)`` 注册、**不注册成 ``/`` 命令** →
   插件过滤器通过就置 ``is_wake=True``，不受唤醒前缀限制（``waking_check/stage.py:219``）。
2. ``event.stop_event()`` 能拦住后面所有插件和 LLM
   （``process_stage/method/star_request.py:37``、``:51`` 有 ``if event.is_stopped(): break``）。
3. 优先级必须**高于** ``presence_reply``（它用 ``maxsize + 1``），
   否则禁言期间她还会先喊「吾辈在！」。
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path
from sys import maxsize

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.message_components import Plain
from astrbot.api.star import Context, Star

PLUGIN_ID = "astrbot_plugin_mute"
DATA_DIR = Path(__file__).resolve().parents[2] / "plugin_data" / PLUGIN_ID
STATE_FILE = DATA_DIR / "mute_state.json"
GLOBAL_KEY = "global"

_UNIT_MINUTES = {
    "个小时": 60,
    "个钟头": 60,
    "hours": 60,
    "hour": 60,
    "小时": 60,
    "钟头": 60,
    "hrs": 60,
    "hr": 60,
    "h": 60,
    "时": 60,
    "minutes": 1,
    "minute": 1,
    "分钟": 1,
    "mins": 1,
    "min": 1,
    "m": 1,
    "分": 1,
    "seconds": 1 / 60,
    "second": 1 / 60,
    "秒钟": 1 / 60,
    "secs": 1 / 60,
    "sec": 1 / 60,
    "s": 1 / 60,
    "秒": 1 / 60,
}

_DURATION_RE = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>"
    + "|".join(sorted(_UNIT_MINUTES, key=len, reverse=True))
    + r")?",
    re.IGNORECASE,
)

_FULL_KEY = re.compile(r"[^a-zA-Z0-9_:\-\u4e00-\u9fff]+")


def parse_duration(text: str, default_minutes: int, max_minutes: int) -> dict | None:
    """从消息里抠出时长，返回秒数等信息；没写时长就用默认值。"""
    match = _DURATION_RE.search(text or "")
    if match and match.group("value"):
        value = float(match.group("value"))
        unit = (match.group("unit") or "").lower()
        minutes = value * _UNIT_MINUTES.get(unit, 1.0)
        duration_text = match.group(0).strip()
        if not unit:
            duration_text = f"{int(value)}分钟"
    else:
        minutes = float(default_minutes)
        duration_text = f"{int(default_minutes)}分钟"

    capped = False
    minutes = max(minutes, 1 / 60)
    if max_minutes > 0 and minutes > max_minutes:
        minutes = float(max_minutes)
        capped = True
        duration_text = f"{max_minutes}分钟"

    seconds = max(1.0, minutes * 60)
    return {
        "seconds": seconds,
        "minutes": max(1, round(seconds / 60)),
        "duration": duration_text,
        "capped": capped,
    }


def parse_mute_request(
    text: str,
    words: list[str],
    default_minutes: int,
    max_minutes: int,
) -> dict | None:
    """消息里出现禁言口令就返回禁言请求，否则返回 None。"""
    hit = next((word for word in words if word and word in (text or "")), "")
    if not hit:
        return None
    request = parse_duration(text.split(hit, 1)[1], default_minutes, max_minutes)
    if request is None:
        return None
    request["word"] = hit
    return request


def render_reply(template: str, request: dict) -> str:
    """替换回复里的 {duration} / {minutes}。"""
    try:
        return template.format(
            duration=request.get("duration", ""),
            minutes=request.get("minutes", 0),
        ).strip()
    except (KeyError, IndexError, ValueError):
        return template.strip()


class MuteStore:
    """禁言状态，落盘在 ``core/data/plugin_data/astrbot_plugin_mute/mute_state.json``。"""

    def __init__(self, path: Path):
        self.path = path
        self.targets: dict[str, dict] = {}
        self.load()

    def load(self) -> None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.targets = {}
            return
        except (OSError, ValueError) as exc:
            logger.warning("禁言插件：读取状态文件失败（%s），按未禁言处理", exc)
            self.targets = {}
            return
        targets = raw.get("targets") if isinstance(raw, dict) else None
        if isinstance(targets, dict):
            self.targets = {
                str(key): value
                for key, value in targets.items()
                if isinstance(value, dict)
            }
        else:
            self.targets = {}

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"targets": self.targets}
            self.path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except (OSError, ValueError) as exc:
            logger.error("禁言插件：写状态文件失败：%s", exc)

    def prune(self, now: float) -> list[str]:
        """清掉已到期的目标，返回被清掉的 key。"""
        expired = [
            key
            for key, item in self.targets.items()
            if float(item.get("deadline", 0) or 0) <= now
        ]
        for key in expired:
            self.targets.pop(key, None)
        return expired

    def deadline(self, key: str) -> float:
        item = self.targets.get(key) or {}
        try:
            return float(item.get("deadline", 0) or 0)
        except (TypeError, ValueError):
            return 0.0

    def is_active(self, key: str, now: float) -> bool:
        return self.deadline(key) > now


class MutePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.store = MuteStore(STATE_FILE)
        self._timers: dict[str, asyncio.Task] = {}
        words = config.get("command_words", [])
        self.words = (
            [str(word).strip() for word in words if str(word).strip()]
            if isinstance(words, list)
            else []
        )
        if not self.words:
            self.words = ["闭嘴"]
        resume_words = config.get(
            "unmute_words", ["丛雨说话", "可以说话了", "解除禁言"]
        )
        self.unmute_words = (
            [str(word).strip() for word in resume_words if str(word).strip()]
            if isinstance(resume_words, list)
            else []
        )
        logger.info("Mute plugin v1.1.0 loaded with manual resume enabled")

    async def initialize(self) -> None:
        """启动/重载后恢复：清掉已到期的，给还没到期的补上定时器。"""
        now = time.time()
        expired = self.store.prune(now)
        if expired:
            self.store.save()
            logger.info("禁言插件：%s 的禁言已过期，已恢复", "、".join(expired))
        for key, item in list(self.store.targets.items()):
            self._arm(key, float(item.get("deadline", 0) or 0))

    async def terminate(self) -> None:
        for task in list(self._timers.values()):
            if not task.done():
                task.cancel()
        self._timers.clear()

    # ---------- 内部工具 ----------

    def _setting_int(self, name: str, default: int) -> int:
        value = self.config.get(name, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _target_key(self, event: AstrMessageEvent) -> str:
        scope = str(self.config.get("scope", "group")).strip().lower()
        if scope == "global":
            return GLOBAL_KEY
        group_id = str(event.get_group_id() or "").strip()
        return f"group:{group_id}" if group_id else GLOBAL_KEY

    def _silenced_keys(self, event: AstrMessageEvent) -> list[str]:
        keys = [GLOBAL_KEY]
        group_id = str(event.get_group_id() or "").strip()
        if group_id:
            keys.append(f"group:{group_id}")
        return keys

    def _arm(self, key: str, deadline: float) -> None:
        old = self._timers.pop(key, None)
        if old and not old.done():
            old.cancel()
        delay = max(0.0, deadline - time.time())
        try:
            self._timers[key] = asyncio.create_task(self._resume_after(key, delay))
        except RuntimeError as exc:  # pragma: no cover - 没有事件循环时
            logger.warning("禁言插件：定时器创建失败（%s），靠惰性判断恢复", exc)

    async def _resume_after(self, key: str, delay: float) -> None:
        if delay > 0:
            await asyncio.sleep(delay)
        await self._on_resume(key)

    async def _on_resume(self, key: str) -> None:
        self._timers.pop(key, None)
        item = self.store.targets.get(key)
        if not item:
            return
        now = time.time()
        if float(item.get("deadline", 0) or 0) > now:
            # 期间又重新禁言了，按新时间再排
            self._arm(key, float(item.get("deadline", 0) or 0))
            return

        self.store.targets.pop(key, None)
        self.store.save()
        logger.info("禁言插件：%s 已到期，恢复发言", key)

        text = self.config.get("resume_reply", "")
        session = item.get("umo")
        if (
            isinstance(text, str)
            and text.strip()
            and isinstance(session, str)
            and session
        ):
            try:
                await self.context.send_message(
                    session,
                    MessageChain([Plain(text.strip())]),
                )
            except Exception as exc:  # noqa: BLE001 - Platform transports expose different errors.
                logger.exception("禁言插件：到点回话失败：%s", exc)

    # ---------- 主处理器 ----------

    @filter.event_message_type(filter.EventMessageType.ALL, priority=maxsize + 100)
    async def guard(self, event: AstrMessageEvent):
        """① 收到禁言口令就记下时间并回话；② 禁言期内一律静默。"""
        if not self.config.get("enable", True):
            return

        sender_id = str(event.get_sender_id()).strip()
        if not sender_id or sender_id == str(event.get_self_id()).strip():
            return

        now = time.time()
        # WakingCheck removes name prefixes from message_str. Components retain them.
        text = (
            "".join(
                component.text
                for component in event.get_messages()
                if isinstance(component, Plain)
            ).strip()
            or event.get_message_str().strip()
        )
        key = self._target_key(event)
        was_silenced = any(
            self.store.is_active(item, now) for item in self._silenced_keys(event)
        )

        allow_command = not self.config.get("admins_only", False) or event.is_admin()
        if text and allow_command:
            # Resume must win over both overlapping mute words and the silence guard.
            if any(word in text for word in self.unmute_words):
                for target in self._silenced_keys(event):
                    self.store.targets.pop(target, None)
                    timer = self._timers.pop(target, None)
                    if timer and not timer.done():
                        timer.cancel()
                self.store.save()
                logger.info(
                    "Mute manually released for session %s", event.unified_msg_origin
                )
                reply = str(self.config.get("unmute_reply", "好啦，我回来了")).strip()
                try:
                    if reply:
                        await event.send(event.plain_result(reply))
                except Exception as exc:  # noqa: BLE001 - Platform transports expose different errors.
                    logger.exception("Failed to send manual resume reply: %s", exc)
                finally:
                    event.stop_event()
                return

            request = parse_mute_request(
                text,
                self.words,
                self._setting_int("default_minutes", 30),
                self._setting_int("max_minutes", 1440),
            )
            if request is not None:
                # If already muted, ignore new mute requests - only unmute command works
                if was_silenced:
                    event.stop_event()
                    return

                deadline = now + float(request["seconds"])
                self.store.targets[key] = {
                    "deadline": deadline,
                    "umo": event.unified_msg_origin,
                }
                self.store.save()
                self._arm(key, deadline)
                if request.get("capped"):
                    logger.info(
                        "禁言插件：请求时长超过上限，已按上限处理（key=%s）",
                        key,
                    )
                reply = render_reply(
                    str(
                        self.config.get("start_reply", "好的，接下来我会闭嘴{duration}")
                    ),
                    request,
                )
                if reply:
                    try:
                        await event.send(event.plain_result(reply))
                    except Exception as exc:  # noqa: BLE001 - Platform transports expose different errors.
                        logger.exception("禁言插件：回声失败：%s", exc)
                event.stop_event()
                return

        # 到点自动恢复的「惰性判断」：这次消息进来时先清过期状态
        if self.store.prune(now):
            self.store.save()

        if any(self.store.is_active(item, now) for item in self._silenced_keys(event)):
            event.stop_event()
