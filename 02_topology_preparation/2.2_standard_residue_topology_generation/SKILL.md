---
name: standard-residue-topology-generation
description: 为 2.1 已拆分确定的当前标准残基处理对象生成 GROMACS 全原子结构、拓扑及对应原子映射，并形成正式结果记录。
---

# 2.2 Standard residue topology generation

通用 Task Execution 规则读取：

`../../references/task_execution_rules.md`

## 输入与处理范围

当前 2.2 的处理范围必须来自一个已经完成且仍适用的 2.1 topology-preparation setup 拆分方案。

该 2.1 可以记录在当前 Task Sheet，也可以记录在同一科研任务的前序 Task Sheet；当前工作开始前必须能够定位对应 2.1 工作项及其标准残基处理对象。

执行时至少读取：

- 当前 Task Sheet；
- 适用于当前处理对象的已完成 2.1 拆分方案；
- 当前处理对象对应的正式 `stage1_final.pdb`；
- 与该结构对应的 `stage1_final_map.yaml`；
- 当前处理对象对应的 `classification_result.yaml`；
- 当前实际采用的力场及其它参数定义来源。

`classification_result.yaml` 用于定位当前处理范围内的 `STANDARD_RESIDUE` 及其既有身份信息，不重新进行残基分类。

力场及其它参数定义来源以 2.1 方案记录为当前基线，并结合当前 Task Sheet、相关前序 Task Sheet、正式记录 / 日志、当前对话和用户已明确决定再次核对。信息能够唯一确定时直接使用；当前工作需要而仍不能唯一确定时向用户确认。

如果新的确认结果会改变 2.1 中已经形成的拆分或参数来源基础，先更新 / 重新形成适用的 2.1 方案，再继续 2.2。

## Reuse

当前 2.2 不设置 reuse。

在 Stage 2 reuse 机制后续单独完成设计与接口更新前，每次实际进入当前工作项，都基于当前 `stage1_final.pdb`、当前处理范围和当前力场 / 参数定义来源重新生成标准残基全原子结构与拓扑。

## 构造标准残基输入结构

按照 2.1 拆分方案与当前 Task Sheet 工作项确定的处理范围，从 `stage1_final.pdb` 中取得标准残基，构造 pdb2gmx 输入 PDB。

构造过程中保留 `stage1_final.pdb` 中已经确定的 chain 组织和 `TER` 设置，不重新划分 chain，不删除或增加用于表示既有聚合物区段边界的 `TER`，也不跨 `TER` 恢复已经被结构选择截断的聚合物连续性。

## 生成标准残基全原子结构与拓扑

以提取的标准残基结构作为输入，使用当前体系实际采用的力场及其它参数定义来源执行 pdb2gmx。

默认使用 `-ignh`，忽略输入 PDB 中已有的氢原子，由 pdb2gmx 根据当前采用的残基定义重新生成氢原子。

pdb2gmx 的实际 chain 处理、交互选择和其它会影响输出组织的设置由执行 Agent 根据当前输入、目标力场和实际 GROMACS 行为确定；本 Skill 不额外固定 `-chainsep`、`-merge` 或把一次工作强制拆成多次 pdb2gmx 调用。实际采用的完整命令和选择必须进入正式结果记录。

## 核验并整理 pdb2gmx 输出

pdb2gmx 完成后至少检查：

1. pdb2gmx 正常结束；
2. 输入 PDB 中保留的 chain / `TER` 边界已经按本次实际 pdb2gmx 处理形成明确的输出 chain 与 `moleculetype` 组织，没有把被 `TER` 分隔的聚合物区段静默恢复为连续聚合物；
3. 各输出 chain 内的残基组成和顺序与对应输入区段一致；
4. 各输出 chain 的端基设置正确：蛋白质检查 N/C 端，核酸检查 5′/3′ 端。

按 pdb2gmx 实际形成的 `moleculetype` 整理独立 `.itp`。若某个完整分子拓扑直接写入 `.top`，将对应分子拓扑分离为独立 `.itp`，并使 `.top` 通过 `#include` 引用该 `.itp`。

## 原子映射

生成标准残基全原子结构后读取：

`../../references/atom_mapping_rules.md`

同时读取与当前 `stage1_final.pdb` 对应的 `stage1_final_map.yaml`，按共享原子映射规则维护当前处理范围内标准残基的映射，生成：

`standard.map`

`stage1_final_map.yaml` 中与当前处理范围对应的已有 atom record 保留 `original_atom_serial`、`component_id + residue_id` 和 `operations`，并按 `standard.gro` 更新 `current_atom_serial`。

pdb2gmx 新增、且输入结构中不存在对应 atom 的原子建立新记录，`original_atom_serial: null`，并使用 `2.2ADD` 记录新增操作。

## 正式结果

生成正式结果时读取：

`references/results.md`

按其中定义形成：

```text
standard_residue_topology_result.yaml
standard.gro
standard.map
standard.top
pdb2gmx 实际形成的各 moleculetype 对应独立 .itp
```

`standard_residue_topology_result.yaml` 记录本次实际依赖的上游文件、实际使用的力场及其它参数定义来源、pdb2gmx 输入 PDB、实际命令、交互选择以及正式结果文件完整路径。

完成后按仓库级 Task Execution 规则更新当前工作项状态，并按 `references/results.md` 登记正式结果。
