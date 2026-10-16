# BiliSum 部署 — 业务需求文档（BRD）

> 📅 立项：2026-09-17
> 👤 维护者：规划 Agent
> 🎯 状态：**在用（官方安装版）**，2026-09-21 曾搁置，用户已自行装回并实际使用
> 🔗 上游项目：[lycohana/BiliSum](https://github.com/lycohana/BiliSum) · MIT License

> ⚠️ **勘误（2026-10-17 本机实测）——先读这段再看下文**
> 1. **本机跑的不是源码部署，是官方安装版**。`H:\Program\bilisum\` 现为安装版 Electron 应用（`BiliSum.exe` + `resources/app.asar` + 内置后端），**没有 `.venv` / `apps/` / `packages/`**。
> 2. 因此下文 **§三 部署形态、§四 关键路径、§六 环境事实**中所有「源码部署 / `.venv` / `start-web.bat` / `start-desktop.bat`」类描述均为**旧机事实，在本机不成立**；原样保留仅作历史。
> 3. 本机实际形态与可改路径见 **§十**。
> 4. 数据目录仍为 `C:\Users\Unbox\AppData\Local\bilisum\data`（含 `settings.json` / `video_sum.db`），地址未变。

---

## 一、目标

把开源项目 **BiliSum** 部署到本机 `H:\Program\bilisum`，让用户能长期使用「B 站/YouTube 视频 → 转写 → 摘要 → 图文笔记 → 知识库问答」的本地优先工具链。

本项目**不开发功能**，只负责部署、启动与运维；全部功能来自上游，不在本仓库复制源码。

---

## 二、上游项目速览

| 项 | 值 |
|---|---|
| 仓库 | `https://github.com/lycohana/BiliSum` |
| 默认分支 | `master` |
| 部署版本 | **v1.21.1** |
| 部署提交 | `fc693b130c6317918ea8fc9143ea824bd21e2114`（2026-09-10 18:45:41 +0800，`chore(release): v1.21.1`） |
| 许可证 | MIT |
| 技术栈 | Electron + React + Vite（桌面端）/ FastAPI + SQLite（后端）/ yt-dlp + ffmpeg（取流） |

**核心能力**（上游提供，本次不改造）：

```
B站 / YouTube / 本地视频  →  转写  →  文本笔记  →  图文笔记  →  思维导图  →  知识库 RAG
```

- B 站 / YouTube / 本地视频（mp4 / mkv / mov / webm）导入
- 转写：SiliconFlow ASR / 多模态 ASR / 本地 Whisper / FunASR（后两者需额外运行时）
- 结构化摘要、章节时间轴、转写全文、知识笔记、思维导图
- 知识库：跨视频语义检索 + 关键词检索 + RAG 问答 + 标签网络
- 导出 Markdown / Obsidian，可打包笔记与截图
- B 站扫码登录（桌面端内置），应对风控

---

## 三、部署形态

**两种入口，共用同一个后端、同一份数据**：

| 形态 | 入口 | 启动方式 |
|---|---|---|
| **网页版（默认）** | 浏览器打开 `http://127.0.0.1:3838` | 双击 `H:\Program\bilisum\start-web.bat` |
| 桌面版（Electron） | 独立应用窗口 | 双击 `H:\Program\bilisum\start-desktop.bat` |

- 后端**固定监听 `127.0.0.1:3838`**（`packages/infra/src/video_sum_infra/config.py` 中 `port: int = 3838`），只绑定回环地址，不对局域网/公网暴露。
- 网页版与桌面版**不要同时全量启动**：桌面端会自动拉起自己的后端进程；端口被占用时 Electron 会走 `probeBackendPortBusy` 分支。日常二选一即可。
- 后端自带前端静态目录（`apps/web/static`），因此网页版不需要单独的 Web 服务器。

---

## 四、关键路径（本机实测）

| 项 | 位置 / 值 |
|---|---|
| 部署根目录 | `H:\Program\bilisum` |
| Python 虚拟环境 | `H:\Program\bilisum\.venv`（CPython **3.13.14**，由 uv 创建） |
| 后端入口 | `.venv\Scripts\video-sum-service.exe`（等价 `python -m video_sum_service`） |
| 桌面端依赖 | `apps\desktop\node_modules`（Electron **42.3.3**） |
| 前端产物 | `apps\web\static\index.html`（由 `npm run build:web` 生成） |
| **运行数据目录** | `C:\Users\Unbox\AppData\Local\bilisum\data`（**在仓库外**） |
| 数据库 | `…\AppData\Local\bilisum\data\video_sum.db`（SQLite） |
| 服务健康检查 | `http://127.0.0.1:3838/health`（免认证） |

⚠️ **数据目录含个人笔记、知识库索引与 API 凭据，严禁提交仓库、严禁上传。**

---

## 五、验收标准

### 1. 功能验收（测试 Agent 逐项核对）

- [ ] 双击 `start-web.bat` 后，浏览器能自动打开 `http://127.0.0.1:3838` 并显示 BiliSum 界面（非空白、非 404）
- [ ] `http://127.0.0.1:3838/health` 返回 HTTP 200，且 JSON 中 `version` 为 `1.21.1`
- [ ] `/settings`、`/knowledge` 页面能正常渲染（SPA 路由回退正常）
- [ ] 设置页能保存一组 LLM / ASR 配置并持久化（重启服务后仍在）
- [ ] 双击 `start-desktop.bat` 能拉起 Electron 窗口，且窗口内能连上后端（状态不再是「连接中」）
- [ ] 导入一条真实视频链接能走完「转写 → 摘要」流程（**需用户提供可用 API Key**）
- [ ] 手动退出后再次启动不报端口占用错误

### 2. 文档验收

- [ ] `Project/bilisum部署/` 下 BRD / README / Task / CHANGELOG 四件齐全
- [ ] README 的路径、端口、启动方式与实际一致
- [ ] 根 CHANGELOG 有立项记录

### 3. 质量验收

- [ ] 仓库内**无任何 API Key / token / 密码**；`AppData\Local\bilisum\data` 未入库
- [ ] 未修改上游 `H:\Program\bilisum` 内的源码（新增的 `start-web.bat` / `start-desktop.bat` 除外）
- [ ] `git status` 干净，无未推送提交

### 4. 交接验收

- [ ] 测试 Agent 在 `CHANGELOG.md` 明确记录结论；未通过则出 Bug 清单打回

---

## 六、已确认的环境事实（2026-09-17 部署实测）

| 事实 | 证据 |
|---|---|
| 源码 clone 成功 | 416 个提交，413 个文件落地，`git describe` = `v1.21.1` |
| Python 依赖装好 | `uv sync --all-packages` 装 33 个包；`video-sum-core/-infra/-service` 三个本地包均以 editable 方式构建成功 |
| 桌面端依赖装好 | `npm install` 装 534 个包 |
| **Electron 二进制需补装** | 首次 `npm install` 后 `electron\dist\electron.exe` **不存在**（postinstall 未落地）；用 `ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/` 重跑 `electron/install.js` 后到位（42.3.3） |
| 前端可构建 | `npm run build` 全绿：typecheck + vite build + tsc 均通过，产出 `apps/web/static/index.html`（1,685 B） |
| 后端可启动 | `/health` 返回 200；日志 `Uvicorn running on http://127.0.0.1:3838` |
| Web UI 可访问 | `/`、`/settings` 均返回 200 `text/html` |
| **本地 ASR 未就绪** | 服务日志 `probe debug channel=base torch=False funasr=False` → 本地 Whisper / FunASR / 本地 embedding **当前不可用**（见「七、风险与缺口」） |

---

## 七、边界与不做的事

- ❌ **不修改上游源码**。上游目录是 `git clone` 的独立仓库，本仓库只放文档；如需改动，另行立项并登记「本机改动」。
- ❌ **不参与上游版本迭代**。升级要用户明确要求后再做，升级前须备份 `AppData\Local\bilisum\data`。
- ❌ **不提交任何凭据**。API Key 只存在本机设置页 / 数据目录。
- ❌ **不把数据目录纳入仓库**。它是用户资产，路径写在文档里即可。
- ❌ **不擅自清理**。任何删除、移动、改名动作（含 `.venv`、`node_modules`、数据目录）必须先列清单并经用户明确同意。

---

## 八、风险与缺口

| # | 风险 / 缺口 | 影响 | 建议动作 | 状态 |
|---|---|---|---|---|
| 1 | **本地 ASR 缺 torch** | 本地 Whisper、FunASR、本地 Embedding 不可用 | 二选一：① 用在线 ASR（SiliconFlow 等）+ 在线 Embedding，无需 torch；② 在设置页按需安装本地运行时（体积数 GB） | 待用户决定 |
| 2 | **必须配置 LLM / ASR 才能出摘要** | 界面能打开，但不出结果 | 首次使用按 README「首次配置」填一组 LLM（OpenAI 兼容端点）与一个 ASR 服务 | 待用户操作 |
| 3 | Electron 二进制依赖镜像 | 换机重装时若走官方源可能再次缺失 | 重装时设 `ELECTRON_MIRROR` 到 npmmirror，或沿用本次排障步骤 | 已解决（有解法） |
| 4 | Python 版本为 3.13 而非上游 CI 的 3.12 | 理论上存在兼容差异 | 实测基础依赖全部装好并通过构建；若后续遇到 3.13 特有的依赖问题，可重建 3.12 环境（`uv sync --python 3.12`） | 观察中 |
| 5 | 桌面版与网页版共用 3838 端口 | 同时启动会端口冲突 | 日常只用一种形态；网页版更适合常驻 | 使用约定 |
| 6 | 上游为活跃项目（593 star / 周更） | 本地版本会逐渐落后 | 需要新功能时再评估升级；不自动跟 | 接受 |

---

## 九、下一步

1. 用户在设置页配置 **LLM + ASR**，跑通一条真实视频
2. 测试 Agent 按「五、验收标准」逐项验收，在 `Task.md` 勾 `[x]` 或出 Bug 清单
3. 决定是否安装本地 ASR 运行时（风险 1）

---

## 十、需求追加（2026-10-17）：外语（日语）视频转写中文化

### 10.1 用户原话

> 「能在语音转文字阶段转写日语变成中文，然后进入正常总结流程」
> 「他现在反正是把日语当成中文在乱总结」

触发场景：B 站日语视频（例：`【完整版】看完这个视频，不要再说不会画可爱眼睛了`，时长 15:27）走完流程后，摘要与知识卡片失真。

### 10.2 本机形态与可改路径（2026-10-17 实测）

| 项 | 实测值 |
|---|---|
| 应用根 | `H:\Program\bilisum\`（官方安装版 v1.21.1） |
| 前端 | `resources\app.asar`（Electron，37 MB） |
| 后端启动器 | `resources\backend\BiliSum\BiliSum.exe`（PyInstaller onedir） |
| **后端源码** | `…\BiliSum\_internal\runtime\base\Lib\site-packages\{video_sum_core,video_sum_service,video_sum_infra}\**\*.py` |
| 后端运行时 | **便携式 CPython 3.12.10**（`…\runtime\base\python.exe`，`python312._pth`） |
| 数据目录 | `C:\Users\Unbox\AppData\Local\bilisum\data`（`settings.json` / `video_sum.db`） |

🔑 **关键结论**：后端是**未加密的明文 `.py`** + 便携 CPython，**可以就地打补丁**，改完删掉同名 `__pycache__` 重启即可生效，**不需要重新 clone / 构建 / 打包**。
⚠️ 前端在 `app.asar` 内，改 UI 需拆包重打包 → **方案设计上应尽量复用已有界面元素，避免动前端**。

### 10.3 现状诊断（"把日语当中文乱总结"的四个成因）

| # | 成因 | 证据 |
|---|---|---|
| 1 | **ASR 模型选错**。本机 `siliconflow_asr_model = TeleAI/TeleSpeechASR`，该模型面向中文与中文方言，遇日语只能按中文音近字硬猜 → 转写即乱码 | 本机 `settings.json` |
| 2 | **本地 Whisper 路径语言硬编码** | `packages/core/src/video_sum_core/transcribe_subprocess.py:71` → `model.transcribe(..., language="zh", ...)` |
| 3 | **多模态 ASR 提示词硬编码"保持原文"**，明确不翻译 | `pipeline/real.py` `_transcribe_with_multimodal` → `_send_audio_chunk` 内 `"请转录这段音频的全部文字内容，保持原文，不要修改"` |
| 4 | **「输出语言」是死旋钮**。设置页有「中文 / English / 日本語」下拉，但全仓**无任何代码读取它** | `settings_manager.py:88` 仅声明；`runtime_support.py:2230` 仅透传；`pipeline/real.py` 全篇无引用 |

补充事实：**「优先使用 UP 字幕」默认开启**（`prefer_bilibili_subtitle=True`）。视频若带 UP 上传字幕，会跳过 ASR 直接采用字幕原文（`real.py:549`）。日语视频若拿到日语 CC，转写全文即日语；若拿到 B 站中文 AI 字幕，则直接是中文。**这条路径不受 ASR 设置影响**，方案必须一并考虑。

### 10.4 上游能力边界（2026-10-17 核实）

- 上游**最新版即 v1.21.1**（与本机同版本），**没有更新的修复可用**；仓库内检索「日语 / japanese / translate / 翻译」无相关实现，也**无相关 issue 或 PR**。
- SiliconFlow `/audio/transcriptions` 接口**只接受「音频文件 + 模型名」两个请求字段**，不提供 `language`、`prompt` 等参数 → **无法通过传参让它直接输出中文**。
- SiliconFlow 的 `FunAudioLLM/SenseVoiceSmall` 支持中/粤/英/**日**/韩多语种且自带语种识别 → **能正确转写日语，但输出仍是日语**。
- 结论：**要"转写阶段直接出中文"，只能改代码**；纯改配置最多做到"日语正确转写 + 中文摘要"。

### 10.5 候选方案

**方案 A（推荐 · 达标）——转写后接一步"归一化翻译"**

在转写产出之后、摘要之前，插一个语言归一化步骤：检测转录文本语种，与「输出语言」不一致时调用现有 LLM 通道整段翻译，保留 `segments` 时间戳后回到原流程。

- 改动点：`packages/core/src/video_sum_core/pipeline/real.py`（新增归一化方法 + 在各 `_transcribe*` 出口调用）；`transcribe_subprocess.py:71` 的硬编码语言改为可配置或改为自动识别。
- 设置项：**直接接线已存在的 `输出语言`（`language`）** → **前端零改动**，用户本就在设置页选「中文」。
- 规模：单文件为主，约 30–80 行。
- 覆盖：在线 ASR、本地 Whisper、多模态三条路径的出口统一生效；UP 字幕路径同样纳入。
- 代价：多一次 LLM 调用（整篇翻译，长视频 token 成本可观，建议分段 + 复用已有分段重试机制）。

**方案 B（可选 · 治本）——多模态 ASR 提示词改为可配置**

把 `_send_audio_chunk` 里硬编码的提示词改为读设置（新增字段，默认沿用现文案），再把「多模态 ASR」的 `base_url` 指向支持 `input_audio` 的 OpenAI 兼容端点 + omni 模型，提示词写「把音频内容翻译成简体中文」。

- 优点：一次调用同时完成"听 + 译"，最贴合"转写阶段变中文"。
- 代价：需自备支持音频输入的中转端点；仍需改代码；与 UP 字幕路径无关。

**方案 C（止血 · 零代码，可立即试）** —— 不改任何代码，靠配置与提示词：

1. ASR 模型由 `TeleAI/TeleSpeechASR` 换成 `FunAudioLLM/SenseVoiceSmall` → **止住"日语被当中文乱转"**，转写恢复为准确的日语。
2. 在设置页「提示词」把 `摘要系统提示词 / 用户提示词模板` 增补一句：**"若转写原文为日语等外语，先准确翻译为简体中文，再输出中文摘要；不得音译或臆造。"** → 摘要、知识卡片、思维导图产出准确中文。
3. 需要时关闭「优先使用 UP 字幕」，避免日语 CC 直接进流程（或反向利用：有中文 CC 时留着更快）。

- 局限：**视频详情页的「转写全文」仍是日语**，未满足"转写阶段即中文"的字面要求。
- 定位：今天就能验证效果，用来判断"乱总结"是否真的由此而来。

> 📌 **推荐组合**：**先做 C 止血并验证**，同轮把 **A** 排给开发 Agent 做达标。方案 B 延期，触发条件：用户手上有稳定的音频输入中转端点，且不希望承担额外翻译调用的 token 成本。

### 10.6 验收标准（追加）

- [ ] 导入一条**纯日语、无中文字幕**的 B 站视频，走完整流程后，「转写全文」为**通顺简体中文**（非音近乱码、非日语原文）
- [ ] 摘要 / 知识卡片 / 思维导图内容与日语原意一致，无编造（测试 Agent 需人工抽检 ≥ 3 处要点）
- [ ] 时间戳（`segments`）与译文对齐，章节时间轴不错位
- [ ] 中文视频回归：改动后原中文视频流程不劣化（转写不被误翻译、多耗时不明显）
- [ ] 关闭该功能时，行为与 v1.21.1 现状一致（可回退）

### 10.7 边界

- 本项**已突破 §七「不修改上游源码」的原有边界** → 按 §七 约定**登记为「本机改动」**：需在 `README.md` 记录改动的文件、原因、升级时的回归风险（上游升级会覆盖 `site-packages`，补丁需重打）。
- 补丁**只改 `H:\Program\bilisum` 内已安装的文件**，改前先备份原文件；**不动** `AppData\Local\bilisum\data` 内的用户数据。
- 凭据、翻译调用产生的费用由用户承担 → 是否开启由用户在设置页决定。
