# 提案

## Why

上一轮把两份变更日志合并成一个 `CHANGELOG-历史.md`，标了冻结。这个文件的定位是含糊的：它既不是规格，也不是正在进行的改动，读的人不知道该不该信它、该不该往里写。仓库里留一个「只读但不能删」的中间物，等于给以后每个 Agent 留一道判断题。

## What Changes

- 删除根与十个子项目的 `CHANGELOG-历史.md`
- 里面的历史叙事不再保留副本，需要时查 git 历史
- 其中的未完成任务转成按流程管理的 change，不再挂在文本附录里
- 子项目 README 里指向该文件的说明一并清理
- `文档分工` 规格里「历史记录一旦冻结不再新增」这条要求失去对象，整条移除

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。

### Removed Capabilities

无。

## Impact

- 根与十个子项目各删一份 `CHANGELOG-历史.md`
- `AGENTS.md`、`README.md`、十份子项目 README 里的相关引用全部清掉
- `openspec/specs/文档分工/spec.md` 少一条要求
- 历史内容的唯一去处是 git 提交历史
