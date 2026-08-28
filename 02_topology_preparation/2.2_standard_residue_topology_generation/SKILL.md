---
name: standard-residue-topology-generation
description: 为当前处理范围内的标准残基生成 GROMACS 全原子结构、拓扑及对应原子映射，并形成正式结果记录。
---

# 2.2 Standard residue topology generation

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

## 输入与处理范围

当前环节的处理范围由 Task Sheet 中对应工作项确定。

执行时至少读取：

- 当前 Task Sheet；
- 当前体系对应的上游结果中的 `stage1_final.pdb`；
- 当前体系对应的 `classification_result.yaml`；
- 当前体系已经确定使用的力场及其它参数定义来源。

`classification_result.yaml` 用于定位当前处理范围内的 `STANDARD_RESIDUE` 及其既有身份信息，
不重新进行残基分类。

## 构造标准残基输入结构

按照 Task Sheet 中对应工作项确定的处理范围，从 `stage1_final.pdb` 中取得该处理范围内的标准残基，
构造 pdb2gmx 输入 PDB。

构造过程中保留 `stage1_final.pdb` 中原有的 chain 组织和 `TER` 设置，
不重新划分 chain 或重新设置 `TER`。

## 生成标准残基全原子结构与拓扑

以提取的标准残基结构作为结构输入，使用当前体系已经确定使用的力场及其它参数定义来源执行 pdb2gmx。

默认使用 `-ignh`，忽略输入 PDB 中已有的氢原子，
由 pdb2gmx 根据当前采用的残基定义重新生成氢原子。

## 核验并整理 pdb2gmx 输出

pdb2gmx 完成后，核验其生成的标准残基全原子结构和拓扑。

至少检查：

1. pdb2gmx 正常结束；

2. 每条 chain 对应一个 GROMACS moleculetype；

3. 每条 chain 内的残基组成和顺序与 pdb2gmx 输入 PDB 中对应 chain 一致；

4. 各 chain 的端基是否被正确设置：
   - 蛋白质 chain：检查 N 端和 C 端；
   - 核酸 chain：检查 5′ 端和 3′ 端。

拓扑文件按一条 chain 一个独立 `.itp` 组织。

若当前只有一条 chain，且 pdb2gmx 将该 moleculetype 的完整分子拓扑直接写入 `.top`，
需将对应分子拓扑分离为独立 `.itp`，并使 `.top` 通过 `#include` 引用该 `.itp`。

## 原子映射

生成标准残基全原子结构后，读取：

`../../references/atom_mapping_rules.md`

同时读取与当前 `stage1_final.pdb` 对应的 `stage1_final_map.yaml`，
按共享原子映射规则维护当前处理范围内标准残基的映射，生成：

```text
standard.map
```

`stage1_final_map.yaml` 中与当前处理范围对应的已有 atom record 保留
`original_atom_serial`、`component_id + residue_id` 和 `operations`，
并按 `standard.gro` 更新 `current_atom_serial`。

pdb2gmx 新增、且输入结构中不存在对应 atom 的原子建立新记录，
`original_atom_serial` 为 `null`，并使用：

```text
2.2ADD
```

记录该新增操作。

## 正式结果

生成正式结果时读取：

`references/results.md`

按其中定义形成：

```text
standard_residue_topology_result.yaml
standard.gro
standard.map
standard.top
每条 chain 对应的独立 .itp
```

`standard_residue_topology_result.yaml` 记录本次实际依赖的上游文件、
实际使用的力场及其它参数定义来源、pdb2gmx 输入 PDB、实际执行命令、
pdb2gmx 执行过程中实际采用的选择，以及上述正式结果文件的完整路径。

`standard.top` 作为标准残基 topology 的主入口，
正式结果记录同时逐项保存该 `.top` 实际引用的各 chain `.itp`。

完成后按仓库级 Task Execution 规则更新当前 2.2 工作项状态，
并按 `references/results.md` 将 2.2 正式结果文件登记到项目结果索引。
