# ALLBot部署 使用说明

> AstrBot QQ 机器人「丛雨」调教项目：插件命令 + 指令触发群总结 + 转发聊天记录长短分流 + 若干自建插件

## 环境与依赖

**项目管理仓库**：[SSaans/AllAgentBASE](https://github.com/SSaans/AllAgentBASE)，本地工作区 `D:\Project\AllAgentBASE`（**唯一权威**，别再找别的副本）。下面是**实际运行**的文件位置（都在仓库外）。

| 项 | 位置 / 说明 |
|---|---|
| 管理程序 | `D:\Program\AstrBot\AstrBot Launcher`（AstrBot Launcher 0.3.9） |
| 核心版本 | AstrBot v4.26.8 |
| 实例目录 | `C:\Users\WindoseII\.astrbot_launcher\instances\4450a298-f4c2-43fa-b7f7-bd645b753fc3\core` |
| **QQ 生效配置档** | `core\data\config\abconf_626c9487-1b19-4180-8878-48a1b85b26fe.json`（「丛雨丸」）——**改配置要改这一档** |
| 主配置（兜底） | `core\data\cmd_config.json`（全局默认值；**含敏感信息，严禁入库**） |
| 转发阈值 | 在**「丛雨丸」档**的 `platform_settings.forward_threshold`，**实测 = 50**。默认档里的 1500 是兜底，改它没用 |
| 唤醒前缀 | 「丛雨丸」档顶层 `wake_prefix` = **`["丛雨","丛雨酱"]`**。**不要加 `/`**（会误唤醒群内所有 `/` 消息） |
| 人设存储 | `core\data\data_v4.db`（丛雨） |
| QQ 接入 | OneBot v11 反向 WS `:6199` ← SnowLuma 客户端（协议端由用户维护） |
| WebUI | `http://localhost:17163`（端口以 Launcher 当前入口为准，账号 Edi） |
| 群分析插件 | `core\data\plugins\astrbot_plugin_qq_group_daily_analysis` |
| 图片库插件 | `core\data\plugins\astrbot_plugin_meme_library` v1.4.0，图存在 `core\data\meme_library\<关键词>\` |
| 纯唤醒插件 | `core\data\plugins\astrbot_plugin_presence_reply` v1.1.0 |
| 运行日志 | `core\data\logs\astrbot.log`（**已在正常落盘**；判据看文件有没有长大，别只看 `log_file_enable` 字段） |

## 启动 / 停止

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
