# Workflow 4 / Stage 4 architecture freeze

Status: FROZEN — FIRST-PASS GUIDES IMPLEMENTED, REPRESENTATIVE VALIDATION PENDING

本文件只保存 Stage 4 的冻结架构。具体 `.mdp`、`grompp`、`mdrun` 与 run-specific validation 以当前 `04_md_simulation/**/SKILL.md` 为准。

## 1. Catalog and execution model

```text
4.1 Energy minimization   → em.*
4.2 Equilibration         → nvt.* / npt.*
4.3 Production simulation → md.*
```

Stage 4 的关键语义：

```text
sub-stage = execution layer
run unit = execution object
```

Task Sheet 不把 Stage 4 写成固定 `4.1 → 4.2 → 4.3`，而是记录实际 planned run route。

## 2. Planned route / formal run unit

planned entry 在 planning 阶段不提前分配正式 ID。

当该 entry 开始处理时：

```text
bind reusable existing run unit
/ continue matching unfinished run unit
/ instantiate new run unit
```

正式 ID 只允许：

```text
em.N
nvt.N
npt.N
md.N
```

prefix 已提供一级 run class，不再记录 `run_unit_type`。新 ID 使用同 prefix 的下一个历史编号，不回收空缺；身份锁定后、实际执行前立即登记。

## 3. Project-level `run_unit.yaml`

项目只维护一个：

```text
<project_root>/04_md_simulation/run_unit.yaml
```

YAML root 直接是 list，不增加 `run_units:` wrapper。

每个 instantiated run unit 的最小字段：

```yaml
- run_unit_id: md.1
  start_from_run_unit_id: npt.1
  status: 未完成
  path: /full/path/to/run-unit-storage-directory/
  top: /full/path/to/main.top
```

字段语义：

- `run_unit_id`：项目级正式 identity；
- `start_from_run_unit_id`：从哪个 Stage 4 run unit 的状态开始；直接从 Stage 4 之前对象开始时可为空；
- `status`：`未完成 / 已完成 / 已终止`；
- `path`：该 run unit 实际文件的**完整存放目录**，用于跨任务/跨对话查询定位，不规定 execution working directory；
- `top`：该 run unit 实际用于 `grompp` 的主 `.top` 文件完整路径。

多个 run unit 使用同一 main topology 时记录同一个 `top` 路径，不复制 `.top/.itp` 内容。

`top` 用于轻量 topology lineage，并支持 Stage 5 等下游判断不同 TPR 是否来自同一套 topology/system。Stage 5 当前 `.ndx` reuse 规则可据此将 different TPR + same `top` 视为可复用条件。

`run_unit.yaml` 不记录未来 planned entries、不复制 `.mdp` 设置，也不记录 transient `running / failed / continuing` 状态。

## 4. Binding / reuse

在创建新 unit 前先查 `run_unit.yaml` 候选。

候选判断至少考虑：

- predecessor state；
- topology / parameter package；
- planned scientific requirement 与实际有效设置；
- candidate result validity。

真实详细设置以 `.mdp` 和必要 run artifacts 为准。

```text
明确等价 → 复用
明确不等价 → 新建/执行
信息不足 → 用户确认
用户明确重做/对照 → 跳过自动复用
```

一个 run unit 可以被多个 Task Sheet 合法复用。

## 5. Continuation / new segment

技术性 continuation 如果仍然是在完成原 scientific run，则保持同一个 run unit。

原 planned segment 已完成后新增新的科学模拟 segment，则建立新的 planned entry，并在该 entry 开始时绑定新的 formal run unit。

失败本身不产生 `*.failed` identity。

## 6. Execution ownership

当前权威 Skill hierarchy：

```text
04_md_simulation/SKILL.md
04_md_simulation/4.1_energy_minimization/SKILL.md
04_md_simulation/4.2_equilibration/SKILL.md
04_md_simulation/4.3_production_simulation/SKILL.md
```

各 child Skill 自己负责：

```text
final .mdp
→ gmx grompp
→ confirm target .tpr
→ generate gmx_mdrun.sh
→ gmx mdrun
→ run-specific validation
```

Stage 4 不设置独立 Validator Skill。

## 7. Result registration

Stage 4 在 `project_result_index.md` 中登记项目级 `04_md_simulation/run_unit.yaml` 的完整路径和说明。

不把每个 run-unit directory 或 `.mdp/.tpr/.gro/.cpt/.xtc/.edr` 单独登记为 Stage 4 project-level result。

## 8. Explicitly rejected structures

默认不得：

- 用固定 `4.1 → 4.2 → 4.3` 代替真实 planned run route；
- 每个 run unit 建普通 Task Sheet substep；
- planning 时提前分配 formal run-unit ID；
- 建 `simulation_plan.yaml` 或恢复历史 `expected_route.yaml`；
- 每个 run unit 一个 `run_unit.yaml`；
- 建 `simulation_output_index`；
- 在 `run_unit.yaml` 记录 `run_unit_type`；
- 复制完整 `.mdp` 设置；
- 增加无信息量 `run_units:` wrapper；
- 为 replacement run 建 attempts 层；
- 为 Stage 4 建独立 Validator layer。
