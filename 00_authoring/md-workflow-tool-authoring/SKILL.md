---
name: md-workflow-tool-authoring
description: 为本项目设计、实现、测试、注册、升级或废弃确定性共享 Tool 时使用。Tool 提供精确、稳定、可测试的确定性能力；它不是 Agent 理解任务的 parser gate，也不替代 main Skill 的科学判断。
---

# 目标

把真正适合程序化的确定性动作实现为受控共享 Tool，同时保持：

```text
Agent 理解任务和科学判断
→ 由当前 main Skill 指导

确定性 parsing / transform / calculation / file write / mechanical validation
→ 可由 Tool 提供
```

Tool 不是新的科学决策层，也不是新的 runtime orchestration 层。

# 启动前读取

默认先读取：

```text
AGENTS.md
→ 00_authoring/SKILL.md
→ 00_authoring/references/deterministic_tool_protocol.md
→ 目标 Tool 的当前 tool.yaml / 实现 / tests
→ 实际调用它的 main/supporting Skills
```

需要注册或发布 Tool 时再读取 `05_tools/tool_registry.yaml`；涉及多窗口写入协调、inventory/status 或 Legacy 迁移时，再按需读取对应 authoring metadata / Legacy 材料。

不要为了 Tool authoring 预加载整个 `00_authoring/`。

先列出：

```text
已做过
已否定
仍未验证
```

# 1. 先判断是否真的需要 Tool

优先 Tool 化：

- 精确 parsing / structured extraction；
- hash / mapping；
- 稳定文件变换；
- 批量处理；
- 可重复数值计算；
- 明确格式校验；
- 安全、可恢复的文件写入；
- 高频重复且自然语言实现容易不一致的确定性动作。

以下不足以成为新 Tool 的理由：

- 只是包装一次简单读取；
- 只是让 Agent 必须先经过 parser；
- 只是为了把几行 guidance 搬出 Skill；
- 只是为了恢复旧 route/event/state/transaction runtime；
- 只是因为“程序化看起来更正式”。

必须明确 Tool 的定位：

```text
required_capability
preferred_implementation
optional_helper
```

具体 Tool 只有在科学/技术接口真正不可替代时才设为唯一实现。

# 2. Tool 不承担的职责

Tool 不得：

- 解释用户开放式科研意图；
- 扩大任务目标；
- 选择 Task 范围；
- 决定其他 Skill 应做什么；
- 作开放式科学判断；
- 向用户提问；
- 自行创建 Agent；
- 把 parser 输出设成 Agent 理解原始科研文件的唯一许可入口；
- 为普通 Lightweight Runtime 构造 Workstream、route、event、transaction 等旧对象；
- 修改未授权路径。

# 3. 冻结 Tool interface

建议至少明确：

```yaml
name:
version:
status: DESIGNED | IMPLEMENTED | TESTED | ACTIVE | DEPRECATED | RETIRED
capability:
role: required_capability | preferred_implementation | optional_helper
callers: []
entrypoint:
inputs: []
outputs: []
read_paths: []
write_paths: []
side_effects: []
compatibility:
  minimum_python:
  dependencies: []
```

只在真正有价值时增加 cache、transactional write、structured error 等字段。

不要为了统一 Tool schema 把简单工具接口过度复杂化。

# 4. 输入输出原则

优先显式业务接口：

```text
明确文件/目录
+ 必要参数
→ deterministic action
→ 明确输出/report
```

不要设计成：

```text
runtime task object
→ Tool 解包项目状态
→ Tool 决定下一阶段
→ Tool 写 route/event/state closure
```

Tool 可以输出 JSON/YAML/text/科研文件，具体格式由调用方真正需求决定；不是所有 Tool 都必须输出同一种结构化 receipt。

# 5. 权限和副作用

只读 Tool 默认不修改项目文件。

写入型 Tool 必须明确：

- 输入；
- 输出位置或输出策略；
- 是否允许覆盖；
- 冲突行为；
- 部分失败 cleanup；
- 必要的执行前后 validation。

共享 Tool 不得越过当前调用 Skill 授权自行管理其他科研职责。

如果某个 Stage 明确把特定项目级索引交给 Tool 维护，例如 Stage 5 的 trajectory / ndx indexes，则以该 Stage main Skill 为授权来源。

# 6. 实现

Tool 目录：

```text
05_tools/<tool-name>/
├── tool.yaml
├── <entrypoint>
├── tests/
└── README.md          # only when useful
```

要求：

- 默认无网络访问，除非 Tool 明确需要且获授权；
- 路径参数显式；
- 不吞掉异常或伪造 PASS；
- 不嵌入 LLM 调用；
- 不复制其他 Skill 的科学判断；
- 不默认扫描整个项目来猜输入。

# 7. Testing

测试覆盖应根据 Tool 的真实风险选择，例如：

- 正常输入；
- 缺失/错误输入；
- 边界值；
- 权限越界；
- 重复运行；
- 部分失败；
- 输出 validation；
- 性能 benchmark（确有性能要求时）；
- compatibility / migration（确有版本接口时）。

不再要求所有新 Tool 继承 Legacy runtime FAST/FULL schema-validation 测试模式。

测试/fixtures 放入：

`04_evals/<tool-name>/`

# 8. 注册与发布

只有实现和适用测试通过后才可在 `05_tools/tool_registry.yaml` 标记为 `ACTIVE`。

Registry 至少能定位：

- name/version/status；
- Tool 路径与 entrypoint；
- capability / role；
- 主要 caller；
- 重要 read/write 权限；
- tests / validation evidence；
- replacement/deprecation 信息（如有）。

# 9. Callers and ownership

Tool authoring 时必须读取实际 caller Skills，理解它们为什么需要该 capability。

但 Tool guide 不重新定义 caller Skill 的：

- 科学任务目标；
- 方法选择；
- reuse；
- project result registration；
- 用户确认逻辑。

如果 caller Skill 需要修改，记录 cross-skill finding 并交给对应 owner，不在 Tool 内偷偷改变 caller 语义。

# 10. 失败和回退

Tool 失败时：

- 不把失败结果解释成成功；
- 有已验证等价实现时可以回退；
- 无等价实现且 capability 必需时，当前任务保持未完成；
- 不降低科学 gate；
- 不临时恢复 Legacy runtime 以绕过问题。

# 交付

```yaml
status: IMPLEMENTED | TESTED | ACTIVE | REVIEW_REQUIRED | BLOCKED
name:
version:
role:
created_files: []
modified_files: []
registry_updated:
tests:
  passed: []
  failed: []
cross_skill_findings: []
open_questions: []
next_action:
```

# 完成检查

- [ ] Tool 化确有确定性价值；
- [ ] Tool 不是不必要 parser gate；
- [ ] required / preferred / optional 定位清楚；
- [ ] Tool 不承担开放式科学判断；
- [ ] caller Skill 的职责没有被 Tool 重定义；
- [ ] write scope 明确；
- [ ] tests 覆盖真实风险；
- [ ] 未恢复 Legacy orchestration；
- [ ] 未把未测试 Tool 标记为 ACTIVE。
