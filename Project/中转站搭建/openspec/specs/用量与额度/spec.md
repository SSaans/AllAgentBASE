# 用量与额度 Specification

## Purpose
规定面板如何呈现各渠道的消耗与剩余，避免额度用完才发现。

## Requirements

### Requirement: 按渠道汇总用量

系统 SHALL 按渠道统计调用次数与消耗，并能按时间范围查看。

#### Scenario: 看今天的消耗

- **WHEN** 选择今天
- **THEN** 面板按渠道列出调用次数与消耗量

#### Scenario: 某渠道没有调用

- **WHEN** 某渠道在所选范围内没有请求
- **THEN** 该行显示为零，不隐藏

### Requirement: 额度异常可发现

系统 SHALL 在渠道额度接近耗尽或返回额度错误时给出可见提示。

#### Scenario: 上游返回额度不足

- **WHEN** 上游返回额度不足
- **THEN** 面板把该渠道标记为异常，并记录发生时间
