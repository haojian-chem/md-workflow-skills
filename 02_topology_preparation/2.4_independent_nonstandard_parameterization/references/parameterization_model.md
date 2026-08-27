# 2.4 参数化模型建立

## 当前工作项与实例集合

2.4 直接处理当前 Task Sheet 由 2.1 建立的一个工作项，不在本环节重新分类或重新分组。

根据当前工作项的残基名，从 1.2 正式 `classification_result.yaml` 与 `stage1_final_map.yaml` 中定位当前工作项覆盖的全部实例，并持续使用各实例既有的 `component_id + residue_id`。

## 同名实例参数定义一致性检查

选择代表实例前，检查当前工作项中的同名实例是否存在会导致其不应共用同一套参数定义的差异，至少关注：

- 质子化状态；
- 立体构型；
- 其它会改变当前分子化学状态或参数定义的差异。

普通空间构象差异本身不构成拆分参数定义的理由。

若发现同名实例实际需要不同参数定义，不在 2.4 内静默拆分或为同一 residue name 生成多套参数；提醒用户为需要不同参数定义的对象设置不同 residue name 后再继续。

## 代表实例

通过上述检查后，从当前工作项对应的同名实例中选择一个实例作为代表实例，用于建立参数化模型并完成后续量化计算、电荷拟合和 Sobtop 参数化。

代表实例的选择属于当前任务上下文中的执行判断；不建立固定评分体系或额外分组规则。

## 提取重原子结构

从 `stage1_final.pdb` 提取代表实例的当前重原子坐标，并使用 `stage1_final_map.yaml` 中已有的 `component_id + residue_id` 与逐原子记录建立对应关系。

不得仅根据 residue name、chain、resid 或原子顺序重新推断原子身份。

## 补氢

按照当前已经确定的化学状态建立代表实例的全原子结构：

- 存在适用 CCD 时，以 CCD 中的原子、键连接和 H 定义作为补氢依据；
- 不存在适用 CCD 时，根据当前结构的成键关系、价态和局部化学环境判断补氢方式；
- 当前任务或用户已经明确指定的质子化状态、总电荷或其它化学状态必须与补氢结果保持一致；
- 仍不能唯一确定补氢方式时，向用户确认后再继续。

2.4 处理完整独立参数化对象，不引入 topology-linked 参数化中的 standard fragment、截断或 CAP。

## 原子集合与原子顺序

代表实例补氢完成后，确定参数化模型的完整原子集合与原子顺序。

随后生成：

```text
parameterization_model.mol2
parameterization_model.map
```

二者描述同一个代表实例并采用同一原子集合与原子顺序。后续 OPT / FREQ / SP、电荷拟合、`parameterization.chg` 和 Sobtop 参数化必须维持可确定的原子对应关系。

## `parameterization_model.map`

`parameterization_model.map` 只描述代表实例。

来自 `stage1_final.pdb` 的原子：

- 保留 `stage1_final_map.yaml` 对应 record 的 `original_atom_serial`；
- 保留该原子的 `component_id + residue_id`；
- 保留已有 `operations`；
- 只更新为 `parameterization_model.mol2` 中对应的 `output_atom_index`。

2.4 新增 H：

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

`parameterization_model.map` 不描述当前工作项中其它同名实例；全部实例的最终结构映射由 `parameterized_structure.map` 记录。
