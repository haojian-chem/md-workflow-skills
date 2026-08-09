# Active Route Fast-Path Protocol

Status: DESIGN_FROZEN_IMPLEMENTATION_PENDING

本协议定义 R5：在 active route 未被新证据改变时，避免每个普通 task 完成后重新让完整 Workflow 做一次 LLM 语义判断。

## 1. 原则

active route 是可执行的预计路径投影，不只是历史记录。

因此普通节点完成后，若没有任何会改变路线语义的事实，运行时可以确定性判断是否进入 route 中已记录的下一节点。

fast path 不改变以下原则：

- route 不是不可变业务事实；
- 新证据可以触发 Workflow/Manager 语义重判；
- 条件步骤不能在无证据时被静默跳过；
- 用户 scope/终点仍是硬边界；
- Validator gate 仍必须满足。

## 2. 输出状态

fast-path evaluator 只允许返回：

```text
ADVANCE
REENTER_WORKFLOW
STOP_SCOPE
BLOCKED
```

### ADVANCE

满足全部 fast-path 条件，进入 active route 中已经记录的下一 node。

### REENTER_WORKFLOW

有新证据可能改变步骤、条件、gate 或 route，需要当前 Workflow 做语义判断。

### STOP_SCOPE

当前节点已达到用户本轮终点或 active route 终点。

### BLOCKED

状态/记录/route 本身无法安全解释，不能自动推进，也不能把问题伪装成正常 Workflow 分支。

## 3. ADVANCE 必须满足的条件

全部满足才允许 `ADVANCE`：

1. active route 存在、未失效且当前 node 唯一可定位；
2. 当前 task/result identity 与 route node 一致；
3. 当前 task 已进入允许推进的终态；
4. 当前 node 要求的 Operation/Validator gate 已满足；
5. 没有 blocking confirmation/decision；
6. 没有 failure；
7. 没有 `route_affecting_evidence`；
8. artifact candidate/type/interface 与 route 预期一致；
9. 没有新的条件证据会使 REQUIRED/CONDITIONAL 关系改变；
10. Workstream state 与 active route current position 一致；
11. next node 已存在于 active route；
12. next node 位于用户已解析的 route scope 内；
13. next node 不要求尚未解决的输入/decision；
14. 当前没有 project/workstream recovery；
15. 没有高风险/不可逆 barrier 要求 Manager 语义介入。

任一条件无法确定时，不得猜测 ADVANCE。

## 4. 必须 REENTER_WORKFLOW 的触发器

至少包括：

- blocking/nontrivial confirmation item；
- result 明确标记 route-affecting evidence；
- 条件步骤的新证据；
- artifact 类型/接口变化；
- unexpected output；
- Validator outcome 要求新分支；
- 当前 node 与 route 预计 gate 不一致；
- 用户新指令改变范围/策略；
- backend 结果暴露新的科学歧义；
- active route 仍可解释但预计下一 node 可能不再适用。

Workflow 语义重判后，如 route 实际变化，再创建 revision；若没有变化，不创建 no-op revision。

## 5. BLOCKED 与 recovery

以下情况不得作为普通 Workflow 分支处理：

- active route/current position 无法唯一对应；
- task/result identity 冲突；
- Workstream state 与记录矛盾；
- artifact lineage 无法解释；
- route file 缺失/损坏；
- deterministic evaluator 自身错误。

此时返回 `BLOCKED`，由 Manager 判断是否进入 recovery。

## 6. STOP_SCOPE

以下任一成立时返回 `STOP_SCOPE`：

- 当前 node 是用户明确终点；
- 当前 node 是 active route 当前 revision 的终点；
- 下一节点位于用户解析范围之外。

不得因为存在“自然下一步”而越过用户终点。

## 7. 记录策略

fast-path evaluation 不为每个节点创建新的独立大文件。

最小审计证据并入普通 task closure/terminal event 或 R4 commit receipt：

```yaml
route_progression:
  mode: FAST_ADVANCE | WORKFLOW_REENTRY | STOP_SCOPE | BLOCKED
  from_node:
  to_node:
  evaluator_version:
  reason_codes: []
```

只有 debug/recovery 时才需要保存完整 evaluator diagnostics。

## 8. 确定性 evaluator

拟议 capability：

```text
route_fast_path_evaluator
```

输入：

- active route 当前 revision；
- current node；
- task/result terminal summary；
- gate status；
- artifact update summary；
- decision/confirmation summary；
- Workstream current position；
- resolved route scope；
- compact Workflow runtime node spec。

不得读取完整业务日志或自行作科学判断。

## 9. 与 Workflow 的关系

fast path 不是“绕过 Workflow 规则”。

它执行的是 Workflow 已经投影到 active route + compact runtime spec 中的**既定正常路径**。

Workflow 保持：

- route fragment 语义所有权；
- 条件节点语义；
- route-changing evidence 的解释权；
- exceptional execution decision。

## 10. 当前启用状态

在以下条件满足前：

```text
ACTIVE_ROUTE_FAST_PATH = DISABLED
```

激活要求：

- evaluator Tool 实现并 ACTIVE；
- route/current-position fixtures；
- REQUIRED/CONDITIONAL 边界测试；
- user-scope stop 测试；
- decision/failure/recovery 负向测试；
- 与 R4 record committer 的集成测试；
- 1.1 → 1.2 benchmark 验证。
