# 规格变更：入库登记

## Purpose

规定外部技能落盘后的登记动作，保证装了就能被路由到，不会出现「装了但没人知道」。

## ADDED Requirements

### Requirement: 落盘即登记

系统 SHALL 在技能入库的同一次提交里更新根 `AGENTS.md` 的路由表与摘要小节。

#### Scenario: 新技能入库

- **WHEN** 目录 `skill/<名称>/` 出现
- **THEN** 同一次提交包含路由表新增一行与摘要小节

#### Scenario: 忘记登记

- **WHEN** 技能已落盘但路由表没有对应条目
- **THEN** 该技能视为未安装，不得在任务中声称可用

### Requirement: 目录名取中文功能名

系统 SHALL 用中文功能名作目录名，上游英文标识记录在来源文件里。

#### Scenario: 上游名字很长

- **WHEN** 上游标识是一串英文 slug
- **THEN** 目录仍用中文功能名，slug 写进 `来源与许可.md`
