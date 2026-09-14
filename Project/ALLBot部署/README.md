# ALLBot部署 使用说明

> AstrBot QQ 机器人「丛雨」调教项目：插件命令 + 指令触发群总结 + 转发聊天记录长短分流

## 环境与依赖

**项目管理仓库**：[SSaans/AllAgentBASE](https://github.com/SSaans/AllAgentBASE)。本地 Git 工作区：`d:\Project\AllAgentBASE`。以下为实际运行文件位置（仓库外，非独立 Git 仓库）。

| 项 | 位置 / 说明 |
|---|---|
| 管理程序 | `D:\Program\AstrBot\AstrBot Launcher`（AstrBot Launcher 0.3.9） |
| 核心版本 | AstrBot v4.26.8 |
| 实例目录 | `C:\Users\WindoseII\.astrbot_launcher\instances\4450a298-f4c2-43fa-b7f7-bd645b753fc3\core` |
| 主配置 | `core\data\cmd_config.json`（LLM / 平台 / 唤醒前缀 / forward_threshold，含敏感信息，严禁入库） |
| 人设存储 | `core\data\data_v4.db`（丛雨） |
| QQ 接入 | OneBot v11 反向 WS `:6199` ← SnowLuma 客户端（协议端由用户维护） |
| WebUI | `http://localhost:6185`（账号 Edi） |
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
| `/群分析` | 触发当日群聊分析报告（话题/成员称号/金句/质量锐评，image+text；消息量需 ≥200 条/日） |
| `/群漫画` | 将当日核心话题生成为多格漫画 |
| `/分析设置` | 查看/修改分析设置 |
| 短回复 | ≤ `forward_threshold`（默认 1500 字）→ 普通消息直接发送 |
| 长回复 | > `forward_threshold` → 自动转为「合并转发聊天记录」卡片发送 |

## 长短分流标准（用户自定义）

编辑 `core\data\cmd_config.json` → `platform_settings.forward_threshold`（字数阈值），保存后热生效，无需重启。长内容走合并转发卡片，短内容直接发送。

## 敏感信息红线

`cmd_config.json` 内含 LLM API Key、WS token、仪表盘密码。**任何改动不得将这些值提交到本仓库**；仓库文档只引用文件位置。

## 详细需求与验收

见同目录 `BRD.md`，任务明细见 `Task.md`。
