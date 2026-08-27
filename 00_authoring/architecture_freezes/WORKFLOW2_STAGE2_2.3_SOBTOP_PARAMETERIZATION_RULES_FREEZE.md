# Workflow 2 Stage 2 — 2.3 Sobtop 参数化规则冻结

Status: CURRENT AUTHORING REFERENCE

本文件保存 `2.3 Topology-linked nonstandard parameterization` 中已经敲定的 Sobtop 参数化科学与技术规则。

2.3 环节结构、量化计算主线、正式结果记录及向 2.5 的交付读取：

`WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_FREEZE.md`

## 1. FREQ 结果检查

在拟合成键项前，检查 FREQ 结果中的虚频及对应振动模式，确认结果可用于当前参数化。

## 2. Sobtop 成键项拟合输入

基于检查通过的 OPT 结构生成用于 Sobtop 成键项拟合的 mol2，并与对应的频率计算结果一同用于成键参数拟合。

频率计算结果文件：

```text
ORCA     → *.hess
Gaussian → *.fch / *.fchk
```

## 3. LJ 参数补充

使用 Sobtop 参数化时，若当前体系所需的 LJ 参数缺失，根据当前实际体系从 `02_topology_preparation/references/12-6.itp` 或 `02_topology_preparation/references/12-6-4.itp` 中提取适用参数补充。

## 4. Sobtop 输出名称修正

Sobtop 生成的 `.itp` 中 residue name 或 atom name 与用于 Sobtop 的 mol2 中对应原子不一致时，按该 mol2 中对应原子的 residue name 和 atom name 修正后，再形成正式 `parameterized_topology.itp`。
