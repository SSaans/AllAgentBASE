# 开发 Agent 操作手册（DEVELOPMENT SOP）

> 🤖 适用于：开发 Agent (Development Agent)
> 📖 启动指令：「你是开发 Agent，根据 DEVELOPMENT.md 的要求，进行以下开发：<任务描述>」
> 🔗 配套文档：**AGENTS.md（Agent 行为规范入口 + skill 路由，开工前必读）**、BRD.md（需求真相来源）、Task.md（任务清单）

## 第零步：本机路径基线（2026-09-21 换机后，实测）

> 🔴 **换机事实**：旧机 `DESKTOP-VGJ8GGK` / 用户 `WindoseII` → 新机 `DESKTOP-JC65SRL` / 用户 `Unbox`。**旧文档里的 `D:\Project\...`、`D:\Program\...`、`D:\Test\...`、`C:\Users\WindoseII\...` 全部失效。**以下为本机实测基线，一切工作以此为准。

| 用途 | 旧机路径 | **本机实测路径** |
|------|----------|------------------|
| 仓库工作区 | `D:\Project\AllAgentBASE` | **`E:\AllAgentBASE`** |
| 外部项目根 | `D:\Program` | **`H:\Program`** |
| 工具 / 临时目录（仓库外） | `D:\Test` | `H:\Program\_wb` ✅ **已建立**（2026-09-21 换机后创建，探针 / 备份 / 临时脚本都放这里） |
| 仓库内临时脚本 | `D:\Project\AllAgentBASE\temp` | **`E:\AllAgentBASE\temp`**（已被 `.gitignore` 忽略） |
| 用户目录 | `C:\Users\WindoseII` | `C:\Users\Unbox` |
| Git | 系统 PortableGit | `H:\Program\Git\cmd\git.exe`；**本仓库提交身份已配好**（**仓库级** `SSaann` / `ssaann@example.com`；**全局未配**，在其他仓库里仍需显式传 `-c`） |
| Python（可用） | `C:\Users\WindoseII\AppData\Local\Programs\Python\Python313\python.exe` | 受管：`C:\Users\Unbox\.workbuddy\binaries\python\versions\3.13.12\python.exe`<br>⚠️ PATH 上的 `python` 是 WindowsApps 桩，**不可用** |
| 代理 | `127.0.0.1:7897` | 不变（注册表 `ProxyEnable=1` / `ProxyServer=127.0.0.1:7897`） |

**外部项目实测坐标**：`distilly` → `H:\Program\distilly` ✅ · `表情包同步` → `H:\Program\stickersync` ✅ · `ALLBot` → `H:\Program\AstrBot` ✅（实例 `C:\Users\Unbox\.astrbot_launcher\instances\4450a298-f4c2-43fa-b7f7-bd645b753fc3`，**UUID 未变**）· `shinsekai` → `H:\Program\新世界\Shinsekai` ✅（**路径未变**）· `bilisum` → ❌ **本机不存在，未迁移**

⚠️ **换机后旧 venv 一律失效**：venv 内的 `python.exe` 是绝对路径 shim，换机后指向不存在的旧机解释器（实测 `H:\Program\distilly\.venv` 报 `did not find executable at 'C:\Users\WindoseII\...'`）→ **凡 `.venv` 必须重建，不得直接复用。**

---

## 第一步：前置检查（全部通过才能开工）

- [ ] **已读 `AGENTS.md`（Agent 行为规范入口 + skill 路由）**，并按任务类型查阅了对应 skill 卡
- [ ] 已执行 `git pull`，与远程同步
- [ ] **工作区核对：当前目录必须是唯一权威工作区 `E:\AllAgentBASE`**（`git remote -v` 指向 `SSaans/AllAgentBASE`）；若在克隆副本里，先停下，把改动合并回主工作区（**删除副本须经用户明确同意**，不得自行处置）
- [ ] **交接证据三查**（接手前必做，防"证据留在别人本地"）：
  1. 远端是否有新提交：`git fetch origin && git log origin/main..HEAD`（看本地多出的未推送提交）
  2. 其他本地克隆是否有未提交改动：扫描本机是否又出现 `AllAgentBASE` 副本并查其 `git status`，如有则先合并（本机 2026-09-21 实测：权威工作区为 `E:\AllAgentBASE`；另发现一个**旧快照副本** `H:\Program\AllAngelBASE`（停在 09-16 提交 `386888f`，工作树干净、无独有提交），**待用户裁决处置，不得自行删除**）
  3. 运行目录实际配置与文档是否一致（配置档、进程、日志）
- [ ] 已通读 BRD.md（含子项目 BRD）
- [ ] 已读 CHANGELOG.md 最近 3 条记录
- [ ] 若存在 Task.md：确认任务范围，逐条实现
- [ ] 若不存在 Task.md：确认 BRD 需求足够明确；**不明确就交回规划 Agent，不许猜**
- [ ] 开发环境就绪（语言运行时、包管理器可用）

## 第二步：开发

1. 开工时把本次要做的任务在 Task.md 中标记为「修复中」
2. 按 Task.md 逐条实现；完成一条并自测通过后改为「待复验」（等测试 Agent 验收后才可勾选 `[x]`）
3. **进度实时写 Task.md**：每完成一步（尤其每次实测/每轮配置改动）当场更新"自测证据"或任务状态，不攒到收工——实测证据（时间、trace 结果、用户确认）比结论更值钱
4. 只做任务清单内的事，不加不需要的功能
5. 敏感信息（密钥、密码、API Key）一律不入库
6. 遇到需求歧义 → 停下，记录到 CHANGELOG，交回规划 Agent
7. **开发中发现新 Bug → 当场在 Task.md 新建任务（状态：待办），不许视而不见**

## 第三步：自测

### 运行实例与收尾

1. 启动前记录入口、工作目录、已有 PID/父 PID、会话 ID 与历史路径；命令参数可能含 token，只保留脱敏字段。优先使用用户实际启动入口。
2. 必须直接运行脚本时，记录它是否脱离启动器管理。启动器设置页不代表没有独立聊天实例，启动器关闭也不代表所有测试实例已退出。
3. 测试结束走正常退出流程，确认历史含临时增量已保存，插件调度停止、语音队列停止、测试子进程退出，再恢复临时配置。未经这些检查不得称“安全重启”。
4. 退出失败先核对目标归属和保存状态；不能重复启动来掩盖失败，不能全杀 Python。未能收尾时记录具体实例、风险和待办。

### 诊断证据

按完整日期、PID、session_id、turn_id 对齐事件，优先读当前会话结构化日志；聚合日志中的时分秒不可跨天直接比较。HTTP 成功、测试通过或文件存在，只能说明对应步骤通过。

- 本地跑通基本功能（能运行 / 能构建 / 主路径无报错）
- 自测 ≠ 正式测试，正式验收由测试 Agent 负责

## 第四步：记录交接

在 CHANGELOG.md 顶部新增记录，必须写清：**完成了哪些任务 / 改动文件 / 自测结果 / 遗留问题**。

> 📌 **日志归属（2026-09-15）**：根 `CHANGELOG.md` 只记**平台级**事项（本仓库自身变更、大规划与立项）；**子项目的开发细节写入该子项目自己的 `CHANGELOG.md`**（`Project/<子项目>/CHANGELOG.md`），不进根 log。两者各自保持 15 条上限，超出部分归档进同目录 `CHANGELOG.archive.md`。

## 第五步：收工检查（三件套，缺一不算完工）

- [ ] **① CHANGELOG.md** 已新增记录（完成了哪些任务 / 改动文件 / 自测结果 / 遗留问题）
- [ ] **② Task.md** 已更新（本次任务状态改为「待复验」；新发现 Bug 已新建任务「待办」）
- [ ] **③ 改动已落库**：仓库内代码 `git commit + push`；**仓库外代码**（如 Shinsekai 运行目录）已把修复说明 + 改动文件摘要写进本仓库文档（HANDOFF 或 CHANGELOG）并提交推送

```bash
git add <改动文件>
git commit -m "开发 Agent：<简述>"
git push
```

**收工硬检查（缺一即视为未完工，交回重做）**：
- [ ] `git status` 干净——本地不允许残留未提交改动（含未跟踪文件）
- [ ] **`git ls-remote origin main` 的返回值 = 本机 `git rev-parse HEAD`**——本地没有未推送的提交
  （⚠️ 不要只信 `git fetch` 后的 `git log origin/main..HEAD`：本机 `refs/remotes/origin/main` 实测会卡在陈旧值，ahead 数虚高、判据失真。详见文末附录）
- [ ] 若无法 push（网络等），在 CHANGELOG 明示"本地提交未推送"及原因，不得默认已交接

> ⚠️ 只写日志不提交 = 工作白做。只改仓库外代码不留痕 = 仓库失真，下一个 Agent 会被误导。**证据写在克隆副本里没推回主仓库 = 交接失败**（Codex 2026-09-15 教训：全部实测证据留在旧机 `D:\Program\AllAgentBASE` 副本里未提交，规划 Agent 只能靠会话截图还原，快照三处误判）。

---

## 红线（禁止）

- ❌ 修改 BRD.md 的需求部分（只能补充技术细节）
- ❌ 跳过自测就标记任务完成
- ❌ 删除测试 Agent 提出的 Bug 记录
- ❌ 需求不明时自行猜测实现
- ❌ 只写日志：不更新 Task.md、不 commit/push 就宣布完工

---

## 附录：Git 推送与网络应急手册（三 Agent 通用）

> 📌 来源：ALLBot部署 子项目 2026-09-15 连续 10 次推送失败后的排查结论，逐条实测。**规划 / 开发 / 测试 Agent 收工都要 push，一律按本附录处置。**

### 一、什么才算「推送成功」——唯一可信判据

**跑 `git ls-remote origin main`，把返回的 commit 与本机 `git rev-parse HEAD` 比对，一致才算成功。**

以下**全部不可信**（实测踩过）：

| 表面证据 | 为什么不可信 |
|---|---|
| `git status -b` 显示 `[ahead N]` | 本机 `refs/remotes/origin/main` 会**卡在陈旧值**（实测长期停在 `df5181e`，连推 18 个提交后仍不动），ahead 数虚高 |
| `git fetch origin` 的输出 | 同上：嘴上说 `df5181e..b8c879c main -> origin/main`，该引用实际未刷新 |
| `.git/packed-refs` 里的 remote-tracking ref | 网络不通时保持陈旧值，据此算出的「未推送提交数」是错的 |

### 二、三种失败形态，按序处置

**形态 1 —— `CONNECT tunnel failed, response 502`（代理间歇故障，最常见）**
- 特征：代理访问百度 / 镜像站正常
- 处置：**隔 4~6 秒重试**，实测 1~2 次即通

**形态 2 —— `Failed to connect github.com:443 after 21xxx ms`（直连超时）**
- 特征：绕代理直连也挂
- 处置：换另一条路径（代理↔直连**各试一次**即可判断）；直连写法 `git -c http.proxy= -c https.proxy= push origin main`，或清空 `HTTP_PROXY` / `HTTPS_PROXY`
- ⚠️ **代理端口要读注册表，不要读环境变量**（2026-09-20 实测纠正，原文写反了）：
  - ✅ 正确来源：注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings` 的 `ProxyServer` —— 本机实测 **`127.0.0.1:7897`**（进程 `verge-mihomo.exe` / Clash），换机后**仍然是这个值**，稳定可硬编码。
  - ❌ 别用 `$env:HTTPS_PROXY`：它指向**沙箱自己的代理**（`sandbox-cli.exe`，端口每次会话都换——实测见过 `58248` / `63443`），对 GitHub 一律 `CONNECT tunnel failed, response 502`。
- 🔴 **只传 `-c http.proxy=` 不够，必须同时清掉子进程里的代理环境变量**（2026-09-20 实测）：git 仍会读 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY`，被沙箱代理劫持后表现为 **push rc=128 但 stdout/stderr 全空**，而 `ls-remote` 不带参数时也会走环境代理、给出**假的 502**。正解：
  ```python
  env = os.environ.copy()
  for k in ('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy'):
      env.pop(k, None)
  subprocess.run(['git','-c','credential.helper=','-c','credential.helper=wincred',
                  '-c','http.proxy=http://127.0.0.1:7897','-c','https.proxy=http://127.0.0.1:7897',
                  'push','origin','main'], cwd=r'E:\AllAgentBASE', capture_output=True, env=env)
  ```
  按此姿势实测**一次成功**（`d0b44c2..10dc838 main -> main`）。另注：`ls-remote` 核验时**也要带同样的 `-c http.proxy` / `-c https.proxy`**。
- ⚠️ 若 `push` 卡在 401 之后**永久无输出**（`timeout` 退出码 124）= 凭据助手弹 GUI（PortableGit 的 `credential.helper=helper-selector`）→ 用上面 `credential.helper=` + `credential.helper=wincred` 的写法（**先清空列表再指定**，只写 wincred 会被兜底拦回）。

**形态 3 —— `push` 静默失败：rc=128 且 stdout / stderr 全空（最坑）**
- 特征：`ls-remote` / `fetch` 都正常，唯独 `push` 返回 128 且**不打印任何 `fatal:`**；PowerShell 里只看到一层 `RemoteException` 包装
- **解法：加跟踪环境变量重跑，通常一次即成功**
  ```bash
  GIT_TRACE=1 GIT_CURL_VERBOSE=1 GIT_TRACE_PACKET=1 git push origin main
  ```
  跟踪输出会显示完整链路：CONNECT 隧道 `200` → `git-receive-pack` 首轮 `401` → 凭据补齐 `200` → `unpack ok` / `ok refs/heads/main`
- 实测记录：裸推 **6 次全败**，加上跟踪后**每次即通**。遇到形态 3 别再裸重试，直接上跟踪

### 三、抓真实报错的正确姿势（Windows / PowerShell）

PowerShell 的 `2>&1 | Out-File` 会把 git 的中文报错搅成乱码，`$LASTEXITCODE` 也常拿不准。**用 Python `subprocess` 才能拿到真实 exit code 与 stderr 字节**：

```python
import subprocess
p = subprocess.run(['git', 'push', 'origin', 'main'],
                   cwd=r'E:\AllAgentBASE', capture_output=True)
print(p.returncode)
print(p.stdout.decode('utf-8', 'replace'))
print(p.stderr.decode('utf-8', 'replace'))
```

⚠️ `cmd.exe /c ...` 会被本机安全策略**直接拦截**，别走那条路。诊断代理连通性用 `curl.exe -s -o NUL -w "%{http_code}" -x $env:HTTPS_PROXY --max-time 20 <url>`（**必须写 `-o NUL`**，写成 `-o $null` 会把整个响应体倾倒到 stdout）。

### 四、提交身份

**本仓库已配好（仓库级，非全局）**，直接提交即可：

```bash
git commit -m "规划 Agent：<简述>"
```

⚠️ 全局（`--global`）**仍未配置**，在其他仓库里提交仍需显式传：

```bash
git -c user.name=SSaann -c user.email=ssaann@example.com commit -m "规划 Agent：<简述>"
```

中文提交信息建议写入 UTF-8 文件后用 `git commit -F <file>`，避免 PowerShell 传参乱码。

> ℹ️ 本机 git 位于 `H:\Program\Git\cmd\git.exe`（已在新机 PATH 上，直接 `git` 可用）。

### 五、红线

- ❌ **不强推**（不用 `--force` / `--force-with-lease`）
- ❌ **不擅自改用户的代理配置**
- ❌ **不谎报已推送**：推送失败必须在 CHANGELOG 明写「本地提交未推送 + 原因 + 重试方法」，不得默认已交接
