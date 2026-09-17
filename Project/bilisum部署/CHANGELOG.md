# 变更日志 (CHANGELOG) — bilisum部署

> 子项目自身的变更日志。平台级事项在根 `CHANGELOG.md`，两者各自保持 15 条上限，超出部分归档进同目录 `CHANGELOG.archive.md`。

---

## [2026-09-17] 规划 Agent — 追加桌面入口（用户要求「帮我放桌面」）

**完成的工作**：
- ✅ 在用户桌面放置自足启动入口 `BiliSum.bat`（本机桌面路径由注册表 `User Shell Folders` 读出 = `D:\SystemFiles\Desktop`）。
- ✅ 脚本逻辑：检测 `:3838` 是否已 LISTENING → 已在跑则只打开界面；否则用 `.venv\Scripts\pythonw.exe -m video_sum_service` 起服务再开界面；部署目录缺失时给出提示而非静默失败。
- ✅ **实测启动命令**：`pythonw.exe -m video_sum_service` 启动后 **3 秒内** `/health` 返回 200（`status:ok`、`runtime ready`、Python 3.13.14），`/` 返回 200。
- ⚠️ 未能创建正规 `.lnk` 快捷方式：`WScript.Shell` 的 COM 实例化被本机安全策略拦截（「COM object instantiation can run arbitrary code」），故改用 `.bat` 入口。
- ✅ 文档同步：README 补桌面入口说明、实测证据行与排查条目；本机改动登记追加该仓库外文件。

**修改的文件**：

- 新增（仓库外）：`D:\SystemFiles\Desktop\BiliSum.bat`
- 修改：`Project/bilisum部署/README.md`、`Project/bilisum部署/CHANGELOG.md`

**下一步建议**：

- 桌面入口已可用。若想要带 BiliSum 图标的正式快捷方式，需用户手动右键 `start-web.bat` →「发送到 → 桌面快捷方式」，或先放行 COM 策略。

## [2026-09-17] 规划 Agent — 新子项目立项并完成 BiliSum 部署

**背景**：用户指定「把 `lycohana/BiliSum` 部署到 `D:\Program` 并命名为 `bilisum`，同时按流程在 Project 下写文档」。子项目由用户发起，符合根 BRD「子项目立项流程」第 1 条。

**完成的工作**：

- ✅ 完成部署：源码 clone 至 `D:\Program\bilisum`，落在上游 **v1.21.1**（提交 `fc693b130c6317918ea8fc9143ea824bd21e2114`，2026-09-10）。
- ✅ 装好运行环境：`uv sync --all-packages` 装 33 个包（CPython 3.13.14）；`npm install --prefix apps/desktop` 装 534 个包。
- ✅ **排掉一个坑**：首次 `npm install` 后 `electron\dist\electron.exe` 缺失（postinstall 未落地），设 `ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/` 重跑 `electron/install.js` 补齐（42.3.3）。
- ✅ 构建前端：`npm run build` 全绿（typecheck + vite + tsc），产出 `apps\web\static\index.html`。
- ✅ 启动验证：后端正常监听 `http://127.0.0.1:3838`；`/health`、`/`、`/settings` 实测均返回 **200**。
- ✅ 新增两个启动脚本（非上游文件）：`start-web.bat`（推荐）、`start-desktop.bat`。
- ✅ 产出子项目文档四件：`BRD.md`（目标 / 关键路径 / 四类验收 / 风险表 6 条）、`README.md`（启动 / 首次配置 / 环境表 / 本机改动登记 / 排查速查）、`Task.md`（5 项待验收 + 3 项待办）、本文件。
- ✅ 更新根 `BRD.md` 候选清单与已立项说明；根 `CHANGELOG.md` 新增立项记录。

**修改的文件**：

- 新增：`Project/bilisum部署/BRD.md`、`README.md`、`Task.md`、`CHANGELOG.md`
- 修改：根 `BRD.md`（候选清单 + 已立项子项目说明）、根 `CHANGELOG.md`（立项记录）

**仓库外的改动（不在本仓库交付范围内）**：

- `D:\Program\bilisum`：clone 上游仓库 + `.venv` + `apps\desktop\node_modules` + `apps\web\static` + **新增 `start-web.bat` / `start-desktop.bat`**。
- **未改动上游任何源码**；`C:\Users\WindoseII\AppData\Local\bilisum\data`（运行数据）未入库。
- 说明：本轮属环境部署与运维，未编写功能代码；按用户直接指派执行。

**当前状态**：

- ✅ 网页版可用（服务 + 前端 + 静态资源齐备，实测 200）。
- ⏳ **未验证项**（已列入 `Task.md` 任务 3/4/5，不得用构建证据代替）：桌面版窗口实际拉起、设置持久化、真实视频端到端。
- ⚠️ 已知缺口：`.venv` 内无 torch → 本地 Whisper / FunASR / 本地 Embedding 不可用；需用在线 ASR，或在设置页按需安装本地运行时（`Task.md` 任务 6）。

**下一步建议**：

1. 用户先在设置页配置 **LLM + ASR**（可复用 AstrBot 的 `rkapi.com` 中转 Key），跑通一条真实视频。
2. 测试 Agent 按 `BRD.md`「五、验收标准」逐项复验，重点补**桌面版窗口**与**端到端**两项。
3. 决定是否安装本地 ASR 运行时（`Task.md` 任务 6）。
