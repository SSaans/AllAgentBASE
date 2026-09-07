# shinsekai项目byendcycle 使用说明

> Shinsekai（新世界）桌宠部署项目：桌宠开口说话 + 心跳自动检查 + 自动识屏

## 环境与依赖

**项目管理仓库**：[SSaans/AllAgentBASE](https://github.com/SSaans/AllAgentBASE)。本地 Git 工作区为 `H:\Program\AllAngelBASE`，本项目文档位于 `Project/shinsekai项目byendcycle/`。下列安装目录是实际运行文件所在位置，不是独立 Git 仓库。

识屏排查的常见错误、验收规则和后续 Agent 要求见本目录已有的 `HANDOFF_识屏误判修复.md`。

| 项 | 位置 / 说明 |
|---|---|
| 程序安装目录 | `H:\Program\新世界\Shinsekai`（整合包 v2.3.1，无需额外安装 Python） |
| 上游项目 | https://github.com/RachelForster/Shinsekai |
| LLM 配置 | `H:\Program\新世界\Shinsekai\data\config\api.yaml`（视觉模型，Key 仅存本地） |
| TTS | GPT-SoVITS v2pro 本地 bundle（`data\tts_bundles\installed\`） |
| 角色语音模型 | `data\models\Murasame\`（丛雨） |
| 心跳插件 | `plugins\shinsekai_heartbeat\` |
| 识屏插件 | `plugins\screen_state_companion-BYGPT\`（capture_screen 工具） |

## 启动桌宠

直接双击：

```
H:\Program\新世界\Shinsekai\shinsekai.exe
```

首次对话前确认「API 设定」里已保存 LLM 配置（本地已配置完成）。

## 验证「开口说话」

1. 在聊天主窗给角色发任意消息；
2. 角色立绘联动 + 文字气泡回复；
3. TTS 自动拉起 GPT-SoVITS 服务（首次需数秒）并以丛雨语音朗读台词。

## 验证「心跳自动检查 + 自动识屏」

1. 保持聊天窗口开启，静置不动（当前配置 5–60 分钟随机触发）；
2. 触发时角色会主动开口，并调用 `capture_screen` 获取当前屏幕截图；
3. 角色根据屏幕内容自然评论（例如在写代码、看网页时给出相应关心）。

快速测试方法：在插件设置页把「最短/最长空闲时间」临时改为 `0.1–0.2` 分钟（6–12 秒），测完改回。

手动触发识屏：直接在聊天里说「看看我现在的屏幕」。

## 常用配置入口

| 需求 | 位置 |
|---|---|
| 心跳频率 / 模式权重 / 提示词 | 设置 → 插件 → 心跳陪伴 Heartbeat Companion（配置热生效） |
| 心跳配置文件（直接编辑） | `data\plugins\io.github.hard_to_tell.heartbeat_companion\config.json` |
| 识屏插件配置 | `data\plugins\com.local.screen_state_companion\config.json` |
| 插件启用清单 | `data\config\plugins.yaml`（修改后需完整重启） |
| 运行日志 | `logs\main.log`（心跳/识屏事件可在此核对） |

## 已验证结论（2026-09-07）

- 程序运行稳定（双进程常驻，日志无致命错误）
- TTS 语音正常（GPT-SoVITS 服务自动启动、语音模型切换成功、多次派发成功）
- 心跳检查节点多次自动触发（heartbeat.emitted）
- 触发后 capture_screen 截图识屏闭环成功（截图附件生成，模型基于屏幕内容发言）

详细需求与验收记录见同目录 `BRD.md`，任务明细见 `Task.md`。

### 2026-09-08 心跳不触发的已知修复

如果插件显示“已启用”但长时间没有主动说话，先检查日志是否在同一会话每秒重复 `heartbeat.scheduled`。旧逻辑在关闭学习监督时反复重置普通心跳计时，现已修复为只在实际学习会话存在时停止学习监督。识屏定时开关仍保持关闭状态。
