# 导出 Specification

## Purpose
规定如何从来源平台把表情包完整取出来，保证图片不丢、名字不乱、顺序不乱。

## Requirements

### Requirement: 完整取出包内表情

系统 SHALL 读出来源平台上某个表情包内的全部表情，不遗漏。

#### Scenario: 导出一个小包

- **WHEN** 指定一个表情包并执行导出
- **THEN** 该包内每个表情都落到本地，数量与平台上一致

#### Scenario: 包内为空

- **WHEN** 目标包没有任何表情
- **THEN** 系统 SHALL 明确报告为空，不产出空目录假装成功

### Requirement: 文件名可追溯

系统 SHALL 让导出的文件带上可追溯的命名，重名时按规则区分。

#### Scenario: 两个表情同名

- **WHEN** 包内有两个文件同名
- **THEN** 系统按序号或摘要区分，两个都保留
