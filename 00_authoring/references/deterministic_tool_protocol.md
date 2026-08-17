# MD Workflow 确定性 Tool 协议

Status: CURRENT

## 1. 定位

Tool 是可重复执行的确定性能力组件，不是科学决策层，也不是 Agent 理解任务的 parser gate。

```text
Task Execution Agent
→ current main Skill
→ 必要时调用 deterministic Tool
→ Tool 返回确定性结果
→ Agent 继续当前任务
```

适合 Tool 的典型场景：精确 parsing、structured extraction、hash、mapping、批量处理、稳定文件变换、格式校验、可重复数值计算和安全受控写入。

## 2. Tool 不得承担

Tool 不得：

- 解释或扩大用户科研目标；
- 决定 Task 范围或其它 Skill 行为；
- 作开放式科学判断；
- 向用户提问或自行创建 Agent；
- 为普通 Lightweight 执行构造 Workstream、route、event、runtime task/result、artifact state 或 transaction closure；
- 修改未授权路径。

## 3. Current location

Current shared Tool root：

```text
tools/
```

Registry：

```text
tools/tool_registry.yaml
```

共享 Tool authoring：

`00_authoring/md-workflow-tool-authoring/SKILL.md`

测试/fixtures/benchmark：

`evals/`

Skill 独有且不会跨 Skill 复用的小 helper 可以留在当前 Skill 的 `scripts/`。

## 4. Legacy tools

依赖旧 `task.yaml`、Workstream、route/event/state/transaction 或 old runtime contracts 的历史工具统一位于：

```text
legacy/tools/
```

其历史 contracts/runtime 位于：

```text
legacy/contracts/
legacy/runtime/
```

Legacy Tool 不得因为历史 registry 曾标记 `ACTIVE` 就作为 current implementation。重新进入 `tools/` 前必须完成：

```text
current interface adaptation
→ current tests / validation
→ explicit reactivation
→ current registry entry
```

## 5. Tool development trigger

可以考虑共享 Tool：

- 同一确定性逻辑跨 Skill 重复；
- 程序执行明显比自然语言操作更稳定；
- parsing / hashing / mapping / deterministic transform 容易不一致；
- 需要格式校验、批量、cache 或安全原子写入；
- 需要独立测试/benchmark。

不足以成为 Tool 的理由：

- 包装一次简单读取；
- 让 Agent 必须经过统一 parser；
- 为了减少几行 Skill guidance；
- 为了恢复 Legacy runtime orchestration。

## 6. Required / preferred / optional

Skill 引用 deterministic capability 时应区分：

```text
required capability
preferred implementation
optional helper
```

只有科学方法、数据格式、安全约束或已冻结接口真正要求某个具体实现时，才把特定 Tool 写成不可替代。

## 7. Interface principle

Current Tool 优先接口：

```text
明确业务文件 / 目录
+ 必要参数
+ 明确输出位置 / 策略
→ deterministic action
→ 明确结果 / report
```

避免：

```text
runtime task object
→ Tool 解包全局项目状态
→ Tool 决定下一阶段
→ Tool 构造 route/event/state closure
```

Tool 输出是否成为正式科研结果由调用 main Skill 决定。

## 8. Roots and permissions

必须区分：

```text
Skill repository root
MD project root
```

Tool 不得假定两者相同，也不得为了找输入无限扫描项目。

写入型 Tool 必须明确输入、输出位置、覆盖策略、冲突行为、部分失败 cleanup 和执行前后 validation。

默认不直接维护 `task_index.md`、Task Sheet 或 `project_result_index.md`；Stage-specific 明确授权的索引例外由对应 Stage Skill 定义。

## 9. Lifecycle

```text
REQUESTED
→ DESIGNED
→ IMPLEMENTED
→ TESTED
→ ACTIVE
→ DEPRECATED
→ RETIRED
```

只有 `ACTIVE` 且 current-interface-compatible 的 Tool 才能作为默认 production implementation。

## 10. Hard gate / failure

某项确定性能力成为 hard gate 前，必须存在已验证实现或明确安全的等价备用路径。

Tool 失败时不得伪造成功、降低科学要求或临时恢复 Legacy runtime。没有等价路径且 capability 必需时，当前任务保持未完成。

## 11. Self-check

- [ ] Tool 化确有确定性价值；
- [ ] Tool 不承担开放式科学判断；
- [ ] Tool 不成为无必要 parser gate；
- [ ] required / preferred / optional 定位清楚；
- [ ] 明确输入、输出、权限和失败行为；
- [ ] current Tool 位于 `tools/`；
- [ ] tests/evidence 位于 `evals/`；
- [ ] Legacy implementation 仍留在 `legacy/`，未伪装成 current。
