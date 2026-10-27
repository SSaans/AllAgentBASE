# 文档分工 Specification

## Purpose
规定仓库里每份文件装什么内容、由谁维护，让同一件事只有一个权威出处，读者不必在多个文件之间比对口径。

## Requirements

### Requirement: 每类信息只有一个落点

系统 SHALL 为每类信息指定唯一文件，同一个事实不得在两个文件里各写一份。

#### Scenario: 行为描述被写进 README

- **WHEN** 有人想把「某个指令必须带参数」这类行为要求写进 README
- **THEN** 该要求 SHALL 写进 `openspec/specs/` 对应能力，README 只保留一句指向

#### Scenario: 两份文件说法不一致

- **WHEN** 同一行为的描述在 specs 与 README 里出现分歧
- **THEN** 以 `openspec/specs/` 为准，README SHALL 按它修正

### Requirement: 给人看的与给机器看的分开

系统 SHALL 区分两类文档，README 服务于第一次接触项目的人，AGENTS 与 specs 服务于执行任务的 Agent。

#### Scenario: 新人第一次打开仓库

- **WHEN** 一个不了解项目的人打开仓库首页
- **THEN** 他 SHALL 只读 README 就能知道这是什么、有哪些子项目、怎么参与，不需要读 specs

#### Scenario: Agent 开工

- **WHEN** 某个 Agent 开始一项任务
- **THEN** 它 SHALL 读 AGENTS.md 确认规矩与技能路由，再按 change 读对应的 specs 与 tasks

### Requirement: 仓库根只放长期文件

系统 SHALL 保持根目录只含长期存在的文件与目录，临时产物、探针脚本、本机宿主目录一律不入库。

#### Scenario: 在根目录跑了个一次性脚本

- **WHEN** Agent 在仓库根生成探针或中间产物
- **THEN** 该文件 SHALL 落在仓库外的工作目录，或由 `.gitignore` 排除

### Requirement: 历史记录一旦冻结不再新增

系统 SHALL 把已停止维护的历史文件标记为冻结，冻结文件只读不写。

#### Scenario: 有人想往冻结文件里补一条

- **WHEN** 有人打算往 `CHANGELOG-历史.md` 追加新条目
- **THEN** 该请求 SHALL 被拒绝，新的变更依据走 change 归档
