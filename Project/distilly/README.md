# Distilly「蒸馏自己」— 使用说明

> 上游项目：[titanwings/distilly](https://github.com/titanwings/distilly)（分支 `dot-skill`，MIT）
> 需求与验收标准见 `BRD.md`；任务看板见 `Task.md`；变更记录见 `CHANGELOG.md`。

---

## 一句话

把用户本人的历史材料（聊天、文档、邮件、备注）喂给上游项目，产出一套**「我自己」的技能包（Skill）**，装进本机 Agent 后，用我的口吻和套路说话做事。

> 本项目就是**整理成 skill**：不训练模型、不微调、不产出权重文件。

---

## 状态

| 项 | 值 |
|---|---|
| 阶段 | **阶段 1 已完成**（环境部署与验证），阶段 2 待启动 |
| 当前可做 | 准备个人聊天记录与材料，启动阶段 2 |
| 已完成 | ✅ 上游代码部署、Python 环境、测试验证（73 项 / 71 通过）、技能安装（`/distilly`） |

---

## 关键路径（实测）

| 项 | 位置 / 值 |
|---|---|
| 上游源码目录 | `D:\Program\distilly`（**独立 clone，仓库外**） |
| Python 虚拟环境 | `D:\Program\distilly\.venv`（CPython 3.13.14） |
| 个人材料目录（计划） | `D:\Program\distilly\knowledge\self\`（**仓库外，绝不入 git**） |
| 产出物目录（计划） | `D:\Program\distilly\skills\colleague\<代号>\`（**仓库外**） |
| 技能安装位置 | `D:\Project\AllAgentBASE\.claude\skills\distilly`（宿主 Claude Code，已加 `.gitignore`） |
| 触发方式 | 在 Claude Code 里输入 `/distilly` |
| 本仓库只放 | `Project/distilly/` 下的 4 个 md |

> 与 `Project/bilisum部署` 同模式：**源码与数据在仓库外，仓库只留文档**。

---

## 环境（实测）

| 项 | 要求 | 本机现状 |
|---|---|---|
| Python | ≥ 3.9 | ✅ 3.13.14（`.venv`） |
| 核心依赖 | `requests` / `pypinyin` / `python-docx` / `openpyxl` / `pytest` | ✅ 全部已装 |
| 不装 | `playwright`、`slack-sdk` | 本项目不走飞书/钉钉/Slack 采集入口，**不需要** |
| 宿主 | 能读文件 + 执行命令的 Agent 宿主 | ✅ Claude Code（`/distilly`） |
| 外部账号 | **不需要** | — |

⚠️ **本机执行注意**：Bash 工具不可用（Git Bash 损坏）→ 上游的 `bash` / `python3` 命令要改成 **PowerShell + Python 绝对路径**；中文文件读写务必用 UTF-8。

---

## 怎么用

宿主里说一句话即可启动创建流程：

> 用 Distilly 给我创建一个 Person Profile（family 选 colleague）

随后按提示走：填 3 个问题的基本信息 → 提供材料（上传文件 / 直接粘贴）→ 核对预览摘要 → 确认生成 → 装进宿主。

材料准备的格式与隐私分级要求见 `BRD.md` 第八节。

---

## 敏感信息红线

1. **材料、产出物一律放仓库外的 `D:\Program\distilly\`**，任何情况下不入 git。
2. **涉及他人的聊天 / 邮件必须脱敏**（代称化）。
3. **产出物是「模拟我」，不分享、不外发。**
4. 本仓库根目录与 `Project/ALLBot部署/` 下各有一处未跟踪 `data/` 目录（含凭据，处置待用户裁决）——**与本项目无关，不要动**。
5. 仓库工作区里出现的杂散副本（`Programdistilly/`、`DＺProjectAllAgentBASEgit_pull_result.txt`）是**路径拼接失误的产物**，已加 `.gitignore` 防误提交；**清理需用户明确同意**。

---

## 本机改动登记

| 日期 | 改动 | 位置 | 说明 |
|---|---|---|---|
| 2026-09-20 03:xx | 文档勘误：撤掉「不是模型」的澄清口径 | `Project/distilly/` | 用户确认目标就是「整理成 skill」，改为范围边界表述 |
| 2026-09-20 03:xx | `.gitignore` 加固 | 仓库根 | 忽略 `.claude/`、`Programdistilly/`、路径拼接杂散文件，防误提交 |
| 2026-09-20 02:40 | 完成阶段 1 环境部署 | `D:\Program\distilly` | clone 上游、装 Python 环境、跑测试（71/73 通过）、安装到 `.claude/skills/distilly` |
| 2026-09-20 | 新建子项目文档 4 件 | `Project/distilly/` | 仅文档，无代码改动 |
| — | 上游源码改动 | — | **暂无**（如为适配本机改动上游文件，须在此登记） |

---

## 风险速查（完整表见 `BRD.md` 第十一节）

1. **微信/QQ 无内置采集器** —— 材料整理是工作量大头。
2. **隐私高敏** —— 三级分级、仓库外存放、强制脱敏。
3. **`colleague` 家庭无自动质检** —— 评估方案要自建。
4. **上游演进快** —— 锁 commit，升级前备份。
5. **仓库内易误落盘** —— `.claude/` 3000+ 文件，已加 ignore，勿提交。
