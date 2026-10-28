<div align="center">

# 🤖 AllAgentBASE

**两个 AI 角色接力干活的项目骨架**

*需求写清楚、做完留证据，隔一个月回来还认得*

[![GitHub stars](https://img.shields.io/github/stars/SSaans/AllAgentBASE?style=social)](https://github.com/SSaans/AllAgentBASE)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub last commit](https://img.shields.io/github/last-commit/SSaans/AllAgentBASE)](https://github.com/SSaans/AllAgentBASE/commits)

[这是什么](#-这是什么) · [快速开始](#-快速开始) · [目录结构](#-目录结构) · [一次改动长什么样](#-一次改动长什么样) · [常用命令](#-常用命令) · [子项目](#-子项目) · [干活规矩](#-干活规矩)

</div>

---

## 🎯 这是什么

这里放着一个项目，加上一套让它自己往前走的规矩。

**一句话**：你说要什么，规划写清楚，开发做并且自己试，你点头才算完。

```
   你说要什么                    ← 你，一句话就够
        ↓
   规划写清楚                     ← 为什么改、改成什么样、分几步
        ↓
   你瞄一眼说「开工」              ← 你，看那张清单对不对
        ↓
   开发做，还自己试                ← 每条都试一遍，写成一行行记录
        ↓
   你点一遍说「行」                ← 你，说不行就打回，它自己回头改
        ↓
   归档                          ← 合并进 specs，下次谁接手只看 specs
```

为什么要写下来：一个改动要是没人写清楚，接手的人就得从头猜一遍。写在纸上比留在脑子里靠得住，隔一个月回来也还认得。

**一次改动只在一个文件夹里发生**，不用在四五个文档之间找「现在该干什么」。

**几个词先说清**

| 词 | 白话 |
|---|---|
| change | 一次改动的文件夹。为什么改、改成什么样、怎么做、分几步，全装在里面 |
| specs | 已经做到的事，一条条写成「什么情况下会怎样」。改完归档就并进来 |
| 场景 | 就是那一句「什么情况下会怎样」。验收时照着它试一遍，试不出结果的不算 |
| 归档 | 把做完的改动合并进 specs，再把文件夹搬进 archive。搬完就算完事 |

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

这条会建 `openspec/` 目录，再往 `.agents/skills/` 里放六个干活用的技能（探索、提案、实现、改方案、同步规格、归档）。仓库里其他文件一个字不动。

子项目想各管各的，就在子项目目录里再跑一次。OpenSpec 认离当前目录最近的那一套。

### 第三步：立第一个 change

```bash
openspec new change add-你的功能名          # 只建文件夹，不写内容
openspec status --change add-你的功能名     # 看还缺哪个文件
openspec instructions proposal --change add-你的功能名   # 让 Agent 按模板写提案
```

然后依次产出 `proposal.md`、`specs/<能力>/spec.md`、`tasks.md`。这三件齐了就能开工，`design.md` 看情况，改动简单就不写，官方模板也是这么定的。

### 第四步：让 Agent 接力

| 角色 | 派活话术 | 交出什么 |
|---|---|---|
| 规划 | 「把这需求立成 change」 | 提案、规格、任务三件写完，`openspec validate --strict` 通过 |
| 开发 | 「按 change 实现并验完」 | 代码 + `tasks.md` 勾选 + 逐条验收结论 + 提交推送 |

**归档谁说了算**：能上手试出效果的（机器人怎么回、图出成什么样），你跑一遍说行才归档。改的全是仓库里的字和清单，Agent 自己收尾，不来烦你。

---

## 📂 目录结构

一堆文件夹看着晕，其实你只需要认三个地方：`openspec/` 是心脏，`agents/` 是说明书，`Project/` 是十个子项目各自的地盘。其余的自己会转。

```
AllAgentBASE/
├── AGENTS.md            # 所有规矩都在这，Agent 开工必读
├── README.md            # 你现在看的这份
├── agents/              # 两个角色各自的手册
│   ├── 规划.md          # 怎么把话写清楚
│   ├── 开发.md          # 怎么做、怎么自己试
│   ├── 推送排错.md      # 传不上去的时候看这个
│   └── 本机环境.md      # 路径对不上时看这个
├── .agents/skills/      # openspec init 放的六个干活技能，别手改
├── openspec/            # 规格和改动，核心就这一个文件夹
│   ├── specs/           # 已经能做到的，按能力分文件夹
│   └── changes/
│       ├── <正在做的>/  # 一次改动一个文件夹
│       └── archive/     # 做过的，合并完就搬进来
├── Project/             # 10 个子项目，每个自己一套 README + openspec
├── skill/               # 10 个技能包，Agent 的工具箱
├── Guide/               # 图文指南
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

## 📁 一次改动长什么样

每次改动都单独装在一个文件夹里。拿 2026-10-28 那次「把测试并进开发」举例：

```
openspec/changes/archive/2026-10-28-fold-testing-into-development/
├── .openspec.yaml          这个文件夹的身份证，建的时候自动有
├── proposal.md             为什么改
├── specs/交接规矩/spec.md   改成什么样，一条条带场景
├── design.md               怎么做、为什么不用另一种（简单改动可以没有）
└── tasks.md                分几步，做完打勾，末尾是验收结论
```

能力那个文件夹名用的是中文（`交接规矩`）。官方模板建议用英文短横线（`hand-over-rules`），我们图的是你一眼看得懂，校验也不挑这个。

| 文件 | 装什么 | 谁看 |
|---|---|---|
| `proposal.md` | 为什么改。那次写的是「他从来不用测试 Agent，测试这一棒一直空转」 | **你看** |
| `specs/…/spec.md` | 改成什么样。每条都写「什么情况下，系统必须怎么做」，配一条能实际试的场景 | **你看** |
| `design.md` | 怎么做、为什么不用另一种做法、有什么风险。**改得简单就没这个文件** | Agent 自己用 |
| `tasks.md` | 分几步、做完打勾，末尾一行行实测记录 | **你最后看这里** |

验收结论长这样，一行一条：

```
场景名 → 跑了什么 → 实际结果 → 通过 / 失败 / 未测
```

只写「通过」两个字、或者对不上任何场景的，直接打回。这条写进红线了。

归档之后，改动会合并进 `openspec/specs/`，变成「现在已经能做到什么」。以后谁接手，只看 `specs/` 就知道项目能干什么，不用翻历史。

---

## ⌨️ 常用命令

日常真的只用得上这几条。

| 想干什么 | 敲这个 |
|---|---|
| 第一次建规格目录 | `openspec init --tools agents --language zh-CN` |
| 立一个新的改动 | `openspec new change add-你的功能名` |
| 看这改动还缺哪个文件 | `openspec status --change add-你的功能名` |
| 让 Agent 照模板写某一件 | `openspec instructions proposal --change add-你的功能名` |
| 交出去前查一遍 | `openspec validate add-你的功能名 --strict` |
| 一次查全仓 | `openspec validate --all --strict` |
| 还有哪些改动没做完 | `openspec list` |
| 做完了搬进档案柜 | `openspec archive add-你的功能名 -y` |
| 升级完 CLI 刷新技能 | `openspec update` |

几句要提醒的：

- **`--strict` 别省**。不加它，格式写歪了也只提示一句就放过；加了才算真的过。
- `proposal` 那个位置可以换成 `specs`、`tasks`、`design`，写哪件就填哪件。
- 纯文档、纯配置的改动没有规格要合并，归档时加 `--skip-specs`。
- 那六个技能不会自己更新。CLI 升级过就跑一次 `openspec update`，或者把 init 重跑一遍（重跑是安全的，只刷技能）。
- 命令提示不存在，就是路径没配好，看 `agents/本机环境.md`。
- 忘了怎么用就 `openspec --help`，想看某条再加一次 `--help`。

---

## 📦 子项目

| 子项目 | 做什么 | 目录 |
|---|---|---|
| ALLBot部署 | AstrBot QQ 机器人「丛雨」 | `Project/ALLBot部署/` |
| ALLSkill | 外部技能的调研、评估与引进 | `Project/ALLSkill/` |
| 全惠惠平面设计 | 品牌日常平面产出与文案 | `Project/全惠惠平面设计/` |
| 全惠惠视频制作 | 会议快剪、记录、片尾与宣传片 | `Project/全惠惠视频制作/` |
| distilly | 蒸馏自己，生成个人技能包 | `Project/distilly/` |
| 万有引力 | 微信聊天记录导出与长期保存（只做微信） | `Project/万有引力/` |
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
| `AGENTS.md` | 干活规矩、skill 路由 | 规划 Agent |
| `agents/*.md` | 单个角色的开工清单与红线 | 规划 Agent |
| `openspec/specs/` | 已经实现的行为，带场景 | 开发 Agent 写，规划 Agent 审 |
| `openspec/changes/` | 正在做的改动 | 谁立项谁维护 |
| `openspec/changes/archive/` | 做过的改动，只增不改 | 自动归档 |

一条硬规矩：**同一个事实只写一处**。行为要求写进 specs，README 只留指向，两边说法不一致时以 specs 为准。

你真正要看的只有两处：立项时那张清单（`specs/` 里那些「什么情况下会怎样」），和收工前 `tasks.md` 末尾的实测记录。中间过程不用盯。

---

## 🛡️ 干活规矩

1. **没有 change 不动手**。三种例外，从上到下越来越轻：
   - 错别字、失效链接：直接改，提交信息写清楚
   - 纯文档、纯配置、纯重构：还是建 change，但标 `skip_specs: true`，不用编规格
   - 这个仓库自己的规矩和文档：不建 change，答清「为什么改 / 改了什么 / 怎么验证 / 归档到哪」四句就行
2. **开工先读** AGENTS.md，再按角色读 `agents/` 里自己那份
3. **实现前先看提案和规格**，只盯 tasks 不看规格，等于照着清单瞎写
4. **逐路径 `git add`**，绝不用 `git add .`
5. **推送自己搞定**，冲突自己解，不把操作甩给用户
6. **不传秘密**，密钥、账号、本机路径一律不入库
7. **做完要归档**，没归档的 change 等于没做完

---

## ❓ 常见问题

**Q：为什么不设变更日志文件了？**
一个 change 归档后，为什么改、改成什么样、怎么做的、分几步，四件都在目录里，比流水账详细。零碎改动看 git 提交信息，翻旧账用 git log。

**Q：多个 Agent 能同时干活吗？**
能，但避免同时改同一个文件。接力顺序是规划 → 开发。测试并进开发了，自己做的活自己验。

**Q：规格和 README 有什么区别？**
README 写给人看，讲这是什么、怎么用。规格写给执行者看，讲系统必须表现出什么行为，带可以逐条验证的场景。

**Q：没验能直接归档吗？**
不能。归档前要过 `openspec validate --strict`，每个场景还要有一条对应的实测记录，只写「通过」两个字不算。

**Q：为什么有的改动没有 `design.md`？**
官方定的规矩是「这次改得复杂才写」。一句话能说清怎么改的，写它就是凑字数。

**Q：能力名为什么是中文？**
官方模板建议英文短横线（`hand-over-rules`），我们这边写中文（`交接规矩`），因为你要一眼看懂。校验两种都认。

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
