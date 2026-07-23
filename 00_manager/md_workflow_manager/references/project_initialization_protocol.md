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

## 3. 初始化事务

按固定顺序执行：

1. 记录入口检查结果，并准备 `ENTRY_STATE_EVALUATED: NEW`；
2. 创建 `00_project_state/`、`00_project_records/` 和顶层业务阶段目录；
3. 生成 project ID、首个 Workstream 和 Focus；
4. 在候选路径生成 project state 与 Workstream state；
5. 将候选 project state 的持久 `entry_state` 设为 `RESUMABLE`；
6. 对候选对象执行 FULL schema、路径、索引和交叉引用校验；
7. 准备备份、回滚和受控提交；
8. 原子提交 project/workstream state；
9. 追加 `ENTRY_STATE_EVALUATED`；
10. 追加 `PROJECT_INITIALIZED`；
11. 创建初始状态 snapshot；
12. 重新读取并核验最终状态。

schema、引用和状态事务应优先调用 `05_tools/tool_registry.yaml` 中状态为 `ACTIVE` 且版本兼容的确定性 Tool。

未测试的 `IMPLEMENTED` Tool 不得作为默认生产路径。

## 4. 初始 Workstream

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

## 5. 初始化 barrier

在 `PROJECT_INITIALIZED` 已提交且最终状态重新读取通过前，禁止：

- 调用 Workflow planning interface；
- 调用 Workflow execution interface；
- 创建 route record；
- 创建 subagent task；
- 创建前台临时子 Agent；
- 启动 Operation 或 Validator。

`PROJECT_INITIALIZED` 只能在候选状态校验通过并成功提交后追加，不得先写事件再补做校验。

## 6. 失败处理

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

## 7. 初始化后的下一事件

初始化完成后，Manager 才进入独立的请求与路线范围解析：

```text
PROJECT_INITIALIZED
→ ROUTE_SCOPE_RESOLUTION
```

路线范围不明确时创建 blocking decision；范围明确后记录 `ROUTE_SCOPE_RESOLVED`。该过程不属于初始化事务。
