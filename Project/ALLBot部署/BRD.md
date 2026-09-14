# 子项目 BRD：ALLBot 部署（AstrBot QQ 机器人「丛雨」调教）

> 📅 立项时间：2026-09-15
> 👤 发起人：用户（Edi）
> 👤 维护者：规划 Agent
> 🎯 状态：规划完成，待用户确认后进入开发

---

## 项目目标

在已能正常聊天的 AstrBot QQ 机器人（人设：丛雨）基础上完成三项调教，并为其后续衍生程序（插件、辅助工具）建立开发规范：

1. **插件命令正常调用**：打通 AstrBot 插件命令链路，使群内可用 `/` 前缀正常触发插件指令（含第三方插件）；
2. **自动群总结（仅指令触发）**：配置群聊分析插件，群内发指令即可生成当日群聊总结报告（话题 / 成员称号 / 金句 / 质量锐评），并以丛雨人设口吻呈现；
3. **说话通过转发聊天记录实现（长短分流）**：按用户自定义标准自动选择消息形式——短内容直接发送，长内容以 QQ「合并转发聊天记录」卡片发送。

---

## 现状盘点（规划 Agent 实地核查，2026-09-15）

| 项 | 内容 |
|---|---|
| 管理程序 | AstrBot Launcher 0.3.9（安装包 `D:\Program\AstrBot\AstrBot Launcher`） |
| 核心版本 | **AstrBot v4.26.8**（`core/main.py`，`pyproject.toml` 确认） |
| 实例目录 | `C:\Users\WindoseII\.astrbot_launcher\instances\4450a298-f4c2-43fa-b7f7-bd645b753fc3\core` |
| 数据目录 | 上述 `core\data`（cmd_config.json、plugins、logs、data_v4.db） |
| LLM | OpenAI 兼容端点 `https://rkapi.com/v1`；模型 `gpt-5.6-terra`（默认）、`claude-opus-5`；`max_context_tokens=1000000` |
| 人设 | `default_personality = "丛雨"`，`persona_pool = ["*"]`（人设内容存于 `data_v4.db`） |
| QQ 接入 | `aiocqhttp`（OneBot v11）反向 WS `0.0.0.0:6199`，平台名「丛雨v1」← **SnowLuma** 客户端连接 |
| 唤醒前缀 | `["/"]` |
| 管理员 | `admins_id = ["Edi"]` |
| 已装插件 | `astrbot_plugin_qq_group_daily_analysis`（群分析）、`astrbot_plugin_repeater`（复读）、`astrbot_plugin_limited_repeat`、`astrbot_plugin_listen_music`（听歌） |
| 长消息转发 | `platform_settings.forward_threshold = 1500`（回复字数超过该值自动转合并转发，核心逻辑 `core/astrbot/core/pipeline/stage.py`） |
| WebUI | 仪表盘 `0.0.0.0:6185`（账号 Edi） |
| 运行状态 | astrbot 双 python 进程常驻（venv + py312），可正常聊天 |

⚠️ **敏感信息红线**：`cmd_config.json` 内含 LLM API Key、WS token、仪表盘密码，**严禁写入本仓库**，文档只引用位置。

---

## 📌 开发进度快照（2026-09-15 01:00 交接轮）

> 前序开发 Agent（Codex）因 5h 限额中断，本快照供接手 Agent 续跑。证据：Codex 会话截图 + 运行时实测。

| 项 | 状态 | 说明 |
|---|---|---|
| 核心配置 | ✅ 已落地 | `log_file_enable=true`；`admins_id` 增加用户 QQ 号（号码不落库，存于 cmd_config.json） |
| 群分析（手动触发） | ✅ 已实测 | **实测结论：手动 `/群分析` 不受 200 条/日下限限制**（与原假设不同，待接手复核后正式落库） |
| 转发卡片长消息实测 | 🔄 中断未定 | 测试指令已发，被限额打断，结果待接手 Agent 复核 |
| 日志落盘 | ⚠️ 待重启验证 | 进程未重启（自 09-14 17:54 常驻），`logs/astrbot.log` 尚未生成；`log_file_enable` 改动需重启生效 |
| 群漫画 | ⏳ 未开始 | 漫画 API 接入为 Codex 遗留待办 |
| 远端同步 | ⚠️ 未知 | GitHub 网络不可达（Failed to connect github.com:443）；远端是否存在 Codex 提交待网络恢复后 `git pull` 确认 |

---

## 核心功能与技术方案

### 功能 1：插件命令正常调用

**现状**：`plugin_set = ["*"]`（全部启用）、唤醒前缀 `/`、`disable_builtin_commands = false`。群分析插件指令已确认存在：`/群分析`、`/群漫画`、`/设置格式`、`/设置模板`、`/查看模板`、`/分析设置`、`/增量状态`。

**疑点（需开发验证，非已确认 Bug）**：
- `platform_settings.enable_id_white_list = true` 但 `id_whitelist = []`——需确认空白名单的语义（放行全部 or 拦截全部）；群内 `wl_ignore_admin_on_group = true` 仅管理员绕过，普通群友能否用指令待验证；
- `log_file_enable = false`——排查问题无日志可依，建议开启 `log_file_enable = true`。

**方案**：按「群内实际调用 → 抓日志/回复 → 定位拦截点（白名单/权限/前缀/插件加载）」逐层验证修复，保证至少管理员（Edi）与目标群普通成员能正常触发插件指令。

### 功能 2：自动群总结（仅指令触发）

**方案**：直接使用已安装的 `astrbot_plugin_qq_group_daily_analysis`：

- 群内发 `/群分析` 触发当日（`analysis_days=1`）群聊分析，输出格式 `image + text + html`（模板 scrapbook）；
- 分析维度：话题（≤5 个）、成员称号+MBTI（≤8 人）、金句（≤5 条）、聊天质量锐评；另有 `/群漫画` 生成多格漫画；
- 人设联动：`keep_original_persona=false`、`use_plugin_specific_persona=false`——插件提示词要求"从当前人格设定视角和口吻出发"，即报告以丛雨口吻撰写（当前即符合需求，验证时确认）；
- **确认项**：`llm.llm_provider_id = ""`（插件 LLM 调用是否回退默认模型需验证）；
- **确认项**：`group_list_mode = "none"` 且群列表为空——确认语义为"任意群可触发"即可，无需绑定群；`min_messages_threshold = 200` 对**定时分析**生效（手动触发不受此限，Codex 已实测，待复核）；
- 定时自动分析（`auto_analysis_time=["23:00"]`）按用户决策**不启用**，保留为可选迭代。

### 功能 3：说话通过转发聊天记录实现（长短分流）

**机制（已确认存在）**：AstrBot 内置逻辑——LLM 回复**字数超过 `forward_threshold`（当前 1500）** 时自动转为「合并转发聊天记录」卡片发送（`core/astrbot/core/pipeline/stage.py`）。

**方案**：
- 维持"长 → 合并转发、短 → 直接发送"的自动分流；`forward_threshold` 即"长短标准"，由用户定义数值（当前 1500 字，可调）；
- 验证 OneBot v11（SnowLuma）下合并转发卡片在群内正常展示；
- **可选衍生程序（用户确认后立项）**：编写小型插件，将转发节点的 `uin/name` 呈现为「丛雨」人设身份，并支持按丛雨口吻为长内容分段组织转发节点，使转发记录更贴近人设；
- 可选调优项：`segmented_reply`（长回复拆多条间隔发送）当前关闭，如用户需要短消息也按句拆分可另行开启。

---

## 验收标准

### 1. 功能验收

- [ ] 群内可正常调用插件命令（至少 `/群分析`、`/群漫画`），管理员与普通群成员均按预期获得响应或明确的无权限提示
- [ ] `/群分析` 在消息量达标（≥200 条/日）的群内产出完整报告：话题 + 成员称号 + 金句 + 质量锐评，输出 image/text 正常展示
- [ ] 群总结报告以丛雨人设口吻撰写（话题描述/锐评/金句理由符合人设）
- [ ] 短回复（≤阈值）以普通消息直接发送；长回复（>阈值）以合并转发聊天记录卡片发送，群内可正常点开查看
- [ ] 长/短标准由用户自定义（修改 `forward_threshold` 后立即生效，无需重启）

### 2. 文档验收

- [ ] 子项目 BRD.md / README.md / Task.md 齐全且与实测一致
- [ ] 根 CHANGELOG.md 记录立项与各轮开发/测试结论
- [ ] 运行目录（仓库外）改动均有修复说明 + 改动摘要落库（根 BRD 协作规则第 7 条）

### 3. 质量验收

- [ ] 无敏感信息（API Key、WS token、仪表盘密码）提交到仓库
- [ ] 无未说明的 TODO/FIXME 遗留
- [ ] 依赖与环境在 README 中声明
- [ ] 日志已开启，排查链路可复现

### 4. 交接验收

- [ ] 测试 Agent 在 CHANGELOG 中签字结论（通过 / Bug 清单打回）
- [ ] Task.md 任务状态全部流转到「已关闭」（仅测试 Agent 可勾选）

---

## 不做的事情（边界）

- ❌ 不编写新的人设（丛雨人设已由用户定义，仅验证其在总结/转发场景的呈现）
- ❌ 不启用定时自动群总结（`auto_analysis_time` 保持关闭；如需改为定时，用户另行决策）
- ❌ 不在本仓库存储任何运行目录配置、密钥或聊天记录
- ❌ 不修改 SnowLuma / QQ 官方侧配置（协议端由用户维护）

---

## 已知风险与待确认项

| # | 风险/待确认 | 影响 | 处置 |
|---|---|---|---|
| 1 | 空 id 白名单语义不明 | 普通群友可能无法用指令 | 开发阶段实测确认，必要时配置白名单 |
| 2 | 群分析插件 `llm_provider_id=""` | 插件 LLM 可能无法调用 | 手动触发已实测可用，正式报告输出复核 |
| 3 | ~~消息量不足（<200 条）不出报告~~ | 小群无法总结 | **已实测：手动触发不受 200 条限制**（Codex 结论，待复核落库）；定时分析仍受此限 |
| 4 | 合并转发在 SnowLuma/OneBot 的兼容性 | 长回复转发失败 | 长消息实测被限额打断，接手 Agent 重测 |
| 5 | `forward_threshold` 默认 1500 可能不符合用户预期 | 长短分流标准不符 | 由用户定义数值后调优 |
| 6 | `log_file_enable` 改动需重启生效 | 日志未落盘 | 接手 Agent 重启后验证 `logs/astrbot.log` |
