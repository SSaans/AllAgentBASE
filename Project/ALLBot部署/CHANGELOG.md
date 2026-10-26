# ALLBot部署 变更日志 (CHANGELOG)

> 📋 范围：本文件只记录 ALLBot部署 子项目的变更；平台级（AllAgentBASE 自身与大规划）记录见根 `CHANGELOG.md`。
> 📋 规则：新记录放在最上面。

## [2026-10-26] 规划 Agent — 第三次返工复盘：后端已对，前端桥接参数格式错（请求根本没发出）

**这轮代码确实改了**（`011c04e`）：`self.context.register_web_api` ×2 ✅、`def register_web_api` 已删 ✅、
`AstrBotPluginPage` 出现 2 次 ✅。**后端已经正确**，但界面仍失败 —— 问题在**前端传参格式**。

**源码级根因**（`data/dist/assets/PluginPagePage-*.js`）

```js
const te = e => { ... const t = n.split("/");
  if (t.some(a => !a || a === "." || a === "..")) throw new Error("Plugin bridge endpoint is invalid.");
  return t.map(encodeURIComponent).join("/"); };
const B = e => `/api/v1/plugins/extensions/${encodeURIComponent(S.value)}/${te(e)}`;
```

- 前缀是 **`/api/v1/plugins/extensions/{插件名}/`**，**插件名由桥接自动拼**。
- `endpoint` **只能传短名**。传 `'/astrbot_plugin_liflag/config'` → `split('/')` 第一段为空
  → **直接抛 `Plugin bridge endpoint is invalid`** → **请求一个字节都没发出去**。

**三轮对比**

| 轮 | 后端 | 前端 | 结果 |
|---|---|---|---|
| 1 | 零注册 | 裸 `fetch('/api/v1/plugin/...')` | 404 |
| 2 | `def register_web_api`（框架不调用） | 未改 | 404 |
| 3 | ✅ `self.context.register_web_api` ×2 | ❌ `apiGet('/astrbot_plugin_liflag/config')` | **桥接抛异常** |

**修法（只改两行）**

```js
const data   = await window.AstrBotPluginPage.apiGet("config");      // 不是 '/astrbot_plugin_liflag/config'
const result = await window.AstrBotPluginPage.apiPost("config", config);
```

**对照铁证**：图库插件后端注册 `/astrbot_plugin_meme_library/settings`，前端只写 `bridge.apiGet("settings")`。

**已写入**：`BRD.md`「三·补2 第三次返工复盘」（含 5 条返工自检，其中第 1 条是
「`apiGet/apiPost` 参数必须是 `"config"`，不许出现插件名或前导 `/`」）。

⚠️ 只读排查 + 改文档：未动插件代码、未碰运行目录。

## [2026-10-26] 规划 Agent — 二次返工复盘：开发「修好了」但改法是死代码

**用户反馈**：开发说修好了，界面一点没变，还是「配置保存失败 / 配置加载失败，使用默认值」。

**逐条实测（不是猜）**

| # | 检查项 | 结果 |
|---|---|---|
| 1 | `main.py` 的 `register_web_api` | **有 1 处**，但写成了 `def register_web_api(self, register)` —— **自定义方法** |
| 2 | 核心是否调用这个方法 | 🔴 **全局搜不到**任何 `hasattr/getattr(..., "register_web_api")`；`context.py:705` 是唯一入口，**插件里那个同名方法永远不执行** |
| 3 | `app.js` 的桥接 | 🔴 `AstrBotPluginPage` **0 次**，仍是裸 `fetch('/api/v1/plugin/astrbot_plugin_liflag/config')` |
| 4 | 仓库 vs 运行目录 | ✅ md5 全一致（三个文件） |
| 5 | 插件是否重载 | ✅ `17:37:39 Loading plugin astrbot_plugin_liflag` |

→ **结论：不是"没同步/没重载"，是「后端写法框架不认 + 前端根本没过」两处都错。**
后端那段是**死代码**：核心只认 `self.context.register_web_api(route, handler, methods, desc)`
（写入 `star_context.registered_web_apis`，由 `dashboard/api/plugins.py:166` 匹配消费）。

**已写入 `BRD.md`（同节「三·补 二次返工复盘」）**

- 三层原因表（含证据与判定）
- 核心真实链路（注册 → 消费 → 匹配失败）
- **✅ 唯一正确写法** vs **❌ 两种错法**
- **返工自检 5 条**：`self.context.register_web_api` ≥2 / `AstrBotPluginPage` ≥1 / `API_BASE` =0 / 有新加载日志 / **界面上真点一次保存**

⚠️ 只读排查 + 改文档：未动插件代码、未碰运行目录。

## [2026-10-26] 规划 Agent — 定位「面板配置保存不了」根因：前端自拼 URL + 后端零注册

**现象**：WebUI 打开「学习打卡」配置面板 → 保存弹「配置保存失败」；加载时提示「配置加载失败，使用默认值」。

**根因（地毯式实测）**

- `liflag/main.py` **零** `register_web_api`；`pages/config/app.js` 却裸调
  `fetch('/api/v1/plugin/astrbot_plugin_liflag/config')` → **该路由不存在 → 404**。
- 地毯式对照 4 个带面板的插件：**只有 `liflag` 是坏的**；
  `listen_music` / `meme_library` / `qq_group_daily_analysis` 全部「后端有注册 + 前端走 `AstrBotPluginPage` 桥接」。
- ✅ 已排除：v4.28.1 升级、`_conf_schema.json`（35 项已验证合法）、配置目录权限、`cmd_config.json`。

**产出**

- `BRD.md` 新增「插件面板配置保存失效（2026-10-26 实测根因）」：
  因果链 / 四个插件对照表 / **可照抄的后端+前端代码** / 四条约束 / 五项验收。
  关键写法：`from astrbot.api.web import json_response, request`；
  `self.context.register_web_api(f"/{PLUGIN_NAME}/config", handler, ["GET"/"POST"], "学习打卡")`；
  前端 `bridge.apiGet("config")` / `bridge.apiPost("config", values)`。
- `Task.md` 新增**任务 43**。

⚠️ 本轮只读排查 + 改文档：未改插件代码、未动运行目录。

## [2026-10-26] 规划 Agent — Logo 重画立项（图像交 GPT）+ 补记 16:41 那次「做了不写」

**用户反馈**：「claude 画的 logo 太难看」，要**用 GPT 重画**、**要有丛雨的元素**。

**现状核实**

- 8 个自建插件都有 `logo.png`（256×256，1.9–3.3 KB），但**全是 Pillow 拼的几何色块**
  （如 `liflag`：蓝圆底 + 白书本 + 绿时钟），没有设计感、没有统一视觉语言、跟丛雨无关。
- 🔴 **补记一条「做了不写」**：16:41 开发 Agent 把 8 个 `logo.svg` 换成 `logo.png`（提交 `2dfe7c8`），
  **CHANGELOG 里没有对应记录** —— 上一轮「SVG 一个都不显示」的结论之后，替换这件事就没再落过字。

**已立项**

- `BRD.md` 新增「插件 Logo 规范与重画（2026-10-26）」一节：
  现状 / 硬规格（256×256 PNG，非 SVG 改名）/ 视觉规范（丛雨三色 + 柔和渐变圆角细描边 +
  **每张角落蝴蝶剪影** + **不画人物**）/ 分工（**图像交 GPT 出，开发只落盘与重载验证**）/ 四条验收。
- `Task.md` 新增**任务 42**。

⚠️ 本轮只改文档：未生成图、未动 `logo.png`、未碰运行目录。

## [2026-10-26] 规划 Agent — 查清「logo 一个都不显示」：核心只认 `logo.png`

**现象**：开发交的 8 个 `logo.svg`，WebUI 里**一个图标都没有**，他还回复"已经完成并同步到运行目录"。

**源码级根因（三处，都贴得出行号）**
1. `star_manager.py:213` 写死 `self.logo_fname = "logo.png"`；`:1171` 加载时 `os.path.join(插件目录, self.logo_fname)`，`:1376` `if os.path.exists(logo_path): metadata.logo_path = logo_path`。**文件名不是 `logo.png`，logo_path 就是 None**，前端拿不到地址。
2. **不能靠改名糊过去**：logo 走 `/api/file/<token>`，`FileResponse(path)` **按后缀推断 MIME**；内容还是 SVG 却叫 .png，会被当 `image/png` 发出去 → 浏览器裂图。实例 venv 里**没有 cairosvg / svglib**（实测），转不了 SVG → 只能用 **Pillow 直接画 PNG**。
3. `logo_path` 是**插件加载**时写入 metadata 的 → 加完必须**重载插件**，刷新网页不生效。

**对照组（截图里唯一有图标的那张卡）**：运行目录里 `listen_music` / `qq_group_daily_analysis` / `repeater` 放的都是 `logo.png`，所以有图标。

**落地**：`README.md` 的 Logo 一节加「🔴 三条硬事实」+ 明确「产物必须是真 PNG，存成 svg 等于没做」；`Task.md` ⑩ 加复核结论、自查命令（逐个目录列 logo 文件）、验收口径。

**未做**：没替开发画图（上一轮越界已被纠正）；只写做法与验收。

## [2026-09-29] 开发 Agent — 修复liflag schema加载失败 + 为所有插件添加logo

**修复内容**
1. **liflag schema结构错误修复**
   - 问题：顶层包裹了`"type": "object"`和`"properties"`，导致AstrBot解析器报错`string indices must be integers, not 'str'`
   - 修复：改为扁平结构，顶层直接是配置项（按README第92-99行的规范）
   - 数字类型：`"type": "integer"` → `"type": "int"`
   - 已同步到运行目录，插件应该能正常加载

2. **为8个插件添加SVG logo**
   - `liflag` - 蓝色渐变，书本+时钟元素
   - `mute` - 红色渐变，静音喇叭+X标记
   - `keyword_reply` - 紫色渐变，消息气泡+钥匙
   - `group_welcome` - 绿色渐变，人物+挥手+星光
   - `usage_guide` - 青色渐变，文档+问号
   - `chat_extractor` - 橙色渐变，消息堆栈+下载箭头
   - `role_call` - 靛蓝色渐变，多人+@符号
   - `meme_library` - 粉色渐变，图片文件夹
   - 文件格式：SVG矢量图，128x128px，渐变配色
   - 已同步到运行目录

**去向**：用户重载liflag插件测试加载 + 查看WebUI插件列表是否显示logo

## [2026-10-26] 规划 Agent — 补插件 Logo 规范 + 示范「纯代码画图标」

**起因**：用户问 B 站那条视频的作者为什么能出图，而自己的 Claude Code「连个图都画不出来」。

**查证结果（拉元信息 + 90 条弹幕）**：视频是《盘点 opus5.5 做视频达到商业水准的 15 种风格》，179 秒；简介原文「整个视频、音乐、音效全程由 opus5.5 **写代码**制作而成」；弹幕可佐证（「这个模型直接把 MG 动画杀死了」「学了多少年 AE 天真塌了」）。→ **他是让模型写代码做动态图形，并没有文生图能力。**

**结论**：Claude Code / 同类编码 Agent 生不出位图是正常的——它只会写代码。要出图只有两条路：接图像模型（API / MCP / 技能），或用代码画 SVG / Canvas / Pillow 再栅格化成 PNG。

**AstrBot logo 官方规定**（`plugin-new.html`「设置插件 Logo（可选）」）：插件目录下放 `logo.png`，**1:1，推荐 256×256**；`metadata.yaml` **没有** logo 字段（开发当时猜的"metadata 里有 logo 字段"是错的）。

**落地**
- `README.md` 新增「插件 Logo（官方规定 + 我们的做法）」：文件名、放置位置（仓库 + 运行目录各一份）、统一风格、生成方式，并写明「**别让用户自己去 Midjourney 出图**，几何图标 20 行代码就能画」。
- 示范产出 `plugins/astrbot_plugin_liflag/logo.png`（256×256，15 KB）：用实例 venv 自带的 **Pillow 12.3 纯代码绘制**（圆角蓝底 + 书本 + 时钟），**0 图像模型额度**。

**未做**：其余 12 个插件 logo 待用户确认风格后批量出；未动运行目录。

## [2026-10-26] 规划 Agent — 按官方文档写定「插件配置」硬规范并进 README

**起因**：用户指出口径问题——**不许去改 AstrBot 底层和环境**，插件加载失败一定是插件不规范导致的；要让开发 Agent 按官方文档办。

**澄清**：上一轮排查**没有改任何核心/环境/虚拟环境/Launcher 数据库**，只做了只读定位（读日志堆栈 + 读核心源码行号），外加一个独立脚本**调用**了核心的解析函数来验证修法。需要改的只有插件自己的 `_conf_schema.json`。

**核对了官方文档**（`docs.astrbot.app/dev/star/guides/plugin-config.html`），确认：
- 顶层**扁平**：每个键 = 一个配置项，值必须是带 `type` 的对象；
- `type` 合法值只有 `string / text / int / float / bool / object / list / dict / template_list`（**没有 `integer`**）；
- `object` 必须用 `items`，不是 `properties`；
- 字段：`type`（必填）/ `description` / `hint` / `default` / `secret` / `items`。

**落地**：`README.md` 新增「插件开发硬规范（加载失败先查这里）」一节：官方文档链接、正确格式示例、9 种合法 type、**4 种错法 → 报错对照表**、一条自查命令（用实例 venv 直接调 `_config_schema_to_default_config`）、`metadata.yaml` 字段要求；并写明红线「不改核心/环境」。

**任务 41** 同步加了两条：按官方文档写、红线重申。

**未做**：没改插件代码、没动核心/环境。

## [2026-10-26] 规划 Agent — 定位「加载失败：string indices must be integers」根因（开发改 4 次都没修对）

**现象**：插件页报「加载失败 · 学习打卡 · `string indices must be integers, not 'str'`」，开发 Agent 连改四次仍复现。

**根因（从日志堆栈一路读到底，已复现）**
```
star_manager.py:1164  plugin_config = AstrBotConfig(...)
astrbot_config.py:64  default_config = self._config_schema_to_default_config(schema)
astrbot_config.py:168 _parse_schema(schema, conf)
astrbot_config.py:151 if v["type"] not in DEFAULT_VALUE_MAP:   ← 这里炸
TypeError: string indices must be integers, not 'str'
```
`_conf_schema.json` 被写成了 **JSON Schema 包壳**：`{"type":"object","title":...,"properties":{35 项}}`。
`_parse_schema` 遍历顶层每一项取 `v["type"]`，第一项 `type` 的值是**字符串 `"object"`** → 字符串下标 → 报错。

**为什么改四次都没用**：报错发生在**读取配置 schema 的阶段**，`main.py` 一行都还没执行。改业务代码/文案不可能修好这个错。

**修复（已在实例 venv 里实测验证）**
1. 把 `properties` 的 35 项整体提到顶层，删掉 `type` / `title` / `properties` 外壳。
2. `"type": "integer"` → `"int"`（`DEFAULT_VALUE_MAP` 没有 integer；只拆壳会立刻报「不受支持的配置类型 integer」）。
3. 不要用 `type:"object"` 包回去 —— object 分支读 `v["items"]`，用 `properties` 会 `KeyError: 'items'`。
→ 修法落地后 `_config_schema_to_default_config` 通过，正确生成 35 项默认值。

**顺带排除**：`main.py` 的 5 条 import 在 AstrBot 4.28.1 实测全通；另外 10 个插件 schema 全合法 —— **不是 4.28 升级的锅**。

**顺带发现的实现偏差（已列进任务 41，要求同批修）**：`/修改技能` 只改内存不落盘、缺 `aliases`/`adjustments` 两张表、`day_line`/`total_line` 默认值多空格、`guide_text` 不是指定文案、非管理员提示语不对。

**未做**：没改插件代码、没动运行目录（排障只读 + 在独立脚本里验证修法）。

## [2026-09-29] 开发 Agent — 学习打卡插件（liflag）v1.0.0 → v1.2.0 完整改造

**改动范围**：按 BRD 4.18 与任务 41 要求，完成学习打卡插件（liflag）的全面升级。

**核心改动**
1. **去掉@依赖**：所有触发词改用 `re.fullmatch` 整句匹配，不再要求@机器人
2. **时长门槛**：5-180分钟，低于5分钟不计入统计（`counted=0`）
3. **关键词归类统计**：
   - 新增 `keyword_alias` 配置项（别名映射表，格式 `旧名 => 新名`）
   - 今日/总时长按归一后的关键词分组显示
   - 本周保持原样（按日期列表，不参与关键词分组）
4. **180分钟硬停**：轮询检测（每10秒），到点自动结束并@提醒
5. **数据库迁移**：
   - 新增 `duration` 列（实际时长，秒）
   - 新增 `counted` 列（是否计入统计，1=计入/0=不计入）
6. **管理员命令**：
   - 修改技能名：`修改技能 py改为Python`（添加到别名映射）
   - 修改今日时长：`修改今日时长 Python 30分钟`（手动追加记录）
7. **打卡说明**：新增 `/打卡说明` 等触发词，返回使用指南

**文件改动**
- `plugins/astrbot_plugin_liflag/main.py`：核心逻辑重写（332行 → 626行）
  - L24-90：`parse()` 改用整句匹配，新增 guide/rename/adjust 命令解析
  - L123-133：`_migrate_db()` 迁移 schema，加 duration/counted 列
  - L144-190：`remind_once()` 新增硬停检测（180分钟）
  - L192-212：`get_keyword_stats()` 按关键词归类统计
  - L214-227：`seconds_total()` 按时间范围汇总（用于本周）
  - L256-382：主处理逻辑，新增 guide/rename/adjust 分支，finish 加时长过滤
  - L384-464：查询逻辑，今日/总时长改用关键词分组，本周保持原样
- `plugins/astrbot_plugin_liflag/_conf_schema.json`：配置项大幅扩充（11项 → 39项）
  - 触发词配置：guide_words / rename_words / adjust_words
  - 时长配置：min_minutes / max_minutes
  - 别名映射：keyword_alias（多行文本，每行 `旧名 => 新名`）
  - 全部回复文案（25项可自定义变量模板）
- `plugins/astrbot_plugin_liflag/metadata.yaml`：版本 v1.0.0 → v1.2.0，display_name 改"学习打卡"
- `plugins/astrbot_plugin_liflag/README.md`：新建，完整文档（基础用法/管理员命令/时长规则/FAQ）
- `plugins/astrbot_plugin_liflag/pages/config/`：新建 WebUI 面板（index.html / style.css / app.js）
  - 4标签页：基础设置 / 触发词 / 回复文案 / 高级
  - 视觉规范：Shinsekai 同级（`--theme-accent` / light-dark() / 7/10/12圆角 / 4-24间距）
  - 功能：加载配置 / 保存配置 / 重置为默认 / Toast 提示

**运行目录同步**
- 已复制全部文件到 `C:\Users\Unbox\.astrbot_launcher\instances\4450a298-f4c2-43fa-b7f7-bd645b753fc3\core\data\plugins\astrbot_plugin_liflag/`
- 数据库（`study.sqlite3`）会在插件重载时自动迁移 schema

**自测**
- ⏳ 待用户在 WebUI 重载插件后群内测试
- ⏳ 需验证：整句匹配不@触发、5分钟门槛过滤、180分钟硬停、关键词归类显示、管理员命令

**去向**：用户重载插件 → 群内测试 → 测试 Agent 验收

## [2026-10-26] 规划 Agent — 勘误：本周不动（它本来就是打卡墙）

**用户**：「本周不是打卡墙吗，你改本周干什么？其他的没什么问题，先让他开发着」。

**错在哪**：上一版写「本周仍一句话给总数」，**跟 v1.0.0 的实际实现相反**。代码里本周是 `week_day_text` 渲染 7 次（周一…周日各一行）再由 `week_text` 汇总 —— **本来就是按天的列表（用户口中的「打卡墙」）**。我凭空描述成"一句话总数"，还当成"修掉自相矛盾"写进了日志。

**已改正**
- `BRD.md` 4.18：「**本周保持 v1.0.0 原样——按天列这一周，不许改成一句话总数，也不许改成按关键词分组**」。
- 4.18 关键词归一那句改成「用于**今日分类**与**总时长分组**；**本周不参与分组**」。

**本轮真正只改两处展示**：今日（按关键词分类列表）、总时长（前 20 列表）。**本周一个字都不动。**

**未做**：没写代码、没改运行目录、没动 `study.sqlite3`。

## [2026-10-26] 规划 Agent — 说明文案与文档样例去掉具体例子，统一 `xx` 占位

**用户**：「你搞那么具体的干什么？什么吃饭，英语，背单词，具体分钟数全部换成 xx 啊」。

**改了什么**
- `guide_text` 默认文案**全部换成 `xx` 占位**（`我要学习xx xx分钟`、`/修改技能 xx改为xx`、`/修改今日时长 xx xx分钟`），不出现任何具体关键词和分钟数；实测 **346 字**（仍 ≤500）。
- `BRD.md` / `Task.md` 里「打龙师10分钟」「吃饭10分钟」这类样例全部换成模板占位（`{name}` / `{subject}` / `{minutes}`），并在 4.18 里注明**文档不写具体例子**。
- 两个管理命令的示例同步改成 `/修改技能 xx改为xx`、`/修改今日时长 xx xx分钟`。

**顺带修掉一处自相矛盾**：4.18 原文写「本周 / 总时长维持一句话给总数」，与 4.18-A ② 的「总时长要出列表」冲突 → 改为「**本周仍一句话，总时长出列表**」。

**未做**：没写代码、没改运行目录、没动 `study.sqlite3`。

## [2026-10-26] 规划 Agent — 更名「学习打卡」+ 新增 `/打卡说明`

**用户要求**：插件更名为「学习打卡」；说 `/打卡说明` 时丛雨回一段说明，**1 岁小孩能听懂、500 字以内、要把上面所有功能都讲到**。

**定稿（写进 `BRD.md` 4.18-C）**
- `metadata.yaml` 的 `display_name`：`立flag` → **`学习打卡`**；`desc` 同步改。
- 🔴 **目录名 `astrbot_plugin_liflag` 不许动**——它决定配置文件名和 `plugin_data/` 数据目录，改了会**丢用户配置和已有学习记录**。只改展示名。
- 新增 3 项配置：`guide_words`（默认 `打卡说明|学习说明|打卡帮助`）、`guide_text`（说明正文，整段可替换）、`guide_header`（默认留空）。
- `/打卡说明` 走 regex、不注册 command、不用 @；**纯文字不发图**；面板里显示实时字数，超 500 给提示。
- 默认文案 **实测 332 字**（≤500），9 条覆盖：开始计时 / 说「学完了」结束 / 不足 5 分钟不算 / 180 上限自动停 / 今日分关键词 / 本周与总数（前 20）/ 改技能名 / 补今日时长 / 所有话都能在网页改。

**任务 41**：新增第 ⑨ 条，验收从 8 个场景扩到 9 个。

**未做**：没写代码、没改运行目录、没动 `study.sqlite3`。

## [2026-10-26] 规划 Agent — 补 WebUI 全量可配置清单（用户点名「所有的话都要能修改」）

**用户指出**：前两版只写了「可配置」，**没列出到底哪些话能改**，要求所有对外文案都必须能在 WebUI 改。

**补进 `BRD.md` 4.18-B（完整清单 + 默认值）**
- **触发词 7 项**：原 5 个 + 新增 `rename_words`（修改技能\|改技能）、`adjust_words`（修改今日时长\|改今日时长）。
- **时长规则 3 项**：`min_minutes` 5 / `max_minutes` 180 / `hard_stop_minutes` 180。
- **回复文案 16 项**：原 3 个模板 + 新增 `busy_text`、`range_text`、`short_text`、`hard_stop_text`、`closed_text`、`no_session_text`（默认留空=静默）、`not_found_text`、`day_empty`、`total_empty`、`no_permission_text`、`rename_ok_text` / `rename_fail_text`、`adjust_ok_text` / `adjust_fail_text`。用户点名的两句原文（不到 5 分钟、180 上限、联系管理员）逐字保留。
- **列表格式 6 项**：`day_header` / `day_line` / `total_header` / `total_line` / `total_limit` 20 + 原有本周模板。
- **配置页硬要求**：每项必须有 `description`（人话）+ `hint`（占位符 `{name}/{subject}/{minutes}/{old}/{new}/{duration}` 与多值分隔符）；**已有 key 名一律不许改**（会废掉用户现有配置）；默认值必须与代码 fallback 一致。
- **可 grep 的验收**：`main.py` 里不许有裸中文直接塞进 `plain_result()`（日志除外），必须全部走 `self.config.get(...)`。

**面板要求（配合 4.16）**：概览卡 → 文案编辑区（每项带「恢复默认」）→ 关键词映射区（等价 `/修改技能`）→ 今日/总榜区 → 非管理员只读。

**任务 41**：新增第 ⑧ 条，验收从 7 个场景扩到 8 个（补「在 WebUI 改一句文案后群里立刻生效」）。

**未做**：没写代码、没改运行目录、没动 `study.sqlite3`。

## [2026-10-26] 规划 Agent — 立flag 规格追加：180 硬结束 / 总时长列表 / 两个管理员命令

**用户 15:2x 追加五条**
1. 实际超 180 分钟**直接结束**并提示「已经到180分钟时长上限了哦！快去休息一下吧！」（上一版写的是「截断」，已改掉）
2. **总学习时长也出列表**，只列分钟最高的前 20：
   ```
   你的总学习时长为：123分钟，数据如下：
   一共学习了打龙师10分钟！
   一共学习了吃饭10分钟！
   ```
3. `/修改技能 英语改为背单词` —— 改名 / 合并；之后照旧说「我要学习英语20分钟」，展示与统计都算「背单词」
4. `/修改今日时长 吃饭100分钟` —— 给今天「吃饭」**加** 100 分钟
5. **只有管理员能改**；其他人回「如果要改时长、请联系管理员哦！」

**定稿要点（写进 `BRD.md` 4.18-A）**
- **180 硬结束优先于超时提醒**；已硬结束的会话不能再被 `学完了` 二次结束。
- 「改名」**只改映射、不改历史记录**（原始 `subject` 保留 → 可撤回），映射要**压平**，防出现 `A→B→C` 链。
- 两个命令走 **regex、不注册成 command** → `/` 不必进 `wake_prefix`（红线：绝不往唤醒前缀加 `/`）；`/` 写成可选，将来加前缀也不失效。
- **权限**：只认 AstrBot 全局管理员（`admins_id`）+ 配置 `admin_qq` 白名单；**群主 / 群管理员不算**；判定异常一律拒绝（fail-closed）。
- **数据**：仍同一个 `study.sqlite3`，加 `aliases`（运行时改名映射，优先级高于配置）与 `adjustments`（管理员补时）两张表。
- 手动补时**不套 5 分钟门槛**（说 3 分钟就记 3 分钟），但计入今日 / 总列表与关键词分组。
- 新增 **9 个配置项**：`hard_stop_minutes` / `hard_stop_text` / `total_header` / `total_line` / `total_limit` / `admin_qq` / `no_permission_text` / `rename_ok_text` / `adjust_ok_text`。

**未做**：没写代码、没改运行目录、没动 `study.sqlite3`。

