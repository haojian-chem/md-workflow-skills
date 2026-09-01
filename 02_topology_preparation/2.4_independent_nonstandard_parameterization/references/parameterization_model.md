# 2.4 参数化模型建立

## 当前工作项与实例集合

当前工作项直接处理 2.1 已拆分确定的一个独立非标准参数化对象，不在本环节重新分类或重新分组。

当前 Task Sheet 中不要求必须同时出现 2.1，但在执行 2.4 前必须存在一个仍适用、可明确定位的已完成 2.1 topology-preparation setup；它可以来自当前 Task Sheet，也可以来自同一科研任务的前序 Task Sheet。

真正执行当前 processing object 时，使用当前 2.4 local target record。其 `source_target_records` 记录当前实例集合实际来自的 upstream target record(s)。

根据当前工作项的残基名，从正式 `classification_result.yaml` 与实际 source `stage1_final_map.yaml` 中定位当前工作项覆盖的全部实例，并持续使用各实例既有的 `component_id + residue_id`。

## 同名实例参数定义一致性检查

对当前工作项中的全部同名实例检查是否存在会导致它们不应共用同一套参数定义的差异，至少关注：

- 质子化状态；
- 立体构型；
- 其它会改变当前分子化学状态或参数定义的差异。

普通空间构象差异本身不构成拆分参数定义的理由。

若发现同名实例实际需要不同参数定义，不在当前工作项内静默拆分或为同一残基名生成多套参数；提醒用户为需要不同参数定义的对象设置不同残基名后再继续，并在必要时返回 2.1 更新处理对象划分。

## 代表实例

完成上述一致性检查后，从当前工作项对应的同名实例中选择一个实例作为代表实例，用于建立参数化模型并完成后续量化计算、电荷拟合和 Sobtop 参数化。

代表实例的选择属于当前任务上下文中的执行判断；不建立固定评分体系或额外分组规则。

代表实例属于 current 2.4 target 的实际实例集合，不因为被选作代表而形成新的 target identity。

## 提取重原子结构

从实际 source `stage1_final.pdb` 提取代表实例的当前重原子坐标，并使用对应 `stage1_final_map.yaml` 中已有的 `component_id + residue_id` 与逐原子记录建立对应关系。

不得仅根据残基名、chain、resid 或原子顺序重新推断原子身份。

`stage1_final_map.yaml.target_record` 应能够在 current 2.4 target record 的 `source_target_records` 中得到解释；如果当前实例集合来自多个 Stage 1 branches，则逐项使用对应 source structure / map，而不是把不同 branch 的同名实例按 `target_id` 合并。

## 补氢

按照当前已经确定的化学状态建立代表实例的全原子结构：

- 存在适用 CCD 时，以 CCD 中的原子、键连接和 H 定义作为补氢依据；
- 不存在适用 CCD 时，根据当前结构的成键关系、价态和局部化学环境判断补氢方式；
- 当前任务或用户已经明确指定的质子化状态、总电荷或其它化学状态必须与补氢结果保持一致；
- 仍不能唯一确定补氢方式时，向用户确认后再继续。

当前工作处理完整独立参数化对象，不引入 topology-linked 参数化中的标准残基片段、截断或 CAP。

## 原子集合与原子顺序

代表实例补氢完成后，确定参数化模型的完整原子集合与原子顺序。

随后生成：

```text
parameterization_model.mol2
parameterization_model.map
```

二者描述同一个代表实例并采用同一原子集合与原子顺序。后续 OPT / FREQ / SP、电荷拟合、`parameterization.chg` 和 Sobtop 参数化必须维持可确定的原子对应关系。

## `parameterization_model.map`

`parameterization_model.map` 只描述本次实际完成参数化的代表实例，但文件级保存 current target 与实际 source map provenance：

```yaml
target_record: /absolute/path/to/current/2.4/targets/target_001.yaml
source_maps:
  - /absolute/path/to/stage1_final_map.yaml

atoms:
  - output_atom_index: 1
    original_atom_serial: 125
    component_id: component_001
    residue_id: residue_004
    operations: [1.3ADD, ...]
```

其中：

- `target_record` 指向 current 2.4 local target record；
- `source_maps` 只列本次代表实例 / 当前参数化对象实际使用的 Stage 1 map(s)；
- source map 自己的 `target_record` 仍指向各自 upstream target；current 2.4 target 与这些 upstream targets 的关系由 current target record 的 `source_target_records` 表示；
- `source_maps` 记录 atom provenance 文件，不替代 target lineage。

来自代表实例对应 `stage1_final.pdb` 的原子：

- 保留对应 `stage1_final_map.yaml` 记录的 `original_atom_serial`；
- 保留该原子的 `component_id + residue_id`；
- 保留已有 `operations`；
- 只更新为 `parameterization_model.mol2` 中对应的 `output_atom_index`。

当前工作项新增 H：

```text
original_atom_serial = null
component_id + residue_id = 所属代表实例的既有身份
operations = [2.4ADD]
```

逐原子核心字段为：

```yaml
output_atom_index:
original_atom_serial:
component_id:
residue_id:
operations:
```

`parameterization_model.map` 不描述当前工作项中其它同名实例；当前工作项全部实例的结构映射由 `parameterized_structure.map` 记录。

生成后确认：

- `parameterization_model.map.target_record` 指向 current 2.4 target record；
- current target record 的 `source_target_records` 能解释实际 `source_maps` 所属 source targets；
- 不通过相同 residue name 或 `target_id` 建立 branch identity。
