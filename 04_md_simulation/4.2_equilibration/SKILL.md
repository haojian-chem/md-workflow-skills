---
name: equilibration
description: Stage 4.2 Equilibration Skill。负责 nvt.* / npt.* run unit 的 MDP 生成、关键 thermostat/barostat/temperature-change 核验、grompp、gmx_mdrun.sh、mdrun 与平衡结果检查。
---

# 4.2 Equilibration

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

本 Skill 在 shared Task Execution 规则和父级 Stage 4 规则基础上，只定义 NVT/NPT-specific 执行与检查。

## Purpose

执行当前 planned run entry 中属于 `NVT` 或 `NPT` 的 equilibration scientific segment，并完成对应 `nvt.N` 或 `npt.N` formal run unit。

formal run-unit identity、binding/reuse、`run_unit.yaml`、共同脚本格式和 bonded-geometry screening 使用父级：

```text
04_md_simulation/SKILL.md
```

## Object requirements

开始执行前需要：

- 已完成父级 Stage 4 binding 的当前 `nvt.N` 或 `npt.N`；
- 当前 equilibration planned requirement；
- 实际 starting structure；
- 与 starting structure 匹配的 topology / parameter package；
- 当前 run 是否需要继承前序 velocities / dynamical state 的明确信息；
- 需要继承时，对应的 checkpoint；
- 当前 run-unit directory；
- 可用于生成或调整 `.mdp` 的模板或上下文（如存在）。

如果 reuse 已由父级规则判定成立，则不重复执行该 equilibration segment。

## Reuse conditions

在父级 Stage 4 共用条件之外，candidate 至少需要确认：

- run class 与当前 entry 一致：NVT 对 NVT，NPT 对 NPT；
- 目标温度及 thermal coupling 条件满足当前计划；
- NPT 的目标压力及 pressure coupling 条件满足当前计划；
- restraint / release state 与当前 equilibration segment 一致；
- 如当前 entry 包含 heating / cooling / temperature-change process，其实际 `.mdp` 与计划一致；
- starting dynamical state / checkpoint inheritance 与当前计划兼容；
- candidate 已通过本 Skill 的 validation。

只因存在同类 `nvt.N` / `npt.N` 文件不构成 reuse。

## Execution rules

### 1. Generate / adjust `nvt.N.mdp` or `npt.N.mdp`

根据 planned requirement、当前体系/状态以及已有模板或上下文生成或调整最终 `.mdp`。

通用原则：

- 能可靠推断的参数直接确定；
- 只把无法可靠判断且会改变科学含义的项目交给用户确认；
- 不要求用户逐项指定全部 `.mdp` 参数；
- 最终实际 `nvt.N.mdp` / `npt.N.mdp` 是本 run 的 detailed settings authority。

在 `grompp` 前必须明确核验：

- thermostat / thermal bath 设置是否与 planned temperature condition 一致；
- temperature coupling target 与当前体系及 equilibration purpose 是否适当；
- NPT 时 barostat / pressure bath 设置是否与 planned pressure condition 一致；
- NPT 时 pressure coupling target 与当前体系及 equilibration purpose 是否适当；
- planned restraint / restraint release 要求是否被正确体现；
- 如存在 heating、cooling 或其他 temperature-change / annealing 过程，起止条件、过程与 timing 是否与计划一致。

不要把上述核验机械展开成固定的 `.mdp` keyword checklist；判断对象是实际 scientific condition 与最终 `.mdp` 是否一致。

### 2. `gmx grompp`

使用：

- 当前最终 `.mdp`；
- 实际 starting structure；
- 配套 topology / parameter package；
- 当前 run 需要继承 dynamical state 时，对应 checkpoint。

输出目标：

```text
nvt.N.tpr
```

或：

```text
npt.N.tpr
```

要求：

- 需要 continuity 时，不得因为 checkpoint 缺失而静默改成重新生成 velocities；
- `grompp` warning 必须读取并判断；
- 不得为了让 `grompp` 通过而盲目使用 `-maxwarn`；
- 成功后确认预期 `.tpr` 正常生成；
- `grompp` 失败时不得生成 `gmx_mdrun.sh`。

### 3. Generate `gmx_mdrun.sh`

按父级 Stage 4 统一格式生成。

NVT/NPT 默认 argument tendency：

```text
-deffnm nvt.N / npt.N
-nt 12
-update gpu
-pin on
```

NVT 示例：

```bash
gmx mdrun \
    -deffnm nvt.1 \
    -nt 12 \
    -update gpu \
    -pin on
```

NPT 示例：

```bash
gmx mdrun \
    -deffnm npt.1 \
    -nt 12 \
    -update gpu \
    -pin on
```

NVT/NPT 不默认继承 EM 的：

```text
-maxh 0.08
```

### 4. Execute equilibration

本地由 Agent 执行 NVT/NPT 时默认使用 `tmux`，在对应 run-unit directory 中通过：

```bash
bash gmx_mdrun.sh
```

执行。

technical continuation 是否保持当前 formal run unit，按父级 Stage 4 continuation rule 判断。

## Validation requirements

### Common checks

NVT/NPT 完成前至少检查：

1. `mdrun` 是否正常结束；
2. 对应 `.log` 是否存在，并确认其中表明正常结束；
3. final `.gro` 是否正常生成；
4. `.cpt` 是否正常生成；
5. final `.gro` 是否通过父级 Stage 4 bonded-geometry screening。

### NVT-specific checks

至少判断：

- temperature 是否达到并稳定在 intended temperature condition 附近；
- 如果本 run 包含 planned temperature-change process，实际 temperature response 是否与计划一致。

不设置对所有体系都适用的统一 `±X K` 硬阈值；结合当前 thermostat、体系规模、simulation length 与计划判断。

### NPT-specific checks

至少判断：

- temperature behavior 是否符合 intended condition；
- pressure behavior 是否符合 intended condition；
- volume / density 是否趋于稳定；
- 如果本 run 包含 planned temperature-change process，实际 temperature response 是否与计划一致。

瞬时 pressure fluctuation 本身不能自动判定 NPT 失败；应结合 pressure distribution、volume/density behavior、run length 与当前 scientific purpose 判断。

## Official results

本 Skill 完成后，当前 `nvt.N` / `npt.N` 被视为已验证的 equilibration run unit，并由父级 Stage 4：

- 将 `run_unit.yaml` 中该 unit 的 status 更新为 `已完成`；
- 在当前 planned route entry 中保留 bound run-unit ID；
- 通过项目级 `04_md_simulation/run_unit.yaml` 供后续 Stage 4 entry 定位、继承与复用。

本 Skill 不把 `.mdp/.tpr/.gro/.cpt/.log` 等逐项登记到 `project_result_index.md`。

## User confirmation boundary

仅在以下情况要求用户确认：

- thermostat / barostat / restraint / temperature-change protocol 存在多个合理科学方案且现有计划无法判定；
- continuity 需要 checkpoint，但 checkpoint 缺失且是否改为新的 scientific run 需要用户选择；
- `grompp` warning 涉及无法可靠自动判断的实质性科学取舍；
- validation 结果使继续、延长、修改条件或新建 segment 之间存在真正的科学选择。

可由实际文件、既定 protocol 和 GROMACS 输出可靠判断的事项不应逐项交给用户。
