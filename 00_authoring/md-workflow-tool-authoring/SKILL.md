---
name: md-workflow-tool-authoring
description: 为本项目生成、测试、注册、升级、维护或废弃确定性共享工具时使用。用于 schema 校验、状态事务、引用检查、结构化渲染及其他可重复程序逻辑；不要用于运行具体 MD 科学任务或替代 Manager、Workflow、Operation、Validator 的判断。
---

# 目标

把重复、缓慢或易产生不一致的确定性逻辑实现为受控共享工具，同时保持四层 Skill 的决策职责不变。

Tool 不是 Agent，也不是新的决策层。

# 启动前读取

1. 项目根 `AGENTS.md`；
2. `00_authoring/SYNC_STATUS.md`；
3. `00_authoring/skill_inventory.yaml`；
4. `00_authoring/file_ownership.yaml`；
5. `00_authoring/md-workflow-skill-authoring/references/deterministic_tool_protocol.md`；
6. `05_tools/tool_registry.yaml`；
7. 目标 Tool 的 `tool.yaml`、实现、tests 和调用方；
8. 涉及 schema 时读取 `03_contracts/README.md`。

先列出：

```text
已做过
已否定
仍未验证
```

# 使用边界

用于：

- 新建确定性工具；
- 修复或优化现有工具；
- 增加 cache、批量或增量模式；
- 维护输入输出 contract；
- 建立 fixtures、benchmark 和回归测试；
- 注册、升级、废弃和迁移工具。

不用于：

- 选择 Workstream、路线或下一任务；
- 科学质量判断；
- 直接运行 MD 业务流程；
- 在业务 task 中临时生成未注册脚本；
- 修改工具权限之外的项目文件。

# 步骤 1：确认工具化必要性

只有满足至少一项时继续：

- 确定性逻辑重复出现；
- LLM 执行耗时明显高于程序；
- 自然语言结果不稳定；
- 需要缓存、批量处理或增量检查；
- 需要事务、原子写入或回滚；
- 需要可重复 benchmark。

否则保留在现有 Skill 中，不新增工具。

# 步骤 2：冻结 Tool contract

```yaml
name:
version:
status: DESIGNED | IMPLEMENTED | TESTED | ACTIVE | DEPRECATED | RETIRED
purpose: []
callers: []
entrypoint:
inputs: []
outputs: []
read_paths: []
write_paths: []
side_effects: []
cache:
  enabled:
  key:
  location:
error_model:
  pass_exit_code:
  validation_failure_exit_code:
  tool_failure_exit_code:
compatibility:
  minimum_python:
  dependencies: []
```

输入输出必须机器可读。工具不得用自由文本代替关键状态、错误路径和耗时信息。

# 步骤 3：设计权限和副作用

- 只读工具默认不得修改项目权威文件；
- cache 必须可删除、可重建、非权威；
- 写入工具必须先生成候选文件并完成校验；
- 多文件事务必须定义失败回滚；
- 涉及科研业务文件时，只能由对应 Operation/Validator 调用；
- Manager 只能直接调用管理状态、schema、引用、事务和摘要类工具。

# 步骤 4：实现

工具目录：

```text
05_tools/<tool-name>/
├── tool.yaml
├── <entrypoint>
├── tests/
└── README.md          # 仅在 tool.yaml 不足以说明使用时创建
```

要求：

- 默认无网络访问；
- 路径参数显式，不依赖未声明当前目录；
- 输出稳定 JSON 或 YAML；
- 错误包含对象路径、schema/规则和简短原因；
- 不吞掉异常或伪造 PASS；
- 不把 LLM 调用嵌入确定性工具；
- 不复制共享 schema 定义。

# 步骤 5：FAST/FULL 校验工具要求

runtime schema 工具必须支持：

```text
FAST
FULL
```

FAST：

- 仅处理 changed paths；
- 仅检查直接引用；
- schema hash cache 命中时跳过 schema meta-validation；
- 不扫描完整项目历史。

FULL：

- 校验全部适用 runtime instances；
- 执行项目级交叉引用检查；
- schema 变化或 cache 缺失时执行 meta-validation。

不得增加模型强度分层逻辑；模型配置不属于 Tool contract。

# 步骤 6：测试

至少覆盖：

- 正常输入；
- schema/输入错误；
- 缺失文件；
- cache hit 与 cache miss；
- FAST 不扫描无关对象；
- FULL 能发现跨对象引用错误；
- 权限越界；
- 重复运行幂等性；
- 性能 benchmark；
- 旧版本兼容或明确迁移失败。

测试和 fixtures 放入：

```text
04_evals/<tool-name>/
```

# 步骤 7：注册与发布

只有实现和适用测试通过后才可在 `05_tools/tool_registry.yaml` 标记为 `ACTIVE`。

注册信息至少包括：

- name、version、status；
- path、entrypoint；
- callers；
- read/write 权限；
- input/output contract 摘要；
- tests 与 benchmark 路径；
- replacement/deprecation 信息。

# 步骤 8：维护

发生以下变化时重新评估工具：

- schema、contract 或目录结构变化；
- 调用方输入输出变化；
- cache key 或权限变化；
- 性能显著退化；
- 出现错误 PASS、漏检或不幂等；
- 依赖版本不兼容。

破坏性升级使用新 major version，并保留迁移说明。不得原地改变既有 contract 后仍声称兼容。

# 交付

```yaml
status: IMPLEMENTED | TESTED | ACTIVE | REVIEW_REQUIRED | BLOCKED
name:
version:
created_files: []
modified_files: []
registry_updated:
tests:
  passed: []
  failed: []
benchmark:
  command:
  result:
compatibility:
  breaking:
  migration:
open_questions: []
next_action:
```

# 完成条件

- 工具化必要性明确；
- Tool contract、权限和副作用已冻结；
- 实现无 LLM 决策逻辑；
- fixtures 与 benchmark 覆盖核心路径；
- registry、版本和兼容性信息一致；
- 未破坏四层 Skill 的职责边界；
- 未将未测试工具标记为 ACTIVE。
