# 导入 Specification

## Purpose
规定写入目标平台的流程与失败处理，保证写坏了能回滚，不会把用户原有的表情包搞乱。

## Requirements

### Requirement: 先计划后执行

系统 SHALL 在写入前先产出一份执行计划，列清要新增、覆盖与跳过哪些项。

#### Scenario: 导入前

- **WHEN** 开始导入
- **THEN** 先输出计划，说明每个表情的去向与冲突处理方式

### Requirement: 写入前备份

系统 SHALL 在改动目标平台数据前做备份，失败时按备份回滚。

#### Scenario: 写到一半失败

- **WHEN** 导入过程中出错
- **THEN** 系统按备份恢复原状，并报告失败位置

### Requirement: 结果要有报告

系统 SHALL 输出结构化结果，含成功数、跳过数、失败项与原因。

#### Scenario: 导入结束

- **WHEN** 流程完成
- **THEN** 输出报告，失败项逐条给出原因，不只给一个总数
