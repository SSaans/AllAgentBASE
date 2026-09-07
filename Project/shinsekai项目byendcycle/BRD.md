# 子项目 BRD：shinsekai项目byendcycle

> 📅 立项时间：2026-09-07
> 👤 发起人：用户（byendcycle）
> 👤 维护者：规划 Agent
> 🎯 状态：部署完成，链路已验证（2026-09-07 测试 Agent 复核通过）

---

## 项目目标

在本地成功部署 **Shinsekai（新世界）桌宠助手**，并达成四件事：

1. **成功部署**：Shinsekai 程序可正常启动、长期稳定运行；
2. **桌宠开口说话**：接入 LLM 对话 + TTS 语音合成，角色能以语音形式主动开口；
3. **心跳陪伴自动检查**：基于自带的「心跳陪伴 Heartbeat Companion」插件，在空闲时自动触发检查节点；
4. **自动识屏**：到达检查节点时自动截屏，交由支持视觉的主模型识别用户正在做什么，并自然地搭话。

---

## 背景与环境

| 项 | 内容 |
|---|---|
| 上游项目 | [RachelForster/Shinsekai](https://github.com/RachelForster/Shinsekai) |
| 本地安装路径 | `H:\Program\新世界\Shinsekai`（Releases 整合包，自带 runtime Python 3.10） |
| 程序版本 | v2.3.1 |
| 角色配置 | 丛雨（Murasame，主用）、ALyCE |
| LLM | OpenAI 兼容端点（视觉能力模型，`data/config/api.yaml` 本地配置） |
| TTS | GPT-SoVITS v2pro（本地 bundle，`data/tts_bundles/installed/`），语音模型 丛雨 |
| 关键插件 | `shinsekai_heartbeat`（心跳陪伴）、`screen_state_companion-BYGPT`（识屏截图） |

⚠️ API Key 等敏感信息仅存于本地 `data/config/api.yaml`，**严禁**写入本仓库。

---

## 核心功能与技术方案

### 1. 部署与运行

- 整合包方式部署：`shinsekai.exe` + `runtime\pythonw.exe` 双进程；
- 启动入口：`shinsekai.exe`（设置中心 / 聊天主窗一体化启动）；
- 配置与数据均落在项目 `data/` 目录下，便于备份。

### 2. 桌宠开口说话（LLM + TTS）

- LLM：`data/config/api.yaml` 中配置 OpenAI 兼容供应商（已具备视觉能力，用于识屏）；
- TTS：GPT-SoVITS 本地 bundle，程序在需要合成时自动拉起 GPT-SoVITS API 服务（127.0.0.1:9880），使用 丛雨 语音模型（`data/models/Murasame/`）；
- 角色（丛雨）收到消息后：立绘联动 + 文字气泡 + TTS 语音朗读。

### 3. 心跳陪伴自动检查（shinsekai_heartbeat 插件）

- 空闲随机时长后触发检查节点（当前配置 5–60 分钟随机，可在插件设置页调整）；
- 每次节点按权重随机选择模式：识屏（50）/ 自言自语（25）/ 主动提问（25）；
- 用户发言、角色回复中、TTS 播放中不会插队打断；
- 可选学习监督模式（当前关闭；说「我要学习，请监督我」即开启 25 分钟专注监督）。

### 4. 自动识屏（screen_state_companion-BYGPT 插件）

- 该插件向主模型注册 `capture_screen` LLM 工具：截图 → 存入 `data/chat_attachments/screen-state-*` → 以图片附件形式送入下一轮对话；
- 心跳插件的提示词已配置「这时看看用户现在的屏幕，调用 capture_screen」，触发检查节点时主模型自行调用工具获取截图；
- 主模型（视觉模型）根据截图判断用户在做什么，并以角色身份自然开口；
- 截图不持久保存摘要，仅作为当轮对话附件。

### 工作链路

```
空闲到达检查节点（心跳调度）
  → 心跳插件发出主动消息（识屏/自言自语/提问）
  → 主模型按提示词调用 capture_screen 工具
  → 截图作为图片附件回传 → 主模型识屏判断用户行为
  → 角色以丛雨身份 + TTS 语音开口评论/关心
```

---

## 验收标准

### 1. 功能验收

- [x] Shinsekai 可正常启动运行（进程常驻，日志无致命错误）
- [x] 桌宠能用语音开口说话（TTS 派发成功，GPT-SoVITS 服务自动拉起，语音模型切换成功）
- [x] 心跳陪伴插件自动触发检查节点（日志多次 `heartbeat.emitted`）
- [x] 检查节点触发自动识屏（心跳触发后 `capture_screen` 被调用，生成截图附件，模型基于屏幕内容发言）
- [x] 用户主动说「看看我的屏幕」时也能调用识屏工具

### 2. 文档验收

- [x] 子项目 BRD.md（本文件）与 README.md 齐全
- [x] 根 CHANGELOG.md 记录立项与验证结论
- [x] Task.md 任务清单与实际完成度一致

### 3. 质量验收

- [x] 无敏感信息（API Key）提交到仓库
- [x] 无未说明的 TODO/FIXME 遗留
- [x] 依赖与环境在 README 中声明
- [x] 已知小问题（不影响功能）已在 BRD「已知问题」记录

### 4. 交接验收

- [x] 测试 Agent 在 CHANGELOG 中签字结论
- [x] 可选迭代项由用户决策：不做（2026-09-07 确认，仅维护现有功能）

---

## 已知问题（不影响核心功能）

1. **心跳调度日志噪音**：`heartbeat.scheduled` 每秒输出一行日志，导致 `logs/main.log` 增长较快（已 11MB）。属上游插件行为，不影响功能；如需处理可在下一轮迭代评估。
2. **Moondream Vision 插件未启用**：本地视觉方案（moondream2 模型）当前禁用且模型权重未下载。识屏现走「主模型视觉 + capture_screen」路线，效果依赖主模型视觉能力，已验证可用。如需离线识屏可后续启用（需下载约 1.7GB 模型）。
3. **学习监督模式默认关闭**：如需「监督我学习」功能，在插件设置或 `data/plugins/io.github.hard_to_tell.heartbeat_companion/config.json` 中开启 `study_supervision_enabled`。

---

## 不做的事情（边界）

- ❌ 不修改 Shinsekai 核心源码（纯配置 + 插件层面完成需求）
- ❌ 不在本仓库存储角色包、语音模型、聊天记录等大文件
- ❌ 不提交任何 API Key / 密钥
- ❌ 不做多角色同时识屏（当前仅丛雨主用）
