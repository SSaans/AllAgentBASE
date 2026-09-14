# ALLBot部署 变更日志 (CHANGELOG)

> 📋 范围：本文件只记录 ALLBot部署 子项目的变更；平台级（AllAgentBASE 自身与大规划）记录见根 `CHANGELOG.md`。
> 📋 规则：新记录放在最上面。以下条目于 2026-09-15 由根 `CHANGELOG.md` 原文拆分迁入，未作改写。

---

## [2026-09-15] 规划 Agent - 确认 ALLBot部署 BRD 事实勘误（闭环任务 14）并同步 Task.md

**背景**：`Project/ALLBot部署/Task.md` 任务 14「规划事实需勘误」明确写着「开发仅在 README/CHANGELOG 记录证据，BRD 需求部分交规划 Agent 确认」。本轮按 `PLANNING.md` 第二步第 3 条（过期描述属职责内，直接修正）闭环该任务。

**核对结论：BRD.md 确认 4 处过期描述并修正**：
1. 头部状态「规划完成，待用户确认后进入开发」已过期 → 改为「开发与自测完成，待测试 Agent 正式验收」
2. 功能 1「疑点（需开发验证，非已确认 Bug）」中「空白名单语义待确认」「`log_file_enable=false` 建议开启」均已过期 → 重写为「已验证结论」，写明空白名单直接放行、日志开关已置 true、三条 `/` 指令已真实进总线
3. 验收标准「修改 `forward_threshold` 后立即生效，无需重启」表述不完整 → 补注「须经对应配置档 API 保存才热生效；直接编辑磁盘 JSON 不会更新运行对象」（与 README.md 一致）
4. 「开发进度快照」注释仍指向已清除的副本 `D:\Program\AllAgentBASE` → 按「保留原文 + 追加勘误」处理，不改写历史表述，另加勘误标注提示勿再按该路径查找

**已核对无需修改**：QQ 走独立配置档「丛雨丸」、`keep_original_persona=true` 才加载丛雨人设、`min_messages_threshold=200` 仅限定时分析、磁盘编辑不等于热更新——这 4 处事实 BRD 已在前轮合并 Codex 证据时吸收，全文核对无残留误述，本次不再改动。

**完成的工作**：
- ✅ 勘误 `Project/ALLBot部署/BRD.md` 共 4 处
- ✅ `Task.md`：任务 14 由「待办」改为「待复验」，注明规划 Agent 已完成 BRD 勘误；按 `AGENTS.md` 约定 `[x]` 关闭仅测试 Agent 可勾选
- ✅ `Task.md` 头部状态行同步为当前实际进度
- ✅ 顺带修正上一条记录中「待办：网络恢复后推送」的过期表述（该轮推送实际已成功）
- ✅ CHANGELOG 新增本条，最旧 1 条（2026-09-08 识屏误判压缩 Bug 回退）移入 `CHANGELOG.archive.md`，主文件保持 15 条上限

**修改的文件**：
- 修改：`Project/ALLBot部署/BRD.md`、`Project/ALLBot部署/Task.md`、`CHANGELOG.md`、`CHANGELOG.archive.md`
- 未新增任何文件；未改动运行目录、代码与配置

**下一步**：
- 交测试 Agent：按 Task.md 待复验项（任务 2/3/4/5/6/10/11/14）结合真实群内结果正式验收，`[x]` 由测试 Agent 勾选
- 交开发 Agent：任务 12 日志落盘，经 Launcher 正常重启后核对 `core/data/logs/astrbot.log`
- 等用户输入：任务 13 `/群漫画` 绘图供应商凭据与端点；任务 7/8/9 待用户决策，保持待办不启用
- 规划 Agent 本轮无遗留阻塞项

---

## [2026-09-15] 开发 Agent — ALLBot 指令链路、人设继承与配置核实（持续验证中）

**已完成的开发与自测**：
- 开工工作区干净，git pull --ff-only 同步至 98cf6ca；通读根/子项目 BRD、DEVELOPMENT、AGENTS 及最近三条日志。
- 发现 QQ 实际路由到“丛雨丸”独立配置，旧 wake_prefix 只有“丛雨”，admins_id 只有昵称 Edi。通过原生配置 API 给实际 QQ 配置补 `/` 并保留“丛雨”；默认与 QQ 档均按用户明确提供的 QQ 号添加管理员，保留原条目。
- 修正插件 analysis_features.keep_original_persona=false 导致的系统人设缺失，改为 true；保留已有丛雨人设、不指定新人设。全局 log_file_enable 从 false 改 true。
- 核心空白名单直接放行；插件模型留空会回退会话 provider；手动分析绕过 200 条阈值；阈值需通过对应配置档 API 保存才热生效。均已核对安装源码。
- 用户授权指定测试群并亲自重发三条指令。2026-09-15 00:52 起，/分析设置正常，/群分析使用会话 claude-opus-5/claude-opus-5，真实完成话题 2、称号 2、金句 5、质量锐评 1。结构化 trace 状态 succeeded，00:53:43 报告图片生成，用户确认除漫画外正常。群聊原文与报告未入库。
- /群漫画成功生成分镜，但 drawing_provider_overrides 为空，trace failed；用户拟提供 GPT Image 2 供应商，等待本机配置资料。不得将指令通达当成出图成功。
- 新增 tests/check_installed_source.py：8 项隔离自测通过，执行安装源码中的白名单、人设、模型回退、定时关闭、转发分支；覆盖 1499/1500/1501 字和自定义阈值。该结果不是正式验收，也不覆盖完整消息流水线。

**改动文件与交付范围**：
- 本仓库：Project/ALLBot部署/Task.md、README.md、tests/check_installed_source.py、CHANGELOG.md。
- 仓库外：实例 core/data/cmd_config.json（文件日志与管理员）、core/data/config/abconf_626c9487-1b19-4180-8878-48a1b85b26fe.json（QQ 实际前缀与管理员）、core/data/config/astrbot_plugin_qq_group_daily_analysis_config.json（人设继承）。未改业务源码；Git 中仅有自测脚本和改动摘要，不包含运行配置备份或凭据。

**运行保护与未完成项**：
- 原实例 Launcher PID 2456 → venv 4304 → Python 9076，Windows session 1；未另起聊天实例、未清历史、未全杀进程。插件重载前活跃分析任务为 0，重载日志确认旧插件资源清理完成，定时分析名单为空，不注册定时任务。
- 日志开关落盘后当前进程未动态增加文件 sink，已请用户通过 Launcher 正常重启后核查；电脑控制工具因环境启动错误不可用。管理 API 可用，未改 SnowLuma 配置。
- 任务 2/3/4 和修复 10/11 待复验；漫画供应商、长卡片群内展示、日志落盘仍验证中。普通群员权限提示、≥200 条群与图片视觉/人设口吻正式验收交测试 Agent。可选任务 7–9 未启动。
- 新问题均已登记 Task 10–14；BRD 的需求部分未改，规划事实差异由规划 Agent 勘误。

**交接说明（规划 Agent 补记 2026-09-15）**：本条证据原留在 Codex 本地克隆 `D:\Program\AllAgentBASE`（未提交未推送），规划 Agent 于后续轮次合并入库；据此修正此前快照中的三处误判——① 转发卡片长消息实为「已实测可点开」而非中断未定；② 群漫画实为「已完成分镜、缺绘图供应商」而非未开始；③ QQ 配置实为独立档「丛雨丸」而非 cmd_config.json。BRD/Task 已按此勘误。

---

## [2026-09-15 01:10] 规划 Agent - Codex 5h 限额中断，ALLBot部署 交接规划更新

**完成的工作**：
- ✅ 读取 Codex 会话截图 + 运行时核查，还原开发进度：
  - 核心配置修复已落地（`cmd_config.json`：`log_file_enable=true`；`admins_id` 增加用户 QQ 号，号码不落库）
  - 实测结论：手动 `/群分析` 不受 200 条/日下限限制（已写入 BRD 风险表，待接手复核落库）
  - 转发卡片长消息实测被限额打断、结果未知；进程未重启（自 09-14 17:54 常驻），`astrbot.log` 尚未生成
- ✅ 更新子项目 BRD.md：新增「开发进度快照（2026-09-15 交接）」小节；风险表修订 200 条限制项、新增日志重启项
- ✅ 重写子项目 Task.md：按证据标注任务状态（任务 1 待复验 / 2-3 修复中），并入 Codex 遗留项（漫画 API、长卡片结果、日志落盘）与续跑项
- ✅ 归档 CHANGELOG 最旧 1 条至 `CHANGELOG.archive.md`（保持 15 条）
- ⚠️ GitHub 网络不可达（Failed to connect github.com:443），本地提交完成，**push 待网络恢复后重试**；远端是否存在 Codex 提交未知

**修改的文件**：
- 修改：`Project/ALLBot部署/BRD.md`、`Project/ALLBot部署/Task.md`、`CHANGELOG.md`、`CHANGELOG.archive.md`

**当前状态**：
- ✅ 交接规划就绪，可交给新开发 Agent（启动指令见本次会话回复）
- ⚠️ 续跑待办：转发卡片实测、群漫画、日志落盘验证、git push

---

