# 技能发现 Specification

## Purpose
规定找候选技能的顺序与产出形态，避免每次换个工具重新试一遍。

## Requirements

### Requirement: 按固定顺序调用工具

系统 SHALL 按既定顺序使用发现工具，前一个没有结果再换下一个。

#### Scenario: 第一个工具零结果

- **WHEN** 首选工具没有返回可用候选
- **THEN** 依次尝试后续工具，并记下每个工具的结果

#### Scenario: 多个工具都找到同一个

- **WHEN** 两个工具返回同一个候选
- **THEN** 合并为一条，标注多个来源

### Requirement: 候选池要带来源

系统 SHALL 为每个候选记录来源、标识与一句话定位。

#### Scenario: 产出候选池

- **WHEN** 一轮调研结束
- **THEN** 输出候选清单，每条含来源平台、标识与定位

#### Scenario: 全部落选

- **WHEN** 所有候选都不达标
- **THEN** 系统 SHALL 如实报告无合适候选，不硬选一个交差
