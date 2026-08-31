---
name: periodic-box-construction
description: Stage 3.1 Periodic box construction。使用 gmx editconf 对当前 validated .gro 建立或调整周期盒并保持 topology association；当前版本不允许用自定义脚本直接改写坐标或 box vector。
---

# 3.1 Periodic box construction

## Purpose

对当前 validated `.gro` 建立任务所需 periodic box / centering，并把新的 coordinate file 与原有 `.top` / `.itp` 关联一起交给后续步骤。

## Inputs / object

需要：

- 当前 validated `.gro`；
- 与该 `.gro` 关联的实际 `.top` 与必要 `.itp`；
- 当前任务的 box requirement，例如明确 box dimensions 或 solute-to-boundary distance。

输入不要求直接来自 Stage 2；任何已验证且 topology association 明确的当前 `.gro` 都可作为 3.1 对象。

## Reuse

已有 3.1 结果只有在以下信息都明确等价时才自动复用：

- input coordinate identity / system composition 相同；
- topology association 相同；
- 实际 box geometry / dimensions 或 distance requirement 相同；
- centering intent 和其它影响结果的 `editconf` 设置相同；
- 旧结果已通过本 Skill validation；
- 用户未明确要求重新构建或做对照。

明确不等价则重新执行；信息不足则向用户确认。

## Execution guidance

当前实现边界只有：

```text
gmx editconf
```

当前版本不得用 Agent 直接改 `.gro` 坐标/box vector，也不得以自定义 coordinate-editing script 代替 `editconf`。

参数 tendency：

```text
-c     通常用于 box construction / centering
-box   用户或 Task Sheet 给出明确 box dimensions 时使用
-d     给出 system/solute 到 box boundary 距离时使用
```

`-box` 与 `-d` 根据实际 requirement 选择，不机械同时加入。其它参数只有当前任务确有理由时使用。

## Validation

完成前至少确认：

- 输出 `.gro` 可正常读取；
- box vectors / dimensions 与当前 requirement 一致；
- 需要 centering 时已实现预期 centering；
- atom count、atom order、residue/molecule composition 未被无关改变；
- 关联 `.top` / `.itp` 仍对应同一分子拓扑；
- 没有为目录对称无意义复制 topology files。

失败时当前 3.1 实例保持未完成，不把未经验证的 boxed structure 交给下游。

## Results / handoff

正式 handoff：

- validated boxed `.gro`；
- 继续引用的实际 `.top` / 必要 `.itp` association；
- Task Sheet 中足以恢复本次 box requirement / actual settings 的记录。

真实项目工作目录：

`03_md_preparation/01_periodic_box_construction/<task_id>/`
