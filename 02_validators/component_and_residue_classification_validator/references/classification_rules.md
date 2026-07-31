# 组分与残基分类规则

# 1. 定义范围

本文件是 `structure_preparation_workflow` 1.2 的科学判定语义唯一权威来源，定义：

- model 范围；
- 结构事实与名称身份；
- 残基分类；
- RTP/CCD 参考；
- 缺失残基与重原子检查；
- 可能共价连接；
- 金属配位；
- topology effect；
- 确认事项聚合。

执行编排、层级权限、用户交互和管理目录提交权分别由 Validator `SKILL.md`、上级 Workflow 和 `layer_boundaries.md` 定义，本文件禁止重复定义。

模型范围无法建立、输入哈希失配、配置/schema 无效或输出无法可靠生成时属于技术失败。科学歧义、分类冲突和候选关系必须写入结构化结果，禁止伪装成技术失败。

# 2. 模型范围

执行顺序固定为：

```text
inspect_model_scope
→ selected model resolved
→ full classification pass
```

规则：

- 单 model 自动选择；
- 多 model 只枚举 model ID 和最小链/残基/原子计数，随后形成用户选择请求；
- selected model 未解决前，禁止执行完整残基分类；
- model ID 使用源结构中的 model 标识，禁止额外生成 model UUID。

# 3. 精确名称规则

结构中的 `residue_name` 和 `atom_name` 必须原样保留并区分大小写：

```text
HEM != Hem != hem
FE atom name != Fe element symbol
```

禁止执行：

- 大小写归一化；
- alias 合并；
- 正则匹配；
- 编辑距离或模糊名称匹配；
- 依据近似名称自动选择 CCD/RTP 模板。

结构残基名与 CCD ID 不同，只允许通过项目定义中的显式 `ccd_id` 建立映射。


## 3.1 源身份与当前身份

每个已观察残基和关系端点必须同时保存两套正式身份，并使用不同字段名：

```yaml
source_identity:
  source_model_id: "1"
  source_chain_id: A
  source_resid: {number: "145", insertion_code: A}
  source_residue_name: CYS

current_identity:
  current_model_id: "1"
  current_chain_id: A
  current_resid: {number: "145", insertion_code: A}
  current_residue_name: CYS
```

关系端点分别追加 `source_atom_name` 和 `current_atom_name`。规则：

- `source_*` 是输入来源追溯身份，后续结构 revision 禁止覆盖；
- `current_*` 是本次实际读取的 STRUCTURE revision 身份，只能由真实存在的新结构更新；
- 1.2 禁止修改结构，因此 `OBSERVED` 实例的 source/current 值应相等，但两套字段仍必须分别输出；
- `MISSING_EXPECTED` 残基只有 `source_identity`，`current_identity` 必须为 `null`；
- `chain_index` 是逻辑分组编号，必须位于 identity 外部；topology effect 可以改变 `chain_index`，禁止据此改写 current identity；
- `sequence_position` 只是 polymer 序列辅助索引，不属于第三套残基编号；
- v1 平铺的 `source_chain_id`、`source_resid`、`residue_name` 和 `atom_name` 仅为兼容镜像，必须与权威 identity 字段一致，禁止赋予独立语义。

## 3.2 下游选择身份

最终 `classification_result.yaml` 必须为 1.3 输出不可重建的权威选择身份：

- `source_structure`：本次分类对应的源结构 path、SHA-256 与格式；
- `component_id`：根据 final component membership 生成，禁止由 `chain_index` 充当或重建；
- `residue_id`：根据 immutable `source_identity` 生成；
- `endpoint_id`：根据 source residue identity 与 exact atom name 生成；
- `relation_id`：根据 relation type 与两个 endpoint IDs 生成，与 endpoint 顺序和 evidence status 无关。

聚合 `SOLVENT_GROUP`、`ION_GROUP` 和 `REPEATED_SMALL_MOLECULE_GROUP` 只改变逻辑分组，不得删除实例级 residue records。每个 component 分别列出：

- `residue_ids`：当前结构中实际存在、可被选择的 observed residues；
- `missing_residue_ids`：来源记录中 expected but unobserved residues，仅用于追溯，不作为坐标选择对象。

这些 ID 对下游是 opaque contract values；1.3 必须读取 1.2 输出，禁止根据字段自行复刻 ID 算法。


# 4. 分类字段

## 4.1 `polymer_class`

允许值：

```text
POLYMER
BRANCHED
NONPOLYMER
WATER
```

## 4.2 `topology_class`

允许值：

```text
STANDARD_RESIDUE
TOPOLOGY_LINKED_NONSTANDARD
INDEPENDENT_NONSTANDARD
SOLVENT_COMPONENT
ION_COMPONENT
```

`TOPOLOGY_LINKED_NONSTANDARD` 表示某个非标准组分已因确认且实际应用了 topology effect 的成键关系而纳入连接拓扑。触发关系可以是 `COVALENT_CONNECTION`、`METAL_COORDINATION`，或其他由项目规则明确允许的 topology-forming relation。

该字段只描述组分的拓扑归属，禁止据此反推化学关系类型；关系类型必须由 relation result 单独记录。

`UNKNOWN`、`UNRESOLVED` 和 `CONFLICT` 是 `resolution_status`，禁止写入分类字段。

## 4.3 合法组合

| polymer_class | topology_class |
|---|---|
| `POLYMER` | `STANDARD_RESIDUE`, `TOPOLOGY_LINKED_NONSTANDARD` |
| `BRANCHED` | `STANDARD_RESIDUE`, `TOPOLOGY_LINKED_NONSTANDARD`, `INDEPENDENT_NONSTANDARD` |
| `NONPOLYMER` | `TOPOLOGY_LINKED_NONSTANDARD`, `INDEPENDENT_NONSTANDARD`, `SOLVENT_COMPONENT`, `ION_COMPONENT` |
| `WATER` | `SOLVENT_COMPONENT` |

# 5. 项目级残基定义

`project_residue_definitions.yaml` 使用列表：

```yaml
schema_version: "1.0"
residue_definitions:
  - residue_name: HEM
    polymer_class: NONPOLYMER
    topology_class: INDEPENDENT_NONSTANDARD
    ccd_id: HEM
```

规则：

- `residue_name`、`polymer_class`、`topology_class` 必填；
- `ccd_id` 可选；未提供时等于精确 `residue_name`；
- 同一个精确 `residue_name` 只允许定义一次；
- v1 定义禁止包含 model、chain、source residue number 或连接原子限制；
- 一条定义适用于 selected model 中所有精确同名实例。
- 项目级残基定义建立所有精确同名实例的 baseline 分类；确认的 topology-forming relation 只允许提升参与该关系的具体实例，禁止反向修改其他同名实例的 baseline。

# 6. 分类来源顺序

## 6.1 `REGISTRY`

```text
项目定义
→ 精确 Skill registry
→ entity/polymer context
```

项目定义与 Skill registry 同时命中时：

- 两个分类标签一致：接受，并记录一致性证据；
- 任一标签不同：记录 `PROJECT_REGISTRY_CLASSIFICATION_CONFLICT`，完成其余检查后统一确认；
- 禁止设置自动优先级覆盖冲突。

## 6.2 `FORCE_FIELD_ANALYSIS`

```text
项目定义
→ 所选力场的精确 RTP residue block
→ 仍未解决时使用精确 Skill registry
→ entity/polymer context
```

力场是否识别某个残基只由 `*.rtp` 中的精确 residue block 名称决定。`residuetypes.dat` 和 RTP 文件名禁止参与识别。

项目定义与 RTP 分类同时命中时：

- 两个标签一致：接受；
- 标签不同：记录 `PROJECT_FORCE_FIELD_CLASSIFICATION_CONFLICT`；
- 项目未定义但 RTP 命中：采用 RTP 分类，禁止并行咨询 Skill registry；
- 只有项目和 RTP 都未解决时才允许使用 Skill registry fallback。

# 7. RTP 与端基

## 7.1 重复 RTP 定义

- 非水残基的同一精确 RTP 名称定义多次：生成 `DUPLICATE_FORCE_FIELD_RESIDUE_TEMPLATE`，统一人工确认；
- 水允许同一力场目录存在多个水模型 RTP；禁止在 1.2 根据这些重复项自动选择水模型；
- 普通水禁止使用 RTP 水原子名核验原始水；
- 禁止以 RTP 文件名推测残基类别。

## 7.2 普通与端基模板

普通内部标准残基使用精确同名 RTP block。

N/C 端和 5′/3′端标准残基必须先确定端基角色，再使用显式 terminal-template mapping 选择端基 RTP block：

```text
terminal role
+ source residue name
→ explicit RTP terminal residue name
```

禁止通过删除或添加 `N`、`C`、`5`、`3` 等字符猜测端基名称。

- terminal mapping 不唯一：生成 `TERMINAL_RTP_TEMPLATE_AMBIGUOUS`；
- 缺少可用 mapping 或完整端基 RTP block：重原子检查写为 `REFERENCE_TEMPLATE_UNAVAILABLE`；
- 禁止回退到普通内部模板并宣称端基通过。

1.2 禁止应用 `.n.tdb`、`.c.tdb` 或其他 terminal patch 合成模板。

# 8. 重原子检查

## 8.1 参考矩阵

| 模式 | 分类 | 重原子参考 |
|---|---|---|
| `REGISTRY` | 标准残基 | CCD |
| `REGISTRY` | 相连/独立非标准残基 | CCD |
| `FORCE_FIELD_ANALYSIS` | 标准残基 | 已选 RTP block，包括显式端基 block |
| `FORCE_FIELD_ANALYSIS` | 相连/独立非标准残基 | CCD |
| 任一模式 | 普通水、普通离子 | `NOT_APPLICABLE` |

## 8.2 输出状态

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

规则：

- 只记录缺少和多出的原子名称；禁止追加主链、侧链、端基或金属中心原子分类；
- CCD alternate atom name 只能形成待处理映射证据，禁止静默改名。

## 8.3 altLoc

只要残基存在多个 altLoc：

```text
conformation status: MULTIPLE_CONFORMATIONS
heavy atom check: NOT_PERFORMED
reason: MULTIPLE_CONFORMATIONS_PRESENT
```

禁止将多个构象的原子并集作为一个伪完整残基进行比较。

# 9. CCD 规则

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

- 禁止扫描用户未指定的文件系统目录；
- 本地目录默认只查找精确 `<ccd_id>.cif`；
- 文件名匹配后仍必须核验文件内部 component ID；
- 有效外部文件必须复制到项目 `reference_data/ccd/`，并核验复制前后 SHA-256；
- 项目 snapshot 是本次结果的权威 CCD 文件；
- 单个 component 获取失败只记录并继续；
- CCD 机制整体不可用或 snapshot 无法一致写入时属于技术失败；
- 多个相同 SHA-256 的有效候选视为同一参考；
- 多个不同内容的有效本地候选必须进入统一确认。

# 10. 缺失残基

## 10.1 PDB/mmCIF

使用可用的预期序列、实际坐标以及 PDB `REMARK 465` 或 mmCIF unobserved-residue 记录建立证据。

禁止仅凭作者编号跳号认定残基缺失。

1.2 只记录缺失残基身份；禁止判断缺失区域属于内部、N 端、C 端或其他区域。

正式缺失残基记录必须具有作者原始编号：

```yaml
source_resid:
  number: "145"
  insertion_code: null
```

插入码必须按源文件原样保留。

作者编号无法确定时：

- 禁止生成虚构编号；
- 禁止使用 sequence position 替代正式 `source_resid`；
- 继续完成所有其他可执行检查；
- 统一返回 `MISSING_RESIDUE_SOURCE_RESID_UNAVAILABLE`。

链归属无法确定时统一返回 `MISSING_RESIDUE_CHAIN_UNRESOLVED`。

无法建立 author `source_resid` 或 `chain_index` 的记录必须写为 `MAPPING_UNRESOLVED`，禁止伪装成已解析的 `MISSING_EXPECTED` residue record。

## 10.2 AF3 CIF

AF3 CIF 只有在提供 AF3 输入 JSON、FASTA 或等价序列参考时才执行缺失残基检查。

缺少输入序列时记录：

```text
NOT_PERFORMED
AF3_INPUT_SEQUENCE_NOT_PROVIDED
```

该状态禁止解释为已经确认没有缺失残基。

AlphaFold Server `job_request.json`：

- 顶层 list 必须恰好包含一个 `dialect: alphafoldserver` job；
- entity 无显式 ID 时按 entity 顺序和 `count` 生成 `A..Z, AA..` chain IDs；
- ligand 和 ion 占用 chain ID，但禁止生成 polymer sequence；
- 多 job、非法 count 或 ID 数量不一致必须拒绝解析。

# 11. `chain_groups` 与 `chain_index`

`chain_index` 是 1.2 建立的内部组分归属编号，禁止解释为源文件 chain ID。

基础规则：

- 每条 polymer/branched chain 一个 `chain_index`，按 selected model 中首次出现顺序分配；
- 每种精确名称的普通水和普通离子汇总为一个组；
- 同种、同分类、无特殊关系或异常的重复独立小分子可以汇总；
- 普通汇总组仍必须为每个 `OBSERVED` 实例保留 `residue_record`；汇总只改变 component/chain group 的组织方式，不得删除实例级身份记录；
- 存在 altLoc、分类冲突、模板异常、显式/候选关系或项目特殊处理的实例必须从汇总组中提出并单独记录；
- 独立小分子即使与 polymer chain 使用相同作者 chain ID，也必须使用独立 `chain_index` 并记录 source association。

结构 entity/polymer 事实对 baseline grouping 具有权威性：

- 结构明确属于 polymer/branched chain 的残基，即使分类为 `CONFLICT` 或 `UNRESOLVED`，仍保留在原结构链；
- 结构明确为 nonpolymer entity 的组分，禁止仅凭项目分类标签提升为 polymer chain；
- grouping 完成后必须恢复原始分类值、冲突状态和证据，禁止借 grouping 静默解决分类冲突。

最终整合：

- 非标准组分与一条 polymer chain 存在确认的 topology-forming relation：编入该 polymer chain 的 `chain_index`；
- 与多条 polymer chain 相连：建立 `MULTICHAIN_LINKED_COMPONENT`，记录 `linked_polymer_chain_indices`；
- 只与其他非标准组分形成 topology-forming connected component：建立 `LINKED_NONSTANDARD_GROUP`；
- 标准残基参与连接或配位时默认保持 `STANDARD_RESIDUE`。

# 12. 可能共价连接

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
- 必须枚举全部唯一实例组合，禁止自动选择最近的一对；
- 同一原子禁止与自身配对；
- 显式 PDB/mmCIF 连接和几何距离必须分别记录；
- 只有显式确认或用户确认后的几何候选才允许影响 topology；
- 输入定义本身禁止创建结构连接。

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

# 13. 金属配位

`possible_coordination.yaml` 必须明确金属端、供体端、元素、距离范围和 topology effect：

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
- 元素字段必填，并在几何判断前核验；
- 同一金属具有多个不同供体是合法事实，禁止自动判定为冲突；
- 关系类型必须保持 `METAL_COORDINATION`；
- `promote_nonstandard_to_linked: true` 只在显式关系确认或用户确认几何候选后生效；
- HEM–CYS/HIE 等 topology-forming coordination 可以将 HEM 提升为 `TOPOLOGY_LINKED_NONSTANDARD`；
- Mg、Zn 等是否改变 topology 必须由项目定义明确，禁止仅凭距离自动判断；
- `promote_nonstandard_to_linked: false` 只记录配位，禁止改变 topology 或 chain group。

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

# 14. 完整扫描与确认

除 model selection barrier 外，正式 1.2 解析禁止在遇到第一项科学问题时停止。

执行顺序：

```text
完成全部可执行残基分类
→ 完成缺失残基和重原子检查
→ 完成全部可能共价连接定义
→ 完成全部金属配位定义
→ 汇总仍需确认的问题
→ 生成 PENDING_USER_CONFIRMATION 或 COMPLETE
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

以下事实只记录，禁止自动形成确认项：

- 明确缺失重原子；
- 单个 CCD 获取失败；
- partner/atom 不存在；
- 无显式关系的元素异常；
- 几何不支持；
- 多构象事实。

同一 `issue_type + subject + resolution_status` 的跨阶段重复报告必须合并，并保留全部不同 evidence。

# 15. 禁止使用的力场推断来源

1.2 禁止读取或应用：

```text
residuetypes.dat
*.n.tdb
*.c.tdb
specbond.dat
```

`specbond.dat` 只表示力场可能支持某种特殊连接，禁止据此证明当前结构存在连接。

已确认特殊键的力场支持能力由后续 topology preparation 处理。
