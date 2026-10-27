# 规格变更：技能加载

## Purpose

规定 AGENTS.md 如何索引仓库里的技能资产，让 Agent 在开工时按任务类型取用正确的技能，避免把大段正文常驻在上下文里。

## ADDED Requirements

### Requirement: 入口提供技能路由

系统 SHALL 在 AGENTS.md 里维护一张路由表，把任务类型映射到 `skill/` 下对应的目录。

#### Scenario: 接到一个出图任务

- **WHEN** Agent 收到海报或配图类任务
- **THEN** 它 SHALL 按路由表找到对应技能目录，读取其中的 `SKILL.md` 后再动手

#### Scenario: 路由表里没有匹配项

- **WHEN** 任务找不到对应技能
- **THEN** Agent SHALL 按通用规矩执行，并在收工后建议是否新增登记

### Requirement: 入口只放摘要

系统 SHALL 让 AGENTS.md 只保留技能的触发条件与关键约束，正文留在技能目录内按需加载。

#### Scenario: 技能正文很长

- **WHEN** 某技能的 `SKILL.md` 体积较大
- **THEN** AGENTS.md 里 SHALL 只写摘要与指针，不复制正文

### Requirement: 新增技能必须登记

系统 SHALL 要求新引入的技能同时更新路由表，未登记的技能视为未安装。

#### Scenario: 从外部引进一个技能

- **WHEN** 仓库新增 `skill/<名称>/`
- **THEN** 同一次提交 SHALL 包含 AGENTS.md 路由表与摘要小节的更新

#### Scenario: 技能已删除但路由还在

- **WHEN** 路由表指向的目录已不存在
- **THEN** 该行 SHALL 被清理，避免 Agent 按死链去找
