# ALLBot部署 使用说明

> AstrBot QQ 机器人「丛雨」调教项目：插件命令 + 指令触发群总结 + 转发聊天记录长短分流

## 环境与依赖

**项目管理仓库**：[SSaans/AllAgentBASE](https://github.com/SSaans/AllAgentBASE)。本地 Git 工作区：`D:\Program\AllAgentBASE`。以下为实际运行文件位置（仓库外，非独立 Git 仓库）。

| 项 | 位置 / 说明 |
|---|---|
| 管理程序 | `D:\Program\AstrBot\AstrBot Launcher`（AstrBot Launcher 0.3.9） |
| 核心版本 | AstrBot v4.26.8 |
| 实例目录 | `C:\Users\WindoseII\.astrbot_launcher\instances\4450a298-f4c2-43fa-b7f7-bd645b753fc3\core` |
| QQ 生效配置 | `core\data\config\abconf_626c9487-1b19-4180-8878-48a1b85b26fe.json`（丛雨丸，平台路由指向此档） |
| 主配置 | `core\data\cmd_config.json`（LLM / 平台 / 唤醒前缀 / forward_threshold，含敏感信息，严禁入库） |
| 人设存储 | `core\data\data_v4.db`（丛雨） |
| QQ 接入 | OneBot v11 反向 WS `:6199` ← SnowLuma 客户端（协议端由用户维护） |
| WebUI | 本轮实际为 `http://localhost:17163`（以 Launcher 当前入口为准，账号 Edi） |
| 群分析插件 | `core\data\plugins\astrbot_plugin_qq_group_daily_analysis`（指令 `/群分析` `/群漫画` 等） |
| 插件配置 | `core\data\config\astrbot_plugin_qq_group_daily_analysis_config.json` |
| 运行日志 | 需开启 `log_file_enable=true` 后查看 `core\data\logs\astrbot.log` |

## 启动 / 停止

通过 **AstrBot Launcher**（`astrbot-launcher.exe`）管理实例启停；命令行确认进程：

```powershell
Get-Process | Where-Object { $_.ProcessName -match 'astrbot|python' }
```

## 群内用法（目标能力）

| 操作 | 说明 |
|---|---|
| `/群分析` | 触发当日群聊分析报告（话题/成员称号/金句/质量锐评；当前版本手动调用绕过 200 条门槛，无记录时明确提示） |
| `/群漫画` | 将当日核心话题生成为多格漫画 |
| `/分析设置` | 查看/修改分析设置 |
| 短回复 | ≤ `forward_threshold`（默认 1500 字）→ 普通消息直接发送 |
| 长回复 | > `forward_threshold` → 自动转为「合并转发聊天记录」卡片发送 |

## 长短分流标准（用户自定义）

在 WebUI 中选择 QQ 实际使用的配置档“丛雨丸”，修改 `platform_settings.forward_threshold` 并保存。配置 API 会重建该档的消息流水线，无需重启；直接编辑磁盘 JSON 不会立即更新运行对象。当前阈值保留 1500，按 Plain 文本组件的字符数累计；等于阈值仍直接发送。转为图片、语音等非文本组件时不应套用纯文本字数规则。

## 敏感信息红线

`cmd_config.json` 内含 LLM API Key、WS token、仪表盘密码。**任何改动不得将这些值提交到本仓库**；仓库文档只引用文件位置。

## 详细需求与验收

见同目录 `BRD.md`，任务明细见 `Task.md`。

## 2026-09-15 开发核实与本机改动

- QQ 路由指向独立配置“丛雨丸”，不是默认配置。其唤醒前缀原为 `["丛雨"]`，本轮保留并加入 `/`；默认档和 QQ 档保留原管理员条目，添加用户明确提供的 QQ 号。WebUI 昵称 Edi 不等于 QQ 管理员身份。
- `/群分析`、`/群漫画`、`/分析设置` 等由插件声明为管理员命令；普通群友应得到明确无权限提示。空核心白名单不拦截，插件 `group_list_mode=none` 不限群。
- 插件 `analysis_features.keep_original_persona` 从 false 改为 true，继承已有丛雨人设；`use_plugin_specific_persona=false` 保持。旧文档称两个开关均 false 仍会继承人设，与 `_build_system_prompt` 实现不符。
- `llm.llm_provider_id` 为空会回退到当前会话模型，再回退首个可用模型；本轮真实回退与 LLM 请求成功，不需要硬编码 provider。
- `min_messages_threshold=200` 只限制非手动分析。手动 `/群分析` 在少量消息场景已成功；未擅自改变门槛或开启定时总结。
- 默认配置 `log_file_enable=true` 已保存。此安装版本只在启动阶段配置日志文件 sink，需正常重启 Launcher 管理的实例后检查 `core/data/logs/astrbot.log` 增长；WebUI 内存日志可即时核对，但不能替代落盘验收。
- 群报告已生成且用户确认正常；漫画完成分镜后因缺少绘图供应商中止。兼容 Images API 的接口使用 `daily_comic.drawing_provider_overrides` 中的 `openai_images` 模板，模型与端点按供应商实际值填写，不把模型名称误当成已配置供应商。
- 仓库外修改均为上述三个 JSON 的配置字段，未修改 AstrBot 或第三方插件业务源码。运行配置、密钥、聊天记录及报告图片均未入库。源码隔离自测脚本是本仓库新增文件。

## 自测与正式验收

使用已安装 Python 运行 `tests/check_installed_source.py --core <实例 core 绝对路径>`。脚本仅依赖 Python 标准库，从指定安装源代码抽取方法，使用合成数据检查白名单、人设回归、模型回退、定时关闭与转发字数边界；不启动 AstrBot、不调用 LLM、不读取群聊记录、不修改配置。

本轮 8 项通过。实际 QQ 消息、图片排版、人设口吻、可展开转发卡片与普通成员权限提示仍须结合真实群内结果验收。测试 Agent 才可将 Task.md 勾选关闭。
