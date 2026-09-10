---
name: energy-minimization
description: Stage 4.1 Energy minimization Skill。负责 em.* run unit 的 MDP 生成、grompp、gmx_mdrun.sh、mdrun 与 EM 结果检查。
---

# 4.1 Energy minimization

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

本 Skill 在 shared Task Execution 规则和父级 Stage 4 规则基础上，只定义 EM-specific 执行与检查。

## Purpose

执行当前 planned run entry 中属于 `EM` 的 scientific segment，并完成对应 `em.N` formal run unit。

本 Skill 只拥有 EM-specific 执行与检查。formal run-unit identity、binding/reuse、`run_unit.yaml`、共同脚本格式、bonded-geometry screening 与本地执行倾向使用父级：

```text
04_md_simulation/SKILL.md
```

其中资源 / offload / wall-clock 等用户执行倾向由父级按需读取：

`04_md_simulation/references/execution_preferences.md`

## Object requirements

开始执行前需要：

- 已完成父级 Stage 4 binding 的当前 `em.N`；
- 当前 EM planned requirement；
- 实际 starting structure；
- 与 starting structure 匹配的 topology / parameter package；
- 当前 run-unit directory；
- 可用于生成或调整 EM `.mdp` 的模板或上下文（如存在）。

如果 reuse 已由父级规则判定成立，则不重复执行 EM。

## Reuse conditions

在父级 Stage 4 共用条件之外，EM candidate 至少需要确认：

- scientific minimization purpose 与当前 entry 等价；
- 实际 EM `.mdp` 的关键设置满足当前要求；
- starting state 与当前要求兼容；
- candidate 已通过本 Skill 的 EM validation。

只因存在 `em.N` 文件或同名目录，不构成 reuse。

## Execution rules

### 1. Generate / adjust `em.N.mdp`

根据当前 EM scientific purpose、planned requirement、starting system 与已有模板/上下文生成或调整：

```text
em.N.mdp
```

原则：

- 能从体系与既定 protocol 可靠推断的参数直接确定；
- 只有存在真正影响科学含义且无法可靠判断的选择时才询问用户；
- 不要求用户逐项指定所有 `.mdp` 参数；
- 最终实际 `em.N.mdp` 是本 run 的 detailed settings authority。

### 2. `gmx grompp`

使用：

- 当前 `em.N.mdp`；
- 实际 starting structure；
- 配套 topology / parameter package。

输出目标：

```text
em.N.tpr
```

要求：

- `grompp` warning 必须读取并判断；
- 不得为了让 `grompp` 通过而盲目使用 `-maxwarn`；
- `grompp` 成功后确认预期 `em.N.tpr` 正常生成；
- `grompp` 失败时不得继续生成 `gmx_mdrun.sh`。

### 3. Generate `gmx_mdrun.sh`

按父级 Stage 4 统一格式生成。

当前 formal run-unit identity 决定：

```text
-deffnm em.N
```

其余线程数、wall-clock cap、CPU/GPU 资源选项和执行方式不在本 Skill 中固定。生成脚本时由父级 Stage 4 读取 `references/execution_preferences.md`，并结合当前硬件、GROMACS build、当前 Task Sheet / 用户明确要求确定实际命令。

如果实际使用 `-maxh`，它只限制本次 `mdrun` 的 wall-clock，不是 scientific completion criterion；是否完成仍由实际 EM convergence 与 validation 判断。

### 4. Execute EM

按父级 Stage 4 已解析的当前执行偏好和实际运行环境执行：

```bash
bash gmx_mdrun.sh
```

当前环境不适合 preference reference 中某项资源倾向时，按父级规则调整并以实际脚本为准。

## Validation requirements

EM 完成前至少检查：

1. `mdrun` 是否正常结束；
2. `em.N.log` 是否存在，并确认其中表明正常结束；
3. final `em.N.gro` 是否正常生成；
4. final `Fmax`；
5. final structure 的 bonded geometry。

### Fmax

检查 final `Fmax` 是否满足当前 EM 设置与 planned requirement 对应的 convergence expectation。

不得硬编码一个对所有体系都成立的 universal `Fmax` threshold。如果 final `Fmax` 不满足预期，不得直接接受，应检查 `em.N.log` 与当前 EM 设置判断原因。

### Bonded geometry

对 final `em.N.gro` 执行父级 Stage 4 定义的 bonded-geometry screening：

- bond / constraint reference length；
- angle reference value；
- SETTLE fixed geometry；
- 其他 bonded function 按实际 function definition。

被筛出的显著偏移需要进一步判断，不自动等价于 EM 失败。

## Official results

本 Skill 完成后，当前 formal `em.N` 被视为已验证的 EM run unit，并由父级 Stage 4：

- 将 `run_unit.yaml` 中该 unit 的 status 更新为 `已完成`；
- 在当前 planned route entry 中保留 bound `em.N`；
- 通过项目级 `04_md_simulation/run_unit.yaml` 供后续 Stage 4 entry 定位和复用。

本 Skill 不把 `em.N.mdp`、`em.N.tpr`、`em.N.gro`、`em.N.log` 等逐项登记到 `project_result_index.md`。

## User confirmation boundary

仅在以下情况要求用户确认：

- EM 的 scientific target/criterion 存在多个合理选择且上下文不能判定；
- `grompp` warning 涉及实质性科学取舍，无法依据当前体系可靠判断；
- validation 出现异常且继续、修改设置或重新运行之间存在真正的科学选择。

普通可诊断的软件信息、文件定位或可由已有 protocol 明确推断的设置不应转给用户逐项决定。纯计算资源 / 执行方式调整按父级 Stage 4 execution preference 规则处理。
