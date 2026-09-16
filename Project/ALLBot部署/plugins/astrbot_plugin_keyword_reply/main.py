"""关键词自动回复插件：命中规则就回话，不需要 @、不需要唤醒词。

实现要点：
1. 用 ``@filter.regex`` 注册处理器（官方 ``star/filter/regex.py`` 注释原文：
   「正则表达式过滤器不会受到 wake_prefix 的制约」），**不注册成 `/` 命令**。
2. 回话后必须 ``event.stop_event()``，否则这条消息会被当成「已唤醒」，
   LLM 还会再答一遍（变成答两句）。
3. 规则写在配置里（``rules_text``），一条一行；保存配置后 AstrBot 会自动热重载本插件
   （``dashboard/services/config_service.py`` 保存配置后调用 ``plugin_manager.reload``），
   所以触发词改了也能立刻生效。
"""

from __future__ import annotations

import random
import re

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

PLUGIN_ID = "astrbot_plugin_keyword_reply"

# 占位正则：永远不匹配。真正的规则正则在插件实例化时从配置编译并装回去。
NEVER_MATCH = r"(?!)"

# 形如  qq:123456: 规则内容  或  group:987654: 规则内容
_TARGET_PREFIX = re.compile(r"^(?P<kind>qq|group)\s*:\s*(?P<value>[^:\s]+)\s*:\s*(?P<body>.+)$")


def parse_rules(text: object) -> tuple[list[dict], list[dict]]:
    """把配置里的多行文本解析成 (默认规则, 指定对象规则)。

    每行格式：``触发词 => 回复1|回复2|回复3``
    - 多个回复用 ``|`` 分隔 → 随机挑一条；只写一条 → 固定回这一条。
    - 想固定回复里带 ``|``：写成 ``=整句回复``。
    - 触发词两端加 ``/`` 表示按正则匹配（例如 ``/^晚安$/``），否则按纯文本「包含即命中」。
    - 行首加 ``qq:号码:`` 或 ``group:群号:`` → 只对这个人 / 这个群生效。
    - 行首 ``#`` 是注释。
    """
    default_rules: list[dict] = []
    targeted_rules: list[dict] = []
    if not isinstance(text, str):
        return default_rules, targeted_rules

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        kind, value, body = "", "", line
        prefix_match = _TARGET_PREFIX.match(line)
        if prefix_match:
            kind = prefix_match.group("kind").lower()
            value = prefix_match.group("value").strip()
            body = prefix_match.group("body").strip()

        if "=>" not in body:
            logger.warning("关键词回复：忽略写法不对的规则行 %r（缺少 =>）", raw_line)
            continue
        trigger_text, _, reply_text = body.partition("=>")
        trigger_text = trigger_text.strip()
        reply_text = reply_text.strip()

        rule_regex = compile_trigger(trigger_text)
        if rule_regex is None or not reply_text:
            continue

        if reply_text.startswith("="):
            replies = [reply_text[1:].strip()]
        else:
            replies = [part.strip() for part in reply_text.split("|") if part.strip()]
        if not replies:
            continue

        rule = {
            "trigger": trigger_text,
            "regex": rule_regex,
            "replies": replies,
            "kind": kind,
            "value": value,
        }
        (targeted_rules if kind else default_rules).append(rule)

    return default_rules, targeted_rules


def compile_trigger(trigger: str) -> re.Pattern[str] | None:
    """把触发词编译成正则；``/.../`` 视为原始正则，其余按纯文本转义。"""
    if not trigger:
        return None
    if len(trigger) > 2 and trigger.startswith("/") and trigger.endswith("/"):
        pattern_text = trigger[1:-1]
    else:
        pattern_text = re.escape(trigger)
    try:
        return re.compile(pattern_text)
    except re.error as exc:
        logger.warning("关键词回复：触发词 %r 不是合法正则（%s），已跳过", trigger, exc)
        return None


def build_pattern(rules: list[dict]) -> str:
    """把所有规则合成一个正则；没有任何规则时返回永不匹配的正则。"""
    parts = [f"(?:{rule['regex'].pattern})" for rule in rules]
    if not parts:
        return NEVER_MATCH
    try:
        re.compile("|".join(parts))
    except re.error as exc:
        logger.error("关键词回复：规则合并后正则不合法（%s），本插件本次不生效", exc)
        return NEVER_MATCH
    return "|".join(parts)


def match_rule(
    rules: list[dict],
    text: str,
    sender_id: str,
    group_id: str,
) -> dict | None:
    """按「指定对象规则优先、默认规则兜底」的顺序找第一条命中的规则。"""
    default_rules, targeted_rules = rules
    for rule in targeted_rules:
        if rule["kind"] == "qq" and rule["value"] != sender_id:
            continue
        if rule["kind"] == "group" and rule["value"] != group_id:
            continue
        if rule["regex"].search(text):
            return rule
    for rule in default_rules:
        if rule["regex"].search(text):
            return rule
    return None


def pick_reply(rule: dict) -> str:
    """从命中规则里挑一条回复（多条随机，一条固定）。"""
    return random.choice(rule["replies"])


def render(text: str, event: AstrMessageEvent) -> str:
    """替换回复里的 {nickname} / {sender_id} / {group_id} 占位符。"""
    if "{" not in text:
        return text
    values = {
        "nickname": event.get_sender_name(),
        "sender_id": event.get_sender_id(),
        "group_id": event.get_group_id(),
    }
    try:
        return text.format(**values)
    except (KeyError, IndexError, ValueError):
        return text


class KeywordReplyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.default_rules, self.targeted_rules = parse_rules(
            config.get("rules_text", ""),
        )
        all_rules = [*self.targeted_rules, *self.default_rules]
        # 关掉插件时也照样装一个「永不匹配」的正则，避免残留上一轮的触发词
        self.pattern = (
            build_pattern(all_rules) if config.get("enable", True) else NEVER_MATCH
        )
        self._install_filters(self.pattern)
        logger.info(
            "关键词回复插件已加载：默认规则 %d 条、指定对象规则 %d 条",
            len(self.default_rules),
            len(self.targeted_rules),
        )

    def _install_filters(self, pattern: str) -> None:
        """把按配置编译好的正则装到本插件的处理器上。

        类体上的 ``@filter.regex`` 只能写死常量，这里用运行时配置替换掉它。
        """
        try:
            from astrbot.core.star.filter.regex import RegexFilter
            from astrbot.core.star.star_handler import star_handlers_registry
        except Exception as exc:  # pragma: no cover - 依赖核心实现细节
            logger.error("关键词回复：无法加载核心过滤器实现：%s", exc)
            return

        handler_full_name = (
            f"{self.handle_keywords.__module__}_{self.handle_keywords.__name__}"
        )
        metadata = star_handlers_registry.get_handler_by_full_name(handler_full_name)
        if metadata is None:
            logger.error(
                "关键词回复：找不到自己的处理器 %s，触发词将不生效，请在 WebUI 重载本插件",
                handler_full_name,
            )
            return

        kept = [f for f in metadata.event_filters if not isinstance(f, RegexFilter)]
        kept.append(RegexFilter(pattern))
        metadata.event_filters[:] = kept

    @filter.regex(NEVER_MATCH, priority=10)
    async def handle_keywords(self, event: AstrMessageEvent):
        """命中关键词规则时回复一句话，并阻止后续 LLM 再答一遍。"""
        if not self.config.get("enable", True):
            return

        sender_id = str(event.get_sender_id()).strip()
        if not sender_id or sender_id == str(event.get_self_id()).strip():
            return

        text = event.get_message_str().strip()
        if not text:
            return

        group_id = str(event.get_group_id() or "").strip()
        allowed_groups = self.config.get("group_whitelist", [])
        if (
            group_id
            and isinstance(allowed_groups, list)
            and allowed_groups
            and group_id not in {str(item).strip() for item in allowed_groups}
        ):
            return

        rule = match_rule(
            (self.default_rules, self.targeted_rules),
            text,
            sender_id,
            group_id,
        )
        if rule is None:
            # 没命中就什么都不做，也不 stop_event（让正常聊天照常走）
            return

        reply = render(pick_reply(rule), event).strip()
        if not reply:
            return

        try:
            await event.send(event.plain_result(reply))
        except Exception as exc:
            logger.error("关键词回复：发送失败：%s", exc)
        finally:
            # 必须拦住，否则 LLM 会再答一遍（官方文档也点了这个坑）
            event.stop_event()
