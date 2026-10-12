---
name: find-skills-vercel
description: "查找、推荐 Agent Skills 的默认入口（优先级1）。先检索 skills.sh；不足时按 SkillHub、AgentSpace、装前查的顺序继续。用户说找 skill、有没有现成技能、推荐技能时使用。"
---

# Vercel 技能发现 · 默认入口

## 本地调用约定

用户已选择的默认顺序：find-skills-vercel → find-skill-skillhub → find-skills-agentspace → find-skill-zqc。
先检查当前可用技能是否已满足需求，再按该顺序查找；前一来源结果不足、不相关或不可用时进入下一来源。用户点名来源时直接使用该来源；用户要求全面比较时依序检索并合并去重。
第四项用于补充发现与候选评估，可在用户要求评估或出现需核实的权限、外联、安装脚本时直接调用。评估服务故障或未收录须明确说明，不作安全保证。
搜索只发送概括后的任务关键词，不上传笔记正文。实际推荐前阅读候选 SKILL.md 和必要脚本，核对当前系统依赖、来源与适配范围。
本地约定覆盖上游示例里的固定结束提问、固定输出格式和自动安装建议。保持中文、清晰结构、陈述句结尾。用户已经明确授权的安装直接完成；普通找技能请求只检索与推荐，不能据此自动安装候选。
多个同名技能按来源、命名空间及仓库路径区分，不能只按显示名称或 slug 认定相同。

## 检索方法

1. 提取任务意图，用具体英文词及相邻术语检索 skills.sh。该索引不等于 GitHub 全站搜索。
2. 阅读 [上游说明](UPSTREAM-SKILL.md) 中的候选核对方法，结合契合度、来源与维护情况判断，不单凭热度下结论。
3. 本机没有 npx，使用已安装的 AgentSpace Windows 适配脚本，仅指定 skills-sh 来源；它调用同一公开检索源，不会安装软件。

```powershell
& "C:\Users\Unbox\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -X utf8 "C:\Users\Unbox\.codex\skills\find-skills-agentspace\scripts\search_windows.py" "obsidian" --source skills-sh --limit 5
```

将示例关键词替换为实际需求。该适配仅检索，不执行上游扫描；推荐前仍需阅读候选。每个来源失败须与零结果区分，按上述顺序继续。GitHub 技能安装沿用已具备的 skill-installer。
