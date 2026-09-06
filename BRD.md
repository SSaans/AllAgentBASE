# 业务需求文档 (BRD)

> 📅 更新时间：2026-09-06  
> 👤 维护者：规划 Agent  
> 🎯 状态：初始化

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
└── .gitignore        # Git 忽略规则
```

### 2. Agent 接力工作流
- **规划 Agent**：审阅代码、补充需求、规划技术方案
- **开发 Agent**：根据 BRD 编写代码、实现功能
- **测试 Agent**：按照验收标准测试、修复 Bug

### 3. Git 同步机制
- Agent 开始工作前：`git pull` 拉取最新内容
- Agent 完成工作后：`git push` 推送修改
- 通过 CHANGELOG.md 进行工作交接

---

## 技术方案

### 版本控制
- **工具**：Git + GitHub
- **仓库地址**：https://github.com/SSaann/AllAgentBASE
- **分支策略**：暂时使用 main 分支，后续可根据需要建立功能分支

### 文档管理
- **BRD.md**：唯一真相来源，记录项目需求和技术方案
- **CHANGELOG.md**：Agent 交接日志，记录每次改动
- **AGENTS.md**：明确各 Agent 的职责边界

### 协作规则
1. 所有 Agent 必须先读 BRD.md 和 CHANGELOG.md 最近 3 条
2. 完成工作后必须更新 CHANGELOG.md
3. 避免多个 Agent 同时修改同一文件
4. 敏感信息（密码、API Key）禁止提交到仓库

---

## 验收标准

- [ ] 项目结构完整（4 个文件夹 + 核心文档）
- [ ] 核心文档齐全（BRD、CHANGELOG、AGENTS、.gitignore）
- [ ] 能够成功执行 git pull/push
- [ ] 多个 Agent 能够基于 CHANGELOG 进行协作
- [ ] README.md 已推送到 GitHub

---

## 不做的事情

- ❌ 不支持多个 Agent 同时编辑同一文件
- ❌ 不自动解决 Git 冲突（需要人工介入）
- ❌ 不存储敏感信息到仓库

---

## 待补充内容

> 规划 Agent 请在此记录需要进一步明确的需求

- [ ] 具体子项目的需求（如：QQ 群机器人）
- [ ] 每个子项目的验收标准
- [ ] 自动化测试方案（如果需要）

---

**下一步**：开发 Agent 根据此文档创建项目基础文件
