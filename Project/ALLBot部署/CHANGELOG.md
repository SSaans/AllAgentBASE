# ALLBot部署 变更日志 (CHANGELOG)

> 📋 范围：本文件只记录 ALLBot部署 子项目的变更；平台级（AllAgentBASE 自身与大规划）记录见根 `CHANGELOG.md`。
> 📋 规则：新记录放在最上面。

## [2026-10-27] 规划 Agent — 第五次定位：管理员命令仍全哑，他把错误「包裹」了没修掉

**用户实测（11:20–11:21）**：`修改今日时长打龙师100000分钟` / `修改今日市场打龙师10分钟` / `修改技能打龙师为滚木`
**三条全无反应**；同时 `打卡说明` 正常 → 证明差别只在**是否经过 `is_admin()`**。

**当前代码（仓库与运行目录 md5 一致，都是这份）**

```python
def is_admin(self, event):
    try:
        platform = self.context.get_using_platform()   # 方法根本不存在
        ...
    except Exception as e:
        logger.warning(f"is_admin检查失败: {e}")
        return False                                    # 于是永远 False
```

**判断：这是「把错误包起来」，不是「修好」**

- 上一版直接抛 `AttributeError`（日志有堆栈，能查）；
- 这一版加 `try/except` 吞掉，**异常照样发生**，只是变成一条 `warning`，
  然后 `is_admin` **永远返回 False** → 每条管理员命令**静默拒绝**，比之前更难查。

**唯一正确写法**：`def is_admin(self, event): return event.is_admin()`
（依据 `astr_message_event.py:268`；同项目 `astrbot_plugin_mute/main.py:323` 同写法）

**并列了三种「假修复」黑名单**：保留 `get_using_platform` 包 try／加 `hasattr` 判空／改读 `admin_qq`（配置里根本没这个键）。

`BRD.md` 新增「三·补5」；`Task.md` 任务 44 已记本次结论。
**自检两条**：`grep -c get_using_platform` 必须 0；`is_admin` 只允许一行 `return event.is_admin()`。
**必测三条**：管理员发上面三条要有回复；非管理员要回「如果要改时长、请联系管理员哦！」。

⚠️ 只改文档：未动插件代码。

## [2026-10-27] 规划 Agent — 立「加功能四件套」硬流程（开发只改后端、WebUI 一点没动）

**用户报告**：开发加了暂停/继续/放弃三个功能，**但 WebUI 完全没变** —— 用户看不见、点不到、也没说明。

**逐文件核对（`cabd9c7`）**

| 文件 | 状态 |
|---|---|
| `main.py` | ✅ 10:46 已改（is_admin + 暂停/继续/放弃 + `paused`/`paused_at`/`pause_total`） |
| `_conf_schema.json` | ✅ 10:47 已改（+12 项） |
| `pages/config/` | 🔴 **一个字节没动**（还是 10-26 15:43） |
| `README.md` | 🔴 **没更新**（还是 10-26 15:42） |
| 休息 5/15/30 | 🔴 **完全没做** |

**根因（认知级）**：开发以为"配置项进了 schema，WebUI 就有了"。
**错**：schema 只影响**核心自动生成的配置页**；`pages/config/` 是**手写 HTML/JS**，不会自动跟着变。

**已立规矩：`README.md`「加功能的四件套硬流程（缺一件 = 没做完）」**

| # | 交付物 | 不做的后果 |
|---|---|---|
| ① | 功能代码 `main.py` | 功能不存在 |
| ② | 配置项 `_conf_schema.json` | 用户改不了 |
| ③ | **面板控件 `pages/config/`** | **WebUI 上完全看不到** ← 本次栽在这 |
| ④ | 说明文档 `README.md` | 用户不知道有这功能 |

附提交前自查四条命令 + **本次真实反面案例**入档。

`Task.md` 任务 44 已补进度表（哪项做了、哪项没做、哪项没做全）。

⚠️ 只改文档：未动插件代码。

## [2026-10-27] 规划 Agent — 任务 43 结案（用户实测通过）+ 立 v1.3.0 交付规划

**信息更正**：任务 43 面板保存 **用户 2026-10-27 10:40 亲自实测通过**（改一项→保存→成功→落盘）。
此前我还在说"待复验"，是信息落后。`Task.md` 已改为「用户已验证，等测试 Agent 签字关闭」。

**新增 `BRD.md`「学习打卡 v1.3.0 交付规划」**（用户要求覆盖七个维度）：

- **目标**：三阶段 —— 不崩 / 能管 / 有节奏；判据是「连续用一周不出错」
- **范围**：做 4 类（修 bug、加 4 个管理员命令、12 项配置、面板控件）；
  **明确不做**：每日打卡/排行榜、面板视觉重做、改核心、动 `keyword_reply`、新建目录
- **关键步骤与依赖**：① 修 `is_admin`（**唯一硬前置**）→ ② 异常兜底 → ③ 解析放宽 → ④ 状态机骨架
  → ⑤⑥⑦ 暂停/放弃/休息 → ⑧ 配置项 → ⑨ 面板 → ⑩ 自测
- **风险点 8 条**：休息状态重启丢、暂停与休息打架、改表坏数据、`不学了` 语义做偏、
  `修改总时长` 算进今天、文案漏配、开发空转、改完不重载
- **优先级**：P0 修 `is_admin` + 异常兜底 → P1 解析/暂停/放弃/休息 → P2 配置 → P3 面板 → P4 样式
- **预期产出**：代码（main.py / schema +12 / pages）、文档（CHANGELOG / Task / 500 字报告）、
  证据（6 项自检 + 九条验收 + 新加载日志）

⚠️ 只改文档：未动插件代码。

## [2026-10-27] 规划 Agent — Task 顶部改成「现在做什么」+ README 立「交付报告要求」

**用户指责**：开发读了几轮文件就"待命中"，需求（休息/暂停/放弃）一条没动 —— 根因是**任务藏在 Task.md 第 236 行**，
而文件开头还停在 9-21 的旧状态（"AstrBot 从未启动过"，早就不成立了）。

**改法一：`Task.md` 顶部整段重写为「现在做什么」**

| 优先级 | 任务 | 一句话 |
|---|---|---|
| **P0** | **任务 44** | 管理员命令点了没反应（`is_admin` 崩）+ 加 `不学了` / 休息 5-15-30 / `学习暂停` / `继续学习` |
| **P1** | 任务 43 | 面板保存已改完（实测 GET/POST 200、值能落盘），只差界面复验 |
| P2 | 任务 42 | logo 重画，待重载看效果 |
| P3 | 任务 35 | 其余插件补 README + 面板 |

并写明「打开 BRD 对应章节照规格写」「做完必须交自检输出 + 500 字大白话报告」。

**改法二：`README.md` 新增「交付报告要求（强制，不得逃避）」**

四条硬要求：① 说功能变成什么样，不说改了哪一行；② **1 岁小孩能听懂**，不许出现函数名/行号/API；
③ **≤500 字**；④ 讲清「以前什么样、现在什么样」。附合格/不合格例子，并点名反面案例
（连说"修好了"、实际"什么都没改"）。核心一句：**报告写不清 = 没法验收 = 这轮白干。**

⚠️ 只改文档：未动插件代码。

## [2026-10-27] 规划 Agent — 查明管理员命令「完全没反应」三层根因 + 立 v1.3.0 规格

**用户报告**：群里发「修改技能…」「修改今日时长…」**一点反应都没有**；但「总学习时长」正常。

**三层根因（全部实测，不是推测）**

| # | 层 | 证据 |
|---|---|---|
| **1** | **`is_admin()` 一进门就抛异常** | `main.py:348` 用 `self.context.get_using_platform()`；日志实锤 `AttributeError: 'Context' object has no attribute 'get_using_platform'` → 异常被吞 → **静默无回复** |
| **2** | **解析要求空格** | 用真实配置跑：「修改技能打龙师改为滚木」→ `None`；「修改今日时长 打龙师1分钟」→ `None`（`\s+` 要求空白） |
| **3** | **超大数字溢出** | 22 位数字能解析，但写库时 `OverflowError: Python int too large to convert to SQLite INTEGER` → 又一条静默失败 |

**修法**：① `is_admin` 改 `return event.is_admin()`（核心 `astr_message_event.py:268`，禁言插件同写法）；
② 正则 `\s+` → `\s*`；③ 分钟数夹紧 1–1440 后再写库；④ `handle()` 外层加 try/except，异常必须记日志并回一句。

**v1.3.0 规格已写入 `BRD.md`（含状态流转图）**

- 状态机四态：`IDLE / STUDYING / PAUSED / RESTING`
- 管理员命令扩到 **4 个**：改技能 / 改今日 / 改本周 / 改总时长（均增量，单次 1–1440）
- **`不学了`** → 当前所有正在计时的会话 `counted=0`、`duration=0`（不删记录，保留可追溯）
- **休息**：学完先「恭喜完成」→ 问 5/15/30 → 休息中**禁止学习、不可暂停** → 到点「休息完毕，可以继续学习啦」
- **暂停**：`学习暂停` / `继续学习`；空状态回「你现在还没有开始学习哦」；重复操作有专门提示
- 新增 8 个配置项 + 8 条文案键，全部可在 WebUI 改
- **验收九条**已列全

`Task.md` 新增**任务 44**（含"必须附交付自检输出"）。

⚠️ 只读排查 + 改文档：未动插件代码、未碰运行目录。

## [2026-10-27] 规划 Agent — 立「交付自检协议」：说修好了必须自己测过并贴输出

**用户要求**：「他说修好了之后你要让他自检，不然他修好了自己都不测搞鸡毛」。

**三条硬规矩（写入 `BRD.md`「三·补4 交付自检协议」，适用于所有插件面板类改动）**

1. **「代码写完了」不算交付** —— 必须在界面上**真点一次**，并把结果贴出来。
2. **自检必须贴原始输出**，不接受「已通过 / 测试正常」这类结论。
3. **自检没过就别说修好了** —— 写清卡在哪一条、报什么错，然后停手回报。

**任务 43 的 6 项自检（可直接复制填写）**

① 两个 handler 签名只能有 `self`
② `self.context.save_config` = **0**、`self.config.save_config` ≥ 1
③ `apiGet/apiPost` 参数是 **`"config"`**（不许带插件名或前导 `/`）
④ 重载后日志无新 `TypeError.*api_`
⑤ 浏览器 F12 Console 无报错
⑥ **界面实点保存 + 改前改后值都贴出来 + 重载后值仍在**

**判定**：6 条全部有输出且符合预期才算修完；**缺一条视为未交付**。

`Task.md` 任务 43 已把该要求写成验收硬条件。

⚠️ 只改文档：未动插件代码、未碰运行目录。

## [2026-10-27] 规划 Agent — 第四次定位：日志 Traceback 实锤，卡在 handler 签名（+ 第 5 层待撞）

**证据**（`astrbot.log` 10-27 09:50）

```
dashboard/asgi_runtime.py:471  result = view_func(**path_params)
TypeError: Main.api_get_config() missing 1 required positional argument: 'req'
```

链路**已经全通**：路由匹配 ✅（`plugin_path='astrbot_plugin_liflag/config'`）、
鉴权 ✅（`AuthContext(username='Edi', via='jwt')`）、handler 找到 ✅ —— **只死在最后一步调用**。

**第 4 层**：handler 签名多了一个**必需参数** `req`；核心是 `view_func(**path_params)`，
**永不传 request 对象**。→ 去掉 `req`，改用**模块级 `request`**（`from astrbot.api.web import request`）。

**第 5 层（修完上面马上撞）**：`self.context.save_config(...)` —— **`StarContext` 没有这个方法**（全库 0 命中）。
→ 必须 `await asyncio.to_thread(self.config.save_config)`（对照 `library_ui.py:369`）。

**五层错误总表已写入 `BRD.md`「三·补3 第四次定位」**，并附**完整可跑代码**与 **6 条返工自检**
（签名只能有 `self` / `self.context.save_config` 必须 0 / `apiGet` 参数是 `"config"` /
日志无新 TypeError / F12 无报错 / 界面真点保存且配置文件值真变）。

⚠️ 只读排查 + 改文档：未动插件代码、未碰运行目录。

## [2026-10-26] 开发 Agent — 任务 42 GPT 系列 Logo 制作与同步

- 改动：8 个 plugins/astrbot_plugin_{liflag,mute,keyword_reply,group_welcome,usage_guide,chat_extractor,role_call,meme_library}/logo.png；已同步运行实例对应目录。
- 生成：内置 image_gen 逐张生成，薄荷绿/紫/红配色、柔和插画、功能符号、右下角蝴蝶；无人物和文字。缩放仅用于导出规定尺寸，非代码绘制。
- 自测：8/8 真 PNG、256×256，仓库与运行副本 SHA-256 相同；已目视检查全部原图和并排总览。
- 证据：H:/Program/_wb/allbot-logos-20261026/ 保存原图、旧图双份备份、preview.jpg、validation.json、prompts.json。
- 推送状态：本地已提交；自动审批拒绝向远程 main 推送，理由为用户未明确授权发布到共享默认分支。取得明确授权后执行 git push origin main，并核对远端 HEAD。
- 待复验：启动器只返回空区域，截图 FrameArrived timeout；两次无进展后停止 UI 操作。未执行插件重载，未宣称 WebUI 全部显示，任务保持未关闭。
- 补记：此前 2dfe7c8 将 SVG 换成 PNG，遗漏开发日志；本次记明，该批几何图已由本次 GPT 图替换。
- 边界：未改核心、配置、数据库或插件功能；他人未提交改动保留。

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

