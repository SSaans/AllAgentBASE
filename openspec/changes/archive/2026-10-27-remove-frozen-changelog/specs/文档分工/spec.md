# 规格变更：文档分工

## REMOVED Requirements

### Requirement: 历史记录一旦冻结不再新增

系统 SHALL 把已停止维护的历史文件标记为冻结，冻结文件只读不写。

#### Scenario: 有人想往冻结文件里补一条

- **WHEN** 有人打算往 `CHANGELOG-历史.md` 追加新条目
- **THEN** 该请求 SHALL 被拒绝，新的变更依据走 change 归档

**Reason**: 仓库不再保留任何时间线日志文件，冻结机制失去对象。历史内容改由 git 提交历史承担，变更记录由 `openspec/changes/archive/` 承担。

**Migration**: 需要回溯某次改动时看 `openspec/changes/archive/`；需要看某个时间点的文件状态时用 `git log` 与 `git show`。两者都不需要额外的存档文件。
