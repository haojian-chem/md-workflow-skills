# Workstream 路线规划协议

本文件定义 Manager 如何使用多个 Workflow 为一个 Focus Workstream 生成、拼接和修订预计路线。

## 1. 两类 Workflow 接口

Workflow 是 Skill，不是 Agent。Manager 对 Workflow 有两种独立调用目的。

### 1.1 规划接口

用于首次规划、范围调整、创建分支、失败后的替代路线和新证据触发的重规划。

Workflow 返回：

`03_contracts/workflow_route_fragment.schema.yaml`

该返回描述本 Workflow 范围内的预计路线片段，不授权执行任何 task unit。

### 1.2 执行接口

用于实际推进当前 Workstream。每完成一个 task unit、人工决定、外部任务核验或恢复动作后再次调用。

Workflow 返回：

`03_contracts/workflow_decision.schema.yaml`

该返回每次只包含一个当前决定：`EXECUTE | SKIP | PAUSE | COMPLETE | BLOCKED`。

## 2. 职责分配

Manager 负责：

- 解析本轮规划起点、终点和停止条件；
- 根据 stage registry 确定涉及的 Workflow；
- 逐个请求 Workflow route fragment；
- 校验相邻 fragment 的出口 artifact 与入口要求；
- 拼接完整 Workstream route；
- 创建不可变 route record 和 revision；
- 在执行 decision 与 active route 不一致时决定重规划、暂停或恢复。

Workflow 负责：

- 定义本阶段 substep 顺序；
- 基于 Workstream 局部状态生成本阶段 route fragment；
- 标记 REQUIRED 与 CONDITIONAL 步骤；
- 声明入口要求、出口 artifact、gate、假设和 blocker；
- 在执行时基于最新证据返回一个实时 decision。

Manager 不得根据阶段名称自行编造 Workflow 内部步骤。Workflow 不得拼接其他 Workflow 或写 route record。

## 3. 规划触发条件

以下情况必须生成新路线或 route revision：

- 创建首个 Workstream；
- 创建参数、对照、重复或测试 Workstream；
- 用户首次指定或修改起点、终点；
- Validator 结果改变条件步骤；
- 用户决定改变后续路径；
- artifact 被 INVALIDATED 或 SUPERSEDED；
- task 失败并采用替代方案；
- Workflow 条件或可用性变化；
- 当前 decision 与 active route 因新证据不再一致。

仅当前位置前进、且预计后续步骤没有变化时，不创建 revision。

## 4. 规划范围

Manager 将范围规范化为：

```yaml
planning_scope:
  start:
    workflow_name:
    substep:
    artifact_set_id:
    point_kind: CURRENT | WORKFLOW_ENTRY | WORKFLOW_EXIT | SPECIFIC_SUBSTEP | ARTIFACT
  end:
    workflow_name:
    substep:
    artifact_set_id:
    point_kind: WORKFLOW_EXIT | SPECIFIC_SUBSTEP | ARTIFACT | WORKSTREAM_GOAL | PROJECT_END
```

可使用的常见终点语义：

- 下一 task；
- 下一 gate；
- 指定 substep；
- 当前 Workflow 结束；
- 指定 Workflow 结束；
- Workstream 目标；
- 项目终点。

用户请求无法唯一解析成终点时，Manager 才向用户确认。

## 5. 确定 Workflow 范围

Manager 读取 `stage_registry.yaml`：

1. 定位起点和终点所在 Workflow；
2. 按 stage order 得到需要经过的 Workflow 列表；
3. 检查每个 Workflow 的 connection status 和 planning interface；
4. 对已连接 Workflow 请求 fragment；
5. 对尚未连接 Workflow 在边界处生成明确 blocker。

未连接 Workflow 的内部步骤不得由 Manager 或前一个 Workflow推测。

## 6. 请求 route fragment

Manager 向每个 Workflow 仅提供当前规划所需的最小上下文：

```yaml
workstream_id:
workflow_name:
start_substep:
end_substep:
current_position:
available_artifacts: []
resolved_decisions: []
user_constraints: []
known_conditions: []
target_goal:
skill_availability: []
```

Workflow 返回 fragment，至少包含：

- fragment ID；
- Workstream 与 Workflow 标识；
- COMPLETE、PARTIAL 或 BLOCKED；
- 本阶段范围；
- REQUIRED/CONDITIONAL steps；
- entry requirements；
- exit artifacts；
- assumptions；
- unresolved items；
- blockers。

## 7. 条件步骤

证据不足时，条件步骤必须保留在 fragment 中：

```yaml
necessity: CONDITIONAL
condition: 只有完整性报告要求补全时执行
```

不得在规划阶段：

- 无证据删除条件步骤；
- 无证据宣称条件步骤必定执行；
- 由 Manager 代替 Validator 做科学判断。

执行阶段由当前 Workflow 根据最新报告返回 `EXECUTE` 或 `SKIP`。

## 8. Fragment 拼接

Manager 按顺序检查：

```text
fragment A exit artifacts
是否满足
fragment B entry requirements
```

兼容时，将步骤重新编号后写入 route record。

不兼容时：

- route 标记为 PARTIAL 或 BLOCKED；
- 记录 `known_blockers` 和阻断 Workflow 边界；
- 不自动增加未定义的转换步骤；
- 不把不兼容 artifact 标为有效输入。

## 9. 完整、部分与阻断路线

### COMPLETE

所有涉及 Workflow 已连接，fragment 可拼接，且没有已知 blocker。

### PARTIAL

已规划部分有效，但后续 Workflow 尚未连接、存在未决条件，或用户只要求到某个边界。

### BLOCKED

无法形成任何安全可执行的预计路线，或当前范围在入口即被阻断。

PARTIAL 路线可以执行其已规划且未阻断的前段；到 blocker 前必须停止。

## 10. 创建 route record

Manager 将 fragment 拼接结果写入：

`03_contracts/route_record.schema.yaml`

route record 必须保存：

- planning status；
- 起点和终点；
- source fragment provenance；
- REQUIRED/CONDITIONAL steps；
- assumptions；
- conditional steps；
- known blockers；
- stop conditions；
- supersedes 关系。

route 文件创建后不可覆盖。Workstream state 只更新 `active_route_id`。

## 11. 执行时使用路线

预计路线是动态投影，不是硬编码批处理队列。

每个 task unit 前，Manager：

1. 读取当前 Workstream state 和 active route；
2. 调用当前 Workflow 的 execution interface；
3. 校验 workflow decision；
4. 比较 decision 与 active route 的预计下一步。

### 决定与路线一致

继续创建一个 task unit。

### 因新证据产生合理差异

先创建 route revision，再执行新 decision。

### 差异无法解释

返回 `PAUSE | BLOCKED`，或将 Workstream 标记为 `NEEDS_RECOVERY`。不得先执行后补改路线。

## 12. Workflow 切换

当前 Workflow 返回阶段 `COMPLETE` 后，Manager：

1. 核验阶段完成 gate 和出口 artifact；
2. 检查用户终点是否达到；
3. 查询 stage registry；
4. 自动进入下一个已连接 Workflow；
5. 更新 Workstream current position；
6. 调用下一 Workflow 的 execution interface。

以下情况暂停：

- 用户终点达到；
- 下一 Workflow 未连接；
- 出口 artifact 不满足下一阶段入口；
- 存在 blocking decision；
- 应创建新 Workstream；
- 高风险或不可逆操作需要确认。

## 13. 加载策略

### 路线规划

按阶段顺序串行读取涉及的 Workflow。获取 fragment 后释放无关局部内容，不一次性载入所有 Workflow references。

### 实际执行

只加载当前 Workflow、当前 task unit 的 Operation/Validator contract 和目标 Workstream 所需记录。

### 阶段切换

仅在当前阶段完成后加载下一 Workflow。

## 14. 用户展示

完整路线只在以下情况展示：

- 首次创建；
- route revision 实际改变步骤、条件、终点或 blocker。

其他情况下只显示：

- Focus Workstream；
- 当前位置；
- 预计下一 task；
- route planning status；
- 当前 blocker 或决策。

## 15. 自检

- [ ] 起点、终点和停止条件已解析；
- [ ] 每个 Workflow 的 fragment 来自该 Workflow 自身规则；
- [ ] 条件步骤保留条件和证据要求；
- [ ] 相邻 fragment 的 artifact 接口已核验；
- [ ] 未连接 Workflow 在边界明确阻断；
- [ ] route record 保存 source fragments；
- [ ] 执行 decision 与路线不一致时先修订或暂停；
- [ ] Manager 未自行编写 Workflow 内部步骤；
- [ ] Workflow 未跨阶段拼接路线。
