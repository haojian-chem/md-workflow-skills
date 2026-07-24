# MD Simulation Protocol and Plan Ownership

## 1. 唯一 owner

以下阶段内对象的唯一领域 owner 均为：

```text
01_workflows/md_simulation_workflow/
```

- `simulation_protocol_spec`；
- `md_simulation_plan`。

它们不属于 `md_preparation_workflow`，也不属于 Manager route record。

权威边界：

```text
md_preparation_workflow
→ VALIDATED SYSTEM
→ md_simulation_workflow
→ validated simulation protocol
→ immutable md_simulation_plan
→ per-run VALIDATED MD_INPUT
→ execution / status / output validation
→ VALIDATED MD_OUTPUT
```

`md_preparation_workflow` 负责结构、拓扑、盒子、溶剂和离子后的完整 SYSTEM；protocol、`.mdp`、`grompp`、`.tpr`、run units 和执行计划属于 `md_simulation_workflow`。

## 2. Protocol spec

protocol spec 是已解决用户决定、显式文件和 artifact facts 的结构化阶段输入，由：

```text
md_simulation_protocol_specification
→ md_simulation_protocol_validator
```

生成和验证。

它描述：

- run units、roles、sequence 和 dependencies；
- MDP/template identities；
- SYSTEM 或 prior-run start states；
- grompp settings；
- execution policy 中已解决或 deferred 的字段；
- expected outputs/completion criteria；
- field provenance；
- resolved decisions 和分层 unresolved items。

每个科学字段必须有明确来源。不得把“按标准流程”“使用默认设置”等模糊表述直接物化为科学参数。

## 3. Plan

validated protocol spec 由：

```text
md_simulation_plan_materialization
→ md_simulation_plan_validator
```

保真物化为 immutable plan。

plan 描述当前科学模拟方案，但不直接授权执行。它不得新增 protocol 未声明的 run unit 或参数。

## 4. 与 Workstream route 的区别

### Workstream route

由 Manager 根据 Workflow fragments 拼接并持久化，描述：

- 本轮预计 task units；
- start/end/stop conditions；
- Workflow/Operation/Validator 调用路径；
- route version 和 revision lineage。

### Simulation protocol/plan

由本 Workflow 局部拥有，描述科学方案和 run DAG。

```text
validated protocol/plan
→ Workflow route fragment
→ Manager Workstream route
```

Manager 使用 plan 投影或修订 route；plan 不替代 route record，route 也不得反向发明 plan 内容。

## 5. 动态而非硬锁定

protocol/plan 生成后仍可因新 evidence 或用户决定修订。以下变化创建新 protocol 和/或 plan version：

- 新增、删除或重排 run unit；
- 修改 MDP、温度、压力、约束、步数或其他科学参数；
- 延长 production 并需要新 TPR；
- 新增 continuation/production segment；
- 改变 SYSTEM、上游 MD_OUTPUT 或 start checkpoint；
- 改变 completion criteria；
- 用户改变阶段终点或比较方案。

新 version 使用 `supersedes_spec_id` 或 `supersedes_plan_id` 指向旧版本，并触发 route revision。旧 protocol、plan、MD_INPUT 和 MD_OUTPUT 不得覆盖。

仅 backend/resource 变化：

- 不改变 TPR 和科学方案：通常只生成新 execution spec；
- 改变科学输入：修订 protocol/plan 并重新准备 MD_INPUT。

## 6. 阶段入口

标准 Workflow entry artifact：

```text
VALIDATED SYSTEM
```

SYSTEM 至少提供 run input preparation 所需的：

- coordinates/structure；
- topology root 和 include closure；
- box、solvent 和 ions 后的完整体系 identity；
- upstream validation/lineage。

若 route 从已有后续 substep 开始，可以使用仍有效的 validated protocol、plan、MD_INPUT、submission 或 MD_OUTPUT evidence。不得因为存在 TPR 或目录而跳过 provenance gate。

## 7. Protocol 生成输入

protocol specification 必须基于：

- resolved route scope；
- VALIDATED SYSTEM IDs；
- 当前有效 RESOLVED decision records；
- explicit MDP/template identities；
- 明确 prior-run MD_OUTPUT/checkpoint identities，如适用。

协议字段与来源通过 `field_provenance` 关联。

未决项分层：

- `PLAN_VALIDATION`：阻止 protocol/plan gate；
- `INPUT_PREPARATION`：允许 protocol/plan 存在，但阻止相应 grompp task；
- `EXECUTION`：不改变科学输入时可 deferred，阻止 execution task。

## 8. Plan 与 MD_INPUT

```text
VALIDATED SYSTEM or upstream VALIDATED MD_OUTPUT
+ validated protocol and plan
+ selected run unit
→ md_run_input_preparation
→ MD_INPUT candidate
→ md_run_input_validator
→ VALIDATED MD_INPUT
```

MD_INPUT 至少包含：

- TPR；
- actual MDP identity/controlled copy；
- coordinates/topology/include/checkpoint provenance；
- grompp command/version/warning evidence；
- run input manifest；
- input validation report。

## 9. 默认目录

```text
04_md_simulation/
├── 00_plan/
│   ├── simulation_protocol_spec.yaml
│   ├── md_simulation_protocol_validation_report.yaml
│   ├── md_simulation_plan.yaml
│   └── md_simulation_plan_validation_report.yaml
├── <run_unit_id>/
│   ├── input/
│   │   ├── run.mdp
│   │   ├── run.tpr
│   │   ├── md_run_input_manifest.yaml
│   │   └── md_run_input_validation_report.yaml
│   ├── md_run_execution_spec.yaml
│   └── <execution and output files>
└── 99_validation/
```

目录名称不构成完成证据。

## 10. 修复边界

output/input validation 发现问题后：

- 仅 command/backend/resources 变化且 TPR 不变：新 execution spec；
- 需要新 TPR 但 protocol 不变：重新执行 run input preparation；
- MDP、run units、start state 或 completion criteria 变化：新 protocol/plan version，再生成 MD_INPUT；
- SYSTEM 的结构、拓扑、盒子、溶剂或离子变化：返回 `md_preparation_workflow` 或创建新 Workstream；
- 不得把所有 MD_INPUT 变化笼统归回 `md_preparation_workflow`。

## 11. 本地接口

```text
01_workflows/md_simulation_workflow/schemas/md_simulation_protocol_spec.schema.yaml
01_workflows/md_simulation_workflow/schemas/md_simulation_plan.schema.yaml
```

它们是阶段内接口，不替代 `03_contracts/` runtime contracts。