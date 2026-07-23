# Workstream 路线规划协议

本文件定义 Manager 如何在项目初始化完成后，为一个 Focus Workstream 解析路线范围、请求 Workflow route fragment、拼接 route 并进行修订。

## 0. 前置边界

路线规划协议不负责项目入口判定或项目初始化。

进入本协议前必须满足：

- NEW 项目已经完成 `PROJECT_INITIALIZED`；或
- 项目是可信的 RESUMABLE；
- Focus Workstream 已确定；
- 项目不处于未完成的项目级恢复。

`NEW`、首个 Workstream 创建或项目初始化本身不构成路线规划触发条件，也不得自动创建首条 route。

处理顺序必须是：

```text
ENTRY_STATE_EVALUATED
→ PROJECT_INITIALIZED（仅 NEW）
→ ROUTE_SCOPE_RESOLUTION
→ ROUTE_SCOPE_RESOLVED
→ ROUTE_PLANNING
→ ROUTE_CREATED
→ EXECUTION
```

在 `ROUTE_SCOPE_RESOLVED` 前，不得请求 Workflow fragment、创建 route record 或业务 task。

## 1. 两类 Workflow 接口

Workflow 是 Skill，不是 Agent。Manager 对 Workflow 有两种独立调用目的。

### 1.1 规划接口

用于首次路线规划、范围调整、创建分支后的路线规划、失败后的替代路线和新证据触发的重规划。

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

- 在初始化之后独立解析本轮路线起点、终点和停止条件；
- 对模糊终点创建用户 decision，而不是自行补全；
- 根据 stage registry 确定涉及的 Workflow；
- 逐个请求 Workflow route fragment；
- 校验相邻 fragment 的出口 artifact 与入口要求；
- 拼接完整 Workstream route；
- 创建不可变 route record 和 revision；
- 在 execution decision 与 active route 不一致时决定重规划、暂停或恢复。

Workflow 负责：

- 定义本阶段 substep 顺序；
- 基于 Workstream 局部状态生成本阶段 route fragment；
- 标记 REQUIRED 与 CONDITIONAL 步骤；
- 声明入口要求、出口 artifact、gate、假设和 blocker；
- 在执行时基于最新证据返回一个实时 decision。

Manager 不得根据阶段名称自行编造 Workflow 内部步骤。Workflow 不得拼接其他 Workflow 或写 route record。

## 3. 独立的路线范围解析事件

路线范围解析发生在项目入口处理之后、PLAN 之前。

### 3.1 可以直接解析的来源

只有下列来源之一明确给出终点时，Manager 才能直接解析：

- 用户明确指定 substep、gate、Workflow、artifact、Workstream 目标或项目终点；
- 已解决 decision 明确记录终点；
- 用户明确要求继续一个已有且仍有效的 active route；
- 既有 Workstream 目标已明确记录，且用户明确要求按该目标继续。

例如：

```text
只完成 source_recognition
```

可解析为 `structure_preparation_workflow/source_recognition` 终点。

### 3.2 必须确认的模糊范围

以下表述本身不足以确定终点：

- “开始处理这个结构”；
- “跑一下流程”；
- “测试一下这个项目”；
- “继续做”，但不存在可用 active route；
- 只描述对象、问题或期望效果，没有说明推进到哪里。

Manager 不得默认选取：

- 下一 task；
- 下一 gate；
- 当前 Workflow 结束；
- Workstream 目标；
- 项目终点。

终点不明确时必须：

1. 创建 blocking decision record；
2. 追加 `ROUTE_SCOPE_REQUESTED`；
3. 将 Workstream 置为 `WAITING`，hold reason 为 `USER_DECISION`；
4. 向用户确认终点；
5. 不请求 route fragment，不创建 route 或 task。

用户决定落盘后追加 `ROUTE_SCOPE_RESOLVED`。该事件只表示范围已明确，不等于 route 已创建。

## 4. 规划触发条件

只有路线范围已经解析后，以下情况才触发新 route 或 revision：

- 首次生成 Workstream 路线；
- 新参数、对照、重复或测试 Workstream 的范围已解析；
- 用户修改起点、终点或停止条件；
- Validator 结果改变条件步骤；
- 用户决定改变后续路径；
- artifact 被 INVALIDATED 或 SUPERSEDED；
- task 失败并采用替代方案；
- Workflow 条件或可用性变化；
- 当前 decision 与 active route 因新证据不再一致。

仅当前位置前进、且预计后续步骤没有变化时，不创建 revision。

Workstream 创建、NEW 初始化或 Focus 选择本身不自动触发 route 创建。

## 5. 规划范围

Manager 将已经解析的范围规范化为：

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
  stop_conditions: []
  resolution_source: USER_REQUEST | RESOLVED_DECISION | ACTIVE_ROUTE | RECORDED_WORKSTREAM_GOAL
```

可使用的终点语义：

- 指定 substep；
- 指定 gate；
- 指定 artifact；
- 当前或指定 Workflow 结束；
- Workstream 目标；
- 项目终点。

“下一 task”或“下一 gate”只能在用户明确这样指定时作为终点，不能作为 Manager 的默认值。

## 6. 确定 Workflow 范围

Manager 读取 `stage_registry.yaml`：

1. 定位起点和终点所在 Workflow；
2. 按 stage order 得到需要经过的 Workflow 列表；
3. 检查每个 Workflow 的 connection status 和 planning interface；
4. 对已连接 Workflow 请求 fragment；
5. 对尚未连接 Workflow 在边界处生成明确 blocker。

未连接 Workflow 的内部步骤不得由 Manager 或前一个 Workflow 推测。

## 7. 请求 route fragment

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

## 8. 条件步骤

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

## 9. Fragment 拼接

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

## 10. 完整、部分与阻断路线

### COMPLETE

所有涉及 Workflow 已连接，fragment 可拼接，且没有已知 blocker。

### PARTIAL

已规划部分有效，但后续 Workflow 尚未连接、存在未决条件，或用户只要求到某个边界。

### BLOCKED

无法形成任何安全可执行的预计路线，或当前范围在入口即被阻断。

PARTIAL 路线可以执行其已规划且未阻断的前段；到 blocker 前必须停止。

## 11. 创建 route record

Manager 将 fragment 拼接结果写入：

`03_contracts/route_record.schema.yaml`

route record 必须保存：

- planning status；
- 已解析的起点、终点和停止条件；
- scope resolution source；
- source fragment provenance；
- REQUIRED/CONDITIONAL steps；
- assumptions；
- conditional steps；
- known blockers；
- supersedes 关系。

route 文件创建后不可覆盖。Workstream state 只更新 `active_route_id`。

`ROUTE_SCOPE_RESOLVED` 与 `ROUTE_CREATED` 是两个不同事件；前者不得代替后者。

## 12. 执行时使用路线

预计路线是动态投影，不是硬编码批处理队列。

每个 task unit 前，Manager：

1. 确认项目初始化 barrier 已通过；
2. 确认路线范围已解析；
3. 读取当前 Workstream state 和 active route；
4. 确认 `active_route_id` 非空且路线适用；
5. 调用当前 Workflow 的 execution interface；
6. 校验 workflow decision；
7. 比较 decision 与 active route 的预计下一步。

### 决定与路线一致

继续创建一个 task unit。

### 因新证据产生合理差异

先创建 route revision，再执行新 decision。

### 差异无法解释

返回 `PAUSE | BLOCKED`，或将 Workstream 标记为 `NEEDS_RECOVERY`。不得先执行后补改路线。

## 13. Workflow 切换

当前 Workflow 返回阶段 `COMPLETE` 后，Manager：

1. 核验阶段完成 gate 和出口 artifact；
2. 检查用户终点是否达到；
3. 查询 stage registry；
4. 自动进入 active route 中的下一个已连接 Workflow；
5. 更新 Workstream current position；
6. 调用下一 Workflow 的 execution interface。

以下情况暂停：

- 用户终点达到；
- 下一 Workflow 未连接；
- 出口 artifact 不满足下一阶段入口；
- 存在 blocking decision；
- 应创建新 Workstream；
- 高风险或不可逆操作需要确认。

不得越过 active route 已解析的终点。

## 14. 加载策略

### 路线范围解析

只读取用户请求、Focus Workstream 目标、active route 摘要、相关 resolved decisions 和 stage registry；不加载 Workflow 业务细节。

### 路线规划

按阶段顺序逐个读取涉及的 Workflow。获取 fragment 后释放无关局部内容，不一次性载入所有 Workflow references。

### 实际执行

只加载当前 Workflow、当前 task unit 的 Operation/Validator contract 和目标 Workstream 所需记录。

### 阶段切换

仅在当前阶段完成后加载下一 Workflow。

## 15. 用户展示

范围未解析时显示：

- Focus Workstream；
- Route scope: unresolved；
- 当前 blocking decision；
- Expected next task: none。

完整路线只在以下情况展示：

- 首次创建；
- route revision 实际改变步骤、条件、终点或 blocker。

其他情况下只显示：

- Focus Workstream；
- 当前位置；
- 预计下一 task；
- route planning status；
- 当前 blocker 或决策。

## 16. 自检

- [ ] NEW 初始化与路线范围解析没有合并；
- [ ] `PROJECT_INITIALIZED` 前未进入本协议；
- [ ] 路线范围来自明确用户请求、resolved decision、有效 active route 或明确记录的 Workstream 目标；
- [ ] 模糊请求已创建 `ROUTE_SCOPE_REQUESTED`，未自行选择默认终点；
- [ ] `ROUTE_SCOPE_RESOLVED` 前未请求 fragment 或创建 route；
- [ ] Workstream 创建本身未自动生成 route；
- [ ] 每个 Workflow 的 fragment 来自该 Workflow 自身规则；
- [ ] 条件步骤保留条件和证据要求；
- [ ] 相邻 fragment 的 artifact 接口已核验；
- [ ] 未连接 Workflow 在边界明确阻断；
- [ ] route record 保存 source fragments 和 scope resolution source；
- [ ] active route 不存在时未创建业务 task；
- [ ] execution decision 与路线不一致时先修订或暂停；
- [ ] Manager 未自行编写 Workflow 内部步骤；
- [ ] Workflow 未跨阶段拼接路线。
