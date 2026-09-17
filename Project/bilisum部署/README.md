# bilisum部署 使用说明

> BiliSum —— 把 B 站 / YouTube / 本地视频变成转写、摘要、图文笔记、思维导图和可检索知识库。数据全部留在本机。

---

## 一、怎么启动（最常用）

**桌面有个 `BiliSum` 图标，双击它就完事** —— 它会自动把服务起好并打开界面（服务已经在跑时只开界面，不会重复启动）。

想换个地方点，也可以去 `D:\Program\bilisum\` 双击：

| 双击这个 | 会怎样 |
|---|---|
| **`start-web.bat`** | 后台起服务，浏览器自动打开 `http://127.0.0.1:3838` —— **推荐日常用这个** |
| `start-desktop.bat` | 开一个独立应用窗口（Electron，内置 B 站扫码登录） |

两种方式用的是**同一个后端、同一份数据**，所以笔记和知识库是通的。**同一个时刻只用一种即可**（都占 3838 端口）。

**怎么关**：网页版关掉「BiliSum backend」那个 python 进程即可（任务管理器里找 `pythonw.exe`，或直接重启电脑）。桌面版关窗口就结束了。

---

## 二、第一次用必须先配置（不然出不了结果）

打开界面后进 **设置页**，至少填两组东西：

1. **LLM**（总结、笔记、问答都要它）
   —— 任何 OpenAI 兼容端点都行：填 `Base URL` + `API Key` + 模型名。
   你机器上的 AstrBot 用的是 `rkapi.com` 中转站，同一个 Key 通常可以直接拿来用。
2. **转写服务（ASR）**
   —— 建议先用**在线**的（如 SiliconFlow ASR），不用装几个 GB 的本地模型。
   —— 本地 Whisper / FunASR **当前不可用**（没装 torch，见下方「已知缺口」）。

可选：知识库的 Embedding、图文笔记的视觉模型（VLM），在设置页按需配。

> 💡 配置只存在本机数据目录，不会上传，也不会进 Git。

---

## 三、环境与依赖

**项目管理仓库**：[SSaans/AllAgentBASE](https://github.com/SSaans/AllAgentBASE)，本地工作区 `D:\Project\AllAgentBASE`（**唯一权威**）。
下面是 BiliSum **实际运行**的位置（全部在仓库外，不属于本仓库交付物）。

| 项 | 位置 / 说明 |
|---|---|
| 部署根目录 | `D:\Program\bilisum`（上游 `git clone`，独立仓库） |
| 上游来源 | `https://github.com/lycohana/BiliSum`，分支 `master` |
| 版本 | **v1.21.1**（提交 `fc693b1`，2026-09-10） |
| Python 环境 | 根目录 `.venv`（**CPython 3.13.14**，uv 管理，33 个包） |
| 桌面端依赖 | `apps\desktop\node_modules`（534 个包，Electron 42.3.3） |
| 前端产物 | `apps\web\static\`（由 `npm run build:web` 生成，后端直接对外提供） |
| **服务地址** | `http://127.0.0.1:3838`（只绑本机回环，外网访问不到） |
| **数据目录** | `C:\Users\WindoseII\AppData\Local\bilisum\data` ← **你的笔记、知识库、配置都在这** |
| 数据库 | `…\data\video_sum.db` |
| 启动脚本（我加的） | `start-web.bat`、`start-desktop.bat` |

**手动启动（不用脚本时）**：

```powershell
cd D:\Program\bilisum
.\.venv\Scripts\video-sum-service.exe        # 后端，前台运行，Ctrl+C 停止
```

**改完代码后要重新构建前端**：

```powershell
cd D:\Program\bilisum
npm run build:web        # 更新 apps\web\static
```

---

## 四、怎么用

| 想干的事 | 怎么做 |
|---|---|
| 总结一条 B 站视频 | 首页粘贴链接 → 建任务 → 等转写+摘要完成 |
| 批量处理合集 / 多 P | 粘贴合集链接，按合集会话批量跑 |
| 处理本地视频 | 导入 mp4 / mkv / mov / webm |
| 看笔记 | 视频详情页 → 文本笔记 / 图文笔记 / 思维导图 |
| 导出 | 导出 Markdown 或 Obsidian 格式（可打包笔记+截图） |
| 跨视频提问 | 「知识库」页检索或直接问答 |
| 应对 B 站风控 | 用**桌面版**里的扫码登录 |
| 命令行用 | 上游另有 `npm install -g bilisum` 的 CLI，本次**没装** |

---

## 五、已知缺口

| 缺口 | 说明 | 要怎么办 |
|---|---|---|
| **本地 ASR 不可用** | 服务日志实测 `torch=False funasr=False` → 本地 Whisper、FunASR、本地 Embedding 都跑不了 | 用在线 ASR；或按需在设置页安装本地运行时（体积数 GB，首次很慢） |
| 还没配任何 Key | 界面能开，但不出摘要 | 见「二、第一次用必须先配置」 |
| 没做开机自启 | 每次要手动双击 | 需要的话可以加，但没有自动加 |

---

## 六、本机改动登记（2026-09-17 部署）

**在 `D:\Program\bilisum` 里我做了什么**（该目录是独立的上游仓库）：

- `git clone` 上游 `master`，落在 v1.21.1，**未改动任何上游源码**。
- 新建 `.venv`（uv sync，Python 3.13.14，33 包）。
- `npm install --prefix apps/desktop`（534 包）。
- **补装 Electron 二进制**：首次装完 `electron\dist\electron.exe` 缺失（postinstall 没落地），用镜像重跑 `node install.js` 补齐 → 版本 42.3.3。
- `npm run build` 构建前端 → 生成 `apps\web\static\index.html`。
- **新增两个启动脚本**（非上游文件，位于 `D:\Program\bilisum\`）：`start-web.bat`、`start-desktop.bat`。
- **新增桌面入口**（仓库外文件，2026-09-17 追加）：`BiliSum.bat` 放在用户桌面（本机桌面路径经注册表 `User Shell Folders` 读出为 `D:\SystemFiles\Desktop`）。脚本先检测 `:3838` 是否已监听 → 在跑就直接开界面，否则用 `.venv\Scripts\pythonw.exe -m video_sum_service` 起服务再开界面；部署目录被移动时会提示而不是静默失败。

**没做的事**：

- 没改上游任何 `.py` / `.ts` / 配置文件。
- 没装 `npm install -g bilisum`（全局 CLI）。
- 没装 torch / FunASR / 本地模型。
- 没动系统环境变量、没设开机自启、没开防火墙端口。

**验证证据**（2026-09-17 实测）：

| 项 | 结果 |
|---|---|
| `uv sync --all-packages` | 成功，33 包（core / infra / service 三个本地包均构建成功） |
| `npm install` | 成功，534 包 |
| `npm run build` | 成功（typecheck + vite + tsc 全绿） |
| 启动后端 | 成功，日志 `Uvicorn running on http://127.0.0.1:3838` |
| 桌面入口的启动命令 | 成功：`pythonw.exe -m video_sum_service` 启动后 **3 秒内** `/health` 返回 200（`status:ok`、`runtime ready`、Python 3.13.14）；`/` 返回 200 |
| `GET /health` | **200**，`{"service":"BiliSum","version":"1.21.1", …}` |
| `GET /` | **200**，`text/html`，1,685 B |
| `GET /settings` | **200**，`text/html` |

---

## 七、自测与正式验收

**本轮属于「部署 Agent 自测」**：证明的是**服务起得来、界面打得开、构建过得去**。

⚠️ **源码自测 ≠ 验收**。以下必须另测，不能用上面的证据代替：

- 真实视频能否走完「转写 → 摘要」（需要配好 Key）
- 设置页保存是否重启后仍生效
- 桌面版窗口能否真正连上后端
- 导入导出、知识库问答的实际效果

**只有测试 Agent 能勾 `[x]`。** 验收标准见同目录 `BRD.md`「五、验收标准」，任务明细见 `Task.md`。

---

## 八、排查速查

| 现象 | 原因 / 处理 |
|---|---|
| 浏览器打不开 3838 | 后端没起来。看任务管理器有没有 `pythonw.exe`；手动前台跑 `video-sum-service.exe` 看报错 |
| 端口被占用 | 网页版和桌面版同时开了，或者旧进程没退干净。关掉多余的再启 |
| 界面能开、点了没反应 | 十有八九是**没配 LLM / ASR**，或 Key 无效 |
| 桌面版白屏 | 前端产物缺失，跑一次 `npm run build:web` |
| 想重装桌面端依赖 | 记得设 `ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/`，否则 Electron 二进制可能又缺失 |
| 数据想备份 | 直接复制整个 `C:\Users\WindoseII\AppData\Local\bilisum\data` |
| 桌面 `BiliSum` 双击没反应 | 看它是不是还提示「folder missing」——那说明 `D:\Program\bilisum` 被挪走或删了，把目录放回去即可 |

---

## 九、详细需求

见同目录 `BRD.md`（部署目标 / 关键路径 / 验收标准 / 风险表），任务看板见 `Task.md`。
