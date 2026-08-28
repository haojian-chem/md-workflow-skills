# `moleculetype` 组织

对当前 Task Sheet 指定进入拓扑整合的全部 residue / component 进行 `moleculetype` 组织。

组织时结合这些对象之间已确认的 topology-linked 关系，以及各前置拓扑结果提供的结构、映射和拓扑信息。

## 组织规则

- topology-linked 非标准残基连接一条标准链时，将该非标准残基与相关标准链组织到同一个
  `moleculetype`；
- topology-linked 非标准残基连接多条标准链时，将该非标准残基与相关标准链组织到同一个
  `moleculetype`；
- 多个 topology-linked 非标准残基连接同一条标准链时，将该标准链与这些非标准残基组织到同一个
  `moleculetype`；
- 未参与 topology-linked 关系的标准链，如无其它拓扑信息要求改变其组织，保留标准残基拓扑生成正式结果中的
  `moleculetype` 组织；
- 独立非标准残基、solvent 和 ion 按各自采用的拓扑定义组织 `moleculetype`；不存在额外连接关系时，
  不与其它对象合并。

`moleculetype` 组织只建立 GROMACS 拓扑所需的分子类型组织，不改变既有 component 身份、
`component_id + residue_id`、component 的 residue 组成或已经确认的 topology-linked 关系。

同一个 `moleculetype` 同时包含标准残基与非标准残基时，组织顺序为标准残基在前、非标准残基在后。
各来源结构和 `.itp` 内部已有的 residue / atom 相对顺序保持不变。

## `moleculetype` 名称

完成组织后：

- 标准残基、topology-linked 非标准残基和独立非标准残基形成的 `moleculetype`，按当前组织顺序从 1
  开始连续命名为 `molecule_1`、`molecule_2`、`molecule_3`……；
- solvent / ion 对应的 `moleculetype` 使用其 residue name 作为名称。

对于本次整合实际生成的 `.itp`，确定的名称写入对应 `[ moleculetype ]`。
