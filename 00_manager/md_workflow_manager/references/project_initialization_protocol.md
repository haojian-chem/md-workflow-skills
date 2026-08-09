# 项目初始化事务协议

## 1. 适用范围

本协议仅用于 Manager 将入口状态判定为 `NEW` 后的项目基础初始化。

`NEW` 只是本轮入口判定。初始化完成后的持久项目状态必须为 `RESUMABLE`。

初始化不负责：

- 解析路线终点；
- 创建首条业务 route；
- 调用 Workflow；
- 创建业务 task；
- 启动 Operation 或 Validator；
- 创建初始化 state snapshot。

NEW 初始化期间不得读取任何 Workflow 定义。Workflow、route planning protocol 和业务 Skill 只能在 `PROJECT_INITIALIZED` barrier 之后按实际请求加载。

## 2. 启动条件

仅当以下条件同时满足时自动初始化：

- Skill architecture root 已明确；
- MD project root 已明确；
- 没有可信可恢复状态；
- 项目目录为空或只有初始输入；
- 没有明显旧结构、拓扑、完整体系或模拟产物；
- 没有目录所有权冲突；
- 不需要用户确认破坏性操作。

已有明显业务产物但缺少可信状态时，不得判为 NEW，应进入恢复。

## 3. 初始化 capability 预检

在创建候选状态或产生部分管理写入前，只确认初始化 hard gate 所需能力是否可运行，不执行完整业务审计。

### 必需能力

```text
FULL_RUNTIME_VALIDATION
CONTROLLED_STATE_COMMIT
```

当前满足方式：

- `FULL_RUNTIME_VALIDATION`：使用 registry 中 `ACTIVE` 的 `runtime_schema_validator`；
- `CONTROLLED_STATE_COMMIT`：使用本协议第 5 节定义的内建确定性提交路径；
- `state_transaction` Tool 是后续优化，不是 NEW 初始化的强制依赖；其状态为 `DESIGNED` 不得阻塞初始化。

capability 预检只检查工具/内建路径的可用性、版本兼容性和必要路径，不提前运行 FULL validation。

若必需能力缺失：

```text
Current blocker:
<missing capability>

Pending after current barrier:
<route scope / Workflow coverage / later inputs>
```

只有缺失的当前 capability 可以作为初始化停止原因。用户请求的路线终点是否明确、后续 Workflow 是否已连接，均在 `PROJECT_INITIALIZED` 之后处理，不得列为当前初始化 blocker。

## 4. 初始化事务

按固定顺序执行：

1. 完成最小入口检查和 capability 预检；
2. 记录入口检查结果，并准备 `ENTRY_STATE_EVALUATED: NEW`；
3. 创建 `00_project_state/`、`00_project_records/` 和顶层业务阶段目录；
4. 生成 project ID、首个 Workstream 和 Focus；
5. 在候选路径生成 project state 与 Workstream state；
6. 将候选 project state 的持久 `entry_state` 设为 `RESUMABLE`；
7. 使用 `runtime_schema_validator --mode FULL` 和 candidate logical-path overlay 对当前候选初始化对象执行一次有效 FULL 校验；
8. FULL PASS 后准备备份、回滚和受控提交；
9. 通过内建确定性路径或 ACTIVE `state_transaction` 提交状态；
10. 追加 `ENTRY_STATE_EVALUATED`；
11. 追加 `PROJECT_INITIALIZED`；
12. 执行 lightweight post-commit verification；
13. 结束初始化，并独立进入请求与路线范围解析。

`runtime_schema_validator` 必须显式使用：

```text
Skill root 下的 03_contracts/
MD project root 下的候选状态、正式状态与 cache
```

不得把 MD project root 误当成 contracts 所在目录。

### 4.1 FULL 次数规则

初始化 gate 要求的是“一次有效 FULL PASS”，不是机械执行多轮 FULL。

- candidate 内容未变化且已经获得有效 FULL PASS 时，不得再次执行 FULL；
- Tool 调用参数错误、调用失败、返回空结果或其他未形成有效 validation result 的情况，不视为完成 FULL gate，修正调用后可重新运行；
- FULL FAIL 后若修改了 candidate，必须对修改后的 candidate 重新运行 FULL；
- 正式提交成功后不得为了保守复核再次执行 FULL；
- post-commit 阶段只做第 4.2 节的轻量一致性核验。

### 4.2 Lightweight post-commit verification

受控提交和初始化事件写入后，只核验提交是否与已经通过 FULL 的 candidate 一致，不重复项目级 schema/reference 扫描。

至少确认：

- 正式 `project_state.yaml` 与初始 Workstream state 文件存在且可读取；
- YAML/JSON 可解析；
- project ID、Workstream ID、两个 root、`entry_state: RESUMABLE` 等初始化关键字段与已验证 candidate 一致；
- 提交目标内容 hash 或等价确定性比较结果与已验证 candidate 一致；
- `ENTRY_STATE_EVALUATED` 与 `PROJECT_INITIALIZED` 事件已成功追加且引用可定位；
- 不存在提交失败留下的 candidate/backup 冲突信号。

post-commit verification 不调用 `runtime_schema_validator --mode FULL`。发现不一致时进入 `NEEDS_RECOVERY`，不得通过重复 FULL 掩盖提交问题。

## 5. 内建确定性状态提交路径

在 `state_transaction` Tool 尚未 ACTIVE 时，Manager 使用本节作为已批准的确定性备用路径。该路径不是 LLM 自由推理校验，也不降低 FULL gate。

固定顺序：

1. 候选文件必须位于目标文件同一文件系统中的受控临时目录；
2. FULL PASS 前不得改写正式 `project_state.yaml` 或 Workstream state；
3. 对已有目标创建 `.bak` 或等价恢复副本；NEW 项目目标通常不存在，但仍检查同名冲突；
4. 每个候选文件完整写入并关闭后，使用原子 rename/replace 提交到对应正式路径；
5. 不通过复制后删除来模拟原子替换；
6. 任一文件提交失败立即停止后续提交；
7. 无正式文件被替换时返回 `BLOCKED`；
8. 已发生部分提交时进入 `NEEDS_RECOVERY`，保留候选、备份和失败证据；
9. 所有状态文件提交成功并通过 lightweight post-commit verification 后，初始化事务才算闭合。

该路径只负责管理状态提交，不复制、不移动、不修改 PDB 或其他业务输入。

## 6. 初始 Workstream

初始 Workstream 必须处于未规划状态：

```yaml
current_position:
  workflow_name: null
  substep: null
  task_id: null
activity_status: IDLE
active_route_id: null
active_task_id: null
```

初始 purpose 可以概括研究对象或用户请求，但不得把未确认的路线终点写成既定目标。

## 7. 初始化 barrier

在 `PROJECT_INITIALIZED` 已提交且 lightweight post-commit verification 通过前，禁止：

- 读取 Workflow 定义；
- 调用 Workflow planning interface；
- 调用 Workflow execution interface；
- 创建 route record；
- 创建 subagent task；
- 创建前台临时子 Agent；
- 启动 Operation 或 Validator。

`PROJECT_INITIALIZED` 只能在候选状态 FULL 校验通过并成功提交后追加，不得先写事件再补做校验。事件追加后的 post-commit verification 只核验提交一致性，不重新运行 FULL。

## 8. Snapshot 策略

NEW 初始化完成时不创建 state snapshot。

原因：

- 初始化状态本身就是首次权威状态，没有更早的可信状态可回滚；
- candidate + FULL + controlled commit + `.bak`/失败证据已经覆盖初始化事务恢复需求；
- `project_state.yaml`、初始 Workstream state 和初始化事件共同构成足够的恢复锚点；
- 此时创建 snapshot 只会复制刚提交的状态并增加初始化 I/O 与记录复杂度。

后续 snapshot 只在 `design_records/logging_and_record_system.md` 定义的真正恢复关键节点创建。

## 9. 失败处理

### capability 预检失败

- 返回 `BLOCKED`；
- `Current blocker` 只列缺失 capability；
- 路线范围和 Workflow 覆盖列入 `Pending after current barrier`；
- 不创建候选状态或部分管理目录。

### FULL 或提交前失败

- 返回 `BLOCKED`；
- 保留结构化诊断；
- 不记录 `PROJECT_INITIALIZED`；
- 不进入业务流程。

### 部分提交或 post-commit verification 异常

- 项目进入 `NEEDS_RECOVERY`；
- 停止新的写入型 task；
- 保留候选、备份、事件和失败证据；
- 不通过重复 FULL 代替恢复；
- 按恢复流程重建一致状态。

## 10. 初始化后的下一事件

初始化完成后，Manager 才进入独立的请求与路线范围解析：

```text
PROJECT_INITIALIZED
→ ROUTE_SCOPE_RESOLUTION
```

此时才允许按需读取 `stage_registry.yaml`、`route_planning_protocol.md` 和实际涉及的 Workflow。

路线范围不明确时创建 blocking decision；范围明确后记录 `ROUTE_SCOPE_RESOLVED`。该过程不属于初始化事务。

后续 Workflow 未连接时，只能在路线规划到达对应边界后形成 `PARTIAL | BLOCKED`，不得追溯为初始化失败原因。