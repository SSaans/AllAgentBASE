# distilly 变更日志

## [2026-09-20] 开发 Agent — 新子项目立项：distilly（蒸馏自己）

**完成的工作**：
- ✅ 分析上游项目 `titanwings/distilly`（分支 `dot-skill`）：通读 `SKILL.md` 全文、拉取完整文件树、`requirements.txt` 与 README，摸清四层机制（采集 / 分析 / 产出 / 进化）、三种 character family（`colleague` / `relationship` / `celebrity`）、8 个兼容宿主、7 个产出文件、`tools/` 与 `prompts/` 全清单
- ✅ **识别并记录关键预期落差**：上游是**知识蒸馏（Prompt 人设层）**，产出 Person Profile 技能包，**不训练模型权重**、不微调、不产出模型文件；上游自述「不宣称克隆本人」。用户「训练出一个个性化模型」的目标若按字面理解，本项目无法满足 → 已在 BRD 第一节置顶澄清，并给出替代路径（把产物作为微调路线的语料口径与评测 rubric 上游）
- ✅ 产出子项目四件：`BRD.md`（十四节：目标与澄清 / 上游速览 / 代码结构与核心功能 / 适用场景 / 落地映射 / 六阶段实施方案 / 环境与依赖 / 数据准备范围与格式 / 蒸馏关键环节 / 效果验证与评估 / 十条限制与风险 / 四类验收标准 / 边界 / 下一步）、`README.md`、`Task.md`（12 项任务）、`CHANGELOG.md`
- ✅ 落地关键差异点：family 固定 `colleague`；数据入口**只走 Ⓓ上传文件 + Ⓔ直接粘贴**（上游采集器只覆盖飞书/钉钉/Slack，本机 QQ/微信无采集器 → 材料整理是工作量大头）；**`colleague` 家庭无上游自动质检**，评估方案自建（known-answer / edge-case / voice 盲测 / rubric）
- ✅ 明确本机执行约束：Bash 工具不可用 → 上游 `bash`/`python3` 命令须改写为 PowerShell + Python 绝对路径
- ✅ 隐私边界：材料与产出物一律放仓库外 `D:\Program\distilly\`，三级分级（public/internal/private），涉及他人材料强制脱敏
- ✅ 更新根 `BRD.md`（状态行、候选清单、已立项子项目说明）与根 `CHANGELOG.md`（立项记录）
- ✅ 顺带按用户要求重整记忆分层：用户级记忆只留跨项目基础（红线 / 沟通偏好 / 本机环境 / Git 推送），工作区记忆改为索引，项目细节下沉到 `D:\.workbuddy\memory\projects\<项目>.md`

**修改的文件**：
- 新增：`Project/distilly/`（`BRD.md`、`README.md`、`Task.md`、`CHANGELOG.md`）
- 修改：`BRD.md`、`CHANGELOG.md`（仅文档）

**当前状态**：
- ✅ **阶段 0 完成**：立项 + 规划，方案可执行、阶段可验收
- ⏳ **未做任何部署与执行**：未 clone 上游、未装依赖、未整理材料、未执行蒸馏。本轮按用户要求「不附带具体代码实现」，只出规划
- ⚠️ **角色边界声明**：本 BRD 由**开发 Agent 按用户明确指派代拟**，其需求章节按 `AGENTS.md` 属规划 Agent 职责范围 → 已在 BRD 与 `Task.md`（任务 2）标注「**待规划 Agent 确认**」，未越权改动任何既有 SOP 与根级规范
- ⚠️ 待用户拍板 3 项：① 预期对齐（人设包 ≠ 权重模型）② 实施方案与 family 选择 ③ 材料是否加密存放

**下一步建议**：
1. 用户先答任务 1（预期对齐）——这是后续一切工作的前提
2. 用户回复「按这个方案做」后，对开发 Agent 下达：「你是开发 Agent，根据 DEVELOPMENT.md，按 `Project/distilly/Task.md` 任务 4 开始」
3. 阶段 2 需要用户配合导出 QQ / 微信材料（无自动采集器）
