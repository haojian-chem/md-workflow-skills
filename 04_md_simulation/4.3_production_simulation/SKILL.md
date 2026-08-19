---
name: production-simulation
description: Stage 4.3 Production simulation Skill。负责 md.* run unit 的 MDP 生成、duration/tinit/coupling/output 设置核验、grompp、gmx_mdrun.sh、mdrun 与 production 结果检查。
---

# 4.3 Production simulation

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

本 Skill 在 shared Task Execution 规则和父级 Stage 4 规则基础上，只定义 production-specific 执行与检查。

## Purpose

执行当前 planned run entry 中属于 `MD` 的 production scientific segment，并完成对应 `md.N` formal run unit。

formal run-unit identity、binding/reuse、`run_unit.yaml`、共同脚本格式和 bonded-geometry screening 使用父级：

```text
04_md_simulation/SKILL.md
```

## Object requirements

开始执行前需要：

- 已完成父级 Stage 4 binding 的当前 `md.N`；
- 当前 production planned requirement；
- 实际 starting structure；
- 与 starting structure 匹配的 topology / parameter package；
- 当前 run 是否需要继承前序 dynamical state 的明确信息；
- 需要继承时，对应 checkpoint；
- 当前 run-unit directory；
- 可用于生成或调整 production `.mdp` 的模板或上下文（如存在）。

如果 reuse 已由父级规则判定成立，则不重复执行该 production segment。

## Reuse conditions

在父级 Stage 4 共用条件之外，candidate 至少需要确认：

- production scientific purpose 与当前 planned entry 等价；
- planned duration 与 candidate 实际 run definition 相容；
- `tinit` / time-start semantics 与当前 segment 的前序关系一致；
- temperature coupling 条件与当前要求一致；
- NPT production 时 pressure coupling 条件与当前要求一致；
- restraint / bias / special coupling 等当前 run 明确要求一致；
- output settings 足以满足当前 planned use；
- predecessor dynamical state / checkpoint inheritance 兼容；
- candidate 已通过本 Skill 的 production validation。

只因存在 `md.N` 目录或同名 run files，不构成 reuse。

## Execution rules

### 1. Generate / adjust `md.N.mdp`

根据 planned production requirement、当前体系/状态以及已有模板或上下文生成或调整：

```text
md.N.mdp
```

原则：

- 能可靠推断的参数直接确定；
- 只把无法可靠判断且会改变 scientific meaning 的项目交给用户确认；
- 不要求用户逐项指定全部 `.mdp` 参数；
- 最终实际 `md.N.mdp` 是本 run 的 detailed settings authority。

在 `grompp` 前至少明确核验：

- planned simulation duration；
- `tinit` 与当前 run unit 的时间起点、前序 simulation segment 关系是否一致；
- target temperature 与 thermostat / thermal coupling 设置；
- NPT production 时 target pressure 与 barostat / pressure coupling 设置；
- restraint / bias / special coupling 等当前 run 的明确要求；
- output frequency / output settings 是否满足当前 simulation 与后续 intended use。

### 2. `gmx grompp`

使用：

- 当前最终 `md.N.mdp`；
- 实际 starting structure；
- 配套 topology / parameter package；
- 当前 run 需要继承 dynamical state 时，对应 checkpoint。

输出目标：

```text
md.N.tpr
```

要求：

- 需要 continuity 时，不得因为 checkpoint 缺失而静默改为重新生成 velocities；
- `grompp` warning 必须读取并判断；
- 不得为了让 `grompp` 通过而盲目使用 `-maxwarn`；
- 成功后确认预期 `md.N.tpr` 正常生成；
- `grompp` 失败时不得生成 `gmx_mdrun.sh`。

### 3. Generate `gmx_mdrun.sh`

按父级 Stage 4 统一格式生成。

Production MD 默认 argument tendency：

```text
-deffnm md.N
-nt 12
-update gpu
-pin on
```

例如：

```bash
gmx mdrun \
    -deffnm md.1 \
    -nt 12 \
    -update gpu \
    -pin on
```

Production MD 不默认继承 EM 的：

```text
-maxh 0.08
```

### 4. Execute production MD

本地由 Agent 执行 production MD 时默认使用 `tmux`，在对应 run-unit directory 中通过：

```bash
bash gmx_mdrun.sh
```

执行。

checkpoint continuation 如果只是完成原 planned scientific segment，保持同一个 `md.N`。已经完成原 segment 后增加新的 production segment，则由父级 Stage 4 创建 / 绑定新的 planned entry 与 formal run unit。

## Validation requirements

Production run 完成前至少检查：

1. `mdrun` 是否正常结束；
2. `md.N.log` 是否存在，并确认其中表明正常结束；
3. final `md.N.gro` 是否正常生成；
4. `md.N.cpt` 是否正常生成；
5. final `md.N.gro` 是否通过父级 Stage 4 bonded-geometry screening；
6. temperature behavior 是否符合 intended condition；
7. NPT production 时，pressure behavior 与 volume / density behavior 是否符合 intended condition。

不对所有 production run 硬编码统一 temperature deviation、instantaneous pressure 或 density fluctuation threshold。应结合实际 coupling method、体系规模、run length 和 planned scientific condition 判断。

## Official results

本 Skill 完成后，当前 `md.N` 被视为已验证的 production run unit，并由父级 Stage 4：

- 将 `run_unit.yaml` 中该 unit 的 status 更新为 `已完成`；
- 在当前 planned route entry 中保留 bound `md.N`；
- 通过项目级 `04_md_simulation/run_unit.yaml` 供后续 Stage 4 continuation/reuse 与 Stage 5 定位实际 run files。

本 Skill 不把 run-unit 内部各文件逐项登记到 `project_result_index.md`。

## User confirmation boundary

仅在以下情况要求用户确认：

- production duration、coupling、restraint/bias 或其他 scientific condition 存在多个合理方案且计划无法判定；
- `tinit` / time-start relation 与前序 segment 存在科学语义冲突而无法自动解决；
- continuity 需要 checkpoint，但 checkpoint 缺失且是否改为新的 scientific run 需要用户选择；
- `grompp` warning 涉及无法可靠自动判断的实质性科学取舍；
- validation 结果使继续、延长、修改条件或新建 segment 之间存在真正的科学选择。

可由实际文件、既定 protocol 和 GROMACS 输出可靠判断的事项不应逐项交给用户。
