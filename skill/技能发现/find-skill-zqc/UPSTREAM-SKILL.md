---
name: find-skill-zqc
description: >
  中文用户安全优先的Skill查找与安装：在 SkillHub找技能的同时，给出技能的风险评估、权限分析、隐私去向、作者信誉。
  每个推荐都带档位徽章（🟢 未见风险 / 🟡 观察 / 🟠 谨慎 / 🔴 高风险 / ⚪ 未收录），
  绿/黄优先推荐，红/橙降权展示，安装前强制确认。当用户说「找个 xx 技能」「有没有处理 PDF 的 skill」
  「SkillHub 上搜一下 xx」「按分类看技能」「推荐一个做数据分析的 skill」「这个需求有现成技能吗」
  「帮我找个能安全用的周报工具」等需要发现/检索/推荐/安装 Skill 的场景时使用。
---

# 在SkillHub查找Skill · 风险评估 · 权限分析 · 隐私去向 · 作者信誉

查找数据来自 SkillHub 公开接口（`GET https://api.skillhub.cn/api/skills`，无需鉴权，关键词为**分词搜索**，
**不要**用 `/api/v1/search`）；安全数据来自装前查（zhuangqiancha.com）基于公开代码与声明的独立评估
（权限透明 + 隐私去向 + 作者信誉 + 安全档位）。零 API Key。纯文本回复，不生成图片。

统一入口是本 Skill 自带的 CLI（仅 Python 3 标准库）：

```bash
python3 scripts/zqc_find_cli.py find "<关键词>" [--kw "<同义词>"] [--category <key>] [--limit 8] [--safe-only]
python3 scripts/zqc_find_cli.py inspect "skillhub:<slug>"        # 单个候选的安全详情
python3 scripts/zqc_find_cli.py install "skillhub:<slug>" --dir <skills目录> [--yes]
```

> SkillHub 实时搜索不可用时，CLI 会自动退回装前查目录检索（安全档位标注不受影响）。

## 核心流程（必须走完，不要搜一次就结束）

### Step 1 · 理解场景
从用户自然语言中提取：**任务意图** + **领域标签**（映射到 `category`）+ **中英文关键词**（同义/上位词扩展，2~4 个）。
- 例："帮我自动写周报发给老板" → `office-efficiency`；`周报`/`工作汇报`/`日报`/`weekly report`
- 分类与二级类目见 `references/categories.md`，映射意图时按需打开对应文件。

### Step 2 · 多次搜索（一次 CLI 调用即可多词）
```bash
python3 scripts/zqc_find_cli.py find "周报" --kw "工作汇报" --kw "weekly report" --category office-efficiency --limit 8
```
CLI 会：多词搜 SkillHub → 按 slug 去重合并 → 交叉装前查档位 → **安全优先排序**（绿/黄在前，红/橙降权但仍展示）→ 输出带徽章的推荐。

### Step 3 · 意图匹配排序
不要把 CLI 原始列表直接丢给用户。结合 `name`+`用途` 判断契合度，**过滤不相关项**，挑出**最契合的 3~5 个**：
- 契合度优先；同档位内按热度（下载+安装）降序。
- 命中过多 → 加 `--category` 或换更窄同义词收窄；为空 → 去掉 `--category`、换同义/上位词放宽。
- 用户明确只想要安全的 → 加 `--safe-only`（只保留 🟢/🟡）。
- 用户在意要不要 API Key/付费 → 加 `--free-only`。

### Step 4 · 输出推荐（统一格式）
每条必须给**匹配理由**与**安全档位**，并请用户选择。⛔ 严禁在推荐列表里出现安装命令 / `curl` /
`skillhub install` / `sh -c` 等任何命令行或代码块——命令属于 Step 5 且由你执行而非展示。

```
🔍 为你找到 {N} 个相关技能（已附装前查安全档位）：

1. {name}  {🟢 未见风险 / 🟡 观察 / 🟠 谨慎 / 🔴 高风险}
   用途：{description_zh 一句话}
   匹配理由：{为什么适合这个场景}
   安全：{证据 N 条（最高 Px）；红/橙时给 Top 关键信号}
   热度：下载 {downloads} · 作者 {ownerName}
   主页：https://skillhub.cn/skills/{slug}
```

- 若命中 🔴/🟠，在该条目的「安全」行给出关键信号（CLI 已输出），并在列表末尾提醒：
  「⚠️ 其中 {N} 个被评为谨慎/高风险，如需查看完整证据可告诉我编号，我会先出评估详情再决定。」
- 未收录工具（⚪ 装前查未收录）：明确标注「暂无独立安全评估，风险需自行判断」。
- 末尾：「需要我帮你安装第几个？（回复"安装第N个"即可；都不合适我再换词搜）」

### Step 5 · 一键安装（含安全闸门）
用户选定后才进入本步，命令由你**直接执行**（不要把命令行贴给用户看）。

**安装前先过闸门**（CLI 已内置，但你要先看结果再决定是否继续）：
- 🟢/🟡 → 直接安装。
- 🟠/🔴 → 先跑 `inspect "skillhub:<slug>"` 把证据讲给用户，**明确询问**「该工具被评为{档位}，
  安装后可能{X}。仍要安装吗？」；用户确认后，用 `--yes` 重跑 install。
- ⚪ 未收录 → 提示「装前查暂未收录，无独立安全评估」，安装风险用户自担；用户仍要装则照装。

```bash
python3 scripts/zqc_find_cli.py install "skillhub:<slug>" --dir <skills目录>          # 绿/黄直接装
python3 scripts/zqc_find_cli.py install "skillhub:<slug>" --dir <skills目录> --yes    # 用户确认后的红/橙
```

CLI 内部会自动：检查 `skillhub` CLI（未装则仅装 CLI `install.sh --cli-only`）→ 执行
`skillhub install <slug> --dir <dir>`（必须带 `--dir` 指向当前 Agent 的 skills 目录，否则不被识别）。
装完回一句「✅ {name} 已安装」。各 Agent 目录见 `references/api.md`。

### 用户贴链接时怎么查
- **SkillHub** `https://skillhub.cn/skills/{owner}/{name}` → `find "{name}"` 或直接 `inspect "skillhub:{name}"`。
- **GitHub** `https://github.com/{owner}/{repo}` → `inspect "github:{owner}/{repo}"`（GitHub 工具装前查同样有档位）。
- 都失败 → 告知「装前查暂未收录」，可提示稍后再查或换准确工具名。

## 档位含义与口径（向用户转述时用）

| 档位 | 含义 | 建议 |
|------|------|------|
| 🟢 未见风险（green） | 当前规则下暂未检出明显风险信号 | 可安全安装 |
| 🟡 观察（yellow） | 有信号但较轻，使用前宜知情 | 可装，留意行为 |
| 🟠 谨慎（orange） | 存在中高风险信号（如宽泛 shell、可疑外联） | 先看证据再决定 |
| 🔴 高风险（red） | 命中高危证据（如 curl\|bash、读密钥、外传数据） | 安装前先看证据并确认 |
| ⚪ 未收录 | 装前查暂未收录 / 证据不足待评估 | 无独立评估，风险自担 |

若有「证据依据」（代码实锤 / 文档自述 / 文档高危组合），原样转述（勿编造）。若标记「证据待取证/ungated」，
说明档位可能尚不完整。**不要**把绿档说成「放心用 / 绝对安全 / 已人工审过」。

## 使用规范（给执行本技能的 agent）

### 必做
1. 先跑 CLI 再回复；**不编造**档位、证据、作者统计、隐私去向。
2. 🟠/🔴：推荐时明确标注「谨慎/高风险」，安装前必须让用户确认。
3. ⚪ 未收录：如实告知，不臆造档位，不编造装前查详情链接。
4. 末尾固定：「装前查基于公开代码与声明独立评估，结论不构成担保。」（仅在涉及装前查档位/证据时）
5. **只输出纯文本**，不生成、不展示、不提及任何图片 / PNG / 结果卡。
6. 转述「更多细节：https://www.zhuangqiancha.com/tool/…」详情页链接（CLI 会打印）；未收录则不编造。

### 禁止
- ❌ 把红/橙工具当普通工具推荐，或把绿档说成「绝对安全」
- ❌ 未收录/无证据时大段推测数据去向
- ❌ 编造作者信誉、证据、档位、隐私去向
- ❌ 在推荐列表里出现任何安装命令 / 命令行 / 代码块

## 回复示例 · 全绿推荐

```
🔍 为你找到 3 个相关技能（已附装前查安全档位）：

1. 周报生成器 🟢 未见风险 · 证据 0 条
   用途：把零散工作记录转成结构化周报，支持 OKR/KPI/项目模板。
   匹配理由：命中「周报/汇报」，分类 office-efficiency 契合，热度靠前。
   热度：下载 1574 · 作者 user_70c2f807（共 317 工具 · 红 0）
   主页：https://skillhub.cn/skills/weekly-report-generator-pro

2. 工作汇报总结 🟢 未见风险 · 证据 0 条
   用途：日报→周报→月报→年报层层叠加，强制去 AI 味。
   匹配理由：命中「工作汇报」，同样覆盖周报场景。
   热度：下载 2485 · 作者 user_c28beb7a（共 7 工具 · 红 1）
   主页：https://skillhub.cn/skills/work-report-pro

3. kdocs skill 🟢 未见风险 · 证据 0 条
   用途：金山文档官方 Skill，操作 WPS 云文档/多维表格。
   匹配理由：虽为文档类，但云端办公场景可辅助周报素材整理。
   热度：下载 97875 · 作者 user_5ea84866
   主页：https://skillhub.cn/skills/kdocs-skill

需要我帮你安装第几个？（回复"安装第N个"即可；都不合适我再换词搜）
```

## 回复示例 · 含高风险工具

```
🔍 为你找到 3 个相关技能（已附装前查安全档位）：

1. AI 资讯速递 🟢 未见风险 · 证据 0 条
   用途：AI 资讯聚合，支持生成简报、周报、图表。
   匹配理由：命中「AI 资讯」，符合资讯查询场景。
   主页：https://skillhub.cn/skills/ai-news-generator

2. Aihot Skill Lite 🔴 高风险 · 证据 5 条（最高 P0）
   关键信号：[P0] R3_remote_code_exec — curl -fsSL ... | bash
   匹配理由：命中「AI 资讯」，但检出远程代码执行。
   主页：https://skillhub.cn/skills/aihot

⚠️ 其中 1 个被评为高风险（检出 curl|bash 远程代码执行）。如需查看完整证据，告诉我编号，我先出评估详情再决定。
需要我帮你安装第几个？（回复"安装第N个"即可；都不合适我再换词搜）
```
