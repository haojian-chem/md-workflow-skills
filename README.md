# MD Workflow Skills

用于设计、维护和执行面向分子动力学科研任务的 Skill / Tool 体系。

当前核心原则：

```text
Skill = 指导 Agent 如何处理科研任务
main Skill + 按需 references
supporting Skill only when complex and clearly bounded
Tool only for deterministic capability
```

不再把科研 Skill 强制分类为 Workflow / Operation / Validator，也不以 parser / wrapper / dispatcher 作为 Agent 理解任务的固定前置层。

## Current scientific Skill layout

Active scientific Skills 按 Stage / 科学职责组织：

```text
01_structure_preparation/
├── SKILL.md
├── 1.1_source_recognition/
├── 1.2_component_and_residue_classification/
├── 1.3_chain_and_residue_selection/
├── 1.4_altloc_occupancy_resolution/
├── 1.5_completeness_check/
├── 1.6_missing_region_completion/
├── 1.7_protein_protonation_assignment/
├── 1.8_reorder_and_mapping/
└── 1.9_validation/

02_topology_preparation/
├── SKILL.md
└── 2.5_topology_integration_and_assembly/

04_md_simulation/
├── SKILL.md
├── 4.1_energy_minimization/
├── 4.2_equilibration/
└── 4.3_production_simulation/

05_analysis/
└── SKILL.md
```

Stage 2 其余 2.x Skills 和 Stage 3 detailed Skills 仍在当前架构下继续实现；不为了目录整齐预先创建空 Skill package。

历史 `01_workflows/`、`02_operations/`、`02_validators/` 已退出 active scientific Skill layout。确需保留的历史实现进入 `00_authoring/archive/` 或 Git history。

## Runtime model

默认真实项目运行采用 Lightweight Runtime v2：

```text
Manager
→ Task Sheet
→ long-lived Task Execution Agent
→ current main Skill
→ 按需读取 reference / supporting Skill / Tool guide
```

Manager 负责任务定位、创建和初始规划；Task Execution Agent 长期持有 Task Sheet，逐步完成 reuse、执行、validation、记录和后续计划调整。普通子环节之间不返回 Manager 调度。

Runtime architecture：

`00_authoring/project_design/lightweight_runtime_v2_spec.md`

Manager：

`00_manager/SKILL.md`

## Authoring

Skill 编写/修改窗口的唯一 authoring 入口：

```text
AGENTS.md
→ 00_authoring/SKILL.md
→ 当前负责的目标 Skill / 文件
```

Authoring 采用：

```text
read broadly
write narrowly
```

可以并且应该读取相关上下游 Skill 来理解接口，但当前 Skill 不替其他 Skill 定义内部步骤、参数、validation 或 official results；已有 owner 的规则只引用，不复制成 shadow specification。

Stage architecture freezes：

`00_authoring/architecture_freezes/`

项目级 Stage catalog / 建设状态：

`00_authoring/project_design/MD_WORKFLOW_MASTER_PLAN.md`

## Tools and evaluation

共享确定性 Tool：

`05_tools/`

Tool authoring guide：

`00_authoring/md-workflow-tool-authoring/SKILL.md`

测试、fixtures 和 benchmark：

`04_evals/`

Tool 是确定性能力组件，不是第五个科学决策层，也不是强制 parser gate。

## Legacy material

以下内容不属于默认 current runtime / Skill layout：

```text
03_contracts/
runtime/
design_records/ 中的旧 runtime 设计材料
00_authoring/archive/
```

它们只用于旧项目恢复、明确 Legacy 调试、历史审计或迁移，不应推翻 current Skill / architecture freeze。

## Real MD project records

默认项目记录：

```text
<project_root>/00_project_records/
├── task_index.md
├── project_result_index.md
└── tasks/
    └── Txxxx.md
```

科研执行文件仍写入项目对应 Stage 工作目录；Skill repository 的源码目录和真实 MD project 的 execution directory 是两个不同概念。
