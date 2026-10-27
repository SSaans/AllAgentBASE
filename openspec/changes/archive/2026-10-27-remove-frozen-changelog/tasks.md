# 任务

## 1. 清理文件

- [x] 1.1 删除根 `CHANGELOG-历史.md`
- [x] 1.2 删除十个子项目的 `CHANGELOG-历史.md`
- [x] 1.3 确认备份完整，仓库内无残留（`find . -name "CHANGELOG*"` 返回空）

## 2. 清理引用

- [x] 2.1 `AGENTS.md`：根目录地图、产物分工表、入库白名单、常见违规、第 9 条规则
- [x] 2.2 `README.md`：目录结构
- [x] 2.3 十份子项目 README 与相关文档
- [x] 2.4 `openspec/specs/文档分工/spec.md` 移除对应要求

## 3. 承接未完成的活

- [x] 3.1 建立 `verify-skill-assets` 承接五条技能复验
- [x] 3.2 三条子项目待办写进各自 README（万有引力 §七、ALLSkill「首期方向」、平面设计 §十一）

## 4. 收尾

- [x] 4.1 全仓扫一遍死链
- [x] 4.2 `openspec validate remove-frozen-changelog --strict` 通过
- [x] 4.3 归档并提交推送

> 顺手修了 `verify-skill-assets` 的校验：它是纯核验类 change，没有规格增量，补 `skip_specs: true` 后 `--strict` 通过。

## 收工说明

**死链清理结果**：`BRD.md` / `Task.md` / `PLANNING.md` / `DEVELOPMENT.md` / `TESTING.md` / `CHANGELOG-历史.md` 的引用全部改写成 `openspec/specs/`、`openspec/changes/`、`agents/*.md`；三张执行卡（规划 / 开发 / 测试）的触发词同步换成新说法。只有 `AGENTS.md` 第 464 行保留旧名词——那一句本身就在讲「这套旧流程被替换掉了」，删掉就读不通。

**没动的地方**：`temp/`（仓库根的临时产出，11 个文件，指向 `Task.md` 的死链还在里面）、`.workbuddy/memory/`（历史日记，只追加不重写）、`openspec/changes/archive/`（历史留档）。`temp/` 要不要清，另议。
