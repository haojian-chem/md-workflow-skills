# 2.3 参数化模型建立

本 reference 由 `../SKILL.md` 在建立 2.3 参数化模型时读取。

## 输入

建立参数化模型时使用：

- 当前 Task Sheet 中本次 2.3 工作项确定的 `TOPOLOGY_LINKED_NONSTANDARD` 残基组合；
- `classification_result.yaml` 中与这些残基相关、`judgment: CONFIRMED` 且 `topology_effect_applied: true` 的 `topology_linked_checks[]`，包括 `relation_id`、连接端点 residue identity 与 atom name；
- `stage1_final_map.yaml`，用于读取稳定的 `component_id + residue_id`、atom mapping 与既有 `operations`；
- `stage1_final.pdb`，用于读取 `TOPOLOGY_LINKED_NONSTANDARD` 残基当前重原子坐标；
- 当前 2.2 正式结果中的全原子标准残基结构与对应 map，用于提取标准残基片段及 2.2 新增 H。

## 参数化模型范围

1. 将当前 2.3 工作项需要共同参数化的全部 `TOPOLOGY_LINKED_NONSTANDARD` 残基纳入参数化模型。
2. 与这些残基存在已确认拓扑连接的标准残基完整保留。
3. 从完整保留的标准残基向外围扩展至合适截断位置。截断应尽量远离拓扑连接及其直接局部环境，优先选择对电子结构扰动较小的低极性单键，并优先在合适的非极性 C–C 单键处截断；截断后封端以恢复合理价态。避免在拓扑连接本身以及明显的极性、带电或共轭区域截断。
4. 存在多个拓扑连接位点时，分别确定各连接位点需要保留的局部结构，参数化模型取这些保留范围的并集；同一原子只保留一次，不因多个连接位点位于同一标准聚合物中而自动纳入它们之间的全部结构。

## 蛋白质体系

沿肽链在拓扑连接残基两侧各跨过一个相邻肽键，参数化模型分别延伸至相邻残基的 Cα；去除 Cα 外侧不再保留的原子，并补 H 将边界 Cα 处理为甲基。

## 核酸体系

1. 沿核酸链向 5′ 和 3′ 方向各外扩至少一个相邻核苷酸；外扩核苷酸至少完整保留糖和碱基，并保留其与参数化模型内部核苷酸之间的磷酸二酯连接。外侧边界截至糖的 O5′ / O3′，分别补 H 形成 5′-OH / 3′-OH。
2. 已保留碱基存在互补配对时，将对应的配对核苷酸纳入参数化模型，并以该配对核苷酸为中心按前条相同规则沿其所在核酸链向 5′ 和 3′ 方向外扩和封端。

## 标准残基一侧的原子变化

根据已确认的拓扑连接，确定标准残基一侧因该连接形成而不应继续保留的原子，并在参数化模型中去除这些原子。

同时记录对应 2.2 标准残基全原子结构中的原子及导致该删除的 `relation_id`。这些记录随后写入 `topology_linked_parameterization_result.yaml.standard_atom_deletions`，供 2.5 使用。

## 非标准残基补氢

- 存在对应 CCD 时，以 CCD 中的原子、键连接和 H 定义作为非标准残基补氢依据。
- 不存在对应 CCD 时，根据当前结构的成键关系、价态和局部化学环境判断补氢方式。
- 无论采用哪种依据，都必须计入当前已确认拓扑连接造成的连接状态变化，相应调整连接原子上的 H。
- 仍不能唯一确定补氢方式时，向用户确认。

## `parameterization_model.map`

`parameterization_model.map` 以 `stage1_final_map.yaml` 为稳定身份与 atom-level history 的主 baseline，不把 2.2 map 作为整体父级。

参数化模型中各类原子按以下方式维护：

1. `TOPOLOGY_LINKED_NONSTANDARD` source heavy atoms，以及标准残基片段中能够对应到 Stage 1 最终结构的 atoms：保留 `stage1_final_map.yaml` 对应 record 的 `original_atom_serial`、`component_id + residue_id` 和既有 `operations`，只更新为参数化模型中的 `output_atom_index`。
2. 标准残基片段中由 2.2 新增、Stage 1 最终结构中不存在的 H：从 2.2 map 读取对应 record，保留 `original_atom_serial: null`、`component_id + residue_id` 和包含 `2.2ADD` 的 operation history，再更新为参数化模型中的 `output_atom_index`。
3. 2.3 为 `TOPOLOGY_LINKED_NONSTANDARD` residue 新增的 H：建立新 record，`original_atom_serial: null`，保存所属 residue 的 `component_id + residue_id`，`operations = [2.3ADD]`。
4. 参数化模型截断 / 封端产生的临时 CAP atom：建立 `2.3CAP` record，`original_atom_serial: null`，`component_id: null`，`residue_id: null`。
5. 因参数化模型截取而未纳入的 atoms，以及标准残基一侧因拓扑连接而在参数化模型中去除的 atoms，不写入当前 2.3 map；标准残基一侧需要在 2.5 实际删除的原子由正式结果记录保存。

逐原子核心字段：

```yaml
output_atom_index:
original_atom_serial:
component_id:
residue_id:
operations:
```

## 结果

完成模型范围、标准残基一侧原子处理、非标准残基补氢和封端后，确定参数化模型的 atom set 与 atom order，并生成：

```text
parameterization_model.mol2
parameterized_structure.gro
parameterization_model.map
```

三者使用同一套已确定的 atom order；后续量化计算、电荷拟合和 Sobtop 参数化沿用该原子对应关系。
