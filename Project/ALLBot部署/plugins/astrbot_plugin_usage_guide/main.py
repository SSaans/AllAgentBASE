"""「使用说明」插件：问一句就回一段大白话介绍。

规格见 BRD 4.15：
- 触发用 ``@filter.regex``（@ 或者不 @ 都能触发），不是 ``/`` 命令。
- 输出**就是一段话**（不做海报/图片）。
- 正文可在配置里改；另外提供一个「让 AI 写一版草稿」的开关，
  草稿只发给用户看，**不自动覆盖**已经写好的正文。
"""

from __future__ import annotations

import re

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

PLUGIN_ID = "astrbot_plugin_usage_guide"

# 占位正则：永远不匹配；真正的触发词在插件实例化时从配置装上。
NEVER_MATCH = r"(?!)"

DEFAULT_DRAFT_PROMPT = (
    "你在帮一个 QQ 群机器人写「使用说明」。请用一岁小孩也能看懂的大白话，"
    "写一段（就一段，不要分点编号之外的多余格式、不要 Markdown、不要标题），"
    "介绍这个机器人能帮群友做哪些事：群聊总结（群分析）、把群话题画成漫画（群漫画）、"
    "存表情包和取表情包（加图 / 关键词.jpg）、让它闭嘴一段时间（丛雨闭嘴 30分钟）、"
    "以及关键词自动回复之类的功能。语气活泼一点，80-160 字。"
)


def parse_trigger_list(text: object) -> list[str]:
    """一行一个触发词；``|`` 分隔也认；行首 ``#`` 是注释。"""
    if not isinstance(text, str):
        return []
    triggers: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        for part in line.split("|"):
            item = part.strip()
            if item and item not in triggers:
                triggers.append(item)
    return triggers


def build_pattern(triggers: list[str]) -> str:
    """把触发词拼成正则（纯文本包含即命中）；没有触发词时永不匹配。"""
    parts = [re.escape(trigger) for trigger in triggers if trigger]
    if not parts:
        return NEVER_MATCH
    return "|".join(f"(?:{part})" for part in parts)


def hit_any(triggers: list[str], text: str) -> bool:
    return any(trigger and trigger in text for trigger in triggers)


class UsageGuidePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.triggers = parse_trigger_list(config.get("triggers", ""))
        self.draft_triggers = parse_trigger_list(config.get("draft_triggers", ""))
        pattern = (
            build_pattern([*self.triggers, *self.draft_triggers])
            if config.get("enable", True)
            else NEVER_MATCH
        )
        # 关掉插件时也照样装一个「永不匹配」的正则，避免残留上一轮的触发词
        self._install_filters(pattern)
        logger.info(
            "使用说明插件已加载（触发词 %d 个、草稿触发词 %d 个）",
            len(self.triggers),
            len(self.draft_triggers),
        )

    def _install_filters(self, pattern: str) -> None:
        """把按配置拼好的正则装到本插件的处理器上（类体上只能写常量）。"""
        try:
            from astrbot.core.star.filter.regex import RegexFilter
            from astrbot.core.star.star_handler import star_handlers_registry
        except Exception as exc:  # pragma: no cover - 依赖核心实现细节
            logger.error("使用说明：无法加载核心过滤器实现：%s", exc)
            return

        handler_full_name = f"{self.send_guide.__module__}_{self.send_guide.__name__}"
        metadata = star_handlers_registry.get_handler_by_full_name(handler_full_name)
        if metadata is None:
            logger.error(
                "使用说明：找不到自己的处理器 %s，触发词将不生效，请在 WebUI 重载本插件",
                handler_full_name,
            )
            return

        kept = [f for f in metadata.event_filters if not isinstance(f, RegexFilter)]
        kept.append(RegexFilter(pattern))
        metadata.event_filters[:] = kept

    async def _draft_guide(self, event: AstrMessageEvent) -> str:
        """让当前会话的模型写一版草稿。"""
        provider = self.context.get_using_provider(umo=event.unified_msg_origin)
        if provider is None:
            return ""
        prompt = self.config.get("draft_prompt", "")
        if not isinstance(prompt, str) or not prompt.strip():
            prompt = DEFAULT_DRAFT_PROMPT
        response = await provider.text_chat(
            prompt=prompt,
            session_id=getattr(event, "session_id", None),
        )
        return str(getattr(response, "completion_text", "") or "").strip()

    @filter.regex(NEVER_MATCH, priority=10)
    async def send_guide(self, event: AstrMessageEvent):
        """命中触发词就发一段介绍；说「生成使用说明」就先让 AI 写一版草稿。"""
        if not self.config.get("enable", True):
            return

        text = event.get_message_str().strip()
        if not text:
            return

        draft_mode = hit_any(self.draft_triggers, text)
        if not draft_mode and not hit_any(self.triggers, text):
            return

        current = self.config.get("guide_text", "")
        current = current.strip() if isinstance(current, str) else ""

        if draft_mode:
            try:
                draft = await self._draft_guide(event)
            except Exception as exc:
                logger.error("使用说明：草稿生成失败：%s", exc)
                draft = ""
            if not draft:
                body = f"模型这会儿没空，先看我自己写的那版吧：\n\n{current}" if current else "模型这会儿没空，稍后再试～"
            else:
                body = (
                    "这是我让模型写的一版草稿，你看看要不要用：\n\n"
                    f"{draft}\n\n"
                    "（想用的话，把上面这段原样粘到插件配置的「介绍正文」里就行，"
                    "我不会自己覆盖你写好的内容。）"
                )
        else:
            body = current or "我还没写使用说明呢，请在插件配置里填一下「介绍正文」～"

        try:
            await event.send(event.plain_result(body))
        except Exception as exc:
            logger.error("使用说明：发送失败：%s", exc)
        finally:
            # 拦住后续，避免 LLM 又答一遍
            event.stop_event()
