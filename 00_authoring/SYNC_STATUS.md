# Authoring 文件同步状态

更新日期：2026-08-06

# 当前基线

```text
1.2 component/residue classification: present_unvalidated
1.3 chain/component selection: PASS（沿用 2026-07-31 验收）
runtime_schema_validator: ACTIVE
```

1.2 已完成当前状态、独立关系决定与本地 CCD-compatible library 的实现调整，但尚未完成新的仓库级、真实结构与 1.2→1.3 回归。2026-07-31 的 PASS 证据只适用于旧业务 head，不得用于本次修改。

# 权威位置

```text
1.2 局部执行编排
→ 02_validators/component_and_residue_classification_validator/SKILL.md

1.2 科学语义
→ 02_validators/component_and_residue_classification_validator/references/classification_rules.md

1.2 CLI 与模块接口
→ 02_validators/component_and_residue_classification_validator/scripts/README.md

1.2 当前验收状态
→ 04_evals/component_and_residue_classification_validator/VALIDATION.md

1.3 选择接口与验收
→ 02_operations/chain_and_component_selection/
→ 04_evals/chain_and_component_selection/VALIDATION.md
```

本文件只记录状态和权威位置，不复制业务规则。

# 1.2 本次变更

```text
classification_observations.yaml
→ 保存同一 structure SHA + selected model 的当前状态
→ 关系检查直接更新 relation observations、分类、分组和 summary

relation_decisions.yaml
→ 独立保存稳定 relation_id 对应的人工决定

references/ccd_library/
→ 固定内置本地库；附加库必须显式声明
→ 禁止运行时下载、cache、snapshot 和无界扫描

classification_result.yaml
→ 继续物化 1.3 使用的 opaque component/residue/endpoint/relation IDs
```

# 当前验证结论

已完成：

- Python 编译与 JSON Schema 元校验；
- 38 个内置 CCD-compatible atom-table 条目的 ID/hash/解析检查；
- relation ID 的共价无方向与配位有角色检查；
- relation result → observations → topology regrouping 的合成检查；
- current observations → final 1.3 contract 的合成整合检查。

仍需：

- 更新并执行完整 1.2 测试集；
- 真实 PDB/mmCIF/AF3/GROMACS 回归；
- 1.2→1.3 真实选择回归；
- 补齐并核验已批准的辅因子/配体 CCD seed；
- Authoring/Manager closure 回归。
