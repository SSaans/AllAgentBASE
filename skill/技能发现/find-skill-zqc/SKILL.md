---
name: find-skill-zqc
description: "优先级4：补充 SkillHub 搜索及装前查的候选权限、隐私去向和作者评估。前三来源不足，或用户要求检查某个候选时使用；外部评级不代表安全保证。"
---

# 找技能 · 风险评估版

## 本地调用约定

用户已选择的默认顺序：find-skills-vercel → find-skill-skillhub → find-skills-agentspace → find-skill-zqc。
先检查当前可用技能是否已满足需求，再按该顺序查找；前一来源结果不足、不相关或不可用时进入下一来源。用户点名来源时直接使用该来源；用户要求全面比较时依序检索并合并去重。
第四项用于补充发现与候选评估，可在用户要求评估或出现需核实的权限、外联、安装脚本时直接调用。评估服务故障或未收录须明确说明，不作安全保证。
搜索只发送概括后的任务关键词，不上传笔记正文。实际推荐前阅读候选 SKILL.md 和必要脚本，核对当前系统依赖、来源与适配范围。
本地约定覆盖上游示例里的固定结束提问、固定输出格式和自动安装建议。保持中文、清晰结构、陈述句结尾。用户已经明确授权的安装直接完成；普通找技能请求只检索与推荐，不能据此自动安装候选。
多个同名技能按来源、命名空间及仓库路径区分，不能只按显示名称或 slug 认定相同。

## 检索与检查

```powershell
& "C:\Users\Unbox\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -X utf8 "C:\Users\Unbox\.codex\skills\find-skill-zqc\scripts\zqc_find_cli.py" find "obsidian" --limit 5
& "C:\Users\Unbox\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -X utf8 "C:\Users\Unbox\.codex\skills\find-skill-zqc\scripts\zqc_find_cli.py" inspect "skillhub:find-skills" --limit 5
```

按实际需求替换示例参数。详细流程见 [上游说明](UPSTREAM-SKILL.md) 及 [接口说明](references/api.md)。只把实际返回的评估当作第三方数据，说明未收录、故障或过期情况，不能编造评级。
原脚本的 install 子命令依赖 Unix command/Bash，在 Windows 不适用。本机使用 find/inspect 进行检索与检查；已获授权的后续安装交给 skill-installer 或 SkillHub 官方 ZIP 路径。
脚本按裸 slug 匹配评估，遇到同名来源时核对原始作者与版本，无法确认对应关系时不把评级移用于另一技能。
