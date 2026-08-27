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

## 3. LJ 参数

Sobtop 参数化环节同时处理 LJ 参数。

金属离子 LJ 参数优先从预存且适用于当前参数化体系的参数文件中取得。

预存参数直接按 GROMACS 参数格式保存。12-6 与 12-6-4 参数分别维护在不同文件中，不混合保存。

当前 Merz 离子 LJ 参数保存于 Stage 2 共享 references：

```text
02_topology_preparation/references/12-6.itp
02_topology_preparation/references/12-6-4.itp
```

每个参数文件在注释区域集中定义文献引用，例如：

```text
; References
; ref1: Li et al., J. Chem. Theory Comput. 2013, DOI: 10.1021/ct400146w
; ref2: ...
```

具体参数行的行尾备注记录参数集、文献中明确指定的配合使用溶剂模型及对应引用，例如：

```text
; CM  | TIP3P   | ref1
; IOD | SPC/E   | ref1
; HFE | TIP4PEW | ref1
```

原文未将参数绑定到具体溶剂模型时，不补写溶剂模型。

后续补充参数时继续沿用上述参数文件组织与溯源方式。

## 4. Sobtop 输出名称修正

Sobtop 生成的 `.itp` 中 residue name 或 atom name 与用于 Sobtop 的 mol2 中对应原子不一致时，按该 mol2 中对应原子的 residue name 和 atom name 修正后，再形成正式 `parameterized_topology.itp`。

## 5. 尚待继续确定

除本文件已经冻结的规则外，Sobtop 参数化的其它详细设置与检查要求继续在 2.3 设计中确定。
