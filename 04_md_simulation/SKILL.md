---
name: md-simulation
description: Stage 4 分子动力学模拟总 Skill。管理 planned run route、formal run-unit 绑定与复用、project-level run_unit.yaml，以及 4.1/4.2/4.3 执行层之间的关系。
---

# 4 MD simulation

通用 Task Execution 规则读取：

`../references/task_execution_rules.md`

本 Skill 仅在此基础上定义 Stage 4-specific 的 run route、run-unit、binding/reuse/continuation 与共享结果组织规则。

## Purpose

负责 Stage 4 的总体执行规则。

Stage 4 不把任务表示为固定的 `4.1 → 4.2 → 4.3` 串行步骤，而是执行当前 Task Sheet 中由 run-plan entries 组成的 planned run route。每个 entry 在真正开始时绑定一个 formal run unit，再由对应子 Skill 执行。

Stage 4 的三个执行层为：

```text
4.1 Energy minimization   → em.*
4.2 Equilibration         → nvt.* / npt.*
4.3 Production simulation → md.*
```

本 Skill 拥有 Stage 4 公共的 run-unit、绑定、复用、续跑、目录与结果登记规则；具体 `.mdp`、`grompp`、`mdrun` 和 run-specific validation 由相应子 Skill 拥有。

本地计算资源与命令执行倾向统一读取：

`references/execution_preferences.md`

该 reference 记录用户长期执行偏好，不是模拟科学参数规范；当前 Task Sheet / 当前运行环境的实际要求可以覆盖其中的资源倾向。

## Object requirements

开始处理当前 planned run entry 前，至少需要：

- 当前 Task Sheet 中的 planned run route；
- 当前 entry 的 run class 与关键科学要求；
- 实际前序状态；
- 与当前体系匹配的 topology / parameter package；
- 判断候选 run unit 是否可复用时所需的实际 run files。

项目级 run-unit index 为：

```text
04_md_simulation/run_unit.yaml
```

如果当前项目第一次进入 Stage 4、该文件尚不存在，由本 Stage 4 main Skill 在第一次需要实例化 formal run unit 前创建，并初始化为 YAML 空 list：

```yaml
[]
```

已有该文件时直接读取和维护，不重新初始化或覆盖历史记录。

当前 Task Sheet 的 planned run route 是**当前执行范围**的唯一模拟计划来源。不得另外创建 `simulation_plan.yaml` 或恢复历史 `expected_route.yaml`。

同一科研任务可以把不同模拟区段拆到不同 Task Sheet。后续 Task Sheet 不需要复制前序 Task Sheet 的完整 planned run route；需要继承的已实例化模拟历史通过项目级 `run_unit.yaml`、实际 run files 和必要的前序 Task Sheet 引用定位。当前 Task Sheet 只记录自己需要执行或继续的 planned run entries。

## Planned run route

一个 planned route 可以包含任意数量、任意必要组合的 EM/NVT/NPT/MD entry，例如：

```text
EM
→ NVT 300 K
→ NPT 300 K / 1 bar
→ NPT restraint release
→ MD 100 ns
```

每个 entry 只记录足以识别该科学 segment 的轻量要求，不复制完整 `.mdp`。formal run-unit ID 在 planning 阶段保持为空。

通常一个 planned route entry 绑定一个 formal run unit。如果原绑定 unit 后续不能继续使用并需要新 unit，则将该 entry 重新绑定到新 unit；旧 unit 保留在 `run_unit.yaml`，不增加 `attempts` 层。

## Formal run-unit identity

formal run-unit ID 只允许：

```text
em.N
nvt.N
npt.N
md.N
```

run class 已由 prefix 表达，不另设 `run_unit_type`。

新 run unit 的编号规则：

1. 确认项目级 `run_unit.yaml` 已存在；首次不存在时按本 Skill 初始化为空 list；
2. 按对应 prefix 查已有正式编号；
3. 分配下一个新编号；
4. 不回收历史编号空缺；
5. formal ID 一旦锁定，必须在实际执行前立即登记。

## Project-level `run_unit.yaml`

项目只维护一个：

```text
04_md_simulation/run_unit.yaml
```

YAML root 直接为 list，不增加 `run_units:` wrapper。

每个记录只要求：

```yaml
- run_unit_id: md.1
  start_from_run_unit_id: npt.1
  status: 未完成
  path: /project/04_md_simulation/md.1/
  top: /project/03_md_preparation/system/sys.top
```

字段：

- `run_unit_id`
- `start_from_run_unit_id`
- `status`
- `path`
- `top`

允许状态：

```text
未完成
已完成
已终止
```

`path` 必须指向该 formal run unit 自身的完整目录。多个 run-unit 目录可以共享同一个 Stage 4 parent directory，但不同 run unit 的 `path` 不应因此写成相同目录。

`top` 必须记录该 run unit 实际用于 `grompp` 的主 `.top` 文件完整路径。多个 run unit 使用同一主 topology 时，应记录同一个 `top` 路径，不为每个 run unit 复制 topology。该字段用于轻量记录 topology lineage，并支持 Stage 5 等下游环节结合 `.tpr` 与 `top` 关系判断多个 run unit 是否来源于同一套体系/topology；如需严格确认 `.ndx` 可复用性，仍应进一步核验实际 `.tpr` / atom ordering compatibility。

`run_unit.yaml` 只用于 instantiated run-unit discovery / maintenance：

- 不记录未来 planned entries；
- 不复制详细 `.mdp` 设置；
- 不复制 `.top` / `.itp` 内容，只记录实际主 `.top` 完整路径；
- 不记录 transient `running / failed / continuing` 状态；
- 不替代真实 run files。

## Binding and reuse

当前 planned entry 真正开始时执行：

```text
read planned entry
→ identify run class + requirement
→ determine actual predecessor state
→ ensure/read run_unit.yaml
→ locate candidate instantiated units
→ inspect actual run files as needed
  ├─ reusable completed unit → bind
  ├─ matching unfinished unit and continuation is appropriate → bind / continue
  └─ no usable unit → allocate new ID → register 未完成 → execute
→ write bound run_unit_id back to the planned entry
```

复用至少检查：

- predecessor state compatibility；
- topology / parameter package compatibility；
- planned scientific requirement 与 candidate 实际有效设置的一致性；
- candidate run result 是否已通过对应子 Skill 要求的检查。

`run_unit.yaml` 中的 `top` 可用于快速定位 candidate 所属的主 topology；真实有效设置和严格兼容性仍以实际 `.mdp`、`.tpr`、topology package 与其他必要 run artifacts 为准。

统一复用判定：

```text
明确等价 → 自动复用
明确不等价 → 创建 / 执行新的 run unit
信息不足 → 询问用户
用户明确要求重做 / 对照 → 跳过自动复用
```

一个 run unit 可以被多个 Task Sheet 合法复用，不因为进入新的 Task Sheet 而复制一份新的 formal unit。

## Continuation versus new run unit

技术性 continuation 如果仍是在完成原 scientific run，则保持同一个 run unit。

例如：

```text
md.4 target = 100 ns
run interrupted at 63 ns
checkpoint continuation to 100 ns
→ still md.4
```

已经完成原计划 segment 后新增一个科学 segment，则创建新的 planned entry，并在开始时绑定新的 `md.N`。

失败本身不产生 `*.failed` run-unit identity。

## Common execution requirements

各子 Skill 均遵循：

```text
current state + topology package + run requirement
→ generate / adjust final run .mdp
→ gmx grompp
→ confirm expected .tpr
→ generate gmx_mdrun.sh
→ execute gmx mdrun
→ run-specific validation
```

在新 run unit 正式登记时，必须同时解析并记录本次 `grompp` 使用的主 `.top` 完整路径；后续不得根据 `.tpr` 文件名或 run-unit prefix 猜测其 topology 来源。

最终实际 `.mdp` 是 detailed simulation settings 的权威记录。

### `gmx_mdrun.sh`

只在 `grompp` 成功并确认目标 `.tpr` 正常生成后创建。

脚本只保存实际 `gmx mdrun` 命令，不写 metadata、status、time prose，也不加 shebang。格式固定为 shell continuation 形式，例如：

```bash
gmx mdrun \
    -deffnm md.1
```

规则：

- 第一行使用 `gmx mdrun` shell continuation 形式；
- 每个实际 option/value 单独一行；
- 后续行缩进 4 spaces；
- 除最后一行外，每个 command line 都使用 shell line continuation；
- 使用 `bash gmx_mdrun.sh` 执行；
- `grompp` 失败时不得生成该脚本。

生成实际 `gmx_mdrun.sh` 前读取 `references/execution_preferences.md`，并结合当前 Task Sheet 和当前运行环境确定线程、GPU 卸载、`tmux`、最长运行时间等执行倾向。实际命令可以因当前环境调整；最终脚本记录本次真实执行命令。

## Common bonded-geometry screening

各 run-specific validation 都必须对最终 `.gro` 执行明显 bonded-geometry 异常筛查。

默认规则：

- 对具有明确参考键长的 bond / constraint 项，`|r - r0| > 0.08 nm` 时标记为显著异常；
- 对具有明确参考键角的 angle 项，`|θ - θ0| > 30°` 时标记为显著异常；
- SETTLE 等具有明确固定几何的项，按其参考几何检查；
- 采用其他几何定义的 bonded function，按该 function 的实际定义检查，不机械套用普通 bond / angle 阈值。

这些阈值用于发现明显结构异常，不作为普适的力场质量判据。被标记的项需要进一步判断，而不是自动判定该 run 无效。

## Sub-Skill mapping

当前 entry 按 run class 加载对应子 Skill：

```text
EM  → 04_md_simulation/4.1_energy_minimization/SKILL.md
NVT → 04_md_simulation/4.2_equilibration/SKILL.md
NPT → 04_md_simulation/4.2_equilibration/SKILL.md
MD  → 04_md_simulation/4.3_production_simulation/SKILL.md
```

不为 Stage 4 建立独立 Validator Skill。运行检查由相应 4.1/4.2/4.3 Skill 直接负责。

## Completion and result maintenance

当一个 formal run unit 完成对应子 Skill 的全部必要检查后：

- 将其 `run_unit.yaml` status 更新为 `已完成`；
- 将 bound `run_unit_id` 保存在 Task Sheet planned route entry；
- Task Sheet 只记录恢复与科学判断需要的关键执行信息，不记录逐命令流水账。

如果 run unit 明确终止且不再继续，将其 status 更新为 `已终止`。

Stage 4 在 `project_result_index.md` 中登记：

```text
04_md_simulation/run_unit.yaml 的完整路径
+ 对该文件的说明：Stage 4 project-level index of instantiated run units
```

不得把每个 `.mdp/.tpr/.gro/.cpt/.xtc/.edr` 或每个 run-unit directory 分别登记成 project-level result。

## Forbidden defaults

不得：

- 把 Stage 4 强制简化成一次 `4.1 → 4.2 → 4.3`；
- 为每个 run unit 建一个普通 Task Sheet substep；
- planning 时提前分配 formal run-unit ID；
- 为 run unit 增加 `run_unit_type`；
- 创建 per-run `run_unit.yaml`；
- 创建 `simulation_output_index`；
- 把详细 `.mdp` 参数复制到 `run_unit.yaml`；
- 把 `.top` / `.itp` 内容复制到 `run_unit.yaml`；
- 因为一次失败就创建 `*.failed` run unit；
- 为 validation 额外拆出 Stage 4 Validator layer；
- 把 `references/execution_preferences.md` 中的资源执行倾向解释成 scientific simulation requirement。