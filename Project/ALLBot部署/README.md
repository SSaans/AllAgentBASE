# ALLBot部署 使用说明

> AstrBot QQ 机器人「丛雨」调教项目：插件命令 + 指令触发群总结 + 转发聊天记录长短分流 + 若干自建插件

## 环境与依赖

**2026-09-21 新机环境补验**：本会话终端起点仍为 `D:\`，项目操作须显式指定 `E:\AllAgentBASE`。实例 venv 的旧用户路径已修复，Python 3.12.13、pip、依赖一致性及核心依赖导入通过；这只证明环境可用，未启动机器人，群内功能及插件加载仍待任务 38 复验。旧日志文件存在不能证明新机正在写日志。

**项目管理仓库**：[SSaans/AllAgentBASE](https://github.com/SSaans/AllAgentBASE)，本地工作区 `E:\AllAgentBASE`（**唯一权威**，别再找别的副本）。下面是**实际运行**的文件位置（都在仓库外）。

| 项 | 位置 / 说明 |
|---|---|
| 管理程序 | `H:\Program\AstrBot\AstrBot Launcher`（AstrBot Launcher 0.3.9） |
| 核心版本 | AstrBot v4.26.8 |
| 实例目录 | `C:\Users\Unbox\.astrbot_launcher\instances\4450a298-f4c2-43fa-b7f7-bd645b753fc3\core` |
| **QQ 生效配置档** | `core\data\config\abconf_626c9487-1b19-4180-8878-48a1b85b26fe.json`（「丛雨丸」）——**改配置要改这一档** |
| 主配置（兜底） | `core\data\cmd_config.json`（全局默认值；**含敏感信息，严禁入库**） |
| 转发阈值 | 在**「丛雨丸」档**的 `platform_settings.forward_threshold`，**实测 = 50**。默认档里的 1500 是兜底，改它没用 |
| 唤醒前缀 | ⚠️ **2026-09-21 实测为 `['丛雨酱']`**（`丛雨` 已不在其中；**用户自行调整的，不是故障、别改回去**）。**不要加 `/`**（会误唤醒群内所有 `/` 消息） |
| 人设存储 | `core\data\data_v4.db`（丛雨） |
| QQ 接入 | OneBot v11 反向 WS `:6199` ← SnowLuma 客户端（协议端由用户维护） |
| WebUI | 端口由 Launcher 分配（**旧机末次实测 `19953`；旧文档的 17163 已过期**）→ **以 Launcher 面板里的实际入口为准**，账号 Edi |
| 群分析插件 | `core\data\plugins\astrbot_plugin_qq_group_daily_analysis` |
| 图片库插件 | `core\data\plugins\astrbot_plugin_meme_library` **v1.7.0**，图存在 `core\data\meme_library\<关键词>\` |
| 纯唤醒插件 | `core\data\plugins\astrbot_plugin_presence_reply` v1.1.0 |
| 运行日志 | `core\data\logs\astrbot.log`（判据看文件有没有长大，别只看 `log_file_enable` 字段）。⚠️ **换机后本机尚未启动过实例**：当前日志内容仍是旧机的（最后一条 = `2026-09-21 00:31` 关闭记录，路径含 `WindoseII`） |

## 启动 / 停止

> 🔴 **新机首启前置（2026-09-21 规划 Agent）**：迁移后本机**尚未成功启动过实例**。Launcher 会弹
> `文件系统错误: Version zip file not found: "C:\Users\WindoseII\.astrbot_launcher\versions\v4.26.8.zip"`。
>
> - **这不是数据损坏**：实例目录、配置、插件、人设库均完好；`venv` 的旧 Python 路径已由测试 Agent 修复并验证通过。
> - **根因**：Launcher 的持久化库 `C:\Users\Unbox\.astrbot_launcher\data.redb` 里残留**旧机的绝对路径**；而版本包其实就在 `C:\Users\Unbox\.astrbot_launcher\versions\v4.26.8.zip`（4,371,179 B）。
> - **修法（需在 Launcher 界面操作，按省事排序）**：
>   1. 点版本号旁的「可更新」重新下载 / 修复 → 让它按当前用户目录重建记录；
>   2. 进「高级」页看有无「数据目录 / 实例目录」设置项，指向 `C:\Users\Unbox\.astrbot_launcher`；
>   3. 仍不行：完全退出 Launcher（确认托盘无残留）→ **先备份 `data.redb`** → 删除实例记录后重新导入 `instances\4450a298-…\core`。
> - ⚠️ **红线**：Agent 不得二进制改写 `data.redb`（redb 带页校验，原地改即损坏）。
> - 📌 启动后两个易踩点：① 按本文件上方插件清单核对加载，**首启之前「插件已加载/已生效」的旧结论一律不成立**；② **WebUI 端口由 Launcher 分配**（旧机末次实测 `19953`，文档旧值 `17163` 已过期）。

通过 **AstrBot Launcher** 管理开关；命令行查进程：

```powershell
Get-Process | Where-Object { $_.ProcessName -match 'astrbot|python' }
```

⚠️ 改核心文件（见文末「核心补丁」）必须经 Launcher **正常重启**才加载。**不许按进程名批量强杀。**

## 群内怎么用

| 操作 | 说明 |
|---|---|
| `@丛雨` + `群分析` | 出当天的群聊分析报告（话题 / 称号 / 金句 / 锐评）。手动触发**不受** 200 条门槛限制 |
| `@丛雨` + `群漫画 [天数]` | 把最近 N 天的核心话题画成多格漫画（不写天数走默认） |
| `@丛雨` + `分析设置` | 看/改分析设置 |
| 直接叫「丛雨」「丛雨酱」 | 也可以唤醒（名字在唤醒前缀里） |
| 短回复 | ≤ 阈值 → 直接发普通消息 |
| 长回复 | > 阈值 → 自动转「合并转发聊天记录」卡片（标题显示「丛雨的聊天记录」） |

**当前命令写法（2026-09-16 源码与实测勘误）**：名字前缀中没有 `/`，因此使用 `@丛雨 sid`、`@丛雨 群分析`、`@丛雨 群漫画`，**命令前不要再带 `/`**。`@` 只完成唤醒，并不会自动删除正文中的斜杠；内置 `sid` 和上述插件命令均未注册带斜杠的别名。旧文档中「@ + /命令」在当前配置下不成立。无需把 `/` 加回前缀。

**管理员与白名单是两道判断**：管理员名单按发言人 QQ 识别；核心白名单按群号/会话 ID 识别。只有管理员例外开关开启，管理员才会跳过对应的群/私聊白名单检查；仅在两个名单中同时填写自己的 QQ 不会自动获得豁免。

**唤醒方式说明**：AstrBot 的命令过滤器要求 `is_at_or_wake_command` 为真（`star/filter/command.py:191-192`）。满足它的方式有：@ 机器人 / @全体 / 引用机器人消息 / 私聊 / 消息以 `wake_prefix` 里的词开头。
🔴 **不要把 `/` 放进唤醒前缀**——实测那样会让群里任何 `/` 开头的消息都被当成唤醒，跟别的 bot 指令打架。

## 长短分流标准

话短就直接发；话长（超过 `forward_threshold`）就打包成 QQ 合并转发卡片。

- **改哪**：WebUI → 平台设置 → 选中 **「丛雨丸」** 档 → 改 `forward_threshold` → 保存，**马上生效、不用重启**。
- **字段全路径**：`platform_settings.forward_threshold`；生效判断在 `core/astrbot/core/pipeline/result_decorate/stage.py:414`（`if word_cnt > self.forward_threshold`）→ **刚好等于阈值还是直发**。
- **别改错地方**：全局默认 1500 在 `core/astrbot/core/config/default.py:66`，被档内值覆盖，**改它不影响 QQ 实际行为**。直接改磁盘 JSON 也不会更新运行中的对象。
- **硬前提**：`provider_settings.streaming_response` 必须是 `false`，否则流式结果提前发出去、跳过长度判断。
- 字数按 Plain 文本组件累加；图片、语音这类不算字数。`segmented_reply` 当前是 `false`，短回复稳定 1 条。

## 敏感信息红线

`cmd_config.json` 里有 LLM API Key、WS token、仪表盘密码。**任何改动都不许把这些提交到仓库**，文档只写文件位置。
⚠️ 仓库根 `data/` 是个**未跟踪**目录且含敏感文件（`.gitignore` 没覆盖它）→ 永远**不要 `git add .`**，只 `git add Project`。

## 插件开发硬规范（加载失败先查这里）

> 官方文档（**唯一权威**）：
> - 插件配置：https://docs.astrbot.app/dev/star/guides/plugin-config.html
> - 插件开发总指南：https://docs.astrbot.app/dev/star/plugin-new.html
> - 项目仓库：https://github.com/AstrBotDevs/AstrBot
>
> 🔴 **红线：绝不去改 AstrBot 核心 / 虚拟环境 / Launcher 数据库 / 全局配置**。
> 插件加载失败，先假定**插件自身不规范**（`_conf_schema.json`、`metadata.yaml`、import、语法），在插件目录里找原因；核心只需要读日志堆栈定位，不需要改。

### `_conf_schema.json` 必须是「扁平」结构

**✅ 正确写法**（顶层每个键就是一个配置项，值必须是带 `type` 的对象）：

```json
{
  "start_word": { "type": "string", "description": "开始触发词", "hint": "例如 xx", "default": "我要学习" },
  "min_minutes": { "type": "int", "description": "最短分钟数", "default": 5 },
  "group_rules": {
    "type": "object",
    "description": "嵌套配置",
    "items": {
      "enable": { "type": "bool", "description": "开关", "default": true }
    }
  }
}
```

**字段说明**：`type`（**必填**）、`description`（一句人话）、`hint`（问号里的说明）、`default`（默认值）、`secret`（token 这类填 `true`，WebUI 会打码）、`items`（**只有 `object` 类型必填**）。

**`type` 只有这 9 个合法值**：`string` / `text` / `int` / `float` / `bool` / `object` / `list` / `dict` / `template_list`
- 多行大文本用 `text`（WebUI 给可拖拽的 textarea）；单行用 `string`
- **没有 `integer`**，整数一律写 `int`

### 四种典型错法 → 对应报错（一看就能对上）

| 错法 | 报错 |
|---|---|
| 顶层套成 JSON Schema：`{"type":"object","title":"...","properties":{...}}` | 加载失败 `string indices must be integers, not 'str'` |
| 某一项写成字符串：`"start_word": "text"` | 同上 |
| 写成 `"type": "integer"` | `不受支持的配置类型 integer` |
| `object` 用了 `properties` 而不是 `items` | `KeyError: 'items'` |

> **2026-10-26 实例**：学习打卡插件踩了第 1 条 —— `_conf_schema.json` 被包成 `{type,title,properties}`，开发连改 4 次业务代码都无效，**因为报错发生在读取 schema 阶段，`main.py` 一行都还没执行**。

### 改完必须自查（一条命令，别靠"重载试试"赌）

用实例 venv 跑，能打印出「N 项 OK」才算过：

```bash
"<实例目录>/venv/Scripts/python.exe" -c "import sys,json;sys.path.insert(0,r'<实例目录>/core');from astrbot.core.config.astrbot_config import AstrBotConfig as C;d=json.load(open(r'<插件目录>/_conf_schema.json',encoding='utf-8'));print(len(C._config_schema_to_default_config(None,d)),'项 OK')"
```

### `metadata.yaml` 也按官方字段写

`name` / `display_name` / `desc` / `version` / `author` / `repo` / `astrbot_version`（PEP 440 格式，如 `>=4.24.1`，**不加 `v` 前缀**）/ `support_platforms`（必须是 `aiocqhttp`、`telegram` 这类适配器 key 的列表）。

### 插件 Logo（官方规定 + 我们的做法）

**官方规定**（`plugin-new.html`「设置插件 Logo（可选）」）：在**插件目录下放一个 `logo.png`** 即可，**长宽比 1:1，推荐 256×256**。`metadata.yaml` 里**没有** logo 字段，别去加。

> 🔴 **三条硬事实（2026-10-26 源码级核实，改之前先看）**
> 1. **只认 `logo.png`，`logo.svg` 一律无效。** 核心写死了 `star_manager.py:213` → `self.logo_fname = "logo.png"`，加载时 `os.path.join(插件目录, "logo.png")` 再 `os.path.exists()` 判断；文件名不对，`metadata.logo_path` 就是 None，前端拿不到地址，卡片显示默认图标。
> 2. **不能把 svg 改名成 png。** logo 通过 `/api/file/<token>` 返回，用的是 `FileResponse(path)` **按后缀推断 MIME**；内容还是 SVG 就会被当成 `image/png` 发出去，浏览器裂图。而实例 venv 里**没有 cairosvg / svglib**（实测），转不了 SVG → **直接用 Pillow 画 PNG**（PIL 12.3 在）。
> 3. **加完必须重载插件。** `logo_path` 是在**插件加载**阶段写进 metadata 的（`star_manager.py:1171`、`:1376`），光刷新网页不生效。


**落地约定**
- 文件名固定 `logo.png`，放在插件根目录（和 `metadata.yaml` 同级）；仓库 `plugins/<插件>/logo.png` 与运行目录 `core/data/plugins/<插件>/logo.png` **各放一份**。
- 统一风格：圆角方形底 + 单色几何图标 + 一个主色（跟插件语气一致），**不要文字**（中文渲染容易糊）。
- `plugins/astrbot_plugin_liflag/logo.png` 是**风格参考样例**（圆角蓝底 + 书本 + 时钟）；正式版由开发按下面的方法自己画，13 个（自建 9 个）都要有。

### 开发 Agent 注意：**你能画，别问用户要图**

你不需要图像模型、不需要 Midjourney、不需要用户提供描述。**实例自带的 venv 里就有 Pillow 12.3**，直接画就是：

> 产物必须是 **`logo.png`（真 PNG）**，存成 `logo.svg` 等于没做。已有的 svg 留着无所谓，但**必须补 png**。画完在 WebUI 点一次**重载插件**才显示。

```bash
"<实例目录>/venv/Scripts/python.exe" make_logo.py
```

最小可跑模板（改颜色和图形就行，超采样再缩，边缘才不毛糙）：

```python
from PIL import Image, ImageDraw
S, OUT = 1024, 256                     # 4 倍超采样，最后缩到 256
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([0, 0, S-1, S-1], radius=int(S*0.22), fill=(76,125,240,255))   # 圆角底
# 这里画你的图形：d.polygon / d.ellipse / d.line / d.rounded_rectangle
# 例如画个圆：d.ellipse([S*0.3, S*0.3, S*0.7, S*0.7], fill=(255,255,255,255))
img.resize((OUT, OUT), Image.LANCZOS).save("logo.png", "PNG")
```

**自建插件 9 个，图标概念**（自己画，别互相撞色）

| 插件 | 图形 | 主色 |
|---|---|---|
| `liflag` 学习打卡 | 书本 + 时钟 | 蓝 `#4C7DF0` |
| `keyword_reply` 关键词回复 | 对话气泡 + 钥匙 | 紫 `#7C5CF0` |
| `group_welcome` 入群欢迎 | 门 + 招手小人 | 绿 `#2FB67C` |
| `usage_guide` 使用说明 | 问号 + 书签 | 青 `#2FA9B6` |
| `mute` 禁言 | 喇叭 + 斜杠 | 红 `#E05B5B` |
| `meme_library` 图片库 | 叠放的照片 | 橙 `#F0913C` |
| `presence_reply` 纯唤醒 | 耳朵 + 声波 | 粉 `#E85C9B` |
| `role_call` 指定召唤 | 喇叭 + @ | 深青 `#2F7CB6` |
| `chat_extractor` 聊天提取 | 文档 + 导出箭头 | 灰蓝 `#5C7A99` |

**上游 4 个（`qq_group_daily_analysis` / `repeater` / `limited_repeat` / `listen_music`）不要动**，那是别人的文件。

**验收**：13 个插件卡片在 WebUI 里都能看到各自图标，不是清一色默认星形。

## 详细需求与验收

见同目录 `BRD.md`（功能规格 + 验收标准），任务明细见 `Task.md`。

---

## 本机改动登记

### 2026-09-15 开发核实

- QQ 路由指向独立配置档「丛雨丸」，不是默认档。管理员已按用户给的 QQ 号加入 `admins_id`（WebUI 昵称 Edi ≠ QQ 管理员身份）。
- `/群分析`、`/群漫画`、`/分析设置` 等由插件声明为**管理员命令**，普通群友会收到明确的无权限提示；空核心白名单不拦截；插件 `group_list_mode=none` 不限群。
- 插件 `analysis_features.keep_original_persona` 从 false 改成 **true**，才会继承丛雨人设（旧文档说「两个开关都 false 也会继承」与实现不符）。
- `llm.llm_provider_id` 留空会回退当前会话模型，实测能调通，不需要写死 provider。
- `min_messages_threshold=200` **只限制定时分析**，手动 `/群分析` 不受限。
- 群漫画已配 `daily_comic.drawing_provider_overrides` 的 `openai_images` 供应商，2026-09-15 11:47 在测试群真实出图并发送成功。API Key 只在本机配置里。
- 除上述配置字段外，**没改过 AstrBot 或第三方插件的业务源码**。运行配置、密钥、聊天记录、报告图片都没入库。

### 唤醒前缀的最终口径（2026-09-16）

- **最终值 = `["丛雨","丛雨酱"]`**（用户 2026-09-16 02:18 设置），**不含 `/`**。
- 历史过程留档：曾把 `/` 加回前缀以恢复命令，结果发现**群里任何 `/` 开头的消息都会被当成唤醒**（含群内其它 bot 的指令），误触发且尴尬 → 已移除。
- **正确做法 = @ 机器人**：`is_at_or_wake_command` 在「@ / @全体 / 引用机器人消息 / 私聊」时为真，**和 `wake_prefix` 无关**。

### 核心补丁登记（**升级会丢，要重打**）

- **合并转发卡片标题**：核心 `astrbot/core/pipeline/result_decorate/stage.py:417` 原本硬编码 `name="AstrBot"` → 已改为 `"丛雨"`。
  - ⚠️ 这是**改核心文件**，AstrBot 升级后会被覆盖，必须重新打。
  - 插件侧同类改动在 `src/infrastructure/platform/base.py:190`（`self_name` 也改成了「丛雨」），那个属插件自身代码。
- 为什么不用插件钩子改：`on_decorating_result`（`stage.py:163`）比转发节点构造（`stage.py:415`）**早**，钩子里拿不到那个节点。

### 日志落盘

- 结论：**已落盘**（实测 `astrbot.log` = 115,590 B，跨度 `11:16:02 → 23:56:38`）。
- 📌 该版本只在**启动阶段**配置日志文件 sink，所以改完 `log_file_enable` 必须**正常重启**才生效。

---

## 🔴 开工必读（任何 Agent 接手前，先读这三份）

**顺序固定，不许跳：**

1. **`Task.md` 最上面那张「现在做什么」表** —— 现在该做哪件事、什么优先级、谁负责
2. **`BRD.md` 对应章节** —— 需求与规格（表里会写去哪个章节）
3. **`README.md` 的「加功能四件套」+「交付报告要求」** —— 交付标准

**读完之后先复述一句**「我要做的是 X，交付标准是 Y」，等确认再动手。
**没读过就动手 = 违规**，写出来的东西多半是错的（历史上已经发生过多次）。

> 📌 这条是 2026-10-27 用户当面要求定下的：
> 「每次执行的时候，我都要看到你 read BRD 和 Readme」「你以后也要阅读 Task.md」。

---

## 🔴 加功能的「四件套」硬流程（缺一件 = 没做完）

> 这是本子项目的**强制交付流程**，不遵守的提交一律打回。

**只要加了新功能，这四样必须同时交付：**

| # | 交付物 | 在哪 | 不做的后果 |
|---|---|---|---|
| **①** | **功能代码** | `main.py` | 功能不存在 |
| **②** | **配置项**（每个可调的东西都要有） | `_conf_schema.json` | 用户改不了，只能找开发者 |
| **③** | **面板控件**（让用户能点、能看状态） | `pages/config/`（index.html + app.js） | **WebUI 上完全看不到这个功能** ← 本次就栽在这 |
| **④** | **说明文档**（怎么用、有什么限制） | `README.md` 的「群内怎么用」「配置项」 | 用户不知道有这个功能 |

**⚠️ 最容易漏的是 ③。**

`_conf_schema.json` 加了项，**只会让核心自动生成的配置页多几个输入框**；
**自定义面板 `pages/config/` 是手写的 HTML/JS，不会自动跟着变。**
所以新功能要在面板上出现，**必须在 `index.html` 加控件、在 `app.js` 接数据**。

**自查（提交前跑一遍，四条全绿才能提交）**

```bash
P=plugins/astrbot_plugin_liflag
echo "① 代码：$(grep -c 'def ' $P/main.py) 个函数"
echo "② 配置项：$(python -c "import json;print(len(json.load(open('$P/_conf_schema.json',encoding='utf-8-sig'))))") 项"
echo "③ 面板：$(grep -c 'data-key\|id=' $P/pages/config/index.html) 个控件节点"
echo "④ 说明：$(grep -c '^###' $P/README.md) 个小节"
```
然后**逐项对照**：新加的功能，四样里是不是都有它的影子？
（新功能的触发词进了 schema 吗？面板上有它的控件吗？README 里写了怎么用吗？）

**真实反面案例（2026-10-27 10:47）**：开发提交了暂停/继续/放弃三个功能 + 12 个配置项，
**但 `pages/config/` 一个字节没动、`README.md` 还是昨天的** ——
结果用户打开 WebUI：**功能看不见、按钮没有、说明没有**，等于没做。

---

## 🔴 测试分工：谁测什么（2026-10-27 用户明确）

| 谁 | 测什么 | 在哪测 |
|---|---|---|
| **开发 Agent** | **自测**：代码能跑、接口能通、逻辑对 | **本机**（命令行 / 本地起进程 / 单元脚本） |
| **用户** | **群内实测**：真在 QQ 群里发命令，看机器人怎么回 | **群里**（只有用户能发） |
| **测试 Agent** | **按验收标准逐条复验** | 读证据 + 必要时本机复现 |

**🔴 两条硬约束**

1. **开发 Agent 不许自己在群里发测试消息。**
   群是用户的，机器人是给用户用的。开发要验证就**本机造数据、写脚本、看日志**，
   或者等用户测完把结果贴回来。
2. **开发的自测 ≠ 群内验收。**
   自测通过只能说"我认为它应该能用"，**不能写成"已验收""群内正常"**。
   群里到底行不行，**只有用户发过才知道**。

**所以开发的交付话术应该是**：
> 「我已在本机自测：X 项通过，证据如下。**群里还需要你发一下这三条**：…」

**而不是**：
> 「已修复，群内测试通过」（← 他根本没在群里发过）

---

## 一次做完（省 token 的工作方式，2026-10-27 起强制）

每一轮对话都要花钱。来回确认十次，比一次做对贵十倍。所以：

**对 Agent 的要求**

1. **接了任务就一路做到完**，中途不许问「要不要我继续」「需要我这样做吗」。
   只有两种情况可以停下来问：**要删/改用户的东西**，或者**文档里真的没写清**（说清是哪一条缺）。
2. **不要复述你读到了什么。** 读完直接干，别把文档内容抄一遍给用户看。
3. **一次交齐四样**：改了什么、证据、没做完的部分、下一步。**不许分几次报。**
4. **空转等于没干。** 只读文件、只发「在」「好的」「收到」而不动手，算这一轮白花。
5. **不确定就按文档做，别停下来问。** 文档写错了由规划 Agent 改，你不背这个锅。

**给用户的话术（一句话派活）**

> 按 Task 顶部的 P0 做，规格在 BRD 对应章节。**一次做完再回我**，中途别问。

**什么时候才该拆成多轮**

- 任务本身要你先做决策（比如删不删数据）
- 一轮做不完（比如要跑十几分钟的训练）
- 上一次做错了，要重新对齐方向

**除此之外，拆轮次就是在烧钱。**

---

## 交付报告要求（强制，不得逃避）

**修完不等于交付。修完 + 讲明白，才算交付。**

任何功能修复 / 新增，提交后**必须在回复里附一段说明**，四条硬要求：

1. **说「功能变成什么样了」**，不要说「改了 main.py 第 188 行」
2. **用 1 岁小孩能听懂的话** —— 不许出现函数名、行号、API 路径、技术黑话
3. **不超过 500 字** —— 超了没人看
4. **讲清「以前什么样、现在什么样」**

**✅ 合格的例子**

> 以前你在面板上点保存，它假装保存了，其实啥也没记住。现在点保存是真记住，重启也不丢。
> 另外加了个休息：学完它会问你要不要歇会儿，回 5、15 或 30 就行，歇着的时候不能开始新的学习。

**❌ 不合格的例子**

> 修复 handler 签名，去掉 req 参数改用模块级 request，并把 self.context.save_config 换成 self.config.save_config。

（技术上全对，**但用户看不懂，等于没报告**）

**为什么这条是硬性要求**：用户不是开发者，他只能靠「功能有没有变好」判断你有没有干活。
**报告写不清 = 他没法验收 = 这轮白干。**

**❌ 反例二：只声称完成、不给证据（用户 2026-10-27 原话，已收为硬标准）**

> 「不要只声称『已完成』却根本没有实际完成任何内容。请明确说明你实际做了哪些操作、
> 涉及哪些文件或步骤、当前真实进展与未完成的部分，并给出可验证的结果，而不是空泛的完成声明。」

**所以报告必须包含这四样：**

| 要说清 | 举例 |
|---|---|
| **实际做了哪些操作** | 「在面板加了休息时长的三个按钮，接上了保存」 |
| **涉及哪些文件** | 「面板页面、面板脚本、插件配置清单、说明文档」 |
| **当前真实进展 + 未完成部分** | 「暂停/放弃做完了；休息做了选择，倒计时还没做」 |
| **可验证的结果** | 「打开面板能看到三个按钮，点了会保存；群里发『我要学习』后能选休息时长」 |

**不许出现的三句话**：
- 「已完成」（没有下文）
- 「已同步到运行目录」（没说验证过界面）
- 「测试通过」（没贴输出）

**反面案例（真实发生过）**：开发连说几次「修好了」，用户打开界面发现一点没变；
追问后回答「我确实什么都没改」。**说了不做、做了不说，都算没交付。**

---

## 自测与正式验收

跑已安装源码的隔离自测（只用标准库，不启动 AstrBot、不调 LLM、不读群聊记录、不改配置）：

```powershell
python tests/check_installed_source.py --core <实例 core 绝对路径>
python tests/check_group_plugins.py   --core <实例 core 绝对路径>
```

- `check_installed_source.py`：白名单 / 人设回归 / 模型回退 / 定时关闭 / 转发字数边界 / 实际 QQ 配置档 / 转发节点到 OneBot 群合并转发。
- `check_group_plugins.py`：图片库与纯唤醒插件的隔离用例。

⚠️ **源码自测 ≠ 验收**。真实 QQ 消息、图片排版、人设口吻、卡片能否点开、普通成员权限提示、@ 与叫名字触发、两类卡片标题，都必须结合**真实群内结果**判断。**只有测试 Agent 能勾 `[x]`。**

## 自建插件使用入口

### 群友图片库 v1.2.0

- 入口：WebUI → 插件 → 群友图片库；或直达 `http://127.0.0.1:17163/#/plugin-page/astrbot_plugin_meme_library/library`（端口随 Launcher 实际入口）。
- 「图库」页：预览、上传、改关键词、移动图片、**二次确认删除**（删除只移到图库 `.trash/<编号>/<关键词>/`，能从文件系统找回）。
- 「回复与口令」页：改存图口令（默认 `/c`）、取图后缀（默认 `.jpg`）、数量连接符（默认 `x`），以及成功/重复/失败/没这个词/主人没这个词/超量各类回复——**保存立即生效**。
- 图片存在 `core\data\meme_library\<关键词>\`，按内容哈希命名去重；图库**独立于插件目录**，更新插件不会覆盖图。
- 用法：图片与 `/c 测试鱼.jpg` 同条发（或回复那张图发口令）；`测试鱼.jpg` 随机取 1 张、`测试鱼.jpgx3` 取 3 张（同批不重复、连续单张会避开上一张）；**只发「测试鱼」不触发**。
- ⏳ **待开发**：一次存多张 —— 一条消息带多张图 + `加图 <关键词>.jpg` → 全部入库；回复「存好了」/「x 张都存好了」（见 `BRD.md` 4.10、任务 24）。

### 纯唤醒回复 v1.1.0

- 只 @ 她、或只发完整唤醒词（后面没别的话）→ 回「吾辈在！」；**带其他内容则正常走 LLM**。
- 回复文字可在插件配置里改；唤醒词从**当前会话的核心 `wake_prefix`** 读（插件里不另存词表）。
- 现值 = `["丛雨","丛雨酱"]` → @ 和叫名字**都能触发**（**不加 `/`**）。

### 卡片标题

核心节点 `name` 与群分析报告 `self_name` 都已改成「丛雨」。补丁已随正常重启加载；**AstrBot 升级后要重打**。

## 第七轮四个插件（2026-09-16 已实际加载）

四个插件可在 WebUI → 插件页找到，点配置即可编辑，保存会热重载，不需要重启实例。

| 插件 | 群里怎么用 | 配置位置 |
|---|---|---|
| 关键词回复 v1.0.0 | 直接发「我是笨蛋吗」，随机回 是/不是/不知道/钝角；命中后不再让 AI 接话 | `rules_text` 一行一条：`触发词 => 答案1|答案2`；固定用 `触发词 => =答案`；指定个人用 `qq:QQ号: 触发词 => =答案` |
| 入群欢迎 v1.0.0 | 新成员进群自动欢迎，普通群消息不触发欢迎 | `welcome_text`、`at_new_member`、`group_texts`；支持 `{nickname}` / `{user_id}` / `{group_id}` |
| 使用说明 v1.0.0 | `@丛雨 使用说明` 回一段介绍 | `guide_text` 可改正文；`triggers` 可改触发词 |
| 禁言 v1.1.0 | `@丛雨 丛雨闭嘴` 默认 30 分钟，也可写 `闭嘴 10秒`；禁言期间一切新消息静默；`@丛雨 丛雨说话` / `可以说话了` / `解除禁言` 提前恢复 | `default_minutes`、`command_words`、`unmute_words`、`start_reply`、`unmute_reply`、`scope`、`admins_only` |

禁言默认只影响当前群。重复禁言口令重置计时但不回话；解除口令先于静默拦截判断，回复默认「好啦，我回来了」。自动到期默认静默恢复。手动恢复同时取消定时器并更新 `core/data/plugin_data/astrbot_plugin_mute/mute_state.json`。

源码备份已入仓库 `Project/ALLBot部署/plugins/`；运行副本在 `core/data/plugins/`，配置只存 `core/data/config/<插件名>_config.json`。安装前的未加载源码保存在 `core/data/temp/round7_before_install_20260916/`。本轮未修改唤醒前缀、供应商或 QQ 连接配置。

加载证据：运行日志 `2026-09-16 14:24:25–14:24:26` 记录四项加载，管理接口四项均启用；61 项隔离自测通过。真实群内结果需另行记录，不能用这些证据代替群内验收。

### 存图插件 v1.4.0 新设置

图库中修改关键词为已有关键词会自动合并去重；「删除关键词」确认后将整组图片移到 `.trash`。插件设置/图库设置可编辑「单次最多发送几张图片」（默认20）、「不限量 QQ 名单」和超量回复。名单中的人豁免上限；留空则所有人受限。超量先发到上限，再回「再发就刷屏啦...」。

### 立flag（v1.0.0）

插件页找到「立flag」→配置，可改触发词、提醒延后分钟数、回复、每周模板和累计祝贺门槛。

- `@丛雨 我要学习吃饭20分钟`：开始本人在本群的学习计时，20分钟计划在第30分钟提醒一次；发 `学完了` 结束，按实际时长统计。
- `@丛雨 今日学习时长 Edi`、`@丛雨 本周学习时长 Edi`、`总学习时长 Edi`：查询当前群此人的数据。姓名可换成QQ，省略默认本人。同名用QQ区分。
- 北京时间按日拆分，本周周一到周日；正在计时的学习也计入。忘记结束会一直累计，可发完成词结束。重载/重启不丢记录。
- 总时长祝贺规则一行一条：`0 => 继续加油`、`120 => 太棒了吧`；达到某门槛就使用该档，超过仍适用，直到达到更高门槛。
- 数据：`core/data/plugin_data/astrbot_plugin_liflag/study.sqlite3`，只在运行目录。

### 指定人员召唤（v1.0.0）

- `设置程序员 @甲 @乙`：设置当前群的程序员名单（重复设置会替换）。角色名可以换成其他称呼，不含空格。
- `召唤程序员 有人做程序吗`：逐个真正 @ 名单成员，然后分隔线及正文；也可只发 `召唤程序员`。
- 插件配置可填多个设置/召唤前缀、修改文案。默认只有机器人管理员可设置，群友均可召唤；权限开关可编辑。
- 数据：`core/data/plugin_data/astrbot_plugin_role_call/roles.sqlite3`，名单按群隔离。

以上两个插件已加载、自测通过，真实 QQ 展示与完整流程仍待用户/测试 Agent 复验。
