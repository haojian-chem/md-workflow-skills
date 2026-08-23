# 1.2 组分与残基分类规则

本文件拥有结构准备 1.2 的详细科学判断规则。执行主线见 `../SKILL.md`；正式结果组织见 `result_recording_rules.md`；机器字段约束见 `../schemas/`。

## 1. 身份、名称与正式顺序

源结构中的残基名、原子名、chain、残基编号、insertion code 和 `altLoc` 必须按实际记录解释。除非当前参考文件本身给出明确对应关系，不通过大小写归一化、模糊匹配、正则近似或字符串增删推断残基或原子身份。

每个已观察残基保留：

- `source_identity`：当前 1.2 输入结构中的源身份；
- `current_identity`：当前 1.2 实际检查对象中的身份。

1.2 不修改结构，因此普通已观察残基的 `source_identity` 与 `current_identity` 应指向同一结构实例。已确认缺失残基没有当前坐标实例，`current_identity` 为 `null`。

`residue_id` 与 `component_id` 的正式含义按仓库级 `canonical_terminology.md`。`source_resid`、`current_resid`、PDB `resid`、`sequence_position` 与 `residue_id` 是不同字段，正式记录不得互相替代。

`residue_records[]` 的数组顺序是 1.2 建立的正式残基顺序。已观察残基和 `MISSING_EXPECTED` 残基都放在其实际序列/结构语义位置。`chain_groups[].residue_ids` 与 `missing_residue_ids` 只表达成员关系，不承担排序语义。

稳定身份的机械物化可以使用 `../scripts/selection_identity.py`。该辅助工具只根据已经确定的身份和成员关系生成 `residue_id`、`component_id`、`endpoint_id` 与 `relation_id`，不拥有任何分类或关系判断。

## 2. 分类语义与内置 registry

`polymer_class` 固定为：

```text
POLYMER
BRANCHED
NONPOLYMER
WATER
```

`topology_class` 固定为：

```text
STANDARD_RESIDUE
TOPOLOGY_LINKED_NONSTANDARD
INDEPENDENT_NONSTANDARD
SOLVENT_COMPONENT
ION_COMPONENT
```

Skill 内置的精确名称分类依据分别保存在：

```text
references/standard_residue_registry.yaml
references/topology_linked_nonstandard_residue_registry.yaml
references/independent_nonstandard_residue_registry.yaml
```

只有当前分类确实需要相应 registry 时才读取对应文件；不得把 registry 中没有列出的名称自动判为某一类别。

如果项目提供结构化残基定义、共价连接定义或金属配位定义，可分别按以下 schema 理解其字段：

```text
schemas/project_residue_definitions.schema.yaml
schemas/possible_connections.schema.yaml
schemas/possible_coordination.schema.yaml
```

这些 schema 只约束项目定义文件的字段，不替项目文件本身提供科学事实。

`topology_class` 描述当前组分在后续拓扑处理中的归属，不表示证据充分程度。检查过程中可以使用以下 `resolution_status` 区分判断状态：

```text
RESOLVED
CONFLICT
UNRESOLVED
```

但是正式 v2 `classification_result.yaml` 只接受 `resolution_status: RESOLVED`。如果 `CONFLICT` 或 `UNRESOLVED` 会影响最终分类，必须在正式 COMPLETE 结果生成前闭合。

### `REGISTRY`

分类依据按以下顺序使用：

```text
项目残基定义
→ 精确匹配的 Skill 内置残基 registry
→ 当前结构中的实体、聚合物或化学组分语义
```

### `FORCE_FIELD_ANALYSIS`

分类依据按以下顺序使用：

```text
项目残基定义
→ 当前指定目标力场中的精确残基定义
→ 精确匹配的 Skill 内置残基 registry
→ 当前结构中的实体、聚合物或化学组分语义
```

这里的“精确”表示当前 `residue_name` 能直接对应到实际参考条目；不得仅因为名称相近就视为同一残基。

不同有效依据给出互相冲突的分类，且冲突会改变正式 `topology_class` 时，记录冲突并向用户确认；不得静默选择一个来源覆盖另一个。

CCD 中存在某个组分定义，只说明存在该化学组分参考，不自动把对应残基归为 `STANDARD_RESIDUE`。

内置 registry 中的名称对应只用于其明确拥有的分类语义。结构中的原始 `residue_name` 仍按源身份保存，不因 registry 对应关系而改写输入结构。

## 3. 目标力场残基定义

当分类模式或重原子检查需要目标力场时，实际判断依据必须指向当前指定力场中真正使用的残基定义文件和具体条目。

对 GROMACS 力场，标准残基识别只依据实际 `*.rtp` 中精确同名的 residue block。不得根据力场目录名、`residuetypes.dat`、文件名提示或字符串增删规则推断某残基一定存在定义。

端基角色如果会改变应使用的残基定义，先依据当前结构或项目语义确定角色，再使用目标力场实际提供的明确条目或 mapping。1.2 不通过应用 `.n.tdb`、`.c.tdb` 等 patch 来生成一个虚构的比较模板。

## 4. CCD 参考

非标准残基需要 CCD 作为比较依据时，使用当前任务实际选定的 CCD 组分定义文件。

可用来源包括：

- `references/ccd_library/` 中现有的已批准本地参考；
- 项目中已有的 CCD 组分定义文件；
- 用户明确提供的 CCD 组分定义文件。

项目或用户提供的 CCD 文件**不要求**转换、复制或导入为 `references/ccd_library/` 的目录结构后才能使用。只要当前 Agent 能够从该文件可靠确定 CCD component ID、重原子名称及当前判断需要的其它字段，就可以直接作为本次参考，并在 `reference_manifest.yaml` 中记录实际文件路径和 SHA-256。

同一 CCD component ID 存在多个内容不同的候选定义，且差异会改变本次分类或重原子判断时，记录参考文件冲突，并向用户确认本次实际使用哪个文件。

CCD component ID 与结构 `residue_name` 的对应必须有明确依据。若二者不同，只能在项目定义、CCD 中明确记录的 alternate atom/name 信息或用户确认建立对应后使用；不得依据名称相似度自动映射。

## 5. 缺失残基检查

缺失残基检查先于重原子组成与命名检查。

只在存在可追溯依据时物化 `MISSING_EXPECTED` 残基，例如：

- PDB/mmCIF 中明确的聚合物序列或 missing-residue annotation；
- 与当前结构 chain 能可靠对应的序列文件；
- 当前项目已经确认的序列—结构 mapping。

不得仅依据以下现象物化缺失残基：

- 残基编号不连续；
- `TER` 或 chain break；
- 两段坐标之间存在空间空缺；
- 视觉判断“这里应该还有残基”。

每个已确认缺失残基必须能够定位到当前正式残基顺序；若残基身份或 chain/sequence mapping 不能唯一确定，记录为未解决事项，不自行猜测。

整个残基缺失时，不再为该位置记录“缺失全部重原子”。其 `heavy_atom_check.execution_status` 使用 `NOT_APPLICABLE`，并记录原因 `RESIDUE_MISSING`。

## 6. 多构象检查

多构象检查与重原子组成与命名检查是两个独立检查项目。

对每个已观察残基检查当前 model 中实际存在的 alternate conformation 表示。普通 PDB 以非空 `altLoc` 为主要依据；其它格式按能够可靠映射的等价语义处理。

结果至少区分：

```text
SINGLE_CONFORMATION
MULTIPLE_CONFORMATIONS
```

存在多构象时记录实际 `altLoc` ID，并对具有非空 `altLoc` 的原子名称记录其候选状态和可读取 occupancy。

`altLoc` 为空的原子属于共享原子。相同 atom name 在互斥的不同 `altLoc` 中各出现一次，本身不属于重复 atom name。

如果可以可靠拆分候选构象，则某个候选构象用于重原子比较的原子集合为：

```text
共享原子
+
该候选 altLoc 的原子
```

不同候选构象不得合并成一个虚构原子集合。

如果多构象 annotation 本身无法可靠解释为独立候选构象，保留多构象事实，同时把对应重原子比较标记为 `NOT_PERFORMED` 并记录实际原因；不得通过任意选择一个 `altLoc` 来完成 1.2 比较。

## 7. 重原子组成与命名检查

本项只处理当前存在的残基。开始比较前必须明确本次实际参考：

- 标准残基：当前已经指定且用于本次检查的目标力场残基定义；
- 非标准残基：当前实际选定的 CCD 组分定义；
- 用户明确指定其它项目残基定义时，记录该实际文件和具体条目。

普通 `SOLVENT_COMPONENT` 和 `ION_COMPONENT` 默认不执行本项的目标力场/CCD 重原子比较，`execution_status` 使用 `NOT_APPLICABLE`。如果当前项目明确为某个特殊溶剂或离子组分指定了需要检查的残基定义，则按该实际定义执行，不套用这一默认豁免。

其它应检查残基如果没有足够参考，不构造预期重原子集合，`execution_status` 记录 `REFERENCE_UNAVAILABLE`。

### 7.1 重复 atom name

在每个实际比较原子集合内检查 atom name 出现次数。

同一 atom name 在同一原子集合中出现多次，记录 `DUPLICATE_ATOM_NAME`，并记录 atom name、出现次数及适用的 `altLoc` 范围。

不同互斥 `altLoc` 中的同名原子不因为名称相同而互相构成重复。

### 7.2 精确重原子比较

以 atom name 为键，比较：

```text
当前残基或候选构象中的重原子名称及出现次数
↔
实际参考条目定义的重原子名称及出现次数
```

原始精确比较必须分别记录：

- `missing_expected_atom_names`：参考定义存在、当前原子集合中没有的重原子名称；
- `unexpected_observed_atom_names`：当前原子集合中存在、参考定义中没有的重原子名称。

不得先应用原子名称对应关系，再生成所谓“原始比较”。

### 7.3 原子名称对应

如果 CCD alternate atom name、项目已确认 mapping 或其它明确参考能够说明某个当前 atom name 与某个参考 atom name 对应，则单独记录原子名称对应候选，并在 `findings` 中使用 `ATOM_NAME_MISMATCH`。

未经确认的对应关系不改变原始精确比较。对应关系已经有充分依据或经用户确认后，可以另外生成 `effective_comparison`；`exact_comparison` 始终保留。

### 7.4 元素不一致

当当前结构和参考定义都能可靠提供元素信息时，对同名或已确认对应的原子检查元素是否相同。元素不同则记录 `ELEMENT_MISMATCH`，并记录当前结构元素与参考定义元素。

元素字段缺失或不可靠时，不根据 atom name 首字母强行构造元素结论。

## 8. 共价连接

共价连接判断使用当前可获得的实际证据，包括：

- PDB `LINK`、mmCIF `_struct_conn` 等显式结构关系；
- 项目明确提供的共价连接定义；
- 端点的残基和原子身份；
- 局部键长和化学环境。

显式结构关系只有在端点身份能够可靠对应，并且没有明显元素或几何冲突时，才作为已确认结构证据。

仅有几何距离落在合理范围内时，关系状态只能是 `CANDIDATE`，不能自动等同于已建立共价键。

显式关系、项目定义和实际几何彼此冲突时记录 `CONFLICT`。若不同解释会改变 `topology_class` 或后续处理对象，向用户确认。

确认的共价连接属于会产生拓扑作用的关系，因此写入正式结果时设置 `topology_effect_applied: true`。

## 9. 金属配位

金属配位判断独立于共价连接。

确认金属配位需要能够可靠定位：

- 金属端点；
- 配位原子端点；
- 对应残基和原子身份；
- 支持该判断的显式结构信息、项目定义或局部几何证据。

仅有合理的金属—配位原子距离可以形成 `CANDIDATE`，但不能自动产生拓扑作用。

确认的金属配位只有在当前项目定义明确 `promote_nonstandard_to_linked: true`，或用户明确确认该关系应作为后续拓扑连接处理时，才设置 `topology_effect_applied: true`。

## 10. 关系状态与人工确认

关系判断使用以下状态语义：

```text
CONFIRMED
CANDIDATE
CONFLICT
REJECTED
NOT_EVALUATED
```

用户确认只在现有证据不足以唯一决定，且不同选择会改变正式关系、分类或 `topology_effect_applied` 时触发。

实际发生的用户关系决定记录到 `relation_decisions.yaml`，并绑定当前结构 SHA-256、`selected_model_id` 和 `relation_id`。只有用户已经明确回答的关系才写入该文件。

人工决定必须反映到最终 `classification_result.yaml`；不能只留下单独决定文件而让正式结果继续保存旧状态。

## 11. 拓扑作用与最终分组

所有 `topology_effect_applied: true` 的已确认关系应用后，再形成最终 `topology_class`、`chain_groups` 和 `component_id`。

基本规则：

- 标准残基保持 `STANDARD_RESIDUE`；
- 与产生拓扑作用的已确认关系相连的独立非标准实例转为 `TOPOLOGY_LINKED_NONSTANDARD`；
- 非标准实例连接一条标准 polymer chain 时，最终分组应保留该连接归属；
- 非标准实例连接多条标准 polymer chains 时，使用能够表达多链连接的独立组分分组；
- 只由非标准残基构成的已连接单元形成独立的 linked-nonstandard group；
- polymer–polymer 直接关系本身不要求把原 polymer chains 合并成一个 `chain_group`。

候选、冲突、拒绝或未评估关系不得改变最终分组。

## 12. 检查完成与发现问题

“检查已经完成”和“未发现问题”不是同一个状态。

一次检查已经按当前对象和参考完整执行，即使发现缺失残基、多构象、重原子差异或候选关系，也可以记录为已完成检查。

只有当前需要形成的判断无法可靠完成，并且该判断会改变正式分类、稳定身份、关系或 `topology_effect_applied` 时，当前 1.2 才保持未完成。

参考文件不可用，但该项不阻断正式分类或稳定身份时，按实际情况记录 `REFERENCE_UNAVAILABLE` 和未解决信息；不得把未检查伪装成没有问题。
