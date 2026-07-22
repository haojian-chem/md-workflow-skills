# Content map 重新生成报告

## 变更

- 全部 17 份 content map 升级到 schema version 3。
- 将单一 `status` 拆分为 `contract_status` 与 `content_ownership_status`。
- 所有路径改为项目根相对路径。
- 将内容分为 `owned_content` 与 `external_references`。
- 外部内容统一标记为 `reference_only`。
- 删除每个文件重复的 `forbidden_duplication`。
- 未完成契约的 12 个 Skill 改为最小 pending 骨架。
- 对 authoring guide、Manager、Structure Preparation Workflow、source_recognition 和分类 validator 建立定制内容归属。
- 新增 `00_authoring/content_map.schema.yaml`。
- 更新 `assets/content_map.template.yaml`。
- 新增 `scripts/validate_content_maps.py`。

## 不包含的修改

本次只重构 content map 系统，没有修改业务 Skill、公共 contract 或 MD 运行逻辑。
