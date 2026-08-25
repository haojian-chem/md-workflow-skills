# Workflow 1 / Stage 1 atom mapping maintenance architecture freeze

Status: **FROZEN AUTHORING RECORD — RUNTIME RULE MATERIALIZED**

Current shared runtime authority:

```text
references/atom_mapping_rules.md
```

本文件只保存 Stage 1 内部原子映射维护的架构边界。执行规则由 `references/atom_mapping_rules.md` 拥有；相关 active Skill 必须显式引用该 runtime reference。

## 1. Baseline

Stage 1 后续原子映射以初始结构、1.2 `classification_result.yaml` 中的 `component_id + residue_id`、当前结构以及前序结构改写步骤的正式结果共同维持。

1.2 本身不承担 atom mapping，因此不引用该共享 runtime reference。

## 2. Applicable steps

1.3–1.8 中会影响后续 atom correspondence 的步骤必须读取 `references/atom_mapping_rules.md`：

```text
1.3  selection / PDB materialization
1.4  alternate-conformation atom deletion / altLoc cleanup / serial renumbering
1.6  atom deletion / atom-name correction / heavy-atom or residue addition / serial renumbering
1.7  residue-name modification affecting atom locator metadata
1.8  reorder / serial materialization / final atom-map generation
```

1.5 不修改结构，不需要引用。

1.9 读取该 reference，用于 Stage 1 final PDB / final map 的逐原子验证。

## 3. Mapping continuity

Stage 1 不通过一个永久 `atom_id` 取代各步骤已有正式结果。每个结构改写步骤必须使输入 → 输出 atom correspondence 可由其正式输入、输出和正式结果解释：surviving atoms 可继续追踪；删除、rename、新增或 replacement 不得静默发生；serial 重编号和 reorder 不等于 atom identity 改变。

具体逐步骤规则由 current `references/atom_mapping_rules.md` 拥有，不在本 freeze 维护第二套可变规范。

## 4. Boundary

本 freeze 只授权并规定 Stage 1 原子映射维护。Stage 2 的 atom mapping / provenance 语义不在本文件中定义，也不由本次 authoring 变更决定。
