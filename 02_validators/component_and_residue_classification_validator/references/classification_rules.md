# 组分与残基分类规则

本文件是结构准备 1.2 的科学语义唯一权威来源。执行顺序见 `../SKILL.md`，机器字段见 `../schemas/`，CLI 见 `../scripts/README.md`。

# 1. 身份与名称

残基名、原子名、chain、residue number、insertion code 和 altLoc 必须按源结构精确保留；禁止大小写归一化、正则/模糊匹配或依据近似名称选择 RTP/CCD。

每个观察残基和关系端点同时保存 immutable `source_identity` 与本次结构的 `current_identity`。1.2 不修改结构，因此观察实例两者值相同；缺失残基没有 current identity。`chain_index` 是可随 topology effect 改变的逻辑分组编号，不属于 identity。

最终 `component_id`、`residue_id`、`endpoint_id` 和 `relation_id` 是下游 opaque contract。1.3 只能读取物化值，禁止自行重建。

普通汇总组仍必须为每个 `OBSERVED` 实例保留 `residue_record`；汇总计数不能代替实例身份，不得删除实例级身份记录。

# 2. 分类

`polymer_class`：`POLYMER | BRANCHED | NONPOLYMER | WATER`。

`topology_class` 该字段只描述组分的拓扑归属，不描述证据充分性，也禁止据此反推化学关系类型：

```text
STANDARD_RESIDUE
TOPOLOGY_LINKED_NONSTANDARD
INDEPENDENT_NONSTANDARD
SOLVENT_COMPONENT
ION_COMPONENT
```

`UNKNOWN`、`CONFLICT`、`UNRESOLVED` 只属于 resolution status。

分类来源顺序：

```text
REGISTRY:
项目定义 → 精确 Skill registry → entity context

FORCE_FIELD_ANALYSIS:
项目定义 → 精确 RTP block → 精确 Skill registry → entity context
```

项目定义与同层有效来源标签不一致时形成确认事项，禁止静默设置优先级。项目定义可省略；缺失时记录 `NOT_PROVIDED`，不阻断。

标准 registry 只收录已批准的氨基酸/质子化名称、DNA/RNA、水和 `NA K CL MG CA ZN`。`HSD/HSE/HSP` 分别映射到 `HID/HIE/HIP`；结构原名仍保留。MSE/SEC/PYL 由 linked registry 建立明确 baseline。

# 3. RTP 与端基

力场识别只依据 `*.rtp` 中精确 residue block。重复非水 block、显式 terminal mapping 冲突必须确认；禁止用文件名、`residuetypes.dat` 或字符串增删规则猜测模板。

端基先确定角色，再查显式 mapping；该角色没有 mapping 时使用精确同名 RTP block。1.2 不应用 `.n.tdb`、`.c.tdb` 或其他 patch 合成模板。

# 4. CCD-compatible libraries

内置库固定为：

```text
references/ccd_library/
```

附加库必须显式列出，且使用同一扁平结构：`index.yaml`、`README.md`、`<component_id>.cif`。运行时禁止联网、cache、snapshot 和无界目录扫描。

解析顺序为内置库后附加库。同一 ID/同一 SHA 可重复，优先首个；同一 ID/不同 SHA 形成 `CCD_COMPONENT_DEFINITION_CONFLICT`。所有文件必须匹配 index SHA 和 CIF component ID。

存在 CCD 条目不等于标准残基；分类仍由项目定义、RTP、registry 和 entity context 决定。

# 5. 重原子与缺失残基

重原子检查先保留 exact atom-name 差集，再单独记录 alternate-name mapping candidate。未经确认不得改写 raw comparison；确认映射后生成 effective comparison，仍保留 exact comparison。

多个 altLoc 的残基不合并原子集合；重原子比较记为 `NOT_PERFORMED`。普通水和普通离子为 `NOT_APPLICABLE`。参考缺失记为 `REFERENCE_TEMPLATE_UNAVAILABLE`，不伪造通过。

缺失残基只在来源可追溯时物化；编号或 chain mapping 无法确定时形成确认事项。一次完整遍历即使发现问题，阶段仍可为 `COMPLETED`；`BLOCKED` 只表示无法可靠完成遍历。

# 6. 共价连接与金属配位

`possible_connections.yaml` 和 `possible_coordination.yaml` 都可省略。定义文件只限定要检查的精确 residue/atom 和距离范围；几何支持不能自动等同于化学事实。

关系状态：

```text
CONFIRMED
CANDIDATE
CONFLICT
NOT_EVALUATED
REJECTED
```

确认状态：

```text
NOT_REQUIRED
PENDING_CONFIRMATION
CONFIRMED_BY_USER
REJECTED_BY_USER
```

显式结构关系且与定义/几何一致时为 `CONFIRMED + NOT_REQUIRED`；只有几何支持时为 candidate；定义冲突、多构象或元素问题按证据记录，不被其他异常覆盖。

`relation_id` 只由 `selection_identity.py` 生成：共价端点无方向排序；配位固定 `metal → donor` 角色。`request_index` 只用于当前确认界面，持久决定必须绑定 relation ID。

# 7. 人工关系决定

人工关系决定独立保存在 `relation_decisions.yaml`，并绑定结构 SHA 与 selected model。只允许 `CONFIRMED` 或 `REJECTED`；未回答请求不写入该文件。

自动重跑不得覆盖已有决定。相同决定幂等；相反决定必须显式替换。决定目标在当前检查中不存在时记录 `RELATION_DECISION_TARGET_NOT_FOUND`，不得静默删除。

# 8. Topology effect 与分组

确认共价连接总是 topology-forming。确认金属配位只有在定义明确 `promote_nonstandard_to_linked: true` 时产生 topology effect。候选、冲突、拒绝或无法评估关系不改变分类与分组。

应用后：

- 标准残基保持 `STANDARD_RESIDUE`；
- 独立非标准、水或离子实例提升为 `TOPOLOGY_LINKED_NONSTANDARD`，水改为 `NONPOLYMER`；
- 非标准组分连接一个 polymer 时并入该 polymer group；
- 只连接非标准组分时形成 `LINKED_NONSTANDARD_GROUP`；
- 同时连接多个 polymer 时形成 `MULTICHAIN_LINKED_COMPONENT`；
- polymer–polymer 直接关系不合并原 polymer groups。

当前 groups 必须从保存的 baseline 状态和全部已确认 topology relations 重新计算，以保证重跑和决定替换幂等。

# 9. 当前状态与最终结果

`classification_observations.yaml` 保存当前状态，并记录五个检查阶段及实际独立 relation outputs。`completed_checks` 不暗示每个阶段都有单独结果文件。

关系 result 保存完整检查证据；observations 只保留当前有效关系状态。最终构建器不得再次推断关系、改变 topology effect 或重新计算 relation ID，只负责物化下游选择 ID、聚合确认事项和生成最终契约。
