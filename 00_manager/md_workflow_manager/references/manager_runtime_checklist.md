# Manager 运行自检清单

按当前动作选择适用项，不得为完成清单而加载无关历史或科学文件。

## 1. 入口与初始化

- [ ] 两个根目录已明确且有效；
- [ ] 入口状态有直接证据；
- [ ] 有明显旧业务产物但无可信状态时未判为 NEW；
- [ ] 初始化 hard-gate capability 已在部分写入前完成预检；
- [ ] `FULL_RUNTIME_VALIDATION` 有 ACTIVE Tool 或权威内建确定性路径；
- [ ] `state_transaction` 未 ACTIVE 时使用已批准的内建提交路径，而非阻塞 NEW；
- [ ] NEW 已自动初始化；
- [ ] 初始化后持久 project state 为 RESUMABLE；
- [ ] `PROJECT_INITIALIZED` 只在候选状态校验和提交成功后记录；
- [ ] 初始化没有创建 route、业务 task 或调用 Workflow。

## 2. 路线范围与规划

- [ ] 路线范围解析独立于初始化；
- [ ] 模糊请求没有被补成默认终点；
- [ ] 初始化完成前的路线歧义只列为 pending，不列为当前 blocker；
- [ ] `ROUTE_SCOPE_RESOLVED` 前未创建 route；
- [ ] route fragment 来自对应 Workflow；
- [ ] 未连接 Workflow 只在路线规划到达边界后形成 PARTIAL/BLOCKED；
- [ ] 未连接 Workflow 未被追溯为初始化失败原因；
- [ ] 相邻 fragment 的 artifact 接口已核验；
- [ ] route 仅在实际变化时 revision。

## 3. 执行与子 Agent

- [ ] active route 存在、适用且包含当前位置；
- [ ] 当前 task 来自 Workflow execution decision；
- [ ] 未根据阶段名称编造 Workflow 内部步骤；
- [ ] 同时最多一个前台临时子 Agent；
- [ ] 没有嵌套委派；
- [ ] Operation 与 Validator 结果保持分离；
- [ ] 子 Agent 未写 `00_project_state/**` 或 `00_project_records/**`。

## 4. 校验与提交

- [ ] 普通 task 只对 changed paths 执行一次 FAST；
- [ ] 普通 task 未触发 FULL；
- [ ] schema hash/cache 命中时未重复 meta-validation；
- [ ] 未用 LLM 模拟 FULL schema 或项目级引用校验；
- [ ] 只调用 registry 中状态和版本适用的 Tool；
- [ ] `runtime_schema_validator` 当前为 ACTIVE 且调用参数区分 Skill root 与 Project root；
- [ ] Tool FAIL/ERROR 时未提交候选终态或宣称通过；
- [ ] 候选对象通过适用校验后才提交；
- [ ] 不可变记录未被覆盖。

## 5. 状态、记录与产物

- [ ] 普通 task 未机械写 TASK_PREPARED/TASK_STARTED；
- [ ] 无变化的 project state、route、session 和 snapshot 未重写；
- [ ] 必要 artifact/decision/submission 已登记；
- [ ] artifact validation status 有 Validator 证据；
- [ ] 一条终态 task event 和目标 Workstream state 已落盘；
- [ ] 外部任务未因 tmux/job 消失直接判为完成。

## 6. 用户交互与结束

- [ ] Focus 唯一；歧义时已确认；
- [ ] `Current blocker` 只包含当前 barrier 的直接原因；
- [ ] 后续路线、Workflow 覆盖或输入问题列在 `Pending after current barrier`；
- [ ] blocking decision 已向用户展示；
- [ ] task closure summary 已在下一前台 task 前显示；
- [ ] Operation 完成未表述为科学质量验证通过；
- [ ] 失败未自动重试、降低 gate 或跳过 Validator；
- [ ] 本轮结束前无活动前台子 Agent；
- [ ] 固定状态摘要字段完整。