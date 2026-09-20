"""聊天记录提取插件 - 将 QQ 合并转发消息提取为 txt 或 html 格式"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Image, Plain, Reply, At, Forward, Node, File
from astrbot.api.star import Context, Star

# 导入 OneBot 客户端用于获取 Forward 内容
try:
    from astrbot.core.utils.quoted_message.onebot_client import OneBotClient
    from astrbot.core.utils.quoted_message.chain_parser import OneBotPayloadParser
    HAS_ONEBOT_CLIENT = True
except ImportError:
    HAS_ONEBOT_CLIENT = False
    logger.warning("聊天记录提取插件：无法导入 OneBotClient，Forward 消息提取功能将受限")


def normalize_text(text: str) -> str:
    """规范化文本，移除多余空白"""
    return " ".join((text or "").split()).strip()


def extract_command_and_format(text: str, commands: list[str]) -> str | None:
    """从消息中提取命令和格式

    返回: "txt" | "html" | None
    """
    text_lower = text.lower().strip()

    for cmd in commands:
        if not cmd:
            continue
        # 匹配 /提取 txt, /提取 html, 提取txt, 提取 html 等各种格式
        pattern = rf"(?:^|[/\s])({re.escape(cmd)})\s*(txt|html)"
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            return match.group(2).lower()

    return None


class ChatMessage:
    """聊天消息数据结构"""

    def __init__(
        self,
        sender_name: str = "",
        sender_id: str = "",
        content: str = "",
        timestamp: str = "",
        msg_type: str = "text",
        extra_data: dict | None = None,
        nested_messages: list['ChatMessage'] | None = None,
    ):
        self.sender_name = sender_name
        self.sender_id = sender_id
        self.content = content
        self.timestamp = timestamp
        self.msg_type = msg_type  # text, image, at, file, forward, etc.
        self.extra_data = extra_data or {}
        self.nested_messages = nested_messages or []

    def to_txt_line(self) -> str:
        """转换为 txt 格式的一行"""
        time_str = self.timestamp if self.timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        name = self.sender_name if self.sender_name else "未知"

        if self.msg_type == "text":
            return f"[{time_str}] {name}: {self.content}"
        elif self.msg_type == "image":
            return f"[{time_str}] {name}: 【图片】"
        elif self.msg_type == "at":
            at_name = self.extra_data.get("at_name", "某人")
            return f"[{time_str}] {name}: @{at_name} {self.content}"
        elif self.msg_type == "file":
            return f"[{time_str}] {name}: 【文件】{self.content}"
        else:
            return f"[{time_str}] {name}: 【{self.msg_type}】{self.content}"

    def to_html_bubble(self, is_self: bool = False) -> str:
        """转换为 HTML 气泡格式"""
        bubble_class = "msg-bubble-self" if is_self else "msg-bubble-other"
        time_str = self.timestamp if self.timestamp else datetime.now().strftime("%H:%M:%S")

        # 转义 HTML 特殊字符
        safe_name = (self.sender_name or "未知").replace("<", "&lt;").replace(">", "&gt;")
        safe_content = (self.content or "").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

        if self.msg_type == "text":
            content_html = f'<div class="msg-text">{safe_content}</div>'
        elif self.msg_type == "forward":
            # 合并转发卡片 - 可折叠
            # 检查是否有嵌套消息
            if not self.nested_messages:
                content_html = '<div class="msg-placeholder">【聊天记录 - 已过期或无法加载】</div>'
            else:
                msg_count = self.extra_data.get("message_count", len(self.nested_messages))
                card_id = f"forward_{id(self)}"

                # 生成预览（前3条消息）- 改进内容提取
                preview_lines = []
                for i, nested_msg in enumerate(self.nested_messages[:3]):
                    preview_name = nested_msg.sender_name or "未知"

                    # 根据消息类型生成准确的预览
                    if nested_msg.msg_type == "image":
                        preview_content = "[图片]"
                    elif nested_msg.msg_type == "file":
                        file_name = nested_msg.content or "文件"
                        preview_content = f"[文件: {file_name[:15]}...]" if len(file_name) > 15 else f"[文件: {file_name}]"
                    elif nested_msg.msg_type == "video":
                        preview_content = "[视频]"
                    elif nested_msg.msg_type == "face":
                        preview_content = "[表情]"
                    elif nested_msg.msg_type == "forward":
                        nested_count = len(nested_msg.nested_messages)
                        preview_content = f"[聊天记录({nested_count}条)]"
                    else:
                        # 文本消息
                        content = nested_msg.content or ""
                        preview_content = content[:30] + "..." if len(content) > 30 else content

                    preview_lines.append(f"{preview_name}: {preview_content}")

                preview_html = "<br>".join(preview_lines) if preview_lines else "无预览内容"

                # 生成嵌套消息的完整 HTML
                nested_html = ""
                for nested_msg in self.nested_messages:
                    nested_html += nested_msg.to_html_bubble(is_self=False)

                content_html = f'''
                <div class="forward-card">
                    <div class="forward-header" onclick="toggleForward('{card_id}')">
                        <div class="forward-title">💬 {safe_content}</div>
                        <div class="forward-preview">{preview_html}</div>
                        <div class="forward-count">查看 {msg_count} 条转发消息 ▼</div>
                    </div>
                    <div class="forward-content" id="{card_id}" style="display: none;">
                        {nested_html}
                    </div>
                </div>
                '''
        elif self.msg_type == "image":
            img_url = self.extra_data.get("url", "")
            if img_url and not img_url.startswith("file:") and not img_url.startswith("/") and img_url.strip():
                # 确保图片 URL 是完整的
                if not img_url.startswith("http"):
                    img_url = "https://" + img_url if not img_url.startswith("//") else "https:" + img_url
                content_html = f'<div class="msg-image"><img src="{img_url}" alt="图片" loading="lazy" onerror="this.parentElement.innerHTML=\'【图片加载失败】\';" /></div>'
            else:
                content_html = '<div class="msg-placeholder">【图片 - 无法加载】</div>'
        elif self.msg_type == "face":
            # QQ 表情 - 使用 QQ 官方 CDN
            face_id = self.extra_data.get("face_id", "")
            if face_id:
                # QQ 表情 CDN 地址
                face_url = f"https://gxh.vip.qq.com/club/item/parcel/item/{face_id[:2]}/{face_id}/300x300.png"
                content_html = f'<div class="msg-face"><img src="{face_url}" alt="[表情]" class="face-emoji" onerror="this.outerHTML=\'[表情{face_id}]\';" /></div>'
            else:
                content_html = '<div class="msg-placeholder">[表情]</div>'
        elif self.msg_type == "video":
            video_url = self.extra_data.get("url", "")
            thumb_url = self.extra_data.get("thumb", "")
            if video_url:
                content_html = f'<div class="msg-video">📹 <a href="{video_url}" target="_blank">查看视频</a></div>'
            elif thumb_url:
                content_html = f'<div class="msg-video">📹 视频缩略图<br><img src="{thumb_url}" style="max-width:200px; border-radius:8px; margin-top:6px;" alt="视频缩略图"></div>'
            else:
                content_html = '<div class="msg-placeholder">【视频】</div>'
        elif self.msg_type == "file":
            file_size = self.extra_data.get("size", 0)
            file_url = self.extra_data.get("file_url", "")

            # 计算大小显示
            if file_size > 0:
                if file_size < 1024:
                    size_str = f"{file_size}B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f}KB"
                else:
                    size_str = f"{file_size / 1024 / 1024:.1f}MB"
            else:
                size_str = "未知大小"

            # 如果有URL，显示为可点击链接
            if file_url:
                content_html = f'<div class="msg-file">📄 <a href="{file_url}" target="_blank" style="color:inherit;">{safe_content}</a> ({size_str})</div>'
            else:
                content_html = f'<div class="msg-file">📄 {safe_content} ({size_str})</div>'
        elif self.msg_type == "at":
            at_name = self.extra_data.get("at_name", "某人")
            content_html = f'<div class="msg-text"><span class="msg-at">@{at_name}</span> {safe_content}</div>'
        else:
            content_html = f'<div class="msg-placeholder">【{self.msg_type}】{safe_content}</div>'

        return f'''
        <div class="msg-item {bubble_class}">
            <div class="msg-avatar">
                <img src="https://q1.qlogo.cn/g?b=qq&nk={self.sender_id}&s=100"
                     alt="{safe_name}"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                <div class="msg-avatar-fallback" style="display:none;">{safe_name[0] if safe_name else "?"}</div>
            </div>
            <div class="msg-content">
                <div class="msg-header">
                    <span class="msg-name">{safe_name}</span>
                    <span class="msg-time">{time_str}</span>
                </div>
                <div class="msg-body">
                    {content_html}
                </div>
            </div>
        </div>
        '''


class ChatExtractorPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.output_root = Path(__file__).resolve().parents[2] / "chat_exports"
        self.output_root.mkdir(parents=True, exist_ok=True)
        logger.info("聊天记录提取插件已加载，输出目录: %s", self.output_root)

    def _setting(self, name: str, default: str) -> str:
        value = self.config.get(name, default)
        return value if isinstance(value, str) else default

    async def _reply(self, event: AstrMessageEvent, text: str):
        """发送回复"""
        if text:
            await event.send(event.plain_result(text))

    def _extract_messages_from_node(self, node: Node) -> list[ChatMessage]:
        """从 Node 提取消息列表"""
        messages = []

        # 提取发送者信息
        sender_name = node.name or "未知"
        sender_id = str(node.uin or "")

        # 遍历内容组件
        for component in node.content:
            if isinstance(component, Plain):
                # 纯文本消息
                text = normalize_text(component.text)
                if text:
                    messages.append(ChatMessage(
                        sender_name=sender_name,
                        sender_id=sender_id,
                        content=text,
                        msg_type="text",
                    ))
            elif isinstance(component, Image):
                # 图片消息
                img_url = getattr(component, 'url', '') or getattr(component, 'file', '')
                messages.append(ChatMessage(
                    sender_name=sender_name,
                    sender_id=sender_id,
                    content="",
                    msg_type="image",
                    extra_data={"url": img_url},
                ))
            elif isinstance(component, At):
                # @ 消息
                at_qq = str(getattr(component, 'qq', ''))
                at_name = str(getattr(component, 'name', '')) or at_qq
                messages.append(ChatMessage(
                    sender_name=sender_name,
                    sender_id=sender_id,
                    content="",
                    msg_type="at",
                    extra_data={"at_qq": at_qq, "at_name": at_name},
                ))
            elif isinstance(component, Node):
                # 嵌套 Node（递归处理）
                nested_messages = self._extract_messages_from_node(component)
                messages.extend(nested_messages)

        return messages

    async def _fetch_forward_messages_recursive(self, forward_id: str, client: OneBotClient, depth: int = 0, max_depth: int = 5) -> list[ChatMessage]:
        """递归获取合并转发消息（支持嵌套）

        Args:
            forward_id: Forward 消息的 ID
            client: OneBotClient 实例
            depth: 当前递归深度
            max_depth: 最大递归深度（防止无限递归）

        Returns:
            提取的消息列表
        """
        if depth >= max_depth:
            logger.warning(f"达到最大递归深度 {max_depth}，停止获取嵌套转发")
            return []

        messages = []

        try:
            # 获取 Forward 内容
            forward_payload = await client.get_forward_msg(forward_id)

            if not forward_payload:
                logger.warning(f"无法获取 Forward {forward_id} 的内容")
                return []

            logger.info(f"[深度{depth}] 成功获取 Forward 内容，原始结构: {list(forward_payload.keys())}")

            # 直接从原始 payload 中提取消息
            raw_messages = forward_payload.get('messages', [])
            logger.info(f"[深度{depth}] 原始消息数量: {len(raw_messages)}")

            if not raw_messages:
                return []

            # 解析每条消息
            for msg_data in raw_messages:
                # 提取发送者信息
                sender_info = msg_data.get('sender', {})
                sender_name = sender_info.get('card') or sender_info.get('nickname', '未知')
                sender_id = str(sender_info.get('user_id', ''))

                # 提取时间戳
                timestamp = msg_data.get('time', 0)
                time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") if timestamp else ""

                # 优先使用 raw_message（包含完整内容）
                raw_text = msg_data.get('raw_message', '')

                # 提取消息内容（处理各种类型）
                msg_content = msg_data.get('message', [])

                if not msg_content and raw_text:
                    # 如果没有 message 数组，但有 raw_message，直接使用
                    messages.append(ChatMessage(
                        sender_name=sender_name,
                        sender_id=sender_id,
                        content=raw_text,
                        timestamp=time_str,
                        msg_type="text",
                    ))
                    continue

                # 处理消息数组中的各种类型
                text_parts = []
                has_special_content = False

                for seg in msg_content:
                    seg_type = seg.get('type', '')
                    seg_data = seg.get('data', {})

                    if seg_type == 'text':
                        text_parts.append(seg_data.get('text', ''))
                    elif seg_type == 'face':
                        # QQ 表情 - 使用 QQ 官方 CDN
                        face_id = seg_data.get('id', '')
                        messages.append(ChatMessage(
                            sender_name=sender_name,
                            sender_id=sender_id,
                            content=f"[表情{face_id}]",
                            timestamp=time_str,
                            msg_type="face",
                            extra_data={"face_id": face_id},
                        ))
                        has_special_content = True
                    elif seg_type == 'image':
                        # 图片消息 - 检查多个可能的URL字段
                        img_url = seg_data.get('url') or seg_data.get('file_url') or seg_data.get('image_url') or seg_data.get('file') or ''
                        if img_url:
                            messages.append(ChatMessage(
                                sender_name=sender_name,
                                sender_id=sender_id,
                                content="",
                                timestamp=time_str,
                                msg_type="image",
                                extra_data={"url": img_url},
                            ))
                            has_special_content = True
                        else:
                            # 没有URL，记录警告
                            logger.warning(f"图片消息缺少URL: {seg_data}")
                            messages.append(ChatMessage(
                                sender_name=sender_name,
                                sender_id=sender_id,
                                content="图片",
                                timestamp=time_str,
                                msg_type="image",
                                extra_data={"url": ""},
                            ))
                            has_special_content = True
                    elif seg_type == 'at':
                        at_qq = seg_data.get('qq', '')
                        text_parts.append(f"@{at_qq}")
                    elif seg_type == 'reply':
                        # 引用消息
                        reply_id = seg_data.get('id', '')
                        text_parts.append(f"[回复消息{reply_id}]")
                    elif seg_type == 'forward':
                        # 嵌套的合并转发 - 作为卡片保留，不展开
                        nested_forward_id = seg_data.get('id', '')
                        if nested_forward_id:
                            logger.info(f"[深度{depth}] 发现嵌套转发，ID: {nested_forward_id}")
                            # 递归获取嵌套的消息
                            nested_messages = await self._fetch_forward_messages_recursive(
                                nested_forward_id, client, depth + 1, max_depth
                            )
                            # 创建一个 forward 类型的消息，包含嵌套内容
                            messages.append(ChatMessage(
                                sender_name=sender_name,
                                sender_id=sender_id,
                                content=f"聊天记录",
                                timestamp=time_str,
                                msg_type="forward",
                                extra_data={"message_count": len(nested_messages)},
                                nested_messages=nested_messages,
                            ))
                            has_special_content = True
                    elif seg_type == 'file':
                        # 文件消息 - 按 file → file_name → filename → name 依次兜底
                        file_name = seg_data.get('file') or seg_data.get('file_name') or seg_data.get('filename') or seg_data.get('name') or '未知文件'
                        file_size = seg_data.get('file_size', 0) or seg_data.get('size', 0)
                        file_url = seg_data.get('url') or seg_data.get('file_url') or ''
                        messages.append(ChatMessage(
                            sender_name=sender_name,
                            sender_id=sender_id,
                            content=file_name,
                            timestamp=time_str,
                            msg_type="file",
                            extra_data={"size": file_size, "file_url": file_url},
                        ))
                        has_special_content = True
                    elif seg_type == 'video':
                        # 视频消息 - file → url → video_url 依次兜底
                        video_url = seg_data.get('file') or seg_data.get('url') or seg_data.get('video_url') or seg_data.get('file_url') or ''
                        thumb_url = seg_data.get('thumb') or seg_data.get('cover') or seg_data.get('thumbnail') or ''
                        messages.append(ChatMessage(
                            sender_name=sender_name,
                            sender_id=sender_id,
                            content="",
                            timestamp=time_str,
                            msg_type="video",
                            extra_data={"url": video_url, "thumb": thumb_url},
                        ))
                        has_special_content = True
                    else:
                        # 其他未知类型
                        text_parts.append(f"[{seg_type}]")

                # 如果有文本内容，添加为一条消息
                if text_parts or not has_special_content:
                    content = ''.join(text_parts) if text_parts else raw_text
                    if content:  # 只添加非空消息
                        messages.append(ChatMessage(
                            sender_name=sender_name,
                            sender_id=sender_id,
                            content=content,
                            timestamp=time_str,
                            msg_type="text",
                        ))

            logger.info(f"[深度{depth}] 从 Forward 提取了 {len(messages)} 条消息")
            return messages

        except Exception as e:
            logger.exception(f"[深度{depth}] 获取 Forward 内容时出错: {e}")
            return []

    async def _extract_messages_from_event(self, event: AstrMessageEvent) -> list[ChatMessage]:
        """从消息中提取聊天记录

        支持三种模式：
        1. 直接发送合并转发消息（推荐）-> 提取所有子消息
        2. 引用的是合并转发消息（Forward）-> 递归获取
        3. 引用的是普通消息 -> 提取引用的那条消息本身
        """
        messages = []

        # 优先处理直接发送的 Node（合并转发）
        for component in event.get_messages():
            if isinstance(component, Node):
                logger.info(f"找到直接发送的 Node 组件")
                extracted = self._extract_messages_from_node(component)
                messages.extend(extracted)
                logger.info(f"从 Node 提取了 {len(extracted)} 条消息")
                return messages

        # 查找 Reply 组件
        for component in event.get_messages():
            if isinstance(component, Reply):
                logger.info(f"找到 Reply 组件，chain 长度: {len(component.chain or [])}")

                # 检查是否有 Forward（合并转发的引用）
                for quoted in component.chain or []:
                    logger.info(f"Reply 中的组件: {type(quoted).__name__}")

                    if isinstance(quoted, Forward):
                        # Forward 只有 ID，需要通过 API 获取内容
                        forward_id = getattr(quoted, 'id', None)
                        logger.info(f"找到 Forward 组件，ID: {forward_id}")

                        if not HAS_ONEBOT_CLIENT:
                            await self._reply(event, "❌ 抱歉，无法提取 Forward 消息（缺少必要组件）")
                            return []

                        if not forward_id:
                            await self._reply(event, "❌ Forward 消息没有 ID，无法提取")
                            return []

                        try:
                            # 使用 OneBotClient 递归获取 Forward 内容
                            client = OneBotClient(event)
                            nested_messages = await self._fetch_forward_messages_recursive(forward_id, client)

                            if not nested_messages:
                                logger.warning(f"无法获取 Forward {forward_id} 的内容")
                                await self._reply(event, "❌ 无法获取合并转发消息内容（可能消息已过期）")
                                return []

                            logger.info(f"递归提取完成，总共 {len(nested_messages)} 条消息")

                            # 顶层也包装成forward类型的卡片
                            messages.append(ChatMessage(
                                sender_name="",
                                sender_id="",
                                content="聊天记录",
                                timestamp="",
                                msg_type="forward",
                                extra_data={"message_count": len(nested_messages)},
                                nested_messages=nested_messages,
                            ))
                            return messages

                        except Exception as e:
                            logger.exception(f"获取 Forward 内容时出错: {e}")
                            await self._reply(event, f"❌ 提取失败: {e}")
                            return []

                    elif isinstance(quoted, Node):
                        # Node 包含完整内容
                        logger.info("引用的是 Node 组件")
                        extracted = self._extract_messages_from_node(quoted)
                        messages.extend(extracted)
                        logger.info(f"从引用的 Node 提取了 {len(extracted)} 条消息")

                # 如果没有 Forward/Node，提取普通消息
                if not messages:
                    logger.info("引用的是普通消息，尝试提取")
                    sender_name = getattr(component, 'sender_name', None) or getattr(component, 'nickname', None) or "未知"
                    sender_id = str(getattr(component, 'sender_id', '') or '')
                    logger.info(f"发送者: {sender_name}, ID: {sender_id}")

                    # 提取引用消息的内容
                    text_parts = []
                    for quoted in component.chain or []:
                        if isinstance(quoted, Plain):
                            text_parts.append(normalize_text(quoted.text))
                        elif isinstance(quoted, Image):
                            img_url = getattr(quoted, 'url', '') or getattr(quoted, 'file', '')
                            messages.append(ChatMessage(
                                sender_name=sender_name,
                                sender_id=sender_id,
                                content="",
                                msg_type="image",
                                extra_data={"url": img_url},
                            ))
                        elif isinstance(quoted, At):
                            at_qq = str(getattr(quoted, 'qq', ''))
                            at_name = str(getattr(quoted, 'name', '')) or at_qq
                            text_parts.append(f"@{at_name}")

                    # 如果有文本内容，添加为一条消息
                    if text_parts:
                        messages.append(ChatMessage(
                            sender_name=sender_name,
                            sender_id=sender_id,
                            content=" ".join(text_parts),
                            msg_type="text",
                        ))
                        logger.info(f"提取了文本消息: {' '.join(text_parts)[:50]}")

        logger.info(f"总共提取了 {len(messages)} 条消息")
        return messages

    def _generate_txt(self, messages: list[ChatMessage]) -> str:
        """生成 txt 格式内容"""
        lines = ["=" * 50, "聊天记录", "=" * 50, ""]

        for msg in messages:
            lines.append(msg.to_txt_line())

        lines.extend(["", "=" * 50, f"共 {len(messages)} 条消息", "=" * 50])

        return "\n".join(lines)

    def _generate_html(self, messages: list[ChatMessage]) -> str:
        """生成 HTML 格式内容（美观版）"""
        # HTML 头部和样式
        html_head = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>聊天记录</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .chat-container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }

        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 24px;
            text-align: center;
        }

        .chat-header h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .chat-header .meta {
            font-size: 14px;
            opacity: 0.9;
        }

        .chat-messages {
            padding: 24px;
            max-height: 70vh;
            overflow-y: auto;
        }

        .msg-item {
            display: flex;
            margin-bottom: 20px;
            animation: fadeIn 0.3s ease-in;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .msg-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            position: relative;
            margin-right: 12px;
            flex-shrink: 0;
            overflow: hidden;
        }

        .msg-avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .msg-avatar-fallback {
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            position: absolute;
            top: 0;
            left: 0;
        }

        .msg-bubble-self .msg-avatar {
            order: 2;
            margin-right: 0;
            margin-left: 12px;
        }

        .msg-bubble-self .msg-avatar-fallback {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }

        .forward-card {
            background: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
            margin: 4px 0;
        }

        .forward-header {
            padding: 12px;
            cursor: pointer;
            user-select: none;
            transition: background 0.2s;
            position: relative;
        }

        .forward-header:hover {
            background: #f0f0f0;
        }

        .forward-header.expanded {
            background: #e8f0fe;
        }

        .forward-title {
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 6px;
            color: #333;
        }

        .forward-preview {
            font-size: 13px;
            color: #666;
            line-height: 1.6;
            margin-bottom: 6px;
        }

        .forward-count {
            font-size: 12px;
            color: #667eea;
            text-align: right;
            transition: transform 0.3s;
        }

        .forward-header.expanded .forward-count {
            transform: rotate(180deg);
        }

        .forward-content {
            border-top: 1px solid #e0e0e0;
            padding: 12px;
            background: white;
            max-height: 500px;
            overflow-y: auto;
            display: none;
        }

        .forward-content.show {
            display: block;
            animation: slideDown 0.3s ease-out;
        }

        @keyframes slideDown {
            from {
                opacity: 0;
                max-height: 0;
            }
            to {
                opacity: 1;
                max-height: 500px;
            }
        }

        .forward-content .msg-item {
            margin-bottom: 12px;
        }

        /* 嵌套层级样式 */
        .forward-content .forward-card {
            margin-left: 12px;
            border-left: 3px solid #667eea;
        }

        .forward-content .forward-content .forward-card {
            margin-left: 12px;
            border-left: 3px solid #f093fb;
        }

        .msg-content {
            flex: 1;
            max-width: 70%;
        }

        .msg-bubble-self .msg-content {
            order: 1;
        }

        .msg-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }

        .msg-name {
            font-size: 14px;
            font-weight: 600;
            color: #333;
        }

        .msg-time {
            font-size: 12px;
            color: #999;
        }

        .msg-body {
            background: #f5f5f5;
            padding: 12px 16px;
            border-radius: 12px;
            word-wrap: break-word;
        }

        .msg-bubble-self .msg-body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .msg-text {
            font-size: 15px;
            line-height: 1.6;
        }

        .msg-image img {
            max-width: 100%;
            max-height: 400px;
            border-radius: 8px;
            display: block;
        }

        .msg-face {
            display: inline-block;
        }

        .face-emoji {
            width: 48px;
            height: 48px;
            vertical-align: middle;
        }

        .msg-video {
            font-size: 14px;
            color: #667eea;
        }

        .msg-video a {
            color: #667eea;
            text-decoration: none;
        }

        .msg-video a:hover {
            text-decoration: underline;
        }

        .msg-file {
            font-size: 14px;
            color: #666;
            background: #f5f5f5;
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 3px solid #667eea;
        }

        .msg-bubble-self .msg-file {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border-left-color: white;
        }

        .msg-placeholder {
            font-size: 14px;
            color: #666;
            font-style: italic;
        }

        .msg-bubble-self .msg-placeholder {
            color: rgba(255, 255, 255, 0.8);
        }

        .msg-at {
            color: #667eea;
            font-weight: 600;
        }

        .msg-bubble-self .msg-at {
            color: #fff;
            background: rgba(255, 255, 255, 0.2);
            padding: 2px 6px;
            border-radius: 4px;
        }

        .chat-footer {
            background: #f9f9f9;
            padding: 16px 24px;
            text-align: center;
            color: #666;
            font-size: 13px;
            border-top: 1px solid #eee;
        }

        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }

        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>💬 聊天记录</h1>
            <div class="meta">导出时间：''' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '''</div>
        </div>
        <div class="chat-messages">
'''

        # 消息主体
        message_html = ""
        for i, msg in enumerate(messages):
            # 简单判断：如果 sender_id 包含特定 bot 标识，认为是 self
            is_self = "bot" in msg.sender_id.lower() or msg.sender_name == "丛雨"
            message_html += msg.to_html_bubble(is_self)

        # HTML 尾部
        html_footer = f'''
        </div>
        <div class="chat-footer">
            共 {len(messages)} 条消息 | 由 AstrBot 聊天记录提取插件生成
        </div>
    </div>
<script>
function toggleForward(cardId) {{
    const content = document.getElementById(cardId);
    const header = content.previousElementSibling;

    if (content.style.display === 'none' || content.style.display === '') {{
        content.style.display = 'block';
        header.classList.add('expanded');
    }} else {{
        content.style.display = 'none';
        header.classList.remove('expanded');
    }}
}}
</script>
</body>
</html>
'''

        return html_head + message_html + html_footer

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE, priority=100)
    async def handle_extract(self, event: AstrMessageEvent):
        """处理提取命令"""
        text = event.get_message_str()

        # 获取命令触发词列表
        commands = self.config.get("extract_commands", ["提取", "导出"])
        if not isinstance(commands, list):
            commands = ["提取", "导出"]

        # 提取格式
        format_type = extract_command_and_format(text, commands)

        if not format_type:
            # 不是提取命令，不处理
            return

        logger.info(f"聊天记录提取插件命中: 格式={format_type}")
        event.stop_event()  # 阻止后续处理

        # 提取消息
        try:
            messages = await self._extract_messages_from_event(event)
            logger.info(f"提取完成，消息数量: {len(messages)}")
        except Exception as e:
            logger.exception(f"提取消息时出错: {e}")
            await self._reply(event, f"❌ 提取失败: {e}")
            return

        if not messages:
            await self._reply(event, self._setting("no_forward_reply", "请将聊天记录转发给丛雨（不要引用），然后发送 提取 txt 或 提取 html~"))
            return

        try:
            if format_type == "txt":
                # txt 格式 - 保存文件并发送
                content = self._generate_txt(messages)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"chat_{timestamp}.txt"
                filepath = self.output_root / filename

                filepath.write_text(content, encoding="utf-8")

                # 发送文件 - 使用 File 组件
                file_component = File(name=filename, file=str(filepath))
                await event.send(event.chain_result([file_component]))
                await self._reply(event, self._setting("success_reply_txt", "✅ 提取成功，已整理成 txt 格式~"))

                logger.info("聊天记录提取成功(txt): %s (%d 条消息)", filepath.name, len(messages))

            else:  # html
                # html 格式 - 保存文件并发送
                content = self._generate_html(messages)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"chat_{timestamp}.html"
                filepath = self.output_root / filename

                filepath.write_text(content, encoding="utf-8")

                # 发送文件 - 使用 File 组件
                file_component = File(name=filename, file=str(filepath))
                await event.send(event.chain_result([file_component]))
                await self._reply(event, self._setting("success_reply_html", "✅ 提取成功，已整理成 html 格式~"))

                logger.info("聊天记录提取成功(html): %s (%d 条消息)", filepath.name, len(messages))

        except Exception as exc:
            logger.exception("聊天记录提取失败: %s", exc)
            await self._reply(event, f"❌ 提取失败: {str(exc)[:100]}")
