# 提案

## Why

仓库眼下靠 BRD、Task、CHANGELOG 加三本 SOP 描述「怎么干活」，规则散在六七个文件里，互相重复、还有过期段落。Agent 开工要先读一堆文件才敢动手，收工还得另写一段时间线日志。更麻烦的是一次改动没有固定落点，同一个需求在 BRD、Task、CHANGELOG 各写一遍，三处口径经常打架，返工都耗在这上面。

## What Changes

- 引入 OpenSpec SDD，`openspec/` 成为仓库根的一等公民
- 一次改动对应一个 change 文件夹，内含 proposal、specs、design、tasks 四件
- 删除根 `BRD.md`，需求拆开：给人看的进 README，行为契约进 `openspec/specs/`
- 删除 `PLANNING.md`、`DEVELOPMENT.md`、`TESTING.md`，改为 `agents/` 下三份中文手册
- CHANGELOG 停止维护，历史记录合并冻结，此后的变更由 change 归档承载
- `Task.md` 停用，进度看 `openspec list` 与 `tasks.md` 的勾选
- 子项目同步换结构，每个项目一套 `README.md` 加 `openspec/`

## Capabilities

### New Capabilities

- `变更流程`: 一次改动从想法到归档的固定路径，谁能动手、什么条件才允许归档
- `文档分工`: 每类信息只有一个落点，规定 README、AGENTS、specs、changes 各写什么
- `交接规矩`: 三个 Agent 的职责边界、交接物、提交与推送纪律
- `技能加载`: AGENTS.md 如何索引 `skill/` 下的技能，按什么顺序加载

### Modified Capabilities

无。本仓库此前没有 spec 基线，四份能力全部新建。

## Impact

- 根目录新增 `openspec/`、`agents/`、`.agents/skills/`
- 根目录删除 `BRD.md`、`PLANNING.md`、`DEVELOPMENT.md`、`TESTING.md`
- `CHANGELOG.md` 与 `CHANGELOG.archive.md` 合并为一份冻结历史文件，`Task.md` 停用后内容并入其中
- `Project/` 下 10 个子项目全部重建，`BRD.md` 与 `Task.md` 退役
- 三个 Agent 的开工流程与命令全部改写
- 不涉及运行时代码，本仓库的产物是文档与规范
