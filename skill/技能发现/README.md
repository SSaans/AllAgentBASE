# 技能发现（find skills）

> 一套在本机运行的技能检索工具链。要找现成技能时按固定顺序跑，不用每次重想从哪儿找。
> 本目录**原样留档**，四个上游包的文件一字节未改。

## 调用顺序

| 顺序 | 工具 | 查哪儿 | 什么时候用 |
|---|---|---|---|
| 1 | `find-skills-vercel` | skills.sh（Vercel 索引） | 默认入口 |
| 2 | `find-skill-skillhub` | skillhub.cn 公开接口 | 第 1 项结果不足或不贴题 |
| 3 | `find-skills-agentspace` | skills.sh + ClawHub + GitHub 三源联合 | 需要跨源补充，或要看各源可用性 |
| 4 | `find-skill-zqc` | 装前查（权限、外联、作者信誉） | 补充检索，或要评估某个候选 |

**怎么走**。先看本机已装的技能够不够；不够从第 1 项往下，前一项结果不足、不相关或不可用才进下一项；用户点名来源就直接用那一个，要求全面比较就把四个都跑一遍再合并去重。已经够用就停，不必每次全跑。

## 本机怎么跑（Windows）

四个工具在本机都不需要 Bash、jq 或 gh，用已装的 Python 运行时即可。把示例关键词换成实际需求：

```bash
# 第 1 项：skills.sh 源（借第 3 项的适配脚本，只指定 skills-sh）
python "skill/技能发现/find-skills-agentspace/scripts/search_windows.py" "<关键词>" --source skills-sh --limit 5

# 第 2 项：SkillHub 公开接口，无需鉴权
curl -s "https://api.skillhub.cn/api/skills?keyword=<关键词>&sortBy=score&pageSize=5"

# 第 3 项：三源联合，保留每个来源的状态
python "skill/技能发现/find-skills-agentspace/scripts/search_windows.py" "<关键词>" --source all --limit 5

# 第 4 项：检索 + 装前查档位标注
python "skill/技能发现/find-skill-zqc/scripts/zqc_find_cli.py" find "<关键词>" --limit 5
python "skill/技能发现/find-skill-zqc/scripts/zqc_find_cli.py" inspect "skillhub:<slug>"
```

第 4 项的 `install` 子命令依赖 Unix 的 command 与 Bash，在 Windows 不适用，安装走 SkillHub 官方 ZIP 或 skill-installer。

## 边界

- **只读检索。** 不上传本地内容，只发任务关键词。工具不读凭证、不装软件、不执行候选代码。
- **找技能不等于授权安装。** 用户明确授权才动手装。
- **第三方评级不是安全保证。** 装前查、SkillHub 安全报告都只是旁证，仍要打开候选的 SKILL.md、脚本与来源自己看。
- **区分「没有结果」和「接口故障/限流」。** 前者是查了没命中，后者要如实报缺口，不能混为一谈。
- **同名不同源要分清。** 按来源、命名空间、仓库路径区分，不能只看显示名。

## 来源与许可

四个包都做过本机适配（Windows 调用方式、中文说明、优先级路由），上游原文各自存在同目录的 `UPSTREAM-SKILL.md`，来源、版本与 SHA256 见各自的 `SOURCE.json`。

| 工具 | 上游 |
|---|---|
| `find-skills-vercel` | `github.com/vercel-labs/skills`（`skills/find-skills`，ref `main`） |
| `find-skill-skillhub` | `skillhub.cn/skills/user_290ac21c/find-skill-skillhub`（v1.0.2） |
| `find-skills-agentspace` | `github.com/agentspace-so/skills`（`find-skills`，ref `main`） |
| `find-skill-zqc` | `skillhub.cn/skills/laoxi/zhaojineng`（v1.0.2） |

四个包内均无独立 LICENSE 文件，上游未声明标准开源许可。本仓库只做留档，不对外发布、不收费分发。

## 给别的 agent 用

技能目录扫描只认**第一层有 `SKILL.md`** 的目录，所以要用其中某一个时，把对应的子目录拷进该 agent 的 skills 目录即可，不要拷这个父目录。四个技能的 `SKILL.md` 都在各自子目录第一层。

要整套都用，就四个子目录一起拷，并让 agent 先读本节这张顺序表。

## 相关

- 选型与引进规矩见 `Project/ALLSkill/BRD.md`
- 路由登记见仓库根 `AGENTS.md` §1 与 §2.5
