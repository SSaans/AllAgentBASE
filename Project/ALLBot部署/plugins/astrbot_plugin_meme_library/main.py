"""Store and retrieve group-member images by keyword."""

from __future__ import annotations

import asyncio
import hashlib
import random
import re
import zipfile
import tarfile
import shutil
from pathlib import Path

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Image, Plain, Reply, Node, File
from astrbot.api.star import Context, Star

from .library_ui import LibraryPages

_KEYWORD_PART = r'[^\\/:*?"<>|\r\n]+?'
_RESERVED_WINDOWS_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".img"}


def normalize_keyword(raw: str) -> str | None:
    """Return a safe, stable directory name or None for invalid input."""
    keyword = " ".join((raw or "").split()).strip(" .")
    if not keyword or len(keyword) > 64:
        return None
    if keyword.split(".", 1)[0].casefold() in _RESERVED_WINDOWS_NAMES:
        return None
    if any(ord(char) < 32 or char in '\\/:*?"<>|' for char in keyword):
        return None
    return keyword


def parse_store_request(
    text: str, command: str = "/c", suffix: str = ".jpg"
) -> str | None:
    if not command or not suffix:
        return None
    pattern = rf"(?:^|\s){re.escape(command)}\s+(?P<keyword>{_KEYWORD_PART}){re.escape(suffix)}(?:\s|$)"
    match = re.search(pattern, text or "", re.IGNORECASE)
    return normalize_keyword(match.group("keyword")) if match else None


def parse_fetch_request(
    text: str, suffix: str = ".jpg", multiplier: str = "x"
) -> tuple[str, int] | None:
    if not suffix or not multiplier:
        return None
    pattern = rf"\s*(?P<keyword>{_KEYWORD_PART}){re.escape(suffix)}(?:{re.escape(multiplier)}(?P<count>\d+))?\s*"
    match = re.fullmatch(pattern, text or "", re.IGNORECASE)
    if not match:
        return None
    keyword = normalize_keyword(match.group("keyword"))
    if not keyword:
        return None
    count_text = match.group("count")
    # Very large requests mean all available images; avoid int digit limits.
    significant = (count_text or "1").lstrip("0") or "0"
    count = int(significant) if len(significant) <= 18 else 10**18
    if count < 1:
        return None
    return keyword, count


def has_store_command_prefix(text: str, commands: list[str]) -> bool:
    """Check if text contains any store command prefix (like /ct)."""
    if not text or not commands:
        return False
    text_lower = text.lower()
    return any(cmd.lower() in text_lower for cmd in commands if cmd)


def detect_image_suffix(data: bytes) -> str:
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if data.startswith(b"BM"):
        return ".bmp"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return ".img"


def write_exclusive(path: Path, data: bytes) -> bool:
    """Create one content-addressed file without ever overwriting an existing file."""
    created = False
    try:
        with path.open("xb") as output:
            created = True
            output.write(data)
        return True
    except FileExistsError:
        return False
    except Exception:
        if created:
            path.unlink(missing_ok=True)
        raise


def original_plain_text(event: AstrMessageEvent) -> str:
    """Read raw Plain segments because WakingStage may strip '/' from message_str."""
    components = list(getattr(event.message_obj, "message", None) or [])
    text = "".join(
        component.text for component in components if isinstance(component, Plain)
    )
    return text if text else (event.message_str or "")


def select_source_images(event: AstrMessageEvent) -> list[Image]:
    """Use all current images; only fall back to quoted images when none exist.

    A reply plus new images must not accidentally archive the quoted history too.
    Content-addressed writes handle repeated images, rather than URL deduplication.
    """
    components = list(getattr(event.message_obj, "message", None) or [])
    images = [component for component in components if isinstance(component, Image)]
    if images:
        return images
    return [
        quoted
        for component in components
        if isinstance(component, Reply)
        for quoted in component.chain or []
        if isinstance(quoted, Image)
    ]


def select_source_image(event: AstrMessageEvent) -> Image | None:
    """Compatibility helper for existing integrations expecting a single image."""
    images = select_source_images(event)
    return images[0] if images else None


def select_source_file(event: AstrMessageEvent) -> File | None:
    """Select file from current message or quoted message."""
    components = list(getattr(event.message_obj, "message", None) or [])
    files = [component for component in components if isinstance(component, File)]
    if files:
        return files[0]
    # Check quoted message
    for component in components:
        if isinstance(component, Reply):
            for quoted in component.chain or []:
                if isinstance(quoted, File):
                    return quoted
    return None


def is_archive_file(filename: str) -> bool:
    """Check if filename is a supported archive format."""
    if not filename:
        return False
    lower = filename.lower()
    return lower.endswith(('.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tgz'))


async def extract_images_from_archive(archive_path: Path, temp_dir: Path) -> list[Path]:
    """Extract all images from archive file. Returns list of image paths."""
    def _extract():
        images = []
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Try ZIP first
            if zipfile.is_zipfile(archive_path):
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    zf.extractall(extract_dir)
            # Try TAR formats
            elif tarfile.is_tarfile(archive_path):
                with tarfile.open(archive_path, 'r:*') as tf:
                    tf.extractall(extract_dir)
            else:
                logger.warning(f"Unsupported archive format: {archive_path.name}")
                return []

            # Find all image files recursively
            for file_path in extract_dir.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in _IMAGE_SUFFIXES:
                    images.append(file_path)

            return images
        except Exception as exc:
            logger.warning(f"Failed to extract archive {archive_path.name}: {exc}")
            return []

    return await asyncio.to_thread(_extract)


class MemeLibraryPlugin(LibraryPages, Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.library_root = Path(__file__).resolve().parents[2] / "meme_library"
        self.library_root.mkdir(parents=True, exist_ok=True)
        self._write_lock = asyncio.Lock()
        self._last_sent: dict[tuple[str, str], Path] = {}
        self.register_library_pages()
        logger.info("群友图片库插件已加载，图库目录: %s", self.library_root)

    def _setting(self, name: str, default: str) -> str:
        value = self.config.get(name, default)
        return value if isinstance(value, str) else default

    async def _reply(self, event: AstrMessageEvent, name: str, default: str):
        text = self._setting(name, default)
        if text:
            await event.send(event.plain_result(text))

    def _keyword_dir(self, keyword: str) -> Path:
        if normalize_keyword(keyword) != keyword:
            raise ValueError("关键词含有无效字符")
        target = self.library_root / keyword
        if target.resolve().parent != self.library_root.resolve():
            raise ValueError("关键词目录超出图库范围")
        return target

    async def _store_image(self, keyword: str, image: Image) -> bool:
        source_path = Path(await image.convert_to_file_path())
        data = await asyncio.to_thread(source_path.read_bytes)
        return await self._store_bytes(keyword, data)

    async def _store_bytes(self, keyword: str, data: bytes) -> bool:
        if not data:
            raise ValueError("图片内容为空")

        digest = hashlib.sha256(data).hexdigest()
        destination_dir = self._keyword_dir(keyword)
        destination = destination_dir / f"{digest}{detect_image_suffix(data)}"

        async with self._write_lock:
            await asyncio.to_thread(destination_dir.mkdir, parents=True, exist_ok=True)
            stored = await asyncio.to_thread(write_exclusive, destination, data)
            if not stored:
                return False
            if destination.stat().st_size != len(data):
                destination.unlink(missing_ok=True)
                raise OSError("图片写入不完整")
        return True

    async def _available_images(self, keyword: str) -> list[Path]:
        directory = self._keyword_dir(keyword)
        if not directory.is_dir():
            return []

        def list_images() -> list[Path]:
            return sorted(
                (
                    item
                    for item in directory.iterdir()
                    if item.is_file() and item.suffix.casefold() in _IMAGE_SUFFIXES
                ),
                key=lambda item: item.name.casefold(),
            )

        return await asyncio.to_thread(list_images)

    def _is_owner(self, event: AstrMessageEvent) -> bool:
        config = self.context.get_config(umo=event.unified_msg_origin)
        admin_ids = {str(item).strip() for item in config.get("admins_id", [])}
        return str(event.get_sender_id()).strip() in admin_ids

    def _choose_images(
        self, session: str, keyword: str, images: list[Path], count: int
    ) -> list[Path]:
        """Choose distinct images; avoid the previous single result when possible."""
        key = (session, keyword)
        count = min(count, len(images))
        pool = images
        if count == 1 and len(images) > 1:
            pool = [path for path in images if path != self._last_sent.get(key)]
        selected = random.sample(pool, count)
        if selected:
            self._last_sent[key] = selected[-1]
            if len(self._last_sent) > 1024:
                self._last_sent.pop(next(iter(self._last_sent)))
        return selected

    def _is_muted(self, event: AstrMessageEvent) -> bool:
        """Check if bot is currently muted by querying mute plugin state."""
        try:
            import time
            mute_state_path = (
                Path(__file__).resolve().parents[2]
                / "plugin_data"
                / "astrbot_plugin_mute"
                / "mute_state.json"
            )
            if not mute_state_path.exists():
                return False

            import json
            state = json.loads(mute_state_path.read_text(encoding="utf-8"))
            targets = state.get("targets", {})
            if not isinstance(targets, dict):
                return False

            now = time.time()
            group_id = str(event.get_group_id() or "").strip()
            # Check both global mute and group-specific mute
            for key in ["global", f"group:{group_id}"]:
                item = targets.get(key)
                if isinstance(item, dict):
                    deadline = float(item.get("deadline", 0) or 0)
                    if deadline > now:
                        return True
            return False
        except Exception:
            # If we can't read mute state, assume not muted
            return False

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE, priority=20)
    async def handle_group_image_library(self, event: AstrMessageEvent):
        """Store or fetch images using the editable phrases in plugin settings."""
        sender_id = str(event.get_sender_id()).strip()
        if not sender_id or sender_id == str(event.get_self_id()).strip():
            return

        # Check mute state at entry - respect mute plugin
        if self._is_muted(event):
            return

        text = original_plain_text(event)
        command = self._setting("store_command", "/c").strip() or "/c"
        suffix = self._setting("image_suffix", ".jpg").strip() or ".jpg"
        multiplier = self._setting("count_marker", "x").strip() or "x"

        # All possible command triggers for both store and hint
        all_commands = list(dict.fromkeys([command, "/ct", "加图"]))

        # Aliases are parsed directly, independent of core wake_prefix/commands.
        # Keep /c available even when the editable primary phrase is customized.
        store_keyword = next(
            (
                keyword
                for phrase in dict.fromkeys((command, "/c", "加图"))
                if (keyword := parse_store_request(text, phrase, suffix))
            ),
            None,
        )
        if store_keyword:
            source_images = select_source_images(event)
            source_file = select_source_file(event) if not source_images else None

            # Check if user sent an archive file
            if not source_images and source_file:
                if is_archive_file(source_file.name):
                    event.stop_event()
                    try:
                        # Download archive file using async method
                        archive_path = Path(await source_file.get_file())
                        if not archive_path.exists():
                            await event.send(event.plain_result("压缩包下载失败..."))
                            return

                        # Extract images to temp directory in library root
                        temp_dir = self.library_root / ".temp_extract" / f"extract_{int(asyncio.get_event_loop().time() * 1000)}"
                        temp_dir.mkdir(parents=True, exist_ok=True)

                        extracted_images = await extract_images_from_archive(
                            archive_path, temp_dir
                        )

                        if not extracted_images:
                            await event.send(
                                event.plain_result("压缩包里没有找到图片...")
                            )
                            # Cleanup
                            shutil.rmtree(temp_dir, ignore_errors=True)
                            return

                        # Store all extracted images
                        stored_count = 0
                        for image_path in extracted_images:
                            try:
                                data = await asyncio.to_thread(image_path.read_bytes)
                                stored = await self._store_bytes(store_keyword, data)
                                if stored:
                                    stored_count += 1
                            except Exception as exc:
                                logger.warning(
                                    f"存储压缩包图片失败 {image_path.name}: {type(exc).__name__}"
                                )

                        # Cleanup temp directory
                        shutil.rmtree(temp_dir, ignore_errors=True)

                        # Reply with count
                        if stored_count == 1:
                            await self._reply(event, "stored_reply", "存好了")
                        elif stored_count > 1:
                            template = self._setting(
                                "stored_many_reply", "{count} 张都存好了"
                            )
                            if template:
                                await event.send(
                                    event.plain_result(
                                        template.replace("{count}", str(stored_count))
                                    )
                                )
                        else:
                            await event.send(
                                event.plain_result("压缩包里的图片都存过了")
                            )
                        return
                    except Exception as exc:
                        logger.exception(f"处理压缩包失败: {exc}")
                        await event.send(event.plain_result("处理压缩包失败..."))
                        # Cleanup on error
                        try:
                            if 'temp_dir' in locals() and temp_dir.exists():
                                shutil.rmtree(temp_dir, ignore_errors=True)
                        except:
                            pass
                        return

            if not source_images:
                # User entered correct store format but no image or file
                event.stop_event()
                hint_template = self._setting(
                    "store_command_hint_reply",
                    "请输入 /ct xx.jpg 就能看图啦，支持 x2 等查看多张图~"
                )
                hint = hint_template.replace("{suffix}", suffix)
                hint = hint.replace("{multiplier}", multiplier)
                await event.send(event.plain_result(hint))
                return
            event.stop_event()
            stored_count = 0
            outcomes = []
            for index, source_image in enumerate(source_images, start=1):
                try:
                    stored = await self._store_image(store_keyword, source_image)
                except Exception as exc:
                    # Download exceptions may contain signed URLs: never log them.
                    logger.warning(
                        f"保存群友图片第 {index} 张失败（{type(exc).__name__}）"
                    )
                    outcomes.append((index, "store_failed_reply", "这张图没存下来..."))
                    continue
                if stored:
                    stored_count += 1
                else:
                    outcomes.append((index, "duplicate_reply", "这张已经存过了"))
            if stored_count == 1:
                await self._reply(event, "stored_reply", "存好了")
            elif stored_count > 1:
                template = self._setting("stored_many_reply", "{count} 张都存好了")
                # Literal replacement lets users write other braces freely.
                if template:
                    await event.send(
                        event.plain_result(
                            template.replace("{count}", str(stored_count))
                        )
                    )
            for index, setting, default in outcomes:
                reply = self._setting(setting, default)
                if reply:
                    if len(source_images) > 1:
                        reply = f"第 {index} 张：{reply}"
                    await event.send(event.plain_result(reply))
            return

        fetch = parse_fetch_request(text, suffix, multiplier)
        if fetch is None:
            # Check if user entered store command but format is wrong
            if has_store_command_prefix(text, all_commands):
                event.stop_event()
                hint_template = self._setting(
                    "store_command_hint_reply",
                    "请输入 /ct xx.jpg 就能看图啦，支持 x2 等查看多张图~"
                )
                hint = hint_template.replace("{suffix}", suffix)
                hint = hint.replace("{multiplier}", multiplier)
                await event.send(event.plain_result(hint))
            return

        keyword, requested_count = fetch
        event.stop_event()
        images = await self._available_images(keyword)
        if not images:
            if self._is_owner(event):
                await self._reply(
                    event, "owner_missing_reply", "主人换个关键词逝世吧..."
                )
            else:
                await self._reply(event, "missing_reply", "换个关键词逝世吧...")
            return

        unlimited_ids = self.config.get("unlimited_qq_ids", [])
        if not isinstance(unlimited_ids, list):
            unlimited_ids = []
        unlimited_ids = {
            str(item).strip() for item in unlimited_ids if str(item).strip()
        }
        applies = sender_id not in unlimited_ids
        try:
            limit = max(1, int(self.config.get("max_images_per_request", 20)))
        except (TypeError, ValueError):
            limit = 20
        limited = applies and requested_count > limit
        send_count = min(requested_count, limit) if applies else requested_count
        selected = self._choose_images(
            event.unified_msg_origin, keyword, images, send_count
        )

        # Check if packing is enabled and we have multiple images
        pack_enabled = self.config.get("pack_multiple_images", True)
        if pack_enabled and len(selected) > 1:
            try:
                cards_per_batch = max(
                    1, int(self.config.get("images_per_card", 10))
                )
            except (TypeError, ValueError):
                cards_per_batch = 10

            bot_qq = str(event.get_self_id())
            bot_name = "丛雨"

            for batch_start in range(0, len(selected), cards_per_batch):
                batch = selected[batch_start : batch_start + cards_per_batch]

                # Check mute before each card send
                if self._is_muted(event):
                    logger.info(
                        "群友图片库：检测到禁言状态，已发送 %d/%d 张后停止",
                        batch_start,
                        len(selected),
                    )
                    return

                # Create forward node with images
                node_content = [Image(file=str(img)) for img in batch]
                node = Node(uin=bot_qq, name=bot_name, content=node_content)

                await event.send(event.chain_result([node]))

                # Small delay between cards
                if batch_start + cards_per_batch < len(selected):
                    await asyncio.sleep(0.6)
        else:
            # Pack disabled or single image - send one by one
            for index, image_path in enumerate(selected):
                if self._is_muted(event):
                    logger.info(
                        "群友图片库：检测到禁言状态，已发送 %d/%d 张后停止",
                        index,
                        len(selected),
                    )
                    return
                await event.send(event.image_result(str(image_path)))
                if index + 1 < len(selected):
                    await asyncio.sleep(0.6)

        if limited:
            await self._reply(event, "over_limit_reply", "再发就刷屏啦...")
        elif requested_count > len(images):
            await self._reply(event, "exhausted_reply", "一张也没有了...")
