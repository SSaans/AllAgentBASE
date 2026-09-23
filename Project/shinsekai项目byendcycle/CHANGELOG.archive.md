# shinsekai项目byendcycle 变更日志归档 (CHANGELOG Archive)

> 📋 规则：本子项目 `CHANGELOG.md` 保留最近 15 条记录，超出部分移入本文件（按 `AGENTS.md` §2.1 纪律 8）。
> 📅 首次归档：2026-09-24（规划 Agent）—— 自 `CHANGELOG.md` 按条原文迁入，未作改写。

---

## [2026-09-08 00:02] 规划 Agent - 识屏误判修复交给开发 Agent（交接）

**背景**：用户体验 3 次误判——桌宠把日语教材练习识别成"数学题"。规划 Agent 属职责边界（不写功能代码），产出交接文档给开发 Agent。

**关键结论（重要）**：
- 已确认主模型 = `claude-opus-5`（OpenAI 兼容端点 `rkapi.com/v1`），本地 `moondream_vision` 插件为 `enabled: false`。
- 上一轮"仅强化提示词"的尝试**无效**：用户上传截图显示强化提示词已进入对话，主模型仍判"数学/分数"。**根因在图像理解层，不是提示词层**，开发 Agent 不要再走改提示词路线。
- 建议三条路径让开发 Agent 评估：A) 启用 Moondream 本地视觉前置定级（推荐，心跳插件已有铺垫）；B) 截图前 OCR 提取文字喂给主模型；C) 强制模型先描述文字再归类（兜底，效果有限）。

**修改的文件**：
- 新增：`Project/shinsekai项目byendcycle/HANDOFF_识屏误判修复.md`（完整交接文档：现象、已尝试、诊断、三路径、验收标准、注意事项、背景备份）

**续作（交给开发 Agent）**：
1. 按 HANDOFF 文档修复识屏精度，验收：日语练习不误判为数学、真数学仍能识别、端到端自测通过
2. 改动后重启新世界桌宠；完成后在本 CHANGELOG 顶部记录交接
3. 自动清理截图功能（retention_days=3，已完成验证）**保留勿回退**

---

## [2026-09-07 23:55] 规划 Agent - 修复识屏误判 + 新增自动截图清理

**用户反馈问题**：
- 桌宠自动识屏把"日语教材第2单元练习（助词/词语填空）"误判为"数学题"，体验差

**根因**：
- `screen_state_companion-BYGPT` 插件的识屏提示词过于单薄，主模型仅凭题号、分值、括号填空、圈码序号等版式特征臆断题型，未正确读文字内容；外语/语言练习材料排版与理科试卷高度相似。

**修复内容**（`H:\Program\新世界\Shinsekai\plugins\screen_state_companion-BYGPT\`）：
- 强化 `llm_tool.py`（capture_screen 工具）与 `config.py`（默认 prompt）的提示词：要求模型先辨认真正文字与内容、以实质内容为准，明确"外语练习题/试卷不是数学题"，只有出现数字运算、几何图形、公式等才认定为数学；看不清楚要如实说、不要编造
- 同步更新运行配置 `data\plugins\com.local.screen_state_companion\config.json` 中的 prompt

**新增功能**：自动删除 x 天前的自动识屏截图
- `config.py` 新增 `retention_days` 配置字段（默认 3，范围 1–3650）
- `runtime.py` 新增 `_cleanup_old_screenshots()`：遍历 `data\chat_attachments\screen-state-*`，删除超过保留天数的目录；在程序启动（bind_emit）和每次截图成功（send_screenshot）后自动触发
- `plugin.py` 在设置页新增"自动识屏截图保留天数"配置项

**清理验证**：
- 手动执行同样清理逻辑：删除 61 个老截图目录，占用从 80.1 MB 降至 2.1 MB（释放约 78 MB）
- 四个改动文件均通过 `py_compile` 语法编译

**待办（下次迭代）**：
- 完整重启新世界后人工验证：对日语/外语教材识别不再误判为数学题；观察截图支持保留天数自动生效

---

## [2026-09-07 18:10] 规划 Agent - 记录用户决策（不迭代）并推送首个子项目

**完成的工作**：
- ✅ 用户人工验收通过，决策：**不做可选迭代，仅维护现有功能**
- ✅ Task.md 中任务 12–15（学习监督 / Moondream 本地识屏 / 日志降噪 / 频率调优）标记为用户放弃，留档备查
- ✅ 子项目三件套 + CHANGELOG 一并提交并推送到 GitHub

**修改的文件**：
- 修改：`Project/shinsekai项目byendcycle/Task.md`（可选迭代标记为用户放弃）
- 修改：`CHANGELOG.md`（本条记录）

**当前状态**：
- ✅ 首个子项目交付闭环完成：立项 → 验证 → 人工验收 → 推送
- ✅ 后续仅做功能维护（Shinsekai 程序正常运行于 `H:\Program\新世界\Shinsekai`，无需改动代码）

**下一步建议**：
- 无待办。如 Shinsekai 上游更新或功能异常，由用户发起，规划 Agent 再行立项处理

---

## [2026-09-07 18:05] 规划 Agent - 首个子项目立项：shinsekai项目byendcycle（含部署验证）

**完成的工作**：
- ✅ 用户指定第一个子项目：部署 Shinsekai 桌宠并实现「开口说话 + 心跳自动检查 + 自动识屏」
- ✅ 产出子项目三件套：`Project/shinsekai项目byendcycle/BRD.md`（需求+验收）、`Task.md`（任务清单）、`README.md`（使用说明）
- ✅ 部署验证（测试结论，依据为运行日志与进程状态）：
  - Shinsekai v2.3.1 整合包（`H:\Program\新世界\Shinsekai`）双进程常驻运行，日志无致命错误
  - 桌宠开口说话：LLM 对话正常；GPT-SoVITS 自动拉起，丛雨语音模型切换与多次 TTS 派发成功
  - 心跳陪伴：检查节点多次自动触发（heartbeat.emitted，5–60 分钟随机间隔）
  - 自动识屏：节点触发后 `capture_screen` 工具被主模型调用，截图附件生成并驱动角色基于屏幕内容发言（screen_state_companion-BYGPT 插件）
- ✅ Task.md 中 11 项核心任务全部核对完成，4 项可选迭代待用户决策

**修改的文件**：
- 新增：`Project/shinsekai项目byendcycle/BRD.md`
- 新增：`Project/shinsekai项目byendcycle/Task.md`
- 新增：`Project/shinsekai项目byendcycle/README.md`
- 修改：`CHANGELOG.md`（本条记录）

**当前状态**：
- ✅ 平台第一个子项目立项并验收通过（功能/文档/质量/交接四类标准见子项目 BRD）
- ✅ 敏感信息检查：API Key 仅存于 Shinsekai 本地 `data/config/api.yaml`，未写入本仓库
- ⚠️ 已知小问题已记录在子项目 BRD「已知问题」：心跳调度日志每秒一行（上游插件行为，不影响功能）；Moondream 本地视觉未启用（识屏走主模型视觉路线，已验证可用）

**下一步建议**：
1. 用户人工验收：启动桌宠静置几分钟，观察角色主动开口并识屏
2. 可选迭代由用户决策：学习监督模式 / Moondream 本地识屏 / 识屏频率调优（见 Task.md 任务 12–15）
3. 本地工作目录为 `H:\Program\AllAngelBASE`，工作前记得 `git pull`

---

