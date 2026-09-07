# 交接任务：修复桌宠识屏误判（日语教材被识别成"数学题"）

> 📅 交接日期：2026-09-07
> 👤 交接方：规划 Agent（byendcycle 委托）
> 👥 接收方：shinsekai 项目开发 Agent
> ℹ️ 这是用户明确点名的优先级任务，用户已体验到多次误判，体验很差。

---

## 一、问题现象

桌宠（丛雨）自动识屏**反复把屏幕上的日语教材练习题误判成"数学题"**，并会基于错误判断吐槽用户（"主人不是说要学日语吗，怎么在看数学/分数"）。用户已被说了 3 次，非常不满。

**典型案例（用户两次上传截图确认）**：
- 屏幕实际内容：《新标准日本语》第2单元"单元末练习"——日语助词填空、词语选择，含大量`（ ）`、`①②③④`、分值、例句，无任何数学运算。
- 桌宠判断："这是数学教材，是关于分数的内容"。

## 二、已完成的排查（规划 Agent）

### 已确认的事实
| 项 | 值 |
|---|---|
| 识屏链路插件 | `screen_state_companion-BYGPT`（提供 `capture_screen` 工具） |
| 识屏触发 | 心跳插件提示词 → 主模型调用 `capture_screen` → 截图作为图片附件送入下一轮 |
| 主模型 | **`claude-opus-5`**（OpenAI 兼容端点 `rkapi.com/v1`，见 `data/config/api.yaml`） |
| 本地视觉 | `moondream_vision` 插件处于 **`enabled: false`**（见 `data/config/plugins.yaml`） |
| 插件代码位置 | `H:\Program\新世界\Shinsekai\plugins\screen_state_companion-BYGPT\` |

### 已做的一次无效尝试（关键教训）
规划 Agent 曾**只强化提示词**（`llm_tool.py` + `config.py` 默认 prompt，要求"先读内容、不要凭版式臆断、外语题不是数学题"），并同步了运行配置 `data/plugins/com.local.screen_state_companion/config.json`。

**结果：仍然误判。** 用户上传的第三张截图里，那段强化提示词已经以用户消息形式进入对话，主模型却**依旧**说"看到的是数学教材、分数内容"。

> ⚠️ **结论**：主模型 `claude-opus-5` 对这张图（日文假名 + 填空版式）的**视觉/OCR 读图判断就是错误的**，提示词无法纠正它。问题在"图像理解层"，不在提示词工程层。开发 Agent 不应再走"改提示词"路线。

## 三、原因诊断（开发方向建议）

误判发生在**主模型读图**这一环：截图被当作原生图片附件直接交给 `claude-opus-5`，模型把日文假名/填空版式当成分数符号。有三条可行的解决路径，供开发 Agent 评估采纳：

### 路径 A：启用 Moondream 本地视觉做前置定级（推荐优先评估）
- Moondream Vision 插件已存在且被心跳插件的 `vision.py` 引用（`moondream_query_screen` 工具）。
- 心跳插件里其实已有"用本地 Moondream 先看屏、再由文本规则分类 STUDY/DISTRACTED"的逻辑，说明**本地视觉识别更可靠的思路在项目里已有铺垫**。
- 让识屏走「Moondream 本地先读屏 → 输出文字摘要 → 主模型基于摘要发言」而非「截图原图直发主模型」。本地模型对文本/版式的判读通常比中转的 claude-opus 稳定。
- 需要：`plugins.yaml` 里把 `plugins.moondream_vision.plugin:MoondreamVisionPlugin` 设为 `true` + 下载模型权重（之前 BRD 记录约 1.7GB，需联网）。

### 路径 B：截图前先用 OCR 提取文字，把文字喂给主模型
- 在主模型发言前，对截图做 OCR（如 PaddleOCR/Tesseract），把识别出的文字作为附加上下文，让模型**先读文字再归类**，而非只凭图像语义。
- 需要额外引入 OCR 依赖，或在已有 runtime 里调用可用库。

### 路径 C：让模型先"描述画面文字"再"判断"
- 若坚持走主模型直读图，可在工具返回时追加结构化引导：强制模型先输出"画面中识别到的文字片段"，再据此判断题型（类似 chain-of-thought）。
- 风险：若模型底层 OCR 就错，此路径改善有限（见上一步尝试的教训）。仅作兜底。

## 四、期望交付

请开发 Agent 修复识屏精度，**验收标准**：
1. 对「日语/外语教材练习题」这类画面（题号+分值+括号填空+序号），桌宠**能识别出是语言练习题，不再误判为数学**。
2. 对「真数学题/真分数」画面，仍能正常识别为数学，**不因修复而误伤**。
3. 修复后可做一次端到端自测：触发识屏 → 桌宠基于屏幕实际内容自然搭话，判断正确。
4. 修复后更新该插件的 README 或相关文档，说明处理方式。

## 五、开发 Agent 注意事项

- **代码与配置位置**：`H:\Program\新世界\Shinsekai\plugins\screen_state_companion-BYGPT\`、`plugins\shinsekai_heartbeat\`、`data\plugins\com.local.screen_state_companion\config.json`、`data\config\plugins.yaml`。
- **改动后必须重启新世界桌宠程序**才能生效（当前进程 2026-09-07 23:52 启动）。
- 不要在 `CHANGELOG.md` 之外直接改规划 Agent 已写的 BRD/Task。
- 变更完成后，在本仓库 `CHANGELOG.md`（`H:\Program\AllAngelBASE\CHANGELOG.md`）顶部新增一条交接记录，写清：做了什么 / 改了哪些文件 / 下一步交给谁。

## 六、背景事实备份（勿删）

- 自动清理旧截图的改动也在同一批：`retention_days`（默认3天）+ `runtime.py::_cleanup_old_screenshots()`。这是**已完成且验证通过**的独立功能（清理 61 个老截图、释放约 78MB），不要回退。请开发 Agent 在修复识屏时一并保留此功能。