---
name: ion-addition
description: Stage 3.3 Ion addition。按已冻结的 gmx grompp → gmx genion 内部结构向当前 validated system 加入/替换 ions，并同步 coordinate/topology composition；专用 genion.mdp 的精确模板内容仍需单独实现和验证。
---

# 3.3 Ion addition

## Purpose

根据当前体系的 neutralization / salt concentration / ion species 要求，生成 `genion.tpr` 并用 `gmx genion` 得到 validated ionized coordinate/topology state。

## Inputs / object

需要：

- 当前 validated `.gro`；
- 当前实际 `.top` 与必要 `.itp`；
- neutralization / concentration requirement；
- 正负离子 species，如任务有指定；
- 实际用于 replacement 的 bulk-solvent group。

不得硬编码 `SOL`；replacement group 必须来自当前体系实际 index/group context。

## Reuse

已有 3.3 结果只有在以下信息都明确等价时才自动复用：

- input coordinate/system composition 相同；
- topology association 相同；
- neutralization / concentration intent 相同；
- ion species 相同；
- replacement group 和其它影响结果的 genion settings 相同；
- 旧结果已通过本 Skill validation；
- 用户未要求重做或对照。

体系 composition 一旦变化，旧 `genion.tpr` 不可作为新 3.3 实例的执行输入复用；重复 3.3 必须重新运行 `grompp`。

## Execution guidance

内部结构固定为：

```text
Stage-3 genion MDP template
→ gmx grompp
→ genion.tpr
→ gmx genion
→ ionized .gro + updated topology
```

`grompp` tendency：

```text
-f  Stage-3 dedicated genion.mdp
-c  current validated .gro
-p  current associated .top
-o  genion.tpr for this 3.3 instance
```

`genion` tendency：

```text
-neutral      requested neutralization 时使用
-conc 0.154   biomolecular-system tendency；只有用户/Task Sheet 未给出其它 salt concentration 时采用
-pname/-nname 从当前实际 ion definitions / requirement 推导
```

用户明确 concentration/composition 永远覆盖 `0.154 M` tendency。

### Current implementation gap

Architecture 已冻结要求 3.3 自带一个仅用于生成 genion `.tpr` 的 minimal `genion.mdp`，但其**精确模板内容和代表性执行验证尚未完成**。

因此当前 Skill 可以确定 3.3 的对象、reuse、执行边界和 validation，但在专用模板正式加入并验证前，不应伪造一个 Stage 4 EM/NVT/NPT/MD MDP 作为替代，也不应声称 3.3 implementation 已完全可执行。

## Validation

实际执行可用后，完成前至少确认：

- `grompp` 针对当前 coordinate/topology composition 成功生成本实例 `genion.tpr`；
- `genion` 输出 `.gro` 可正常读取；
- ion replacement/addition 与 requested neutrality / concentration / species intent 一致；
- coordinate molecule composition 与 updated `.top` 一致；
- 必要 `.itp` references 仍可定位；
- 没有复用 composition 改变前的旧 `.tpr`。

## Results / handoff

正式主要 handoff：

- validated ionized `.gro`；
- updated current `.top`；
- continued required `.itp` references；
- Task Sheet 中的 actual ion settings / replacement group 记录。

`genion.tpr` 是当前 3.3 实例的 intermediate execution evidence，不是 Stage 3 的主要科研结果。

真实项目工作目录：

`03_md_preparation/03_ion_addition/<task_id>/`
