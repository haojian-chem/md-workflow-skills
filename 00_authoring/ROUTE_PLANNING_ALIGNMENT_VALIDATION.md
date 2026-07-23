# Route Planning Interface Alignment Validation

日期：2026-07-23

## 1. 当前范围

当前路线体系包括：

- `03_contracts/workflow_route_fragment.schema.yaml`；
- `03_contracts/route_record.schema.yaml` v3；
- `03_contracts/project_event.schema.yaml` 的 route-scope events；
- `00_manager/md_workflow_manager/references/route_planning_protocol.md`；
- Manager 的入口初始化、范围解析、规划循环和执行循环；
- `structure_preparation_workflow` 的 planning/execution 双接口；
- stage registry、layer boundaries、authoring Skill 和模板；
- Manager、Workflow 与 source recognition 行为 fixtures。

## 2. 当前 Contract 变更

### `project_event.schema.yaml`

新增：

```text
ROUTE_SCOPE_REQUESTED
ROUTE_SCOPE_RESOLVED
```

### `route_record.schema.yaml` v3

新增必填对象：

```yaml
scope_resolution:
  source: USER_REQUEST | RESOLVED_DECISION | ACTIVE_ROUTE | RECORDED_WORKSTREAM_GOAL
  resolved_event_id:
  decision_id:
```

`RESOLVED_DECISION` 来源必须提供非空 `decision_id`。

route scope 的解析事件和 route 创建事件保持分离：

```text
ROUTE_SCOPE_RESOLVED
≠ ROUTE_CREATED
```

## 3. Manager barrier

已确认：

```text
ENTRY_STATE_EVALUATED: NEW
→ 候选状态校验和原子提交
→ PROJECT_INITIALIZED
→ ROUTE_SCOPE_RESOLUTION
→ ROUTE_SCOPE_RESOLVED
→ Workflow fragments
→ ROUTE_CREATED
→ Workflow execution decision
```

规则：

- NEW 初始化本身不触发 route planning；
- 首个 Workstream 初始化时 `active_route_id: null`；
- 模糊终点必须创建 blocking decision；
- `ROUTE_SCOPE_RESOLVED` 前不请求 fragment；
- 有效 active route 不存在时不创建业务 task。

## 4. 双接口边界

已确认：

- Workflow 规划接口返回本阶段 `workflow_route_fragment`；
- Workflow 执行接口返回一个 `workflow_decision`；
- Manager 决定跨 Workflow 起终点并拼接 fragment；
- Workflow 不跨阶段拼接路线；
- Manager 不根据阶段名称自行编造内部步骤；
- execution decision 与 active route 因新证据不一致时，先修订路线再执行。

## 5. 当前静态状态

通过 GitHub 回读确认：

```text
md_workflow_manager/SKILL.md: 428 lines
structure_preparation_workflow/SKILL.md: 335 lines
source_recognition/SKILL.md: 263 lines
route_record.schema.yaml: schema_version 3
```

三份 Skill 文件均低于 authoring validator 的 500 行渐进披露警告阈值。

本轮尚未在测试主机重新运行全量 `validate_contracts.py`，因此 route v3 和 event enum 的 Draft 2020-12 `check_schema` 仍列为待执行，不在本报告中提前宣称通过。

当前共享 contract 总数仍为 15。

## 6. 行为 fixtures

当前包括：

- Manager behavior cases：20；
- Manager initialization transaction cases：4；
- Manager route planning cases：12；
- structure preparation route fragment cases：9；
- source recognition safety cases：10。

新增覆盖：

- NEW 初始化不创建 route；
- NEW 自动初始化不依赖额外用户提示；
- NEW 判定与初始化后的 RESUMABLE 持久状态分离；
- `PROJECT_INITIALIZED` 仅在状态校验和提交成功后记录；
- scope event 必须先于 route record；
- route v3 引用 resolved scope event；
- 模糊终点产生 `ROUTE_SCOPE_REQUESTED`；
- 新 Workstream 创建本身不自动规划路线。

既有覆盖：

- 单 Workflow 完整路线；
- 未连接 Workflow 边界的 PARTIAL 路线；
- 条件步骤保留；
- fragment artifact 接口不兼容；
- execution decision 触发 route revision；
- 用户指定 Workflow 内终点；
- 已运行下游时创建新 Workstream；
- 无变化时不创建 revision；
- 默认复制、相同副本复用、目标冲突、多候选选择、显式移动和 hash 失败清理。

## 7. Source recognition 安全规则

已确认：

- 默认复制，不移动原始文件；
- 复制前后计算 SHA-256；
- 原始文件保持不变；
- 相同目标复用；
- 不同内容目标不覆盖；
- 只有 resolved user decision 和 source write permission 同时存在时才允许移动；
- `01_sources/` 等受保护来源不得移动；
- Operation 不直接创建 artifact record 或修改项目状态。

## 8. 仍需完成

相关 Skill 仍保持 `draft`。后续必须：

1. 在测试主机运行全量 contract validator；
2. 将 initialization/scope/route fixtures 转换为完整 schema-valid 对象；
3. 执行 NEW → PROJECT_INITIALIZED 的真实目录测试；
4. 执行模糊请求 → ROUTE_SCOPE_REQUESTED 的测试；
5. 执行明确终点 → ROUTE_SCOPE_RESOLVED → route v3 的规划测试；
6. 执行 Manager → Workflow decision → source_recognition → result → artifact/state 的端到端测试；
7. 用真实 PDB、mmCIF 和 AF3 CIF 文件验证复制、复用、冲突和 hash 清理；
8. 迁移 `component_and_residue_classification_validator`；
9. 后续 Workflow 建立后验证跨阶段 fragment 拼接。

## 9. 未冻结扩展

content map 的以下字段仍未加入 schema：

- `load_when`；
- `applicable_to`。
