# MD Simulation Plan Ownership

## 1. 决定

`md_simulation_plan` 的唯一领域 owner 为：

```text
01_workflows/md_simulation_workflow/
```

它不属于 `md_preparation_workflow`，也不属于 Manager route record。

权威阶段边界为：

```text
md_preparation_workflow
→ VALIDATED SYSTEM
→ md_simulation_workflow
→ simulation protocol resolution
→ immutable md_simulation_plan
→ per-run MD_INPUT preparation
→ execution / status / output validation
→ VALIDATED MD_OUTPUT
```

`md_preparation_workflow` 负责完整体系生成，包括结构、拓扑、盒子、溨剂和离子等 SYSTEM 内容；`.mdp`、`grompp`、`.tpr`、EM/平衡/生产/续跑片段及其执行计划属于 `md_simulation_workflow`。

## 2. 与 Workstream route 的区别

`md_simulation_plan` 与 Workstream active route 不是同一个对象。

### Workstream route

由 Manager 根据 Workflow route fragments 拼接并持久化，描述：

- 当前请求预计经过哪些 task unit；
- 起点、终点和停止条件；
- Workflow/Operation/Validator 调用顺序；
- 当前路线版本及其修订关系。

### MD simulation plan

由 `md_simulation_workflow` 局部拥有，描述：

- 当前科学模拟方案包含哪些 run units；
- run unit 角色、依赖和输入来源；
- 每个 run unit 的 MDP 来源、起始状态、预期输出和技术完成标准；
- 哪些 execution/backend/resource 字段已解决，哪些仍待执行前解决；
- plan 与 SYSTEM、用户决定、模板和旧 plan 的谱系。

Manager 使用 plan 生成或修订 route，但 plan 本身不授权执行，也不替代 route record。

## 3. 动态而非硬锁定

计划生成后不得作为不可调整的固定队列。

当出现以下变化时，创建新的 immutable plan 版本：

- 新增、删除或重排 run unit；
- 修改 `.mdp`、温度、压力、约束、步数或其他科学参数；
- 延长生产模拟并需要新 `.tpr`；
- 新增 continuation 或新的 production segment；
- 改变起始 SYSTEM、上游 MD_OUTPUT 或 checkpoint；
- 改变完成标准；
- 用户改变阶段终点或比较方案。

新 plan 使用 `supersedes_plan_id` 指向旧 plan，并返回 route revision signal。旧 plan、旧 MD_INPUT 和已有 MD_OUTPUT 不得覆盖。

仅资源分配或 backend 变化是否需要新 plan，取决于它是否改变科学输入：

- 不改变 `.tpr` 和科学方案：可以只生成新的 execution spec；
- 改变并行分解之外的科学参数或运行输入：必须生成新 plan/MD_INPUT。

## 4. 阶段入口

从 Workflow entry 开始时，默认入口 artifact 为：

```text
VALIDATED SYSTEM
```

SYSTEM 至少应提供当前 run input preparation 所需的：

- 坐标/结构；
- 拓扑及 include 依赖；
- 盒子、溶剂和离子后的完整体系身份；
- 上游验证和谱系。

若路线明确从已有 run unit 的 input preparation、execution、status 或 output validation 开始，可以使用已有且仍有效的：

- `md_simulation_plan`；
- VALIDATED MD_INPUT；
- submission record；
- MD_OUTPUT candidate/validation evidence。

不得因为存在 `.tpr` 或运行目录而跳过 plan 和 provenance 核验。

## 5. Plan 生成输入

计划生成必须基于结构化、可追踪的 protocol spec。不得从“按常规跑”“做标准平衡”等模糊表述自动推断。

protocol spec 至少引用：

- Workstream ID；
- VALIDATED SYSTEM artifact set IDs；
- run unit 列表和依赖；
- 每个 run unit 的 role；
- MDP 文件或模板身份；
- 起始状态来源；
- 预期输出；
- 技术完成标准；
- 已解决 decision IDs；
- 明确的未决项。

未决科学参数阻塞 plan validation；只影响执行环境的 backend/resource 字段可以在 plan 中保持未解决，但必须在 execution 前形成 gate。

## 6. Plan 与 MD_INPUT

一个 run unit 的 MD_INPUT 在 plan 通过后由专门 Operation 生成。

```text
VALIDATED SYSTEM or upstream VALIDATED MD_OUTPUT
+ validated md_simulation_plan
+ selected run unit
+ MDP identity
→ md_run_input_preparation
→ MD_INPUT candidate
→ md_run_input_validator
→ VALIDATED MD_INPUT
```

MD_INPUT 至少包含：

- `.tpr`；
- 实际使用的 `.mdp` 或其不可变副本/身份；
- 输入坐标、拓扑和 checkpoint provenance；
- `grompp` command record、版本和 warning evidence；
- run input manifest；
- input validation report。

## 7. 目录

默认：

```text
04_md_simulation/
├── 00_plan/
│   ├── simulation_protocol_spec.yaml
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

## 8. 修复边界

output validation 发现问题后：

- 仅 execution 命令、backend 或资源需要调整，且 `.tpr` 不变：留在当前 run unit，生成新 execution spec；
- 需要新的 `.mdp` 或 `.tpr`：回到本 Workflow 的 plan revision 或 run input preparation；
- SYSTEM 的结构、拓扑、溶剂、离子或盒子需要改变：返回 `md_preparation_workflow` 或从相应 SYSTEM artifact 创建新 Workstream；
- 不得把任何 MD_INPUT 变化笼统地归回 `md_preparation_workflow`。

## 9. 本地接口文件

本阶段局部结构由以下 schema 拥有：

```text
01_workflows/md_simulation_workflow/schemas/md_simulation_protocol_spec.schema.yaml
01_workflows/md_simulation_workflow/schemas/md_simulation_plan.schema.yaml
```

它们是阶段内接口，不替代 `03_contracts/` 的 runtime contracts。