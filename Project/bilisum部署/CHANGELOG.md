# 变更日志 (CHANGELOG) — bilisum部署

> 子项目自身的变更日志。平台级事项在根 `CHANGELOG.md`，两者各自保持 15 条上限，超出部分归档进同目录 `CHANGELOG.archive.md`。

---

## [2026-09-17] 规划 Agent — 桌面入口改为原生应用窗口（用户要求「免密、不要浏览器」）

**背景**：用户双击桌面图标后仍被浏览器打开并要求输入访问密钥，明确要求「弄免密、老子不想浏览器打开」。

**完成的工作**：
- ✅ 新增极简 Electron 壳 `desktop-shell/`（`main.js` + `package.json`）：读 `auth.json` 的 `access_token` → 写入 Electron session 的 `bilisum_session` cookie → 在**独立应用窗口**（无菜单栏、带 BiliSum 图标、关窗即退）加载 `http://127.0.0.1:3838`。
- ✅ `launch.pyw` 改为启动 Electron 壳，不再调用 `webbrowser`。
- ✅ **免密机制实测通过**：`/api/v1/settings` 无凭据 → `401`；带 `bilisum_session` cookie → **`200`**；带 bearer → `200`。
- ✅ **定位并解决一个真坑**：环境变量 `ELECTRON_RUN_AS_NODE=1` 会让 `electron.exe` 退化成纯 Node 进程、报 `Cannot find module 'electron'`，窗口起不来。清理该变量后 Electron 正常启动（实测 4 个进程：主 + GPU + 渲染 + 工具，`electron=42.3.3 / chrome=148`）。`launch.pyw` 启动前已强制清理。
- ✅ README 同步：启动章节、本机改动登记（新增桌面壳说明）、排查表新增 2 条。

**修改的文件**：
- 新增（仓库外）：`D:\Program\bilisum\desktop-shell\main.js`、`D:\Program\bilisum\desktop-shell\package.json`
- 修改（仓库外）：`D:\Program\bilisum\launch.pyw`
- 修改：`Project/bilisum部署/README.md`、`Project/bilisum部署/CHANGELOG.md`

**当前状态**：
- ✅ 后端就绪、cookie 免密、Electron 可启动，三项均已实测。
- ⏳ **窗口可见性未在本机沙箱内验证**（沙箱回收子进程 / 权限被拒），需用户双击实测确认。

**下一步建议**：
- 用户双击桌面 `BiliSum`：应直接弹出应用窗口且不要求密钥。若异常，查 `%LOCALAPPDATA%\bilisum\launch.log`。
- `start-web.bat` 保留作为**浏览器版**备用（如需要多标签、跨设备访问时用）。

## [2026-09-17] 规划 Agent — 补上「访问密钥」说明（用户首次打开网页版被拦）

**背景**：用户双击桌面图标成功打开界面，但被「输入访问密钥」拦下，误以为是要填模型 API Key。原 README 漏了这一道门。

**完成的工作**：
- ✅ 定位机制（`apps/service/src/video_sum_service/auth.py`）：密钥优先读环境变量 `VIDEO_SUM_ACCESS_TOKEN`，否则读 `data\auth.json` 的 `access_token`，不存在则随机生成；校验通过后写 `bilisum_session` cookie（30 天）。
- ✅ **实测验证**：`/api/v1/settings` 不带密钥 → `401 需要输入 BiliSum 访问密钥`；带密钥 → `200`（14,747 B）。密钥文件存在且有效。
- ✅ README 新增「二、第一次用要过两道门」：第一道=访问密钥（说明它与模型 Key 无关、密钥位置、输一次管 30 天、桌面版免密、如何更换）；第二道=配 LLM / ASR。排查表补一条。
- ✅ 文档**只写密钥文件路径，不记录密钥内容**。

**修改的文件**：
- 修改：`Project/bilisum部署/README.md`、`Project/bilisum部署/CHANGELOG.md`

**下一步建议**：
- 用户在网页版粘贴密钥进入后，在设置页配置 LLM + ASR 才能真正出摘要。
- 若希望网页版也免密，可考虑让启动器把密钥注入浏览器 cookie（需另立任务），或直接用桌面版。

## [2026-09-17] 规划 Agent — 桌面入口升级为带图标的快捷方式（用户要求「弄个图标、后缀去掉、像个应用」）

**完成的工作**：
- ✅ 桌面入口由 `.bat` 升级为 **`BiliSum.lnk` 快捷方式**：目标直指 `.venv\Scripts\pythonw.exe`，参数 `launch.pyw`，图标取自 `apps\desktop\build\icon.ico`（回读校验 target / args / workdir / icon 全部一致）。
- ✅ 新增无控制台启动器 `launch.pyw`：探 `/health` → 未就绪则 detached 拉起后端（最多等 30 秒）→ 打开 `http://127.0.0.1:3838`；日志落 `%LOCALAPPDATA%\bilisum\launch.log`。
- ✅ 关键设计取舍：**不经 cmd / bat / wscript**，直接以 pythonw 为快捷方式目标 —— 该调用路径已实测可用（3 秒内 `/health` 返回 200）；而 `cmd /c bat`、`wscript + vbs`、`os.startfile(bat)` 三种「脚本链」方式在本机沙箱内均无法拉起后端，故弃用。
- ⚠️ **改动了系统设置**：`HKCU\...\Explorer\Advanced\HideFileExt` 由 `0` → **`1`**，使桌面显示 `BiliSum` 而非 `BiliSum.lnk`（用户明确要求「后缀去掉」）。**可逆**：设回 `0` 即恢复。
- ✅ 桌面原有的 `BiliSum.bat` 已移入回收站（功能重复，可还原）。
- ✅ README 同步更新：启动章节、本机改动登记、排查条目。

**修改的文件**：
- 新增（仓库外）：`D:\SystemFiles\Desktop\BiliSum.lnk`、`D:\Program\bilisum\launch.pyw`
- 修改：`Project/bilisum部署/README.md`、`Project/bilisum部署/CHANGELOG.md`
- 涉及系统设置：`HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced\HideFileExt`

**当前状态**：
- ✅ 桌面 `BiliSum` 图标已就位（含图标、无后缀）。
- ⏳ **未端到端验证**：本机沙箱会阻断「由 shell / 脚本链派生进程」，因此没有在沙箱内完整跑通一次真实双击；已验证的是「工作目录 + pythonw -m video_sum_service」这条实际执行路径可用。**用户首次双击后请确认界面是否正常打开。**

**下一步建议**：
- 用户双击桌面 `BiliSum` 试一次；若未打开，查 `%LOCALAPPDATA%\bilisum\launch.log`。
- 若不想要全局隐藏扩展名，把 `HideFileExt` 设回 `0` 即可（不影响快捷方式本身）。

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
