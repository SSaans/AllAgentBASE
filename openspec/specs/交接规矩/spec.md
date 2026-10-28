# 交接规矩 Specification

## Purpose
规定规划、开发两个 Agent 各自能做什么、交接时交出什么、代码怎样进仓库，让接力过程不越界、不丢活、不互相返工。测试并入开发，自测与验收同属开发，放行归用户。

## Requirements

### Requirement: 提交与推送由 Agent 自己完成

系统 SHALL 要求 Agent 自行解决同步问题，不得把拉取、解冲突、推送交给用户手动操作。

#### Scenario: 推送被远端拒绝

- **WHEN** `git push` 因远端有新提交而失败
- **THEN** 该 Agent SHALL 自行拉取、解决冲突、重试推送，直到远端确认一致

#### Scenario: 暂存文件

- **WHEN** Agent 准备提交
- **THEN** 它 SHALL 按路径逐个 `git add`，禁止使用 `git add .`

### Requirement: 交接必须留下可查的证据

系统 SHALL 让每次交接都有可验证的落点，不接受「我已经做完了」这类口头结论。

#### Scenario: 开发说做完了

- **WHEN** 开发 Agent 声称某功能完成
- **THEN** 证据 SHALL 是 `tasks.md` 的勾选加上一次指向远端的提交，两者缺一不算完成

### Requirement: 两个 Agent 职责互不越界

系统 SHALL 限定每个 Agent 的动作范围，越界的请求一律回交。角色只有规划与开发两个，测试不再是独立角色。

#### Scenario: 规划 Agent 被要求直接写功能代码

- **WHEN** 用户让规划 Agent 顺手把功能实现掉
- **THEN** 规划 Agent SHALL 只产出 change 的四件套，实现部分交开发 Agent

#### Scenario: 开发 Agent 觉得需求写错了

- **WHEN** 开发 Agent 在执行过程中发现规格与实际需求不符
- **THEN** 它 SHALL 停下并回交规划 Agent 修改 change，不得自行改规格

#### Scenario: 开发 Agent 被要求顺手把验收也签了

- **WHEN** 开发 Agent 完成了实现，还没跑过任何实测
- **THEN** 它 SHALL NOT 写下验收结论；验收结论只在逐条跑过 Scenario 并留下证据之后才写

### Requirement: 实现进度与验收结论分开记

系统 SHALL 把「这条实现完了」与「这条验过了」当成两件事，分别落笔。两者都归开发 Agent 写，但验收结论必须附带可复核的证据。

#### Scenario: 开发完成一条任务

- **WHEN** 开发 Agent 按 `tasks.md` 完成一步
- **THEN** 它 SHALL 勾掉该条，但此时 SHALL NOT 声称这一条已经验过

#### Scenario: 场景实测通过

- **WHEN** 开发 Agent 逐条跑过规格里的 Scenario 并拿到结果
- **THEN** 它 SHALL 在 change 里逐条写下「场景名 → 实测动作 → 实际结果 → 通过 / 失败 / 未测」，并注明验的人与日期

#### Scenario: 验收结论缺证据

- **WHEN** 验收结论只有「通过」两字，或没有对应到具体 Scenario
- **THEN** 该结论 SHALL 视为无效，不得据此归档

#### Scenario: 用户本人验过

- **WHEN** 用户自己跑过并给出结论
- **THEN** 结论 SHALL 记为「用户 + 日期」，开发 Agent 不得代写或改写
