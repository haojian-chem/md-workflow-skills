# Authoring 文件同步状态

更新日期：2026-07-22

## 同步范围

本仓库已同步 Phase 1 v2r1 的 authoring 基础文件，包括：

- 17 份 `content_maps/*.yaml`；
- `content_map.schema.yaml`；
- Skill inventory 与文件所有权表；
- 多窗口编写任务单模板；
- `md-workflow-skill-authoring` 的 SKILL、references、assets 和 validation scripts；
- `03_contracts/` 中的共享 schema；
- `AGENTS.md`、评测目录说明及原阶段验证记录。

## 使用原则

- `contract_status: pending|draft` 或 `content_ownership_status: pending|draft` 的文件均未冻结。
- 多窗口正式编写前，必须先读取目标 content map、`file_ownership.yaml`、目标 work order 和本文件。
- `AGENTS.md`、`03_contracts/`、authoring references、content maps、inventory 和 ownership 表仍由主窗口统一修改。
- 业务窗口不得依据旧草案自行修改共享 contract。

## 当前已确认但尚未完全回写共享文件的设计变更

1. 一个临时子 Agent 可以承担一个上下文连续的任务单元：
   - 纯 Operation；
   - 纯 Validator；
   - Operation 与其专属配套 Validator 的连续执行。
   当前 `subagent_task.schema.yaml` 和 `runtime_subagent_protocol.md` 仍主要按单个 Skill 描述，后续需要统一修改。

2. 长耗时 MD 任务通过 tmux 或调度系统提交后可进入 `RUNNING` 状态；主 Agent 不高频轮询。相关公共状态与恢复字段仍需专门设计。

3. 当前项目阶段为：

   `structure_preparation → topology_preparation → md_preparation → md_simulation → analysis`

   - `topology_preparation`：标准残基、相连非标准残基和独立非标准组分的拓扑生成与参数准备；
   - `md_preparation`：力场与拓扑整合、建盒、加水、加离子，生成完整体系；
   - `md_simulation`：MDP 与运行输入准备，以及 EM、NVT、NPT、生产 MD、续跑和运行核验。

4. 真实 MD 项目的当前顶层目录为：

```text
<project_root>/
├── 00_project_state/
├── 00_project_records/
├── 01_structure_preparation/
├── 02_topology_preparation/
├── 03_md_preparation/
├── 04_md_simulation/
└── 05_analysis/
```

5. content map 的 `load_when` 与 `applicable_to` 仍是计划中的 schema 扩展，尚未正式加入当前 schema 和所有 map。

## 当前权威设计记录

在共享 contracts 完成更新前，最新的已确认项目阶段、目录和职责边界以以下文件为准：

- 根目录 `README.md`；
- `design_records/manager_and_project_structure_decisions.md`；
- 本文件。
