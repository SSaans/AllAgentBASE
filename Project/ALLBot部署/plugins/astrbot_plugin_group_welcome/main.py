"""入群欢迎插件：有人进群时自动欢迎一句。

技术要点（规格见 BRD 4.14）：
1. OneBot 的 ``notice`` 事件（``notice_type = "group_increase"``）会被适配器转成消息事件，
   原始数据保留在 ``raw_message`` 里（``aiocqhttp_platform_adapter.py:168-196``）。
2. 必须用**自定义过滤器**把条件卡死在「只有入群通知」。
   绝不能用无条件的 ``event_message_type(GROUP_MESSAGE)``——那样子每一条群消息
   都会让过滤器通过、被当成「已唤醒」，插件会在每句话上都跑一遍。
3. 欢迎发完 ``event.stop_event()``，避免这条空消息继续往下走。
"""

from __future__ import annotations

from sys import maxsize

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.event.filter import CustomFilter
from astrbot.api.message_components import At, Plain
from astrbot.api.star import Context, Star

PLUGIN_ID = "astrbot_plugin_group_welcome"
GROUP_INCREASE = "group_increase"


class GroupIncreaseFilter(CustomFilter):
    """只放行「群成员增加」的 OneBot 通知事件。"""

    def filter(self, event: AstrMessageEvent, cfg: AstrBotConfig) -> bool:
        raw = getattr(event.message_obj, "raw_message", None)
        getter = getattr(raw, "get", None)
        if not callable(getter):
            # 普通消息事件的 raw_message 不是 dict 样式的通知事件
            return False
        try:
            notice_type = getter("notice_type", "")
        except Exception:
            return False
        return str(notice_type or "") == GROUP_INCREASE


def parse_group_texts(text: object) -> dict[str, str]:
    """解析「分群欢迎词」：一行一条 ``群号 => 欢迎词``，``#`` 为注释。"""
    mapping: dict[str, str] = {}
    if not isinstance(text, str):
        return mapping
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=>" not in line:
            continue
        group_id, _, welcome = line.partition("=>")
        group_id = group_id.strip()
        welcome = welcome.strip()
        if group_id and welcome:
            mapping[group_id] = welcome
    return mapping


def render_welcome(template: str, nickname: str, user_id: str, group_id: str) -> str:
    """替换欢迎词里的 {nickname} / {user_id} / {group_id} 占位符。"""
    try:
        return template.format(
            nickname=nickname,
            user_id=user_id,
            group_id=group_id,
        )
    except (KeyError, IndexError, ValueError):
        # 用户写了别的花括号，原样发出即可，不要让插件崩掉
        return template


class GroupWelcomePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.group_texts = parse_group_texts(config.get("group_texts", ""))
        logger.info("入群欢迎插件已加载（分群欢迎词 %d 条）", len(self.group_texts))

    def _welcome_text(self, group_id: str) -> str:
        text = self.group_texts.get(group_id)
        if not text:
            configured = self.config.get("welcome_text", "")
            text = configured if isinstance(configured, str) else ""
        return text.strip()

    async def _resolve_nickname(
        self,
        event: AstrMessageEvent,
        group_id: str,
        user_id: str,
    ) -> str:
        """尽量问协议端要一下群名片；取不到就退回 QQ 号。"""
        call = getattr(getattr(event, "bot", None), "call_action", None)
        if not callable(call):
            return user_id
        try:
            info = await call(
                "get_group_member_info",
                group_id=int(group_id),
                user_id=int(user_id),
                no_cache=True,
            )
        except Exception as exc:
            logger.debug("入群欢迎：取群名片失败（%s），改用 QQ 号", exc)
            return user_id
        if isinstance(info, dict):
            name = str(info.get("card") or info.get("nickname") or "").strip()
            return name or user_id
        return user_id

    @filter.custom_filter(GroupIncreaseFilter, priority=maxsize + 2)
    async def welcome_new_member(self, event: AstrMessageEvent):
        """新成员入群时发一句欢迎语。"""
        if not self.config.get("enable", True):
            return

        raw = getattr(event.message_obj, "raw_message", None)
        getter = getattr(raw, "get", None)
        if not callable(getter):
            return

        user_id = str(getter("user_id", "") or "").strip()
        group_id = str(event.get_group_id() or getter("group_id", "") or "").strip()
        if not user_id or not group_id:
            return
        if user_id == str(event.get_self_id()).strip():
            return

        template = self._welcome_text(group_id)
        if not template:
            event.stop_event()
            return

        nickname = await self._resolve_nickname(event, group_id, user_id)
        text = render_welcome(template, nickname, user_id, group_id)

        chain = []
        if self.config.get("at_new_member", True):
            chain.append(At(qq=user_id, name=nickname))
        chain.append(Plain(text))

        try:
            await event.send(event.chain_result(chain))
        except Exception as exc:
            logger.error("入群欢迎：发送失败：%s", exc)
        finally:
            event.stop_event()
