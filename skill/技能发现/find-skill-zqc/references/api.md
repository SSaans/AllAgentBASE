# API 与安装参考

本 Skill 统一走 `scripts/zqc_find_cli.py`，下面是底层接口与手工操作方式，供排查/扩展用。

## 数据线 1 · SkillHub 发现（API Base `https://api.skillhub.cn`，无需鉴权）

查找统一走 `GET /api/skills`（关键词为**分词搜索**）；**不要**用 `/api/v1/search`。

| 参数 | 说明 | 默认 |
|------|------|------|
| `keyword` | 关键词，分词搜索（标题/描述等命中即返回） | - |
| `category` | 一级标签 key（见 categories.md） | - |
| `source` | 来源（`community`/`enterprise`/`official`/`clawhub`） | - |
| `labels` | 属性标签过滤，`key:value` 逗号分隔，否定用 `key:!value` | - |
| `sortBy` | `updated_at`/`downloads`/`stars`/`installs`/`score` | `updated_at` |
| `order` | `asc`/`desc` | `desc` |
| `page` / `pageSize` | 分页（pageSize 1~100） | `1` / `20` |

返回：`{"code":0,"message":"success","data":{"total":<n>,"skills":[ {...} ]}}`。每项关键字段：
`slug`、`name`、`description`/`description_zh`、`category`、`subCategories`（二级，仅展示）、
`tags`、`labels`（如 `requires_api_key`、`pricing_type`）、`downloads`/`stars`/`installs`、
`ownerName`、`version`、`source`。

> 主页 URL 由 slug 拼接：`https://skillhub.cn/skills/<slug>`。不要用接口返回的 `homepage`
> 字段（那是 `api.skillhub.cn/<owner>/<slug>` 格式）。

### 其他接口

```bash
# 单个 Skill 详情（含 securityReports 官方安全报告）
curl -s "https://api.skillhub.cn/api/v1/skills/<slug>"

# 一级标签 / 二级类目实时列表
curl -s "https://api.skillhub.cn/api/v1/categories"
curl -s "https://api.skillhub.cn/api/v1/subcategories?parent=<一级key>"
```

## 数据线 2 · 装前查安全层（公开分片，零 API Key）

| 数据 | URL（`ZQC_DATA_URL` 可覆盖根，默认 `https://s.zhuangqiancha.com/`） | 内容 |
|------|------|------|
| 全量目录 | `catalog.json` | 11 万+ 工具，列式（cols+rows），含 `slug`/`name`/`grade`/`author`/`finding_count`/`top_severity`/`downloads`/`install_count`，**分类与 SkillHub 12 分类一致** |
| 工具详情 | `tools/{shard:03d}.json` | FNV-1a(slug)%256 落片；含评估证据、capabilities、cveFindings |
| 作者信誉 | `authors.json` | 作者工具数、红/橙/黄/绿计数 |
| 域名图谱 | `tool_domains.json` | 隐私去向（外联域名分类） |

> 详情页统一：`https://www.zhuangqiancha.com/tool/<urlencoded slug>`。装前查基于公开代码与
> 声明独立评估，结论不构成担保。

## CLI 全命令

```bash
# 多关键词搜索 + 档位标注 + 安全优先排序（推荐入口）
python3 scripts/zqc_find_cli.py find "<关键词>" [--kw "<同义词>"]* [--category <key>]
                                           [--limit 8] [--page-size 5] [--safe-only] [--free-only]

# 单个候选的安全详情（证据 / 能力 / 隐私去向 / 作者信誉）
python3 scripts/zqc_find_cli.py inspect "skillhub:<slug>"

# 安装（含安全闸门：🟠/🔴 需 --yes 确认）
python3 scripts/zqc_find_cli.py install "skillhub:<slug>" --dir <skills目录> [--yes]
```

环境变量：
- `ZQC_DATA_URL`：装前查数据根（默认 `https://s.zhuangqiancha.com/`）
- `ZQC_SKILLS_DIR`：install 的默认 `--dir`
- 缓存：`<TMP>/zqc_find_cache/`，TTL 1 小时

## 一键安装（用户选定后）

官方方式走 **SkillHub CLI**（详见 https://skillhub.cn/install/skillhub.md）。CLI 的 `install`
命令已内置下面步骤，无需手工执行。

### 1. 检查 / 安装 CLI

```bash
command -v skillhub && skillhub --version
```

未安装则**仅装 CLI**（沙箱限网时需以允许联网权限执行）：

```bash
curl -fsSL https://skillhub-1388575217.cos.ap-guangzhou.myqcloud.com/install/install.sh | bash -s -- --cli-only
```

> 完整安装（CLI + 默认 Skill）去掉 `-s -- --cli-only`。
> 仅纯安装某技能且 CLI 已存在时，不要询问「是否设为优先源」；只有首次安装或用户明确要求时才询问一次。

### 2. 安装技能（必须用 `--dir` 指向当前 Agent 的 skills 目录）

```bash
skillhub install <slug> --dir <skills目录>
```

不加 `--dir` 会装到 `./skills/` 不被识别。常用 Agent 的 skills 目录：

| Agent | skills 目录 |
|-------|-------------|
| Cursor | `~/.cursor/skills/` |
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/`（或项目 `.agents/skills/`） |
| Windsurf | `~/.codeium/windsurf/skills/`（或项目 `.windsurf/skills/`） |
| Gemini CLI | `~/.gemini/skills/` |
| workbuddy | `~/.workbuddy/skills/` |

- 也可用 `skillhub search <kw>` 在 CLI 内搜索。
- 安装完成后提示用户：「✅ {name} 已安装」。

> 备用（无 CLI / 仅取 zip）：下载接口 302 跳转 `GET /api/v1/download?slug=<slug>[&version=<version>]`，
> 解压到上面对应的 skills 目录。
