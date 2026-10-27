# 任务

## 1. 建立根骨架

- [x] 1.1 在仓库根执行 `openspec init --tools agents --language zh-CN`
- [x] 1.2 确认 `openspec/config.yaml` 写入 `Language: zh-CN`
- [x] 1.3 建立 change `add-openspec-baseline` 并写完四件套

## 2. 重写根文档

- [x] 2.1 README 换成新口径：项目介绍、目录结构、子项目索引表、上手步骤
- [x] 2.2 AGENTS.md 更新根目录地图、change 命令速查、废 CHANGELOG 与停用 Task 的说明
- [x] 2.3 AGENTS.md 补立项流程、CHANGELOG 归档规则（从 BRD 迁入）、报错三句话术
- [x] 2.4 新建 `agents/规划.md`、`agents/开发.md`、`agents/测试.md`，每份控制在 60 行内
- [x] 2.5 删除 `PLANNING.md`、`DEVELOPMENT.md`、`TESTING.md`，内容按 2.4 拆解后入回收站
- [x] 2.6 删除 `BRD.md`，内容按提案清单分流到 README 与 AGENTS.md 后入回收站

## 3. 收尾历史文件

- [x] 3.1 `CHANGELOG.md` 与 `CHANGELOG.archive.md` 合并为 `CHANGELOG-历史.md`，顶部标注停更日期
- [x] 3.2 `Task.md` 中未完成的想法并入历史文件附录，`Task.md` 退役
- [x] 3.3 核对合并后条目数与源文件一致，无丢失

## 4. 迁移子项目

- [x] 4.1 ALLBot部署
- [x] 4.2 ALLSkill
- [x] 4.3 全惠惠平面设计
- [x] 4.4 全惠惠视频制作
- [x] 4.5 distilly
- [x] 4.6 万有引力
- [x] 4.7 表情包同步
- [x] 4.8 中转站搭建
- [x] 4.9 shinsekai项目byendcycle
- [x] 4.10 bilisum部署
- [x] 4.11 每个子项目：建 `openspec/`、从原 BRD 拆出能力与场景、README 保留使用说明、旧文件入回收站

## 5. 校验与归档

- [x] 5.1 `openspec validate add-openspec-baseline --strict` 通过
- [x] 5.2 `openspec archive add-openspec-baseline` 归档并生成主规格
- [x] 5.3 逐路径 `git add` 后提交，推送远端并核对提交号一致
