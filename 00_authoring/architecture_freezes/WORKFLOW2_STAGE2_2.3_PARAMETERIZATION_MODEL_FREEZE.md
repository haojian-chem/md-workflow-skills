# Workflow 2 Stage 2 — 2.3 参数化模型规则冻结

Status: CURRENT AUTHORING REFERENCE

本文件记录 `2.3 Topology-linked nonstandard parameterization` 中已经敲定的参数化模型输入与一般截取规则，作为后续继续设计和正式 Skill generation 的 authoring input。

Stage 2 总体架构继续读取：

`WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md`

## 1. 输入文件与用途

- **Task Sheet**：读取本次需要共同参数化的 `TOPOLOGY_LINKED_NONSTANDARD` 残基集合。
- **`classification_result.yaml`**：读取与这些残基相关且 `topology_effect_applied: true` 的 `confirmed_relations` 及其端点残基和原子身份。
- **`stage1_final_map.yaml`**：读取上述残基和连接端点在 Stage 1 最终结构中的映射。
- **`stage1_final.pdb`**：读取 `TOPOLOGY_LINKED_NONSTANDARD` 残基的当前重原子坐标。
- **2.2 全原子结构及对应 `*.map`**：读取参数化模型所需标准残基的全原子坐标、身份及原子对应关系。

## 2. 参数化模型截取的一般规则

1. 需要共同参数化的全部 `TOPOLOGY_LINKED_NONSTANDARD` 残基均纳入参数化模型。
2. 与这些残基存在拓扑连接的标准残基完整保留。
3. 从完整保留的标准残基向外围扩展至合适的截断位置；截断应尽量远离拓扑连接及其直接局部环境，优先选择对电子结构扰动较小的低极性单键，并优先在合适的非极性 C–C 单键处截断；截断后进行封端以恢复合理价态。避免在拓扑连接本身以及明显的极性、带电或共轭区域中截断。
4. 存在多个拓扑连接位点时，分别按照上述规则确定各连接位点需要保留的局部结构，参数化模型取这些保留范围的并集；同一原子只保留一次，不因多个连接位点位于同一标准聚合物中而自动纳入它们之间的全部结构。

## 3. 后续专项规则

蛋白质、核酸及其它适用体系的具体截取与封端规则在上述一般规则下分别讨论和冻结。
