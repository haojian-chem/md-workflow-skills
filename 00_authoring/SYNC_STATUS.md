# Authoring 文件同步状态

更新日期：2026-08-06

# 当前基线

```text
1.2 component/residue classification: present_unvalidated
1.3 chain/component selection: PASS（沿用 2026-07-31 验收，需针对本次上游变更重跑）
runtime_schema_validator: ACTIVE
```

1.2 当前状态重构已实现；迁移后的本地自动测试与真实 AF3 输入验收通过。hosted CI、真实 PDB/mmCIF/GROMACS、完整 1.2→1.3 选择回归及批准辅因子/配体 CCD seed 仍未闭合，因此状态保持 `present_unvalidated`。

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
- 迁移后的 Skill 1.2 自动测试集本地通过；
- 真实 AlphaFold Server CIF + job request 验收本地通过；
- relation ID、人工决定、topology regrouping 与 final contract 合成检查；
- 历史 1.2→1.3 opaque-ID 接口回归。

仍需：

- hosted GitHub Actions；
- 真实 PDB/mmCIF/GROMACS 回归；
- 完整真实 1.2→1.3 选择验收；
- 已批准辅因子/配体 CCD seed 完整性与 hash 核验；
- Authoring/Manager closure 回归。
