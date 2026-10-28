# 任务

## 1. 规则文件

- [x] 1.1 `AGENTS.md` §3 角色速查：删掉测试行，职责对比表去掉测试列，「接力」一句改成两棒
- [x] 1.2 `AGENTS.md`「三个 Agent 在 change 上的分工」改成两个 Agent 的四阶段表
- [x] 1.3 `AGENTS.md`「勾选与结论的边界」重写：勾选归开发，验收结论也归开发但必须带证据，用户放行才归档
- [x] 1.4 `AGENTS.md` §2.6、§2.7、常见违规、完整工作流程里的「测试 Agent」提法逐个改
- [x] 1.5 `AGENTS.md` §1 路由表删掉测试卡那一行（11 条变 10 条，逐条判存在全通过）

## 2. 手册与执行卡

- [x] 2.1 `agents/测试.md` 的「怎么验」「后台类五场景表」「归档前三道核对」并进 `agents/开发.md`
- [x] 2.2 `agents/开发.md` 的开工检查、收工检查、红线按新分工改（要验、要留证据、不许只勾不验）
- [x] 2.3 `skill/测试Agent/SKILL.md` 的证据规则与红线并进 `skill/开发Agent/SKILL.md`
- [x] 2.4 退役 `agents/测试.md` 与 `skill/测试Agent/`，已备份到 `H:\Program\_wb\retired_20261028\`
- [x] 2.5 `agents/推送排错.md` 里「三个 Agent 通用」改成「两个 Agent 通用」；`agents/本机环境.md` 同

## 3. 对外说明

- [x] 3.1 `README.md` 流程链与角色表改成两棒，加一步「用户点头」
- [x] 3.2 `README.md` 干活规矩里凡提到测试 Agent 的改掉
- [x] 3.3 顺带改到的：`skill/规划Agent/`、`skill/开发Agent/`、`skill/token节省/简介.md`、`skill/superpowers/本地化说明.md`、`Project/ALLBot部署/README.md`、`Project/bilisum部署/README.md`

## 4. 收尾

- [x] 4.1 全仓扫一遍「测试 Agent」，除历史报告与已归档 change 外无残留
- [x] 4.2 `openspec validate fold-testing-into-development --strict` 通过
- [x] 4.3 归档、提交推送
- [x] 4.4 归档后同步主规格 `交接规矩` 的 Purpose（delta 改不到 Purpose，只能随归档后一并落）

## 没改的地方

- `Project/shinsekai项目byendcycle/TESTING_REPORT_20260922.md` 里「验收人：测试 Agent」留着。那是 2026-09-22 的验收报告，改了就成伪造记录
- `Project/ALLBot部署/openspec/changes/archive/2026-10-27-import-from-brd/tasks.md` 里的「交测试 Agent」同理，属已归档的历史
- `temp/` 目录不动，等用户决定要不要清
