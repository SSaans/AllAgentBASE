# 业务需求文档 (BRD)

> 📅 更新时间：2026-09-12  
> 👤 维护者：规划 Agent  
> 🎯 状态：已立项 Shinsekai，当前仅维护；心跳完整验收与退出问题待处理（见子项目任务 17、18）

---

## 项目目标

建立一个 **多 Agent 协作的 GitHub 项目管理平台**，让不同的 AI Agent 通过 Git 同步，在同一个仓库中接力完成任务。

---

## 核心功能

### 1. 统一的项目结构
```
AllAgentBASE/
├── Project/          # 正式项目存放区
├── Guide/            # 指南文档
├── Readme/           # 说明文件
├── Any/              # 其他杂项
├── BRD.md            # 业务需求文档（本文件）
├── CHANGELOG.md      # 变更日志
├── AGENTS.md         # Agent 角色定义
├── PLANNING.md       # 规划 Agent 操作手册（SOP）
├── DEVELOPMENT.md    # 开发 Agent 操作手册（SOP）
├── TESTING.md        # 测试 Agent 操作手册（SOP）
└── .gitignore        # Git 忽略规则
```

### 2. Agent 接力工作流

每个阶段一本操作手册（SOP），开工时对 AI 下达「根据 XX.md 的要求进行操作」的指令，AI 照手册办事：

- **规划 Agent**：按 PLANNING.md 执行 —— 审阅现状、补充需求、产出 Task.md 任务清单
- **开发 Agent**：按 DEVELOPMENT.md 执行 —— 照 BRD 与 Task.md 编码实现、自测
- **测试 Agent**：按 TESTING.md 执行 —— 按验收标准逐项测试、修小 Bug、出结论

每本手册内置：前置检查清单（开工前逐项核对）、工作步骤、红线（禁止事项）。

### 3. Git 同步机制
- Agent 开始工作前：`git pull` 拉取最新内容
- Agent 完成工作后：`git push` 推送修改
- 通过 CHANGELOG.md 进行工作交接

---

## 技术方案

### 版本控制
- **工具**：Git + GitHub
- **仓库地址**：https://github.com/SSaans/AllAgentBASE（2026-09-07 勘误：原误写为 SSaann）
- **分支策略**：暂时使用 main 分支，后续可根据需要建立功能分支

### 文档管理
- **BRD.md**：唯一真相来源，记录项目需求和技术方案
- **CHANGELOG.md**：Agent 交接日志，记录每次改动
- **AGENTS.md**：明确各 Agent 的职责边界
- **PLANNING.md / DEVELOPMENT.md / TESTING.md**：各阶段操作手册（SOP），Agent 开工的执行依据

### 协作规则
1. 所有 Agent 必须先读 BRD.md 和 CHANGELOG.md 最近 3 条
2. 完成工作后必须更新 CHANGELOG.md
3. 避免多个 Agent 同时修改同一文件
4. 敏感信息（密码、API Key）禁止提交到仓库
5. **任务闭环（2026-09-08 新增）**：任何 Agent 发现 Bug 或新需求，必须**当场**记入对应子项目的 Task.md（没有就建一节）。任务状态流转：`待办 → 修复中 → 待复验 → 已关闭`。Task.md 是活看板，必须随工作实时更新；**只写 CHANGELOG 不动 Task.md 视为未完成交接**
6. **提交闭环（2026-09-08 新增）**：写日志 ≠ 完工。收工三件套缺一不可：① CHANGELOG 已记录 ② Task.md 状态已更新 ③ `git commit + push` 已执行。push 失败先 `git pull` 解决冲突再重试
7. **仓库外代码（2026-09-08 新增）**：子项目代码可能在实际运行目录而非本仓库（如 Shinsekai 位于 `H:\Program\新世界\Shinsekai`）。修改仓库外代码后，必须把**修复说明 + 改动文件与摘要**写进本仓库（子项目 HANDOFF 文档或 CHANGELOG）并提交推送，保证仓库始终是唯一真相来源

---

## 验收标准（平台自身）

> 2026-09-07 规划 Agent 更新：逐项核对当前完成度

- [x] 项目结构完整（4 个文件夹 + 核心文档）— Project/、Any/ 曾缺失，已用 .gitkeep 补齐
- [x] 核心文档齐全（BRD、CHANGELOG、AGENTS、.gitignore）— 2026-09-06 开发 Agent 创建并验证
- [x] 能够成功执行 git pull/push — pull 于 2026-09-06 验证；push 由规划 Agent 2026-09-07 提交本次更新验证
- [x] 多个 Agent 能够基于 CHANGELOG 进行协作 — 已完成 开发 Agent → 规划 Agent 两棒交接
- [x] README.md 已推送到 GitHub — 根目录与 Readme/ 各有一份

---

## 不做的事情

- ❌ 不支持多个 Agent 同时编辑同一文件
- ❌ 不自动解决 Git 冲突（需要人工介入）
- ❌ 不存储敏感信息到仓库

---

## 子项目需求规范（2026-09-07 规划 Agent 补充）

> 本节用于解决原"待补充内容"中的三个空白项：具体子项目需求、子项目验收标准、自动化测试方案

### 1. 子项目立项流程

所有正式子项目放入 `Project/<子项目名>/`，立项必须满足：

1. **用户发起**：由用户指定要做什么，Agent 不得自行立项
2. **规划 Agent 起草子项目 BRD**：包含目标、功能清单、验收标准
3. **用户确认后进入开发**：开发 Agent 才能开始编码

每个子项目的标准目录结构：

```
Project/<子项目名>/
├── BRD.md          # 子项目需求（含验收标准，唯一真相来源）
├── README.md       # 使用说明
└── src/ 等         # 代码目录（开发 Agent 创建）
```

### 2. 候选子项目清单（等待用户决策）

| 候选项目 | 说明 | 优先级 |
|---------|------|--------|
| QQ 群机器人 | BRD 初始候选；对接 QQ 群消息，实现自动回复/群管理 | 待定 |
| CHANGELOG 归档工具 | 当 CHANGELOG 超过 15 条时自动归档旧记录到 CHANGELOG.archive.md | 待定 |
| 文档一致性检查脚本 | 校验 BRD/CHANGELOG 格式与勾选项状态，可后续接入 CI | 待定 |

> 2026-09-12 同步纠正：已立项子项目为 `Project/shinsekai项目byendcycle/`。上表为历史候选，不代表当前授权；用户已决定仅维护现有功能。

### 3. 子项目验收标准（通用模板）

每个子项目的 BRD 必须包含以下四类验收标准，缺一不可：

1. **功能验收**：逐条列出可测试的功能点（"能够 XXX"），测试 Agent 逐项核对
2. **文档验收**：CHANGELOG 有完整的开发与测试记录；README 更新到最新用法
3. **质量验收**：无敏感信息提交；无未说明的 TODO/FIXME 遗留；依赖在 README 中声明
4. **交接验收**：测试 Agent 在 CHANGELOG 中明确签字"通过"；未通过则记录 Bug 清单并回到开发 Agent

### 4. 自动化测试方案（轻量级，分阶段）

考虑到平台当前以文档协作为主，不引入重型 CI，分三个阶段推进：

- **阶段一（当前，纯文档协作）**：不强制自动化；由测试 Agent 按验收标准人工核对
- **阶段二（首个子项目落地后）**：子项目自带最小测试集（如 Python 项目用 pytest），测试 Agent 本地执行并将结果记入 CHANGELOG
- **阶段三（可选）**：接入 GitHub Actions，push 时自动运行测试集与文档格式检查

### 5. 平台运维规则（补充）

- **CHANGELOG 归档**：按用户要求复用已有文件，保留历史证据与纠正记录，不自动新增归档 MD。
- **文件夹职责**：
  - `Project/`：正式子项目（立项后才可放入）
  - `Guide/`：工作流指南文档
  - `Readme/`：说明文件与模板
  - `Any/`：实验性、临时内容（不属于正式交付物）

---

## 历史项目状态审阅（2026-09-07，非当前状态）

- ✅ 仓库共 6 个提交，工作区干净，与远程 main 同步
- ✅ 核心文档齐全：BRD、CHANGELOG、AGENTS、.gitignore、README（根目录 + Readme/）
- ✅ 协作机制已实际运转一轮：开发 Agent 完成初始化并通过 CHANGELOG 交接
- ⚠️ `Project/`、`Any/` 文件夹缺失（Git 不跟踪空目录）→ 本次以 `.gitkeep` 占位补齐
- ⚠️ BRD 仓库地址笔误（SSaann → SSaans）→ 已修正
- ❌ 尚无已立项子项目 → 等待用户从候选清单指定第一个子项目

---

**历史下一步（2026-09-07，已由上述立项状态取代）**：
1. 用户确认第一个子项目（可从候选清单选择，也可提出新想法）
2. 规划 Agent 产出 `Project/<子项目名>/BRD.md`
3. 开发 Agent 在子项目 BRD 确认后接力开发
