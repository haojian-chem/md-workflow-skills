# Route Planning Interface Alignment Validation

日期：2026-07-22

## 1. 本轮范围

本轮新增或修改：

- `03_contracts/workflow_route_fragment.schema.yaml`；
- `03_contracts/route_record.schema.yaml` v2；
- `00_manager/md_workflow_manager/references/route_planning_protocol.md`；
- Manager 的规划循环和执行循环；
- `structure_preparation_workflow` 的 planning/execution 双接口；
- stage registry、layer boundaries、authoring Skill 和模板；
- Manager、Workflow 与 source recognition 行为 fixtures；
- `source_recognition` 的默认复制与显式移动规则。

## 2. Schema 检查

对以下两份新增或实质修改的 schema 执行 YAML 解析和 JSON Schema Draft 2020-12 `check_schema`：

```text
workflow_route_fragment.schema.yaml: PASS
route_record.schema.yaml v2: PASS
schema_errors: 0
```

其余 13 份共享 schema 本轮未修改，沿用 `CONTRACT_ALIGNMENT_VALIDATION.md` 中的既有检查结果。

当前共享 contract 总数：

```text
15
```

`validate_contracts.py` 的 REQUIRED 清单已加入 `workflow_route_fragment.schema.yaml`。

## 3. 双接口边界

已确认：

- Workflow 规划接口返回本阶段 `workflow_route_fragment`；
- Workflow 执行接口返回一个 `workflow_decision`；
- Manager 决定跨 Workflow 起终点并拼接 fragment；
- Workflow 不跨阶段拼接路线；
- Manager 不根据阶段名称自行编造内部步骤；
- execution decision 与 active route 因新证据不一致时，先修订路线再执行。

## 4. Skill 静态状态

通过 GitHub 回读确认 front matter 与主要接口段存在：

```text
md_workflow_manager/SKILL.md: 294 lines
structure_preparation_workflow/SKILL.md: 335 lines
source_recognition/SKILL.md: 263 lines
```

三份文件均低于 authoring validator 的 500 行渐进披露警告阈值。

## 5. 行为 fixtures

新增：

- Manager route planning cases：9；
- structure preparation route fragment cases：9；
- source recognition safety cases：10。

覆盖：

- 单 Workflow 完整路线；
- 未连接 Workflow 边界的 PARTIAL 路线；
- 条件步骤保留；
- fragment artifact 接口不兼容；
- execution decision 触发 route revision；
- 用户指定 Workflow 内终点；
- 已运行下游时创建新 Workstream；
- 无变化时不创建 revision；
- 终点歧义；
- 默认复制、相同副本复用、目标冲突、多候选选择、显式移动和 hash 失败清理。

## 6. Source recognition 安全规则

已冻结为：

- 默认复制，不移动原始文件；
- 复制前后计算 SHA-256；
- 原始文件保持不变；
- 相同目标复用；
- 不同内容目标不覆盖；
- 只有 resolved user decision 和 source write permission 同时存在时才允许移动；
- `01_sources/` 等受保护来源不得移动；
- Operation 不直接创建 artifact record 或修改项目状态。

## 7. 仍需完成

以下内容尚未完成，因此相关 Skill 仍保持 `draft`：

1. 将行为 fixtures 转换为可由共享 schema 校验的完整输入/输出对象；
2. 执行一次 Manager → Workflow fragment → route record 的规划测试；
3. 执行一次 Manager → Workflow decision → source_recognition → result → artifact/state 的端到端测试；
4. 用真实 PDB、mmCIF 和 AF3 CIF 文件验证复制、复用、冲突和 hash 清理；
5. 迁移 `component_and_residue_classification_validator`；
6. 后续 Workflow 建立后验证跨阶段 fragment 拼接。

## 8. 未冻结扩展

content map 的以下字段仍未加入 schema：

- `load_when`；
- `applicable_to`。
