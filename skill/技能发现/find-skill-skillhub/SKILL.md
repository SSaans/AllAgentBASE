---
name: find-skill-skillhub
description: "优先级2：在 Vercel 结果不足或用户指定 SkillHub 时，以中英文关键词、分类和标签搜索 skillhub.cn 的技能。使用公开接口，不需要登录。"
---

# SkillHub 中文技能检索

## 本地调用约定

用户已选择的默认顺序：find-skills-vercel → find-skill-skillhub → find-skills-agentspace → find-skill-zqc。
先检查当前可用技能是否已满足需求，再按该顺序查找；前一来源结果不足、不相关或不可用时进入下一来源。用户点名来源时直接使用该来源；用户要求全面比较时依序检索并合并去重。
第四项用于补充发现与候选评估，可在用户要求评估或出现需核实的权限、外联、安装脚本时直接调用。评估服务故障或未收录须明确说明，不作安全保证。
搜索只发送概括后的任务关键词，不上传笔记正文。实际推荐前阅读候选 SKILL.md 和必要脚本，核对当前系统依赖、来源与适配范围。
本地约定覆盖上游示例里的固定结束提问、固定输出格式和自动安装建议。保持中文、清晰结构、陈述句结尾。用户已经明确授权的安装直接完成；普通找技能请求只检索与推荐，不能据此自动安装候选。
多个同名技能按来源、命名空间及仓库路径区分，不能只按显示名称或 slug 认定相同。

## 检索方法

按 [上游说明](UPSTREAM-SKILL.md) 扩展中英文同义词，阅读 [接口说明](references/api.md) 与相关分类参考。公开接口 GET https://api.skillhub.cn/api/skills 无需鉴权。

Windows 可直接用 PowerShell，无需安装 Bash、jq 或 SkillHub CLI：

```powershell
$skillKeyword = [uri]::EscapeDataString('obsidian')
$skillResult = Invoke-RestMethod -Uri "https://api.skillhub.cn/api/skills?keyword=$skillKeyword&sortBy=score&pageSize=5" -TimeoutSec 20
$skillResult.data.skills | Select-Object name,slug,namespace,description_zh,category,labels,version,downloads | ConvertTo-Json -Depth 5
```

替换示例关键词并重复必要的相邻词检索。保留 namespace，按 namespace + slug 去重和生成详情链接；旧文档中的裸 slug 链接可能有同名歧义。网络故障据实报告并按优先级回退。安装已获用户授权的候选时，可使用接口说明记录的官方 ZIP 下载方式并核对文件清单；Windows 不运行 Linux 安装管道。
