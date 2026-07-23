# 项目初始化事务协议

## 1. 适用范围

本协议仅用于 Manager 将入口状态判定为 `NEW` 后的项目基础初始化。

`NEW` 只是本轮入口判定。初始化完成后的持久项目状态必须为 `RESUMABLE`。

初始化不负责：

- 解析路线终点；
- 创建首条业务 route；
- 调用 Workflow；
- 创建业务 task；
- 启动 Operation 或 Validator。

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

在创建候选状态或产生部分管理写入前，先确认初始化所需能力可运行。

### 必需能力

```text
FULL_RUNTIME_VALIDATION
CONTROLLED_STATE_COMMIT
```

当前满足方式：

- `FULL_RUNTIME_VALIDATION`：使用 registry 中 `ACTIVE` 的 `runtime_schema_validator`；
- `CONTROLLED_STATE_COMMIT`：使用本协议第 5 节定义的内建确定性提交路径；
- `state_transaction` Tool 是后续优化，不是 NEW 初始化的强制依赖；其状态为 `DESIGNED` 不得阻塞初始化。

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

1. 完成 capability 预检；
2. 记录入口检查结果，并准备 `ENTRY_STATE_EVALUATED: NEW`；
3. 创建 `00_project_state/`、`00_project_records/` 和顶层业务阶段目录；
4. 生成 project ID、首个 Workstream 和 Focus；
5. 在候选路径生成 project state 与 Workstream state；
6. 将候选 project state 的持久 `entry_state` 设为 `RESUMABLE`；
7. 使用 `runtime_schema_validator --mode FULL` 和 candidate logical-path overlay 校验候选对象、路径、索引和直接交叉引用；
8. 准备备份、回滚和受控提交；
9. 通过内建确定性路径或 ACTIVE `state_transaction` 提交状态；
10. 追加 `ENTRY_STATE_EVALUATED`；
11. 追加 `PROJECT_INITIALIZED`；
12. 创建初始状态 snapshot；
13. 重新读取并核验最终状态。

`runtime_schema_validator` 必须显式使用：

```text
Skill root 下的 03_contracts/
MD project root 下的候选状态、正式状态与 cache
```

不得把 MD project root 误当成 contracts 所在目录。

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
9. 所有状态文件提交成功并重新读取通过后，才允许追加 `PROJECT_INITIALIZED`。

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

在 `PROJECT_INITIALIZED` 已提交且最终状态重新读取通过前，禁止：

- 调用 Workflow planning interface；
- 调用 Workflow execution interface；
- 创建 route record；
- 创建 subagent task；
- 创建前台临时子 Agent；
- 启动 Operation 或 Validator。

`PROJECT_INITIALIZED` 只能在候选状态校验通过并成功提交后追加，不得先写事件再补做校验。

## 8. 失败处理

### capability 预检失败

- 返回 `BLOCKED`；
- `Current blocker` 只列缺失 capability；
- 路线范围和 Workflow 覆盖列入 `Pending after current barrier`；
- 不创建候选状态或部分管理目录。

### 提交前失败

- 返回 `BLOCKED`；
- 保留结构化诊断；
- 不记录 `PROJECT_INITIALIZED`；
- 不进入业务流程。

### 部分提交后异常

- 项目进入 `NEEDS_RECOVERY`；
- 停止新的写入型 task；
- 保留候选、备份、事件和失败证据；
- 按恢复流程重建一致状态。

## 9. 初始化后的下一事件

初始化完成后，Manager 才进入独立的请求与路线范围解析：

```text
PROJECT_INITIALIZED
→ ROUTE_SCOPE_RESOLUTION
```

路线范围不明确时创建 blocking decision；范围明确后记录 `ROUTE_SCOPE_RESOLVED`。该过程不属于初始化事务。

后续 Workflow 未连接时，只能在路线规划到达对应边界后形成 `PARTIAL | BLOCKED`，不得追溯为初始化失败原因。