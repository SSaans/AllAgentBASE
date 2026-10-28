# 规格变更：交接规矩

## REMOVED Requirements

### Requirement: 三个 Agent 职责互不越界

系统 SHALL 限定每个 Agent 的动作范围，越界的请求一律回交。

#### Scenario: 规划 Agent 被要求直接写功能代码

- **WHEN** 用户让规划 Agent 顺手把功能实现掉
- **THEN** 规划 Agent SHALL 只产出 change 的四件套，实现部分交开发 Agent

#### Scenario: 开发 Agent 觉得需求写错了

- **WHEN** 开发 Agent 在执行过程中发现规格与实际需求不符
- **THEN** 它 SHALL 停下并回交规划 Agent 修改 change，不得自行改规格

**Reason**: 角色由三个减为两个，测试并入开发。这条按三个角色写的前提不成立。

**Migration**: 换成下面「两个 Agent 职责互不越界」。原来属于测试那部分约束，落到「实现进度与验收结论分开记」的四个场景里。

### Requirement: 两套勾选各归各

系统 SHALL 区分实现进度与验收结论，实现完成不等于验收通过。

#### Scenario: 开发完成一条任务

- **WHEN** 开发 Agent 按 `tasks.md` 完成一步
- **THEN** 它 SHALL 只勾 `tasks.md`，不动验收结论

#### Scenario: 测试通过

- **WHEN** 测试 Agent 按场景验证全部通过
- **THEN** 它 SHALL 在 change 里留下验收结论，并允许进入归档

**Reason**: 验收结论不再由独立角色签字，改由开发在实测之后写，或由用户本人验完写。原先靠「换个人来签」防的事，现在靠「必须带证据」防。

**Migration**: 换成下面「实现进度与验收结论分开记」。勾选与验收仍然分开记，区别在于签字人变了、证据要求写死了。

## ADDED Requirements

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
