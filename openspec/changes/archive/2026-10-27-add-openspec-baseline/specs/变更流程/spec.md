# 规格变更：变更流程

## Purpose

规定这个仓库里一次改动从提出到归档的固定路径，让任何 Agent 在动手之前都能查到「现在该谁做、做到哪一步」，避免需求、实现、验收三头各干一套。

## ADDED Requirements

### Requirement: 改动必须先立 change

系统 SHALL 要求任何改变仓库行为的改动都先有对应的 change 目录，目录名用动词开头并描述这次要做什么。

#### Scenario: 收到改代码的需求但没有 change

- **WHEN** 用户或上游 Agent 提出一个改动需求，而 `openspec list` 里找不到对应 change
- **THEN** 执行方 SHALL 停止动手，把需求交回规划 Agent 建立 change

#### Scenario: 只想改一个错别字

- **WHEN** 改动只涉及错别字、换行、注释这类不改变任何行为的内容
- **THEN** 执行方 MAY 直接提交，不建 change，但提交信息 SHALL 写明性质

### Requirement: 四件套按依赖顺序产出

系统 SHALL 按 proposal、specs、design、tasks 的顺序产出产物，后一件依赖前一件完成。

#### Scenario: 跳过提案先写任务

- **WHEN** 有人尝试在 proposal 缺失时直接写 tasks
- **THEN** `openspec status` SHALL 把 tasks 标为阻塞，执行方 SHALL 先补齐 proposal

#### Scenario: 改动不涉及行为

- **WHEN** 改动只重构代码或调整工具链，外部可见行为完全不变
- **THEN** change 的 `.openspec.yaml` SHALL 设置 `skip_specs: true`，且 proposal 里说明理由

### Requirement: 归档前必须通过严格校验

系统 SHALL 在归档前要求 `openspec validate --strict` 通过，校验不通过的 change 不得归档。

#### Scenario: 规格缺少场景

- **WHEN** 某条 Requirement 下面没有 `#### Scenario` 段落
- **THEN** 校验 SHALL 报错，执行方 SHALL 补上场景后重新校验

#### Scenario: 归档时主规格的更新

- **WHEN** 校验通过并执行 `openspec archive <change>`
- **THEN** 系统 SHALL 把 change 移入 `openspec/changes/archive/YYYY-MM-DD-<change>/`，并把 delta 合并进 `openspec/specs/`

### Requirement: 归档即变更记录

系统 SHALL 以归档的 change 作为「做过什么」的唯一结构化记录，不再另行维护时间线日志。

#### Scenario: 想知道上个版本改了什么

- **WHEN** 有人需要回溯某次改动的原因与内容
- **THEN** 他 SHALL 在 `openspec/changes/archive/` 下按日期找到对应目录，读其中的 proposal 与 specs

#### Scenario: 零碎杂活需要留痕

- **WHEN** 完成的是一次没有立 change 的小改动
- **THEN** 记录 SHALL 由 git 提交信息承担，不额外写日志文件
