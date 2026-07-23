# 组分与残基分类规则

## 1. 分类目标

分类服务于后续链/组分选择和拓扑路线分流，不等同于完整结构质量验证。

每个 residue/component 同时记录：

- 结构身份：model、entity、chain、residue ID；
- `polymer_class`；
- `topology_class`；
- `component_role`；
- 连接证据；
- 置信度；
- 是否需要人工决定。

不得仅用 residue name 生成最终结论。

## 2. Polymer class

允许：

```text
PROTEIN
DNA
RNA
CARBOHYDRATE
OTHER_POLYMER
NONPOLYMER
WATER
ION
UNKNOWN
```

优先级：

1. mmCIF entity/polymer 类型；
2. PDB SEQRES 与标准主链模式；
3. 坐标中的主链连续性；
4. residue registry；
5. 名称启发式。

低优先级证据不得覆盖冲突的高优先级证据。

## 3. Topology class

### STANDARD_RESIDUE

满足任一：

- canonical registry 中的标准氨基酸、DNA 或 RNA residue；
- alias registry 明确归入标准别名，且当前原子/聚合物上下文没有冲突。

“标准”仅表示可进入标准残基路线候选，不保证任一具体力场无需额外处理。

### COVALENTLY_LINKED_NONSTANDARD

满足至少一种确定性证据：

- mmCIF/PDB 有显式共价连接记录；
- 非标准 residue 位于连续聚合物主链中，且两侧或一侧主链连接证据充分；
- 已解决用户决定或上游可信记录明确确认共价连接。

金属配位、氢键、盐桥和空间接触不属于此类证据。

### INDEPENDENT_NONSTANDARD

非标准组分没有确定共价连接到标准聚合物。它可以是配体、辅因子、游离糖、缓冲剂或其他 nonpolymer。

存在金属配位时仍可保持该 topology class，并通过独立 coordination relation 表达。

### SOLVENT / ION

由 registry、元素组成和 entity metadata 支持。多原子离子与普通小分子存在歧义时不得仅靠名称自动分类。

### UNKNOWN

当前证据不足以可靠归入其他类别，或证据冲突。若影响后续选择或拓扑路线，必须生成 blocking decision。

## 4. Component role

允许：

```text
POLYMER
MODIFIED_POLYMER_RESIDUE
LIGAND
COFACTOR
GLYCAN
SOLVENT
ION
BUFFER_OR_ADDITIVE
UNKNOWN
```

role 是功能/工作流提示，不替代 topology class。不能仅凭常见生化用途确定 role；证据不足时使用 UNKNOWN。

## 5. 显式连接

### mmCIF

优先读取：

- `_struct_conn`；
- polymer/entity linkage；
- branch scheme 和 glycan linkage；
- atom/site identifiers。

连接类型必须保留源字段，不把所有 `struct_conn` 行统一解释为共价键。

### PDB

读取：

- `LINK`；
- `SSBOND`；
- `CONECT`；
- SEQRES/ATOM 主链上下文。

`CONECT` 对金属中心可能表示配位或软件输出习惯，必须结合元素和连接类型解释。

## 6. 几何共价候选

几何候选只用于发现可能缺失的连接记录。

至少记录：

- 两端原子和 residue；
- 距离；
- 使用的元素阈值；
- 是否跨 residue/component；
- 是否与主链连续性一致；
- altLoc/occupancy 影响；
- candidate confidence。

不得因为距离短于阈值直接将对象改为 `COVALENTLY_LINKED_NONSTANDARD`。

## 7. 金属配位候选

金属配位与共价拓扑分类正交。

- 显式 coordination record：记录为 `EXPLICIT_COORDINATION`；
- 仅满足距离规则：记录为 `GEOMETRIC_COORDINATION_CANDIDATE`；
- 受 altLoc、occupancy 或边界条件影响：记录为 `AMBIGUOUS_CLOSE_CONTACT`。

配位关系可以跨标准 residue、非标准 residue、离子或水，但不自动改变任何一方的 topology class。

## 8. 聚合物连续性

蛋白质主链连续性至少使用 C–N 连接和 residue 顺序；核酸使用糖磷酸骨架连接。只依赖 residue 编号连续不充分。

以下情况需要降低置信度：

- insertion code；
- 缺失主链原子；
- 多模型差异；
- altLoc 覆盖连接原子；
- 非常规环化或交联；
- 晶体对称相关连接。

## 9. 多模型

- 各模型组分和分类一致：保留全部统计，给 non-blocking warning；
- 分类不同：在未指定模型时生成 blocking decision；
- task 已指定模型：仅对该模型作 gate 分类，其他模型可作为附录摘要。

## 10. 置信度

```text
HIGH
MEDIUM
LOW
```

建议：

- HIGH：显式 entity/connection + 一致坐标证据；
- MEDIUM：聚合物连续性或 registry + 无冲突证据；
- LOW：名称/距离启发式、缺失关键原子或证据冲突。

LOW 且影响后续路线时必须请求决定。

## 11. 阻断与非阻断

阻断：

- 会改变链/组分保留对象；
- 会改变标准/相连非标准/独立非标准拓扑路线；
- 模型选择改变分类；
- 输入标识不足以唯一引用对象。

非阻断：

- 仅影响注释而不影响对象选择；
- 配位候选未改变共价分类；
- 可在下一专门 Validator 中处理的 altLoc/occupancy 提示。

## 12. 禁止推断

不得：

- 将 HETATM 等同于独立非标准组分；
- 将 ATOM 等同于标准 residue；
- 将金属近距离接触等同于共价键；
- 将 residue name 相同等同于化学状态相同；
- 将具体力场支持与本分类结果混为一谈；
- 将未知对象自动删除或忽略。