# 交接规矩 Specification

## Purpose
规定规划、开发、测试三个 Agent 各自能做什么、交接时交出什么、代码怎样进仓库，让接力过程不越界、不丢活、不互相返工。

## Requirements

### Requirement: 三个 Agent 职责互不越界

系统 SHALL 限定每个 Agent 的动作范围，越界的请求一律回交。

#### Scenario: 规划 Agent 被要求直接写功能代码

- **WHEN** 用户让规划 Agent 顺手把功能实现掉
- **THEN** 规划 Agent SHALL 只产出 change 的四件套，实现部分交开发 Agent

#### Scenario: 开发 Agent 觉得需求写错了

- **WHEN** 开发 Agent 在执行过程中发现规格与实际需求不符
- **THEN** 它 SHALL 停下并回交规划 Agent 修改 change，不得自行改规格

### Requirement: 两套勾选各归各

系统 SHALL 区分实现进度与验收结论，实现完成不等于验收通过。

#### Scenario: 开发完成一条任务

- **WHEN** 开发 Agent 按 `tasks.md` 完成一步
- **THEN** 它 SHALL 只勾 `tasks.md`，不动验收结论

#### Scenario: 测试通过

- **WHEN** 测试 Agent 按场景验证全部通过
- **THEN** 它 SHALL 在 change 里留下验收结论，并允许进入归档

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
