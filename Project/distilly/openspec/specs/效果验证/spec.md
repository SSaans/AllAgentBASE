# 效果验证 Specification

## Purpose
规定如何判断蒸馏结果是否真的像本人，避免用「感觉还行」结案。

## Requirements

### Requirement: 用未参与生成的题目测试

系统 SHALL 用没有进入训练素材的题目检验产出，防止背答案。

#### Scenario: 抽题测试

- **WHEN** 验证开始
- **THEN** 系统从留出集里抽题，逐条生成回答，不与原素材重叠

#### Scenario: 题目全来自素材

- **WHEN** 测试题目全都出现在生成素材里
- **THEN** 该次验证 SHALL 视为无效

### Requirement: 结论要能指出差异

系统 SHALL 对每条测试给出与本人实际表达的对照，指出像与不像的地方。

#### Scenario: 输出验证结论

- **WHEN** 一轮验证结束
- **THEN** 系统逐条列出对照结果，标出明显不像的句子与原因
