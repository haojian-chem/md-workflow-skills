# 1.2 组分与残基分类规则

本文件拥有结构准备 1.2 的详细科学判断规则。执行主线见 `../SKILL.md`；正式结果数据结构与字段语义见 `result_recording_rules.md`；机器字段约束见 `../schemas/`。

## 1. Model、component 与 residue 身份

1.2 按 model 独立处理。一份正式 `classification_result.yaml` 只描述一个 model；model 信息只在文件级记录一次，不复制到每个 component 或 residue。

正式结果的对象层级固定为：

```text
model
└── component_id + chain_index
    └── residue_id
```

规则：

- `component_id` 在当前 model 的正式结果中唯一，是稳定、不透明的 component identity；
- `chain_index` 在当前 model 中唯一，位于 component 一级，是该 component 的逻辑 chain/group 编号，不属于稳定 identity；
- `residue_id` 在所属 `component_id` 内唯一；
- 下游定位 residue 使用 `component_id + residue_id`；
- `component_id` / `residue_id` 不从 chain、resid、残基名或空间关系重新推导；
- 下游需要映射 chain 时直接消费 1.2 已记录的 component 一级 `chain_index`；
- 当前 active 1.2 不使用 source-derived ID 公式，也不需要 `selection_identity.py`。

每个 residue 同时记录：

```text
source_chain_id
current_chain_id
source_resid
current_resid
source_residue_name
current_residue_name
```

其中：

- `source_*` 表示当前 1.2 输入结构中的原始定位或名称；
- `current_*` 表示生成本次 1.2 正式结果时当前结构中的定位或名称；
- 1.2 本身不修改结构，因此普通已存在 residue 的 source / current 值通常相同；
- 已确认缺失 residue 没有当前坐标实例，`current_resid` 与 `current_residue_name` 为 `null`；`current_chain_id` 按能够可靠确定的实际情况记录；
- `source_resid` / `current_resid` 保存当前结构格式中用于定位该 residue 的实际 resid 表达，不另把 insertion code 当作独立科学属性。

每个 component 内 `residues` 的数组顺序是 1.2 对该 component 建立的正式 residue 顺序。缺失 residue 仍位于其应有顺序位置。

## 2. 分类语义与依据

每个 residue 分别形成两类分类结果。

`polymer_class`：

```text
POLYMER
BRANCHED
NONPOLYMER
WATER
```

`topology_class`：

```text
STANDARD_RESIDUE
TOPOLOGY_LINKED_NONSTANDARD
INDEPENDENT_NONSTANDARD
SOLVENT_COMPONENT
ION_COMPONENT
```

二者语义不同：

- `polymer_class` 描述 residue / component 的聚合物或化学组分类别；
- `topology_class` 描述该 residue 在后续 topology preparation 中的处理归属。

Skill 内置精确名称登记表：

```text
references/standard_residue_registry.yaml
references/topology_linked_nonstandard_residue_registry.yaml
references/independent_nonstandard_residue_registry.yaml
```

项目提供的结构化定义文件可以按以下 schema 理解：

```text
schemas/project_residue_definitions.schema.yaml
schemas/possible_connections.schema.yaml
schemas/possible_coordination.schema.yaml
```

这些 schema 只约束输入字段，不替项目文件本身提供科学事实。

### `REGISTRY`

初始分类依据按以下顺序使用：

```text
项目残基定义
→ 精确匹配的 Skill 内置残基登记表
→ 当前结构中的实体、聚合物或化学组分语义
```

### `FORCE_FIELD_ANALYSIS`

初始分类依据按以下顺序使用：

```text
项目残基定义
→ 当前指定目标力场中的精确残基定义
→ 精确匹配的 Skill 内置残基登记表
→ 当前结构中的实体、聚合物或化学组分语义
```

当前 residue name 与参考定义必须精确对应；不得用大小写归一化、模糊匹配、正则近似或字符串增删推断为同一 residue。

不同有效依据给出互相冲突的分类，且冲突会改变正式 `polymer_class`、最终 `topology_class` 或 component membership 时，不静默选择一个来源覆盖另一个；根据当前证据由 Agent 判断，仍不能唯一闭合时向用户确认。

CCD 中存在某个组分定义不等于该 residue 自动属于 `STANDARD_RESIDUE`。

这里得到的 `topology_class` 在共价连接和金属配位检查完成前可以是 provisional。正式 `classification_result.yaml` 只保存关系检查及 topology-effect 更新后的最终 `topology_class`。

## 3. RTP 与 CCD reference

### 3.1 RTP

当分类或重原子检查需要目标力场时，实际依据必须是当前目标力场中真正使用的 `*.rtp` 文件。

对 GROMACS 力场：

- 标准 residue 识别只依据实际 `*.rtp` 中相应 residue block；
- 不根据力场目录名、`residuetypes.dat` 或文件名提示推断 residue 一定存在定义；
- 端基角色如果会改变适用定义，先依据当前结构 / 项目语义确定角色，再使用实际存在的明确 residue definition；
- 1.2 不通过 `.n.tdb`、`.c.tdb` 等 patch 构造虚构的比较模板。

每个本次实际使用的 RTP 文件在 `classification_result.yaml` 文件级 `references` 中赋值为 `RTP_1`、`RTP_2`……，变量值直接写实际文件路径。

### 3.2 CCD

需要 CCD 作为 reference 时，使用当前任务实际确定的 CCD component file。可用来源包括：

- `references/ccd_library/` 中现有已批准本地参考；
- 项目已有 CCD component file；
- 用户明确提供的 CCD component file。

项目或用户提供的 CCD 文件不需要复制或导入到 Skill 内置 CCD library 后才能使用。

CCD reference 的目录在 `classification_result.yaml` 文件级 `references` 中赋值为 `CCD_PATH_1`、`CCD_PATH_2`……。具体检查项引用实际文件时写成：

```text
{CCD_PATH_1}/HEM.cif
```

同一 CCD component ID 存在多个内容不同的候选定义，且差异会改变本次分类或重原子判断时，必须明确当前实际采用哪个文件；不能静默混用。

CCD component ID 与结构 residue name 不同时，只有存在明确项目定义、CCD 自身明确名称对应信息或人工确认时才建立对应；不得根据名称相似度自动映射。

## 4. Residue 三级检查与短路规则

每个 residue 的三个结构检查固定依次为：

```text
1. 残基缺失检查
↓ PASS
2. 多构象检查
↓ PASS
3. 重原子组成与命名检查
```

短路规则是正式结果语义的一部分：

- 残基缺失检查为 `ISSUE` → 多构象检查和重原子检查均为 `SKIPPED`；
- 残基缺失检查为 `PASS`、多构象检查为 `ISSUE` → 重原子检查为 `SKIPPED`；
- 只有前两项均为 `PASS` 时才执行重原子检查；
- 普通 solvent / ion 等当前科学规则明确无需重原子比较的对象，可以在前两项 `PASS` 后把重原子检查记为 `NOT_APPLICABLE`。

正式 COMPLETE 结果中，适用但缺少可靠 reference 的重原子检查不能伪装成 `PASS` 或 `NOT_APPLICABLE`；应先解决 reference 定位 / 选择问题。

### 4.1 残基缺失检查

只在有可追溯依据时确认 residue 应存在但当前 model 中没有坐标，例如：

- PDB/mmCIF 中明确的聚合物序列或缺失 residue 注释；
- 与当前结构 chain 能可靠对应的序列文件；
- 当前项目已经确认的序列—结构对应关系。

不得仅依据 resid 数值不连续、`TER` / chain break、空间空缺或视觉判断推断 residue 缺失。

缺失 residue 必须能被放入所属 component 的正式 residue 顺序，并具有可确定的 `source_chain_id`、`source_resid` 和 `source_residue_name`。整个 residue 缺失时，不再重复记录成“缺失全部重原子”。

### 4.2 多构象检查

仅检查当前 residue 是否存在多构象问题。普通 PDB 主要依据非空 `altLoc`；其它格式按可可靠映射的等价表示判断。

1.2 在这一项只回答：

```text
当前 residue 是否存在多构象问题？
```

1.2 不负责选择保留哪个构象、比较候选构象优先级、以 occupancy 或局部环境完成构象取舍、组装候选结构或删除其它构象；这些处理由 1.4 拥有。

因此一旦本项发现多构象问题，直接记录 `ISSUE`，本 residue 的重原子检查为 `SKIPPED`。

### 4.3 重原子组成与命名检查

本项只在前两项均 `PASS` 时执行。

Reference 选择：

- `FORCE_FIELD_ANALYSIS` 下的 `STANDARD_RESIDUE`：当前目标力场中实际适用的 RTP residue definition；
- `REGISTRY` 下的 `STANDARD_RESIDUE`：当前实际确认的 CCD component definition；
- `TOPOLOGY_LINKED_NONSTANDARD` / `INDEPENDENT_NONSTANDARD`：当前实际确认的 CCD component definition；
- 普通 `SOLVENT_COMPONENT` / `ION_COMPONENT`：默认 `NOT_APPLICABLE`，除非当前项目明确要求基于特定残基定义检查。

检查：

1. reference 中存在、当前 residue 中没有的重原子；
2. 当前 residue 中存在、reference 中没有的额外重原子；
3. 同一 residue 中重复出现的原子名称；
4. 当前原子名称与 reference 名称不一致；
5. 当前结构与 reference 都能可靠提供元素信息时的元素不一致。

原子名称对应必须有明确依据；元素信息缺失或不可靠时，不根据 atom name 首字母强行推断元素。

## 5. Evidence 记录语义

正式结果中的 `evidence` 表示该项最终判断采用的直接依据，不保存完整推理过程。

允许：

```text
RTP_n
{CCD_PATH_n}/XXX.cif
智能体判断
人工决策
```

- Agent 直接依据目标力场 RTP 定义完成判断 → 相应 `RTP_n`；
- Agent 直接依据 CCD component file 完成判断 → `{CCD_PATH_n}/XXX.cif`；
- Agent 综合当前结构、结构注释、项目语义等信息完成判断 → `智能体判断`；
- 最终结论由用户确认 → `人工决策`。

`RTP_n` / `CCD_PATH_n` 必须能在同一 `classification_result.yaml` 文件级 `references` 中解析。1.2 不生成 `reference_manifest.yaml`，也不使用 `ref_001`、`reference_entry` 或对所有 reference 文件强制计算 SHA-256 的机制。

## 6. 共价连接检查

共价连接判断可以使用：

- PDB `LINK`、mmCIF `_struct_conn` 等显式结构关系；
- 项目共价连接定义；
- 端点 residue / atom 身份；
- 局部键长和化学环境。

只有几何接近时不能自动等同于化学共价连接。显式结构关系只有在端点能够可靠定位且不存在明显化学冲突时，才作为确认依据。

工作判断可以形成：

```text
CONFIRMED
CANDIDATE
CONFLICT
REJECTED
```

正式 COMPLETE 结果必须明确记录本项检查结果：

```text
confirmed_relations.covalent_connections
rejected_candidates.covalent_connections
```

两者均为数组。没有确认的共价连接或没有需保留的拒绝候选时，数组为空；空数组表示本项已执行且无相应结果，不表示跳过检查。

写入 `confirmed_relations.covalent_connections` 的关系必须已经闭合。已经明确拒绝且有审计价值的候选写入 `rejected_candidates.covalent_connections`。会改变 component membership、最终 `topology_class` 或 `topology_effect_applied` 的候选 / 冲突若尚未闭合，则不能形成正式 COMPLETE 结果。

需要用户确认时，人工决定记录到当前 model 目录的 `relation_decisions.yaml`。

## 7. 金属配位检查

金属配位独立于共价连接判断。

确认存在配位关系至少要求：

- 金属端点能够唯一定位；
- donor atom 能够唯一定位；
- 当前结构证据与化学身份足以支持该配位判断。

距离接近本身只作为证据，不自动等同于已确认配位。

正式 COMPLETE 结果必须明确记录本项检查结果：

```text
confirmed_relations.metal_coordination
rejected_candidates.metal_coordination
```

没有确认的配位关系或没有需保留的拒绝候选时，对应数组为空。

确认“存在配位关系”不自动产生 topology effect。只有当前项目定义明确要求，或用户明确确认该关系应进入 topology connection 时，才设置 `topology_effect_applied: true`。

## 8. 基于关系检查结果更新最终 `topology_class`

共价连接检查和金属配位检查完成后，使用全部已确认关系形成 residue 的最终 `topology_class`。

只有 `confirmed_relations` 中 `topology_effect_applied: true` 的关系会触发 topology-class 更新：

- `STANDARD_RESIDUE` 保持 `STANDARD_RESIDUE`；
- provisional 为 `INDEPENDENT_NONSTANDARD`、`SOLVENT_COMPONENT` 或 `ION_COMPONENT` 的 residue，如果参与已确认且产生 topology effect 的关系，最终改为 `TOPOLOGY_LINKED_NONSTANDARD`；
- provisional 已经是 `TOPOLOGY_LINKED_NONSTANDARD` 的 residue 保持该类别；
- `topology_effect_applied: false` 的确认关系不改变 `topology_class`；
- `CANDIDATE`、`CONFLICT`、`REJECTED` 不改变正式 `topology_class`。

如果最终 `topology_class` 因关系检查改变，则该最终分类的 `evidence` 记录形成这一关系结论的直接决策来源：Agent 闭合为 `智能体判断`，用户闭合为 `人工决策`。

正式结果不同时保存 provisional 和 final 两套 `topology_class`；`components[].residues[].topology_class` 只保存更新后的最终值。

## 9. Topology effect 与最终 component membership

最终 `topology_class` 更新完成后，再根据全部已确认且 `topology_effect_applied: true` 的关系形成最终 topology grouping。

基本规则：

- 非标准 residue 与一个 standard polymer component 建立 topology connection 时，归入该 component；
- 只由 topology-linked nonstandard residues 构成的连接单元形成一个独立 component；
- 一个非标准单元同时连接多个 standard polymer chain 时，形成共同的 multichain component；
- polymer–polymer 直接关系本身不要求把两个 polymer component 无条件合并；
- 候选、冲突、拒绝或未产生 topology effect 的关系不改变最终 component membership。

最终 component membership 基于全部关系检查结果形成后，再物化 `component_id`、component 一级 `chain_index` 与 component 内 `residue_id`。

## 10. 正式结果闭合条件

结构中存在缺失 residue、多构象问题或重原子问题本身不阻止 1.2 完成；这些是本 Skill 需要正式记录的检查结果。

以下情况会阻止形成正式 `result_status: COMPLETE`：

- 应存在的 residue 身份无法唯一确定；
- 应执行的重原子检查没有可靠 reference；
- 分类冲突仍会改变最终 `polymer_class` / `topology_class`；
- 共价连接或金属配位的冲突仍会改变最终 `topology_class`、component membership 或 `topology_effect_applied`；
- 两类关系检查没有形成完整正式结果；
- 已确认且产生 topology effect 的关系尚未反映到相关 residue 最终 `topology_class` 或 component membership；
- result 中的 evidence 无法解析到实际采用的 reference；
- 规定的三级 residue 检查没有按短路顺序完整记录。
