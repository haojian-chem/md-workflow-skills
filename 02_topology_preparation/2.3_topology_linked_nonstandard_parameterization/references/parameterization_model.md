# 2.3 参数化模型建立

## 输入

建立参数化模型时使用：

- 当前 Task Sheet 中本次 2.3 工作项确定的 `TOPOLOGY_LINKED_NONSTANDARD` 残基组合；
- 当前 2.3 local target record；
- `classification_result.yaml` 中与这些残基相关、`judgment: CONFIRMED` 且 `topology_effect_applied: true` 的 `topology_linked_checks[]`，包括 `relation_id`、连接端点的 `component_id + residue_id` 与 atom name；
- `stage1_final_map.yaml`，用于读取稳定的 `component_id + residue_id`、原子映射与既有 `operations`；
- `stage1_final.pdb`，用于读取 `TOPOLOGY_LINKED_NONSTANDARD` 残基当前重原子坐标；
- 当前 2.2 正式结果中的全原子标准残基结构与对应 map，用于提取标准残基片段及 2.2 新增 H。

当前 2.3 target record 的 `source_target_records` 必须能够覆盖实际形成当前参数化模型的 target-scoped inputs；它可以同时指向 Stage 1 target 和 2.2 target，不通过 `target_id` 推断。

## 参数化模型范围

1. 将当前 2.3 工作项需要共同参数化的全部 `TOPOLOGY_LINKED_NONSTANDARD` 残基纳入参数化模型。
2. 与这些残基存在已确认拓扑连接的标准残基完整保留。
3. 从完整保留的标准残基向外围扩展至合适截断位置。截断应尽量远离拓扑连接及其直接局部环境，优先选择对电子结构扰动较小的低极性单键，并优先在合适的非极性 C–C 单键处截断；截断后封端以恢复合理价态。避免在拓扑连接本身以及明显的极性、带电或共轭区域截断。
4. 存在多个拓扑连接位点时，先按每个位点独立确定其需要保留的局部结构，再取所有局部保留范围的并集。同一原子只保留一次；不因多个连接位点位于同一标准聚合物中而自动纳入它们之间的全部结构。
5. 多个位点的局部保留范围合并后，必须根据**合并后的参数化模型**重新判断共享残基是否仍属于外侧封端残基，不得继续机械沿用各单个位点模型中的封端角色：
   - 如果同一标准残基分别被两个局部范围从肽链 N 端方向和 C 端方向保留，使其在并集模型中同时通过两侧肽键连接到已保留结构，则该残基已经成为参数化模型内部残基。此时按对应 2.2 全原子结构完整保留该残基，包括其侧链和既有 H；不再在该残基 Cα 处封端。
   - 如果同一标准残基虽然被多个局部范围重复涉及，但合并后仍只从肽链同一侧连接到参数化模型主体、另一侧仍是模型外部，则它仍是一个外侧封端残基。按蛋白质体系的单边 Cα 封端规则处理一次，不因被多个位点重复涉及而自动完整保留。
   - 如果该残基本身也是任一已确认拓扑连接直接涉及的标准残基，则“与 topology-linked 非标准残基存在已确认拓扑连接的标准残基完整保留”规则优先，不把它作为外围封端残基截短。
   - 共享残基一旦在合并模型中成为内部残基，不得为了缩小参数化模型而只保留其主链、删除真实侧链，形成与原残基化学身份不一致的 backbone-only 中间残基。
   - 如果现有结构、链连接关系或正式记录不足以唯一判断该共享残基在合并模型中是内部残基还是外侧封端残基，先向用户确认，不静默选择“完整残基”或“只保留局部片段”中的任一种处理。

## 蛋白质体系

对单个位点，沿肽链在拓扑连接残基两侧各跨过一个相邻肽键，参数化模型分别延伸至相邻残基的 Cα；去除 Cα 外侧不再保留的原子，并补 H 将边界 Cα 处理为甲基。

存在多个拓扑连接位点时，上述规则先用于确定每个位点的局部保留范围，再按“参数化模型范围”中的多位点合并规则统一处理。特别是：若一个位点的 C 端方向封端残基与另一个位点的 N 端方向封端残基是同一个标准残基，则合并后该残基位于两个已保留局部区域之间，属于内部残基，应完整保留；不得把两个单边 Cα 封端拼接成一个仅保留主链的残基。

## 核酸体系

1. 沿核酸链向 5′ 和 3′ 方向各外扩至少一个相邻核苷酸；外扩核苷酸至少完整保留糖和碱基，并保留其与参数化模型内部核苷酸之间的磷酸二酯连接。外侧边界截至糖的 O5′ / O3′，分别补 H 形成 5′-OH / 3′-OH。
2. 已保留碱基存在互补配对时，将对应的配对核苷酸纳入参数化模型，并以该配对核苷酸为中心按前条相同规则沿其所在核酸链向 5′ 和 3′ 方向外扩和封端。

## 标准残基一侧的原子变化

根据已确认的拓扑连接，确定标准残基一侧因该连接形成而不应继续保留的原子，并在参数化模型中去除这些原子。

同时记录对应 2.2 标准残基全原子结构中的原子及导致该删除的 `relation_id`，并写入 `topology_linked_parameterization_result.yaml.standard_atom_deletions`。

## 非标准残基补氢

- 存在对应 CCD 时，以 CCD 中的原子、键连接和 H 定义作为非标准残基补氢依据。
- 不存在对应 CCD 时，根据当前结构的成键关系、价态和局部化学环境判断补氢方式。
- 无论采用哪种依据，都必须计入当前已确认拓扑连接造成的连接状态变化，相应调整连接原子上的 H。
- 仍不能唯一确定补氢方式时，向用户确认。

## `parameterization_model.map`

`parameterization_model.map` 以 `stage1_final_map.yaml` 为重原子稳定身份与逐原子历史的主基线；对 2.2 新增 H 再从实际使用的 2.2 map 取得对应 provenance。它不把任何一个 source map 单独解释成 current target identity。

文件级至少记录：

```yaml
target_record: /absolute/path/to/current/2.3/targets/target_001.yaml
source_maps:
  stage1:
    - /absolute/path/to/stage1_final_map.yaml
  standard:
    - /absolute/path/to/standard.map

atoms:
  - output_atom_index: 1
    original_atom_serial: 125
    component_id: component_001
    residue_id: residue_001
    operations: [1.3ADD, ...]
```

其中：

- `target_record` 指向当前 2.3 local target record；
- `source_maps.stage1` 逐项记录本次模型实际使用的 Stage 1 map；
- `source_maps.standard` 只记录本次实际使用的 2.2 maps；没有使用时为空列表或省略该类别；
- target ancestry 由 current target record 的 `source_target_records` 负责，`source_maps` 只记录 atom provenance 的实际输入文件，不替代 target lineage。

参数化模型中各类原子按以下方式维护：

1. `TOPOLOGY_LINKED_NONSTANDARD` 来源重原子，以及标准残基片段中能够对应到 `stage1_final.pdb` 的原子：保留 `stage1_final_map.yaml` 对应记录的 `original_atom_serial`、`component_id + residue_id` 和既有 `operations`，只更新为参数化模型中的 `output_atom_index`。
2. 标准残基片段中由 2.2 新增、`stage1_final.pdb` 中不存在的 H：从 2.2 map 读取对应记录，保留 `original_atom_serial: null`、`component_id + residue_id` 和包含 `2.2ADD` 的 `operations` 历史，再更新为参数化模型中的 `output_atom_index`。
3. 2.3 为 `TOPOLOGY_LINKED_NONSTANDARD` 残基新增的 H：建立新记录，`original_atom_serial: null`，保存所属残基的 `component_id + residue_id`，`operations = [2.3ADD]`。
4. 参数化模型截断 / 封端产生的临时原子：建立 `2.3CAP` 记录，`original_atom_serial: null`，`component_id: null`，`residue_id: null`。
5. 因参数化模型截取而未纳入的原子，以及标准残基一侧因拓扑连接而在参数化模型中去除的原子，不写入当前 2.3 map；标准残基一侧需要从最终结构 / 拓扑中删除的原子由正式结果记录保存。

逐原子核心字段：

```yaml
output_atom_index:
original_atom_serial:
component_id:
residue_id:
operations:
```

## 结果

完成模型范围、标准残基一侧原子处理、非标准残基补氢和封端后，确定参数化模型的原子集合与原子顺序，并生成：

```text
parameterization_model.mol2
parameterized_structure.gro
parameterization_model.map
```

三者使用同一套已确定的原子顺序；后续量化计算、电荷拟合和 Sobtop 参数化沿用该原子对应关系。

生成后确认 `parameterization_model.map.target_record` 指向当前 2.3 target record，且 target record 的 `source_target_records` 能解释 `source_maps` 所属 target-scoped inputs 的实际来源关系。
