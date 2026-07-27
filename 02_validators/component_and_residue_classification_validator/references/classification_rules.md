# 组分与残基分类规则

## 1. 目标与边界

本规则只定义 `structure_preparation_workflow` 1.2 的模型范围、结构事实采集、残基分类、重原子核验、可能共价连接、金属配位和结果整合。

本步骤：

- 只读取并分析结构，不修改、重排、删除或补全结构；
- 不选择需要保留的链、配体、水或离子；
- 不处理 altLoc/occupancy；
- 不分配质子化状态；
- 不生成拓扑；
- 不判断后续结构完整性 gate；
- 不直接向用户提问，所有确认事项完整扫描后统一交给 Manager。

模型范围无法建立、输入哈希失配、配置/schema 无效或输出无法可靠生成时属于技术失败。科学歧义、分类冲突和关系候选不得伪装成技术失败。

## 2. 模型范围

执行顺序固定为：

```text
inspect_model_scope
→ selected model resolved
→ full classification pass
```

- 单 model 自动选择；
- 多 model 只枚举 model ID 和最小链/残基/原子计数，随后请求用户选择；
- selected model 未解决前不执行完整残基分类；
- model ID 使用源结构中的 model 标识，不额外生成 model UUID。

## 3. 精确名称规则

结构中的 `residue_name` 和 `atom_name` 必须原样保留并区分大小写：

```text
HEM != Hem != hem
FE != Fe
```

不得执行：

- 大小写归一化；
- alias 合并；
- 正则匹配；
- 编辑距离或模糊名称匹配；
- 依据近似名称自动选择 CCD/RTP 模板。

结构残基名与 CCD ID 不同，只能通过项目定义中的显式 `ccd_id` 建立映射。

## 4. 分类字段

### 4.1 `polymer_class`

允许值：

```text
POLYMER
BRANCHED
NONPOLYMER
WATER
```

### 4.2 `topology_class`

允许值：

```text
STANDARD_RESIDUE
COVALENTLY_LINKED_NONSTANDARD
INDEPENDENT_NONSTANDARD
SOLVENT_COMPONENT
ION_COMPONENT
```

`UNKNOWN`、`UNRESOLVED` 和 `CONFLICT` 不是分类值，而是 `resolution_status`。

### 4.3 合法组合

| polymer_class | topology_class |
|---|---|
| `POLYMER` | `STANDARD_RESIDUE`, `COVALENTLY_LINKED_NONSTANDARD` |
| `BRANCHED` | `STANDARD_RESIDUE`, `COVALENTLY_LINKED_NONSTANDARD`, `INDEPENDENT_NONSTANDARD` |
| `NONPOLYMER` | `COVALENTLY_LINKED_NONSTANDARD`, `INDEPENDENT_NONSTANDARD`, `SOLVENT_COMPONENT`, `ION_COMPONENT` |
| `WATER` | `SOLVENT_COMPONENT` |

## 5. 项目级残基定义

`project_residue_definitions.yaml` 使用列表：

```yaml
schema_version: "1.0"
residue_definitions:
  - residue_name: HEM
    polymer_class: NONPOLYMER
    topology_class: COVALENTLY_LINKED_NONSTANDARD
    ccd_id: HEM
```

规则：

- `residue_name`、`polymer_class`、`topology_class` 必填；
- `ccd_id` 可选，未提供时等于精确 `residue_name`；
- 同一个精确 `residue_name` 只允许定义一次；
- v1 不包含 model、chain、source residue number 或连接原子限制；
- 一条定义适用于 selected model 中所有精确同名实例。

## 6. 分类来源顺序

### 6.1 `REGISTRY`

```text
项目定义
→ 精确 Skill registry
→ entity/polymer context
```

项目定义与 Skill registry 同时命中时：

- 两个分类标签一致：接受，并记录一致性证据；
- 任一标签不同：记录 `PROJECT_REGISTRY_CLASSIFICATION_CONFLICT`，完成其余检查后统一确认；
- 不设置自动优先级覆盖冲突。

### 6.2 `FORCE_FIELD_ANALYSIS`

```text
项目定义
→ 所选力场的精确 RTP residue block
→ 仍未解决时使用精确 Skill registry
→ entity/polymer context
```

力场是否识别某个残基只由 `*.rtp` 中的精确 residue block 名称决定。`residuetypes.dat` 和 RTP 文件名不参与识别。

项目定义与 RTP 分类同时命中时：

- 两个标签一致：接受；
- 标签不同：记录 `PROJECT_FORCE_FIELD_CLASSIFICATION_CONFLICT`；
- 项目未定义但 RTP 命中：采用 RTP 分类，不再并行咨询 Skill registry；
- 只有项目和 RTP 都未解决时才使用 Skill registry fallback。

## 7. RTP 与端基

### 7.1 重复 RTP 定义

- 非水残基的同一精确 RTP 名称定义多次：`DUPLICATE_FORCE_FIELD_RESIDUE_TEMPLATE`，统一人工确认；
- 水允许同一力场目录存在 TIP3P、OPC 等多种水模型；本步骤不选择水模型，也不使用 RTP 水原子名核验原始水；
- 不以 RTP 文件名推测残基类别。

### 7.2 普通与端基模板

普通内部标准残基使用精确同名 RTP block。

N/C 端和 5′/3′端标准残基必须先确定端基角色，再使用明确的 terminal-template mapping 选择端基 RTP block：

```text
terminal role
+ source residue name
→ explicit RTP terminal residue name
```

不得通过删除或添加 `N`、`C`、`5`、`3` 等字符猜测端基名称。若 terminal mapping 不唯一，则产生 `TERMINAL_RTP_TEMPLATE_AMBIGUOUS`；若没有可用映射或完整端基 RTP block，则正式重原子检查标为参考模板不可用，不回退到普通内部模板宣称通过。

本版本不应用 `.n.tdb`、`.c.tdb` 或其他 terminal patch 合成模板。

## 8. 重原子检查

### 8.1 参考矩阵

| 模式 | 分类 | 重原子参考 |
|---|---|---|
| `REGISTRY` | 标准残基 | CCD |
| `REGISTRY` | 相连/独立非标准残基 | CCD |
| `FORCE_FIELD_ANALYSIS` | 标准残基 | 已选 RTP block，包括明确端基 block |
| `FORCE_FIELD_ANALYSIS` | 相连/独立非标准残基 | CCD |
| 任一模式 | 普通水、普通离子 | 默认不检查 |

### 8.2 输出状态

```text
HEAVY_ATOMS_COMPLETE
MISSING_EXPECTED_HEAVY_ATOMS
UNEXPECTED_HEAVY_ATOMS
MISSING_AND_UNEXPECTED_HEAVY_ATOMS
ATOM_NAME_MAPPING_REQUIRED
REFERENCE_TEMPLATE_UNAVAILABLE
NOT_PERFORMED
NOT_APPLICABLE
```

只记录缺少和多出的原子名称，不将缺失原子分类为主链、侧链、端基或金属中心原子。

CCD alternate atom name 只能形成待处理映射证据，不得静默改名。

### 8.3 altLoc

只要残基存在多个 altLoc：

```text
conformation status: MULTIPLE_CONFORMATIONS
heavy atom check: NOT_PERFORMED
reason: MULTIPLE_CONFORMATIONS_PRESENT
```

不得将多个构象的原子并集作为一个伪完整残基进行比较。

## 9. CCD 规则

唯一 component ID 的确定方式：

```text
显式 project ccd_id
否则 exact residue_name
```

获取顺序：

```text
项目已有 snapshot
→ 用户指定本地目录
→ 共享 cache
→ 按 retrieval_policy 远程下载
```

规则：

- 不扫描用户未指定的文件系统目录；
- 本地目录默认只查找精确 `<ccd_id>.cif`；
- 文件名匹配后仍需核验文件内部 component ID；
- 有效外部文件复制到项目 `reference_data/ccd/` 并核验复制前后 SHA-256；
- 项目 snapshot 是本次结果的权威 CCD 文件；
- 单个 component 获取失败只记录并继续；
- CCD 机制整体不可用或 snapshot 无法一致写入才是技术失败；
- 多个不同内容的有效本地候选进入统一确认。

## 10. 缺失残基

### 10.1 PDB/mmCIF

使用可用的预期序列、实际坐标以及 PDB `REMARK 465` 或 mmCIF unobserved-residue 记录建立证据。不得仅凭作者编号跳号认定残基缺失。

1.2 只记录缺失了哪些残基，不判断缺失区域属于内部、N 端、C 端或其他区域。

正式缺失残基记录必须具有作者原始编号：

```yaml
source_resid:
  number: "145"
  insertion_code: null
```

插入码按源文件原样保留；残基缺失不等于插入码必然为空。

作者编号无法确定时：

- 不生成虚构编号；
- 不使用 sequence position 替代正式 `source_resid`；
- 继续完成所有其他检查；
- 最后统一返回 `MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE`。

链归属无法确定时同样累计为 `MISSING_RESIDUE_CHAIN_UNRESOLVED`。

### 10.2 AF3 CIF

AF3 CIF 默认不执行缺失残基检查。只有用户提供 AF3 输入 JSON、FASTA 或等价序列参考时才检查。没有输入序列时记录：

```text
NOT_PERFORMED
AF3_INPUT_SEQUENCE_NOT_PROVIDED
```

这不表示已经确认没有缺失残基。

## 11. `chain_groups` 与 `chain_index`

`chain_index` 是本步骤建立的内部组分归属编号，不等于源文件 chain ID。

基础规则：

- 每条 polymer/branched chain 一个 `chain_index`，按 selected model 中首次出现顺序分配；
- 每种精确名称的普通水和普通离子汇总为一个组；
- 同种、同分类、无特殊关系或异常的重复独立小分子可以汇总；
- 普通汇总成员不在 `residue_records` 中逐实例展开；
- 存在 altLoc、分类冲突、模板异常、显式/候选关系或项目特殊处理的实例从汇总组中提出并单独记录；
- 独立小分子即使源文件与某条 polymer chain 使用同一作者 chain ID，也使用独立 `chain_index`，并记录 source association。

最终整合时：

- 非标准组分与一条 polymer chain 存在确认的 topology-forming relation：编入该 polymer chain 的 `chain_index`；
- 与多条 polymer chain 相连：独立 `MULTICHAIN_LINKED_COMPONENT` group，并记录 `linked_polymer_chain_indices`；
- 只与其他非标准组分形成 topology-forming connected component：建立 `LINKED_NONSTANDARD_GROUP`；
- 标准残基参与连接或配位时默认仍保持 `STANDARD_RESIDUE`。

## 12. 可能共价连接

`possible_connections.yaml` 只支持已知精确原子对：

```yaml
possible_connections:
  - label: LIG_CYS_LINK
    partner_1: {residue_name: LIG, atom_name: C1}
    partner_2: {residue_name: CYS, atom_name: SG}
    distance_range_angstrom: {minimum: 1.5, maximum: 2.3}
```

规则：

- 两侧无方向，正反重复定义视为同一条；
- `minimum`、`maximum` 均必填；
- 枚举全部唯一实例组合，不自动选择最近的一对；
- 同一原子不得与自身配对；
- 显式 PDB/mmCIF 连接和几何距离分别记录；
- 只有显式确认或用户确认后的几何候选才能影响 topology；
- 输入定义本身绝不创建结构连接。

主要状态：

```text
CONFIRMED_BY_STRUCTURE
GEOMETRY_SUPPORTED_CANDIDATE
NOT_GEOMETRICALLY_SUPPORTED
CONNECTION_DEFINITION_CONFLICT
PARTNER_NOT_FOUND
ATOM_NOT_FOUND
GEOMETRY_NOT_EVALUATED_MULTIPLE_CONFORMATIONS
```

只有几何支持候选和定义冲突进入人工确认。

## 13. 金属配位

`possible_coordination.yaml` 明确金属端、供体端、元素、距离范围和 topology effect：

```yaml
possible_coordination:
  - label: HEM_FE_CYS
    metal: {residue_name: HEM, atom_name: FE, element: Fe}
    donor: {residue_name: CYS, atom_name: SG, element: S}
    distance_range_angstrom: {minimum: 1.8, maximum: 2.7}
    topology_effect:
      promote_nonstandard_to_linked: true
```

规则：

- 金属端与供体端有方向；
- 元素字段必填并在几何判断前核验；
- 同一金属具有多个不同供体是合法的，不自动构成冲突；
- 关系类型始终记录为 `METAL_COORDINATION`；
- `promote_nonstandard_to_linked: true` 只在显式关系确认或用户确认几何候选后生效；
- HEM–CYS/HIE 等 topology-forming coordination 可以将 HEM 提升为 `COVALENTLY_LINKED_NONSTANDARD`；
- Mg、Zn 等是否改变 topology 必须由项目定义明确，不能只凭距离自动判断；
- `false` 只记录配位，不改变 topology 或 chain group。

主要状态：

```text
CONFIRMED_BY_STRUCTURE
GEOMETRY_SUPPORTED_COORDINATION_CANDIDATE
NOT_GEOMETRICALLY_SUPPORTED
COORDINATION_DEFINITION_CONFLICT
PARTNER_NOT_FOUND
ATOM_NOT_FOUND
ELEMENT_MISMATCH
ELEMENT_UNRESOLVED
GEOMETRY_NOT_EVALUATED_MULTIPLE_CONFORMATIONS
```

## 14. 完整扫描与确认

除模型选择 barrier 外，正式 1.2 解析不得在遇到第一项科学问题时停止。

执行方式：

```text
完成全部可执行残基分类
→ 完成缺失残基和重原子检查
→ 完成全部可能共价连接定义
→ 完成全部金属配位定义
→ 汇总仍需确认的问题
→ 生成 PENDING_USER_CONFIRMATION 或 COMPLETE 结果
```

以下问题进入统一确认：

- 项目定义与 Skill/力场分类冲突；
- 非水 RTP 重复定义；
- 端基 RTP 映射歧义；
- 几何支持的共价或配位候选；
- 显式关系与项目定义冲突；
- 缺失残基作者编号或链归属无法确定；
- AF3/序列参考冲突；
- 多个不同内容的有效本地 CCD 候选。

明确缺失重原子、单个 CCD 获取失败、partner/atom 不存在、无显式关系的元素异常、几何不支持和多构象事实只记录，不自动要求用户确认。

## 15. `specbond.dat` 与其他力场文件

1.2 不读取或应用：

```text
residuetypes.dat
*.n.tdb
*.c.tdb
specbond.dat
```

`specbond.dat` 只表示力场可能支持某种特殊连接，不证明当前结构存在该连接。力场对已确认特殊键的支持能力由后续 topology preparation 处理。
