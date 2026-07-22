# Authoring 文件同步状态

更新日期：2026-07-22

## 当前基线

仓库已经同步并对齐：

- 17 份现有 Skill content map；
- content map v3 schema；
- Skill inventory 与文件所有权表；
- 多窗口 work order 与 authoring Skill；
- Workstream 项目模型；
- 日志和记录体系；
- 14 份共享运行 contract；
- 串行 task-unit 临时子 Agent 协议。

本轮验证结果见：

`00_authoring/CONTRACT_ALIGNMENT_VALIDATION.md`

## 使用原则

- `contract_status: pending|draft` 或 `content_ownership_status: pending|draft` 的 Skill 尚未冻结；
- 多窗口编写前必须读取 `AGENTS.md`、本文件、`skill_inventory.yaml`、`file_ownership.yaml`、目标 content map、目标 work order 和 `03_contracts/README.md`；
- `AGENTS.md`、`03_contracts/`、authoring references、content maps、inventory 和 ownership 表仅由主窗口修改；
- 业务窗口不得本地重定义共享状态和记录字段。

## 已确认的运行模型

- Workflow 是可复用阶段流程；
- Workstream 是真实项目中的具体工作分支；
- 一个 Workstream 可以经过多个 Workflow；
- 一个项目可以同时存在多个 Workstream；
- 任意时刻最多一个前台临时子 Agent；
- 多个 tmux 或调度系统外部任务可以并存；
- task unit 支持 `OPERATION | VALIDATOR | OPERATION_WITH_VALIDATOR`；
- Operation 与配套 Validator 即使同一子 Agent 连续执行，结果也必须分开；
- Manager 是 `00_project_state/` 和 `00_project_records/` 的唯一提交者。

## 已对齐的共享 contracts

权威索引：

`03_contracts/README.md`

当前包括：

- 公共状态、Focus、文件和错误类型；
- 用户决策请求；
- Workflow decision；
- subagent task/result；
- project/workstream state；
- project event；
- Manager session front matter；
- route、decision、submission、artifact set 和 snapshot record。

外部任务必须经过：

```text
RUNNING
→ FINISHED_UNVERIFIED
→ Validator 核验
→ COMPLETED 或 FAILED
```

tmux 会话或调度任务消失不能直接判为成功。

## 当前实现状态

- `md_workflow_manager`：设计已冻结，必须按新 contracts 重写；
- `structure_preparation_workflow`：需要改为只消费 Focus Workstream 状态；
- `source_recognition` 与 `component_and_residue_classification_validator`：需要对齐 subagent task/result v2；
- 其他 Phase 1 Skills：尚待编写。

## 尚未冻结

- content map 的 `load_when` 与 `applicable_to` 扩展。

## 当前权威设计记录

- 根目录 `README.md`；
- `design_records/manager_and_project_structure_decisions.md`；
- `design_records/logging_and_record_system.md`；
- `03_contracts/README.md`；
- `00_authoring/CONTRACT_ALIGNMENT_VALIDATION.md`；
- 本文件。
