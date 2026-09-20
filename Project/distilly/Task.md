# distilly 任务清单

> 状态流转：`待办 → 修复中 → 待复验 → 已关闭`（**只有测试 Agent 能勾 `[x]`**）
> 验收标准见 `BRD.md`「十二、验收标准」。

---

## A. 规划阶段（收尾中）

- [ ] 任务 1：产出形态确认（已澄清，待关闭）
  - 结论：本项目产出为**技能包（Skill）**，不涉及模型训练 / 微调（用户 2026-09-20 明确）。
  - 已落到 `BRD.md` 第一节「范围边界」与第十三节。
  - 归属：测试 Agent 关闭。

- [ ] 任务 2：规划 Agent 复核子项目 BRD 的需求部分（待复验）
  - 现状：本 BRD 由**开发 Agent 按用户指派代拟**，需求章节标注为「待规划 Agent 确认」。
  - 归属：规划 Agent。

- [ ] 任务 3：用户确认整体实施方案（阶段 2–6）与 family 选择（`colleague`）（待复验）
  - 归属：用户拍板。

---

## B. 进行中 / 待办

- [x] 任务 4：阶段 1 — 环境与部署（✅ 已完成 2026-09-20 02:40）
  - clone 上游 `dot-skill` 分支到 `H:\Program\distilly`（独立仓库，**不复制源码进本仓库**）。
  - 建 Python 独立环境；装 `requests` / `pypinyin` / `python-docx` / `openpyxl` / `pytest`。
  - 跑既有测试：**73 项 / 71 通过 / 1 跳过 / 4 失败**（失败项为未使用的飞书·钉钉采集器）。
  - 宿主可发现该 Skill；`skill_writer.py --action list` 可执行。
  - 技能装入 `.claude/skills/distilly`，触发方式 `/distilly`。

- [ ] 任务 5：阶段 2 — 个人数据准备（**下一步**）
  - 建 `knowledge/self/{public,internal,private}/` 三级目录。
  - 按 `BRD.md` 第八节表 1–7 整理材料，出一份材料清单表（来源 / 时间跨度 / 条数 / 敏感级别 / 脱敏状态）。
  - 达成判据：「工作方法」与「表达习惯」两维度**各有 ≥ 3 个独立来源**。
  - ⚠️ 前置：微信/QQ 无采集器，**需用户提供材料路径**或手写整理。

- [ ] 任务 6：阶段 3 — 执行蒸馏（待办）
  - 走完 `intake → 材料导入 → Work/Persona 分析 → 预览 → skill_writer 落盘`。
  - 产出 7 个文件（`SKILL.md` / `work.md` / `persona.md` / `work_skill.md` / `persona_skill.md` / `manifest.json` / `meta.json`）。
  - 禁止手工拼目录；一律走 writer。

- [ ] 任务 7：阶段 4 — 装载与试用（待办）
  - 用 `install_generated_skill.py` 装到宿主；只装自包含 `SKILL.md`，**不要整目录复制**。
  - 记录宿主名 / 安装路径 / 触发方式；跑 ≥ 5 轮真实问答。

- [ ] 任务 8：阶段 5 — 效果验证与评估（待办）
  - known-answer ≥ 5 题（及格 4/5）、edge-case 2 题、voice 盲测（混淆率 ≥ 40%）、一致性 rubric（5 维均分 ≥ 3.5）、负样本 1 题。
  - 出评估报告（含失败样例清单）。

- [ ] 任务 9：阶段 6 — 迭代进化（待办）
  - 追加材料或对话纠错各 ≥ 1 轮；验证 known-answer 分数不下降。
  - 验证 `version_manager.py` 备份与回滚可用。

---

## C. 待办（需用户或后续 Agent 决策）

- [ ] 任务 10：仓库内杂散文件清点与处置（待用户裁决）
  - 现状（2026-09-20 只读核查，**未做任何删除**）：仓库工作区里有 3 处异常项，均由「路径拼接失误」与「宿主安装」产生：
    - `Programdistilly/` —— 169 个文件，是本应落在 `H:\Program\distilly` 的仓库根文件副本（反斜杠被吞）。
    - `DＺProjectAllAgentBASEgit_pull_result.txt` —— 同上，`D:\...\git_pull_result.txt` 反斜杠被吞、非法字符 `:` 被替换后的产物。
    - `.claude/` —— 3263 个文件，含 `.claude/skills/distilly`（阶段 1 的宿主安装）与 `settings.local.json`。
  - 已做：三项均加入 `.gitignore`，**防误提交**。
  - 待做：是否删除前两项，由用户明确同意后执行（一律走回收站）。
  - 归属：用户裁决 → 开发 Agent 执行。

- [ ] 任务 11：材料是否加密存放（待办）
  - 现状：`knowledge/self/private/` 计划明文存放。
  - 选项：① 明文（简单）；② 加密容器 / 加密盘（更安全，取用多一步）。
  - 归属：用户决策。

- [ ] 任务 12：上游版本跟进策略（待办）
  - 现状：上游改名过、分支路径可能漂移、宿主支持仍在扩。
  - 建议：锁定部署时的 commit，不自动跟随；升级前先备份产出物与材料。
  - 归属：规划 Agent 评估 → 开发 Agent 执行。

- [x] 任务 13：`DEVELOPMENT.md` 附录补记本机推送坑（✅ 已完成 2026-09-21，由规划 Agent 执行）
  - 已补：沙箱代理环境变量覆盖 `-c http.proxy` 的坑、代理端口改读注册表（`127.0.0.1:7897`）、凭据助手弹窗的处置写法、git 身份已配置。
  - 同时新增「第零步：本机路径基线」（换机后实测路径表）。

---

## C2. 换机遗留（2026-09-21 新增）

- [ ] 任务 14：**换机后重建 Python 环境并复跑测试**（待办，**开发 Agent 优先**）
  - 🔴 现状：`H:\Program\distilly\.venv` 的 `Scripts\python.exe` 是**绝对路径 shim**，指向旧机已不存在的 `C:\Users\WindoseII\AppData\Local\Programs\Python\Python313\python.exe` → 实测报 `did not find executable`。
  - 待做：① 删除旧 `.venv` 后重建（**删除前须用户明确同意**，或直接新建 `venv-new` 再切换）；② 重装 `requests` / `pypinyin` / `python-docx` / `openpyxl` / `pytest`；③ 复跑上游测试，核对是否仍是 71/73；④ 重新校验 `skill_writer.py --action list`。
  - ⚠️ 本机 Python 用受管解释器 `C:\Users\Unbox\.workbuddy\binaries\python\versions\3.13.12\python.exe`（PATH 上的 `python` 是 WindowsApps 桩，不可用）。
  - ⚠️ 注意：`.venv` 在**仓库外**，按红线处置前须先列清单并经用户同意。

- [ ] 任务 15：核对宿主技能安装在新机是否仍生效（待办）
  - 现状：`.claude/skills/distilly` 随仓库迁移到 `E:\AllAgentBASE\.claude\skills\distilly`；尚未验证新机上 Claude Code 是否仍能发现并触发 `/distilly`。
  - 归属：开发 Agent。

---

## D. 维护记录

- 2026-09-21：**换机**（旧机 `WindoseII` → 新机 `DESKTOP-JC65SRL` / `Unbox`）。规划 Agent 实测核对并修正全仓库有效文档路径（本子项目 11 处）；确认上游仍在 `H:\Program\distilly`；**发现 `.venv` 失效**（新增任务 14）；未删除任何文件。
- 2026-09-20 03:xx：按用户澄清撤掉「不是模型」的澄清口径，改为范围边界表述；核查工作区发现 3 处杂散项（只读，未删除），已加 `.gitignore`。
- 2026-09-20 02:40：阶段 1 完成 —— 上游部署、Python 环境、测试 71/73、技能装入 `.claude/skills/distilly`。⚠️ 该结论基于**旧机**，换机后随 `.venv` 失效而不再成立（见任务 14）。
- 2026-09-20：子项目立项。按用户指派由开发 Agent 产出 BRD / README / Task / CHANGELOG 四件。
