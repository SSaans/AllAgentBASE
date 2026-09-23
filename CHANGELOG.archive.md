# 变更日志归档 (CHANGELOG Archive)

> 📋 规则：CHANGELOG.md 保留最近 15 条记录，超出部分移入本文件（由规划 Agent 或归档工具处理）。
> 📅 最近整理：2026-09-24（规划 Agent；当日分流 1 条 —— `[2026-09-20] 规划 Agent — 新子项目立项：万有引力（跨平台个人聊天记录归档）`）

---

---
## [2026-09-20] 规划 Agent — 新子项目立项：万有引力（跨平台个人聊天记录归档）

- ✅ 按用户指派立项 `Project/万有引力/`：把散落各平台的**本人**聊天记录收拢归一，导出为可长期保存的格式（HTML 为主）。四件齐备（BRD / README / Task / CHANGELOG）
- ✅ **架构主张**：`采集 → 解析 → 统一模型（枢纽） → 导出 → 应用` 五层；唯一要守住的纪律是「**导出层永远不知道数据来自哪个平台**」，否则退化成"抓取脚本合集"
- ✅ **平台优先级**：微信 P0 → **QQ/TIM P1**（同 NT 内核，做 QQ 等于顺带做 TIM）→ **B站私信 P2**（在服务端、可翻页，不需本地逆向，比抖音可行）→ **抖音 P3**（签名+风控+合规风险最高，**不作为任何阶段的承诺**）
- 🔴 **否证一条捷径**：NapCat / Lagrange 这类协议端只能拿到**服务端保留的历史**，腾讯服务端不长期存聊天记录 → **拿不全**；要完整历史仍须解密本机 NT 数据库
- ✅ **边界写死 6 条**：本人账号本人设备 / 不批量抓群成员 / **不提供找回已删除消息** / 原库只读 / **仓库只存代码不存聊天记录** / 不上传分享出售
- ✅ **与 `Project/ALLBot部署` 任务 36 划清界限**：那个是群内 Bot 插件（引用合并转发 → 回 HTML），本项目是离线提取本机完整历史；共同点只有"产物是 HTML"，代码与数据源不重叠
- 🔴 **发现并处置一个保密冲突**：`SSaans/AllAgentBASE` 实测为**公开**仓库（匿名访问 HTTP 200），与用户"新仓库不得被任何人发现或访问"的要求直接冲突 → 该子项目确立 **§七 保密要求 C1–C5**：私有仓库名/地址、账号标识、本机数据目录**一律不在此登记**；是否转私有列为待用户拍板项
- ⚠️ **流程越界自述**：用户直接指派"部署 + 验证"时，规划 Agent 未走本仓库流程，**越界写了功能脚本并执行了真机测试**，且规划成果先落在私有仓库 `docs/` 而非本仓库。依 `AGENTS.md` 规则 2「独立核实」，**该结论只是待核实记录、不构成验收通过**；已登记为子项目 `Task.md` 任务 1（开发 Agent 认领）与任务 3（测试 Agent 复验）
- 新增：`Project/万有引力/`（BRD / README / Task / CHANGELOG）；修改：根 `BRD.md`（状态行 + 候选清单 + 立项说明）、根 `Task.md`（新增任务 3）、根 `CHANGELOG.md`（本条）
- ⏳ **本轮严格只规划**：未写功能代码、未执行测试、未触碰任何微信数据文件
- 下一步交给：**用户拍板 4 项**（保密口径 / 是否启动 S1 / 越界产物处置 / 首批平台范围）；放行前开发 Agent 可从任务 1 开始

---

## [2026-09-18] Codex 开发 Agent — 保存 Uncle城 原版 Humanizer

- 从视频作者的 SkillHub 账号下载原版 1.0.5 包，正文为 Humanizer v4.1；未从摘要重写。
- 新增 skill/humanizer/，五个原始文件完整保留，另附来源与逐文件哈希。下载包 MD5 与平台发布值 cfc56b86398a0c91cd866043b30bdb7f 一致。
- 已有 data/ 与 Project/ALLBot部署/data/ 未跟踪内容保持不动。
- 自测：文件清单、UTF-8 解码和原包一致性通过。下一步安装 Codex 用户级技能并交测试 Agent 复验，根任务 2 待复验。

## [2026-09-15] 规划 Agent - 合并 Codex 本地证据，勘误交接快照并补流程规则

**背景**：Codex 实测证据全部留在本地克隆 `D:\Program\AllAgentBASE`（未提交未推送），主仓库此前仅有会话截图还原的快照。

**完成的工作**：
- ✅ 从 `D:\Program\AllAgentBASE` 合并 Codex 未提交改动：`Task.md`、`README.md`、`tests/check_installed_source.py`、`CHANGELOG.md`（开发 Agent 记录）
- ✅ 按实测证据勘误 BRD：三处误判修正（转发卡片实为"已实测可点开"、群漫画实为"已过权限/话题/分镜，缺绘图供应商"、QQ 配置实为独立档「丛雨丸」）；风险表 1/2/4 由"待确认"改为"已实测"，新增风险 7（漫画缺供应商）；现状盘点更正 WebUI 端口（17163）与唤醒前缀
- ✅ 流程规则落库 DEVELOPMENT.md：① 开工核对唯一权威工作区 ② 交接证据三查（远端提交/克隆副本残留/运行目录一致性）③ 进度实时写 Task.md ④ 收工硬检查（git status 干净 + 无未推送提交）

**修改的文件**：
- 合并：`Project/ALLBot部署/Task.md`、`Project/ALLBot部署/README.md`、新增 `Project/ALLBot部署/tests/check_installed_source.py`
- 修改：`Project/ALLBot部署/BRD.md`、`DEVELOPMENT.md`、`CHANGELOG.md`

**当前状态**：
- ✅ 交接证据齐备，可交给测试 Agent 按 Task.md 待复验项正式验收（任务 2/3/4、修复 10/11）
- ⏳ 待办：日志落盘重启验证（任务 1）、群漫画绘图供应商（任务 5）、测试 Agent 正式验收
- ⚠️ 推送状态：本地已提交 fd07556，push 因 GitHub 网络不可达（Failed to connect github.com:443）失败，网络恢复后重试 `git push`

---

## [2026-09-15] 规划 Agent - 新子项目立项：ALLBot部署（AstrBot QQ 机器人「丛雨」调教）

**完成的工作**：
- ✅ 实地核查 AstrBot 部署现状：v4.26.8（AstrBot Launcher 0.3.9），实例 `C:\Users\WindoseII\.astrbot_launcher\instances\4450a298-f4c2-43fa-b7f7-bd645b753fc3\core`，双进程常驻可聊天；LLM 走 `rkapi.com/v1`（gpt-5.6-terra 默认 / claude-opus-5）；人设「丛雨」（`default_personality`）；OneBot v11 反向 WS `:6199` ← SnowLuma；已装 4 个插件（群分析 / 复读 / 限次复读 / 听歌）
- ✅ 确认两项关键机制：群分析插件指令（`/群分析` `/群漫画` `/分析设置` 等 7 条）；`forward_threshold=1500`——LLM 回复超字数自动转「合并转发聊天记录」（核心 `core/astrbot/core/pipeline/stage.py`）
- ✅ 产出子项目三件套：`Project/ALLBot部署/BRD.md`（目标 / 现状盘点 / 技术方案 / 四类验收 / 风险表）、`Task.md`（6 项开发任务 + 3 项可选迭代 + 维护看板）、`README.md`（环境 / 群内用法 / 长短分流标准 / 敏感信息红线）
- ✅ 根 BRD.md 候选清单更新：QQ 群机器人标记为已立项
- ✅ 按平台运维规则归档 CHANGELOG 旧记录（保留最近 15 条，本次共归档 4 条至 `CHANGELOG.archive.md`，含合并远端记录后新增 2 条）

**修改的文件**：
- 新增：`Project/ALLBot部署/BRD.md`、`Project/ALLBot部署/Task.md`、`Project/ALLBot部署/README.md`
- 新增：`CHANGELOG.archive.md`（共归档 4 条旧记录）
- 修改：`BRD.md`（候选清单与立项状态）、`CHANGELOG.md`（本条记录 + 归档）

**当前状态**：
- ✅ 新子项目规划完成，待用户确认后进入开发
- ⚠️ 待确认风险已列入子项目 BRD：空 id 白名单语义、群分析插件 `llm_provider_id` 为空、消息量门槛（≥200 条/日）、合并转发兼容性

**下一步建议**：
1. 用户确认立项后，对开发 Agent 下达：「你是开发 Agent，根据 DEVELOPMENT.md 的要求，按 Project/ALLBot部署/Task.md 开发」
2. 群分析报告依赖当日消息量（默认 ≥200 条），目标群需有一定活跃度

---

## [2026-09-20] 规划 Agent — AGENTS.md 升级为统一 Agent 行为规范入口与 skill 路由中心

- ✅ **根 `AGENTS.md` 由「角色定义」升级为全平台唯一行为规范入口 + skill 路由中心**：新增 §〇 开工三步、§一 Skill 任务路由表、§二 通用 skill（所有 Agent 共用）、§三 角色 skill 速查；**原文 304 行逐字保留**（校验：原第 2 行起逐行存在、缺失 0 行），净增 151 行
- ✅ **整合 `skill/` 下除「达芬奇21中文操作手册」外的全部技能卡**：`token节省`（十条纪律 + 失效红线常驻）、`humanizer`（四条核心原则 + 「不是A而是B」三毒 + 交付前必查清单）、三张角色执行卡（触发条件 / 一句话职责 / 关键约束 / 指针）
- ✅ **采用「入口摘要常驻 + 完整规则留卡 + 指针引用」，不全文照搬**：`humanizer` 正文 24KB，全文照搬会让每个 Agent 每次开工多读 60KB+，直接违背刚落地的 Token 纪律；入口只写**可执行纪律**，完整规则仍以 `skill/<名>/SKILL.md` 为准
- ✅ **新增 §2.3「新增通用 skill 登记规则」**：为后期泛用 skill 预留扩展位（目录与 frontmatter 约定 + 登记四步 + 禁止复制全文 + 角色专属 skill 归 §3 不进 §2）
- ✅ **让「开工必读」真正落地**：三本 SOP 头部配套文档行改为「Agent 行为规范入口 + skill 路由，开工前必读」，并在三本**前置检查首项前**各插入一条「已读 AGENTS.md 并按任务类型查阅对应 skill 卡」；`BRD.md` 文档说明、`README.md` 结构树注释同步更新
- ✅ **命名以仓库为准**：全仓引用统一为 `AGENTS.md`（实测本目录对大小写敏感，新建小写 `agent.md` 会与 `AGENTS.md` 并存成两个入口；`git core.ignorecase=true` 又会令两者在 git 侧混淆）——**未新增文件、未改名、未动目录结构**
- ✅ 校验证据：`AGENTS.md` 原文逐行保留缺失 0 行、H1 唯一、6 个文件全部 CRLF 且 LF-only 行数均为 0
- 修改：`AGENTS.md`(+151)、`PLANNING.md`、`DEVELOPMENT.md`、`TESTING.md`、`BRD.md`、`README.md`、`CHANGELOG.md`（本条）、`CHANGELOG.archive.md`（归档）
- ⏳ 本轮只做文档与规则整合：**未写功能代码、未执行测试**
- 下一步交给：三 Agent 下一轮开工即走新入口（`AGENTS.md` → 路由表 → 对应 skill 卡）；🔴 遗留：`Project/ALLBot部署/plugins/astrbot_plugin_mute/*`、`astrbot_plugin_meme_library/`、两处 `data/` 仍属他人在途/未跟踪，本轮**未触碰**

## [2026-09-16] Codex — 保存达芬奇21中文操作手册技能资产

**完成的工作**：
- ✅ 从公开仓库 `akahoz94/davinci-21-chinese-manual` 导入完整技能目录，源提交为 `c125c77`。
- ✅ 按 `SKILL.md` 声明的名称保存到 `skill/达芬奇21中文操作手册/`，保留 `SKILL.md`、README、MIT 许可证及 `references/` 全部资料。
- ✅ 新增 `简介.md`，概括技能用途、数据覆盖范围、离线浏览方式、来源与署名。
- ⚠️ 本机 Codex 用户级技能安装因账户用量限制被系统拒绝，未使用替代入口绕过；本地仓库资产已保存，云端推送因本机网络 / SSL 环境未取得成功回执。

**修改的文件**：
- 新增：`Task.md`
- 新增：`skill/达芬奇21中文操作手册/`（源技能完整目录及 `简介.md`）
- 修改：`BRD.md`、`CHANGELOG.md`

**下一步建议**：
- 网络 / SSL 环境恢复后执行普通 `git push origin main`；测试 Agent 再核对远端目录、`SKILL.md` frontmatter 与 references 文件清单并关闭根任务 1。

## [2026-09-15] 规划 Agent - 消除重复工作区：清理 D:\Program\AllAgentBASE 克隆副本

**背景**：本机同时存在两份克隆——`D:\Project\AllAgentBASE`（权威工作区）与 `D:\Program\AllAgentBASE`（Codex 本地副本）。DEVELOPMENT.md 已记录教训：实测证据留在副本未推送，导致规划 Agent 只能靠截图还原、快照三处误判。本次按用户要求「只留一个」完成去重。

**核对结论（合并前）**：
- ✅ 两份均指向同一远程 `SSaans/AllAgentBASE`；副本 A 的 HEAD `98cf6ca` 是主工作区 HEAD `1a640ca` 的祖先，主工作区领先 3 个提交，属纯快进关系，无冲突可解
- ✅ A 的 `Project/ALLBot部署/Task.md`、`README.md`、`tests/check_installed_source.py` 与主工作区逐字节相同（已被提交 `fd07556` 收编）；A 仅在 `CHANGELOG.md`、`CHANGELOG.archive.md`、`DEVELOPMENT.md`、`Project/ALLBot部署/BRD.md` 四个文档上更旧，**无独有内容**
- ✅ A 无未推送提交、无 stash；其未提交改动均已由 `fd07556` 落库
- ✅ A 唯一独有资产为被 `.gitignore` 忽略的 `temp/allbot/`（16 个本地脚本）

**完成的工作**：
- ✅ 全量备份两份克隆至 `D:\_AllAgentBASE_merge_backup_20260915-012846`（A 157 文件 / B 171 文件，已核对文件数与字节数）
- ✅ 迁移 `temp/allbot/` 至 `D:\Project\AllAgentBASE\temp\allbot`（仍被忽略，不入库）
- ✅ 将 `D:\Program\AllAgentBASE` 移入回收站，本机仅保留唯一权威工作区
- ✅ 勘误 DEVELOPMENT.md：开工核对与「交接证据三查」中指向副本的过期表述同步更新
- ✅ 归档 CHANGELOG 最旧 3 条至 `CHANGELOG.archive.md`，主文件恢复 15 条上限

**修改的文件**：
- 修改：`CHANGELOG.md`（本条记录）、`DEVELOPMENT.md`（副本引用勘误）、`CHANGELOG.archive.md`（归档 3 条）
- 新增（未跟踪、被忽略）：`temp/allbot/`

**推送状态**：
- ✅ **已推送**。本机须经代理访问 GitHub（`HTTPS_PROXY=http://127.0.0.1:65368`），代理对 push 的 CONNECT 隧道**间歇性故障**：首轮连续 3 次失败（`Empty reply from server` / `CONNECT tunnel failed, response 502`），绕过代理直连亦超时（`Failed to connect github.com:443 after 21015 ms`）；稍后重试第 2 次成功，`36d8ced..7ef5036 main -> main`，此前遗留的 `fd07556`、`1a640ca` 与本条记录共 3 个提交已全部同步至远端
- ℹ️ 经验：本机 push 报 `CONNECT tunnel failed, response 502` 属代理间歇性故障，**隔几秒重试即可**，不必改配置、更不得强推

**当前状态**：
- ✅ 本机仅存 `D:\Project\AllAgentBASE` 一份工作区，重复副本导致的交接风险已消除
- ✅ 远端 `refs/heads/main` 经 `git ls-remote` 实测为 `36d8ced`（本地 remote-tracking ref 曾因 packed-refs 陈旧显示 `df5181e`，已随 fetch 校正）
- ✅ 推送已完成（见本条"推送状态"）；交测试 Agent 按 `Project/ALLBot部署/Task.md` 待复验项正式验收

## [2026-09-16] Codex — 完成技能安装与远端复验

- 已通过 skill-installer 安装指定源版本至 `C:/Users/Unbox/.codex/skills/达芬奇21中文操作手册`；9 个源文件与仓库副本逐一文本一致，仅换行格式有差异。
- 正式权限下推送恢复，合并远端新增提交后普通推送成功；远端 `main` 已核验为 `405f6b6559fb8cdc252e0dc3a489838702cca22e`，包含技能本体与简介。下方安装/推送受阻记录为历史状态。
- 根任务 1 复验关闭。源仓库嵌套 `.git` 仍留在本地导入目录，未提交至云端；不影响远端普通文件或独立安装目录。

## [2026-09-17] 规划 Agent — 新子项目立项：bilisum部署（BiliSum 视频摘要工具）

**完成的工作**：
- ✅ 按用户指派完成部署：clone `lycohana/BiliSum` 到 `D:\Program\bilisum`（v1.21.1 / 提交 `fc693b1`）；装好 Python 环境（uv，CPython 3.13.14，33 包）与桌面端依赖（npm，534 包，Electron 42.3.3）；前端构建通过；后端实测监听 `http://127.0.0.1:3838`，`/health`、`/`、`/settings` 均返回 200
- ✅ 排查并解决 Electron 二进制缺失：首次 `npm install` 后 `electron\dist\electron.exe` 未落地（postinstall 失败）→ 设 `ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/` 重跑 `electron/install.js` 补齐
- ✅ 产出子项目文档：`Project/bilisum部署/BRD.md`（目标 / 关键路径 / 四类验收 / 6 条风险）、`Task.md`（5 项待验收 + 3 项待办）、`README.md`（启动方式 / 首次配置 / 环境表 / 本机改动登记 / 排查速查）、`CHANGELOG.md`
- ✅ 新增两个启动脚本（放在部署目录，非上游文件）：`start-web.bat`（网页版，推荐）、`start-desktop.bat`（Electron 桌面版）
- ✅ 更新根 `BRD.md`：候选清单新增已立项项、状态行与已立项子项目说明同步

**修改的文件**：
- 新增：`Project/bilisum部署/`（BRD.md、README.md、Task.md、CHANGELOG.md）
- 修改：`BRD.md`、`CHANGELOG.md`（本条记录）

**当前状态**：
- ✅ 网页版可用（服务 + 前端 + 静态资源齐备，均实测 200）
- ⏳ **未验证**：桌面版窗口实际拉起、设置持久化、真实视频端到端 —— 本轮只证明了「服务起得来、构建过得去、Web UI 打得开」，不得用构建证据代替实机验收
- ⚠️ 已知缺口：`.venv` 内无 torch → 本地 Whisper / FunASR / 本地 Embedding 不可用，需用在线 ASR

**下一步建议**：
1. 用户在设置页配置 LLM + ASR（可复用 AstrBot 的 `rkapi.com` 中转 Key），跑通一条真实视频
2. 测试 Agent 按 `Project/bilisum部署/BRD.md`「五、验收标准」复验，重点补**桌面版窗口**与**端到端**两项
3. 是否安装本地 ASR 运行时，待用户决定（子项目 `Task.md` 任务 6）

## [2026-09-20] 开发 Agent — 新子项目立项：distilly（蒸馏自己）

- ✅ 按用户指派立项 `Project/distilly/`：分析上游 `titanwings/distilly`（分支 `dot-skill`）并产出可执行规划方案，四件齐备（BRD / README / Task / CHANGELOG）
- 🔴 **关键澄清**：上游是**人设 / 知识层蒸馏（Prompt）**，产出可被 Agent 加载的 Person Profile 技能包，**不训练模型权重**、不微调 —— 已置顶写入 BRD，避免「训练出一个个性化模型」的预期落差；权重级需求需另行立项，本项目只能作其语料口径与评测 rubric 的上游
- ✅ 方案涵盖：环境与依赖、个人数据范围与格式（含三级隐私分级）、六阶段实施路径与各阶段交付物、效果验证与评估、十条限制与风险
- ✅ 落地关键差异点：family 固定 `colleague`；数据入口只走「上传文件 + 直接粘贴」（上游采集器只覆盖飞书 / 钉钉 / Slack，本机 QQ / 微信无采集器）；`colleague` 家庭**无上游自动质检**，评估方案自建
- ⚠️ **角色边界**：BRD 需求章节按 `AGENTS.md` 属规划 Agent 职责，本次由开发 Agent 按用户指派代拟，已在 BRD 与 `Task.md` 标注「待规划 Agent 确认」，未改动任何既有 SOP
- ⚠️ 本轮**只规划不执行**：未 clone 上游、未装依赖、未整理材料、未写功能代码
- 🔧 **勘误根 BRD「不做的事情」**（用户指出）：删除错误条目「不自动解决 Git 冲突（需要人工介入）」，改为新增「Git 归属」章节 —— **Git 拉取 / 冲突解决 / 提交 / 推送一律由 Agent 自行闭环，任何情况都不要求用户人工介入**
- 新增：`Project/distilly/`；修改：`BRD.md`（立项登记 + Git 归属章节）、`CHANGELOG.md`（本条）

---

## [2026-09-20] 规划 Agent — 新子项目立项：表情包同步（StickerSync）

**完成的工作**：
- ✅ 按用户指派立项 `Project/表情包同步/`：把表情包收成「一套 = 一个 Pack」的标准资产，存云端（GitHub）、按需拉取、分发到 QQ / Telegram / 微信
- ✅ **调研 QQ / TIM 表情包底层机制**（用户指定项）：`.eif` 是微软 **Compound File Binary（CFB）** 容器（`Face.dat` 索引已加密、图片本体未加密）；分组规则 `0–26` 本地 / `8213` 云端；云端分组无导出入口；四端本地存储路径已查明；原创贴纸混淆规则为**前 24 字节偶数位 ±1**
- 🔴 **关键否证**：NTQQ 的 `personal-emoji/Ori` 是**缓存**不是数据源（删除后会被 QQ 重建）→ **往缓存丢图片不会被收进收藏**，"直写缓存"捷径不通
- ✅ **调研现成项目**（用户指定项）：结论是**没有任何项目同时覆盖 QQ + TG + 微信 + 云端**，最接近的 `star-39/moe-sticker-bot` 不含 QQ/微信 → **本项目有存在价值**；已列 QQ 侧 5 项、跨平台/TG 侧 5 项作为参考
- ✅ **产出核心设计与方案**：Pack 格式（`manifest.json` + 素材 + 产物）；🔑 **以图片为真相、把 `.eif` 当产物**（避免被腾讯版本迭代绑架）；`core → converters → adapters → webui → sync` 分层；六阶段实施方案各带目标/交付/判据
- ✅ **如实标注能力边界**：**Telegram 全自动 / QQ 半自动 / 微信仅备料**；明确不承诺「一键同步进 QQ/微信」——这两个平台没有开放写入接口，如实写清而非回避
- ⚠️ 本轮**只规划不写代码**：未 clone 上游、未装依赖、未建代码目录，严守 `AGENTS.md` 规划 Agent 边界
- 🔴 **最大不确定项已登记**：QQ `.eif` 的**写入**（`Face.dat` 加密回写）未验证 → `Task.md` 任务 10 目标 A，预设「图片文件夹 + 导入引导」兜底
- 新增：`Project/表情包同步/`（BRD / README / Task / CHANGELOG）；修改：`BRD.md`（立项登记：状态行、候选清单、已立项说明、立项说明）、`CHANGELOG.md`（本条）
- 下一步交给：**用户拍板**（能力边界 / 首批平台 / 云端开放范围 / 整体方案），放行后交**开发 Agent** 从 `Task.md` 任务 5 开始

## [2026-09-20] 规划 Agent — 表情包同步（StickerSync）R2 范围修订：移除 Telegram，TIM 定为攻坚主战场

**变更依据**：用户两条明确指令 —— ①「不需要再处理 Telegram，改为实现 QQ 和微信的同步功能以及相关的封装包。要求逻辑严谨、边界情况处理完善，确保同步过程稳定可靠、封装接口清晰规范。」②「你用的全是 TIM，重点放在 TIM 上，别找错资料了。」

- ✅ **范围收窄**：平台由「QQ + Telegram + 微信」改为「**TIM（主） + 微信**」，Telegram 移出范围（R1 结论保留为历史记录）
- 🔴 **纠正 R1 的关键误判**：TIM 走的是**传统架构而非 NTQQ**，R1 把它归入"兼容轨"是错的 → 现定为**主战场**
- 🔴 **实测出决定性事实**：TIM 的自定义表情存于 **`CustomFace.db`**（CFB 复合文档，**未加密**）→ 这是最干净可靠的数据源；而 **TIM 自带的「导出表情包」功能是坏的**（社区实测其导出 eif 已损坏）→ **放弃 eif 往返，改为直读 db**
- 🔴 **印证用户痛点**：TIM 的表情分组会**无故被清空**（社区长期反馈）→ 由此确立**备份铁律**：动 db 前必须自动备份，备份失败即中止；绝不原地修改，只走「副本改写 → 校验 → 原子替换」，失败自动回滚
- ✅ **写入路径重构为三级**（按风险从低到高）：**W3 面板导入（零风险，先做）→ W2 直写 db（高价值高风险，验证通过前不发布）→ W1 生成 eif（需补齐 `Face.dat` 未公开字段）**
- ✅ **封装包接口规范落定**：`core/`（新增 `cfb.py`）+ `adapters/{tim,wechat}` + `sync/{engine,backup,report}` + `cli`；`PlatformAdapter` 契约（`detect()` 不抛异常、写操作必须 `dry_run`、单素材失败不中断整批）；异常体系扩至 10 类（新增 `BackupFailed`、`DataIntegrityError`）；同步引擎由四阶段扩为**五阶段**（预检 → 计划 → **备份** → 执行校验 → 报告）
- ✅ **边界清单扩至 34 条**（TIM 侧 18 / 微信 8 / 通用 8），每条编号供测试 Agent 回指；新增「db 结构未知 → 只读降级、不猜不写」「写前备份失败即拒绝」「写后校验不过即回滚」等硬规则
- ✅ **新增阶段 0.5「`CustomFace.db` 结构实测」**为前置攻坚（**只读、只用副本**）—— 它是后续一切读写的地基
- 修改：`Project/表情包同步/`（`BRD.md` 全量重写、`README.md` 改大白话版、`Task.md` 重排 16 项、`CHANGELOG.md`）、根 `BRD.md`（状态行 + 候选表同步为 TIM + 微信）、根 `CHANGELOG.md`（本条）
- ⏳ **本轮仍只规划不写代码**：未建代码目录、未触碰任何 TIM / 微信 数据文件
- 下一步交给：**用户拍板**（TIM 三条结论 / 能力边界 / 边界清单 / 云端开放范围），并配合提供 `CustomFace.db` 路径；放行后交**开发 Agent 从任务 5（只读摸结构）开始**，不要直接开写代码

## [2026-09-20] Codex 测试 Agent — Uncle城 原版 Humanizer 安装复验通过

- 使用 skill-installer 从 SSaans/AllAgentBASE 的已核实提交 7e723b0 安装 skill/humanizer 到 C:/Users/WindoseII/.codex/skills/humanizer。
- 原包、仓库和安装目录的五个原始文件逐字节一致，SHA-256 全部匹配 SOURCE.json；name 为 humanizer，三份 references 齐全，配置中未禁用此技能。
- 来源为 Uncle城 的 SkillHub 账号 user_ab5ae6ee，商店包 1.0.5，正文 4.1.0；原版规则未修改。平台 Ed25519 签名已验证通过，原版资产已在远端 main。
- Codex 已按测试 Agent 验收项完成逐字节复验，根任务 2 关闭。本轮已读取技能，可按原版执行；从下一轮可使用 $humanizer 调用。
- 仅更新 Task.md 和 CHANGELOG.md；已有未跟踪数据不纳入提交。

## [2026-09-20] 开发 Agent — .gitignore 加固：防宿主目录与杂散副本误入库

- 🔴 核查发现仓库工作区内有 **3 处非源码杂散项**，都能被一次 `git add .` 带进仓库：`.claude/`（3263 文件，含宿主技能安装 `.claude/skills/distilly` 与 `settings.local.json`）、`Programdistilly/`（169 文件，`D:\Program\distilly` 反斜杠被吞后的副本）、`DＺProjectAllAgentBASEgit_pull_result.txt`（同源失误产物）
- ✅ 已在 `.gitignore` **新增**忽略规则（未删改任何既有规则）；**未删除任何文件**，清理待用户裁决（见 `Project/distilly/Task.md` 任务 10）
- 📌 提醒各 Agent：**不要 `git add .` / `git add Project`**，逐路径显式 add，并用 `git diff --cached --name-only` 断言
- ⚠️ 另记：本地 `refs/remotes/origin/main` 实测**再次陈旧**（停在 `df5181e`），连 `git fetch` 的输出都谎报已刷新 → 推送判据仍以 **`git ls-remote origin main`** 为准
- 修改：`.gitignore`

## [2026-09-20] 规划 Agent — 三 Agent 职责封装为仓库内 skill，并落地 Token 节省纪律

- ✅ **新增 3 张 Agent 执行卡**：`skill/规划Agent/`、`skill/开发Agent/`、`skill/测试Agent/`（各含 `SKILL.md` + `简介.md`）。把 `PLANNING.md` / `DEVELOPMENT.md` / `TESTING.md` 提炼为可直接照单执行的卡片，统一覆盖**触发条件 / 职责边界 / 开工输入 / 可复用步骤 / 输出物 / 红线 / 收工自检**，并声明以对应 SOP 为权威来源（冲突时以 SOP 为准）
- ✅ **新增降本执行卡 `skill/token节省/`**：对「prompt 缓存 + 分层记忆 + 滑动窗口 + 模型分流」**逐条判定**后落地——可落地项写细（文档三层结构 L1/L2/L3、固定前缀策略、先定位再定向读、归档即压缩、只追加不改写、要点式交接）；不适用项**明确标注**（向量库召回、消息分类器、运行时缓存标记在本仓库无运行时宿主）并给等价替代（Grep 即召回、任务分流即分类器），**不硬塞**
- ✅ 三张执行卡各含一节精炼「Token 纪律」并以**指针**引用 `token节省`，**不复制全文**——复制长段本身即违背该纪律
- ⚠️ 本轮守住**公开仓库约束**：执行卡一律不写本机路径、账号标识、代理端口等坐标；已逐份核对 4 个 `SKILL.md` 无敏感信息
- ✅ 同步 `BRD.md`（「文档管理」与「文件夹职责」两处补 `skill/` 说明）、根 `Task.md`（新增任务 4，状态：待复验）
- 修改：`BRD.md`、`Task.md`、`CHANGELOG.md`、`CHANGELOG.archive.md`；新增：`skill/规划Agent/`、`skill/开发Agent/`、`skill/测试Agent/`、`skill/token节省/`（8 个文件）
- ⏳ 本轮只做规划与文档资产封装：**未写功能代码、未执行测试**
- 下一步交给：**测试 Agent 复验**（核对 SKILL.md 结构完整性、frontmatter 可被技能加载器识别、与三本 SOP 无冲突、无敏感坐标）；`[x]` 关闭由测试 Agent 勾选

## 使用说明

### 每个 Agent 工作前必须做的事：
1. ✅ 读完 BRD.md 全文
2. ✅ 读完 CHANGELOG.md 最近 3 条记录
3. ✅ 执行 `git pull` 拉取最新内容（如果 Git 已配置）

### 每个 Agent 工作后必须做的事：
1. ✅ 在本文件顶部添加新的变更记录
2. ✅ 说清楚"做了什么"和"下一步做什么"
3. ✅ 执行 `git push` 推送到 GitHub

### 记录格式：
```markdown
## [日期] Agent角色 - 任务简述

**完成的工作**：
- 列出完成的任务

**修改的文件**：
- 列出修改的文件

**下一步建议**：
- 给下一个 Agent 的建议
```

## [2026-09-12] 规划 Agent — 本地信息同步，远端同步受阻

- 已阅读根职责、规划 SOP、BRD、最近三条交接，以及唯一子项目的 BRD、Task、README 和交接补充；本地基线为 dd49de8。
- 修改 BRD.md：纠正“尚无子项目”现状与自动新增归档规则，标明旧审阅为历史；修改子项目 Task.md：纠正识屏标题，记录交接与同步局限；本条记录于 CHANGELOG.md。
- 当前仅维护 Shinsekai。任务 16 保留历史验收状态；任务 17 待复验，任务 18 待办。未写功能代码、未执行测试，未确认旧 H: 运行目录的当前状态。
- git pull --ff-only 因 Could not resolve host: github.com 失败；本地记录不代表已获取远端最新状态。后续恢复网络后拉取并推送，不强推。
- 下一步：开发 Agent 排查任务 18，测试 Agent 完成任务 17、18 的 UI、语音、历史及退出验收；本轮不启动其他 Agent。

## [2026-09-08] Codex — 补全运行收尾与证据验收流程，纠正心跳关闭状态

- **同步**：已拉取规划 Agent 提交 `77dbf28`，保留新增任务闭环及提交闭环，在既有文件补全流程，未新增 MD。
- **事实**：旧测试 PID 42464 的会话日志 `20260908-023936-42464.jsonl` 记录 03:22–09:35 共 13 次心跳触发；说明直接启动的聊天实例在设置窗口之外持续运行。只读核对时该 PID 与旧 TTS PID 已不存在，未查明退出原因，没有终止用户当前设置进程。
- **修改**：AGENTS、三本 SOP 补充进程归属、正常退出、历史保护、完整日期/会话证据、退出后停止验收、复用现有文档与 Agent 自行 Git 推送；两份 README 纠正推送责任和仓库地址。Task 17 重开为待复验，新增任务 18；HANDOFF 留存本次证据及局限。
- **验证范围**：本轮是只读运行排查与文档一致性检查，无产品代码修改，无新增运行测试。47 项旧回归不能代表心跳完整验收，当前仍未完成正常入口的 UI/语音/历史与退出验收。
- **交接**：继续任务 17、18；本次 Git 交付仅含已有文档，不包含仓库外运行源码。保留历史、三天截图清理和已关闭的定时识屏，不使用快速重启。

> 🎯 作用：Agent 之间的"交接棒"  
> 📋 规则：每次改动必须记录，新记录放在最上面

---

## [2026-09-08] 规划 Agent - 工作流补强：任务闭环 + 提交闭环 + 仓库外代码落库规则

**背景（诊断）**：审阅 2026-09-07 晚至 09-08 的全部交接记录后发现，工作流中只有"记日志"在起作用：识屏误判修复、心跳修复等 5 轮实际工作改的是仓库外代码（`H:\Program\新世界\Shinsekai`），Task.md 未建任务、未更新状态；验证记录自述"无 Git 提交或推送"。"修完提交、建任务"缺少硬性关卡。

**完成的工作**：
- ✅ 根 BRD.md 协作规则新增第 5/6/7 条：任务闭环、提交闭环、仓库外代码落库
- ✅ AGENTS.md 重要规则同步新增三条，并定义任务状态流转约定：`待办 → 修复中 → 待复验 → 已关闭`（已关闭仅测试 Agent 有权勾选）
- ✅ 三本 SOP 手册的"第五步：提交推送"全部升级为**收工检查清单（三件套：CHANGELOG 记录 / Task.md 更新 / commit+push）**，缺一不算完工；"只写日志不提交"列入各手册红线
- ✅ DEVELOPMENT.md：开工标「修复中」、自测完标「待复验」、开发中发现新 Bug 必须当场建任务
- ✅ TESTING.md：前置检查纳入「待复验」任务清单，验收通过勾 `[x]` 关闭、失败打回「待办」
- ✅ Task.md 看板回填与纠偏：过时的识屏"待修复"标注更新为已解决（根因实为流式 JSON 解析缺陷，非图像理解层）；历史修复回填为任务 16（识屏误判）/ 任务 17（心跳静默），新增"维护记录（Bug 修复看板）"章节
- ✅ 子项目 BRD 边界修订：原"不修改核心源码"限定为初始部署阶段；维护阶段允许为修 Bug 改运行目录源码，但改动摘要必须落库

**修改的文件**：
- 修改：`BRD.md`（协作规则 5/6/7 条）
- 修改：`AGENTS.md`（重要规则 + 任务状态标注约定）
- 修改：`PLANNING.md`、`DEVELOPMENT.md`、`TESTING.md`（收工检查清单、任务状态流转、红线）
- 修改：`Project/shinsekai项目byendcycle/Task.md`（识屏标注纠偏 + 维护看板回填）
- 修改：`Project/shinsekai项目byendcycle/BRD.md`（边界修订说明）
- 修改：`CHANGELOG.md`（本条记录）

**当前状态**：
- ✅ 工作流三个缺口全部补上：修完必须提交、Bug 必须建任务、仓库外改动必须留痕落库
- ✅ 平台规则文件与两个子项目文档一致性已核对

**下一步建议**：
1. 后续所有 Agent 会话请用 SOP 启动指令驱动（见 AGENTS.md SOP 索引表），确保拿到手册约束
2. 下一个发现/修复 Bug 的 Agent 按新规则走一遍全流程，验证闭环有效

---

## [2026-09-07 17:40] 规划 Agent - 搭建三阶段 SOP 操作手册工作流

**完成的工作**：
- ✅ 参考外部分享的"文档即指令"标准化流程（每阶段一本 md 手册，开工念指令、AI 照单办事）
- ✅ 创建三本阶段操作手册（SOP）：
  - `PLANNING.md`：规划 Agent 手册（前置检查 → 审阅 → 补需求/产出 Task.md → 记录 → 推送）
  - `DEVELOPMENT.md`：开发 Agent 手册（前置检查 → 照 Task.md 逐条开发 → 自测 → 记录 → 推送）
  - `TESTING.md`：测试 Agent 手册（前置检查 → 按验收标准逐项测 → 修小 Bug/记 Bug 清单 → 结论 → 推送）
- ✅ 每本手册内置三件套：前置检查清单、工作步骤、红线（禁止事项）
- ✅ 接入既有体系：BRD.md 项目结构与工作流章节已更新；AGENTS.md 新增 SOP 索引表（含各阶段启动指令模板）

**修改的文件**：
- 新增：`PLANNING.md`、`DEVELOPMENT.md`、`TESTING.md`
- 修改：`BRD.md`（结构图加入三本手册、工作流改为按手册执行、文档管理补充说明）
- 修改：`AGENTS.md`（新增"各阶段操作手册（SOP）"章节）
- 修改：`CHANGELOG.md`（本条记录）

**当前状态**：
- ✅ 工作流闭环完成：规划（PLANNING.md）→ 开发（DEVELOPMENT.md）→ 测试（TESTING.md）→ 回到规划
- ✅ PLANNING.md 中已约定：子项目立项后由规划 Agent 产出 Task.md 任务清单，开发 Agent 照单干活
- ❌ 仍无已立项子项目，等待用户指定

**下一步建议**：
1. 用户指定第一个子项目，然后对规划 Agent 说：「你是规划 Agent，根据 PLANNING.md 的要求，对 <子项目> 进行立项规划」
2. 开发/测试阶段分别用 DEVELOPMENT.md / TESTING.md 的启动指令驱动

---

## [2026-09-07 16:38] 规划 Agent - 第一轮规划：审阅项目状态并补充 BRD

**完成的工作**：
- ✅ 克隆最新代码（main 分支，df5181e），通读 BRD.md、CHANGELOG.md、AGENTS.md、README
- ✅ 审阅项目状态：核心文档齐全，协作机制已运转一轮（开发 Agent 初始化 → 规划 Agent 本轮接力）
- ✅ 修正 BRD.md 仓库地址笔误（SSaann → SSaans）
- ✅ 补齐 BRD.md 原"待补充内容"三项空白：
  - 子项目立项流程与标准目录结构
  - 候选子项目清单（QQ 群机器人 / CHANGELOG 归档工具 / 文档一致性检查脚本，等用户决策）
  - 子项目验收标准通用模板（功能/文档/质量/交接四类）
  - 自动化测试分阶段方案（人工核对 → 子项目测试集 → GitHub Actions）
  - 平台运维规则（CHANGELOG 15 条归档机制、四个文件夹职责）
- ✅ 更新 BRD.md 平台验收标准为完成度核对（5 项全部达成）
- ✅ 新增"项目状态审阅"章节，记录本轮发现的问题与处置
- ✅ 补建 `Project/.gitkeep`、`Any/.gitkeep`，使目录结构与 BRD 定义一致

**修改的文件**：
- `BRD.md`：头部状态更新、仓库地址勘误、验收标准核对、新增"子项目需求规范"与"项目状态审阅"章节
- `CHANGELOG.md`：新增本条记录
- `Project/.gitkeep`、`Any/.gitkeep`：新增（空目录占位）

**当前状态**：
- ✅ 平台自身 5 项验收标准全部达成（push 由本次提交验证）
- ✅ 本地工作目录：`d:\Project\AllAgentBASE`（注意：与此前记录的 e 盘路径不同，系换机操作，属正常现象）
- ❌ 尚无已立项子项目，平台处于"等待第一个子项目"状态

**下一步建议**：
1. 用户从 BRD 候选清单中指定第一个子项目（QQ 群机器人等），或提出新想法
2. 子项目确定后，规划 Agent 产出 `Project/<子项目名>/BRD.md`
3. 开发 Agent 待命，等子项目 BRD 获用户确认后接力编码
4. 后续 Agent 工作前记得先 `git pull`

**注意事项**：
- Git 身份未写入全局配置，本次提交通过一次性参数使用 `SSaann <ssaann@example.com>`（与最近两笔提交一致）
- BRD 中的候选清单仅是建议，优先级全部"待定"，以用户决策为准

---

## [2026-09-06 19:55] 开发 Agent - 接手项目并验证 Git 连接

**完成的工作**：
- ✅ 接手项目，阅读了 BRD.md、CHANGELOG.md、AGENTS.md
- ✅ 验证 Git 配置和远程仓库连接
- ✅ 成功执行 `git pull`，确认网络连接正常
- ✅ 确认项目结构完整，所有核心文档就绪

**当前状态**：
- ✅ Git 已配置，远程仓库：https://github.com/SSaans/AllAgentBASE.git
- ✅ 网络连接正常，可以正常 pull/push
- ✅ 工作区干净，与远程仓库同步
- ✅ 项目基础框架已搭建完成

**下一步建议**：
1. 规划 Agent 可以开始补充 BRD.md 中的具体子项目需求
2. 或者用户可以直接指定要开发的具体功能
3. 所有后续 Agent 工作前记得先 `git pull`

**注意事项**：
- 项目根目录：`e:\AllAgentBASE`
- 远程仓库地址：https://github.com/SSaans/AllAgentBASE（注意用户名是 SSaans，不是 SSaann）

---

## [2026-09-06] 开发 Agent - 项目初始化

**完成的工作**：
- ✅ 创建项目文件夹结构（Project、Guide、Readme、Any）
- ✅ 创建核心文档：BRD.md、CHANGELOG.md、AGENTS.md
- ✅ 创建 .gitignore 文件
- ✅ 从交接文档中了解项目背景和目标

**修改的文件**：
- 新增：`BRD.md` - 业务需求文档
- 新增：`CHANGELOG.md` - 本文件
- 新增：`AGENTS.md` - Agent 角色定义
- 新增：`.gitignore` - Git 忽略规则
- 已存在：`Guide/multi-agent-workflow-guide.html`
- 已存在：`Readme/README.md`

**当前状态**：
- ⚠️ Git 未安装，暂时无法执行 git pull/push
- ✅ 项目基础文件已创建完成
- ✅ 文件夹结构已就绪

**下一步建议**：
1. 用户安装 Git（从 https://git-scm.com/download/win 下载）
2. 执行 `git clone https://github.com/SSaann/AllAgentBASE.git` 或初始化现有目录
3. 将当前创建的文件推送到 GitHub
4. 规划 Agent 可以开始审阅并补充 BRD.md

**注意事项**：
- 项目根目录现在是 `e:\AgentProjectBASE`
- GitHub 仓库地址：https://github.com/SSaann/AllAgentBASE
