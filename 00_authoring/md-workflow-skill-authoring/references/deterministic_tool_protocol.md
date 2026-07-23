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

共享工具统一放置于：

```text
05_tools/
```

权威注册表：

```text
05_tools/tool_registry.yaml
```

共享工具只能由：

```text
00_authoring/md-workflow-tool-authoring/SKILL.md
```

生成、修改、测试、注册、升级、废弃或迁移。

业务 Skill 可以提出 `tool_request`，但不得在运行中的业务 task 内临时修改共享工具。

## 3. 两个根目录

Tool 调用必须区分：

```text
Skill architecture root
MD project root
```

- Tool 实现、registry 和 `03_contracts/` 位于 Skill architecture root；
- runtime state、records、业务文件和项目 cache 位于 MD project root；
- 不得默认真实 MD 项目根目录内存在 `03_contracts/`；
- schema Tool 必须显式接收或解析 `<skill_root>/03_contracts`；
- 调用方必须记录实际使用的 Tool 名称、版本、project root 和 contracts path。

示例：

```bash
python <skill_root>/05_tools/runtime_schema_validator/validate.py \
  --project-root <md_project_root> \
  --contracts-dir <skill_root>/03_contracts \
  --mode FAST \
  --changed <candidate_or_runtime_paths>
```

## 4. 生成工具的触发条件

满足以下任一条件时，可以提出工具开发请求：

- 同一确定性逻辑在多个步骤重复；
- LLM 执行明显慢于脚本；
- 自然语言执行容易产生不一致；
- 需要缓存、批量处理或增量检查；
- 需要稳定的原子写入或回滚；
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

## 5. 工具生命周期

```text
REQUESTED
→ DESIGNED
→ IMPLEMENTED
→ TESTED
→ ACTIVE
→ DEPRECATED
→ RETIRED
```

只有注册状态为 `ACTIVE` 且适用测试通过的工具可作为默认运行路径。

工具修改时必须：

1. 更新 `tool.yaml` 版本；
2. 保持或明确升级输入输出 contract；
3. 更新 fixtures 和 benchmark；
4. 更新 `tool_registry.yaml`；
5. 说明兼容性、迁移和回退方式；
6. 不覆盖旧版本的审计信息。

## 6. 强制 gate capability 预检

任何 Skill 在把某项能力设为不可跳过的 hard gate 前，必须确认至少存在一种可运行实现：

```text
ACTIVE Tool
或
权威协议明确规定的内建确定性执行路径
```

规则：

- `DESIGNED`、`IMPLEMENTED` 或 `TESTED` 但未 `ACTIVE` 的 Tool 不构成默认可运行实现；
- 只有接口名称、未来计划或未实现目录不构成能力；
- capability 预检应在产生部分状态写入前完成；
- 若 hard gate 没有可运行实现，当前 Manager/Skill 版本应标为 `NOT_RUNNABLE`，不得等到真实项目 NEW 初始化时才暴露自锁；
- 新增 hard gate 时必须增加“能力缺失”负向 fixture；
- 内建确定性路径必须在权威协议中写明输入、顺序、失败处理和权限，不能由运行时 LLM 临时发明。

阻断因果必须按当前 barrier 分层：

```text
Current blocker
Pending after current barrier
```

只把导致当前 barrier 无法通过的事实列为 `Current blocker`。路线范围歧义、未连接 Workflow 或后续科学输入问题，在其处理阶段到达前只能列为 `Pending after current barrier`，不得冒充当前初始化失败原因。

## 7. 运行时 schema 校验模式

### FAST

普通前台 task 默认使用 FAST：

- 只校验本次新增或修改的 runtime instances；
- 只检查这些对象的直接交叉引用；
- 不扫描全部 Workstream、route、artifact、decision 或 event 历史；
- schema 定义未变化且 hash cache 命中时，不重复执行 schema meta-validation；
- 一次工具调用批量处理本次 changed paths；
- 返回精简机器可读摘要。

普通 task 禁止触发全量 contract validation。

### FULL

仅在以下节点使用 FULL：

- 项目初始化候选状态提交前；
- schema 或 contract 文件发生变化；
- 项目恢复前后；
- Project root 或 Skill root 变化；
- 创建重要 Workstream 分支；
- 重要 artifact 被替换、失效或谱系发生重大变化；
- 首个外部长任务提交前；
- Workstream 完成、归档或放弃前；
- 用户明确要求完整审计。

FULL 可以执行：

- schema meta-validation；
- 全部适用 runtime instance 校验；
- 项目级交叉引用扫描；
- 索引、路线、task、artifact、decision、submission 与 event 一致性检查。

当前默认实现：

```text
runtime_schema_validator 0.1.0 — ACTIVE
```

## 8. schema cache

cache key 必须基于适用 schema 文件的内容 hash，不以时间戳代替。

```text
schema hash 未变化且 cache 有效
→ 复用 schema meta-validation 结果
→ 不重复 check_schema
```

schema 文件变化、cache 缺失或用户明确要求重新验证时，重新生成 cache。

cache 是可删除和可重建的非权威数据，不得替代 schema 或项目状态。

cache 默认写在 MD project root 下的已注册 cache 路径，不污染 Skill architecture root。

## 9. 失败与回退

- Tool 返回 `FAIL` 时，Manager/调用 Skill 按结构化错误处理，不得由 LLM 宣称通过；
- Tool 不可用或版本不兼容时，使用已批准的确定性备用路径；没有备用路径时记录当前 capability blocker；
- 不得用 LLM 逐字段模拟 FULL schema 校验作为默认回退；
- 工具失败不得自动修改 schema、降低 gate 或忽略引用错误；
- 后续路线或 Workflow 问题不得与当前 Tool blocker 并列成同一级停止原因。

## 10. 权限

只读工具不得修改项目权威文件。

写入工具必须使用：

```text
候选文件
→ 校验
→ 备份/回滚准备
→ 原子替换或受控事务
→ 结构化结果
```

涉及科研业务文件的工具必须由对应 Operation 或 Validator 调用。Manager 可直接调用仅处理管理状态、schema、引用、事务和用户摘要的已批准工具。