# 1.2 组分与残基分类规则

## 1. 适用范围

本文件只定义 `component_and_residue_classification_validator` 的局部科学与数据语义。它不定义后续链选择、altLoc 处理、结构完整性 gate、补全、质子化或拓扑生成。

## 2. 名称与身份

- `residue_name`、`atom_name` 严格区分大小写并原样保留；
- 不进行 alias、大小写归一化、正则或模糊匹配；
- 作者残基编号保存为：

```yaml
source_resid:
  number: "145"
  insertion_code: A
```

- `source_chain_id` 保留作者链 ID；
- `chain_index` 是 selected model 内部组分归属编号；
- 不为 residue、atom、relation 额外生成 UUID。

## 3. 分类值

`polymer_class`：

```text
POLYMER | BRANCHED | NONPOLYMER | WATER
```

`topology_class`：

```text
STANDARD_RESIDUE
COVALENTLY_LINKED_NONSTANDARD
INDEPENDENT_NONSTANDARD
SOLVENT_COMPONENT
ION_COMPONENT
```

合法组合：

| polymer_class | topology_class |
|---|---|
| POLYMER | STANDARD_RESIDUE, COVALENTLY_LINKED_NONSTANDARD |
| BRANCHED | STANDARD_RESIDUE, COVALENTLY_LINKED_NONSTANDARD, INDEPENDENT_NONSTANDARD |
| NONPOLYMER | COVALENTLY_LINKED_NONSTANDARD, INDEPENDENT_NONSTANDARD, SOLVENT_COMPONENT, ION_COMPONENT |
| WATER | SOLVENT_COMPONENT |

未解决状态通过 `resolution_status: UNRESOLVED | CONFLICT | PENDING_CONFIRMATION` 表达。

## 4. 项目定义

`project_residue_definitions.yaml` 使用列表。每个精确 `residue_name` 只能定义一次：

```yaml
schema_version: "1.0"
residue_definitions:
  - residue_name: HEM
    polymer_class: NONPOLYMER
    topology_class: INDEPENDENT_NONSTANDARD
    ccd_id: HEM
```

同一名称重复定义是确定性配置错误。定义适用于 selected model 中全部精确同名实例；实例差异由关系结果表达。

## 5. 分类来源

### REGISTRY

```text
project exact definition
→ Skill exact registry
→ entity/polymer context
```

项目与 Skill 同时定义且分类标签冲突时累计人工确认，不自动覆盖。

### FORCE_FIELD_ANALYSIS

```text
project exact definition
→ exact RTP residue block
→ unresolved-only Skill registry fallback
→ entity/polymer context
```

RTP 文件名、`residuetypes.dat` 和名称启发式均不参与力场识别。

## 6. Force field RTP

- 扫描指定 root 下所有 `*.rtp`；
- residue block 名称精确匹配；
- 非水模板重复定义需要人工确认；
- 多套水模型可共存，1.2 不选择水模型；
- 标准残基重原子检查使用选定 RTP block 的 `[ atoms ]`；
- terminal residue 使用显式 terminal mapping 指向端基 RTP block；
- v1 不应用 `.n.tdb/.c.tdb`；
- `specbond.dat` 不参与当前结构连接判定。

## 7. CCD

在 REGISTRY 模式下，标准与非标准残基均使用 CCD；在 FORCE_FIELD_ANALYSIS 下，非标准残基使用 CCD。

CCD ID 只来自显式 `ccd_id` 或精确 residue name。获取顺序：项目 snapshot、本地指定目录、共享 cache、按策略下载。项目 snapshot 是本次结果的权威参考。

重原子比较基于 atom identity set，排除 H/D。备用名称只产生候选映射，不自动改名。

## 8. 缺失残基

- PDB/mmCIF 比较预期序列与实际坐标残基；
- residue numbering gap 不能单独证明缺失；
- AF3 默认不检查；需要输入 JSON、FASTA 或等价序列依据；
- 仅记录缺失残基，不标注缺失区域位置类型；
- 缺失残基必须具有作者 `source_resid.number` 才进入正式 residue record；
- 编号或 chain 归属无法确定时完成全扫描后统一确认。

## 9. 重原子与 altLoc

重原子结果只记录完整、缺失、多出、映射、模板不可用或未执行，不分类为主链/侧链。

存在多个 altLoc 的 residue：

```text
MULTIPLE_CONFORMATIONS
```

并跳过重原子检查。关系几何也不从多个构象中选最短距离或平均坐标。

## 10. 可能共价连接

项目只定义已知精确 atom pair 与距离范围。工具枚举全部实例组合。

状态：

```text
CONFIRMED_BY_STRUCTURE
GEOMETRY_SUPPORTED_CANDIDATE
NOT_GEOMETRICALLY_SUPPORTED
CONNECTION_DEFINITION_CONFLICT
PARTNER_NOT_FOUND
ATOM_NOT_FOUND
GEOMETRY_NOT_EVALUATED_MULTIPLE_CONFORMATIONS
```

显式共价且距离符合可直接确认；仅几何支持必须人工确认。定义文件本身不创建连接。

已确认关系可把非标准组分提升为 `COVALENTLY_LINKED_NONSTANDARD`。标准残基默认保持 `STANDARD_RESIDUE`。

## 11. 金属配位

项目定义 metal、donor、元素、距离范围和：

```yaml
topology_effect:
  promote_nonstandard_to_linked: true | false
```

状态：

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

多个 donor 配位同一 metal 是合法的，不自动构成冲突。关系始终为 `METAL_COORDINATION`。

当 topology effect 为 true 且关系由结构显式确认或经用户确认时，非标准组分可提升为 linked。例如 HEM 的 Fe 与蛋白质 CYS:SG 或 HIE:NE2 的 topology-forming 配位。Mg、Zn 是否产生该效果由项目定义明确指定。

## 12. Chain groups

- polymer/branched chain 先按源结构顺序分配稳定 baseline index；
- 普通水、离子按精确名称汇总；
- 条件一致的重复小分子可汇总；
- 异常或参与关系的实例单独记录；
- 与一条 polymer chain 相连的非标准组分最终并入该 index；
- 与多条 chain 相连时独立成组并记录 linked indices；
- source association 只表示原文件归属，不代表 topology 归属。

## 13. 扫描与确认

技术错误立即失败。科学歧义、单 component 参考失败、编号/映射问题完成所有可执行检查后统一汇总。

待确认项在未解决前不得产生 topology effect。存在确认项时可输出 `PENDING_USER_CONFIRMATION` 的整合结果，但 Workflow 不得把 1.2 判为已通过。
