# 变更日志 (CHANGELOG)

## [2026-09-18] Codex 开发 Agent — 保存 Uncle城 原版 Humanizer

- 从视频作者的 SkillHub 账号下载原版 1.0.5 包，正文为 Humanizer v4.1；未从摘要重写。
- 新增 skill/humanizer/，五个原始文件完整保留，另附来源与逐文件哈希。下载包 MD5 与平台发布值 cfc56b86398a0c91cd866043b30bdb7f 一致。
- 已有 data/ 与 Project/ALLBot部署/data/ 未跟踪内容保持不动。
- 自测：文件清单、UTF-8 解码和原包一致性通过。下一步安装 Codex 用户级技能并交测试 Agent 复验，根任务 2 待复验。

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

## [2026-09-16] Codex — 完成技能安装与远端复验

- 已通过 skill-installer 安装指定源版本至 `C:/Users/Unbox/.codex/skills/达芬奇21中文操作手册`；9 个源文件与仓库副本逐一文本一致，仅换行格式有差异。
- 正式权限下推送恢复，合并远端新增提交后普通推送成功；远端 `main` 已核验为 `405f6b6559fb8cdc252e0dc3a489838702cca22e`，包含技能本体与简介。下方安装/推送受阻记录为历史状态。
- 根任务 1 复验关闭。源仓库嵌套 `.git` 仍留在本地导入目录，未提交至云端；不影响远端普通文件或独立安装目录。

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

---

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

> 🎯 作用：Agent 之间的"交接棒"  
> 📋 规则：每次改动必须记录，新记录放在最上面

---

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
