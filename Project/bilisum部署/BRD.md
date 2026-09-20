# BiliSum 部署 — 业务需求文档（BRD）

> 📅 立项：2026-09-17
> 👤 维护者：规划 Agent
> 🎯 状态：部署已完成（自测通过），**待测试 Agent 正式验收**
> 🔗 上游项目：[lycohana/BiliSum](https://github.com/lycohana/BiliSum) · MIT License

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
