<div align="center">

# 🤖 AllAgentBASE

**多 Agent 协作的项目同步与管理平台**

*让 AI 助手在 GitHub 上分角色接力，需求、实现、验收各有归属*

[![GitHub stars](https://img.shields.io/github/stars/SSaans/AllAgentBASE?style=social)](https://github.com/SSaans/AllAgentBASE)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub last commit](https://img.shields.io/github/last-commit/SSaans/AllAgentBASE)](https://github.com/SSaans/AllAgentBASE/commits)

[这是什么](#-这是什么) · [快速开始](#-快速开始) · [目录结构](#-目录结构) · [子项目](#-子项目) · [干活规矩](#-干活规矩)

</div>

---

## 🎯 这是什么

一个用 Git 做同步带的协作仓库。三个 AI 角色在同一个项目上接力，但**任何一次改动都必须先立成一个 change**，写清楚为什么改、改成什么样、怎么实现、分几步做，做完归档。

```
用户提需求
   ↓
规划 Agent ── 写 change 四件套（提案 / 规格 / 设计 / 任务）
   ↓
开发 Agent ── 按 tasks.md 逐步实现，勾掉完成的
   ↓
测试 Agent ── 按规格里的场景逐条验，签字放行
   ↓
归档 ── change 移入 archive，规格合并进 specs
```

一次改动只在一个文件夹里发生，不需要在四五个文档之间找「现在该干什么」。

---

## 🚀 快速开始

### 第一步：建仓库

```bash
git init
git remote add origin https://github.com/你的用户名/仓库名.git
# ⚠️ 逐路径 add，不要用 git add .
git add README.md AGENTS.md .gitignore
git commit -m "初始化项目"
git push -u origin main
```

### 第二步：建规格目录

```bash
openspec init --tools agents --language zh-CN
```

这条命令只创建 `openspec/` 与 `.agents/skills/`，不改动仓库里其他文件。

### 第三步：立第一个 change

```bash
openspec new change add-你的功能名
openspec status --change add-你的功能名
```

按提示依次产出 `proposal.md`、`specs/<能力>/spec.md`、`design.md`、`tasks.md`。四件齐了才能开工。

### 第四步：让 Agent 接力

| 角色 | 派活话术 | 交出什么 |
|---|---|---|
| 规划 | 「把这需求立成 change」 | 四件套写完，`openspec validate --strict` 通过 |
| 开发 | 「按 change 实现」 | 代码 + `tasks.md` 勾选 + 提交推送 |
| 测试 | 「按场景验收」 | 验收结论，放行归档 |

---

## 📂 目录结构

```
AllAgentBASE/
├── AGENTS.md            # Agent 干活的总规矩，开工必读
├── README.md            # 你现在看的这份
├── agents/              # 三个角色各自的手册
│   ├── 规划.md
│   ├── 开发.md
│   └── 测试.md
├── openspec/            # 平台自己的规格
│   ├── config.yaml
│   ├── specs/           # 已经做到的，按能力分文件夹
│   └── changes/
│       └── archive/     # 做过的改变，一次一个文件夹
├── Project/             # 10 个子项目，每个一套 README + openspec
├── skill/               # 可复用的技能资产
├── Guide/               # 图文指南
├── CHANGELOG-历史.md    # 2026-10-27 之前的时间线，已冻结
└── LICENSE
```

子项目长这样：

```
Project/<项目名>/
├── README.md            # 这项目要做什么、怎么用
├── openspec/
│   ├── config.yaml
│   ├── specs/           # 已经实现的能力与场景
│   └── changes/archive/ # 每次改动的完整记录
└── （代码目录由开发 Agent 建）
```

---

## 📦 子项目

| 子项目 | 做什么 | 目录 |
|---|---|---|
| ALLBot部署 | AstrBot QQ 机器人「丛雨」 | `Project/ALLBot部署/` |
| ALLSkill | 外部技能的调研、评估与引进 | `Project/ALLSkill/` |
| 全惠惠平面设计 | 品牌日常平面产出与文案 | `Project/全惠惠平面设计/` |
| 全惠惠视频制作 | 会议快剪、记录、片尾与宣传片 | `Project/全惠惠视频制作/` |
| distilly | 蒸馏自己，生成个人技能包 | `Project/distilly/` |
| 万有引力 | 跨平台个人聊天记录归档 | `Project/万有引力/` |
| 表情包同步 | TIM 表情包导出与导入 | `Project/表情包同步/` |
| 中转站搭建 | 本机 new-api 面板聚合上游 | `Project/中转站搭建/` |
| shinsekai项目byendcycle | 桌面宠物部署 | `Project/shinsekai项目byendcycle/` |
| bilisum部署 | BiliSum 视频摘要工具（已搁置） | `Project/bilisum部署/` |

每个项目的当前进度、验收标准、历史改动，看它自己的 README 与 `openspec/`。

---

## 📋 文档规范

| 文件 | 装什么 | 谁维护 |
|---|---|---|
| `README.md` | 项目是什么、有哪些子项目、怎么上手 | 规划 Agent |
| `AGENTS.md` | 干活规矩、skill 路由、命令速查 | 规划 Agent |
| `agents/*.md` | 单个角色的开工清单与红线 | 规划 Agent |
| `openspec/specs/` | 已经实现的行为，带场景 | 开发 Agent 写，规划 Agent 审 |
| `openspec/changes/` | 正在做的改动 | 谁立项谁维护 |
| `openspec/changes/archive/` | 做过的改动，只增不改 | 自动归档 |

一条硬规矩：**同一个事实只写一处**。行为要求写进 specs，README 只留指向，两边说法不一致时以 specs 为准。

---

## 🛡️ 干活规矩

1. **没有 change 不动手**，零碎改动（错别字、注释）除外
2. **开工先读** AGENTS.md，再按角色读 `agents/` 里自己那份
3. **实现前读齐四件套**，只看 tasks 不看规格等于瞎写
4. **逐路径 `git add`**，绝不用 `git add .`
5. **推送自己搞定**，冲突自己解，不把操作甩给用户
6. **不传秘密**，密钥、账号、本机路径一律不入库
7. **做完要归档**，没归档的 change 等于没做完

---

## ❓ 常见问题

**Q：为什么不写 CHANGELOG 了？**
一个 change 归档后，为什么改、改成什么样、怎么做的、分几步，四件都在目录里，比流水账详细。零碎改动靠 git 提交信息。2026-10-27 之前的记录冻结在 `CHANGELOG-历史.md`。

**Q：多个 Agent 能同时干活吗？**
能，但避免同时改同一个文件。接力顺序是规划 → 开发 → 测试。

**Q：规格和 README 有什么区别？**
README 写给人看，讲这是什么、怎么用。规格写给执行者看，讲系统必须表现出什么行为，带可以逐条验证的场景。

**Q：能不能跳过测试直接归档？**
不能。归档前要过 `openspec validate --strict`，测试 Agent 还要按场景验一遍。

---

## 🤝 贡献指南

欢迎提 Issue 和 Pull Request。

1. Fork 本仓库
2. 建分支 `git checkout -b feature/xxx`
3. 提交改动
4. 推送并开 PR

---

## 📄 许可证

MIT，详见 [LICENSE](LICENSE)。

---

<div align="center">

**Made with ❤️ by the AllAgentBASE Team**

[返回顶部](#-allagentbase)

</div>
