# Workflow 2 Stage 2.6 Topology validation freeze

Status: CURRENT ARCHITECTURE FREEZE

## 0. 文档定位

本文件是 `2.6 Topology validation` 后续 Skill generation 的 current authoring authority。

本轮设计是在 current 1.2 / 2.5 正式接口和 current authoring rules 下重新敲定的结果。旧 Stage 2 综合冻结文件
`WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md` 中与 2.6 具体检查内容、输入文件或结果记录有关的旧文本均被本文件取代，不得作为后续 2.6 Skill generation 的规则来源。

旧 Stage 2 综合冻结文件仍可用于其尚未被其它 current freeze / active Skill 取代的 Stage-level architecture；读取该文件时不得重新引入其中已经被本文件取代的 2.6 旧规则。

本 freeze 完成不表示已经批准生成 `02_topology_preparation/2.6_topology_validation/SKILL.md`。

## 1. 职责

Topology validation 对当前拓扑整合正式结果进行独立、只读终检。

当前职责只检查已经形成的结构文件和拓扑文件，不修改结构文件、`.top`、`.itp`、map 或参数文件，也不在发现问题时顺手修正拓扑。

发现问题时记录实际问题及可确定的来源；后续是否重新进入其它 Stage 2 工作项由 Stage 2 main Skill 负责。

## 2. 直接正式依赖

当前工作项的直接正式依赖固定为：

1. `classification_result.yaml`；
2. `topology_integration_result.yaml`。

`classification_result.yaml` 提供当前正式的 `component_id + residue_id`、`topology_class` 和 `topology_linked_checks`。

`topology_integration_result.yaml` 提供本次需要检查的拓扑整合正式结果，并定位当前结构文件、当前 map、体系 `.top` 和本次拓扑整合生成的 `.itp`。

当前结构文件的 basename 不在 2.6 固定；2.6 使用 `topology_integration_result.yaml` 实际记录的结构文件路径。

## 3. 结果记录中的文件引用

2.6 正式结果记录中的 `references` 同时承担：

1. 记录当前结果实际依赖的上游正式文件；
2. 为结果正文中反复引用的实际检查文件提供公共绝对路径引用。

因此 `references` 应能够定位：

- `classification_result.yaml`；
- `topology_integration_result.yaml`；
- 当前结构文件；
- 当前 map；
- 体系 `.top`；
- `topology_integration_result.yaml` 中记录的本次拓扑整合生成的全部 `.itp`。

上述路径均保持完整绝对路径语义。实际不存在的可选 `.itp` 不建立占位引用。

当前 map 作为需要通过 `component_id + residue_id` 或 atom identity 定位当前结构 / 拓扑原子时的映射依据；本轮不为 map 单独设置逐原子对应检查或 provenance 检查项目。

具体 reference key 名称和正式结果文件 basename 在 Skill generation 时按仓库级结果生成规则统一确定，不在本 freeze 提前建立无必要的平行 schema。

## 4. 必需检查项

### 4.1 检查体系 `.top` 中各 `#include` 指向的文件是否存在

读取体系 `.top` 中实际出现的 `#include`，逐项解析其实际文件路径。

对每个被引用文件确认：

- 文件实际存在；
- 文件可读取。

发现问题时记录对应 `#include` 和无法定位或无法读取的实际文件路径。

本项不顺带承担参数内容、`moleculetype` 定义或其它拓扑语义检查。

### 4.2 检查当前结构文件与体系 `.top` / `.itp` 中记录的分子、残基和原子是否逐项对应

按体系 `.top` 的 `[ molecules ]` 中记录的 `moleculetype` 顺序和数量，读取对应 `moleculetype` 的 `[ atoms ]`，展开当前拓扑所描述的分子、残基和原子顺序。

逐项核对当前结构文件，至少检查：

- 分子数量；
- 分子顺序；
- 每个分子的原子数量；
- residue 顺序；
- atom 顺序；
- 对应位置的 residue name；
- 对应位置的 atom name。

发现差异时记录体系 `.top` 中的 `[ molecules ]` 条目、对应 `moleculetype`、结构文件中的实际位置和具体差异。

### 4.3 检查已确认并产生 topology effect 的 `topology-linked` 关系是否写入最终拓扑

读取 `classification_result.yaml` 中满足以下条件的 `topology_linked_checks`：

```text
judgment = CONFIRMED
且
topology_effect_applied = true
```

使用其中记录的关系两端身份，在需要时结合当前 map 定位当前结构文件和最终拓扑中的对应 atom。

对每条关系检查最终拓扑是否实际写入与该正式关系相对应的 topology effect。

`judgment = REJECTED` 或 `topology_effect_applied = false` 的记录不作为本项要求最终拓扑必须体现的关系。

对 `COVALENT_CONNECTION`，后续 Skill 应检查关系两端 atom 是否在最终拓扑中形成相应成键关系。

对 `METAL_COORDINATION`，本轮只冻结“必须核对其已经要求的 topology effect 是否体现在最终拓扑”这一检查要求；不得未经进一步确认把所有产生 topology effect 的金属配位机械等同为 `[ bonds ]` 直接成键。具体 topology representation 如在 Skill generation 前仍不能由 current upstream result 唯一确定，应保留为需要进一步敲定的科学细节，不自行发明固定表示。

### 4.4 检查 topology-linked 参数化要求删除的标准残基原子是否已经删除

从 `topology_integration_result.yaml` 记录的实际来源定位本次拓扑整合采用的 topology-linked 参数化正式结果。

读取其中的 `standard_atom_deletions`。

对每个指定删除的标准残基 atom，检查：

- 当前结构文件中已经不存在该 atom；
- 最终拓扑文件中对应 `moleculetype` 的 `[ atoms ]` 中已经不存在该 atom。

发现仍保留的 atom 时，记录对应 topology-linked 参数化正式结果、`component_id + residue_id`、atom name、结构文件或最终 `[ atoms ]` 中的实际位置。

### 4.5 检查 topology-linked 参数化要求的标准残基一侧电荷修改是否写入最终拓扑

从 `topology_integration_result.yaml` 记录的实际来源定位本次拓扑整合采用的 topology-linked 参数化正式结果、对应电荷文件及完成该对应所需的 map。

读取参数化正式结果中的 `charge_modification_scope`。

对该范围内相关 atom，检查最终拓扑文件中对应 `moleculetype` 的 `[ atoms ]` 所记录 `charge` 是否采用对应参数化结果指定的电荷值。

发现差异时记录对应 topology-linked 参数化正式结果、`component_id + residue_id`、atom、参数化结果指定值和最终 `[ atoms ]` 实际值。

### 4.6 使用 `gmx grompp` 检查当前结构文件和体系 `.top`

使用当前结构文件和体系 `.top` 执行 `gmx grompp`。

正式结果至少记录：

- 实际使用的 GROMACS version；
- 实际执行命令；
- `gmx grompp` 输出的 note；
- warning；
- error；
- preprocessing 是否成功。

`gmx grompp` 成功不能替代 4.1–4.5 的独立检查。

用于本项检查的 `.mdp`、临时 `.tpr` 或其它 preprocessing 工作文件不因执行本检查自动成为正式结果或项目结果索引项；如 Skill generation 时需要固定专用 validation `.mdp`，应在当时基于 current GROMACS / Stage 3 接口重新确认，不从旧冻结自动继承。

## 5. 正式结果需要记录的内容

2.6 的正式结果至少记录：

1. 本次使用的 `classification_result.yaml` 和 `topology_integration_result.yaml`；
2. 当前结构文件、当前 map、体系 `.top` 和本次拓扑整合生成的全部 `.itp` 的文件引用；
3. 第 4 节六项检查各自实际执行的检查对象和结果；
4. 每个发现问题对应的实际文件、`moleculetype`、`component_id + residue_id`、atom、`relation_id` 或其它能够唯一定位问题的当前标识；
5. `gmx grompp` 的 note、warning、error 和 preprocessing 结果；
6. 当前规定检查是否全部执行，以及是否仍存在阻止当前结构文件和对应拓扑文件作为同一体系继续使用的问题。

正式结果采用 YAML、Markdown 或组合形式以及具体 basename，在 Skill generation 时按结果复杂度和下游机器消费需求确定；本 freeze 不为了格式对称提前创建 schema。

项目结果索引登记范围也在 Skill generation 时根据最终正式结果集合确定；不得把 `gmx grompp` 临时文件、debug、scratch 或 cache 机械登记为正式结果。

## 6. 当前明确删除的旧 2.6 规则

以下旧设计不再作为 current 2.6 必需检查：

- 单独检查当前 map 与结构文件逐原子对应；
- 单独检查当前 map provenance；
- 单独计算当前体系总电荷并设置电荷判据；
- 在 `gmx grompp` 之外再维护一套 atom type / bonded parameter definition 查找检查；
- 以抽象的 `package completeness`、`internal consistency`、`charge/connectivity sanity` 等标签代替具体检查关系。

如果后续出现新的实际需求，应按 current authoring rules 重新证明其必要性后再修改本 freeze 或 current Skill，不从旧 Stage 2 综合冻结恢复这些已经退出的规则。

## 7. 后续 Skill generation 读取规则

后续生成 `02_topology_preparation/2.6_topology_validation/SKILL.md` 时：

```text
00_authoring/SKILL.md
→ references/task_execution_rules.md
→ references/canonical_terminology.md
→ references/result_generation_rules.md
→ 本文件
→ current 1.2 results interface
→ current 2.5 SKILL.md / results interface / 与本检查直接相关的 2.5 references
```

旧 `WORKFLOW2_STAGE2_ARCHITECTURE_FREEZE_AND_LINKED_ITP_HANDOFF.md` 不得作为 2.6 具体检查规则的 generation source；如果为了 Stage-level architecture 需要读取该文件，只读取仍由它拥有且未被 current authority 取代的 Stage-level 内容。
