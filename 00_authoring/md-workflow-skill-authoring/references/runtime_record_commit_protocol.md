# Runtime Record Commit Protocol

Status: DESIGN_FROZEN_IMPLEMENTATION_PENDING

本协议定义 R4：把普通 task 闭环中的机械记录构造、schema 校验和受控提交从 Manager LLM 推理中移出。

## 1. 目标

当前普通 task 的主要固定成本之一是：

```text
structured business result
→ Manager LLM 重新解释
→ 手工构造 result/event/artifact/state YAML
→ 再校验
→ 再提交
```

目标路径：

```text
semantic inputs + structured responsibility result
→ deterministic record builder
→ candidate records/state
→ FAST validation
→ controlled commit
→ compact commit receipt
```

Manager 仍拥有提交授权和语义决定；Tool 只承担机械构造与确定性事务。

## 2. 适用范围

默认用于普通、短耗时、当前进程内闭合的 task。

可以构造：

- task result record；
- terminal task event；
- artifact record（仅有 artifact candidate/status change 时）；
- decision/submission record（仅调用方已提供完整语义对象时）；
- Workstream state 的机械字段更新；
- project state 的必要最小更新（仅项目级字段实际变化时）。

不负责：

- 解释科学结果；
- 决定 artifact 是否科学 VALIDATED；
- 发明 decision；
- 选择 route/next node；
- route revision；
- recovery 语义判断；
- 用户展示内容的开放式总结。

## 3. 输入模型

调用方必须提供已经完成语义解析的输入：

```yaml
commit_request:
  task_identity:
  workstream_id:
  route_id:
  route_node_id:
  execution_backend:
  responsibility_result:
  semantic_state_delta:
  artifact_updates: []
  decision_updates: []
  submission_updates: []
  route_progression:
  allowed_management_paths: []
```

其中：

- `responsibility_result` 必须来自 Operation/Validator/Tool 的结构化终态；
- `semantic_state_delta` 只包含 Manager/Workflow 已决定的语义变化；
- builder 不得根据自由文本 summary 自行推断状态；
- 未提供的语义对象不得由 builder 猜测生成。

## 4. 机械构造规则

builder 可以确定性完成：

- contract version 和固定 metadata；
- task/result identity 复制；
- 终态 event 类型映射；
- 文件路径、hash、时间戳等确定性字段；
- artifact candidate 到 artifact record 的结构映射；
- active_task 清除；
- current position 按已给出的 `route_progression` 更新；
- last-event direct reference；
- 无变化字段保持不写/不重写。

builder 不得：

- 把 `Operation DONE` 转换成 `artifact VALIDATED`；
- 根据 warning 自行决定 route revision；
- 根据 result prose 生成 blocking decision；
- 修改未在 semantic delta 中授权的 Focus/Workstream lifecycle；
- 创建 snapshot；
- 创建 no-op route revision。

## 5. Candidate-first transaction

固定流程：

```text
1. validate commit_request shape
2. read only directly affected current records/state
3. build candidate result/records/state
4. call runtime_schema_validator FAST on changed candidate instances
5. check direct references for changed objects
6. if PASS, controlled commit
7. append terminal event in the same logical closure
8. verify committed hashes/identities
9. return compact commit_receipt
```

任何 FAIL/ERROR：

- 不宣称 task closure committed；
- 不降低 gate；
- 不由 LLM 手工补写绕过；
- 返回结构化 blocker/error。

## 6. Compact receipt

返回 Manager 的信息应尽量小：

```yaml
commit_receipt:
  status: COMMITTED | BLOCKED | ERROR
  task_id:
  workstream_id:
  changed_paths: []
  terminal_event_id:
  artifact_record_ids: []
  decision_record_ids: []
  submission_record_ids: []
  workstream_state_changed: true | false
  project_state_changed: true | false
  validation_status: PASS | FAIL | ERROR
  next_route_position:
  warnings: []
```

Manager 不需要重新读取所有新写 YAML 来“理解一次”；只有 receipt 与预期冲突、Tool 报错或用户要求审计时才回读详细对象。

## 7. 权限

该 capability 只能由 Manager 授权调用。

允许写：

```text
00_project_state/**
00_project_records/**
```

但必须进一步受 `allowed_management_paths` 和 registry 权限约束。

业务文件只读引用，不得由 record committer 修改。

## 8. 与 task.yaml 的关系

普通短 task 仍需要稳定 task identity。

R4 实现可以采用以下任一确定性方式：

- Manager/轻量 builder 在执行前生成最小不可变 `task.yaml`；
- 或统一 task builder 生成并提交。

不得让业务 Agent 手工维护管理目录。

## 9. 强化任务

外部 submission、长耗时、高风险或不可逆任务仍使用强化预记录流程。

R4 可以为这些流程提供 deterministic builder/commit，但不能删除其恢复锚点。

## 10. 实现要求

拟议 capability 名：

```text
runtime_record_committer
```

实现前必须具备：

- tool.yaml；
- fixtures：DONE / BLOCKED / FAILED / artifact change / no project-state change；
- invalid semantic delta 负向测试；
- partial commit / rollback 测试；
- benchmark；
- 与 `runtime_schema_validator` 的集成测试。

只有 ACTIVE 后，Manager 才能把普通 closure 的机械构造默认交给该 Tool。
