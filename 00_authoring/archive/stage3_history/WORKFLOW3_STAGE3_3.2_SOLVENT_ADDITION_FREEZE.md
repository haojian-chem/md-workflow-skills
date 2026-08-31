---
name: solvent-addition
description: Stage 3.2 Solvent addition。使用 gmx solvate 向当前 validated system 加入明确选择的 solvent，并同步 coordinate composition 与当前 topology 的 molecule composition。
---

# 3.2 Solvent addition

## Purpose

向当前 validated coordinate/topology state 加入目标 solvent，生成新的 solvated `.gro` 并更新当前 `.top` 中对应 molecule composition。

## Inputs / object

需要：

- 当前 validated `.gro`；
- 当前实际 `.top` 与必要 `.itp`；
- 明确选择的 solvent coordinate/template；
- 当前任务要求的其它 solvation settings，如有。

3.2 通常继承当前 `.gro` 已有 box；需要 box construction/modification 时优先由 3.1 负责。

## Reuse

已有 3.2 结果只有在以下信息都明确等价时才自动复用：

- input coordinate/system composition 相同；
- topology association 相同；
- solvent template / composition 相同；
- 影响结果的 solvate settings 相同；
- 旧结果已通过本 Skill validation；
- 用户未要求重做或对照。

明确不等价则重新执行；信息不足则向用户确认。

## Execution guidance

当前实现：

```text
gmx solvate
```

参数 tendency：

```text
-cp  current validated .gro
-cs  explicitly selected solvent coordinate/template
-p   current associated topology
-o   current substep output .gro
```

`-scale`、`-radius`、`-shell`、`-maxsol` 等不是自动 tendency，只有任务明确需要时加入。

允许一个 3.2 使用已经构造成 mixed-solvent configuration 的 solvent template；也允许 Task Sheet 中存在多个独立 3.2 实例。

## Validation

完成前至少确认：

- 输出 `.gro` 可正常读取；
- solvent 已按预期加入；
- box 未发生无关改变；
- atom/residue/molecule composition 的变化仅来自预期 solvent addition；
- 当前 `.top` 的 `[ molecules ]` / composition 与 solvated coordinates 一致；
- 必要 `.itp` references 仍可定位；
- 没有发生与 3.2 无关的 topology modification。

失败时当前 3.2 实例保持未完成。

## Results / handoff

正式 handoff：

- validated solvated `.gro`；
- updated current `.top`；
- continued required `.itp` references；
- Task Sheet 中的 actual solvent/settings 记录。

真实项目工作目录：

`03_md_preparation/02_solvent_addition/<task_id>/`
