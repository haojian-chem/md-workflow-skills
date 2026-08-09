# MD Workflow 确定性工具协议

## 1. 定位

Tool 是可重复执行的确定性程序，不是第五个运行时决策层，也不是 Agent。

```text
Manager / Workflow / Operation / Validator
→ 决定何时调用以及如何使用结果
→ Tool 执行确定性校验、转换、事务或渲染
```

Tool 不得：

- 选择项目 Focus、Workstream、路线起点或终点；
- 决定 Workflow 下一 substep；
- 作科学质量判断；
- 向用户提问；
- 自行创建或调用 Agent；
- 修改超出注册权限的文件。

## 2. 工具归属

共享工具统一位于 `05_tools/`，权威注册表为：

```text
05_tools/tool_registry.yaml
```

共享工具只能由：

```text
00_authoring/md-workflow-tool-authoring/SKILL.md
```

生成、修改、测试、注册、升级、废弃或迁移。业务 Skill 可提出 `tool_request`，但不得在运行中的业务 task 内临时修改共享 Tool。

## 3. 两个根目录

Tool 调用必须区分：

```text
Skill architecture root
MD project root
```

- Tool 实现、registry、`03_contracts/` 位于 Skill architecture root；
- runtime state、records、业务文件和项目 cache 位于 MD project root；
- schema Tool 必须显式接收或解析 `<skill_root>/03_contracts`；
- 不得默认真实 MD 项目根目录存在 contracts。

普通 FAST 示例：

```bash
python <skill_root>/05_tools/runtime_schema_validator/validate.py \
  --project-root <md_project_root> \
  --contracts-dir <skill_root>/03_contracts \
  --mode FAST \
  --changed <candidate_or_runtime_paths>
```

## 4. Tool 开发触发条件

满足任一情况可提出工具开发：

- 同一确定性逻辑在多个步骤重复；
- LLM 执行明显慢于脚本；
- 自然语言执行容易不一致；
- 需要缓存、批量或增量检查；
- 需要原子写入或回滚；
- 需要可重复测试与 benchmark。

工具请求至少包含：

```yaml
tool_request:
  capability:
  reason:
  callers: []
  required_inputs: []
  expected_outputs: []
  read_paths: []
  write_paths: []
  side_effects: []
```

## 5. 生命周期

```text
REQUESTED
→ DESIGNED
→ IMPLEMENTED
→ TESTED
→ ACTIVE
→ DEPRECATED
→ RETIRED
```

只有 `ACTIVE` 且适用测试通过的工具可作为默认运行路径。

工具修改必须同步版本、contract、fixtures/benchmark、registry、兼容性/迁移信息和验证证据，不覆盖旧审计信息。

## 6. Hard-gate capability 预检

任何 Skill 设置不可跳过的 hard gate 前，必须确认至少有一种可运行实现：

```text
ACTIVE Tool
或
权威协议明确规定的内建确定性路径
```

规则：

- `DESIGNED | IMPLEMENTED | TESTED` 但未 ACTIVE 不构成默认实现；
- capability 预检必须在部分权威写入前完成；
- hard gate 无实现时应直接标识 capability blocker，不得到真实任务中才发现自锁；
- 新 hard gate 必须有能力缺失负向 fixture；
- 内建路径必须固定输入、顺序、失败和权限，运行时 LLM 不得临时发明。

阻断原因分层：

```text
Current blocker
Pending after current barrier
```

只把当前 barrier 的直接失败原因列为 Current blocker。

## 7. Runtime schema validation profiles

当前 schema validator：

```text
runtime_schema_validator 0.1.0 — ACTIVE
```

### 7.1 INIT_CANDIDATE_VALIDATION

NEW 项目初始化使用一个**受限 FAST invocation profile**，不是新增 CLI mode：

```bash
python <skill_root>/05_tools/runtime_schema_validator/validate.py \
  --project-root <md_project_root> \
  --contracts-dir <skill_root>/03_contracts \
  --mode FAST \
  --changed <candidate_project_state> <candidate_workstream_state> \
  --logical-map <candidate_project_state>=00_project_state/project_state.yaml \
  --logical-map <candidate_workstream_state>=00_project_state/workstreams/<workstream_id>.yaml
```

范围固定为：

- 两个初始化状态候选；
- 它们各自 schema；
- 它们的直接引用；
- candidate logical-path overlay。

不得为了初始化扩大到：

- PDB/mmCIF/其他业务内容；
- 全项目 route/task/artifact/decision/submission/event 扫描；
- 未列入 changed 的 runtime objects。

已有旧业务/管理产物是否意味着 `NEEDS_RECOVERY` 由 Manager entry probe 判断，不由 INIT candidate validation 代替。

验证证据：

```text
04_evals/initialization_candidate_validation/VALIDATION.md
```

### 7.2 FAST

普通前台 task 使用 FAST：

- 只校验本次新增/修改的 runtime instances；
- 只检查这些对象的直接交叉引用；
- 不扫描全部项目历史；
- schema hash/cache 命中时不重复 meta-validation；
- 一次 Tool 调用批量处理 changed paths；
- 返回精简机器可读摘要。

普通 task 禁止触发 FULL。

R4 ACTIVE 后，普通前台 task 的 FAST 默认由 `runtime_record_committer` 内部执行一次，Manager 不再在闭环外重复调用。

### 7.3 FULL

FULL 只用于需要项目级一致性审计的节点：

- schema/contract 发生变化；
- 项目恢复前后；
- Project root 或 Skill root 变化；
- 创建重要 Workstream 分支且协议明确要求；
- 重大 artifact 谱系替换/失效；
- 首个高恢复价值外部长任务提交前（若相应协议要求）；
- Workstream 完成、归档或放弃前；
- 用户明确要求完整审计。

**NEW 初始化不再属于 FULL 触发条件。**

FULL 可执行：

- schema meta-validation；
- 全部适用 runtime instance 校验；
- 项目级交叉引用扫描；
- 索引、route、task、artifact、decision、submission、event 一致性检查。

## 8. Schema cache

cache key 基于适用 schema 文件内容 hash，不以时间戳代替。

```text
schema hash 未变化且 cache 有效
→ 复用 schema meta-validation
```

cache 是可删除/可重建的非权威数据，不替代 schema 或项目状态；默认写入注册的 project cache 路径，不污染 Skill architecture root。

## 9. 失败与回退

- Tool `FAIL`：按结构化错误处理，不得由 LLM 宣称通过；
- Tool 不可用/版本不兼容：仅可使用已批准的确定性备用路径，否则形成 capability blocker；
- 不得用 LLM 逐字段模拟 schema/project-level validation；
- 不得自动修改 schema、降低 gate 或忽略引用错误；
- INIT candidate validation 失败不得通过改跑 FULL 来绕过；
- 后续 route/Workflow 问题不得冒充当前 Tool blocker。

## 10. 权限与写入型 Tool

只读 Tool 不得修改项目权威文件。

写入型 Tool 必须采用：

```text
candidate
→ deterministic validation
→ backup/rollback preparation
→ controlled commit
→ structured receipt
```

涉及科研业务文件的 Tool 必须由对应 Operation/Validator 语义层授权。Manager 可直接调用只处理管理状态、schema、引用、事务、route fast-path evaluation 和用户摘要的已批准 Tool。
