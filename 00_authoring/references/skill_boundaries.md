# Scientific Skill boundaries

Status: CURRENT

## 1. Core model

```text
main Skill first
→ references when detail is long
→ supporting Skill only when boundary is complex and useful
→ deterministic Tool only for deterministic capability
```

科研 Skill 不按 Workflow / Operation / Validator 分类。

一个 main Skill 对应一个可由 Task Execution Agent 直接理解和推进的科研职责，并拥有自己的输入、reuse、核心科学/技术规则、validation 与 results。

## 2. Stage-oriented active layout

Current scientific Skill roots：

```text
01_structure_preparation/
02_topology_preparation/
03_md_preparation/
04_md_simulation/
05_analysis/
```

这些编号对应 MD Workflow Stage 1–5。

Stage root 可以拥有一个 main `SKILL.md`，并按实际复杂度包含 1.x / 2.x / 3.x / 4.x / 5.x Step 或 supporting Skills。

Stage 编号和 Task Sheet step 是科学流程语义，不等于必须建立额外角色层。

## 3. Non-Skill infrastructure

以下不属于 Scientific Skill roots：

```text
references/
evals/
tools/
legacy/
00_authoring/archive/
```

因此 shared references、测试、工具、legacy contracts/runtime 和历史设计材料不得借用 Stage 编号作为根目录前缀。

### AGENTS.md boundary

`AGENTS.md` 是为了测试 / Agent 调用方便而临时生成的辅助文件。它可以指向测试时需要加载的 main `SKILL.md`，但：

- 不属于任何 Skill package；
- 不是 Skill main / reference / supporting Skill 的组成部分；
- 不能作为某条 Skill 规则已经被正式引用、依赖或在真实 Skill runtime 中可达的依据。

正式 Skill 的依赖、reference 与 supporting Skill 关系，必须由对应 `SKILL.md` 及其 package 内部的正式引用建立。

## 4. Supporting Skill

只有复杂且边界清晰时才拆 supporting Skill。适合拆分的情况包括：

- 可独立按需加载；
- 有完整独立科学/技术职责；
- 被多个 main Skill 复用；
- 需要独立测试或维护；
- 拆分显著降低主 Skill 上下文。

不因 validation 配对、目录对称、历史角色分类或减少几段文字而拆 Skill。

## 5. Reference

长但仍属于当前 Skill 的规则、registry、数据表、选择规则、方法说明、大枚举或条件性细节优先放 Skill 自己的 `references/`。

main Skill 必须说明何时读取 reference；不得启动时扫描整个 reference tree。

确有跨多个科研执行 Skill 共用价值、且不属于任何单一 Stage / Step 科学职责的通用 Task Execution 规则统一位于：

```text
references/task_execution_rules.md
```

该文件是仓库级 shared reference，不是独立 Skill、dispatcher 或额外 runtime 环节。所有正式科研执行 Skill 的 main `SKILL.md` 必须显式引用它；引用只建立通用执行规则的可达性，不改变各 Skill 对具体科学规则、validation 与 results 的 ownership。

## 6. Validation ownership

默认：

```text
main Skill 产生 / 判断结果
→ main Skill 定义该结果如何验证
```

只有 validation 本身成为复杂、独立、可复用职责时才拆 supporting validation Skill。

Tool 对自己生成的确定性输出负责机械/格式有效性；main Skill 仍负责判断其是否满足科研目标。

## 7. Tool

Tool 是确定性能力组件：

```text
明确输入
→ deterministic action
→ 明确输出
```

Current shared Tool root：`tools/`。

Tool 不负责开放式用户意图、科研目标选择、任务规划或其它 Skill 的内部决策。

Legacy runtime-dependent tools 位于 `legacy/tools/`，不能因为历史状态自动作为 current implementation。

## 8. External Skill boundary

Authoring 当前 Skill 时可以读取相关外部 Skill，但当前 Skill 对外只定义自身确实需要的接口条件，例如：

```text
consume: 当前职责实际消费哪个正式结果 / 接口
require: 当前职责依赖哪项已冻结能力
```

不要因为存在相邻或后续 Step，就在当前 Skill 中自动增加“如何交给下一环节”的 handoff 章节、handoff 文件或下游处理规则。普通相邻 Step 的流程关系由 Stage main Skill 表达；下游需要什么输入，由下游自己的 Object requirements / input contract 定义。

不得重新定义外部 Skill 的内部步骤、默认参数、方法选择、validation、official results 或文件生命周期。

## 9. Negative scope / 禁止项

Negative scope 只在边界本身需要被明确执行时出现，不要求列完整。

适合明确写出的情况包括：

- 当前职责与相邻职责容易混淆，不写会导致高概率越界；
- 必须阻止 Agent 采用一个常见但已明确否定的默认行为；
- 涉及安全、原始数据保护、不可逆修改或结果完整性；
- 某项禁止条件直接决定 validation 或 result 是否有效。

除此之外，不为“范围看起来完整”枚举本 Skill 不负责的所有事情。其它职责不需要通过当前 Skill 的 negative list 再描述一遍。

## 10. Physical layout follows responsibility

一个 Stage 可以采用：

- 一个 main Skill；
- main Skill + references；
- main Skill + 少量 Step/supporting Skills；
- Stage-specific execution object 结构，例如 Stage 4 run units。

物理布局服从科研职责。没有 current Skill 的 Step 不为目录对称创建空 package；已有内容迁移也不保留 role-based compatibility copy。
