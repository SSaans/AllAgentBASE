# 表情包同步（StickerSync）变更日志

## [2026-09-20] 规划 Agent — 新子项目立项：表情包同步（StickerSync）

**完成的工作**：

- ✅ 按用户指派立项 `Project/表情包同步/`（英文代号 StickerSync）：目标是把表情包收成「一套 = 一个包」的标准资产，存云端、按需拉取、分发到 QQ / Telegram / 微信
- ✅ **调研 QQ / TIM 表情包底层机制**（用户指定项）：
  - `.eif` = 微软 **Compound File Binary（CFB）** 容器；内部为 `1Version.dat` + `Face.dat`（**索引已加密**）+ `Face2.dat` + 数字分组目录（`0–26` 本地分组、`8213` 云端分组）
  - **图片本体未加密**（可用 `compoundfiles` 直接提取）；**`Face.dat` 加密**是保住分组与顺序的拦路虎，社区已有解密成果
  - **云端分组无导出入口、不支持排序**，变通办法：借含本地分组的 `.eif` 导入后「导出全部表情」
  - 本地存储路径已查明（NTQQ Win/macOS、Android、传统 PC QQ 四条）
  - 🔴 **关键否证**：`personal-emoji/Ori` 是**缓存**不是数据源（删掉会被 QQ 重建）→ **单方面往缓存丢图片不会被收进收藏**，"直写缓存"捷径不通
  - 原创贴纸混淆规则：**前 24 字节偶数位 ±1**（社区已逆向），据此可无损提取动态贴纸
  - 上限：QQ 普通 500 / SVIP 1000；微信 300（部分版本 999）—— 本项目的解法是「云端仓库 + 按需装包」，把上限从天花板变成工作台
- ✅ **调研现成项目**（用户指定项），结论：**没有任何项目同时覆盖 QQ + TG + 微信 + 云端**，最接近的 `star-39/moe-sticker-bot`（Go，跨平台贴纸枢纽）不含 QQ/微信 → **本项目有存在价值**
  - QQ 侧：`readme9txt/QQEIF-Extractor`（解析 eif 保排序，仅传统 QQ）、`VanillaNahida/QQFavoriteExtract`（NTQQ 缓存提取 + GUI）、`dogxii/BackupQQEmoji`、`JayMuShui/Encrypted-QQ-Original-Sticker-Decryption`
  - TG 侧：`FHPythonUtils/TStickers`、`yazmeyaa/telegram_sticker_converter`、`SwaggyMacro/LottieViewConvert`
  - 已记录各目标平台写入规格（TG 512 px / 64 KB / 单包 120；微信 GIF ≤ 1 MB、≤ 1024²）
- ✅ **产出核心设计**：
  - **Pack 格式**：`manifest.json` + `stickers/` + `dist/`（产物可重建）
  - 🔑 **关键决策：以图片为真相、把 `.eif` 当产物** —— 避免被腾讯版本迭代绑架，换格式只需换适配器、资产零损失
  - **系统架构**：`core` → `converters` → `adapters/{qq,telegram,wechat}` → `webui` → `sync`，适配器统一 `import_pack / export_pack` 接口，并带 `auto` 字段区分"真一键"与"产物+引导"
- ✅ **产出六阶段实施方案**（Pack 规范 → 读取侧 → 云同步 → 前端 → 写入侧 → 手机侧），每阶段带目标/交付/判据
- ✅ **如实标注能力边界（本 BRD 最重要结论）**：**Telegram 全自动 / QQ 半自动 / 微信仅备料**；明确写入红线 —— **不承诺"一键同步进 QQ/微信"**，因为这两个平台没有开放写入接口

**修改的文件**：
- 新增：`Project/表情包同步/`（`BRD.md`、`README.md`、`Task.md`、`CHANGELOG.md`）
- 修改：根 `BRD.md`（立项登记：状态行、候选清单、已立项子项目说明）、根 `CHANGELOG.md`（本条记录）

**当前状态**：
- ✅ **阶段 0 完成**：立项 + 规划，方案可执行、阶段可验收
- ⏳ **未写任何功能代码**：未 clone 上游、未装依赖、未建代码目录。本轮严格限定在规划职责内（`AGENTS.md` 规划 Agent 边界）
- 🔴 **最大不确定项**：QQ `.eif` 的**写入**（`Face.dat` 加密回写）尚未验证 → 已列为 `Task.md` 任务 10 的目标 A，并预设"图片文件夹 + 导入引导"兜底
- ⚠️ 待用户拍板 4 项：① 能力边界是否接受 ② 首批平台 ③ 云端开放范围 ④ 整体方案

**下一步建议**：
1. 用户先答任务 1、2（边界 + 首批平台），建议 **QQ + Telegram** 优先
2. 用户回复「按这个方案做」后，对开发 Agent 下达：「你是开发 Agent，根据 `DEVELOPMENT.md`，按 `Project/表情包同步/Task.md` 任务 5 开始」
3. 阶段 1 开工前先确认本机 **ffmpeg** 可用性（动图转换依赖）
