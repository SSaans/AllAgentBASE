# 任务

> 口径：只验「装了能不能用、登记对不对、内容与来源是否一致」，不重新评估选型。每条结论带证据。

## 1. 三张执行卡

- [x] 1.1 `skill/规划Agent/` `skill/开发Agent/` `skill/测试Agent/` 三份 `SKILL.md` 结构完整，frontmatter 可被加载器识别
  - 三份都能解析出 `name` / `description` / `version` / `trigger` / `agent_created` 五个固定字段，另有 `description_zh` / `description_en`
  - 缺陷一处：`规划Agent/SKILL.md` 步骤编号从「第 3 步」跳到「第 5 步」，少一个第 4 步
- [x] 1.2 内容与 `AGENTS.md`、`agents/` 手册不冲突
  - 冲突一处：`AGENTS.md` §2.6 写「本仓库只有测试 Agent 能关任务」，而 §3 职责对比表与「勾选与结论的边界」都写开发 Agent 勾 `tasks.md`。同一个文件里前后面打架
  - 其余对齐：红线、收工三件套、`ls-remote` 判据、归档权限四处一致
- [x] 1.3 无敏感坐标（本仓库公开）
  - 扫 `skill/*/SKILL.md`、`简介.md`、`本地化*.md`、`agents/*.md`、`AGENTS.md`：无密钥、无 Token、无手机号、无 QQ 号
  - 唯一命中 `skill/绘画指导/SKILL.md:291` 的 `nyxur42@gmail.com` 是上游作者公开联系方式，属上游原文，不动

## 2. 入口与路由

- [x] 2.1 `AGENTS.md` 路由表每一条指向的路径都存在
  - 11 条路径逐个判存在：全部命中，无缺失
- [x] 2.2 通用 skill 与角色 skill 分类正确
  - `skill/` 下 11 个包全在路由表出现
  - 7 个通用包落在 §2（`token节省` / `humanizer` / `绘画指导` / `绘画基础训练` / `技能发现` / `superpowers` / `openspec`），3 个角色卡落在 §3
  - `达芬奇21中文操作手册` 只在 §1 出现，§1 已注明「不并入本文件，按需加载」，属显式例外，不算漏登
- [x] 2.3 新增技能的登记规则可用（拿一个技能试一遍）
  - 拿 `达芬奇21中文操作手册` 走 §2.3 五步：第 5 步（§1 加一行）过，第 2 步按 §1 的例外口径跳过，**第 1 步不过** —— 该包 frontmatter 只有 `name` / `description` / `agent_created`，缺 `version` 与 `trigger`
  - 结论：规则本身照着做得出来，但上一个新包没完整照做

## 3. 绘画类两包

- [x] 3.1 `skill/绘画指导/` 上游原文未改，来源与许可记录完整
  - `SKILL.md` 自引进后只有一次提交（`7b74fcf`），没被改过
  - `来源与许可.md` 记了上游名、发行名、作者、联系方式、来源页、版本沿革、获取时间与体积
  - 缺一处：**没记 `SKILL.md` 的 sha256**，只能靠 git 单次提交这层旁证
- [x] 3.2 `skill/绘画基础训练/` 同上
  - `SKILL.md` 与 `_meta.json` 的 sha256 与 `来源与许可.md` 记录逐字节一致
  - 提交历史同样只有一次（`a3b23bb`）
- [x] 3.3 两包的本地化补丁说明与实际行为一致
  - 分工、边界、三种装载方式、一句话验证法都在，与 `AGENTS.md` §2.4 / §2.4b 的摘要对得上
  - 缺陷一处：`绘画基础训练/SKILL.md` 没有 frontmatter，补丁里「拷进技能目录就对了」这句在强校验 frontmatter 的装载器上会失效，补丁没交代

## 4. 技能发现工具链

- [x] 4.1 `skill/技能发现/` 四个工具原样留档
  - 四包共 48 个文件，加 `README.md`；每包都有 `SKILL.md` / `SOURCE.json` / `UPSTREAM-SKILL.md`
  - 四包 `upstream_skill_sha256` 与实算 `UPSTREAM-SKILL.md` 哈希逐一一致
- [x] 4.2 `AGENTS.md` §2.5 的调用顺序与实际可用性一致
  - 顺序：§2.5 的表（vercel → skillhub → agentspace → zqc）与 `技能发现/README.md` 第 6 节完全一致
  - 实跑四个，关键词 `poster`，2026-10-28：`skills-sh` 返回 3 条候选；`api.skillhub.cn` 返回正常 JSON；三源联合三条全 `status: ok`；`zqc find` 返回 3 条带装前查档位的候选。四项全通
  - 第 4 项的 `install` 子命令在 Windows 不可用，README 已写明，与实际一致

## 5. 两个工程技能

- [x] 5.1 `skill/superpowers/` 与 `skill/openspec/` 上游文件完整
  - superpowers：87 个文件，`skills/` 下 15 个子包齐全，含 `LICENSE` 与上游 `README.md`
  - openspec：16 个文件，`skills/` 下 12 个技能包加 `README.md`，含 `LICENSE`
- [x] 5.2 `openspec` CLI 可调用，版本与留档一致
  - `openspec --version` 输出 `1.15.0`，与 `本地化说明.md` 记的 CLI v1.15.0 一致
  - 绝对路径 `C:\Users\Unbox\.workbuddy\binaries\node\versions\22.22.2-6\openspec.cmd` 可用
- [x] 5.3 强制引用条款在 `AGENTS.md` 与 `agents/开发.md` 中生效
  - `AGENTS.md` §2.6 / §2.7 都写了「开发 Agent 强制」并给了必读映射
  - `agents/开发.md` **完全没提 superpowers**，只在「设计站不住就改产物」那里用了一条 openspec 命令。强制条款在手册侧只落了一半
  - 顺带查出那条命令放错地方了：`openspec update change` 是 `openspec-update-change` 技能的触发语，不是 CLI 命令。写在 ```bash 块里会被当成命令执行，报错（`openspec update` 是重生成 instruction files，`openspec change` 只有 `show` / `list` / `validate`）

## 6. 收尾

- [x] 6.1 逐条记录验证结果与证据
- [x] 6.2 发现问题，当场修掉
  - 六条发现全部修完，逐条见下「修复记录」
  - 走的是 `AGENTS.md`「什么时候可以不建 change」里的**轻量通道**：本仓库自己的规范与文档改动，不另立 change，答清四问即可。原先按 proposal 说「另立 change」，建了脚手架之后按规则改走轻量通道，脚手架已删
- [ ] 6.3 全部通过后归档
  - 不勾。修复是我自己做的，自己验自己不算验收（`agents/测试.md` 的口径）。等测试 Agent 复验这六处再归档

## 修复记录（四问）

**为什么改**：验证查出 6 处文档与文档、文档与 CLI 实际行为对不上。不修的话，下一个 Agent 照着做会踩空。

**改了什么**

| # | 位置 | 改法 |
|---|---|---|
| 1 | `AGENTS.md` §2.6 | 「只有测试 Agent 能关任务」改成「开发勾 `tasks.md` 的实现进度，验收结论与放行归测试」，与 §3 职责表对齐 |
| 2 | `agents/开发.md` 干活第 2 条 | 把 `openspec update change <名字>` 从 ```bash 块里摘出来，写明它是 `openspec-update-change` 技能的触发语；命令块换成改完后的 `openspec validate --strict` 复校验 |
| 3 | `agents/开发.md` 开头 | 补一句「动手写代码前先过 `skill/superpowers/本地化说明.md`（强制，不是按需）」，让 §2.6 的强制条款落到手册里 |
| 4 | `skill/规划Agent/SKILL.md` | 步骤编号补齐：原「第 5 步」「第 6 步」改为「第 4 步」「第 5 步」，不再跳号 |
| 5 | `skill/达芬奇21中文操作手册/SKILL.md` | frontmatter 补 `version: 1.0.0` 与 `trigger`（达芬奇 / DaVinci Resolve / 快捷键 / 调色 / Fairlight / Resolve FX 等），补齐 §2.3 要求的五个固定字段 |
| 6 | `skill/绘画基础训练/本地化补丁.md` | 在装载说明后补一条已知门槛：上游无 frontmatter，强校验的装载器装不上时，另建 `SKILL.local.md` 只放最小 frontmatter，上游原文不动 |
| 7 | `skill/绘画指导/来源与许可.md` | 「见该 BRD §5.1」是死链（BRD 已退役），改指 `Project/ALLSkill/openspec/specs/` 的 `安全审查` 与 `入库登记` |

**怎么验证**：四条都是可复算的静态检查 —— 路由表 11 条路径全部存在、`openspec --version` 为 1.15.0、四包上游哈希逐一比对、frontmatter 五字段齐（`规划` / `开发` / `测试` / `token节省` / `达芬奇` 五张卡脚本复扫）。CLI 命令逐条对着 `openspec <cmd> --help` 核过。

**归档到哪**：本轮修复本身不进 change（轻量通道），痕迹在这份 `tasks.md` 的修复记录 + 对应提交信息里；本 change 的产物归档到 `openspec/changes/archive/`。
