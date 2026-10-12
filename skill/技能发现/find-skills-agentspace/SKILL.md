---
name: find-skills-agentspace
description: "优先级3：前两级不足、需要跨来源补充或用户指定 AgentSpace 时，联合检索 skills.sh、ClawHub 和 GitHub，并报告各来源是否可用。"
---

# AgentSpace 多来源技能检索

## 本地调用约定

用户已选择的默认顺序：find-skills-vercel → find-skill-skillhub → find-skills-agentspace → find-skill-zqc。
先检查当前可用技能是否已满足需求，再按该顺序查找；前一来源结果不足、不相关或不可用时进入下一来源。用户点名来源时直接使用该来源；用户要求全面比较时依序检索并合并去重。
第四项用于补充发现与候选评估，可在用户要求评估或出现需核实的权限、外联、安装脚本时直接调用。评估服务故障或未收录须明确说明，不作安全保证。
搜索只发送概括后的任务关键词，不上传笔记正文。实际推荐前阅读候选 SKILL.md 和必要脚本，核对当前系统依赖、来源与适配范围。
本地约定覆盖上游示例里的固定结束提问、固定输出格式和自动安装建议。保持中文、清晰结构、陈述句结尾。用户已经明确授权的安装直接完成；普通找技能请求只检索与推荐，不能据此自动安装候选。
多个同名技能按来源、命名空间及仓库路径区分，不能只按显示名称或 slug 认定相同。

## Windows 检索

```powershell
& "C:\Users\Unbox\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -X utf8 "C:\Users\Unbox\.codex\skills\find-skills-agentspace\scripts\search_windows.py" "obsidian" --source all --limit 5
```

新增脚本仅用 Python 标准库实现三源只读搜索，保留每个来源的状态。它不读取凭证、不安装软件，也不执行原版风险模式扫描。GitHub 为匿名仓库搜索，遇到限流或不可用时必须说明缺口，可用现有网页检索补充，不能声称已覆盖全站。

原 Bash 脚本 scripts/find.sh 与 [上游说明](UPSTREAM-SKILL.md) 保留以供参照；本机没有 Bash/jq/gh 运行环境，默认使用上述适配。阅读原文中的评价标准，并人工检查候选 SKILL.md、脚本和来源。已有结果足够时不重复搜索相同来源与关键词。
