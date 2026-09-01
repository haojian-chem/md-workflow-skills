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

这里的 main Skill 是**一个 Skill package 的正式入口**，不等于每个 MD Workflow Stage 都必须存在 Stage-level main Skill。编号 Step 自己的 `SKILL.md` 也是其 package 的 main Skill。

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

Stage root 可以根据真实职责采用不同结构：

```text
无 Stage main + numbered Step Skills
Stage main only
Stage main + execution-layer / capability Skills
```

是否设置 Stage main 只取决于是否存在真实、不可合理下放的 Stage-wide orchestration / shared object / lifecycle；不得为了目录对称、Step 数量多或表达相邻流程而自动创建 Stage main。

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

复杂正式结果的详细接口说明也属于当前 Skill 自己的 reference。满足结果字段多、结果文件关系复杂、被多个后续环节读取等条件时，优先使用：

```text
references/results.md
```

main Skill 只保留正式结果摘要、结果入口和必要完成条件；科研执行 Skill 共用的 validation / result generation / result-recording 规则读取仓库级 shared execution reference：

`../../references/result_generation_rules.md`

`references/results.md` 是 Skill source reference，不是科研执行生成的 result artifact，也不是 handoff 文件。

确有多个科研执行 Skill 共用价值、且不属于任何单一 Stage / Step 科学职责的通用 Task Execution 规则统一位于：

```text
../../references/task_execution_rules.md
```

该文件是仓库级 shared reference，不是独立 Skill、dispatcher 或额外 runtime 环节。所有正式科研执行 Skill 的 main `SKILL.md` 必须显式引用它；引用只建立通用 Task Execution 规则的可达性，不改变各 Skill 对具体科学规则、validation 与 results 的 ownership。

## 6. Validation ownership

默认：

```text
main Skill 产生 / 判断结果
→ main Skill 定义该结果需要哪些检查才能完成当前职责
```

这里的 ownership 不等于“每个结果 owner 都必须再执行一次穷尽式独立终检”。Validation 强度必须与当前职责、操作风险和结果声明相匹配：

- 当前操作主要由成熟软件组件直接完成，且可由退出状态、关键输出和少量一致性检查可靠确认时，保持轻量；
- 不为已经在当前执行过程中自然完成的检查再复制第二套同义检查；
- 如果另有可选的独立深度 validation Skill，当前结果 owner 不需要复制该 Skill 的完整检查范围；
- 当前结果 owner 仍应检查足以确认“自己的操作按预期完成、当前正式结果没有明显不一致”的必要内容；
- 只有当前结果本身的正确性确实依赖更深入检查时，才把这些检查纳入当前 Skill。

科研执行 Skill 共用的 validation ownership 与正式结果生成机制由 `../../references/result_generation_rules.md` 统一定义；本文件只固定 Skill ownership 边界。

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

不要因为存在相邻或后续 Step，就在当前 Skill 中自动增加“如何交给下一环节”的 handoff 章节、handoff 文件或下游处理规则。下游需要什么输入，由下游自己的 Object requirements / input contract 定义。

跨 Step 推进按实际 Stage 架构处理：

- 当前 Stage 存在真正拥有 Stage-wide orchestration 的 main Skill 时，Stage-specific route / shared-object relationship 可以由该 Stage main 拥有；
- 当前 Stage 不设置 Stage main Skill 时，Task Execution Agent 根据 Task Sheet、当前 Step 的正式结果 / input contract 和实际执行证据推进，不为表达相邻关系另建 synthetic Stage owner；
- 一个 Task Sheet 可以只覆盖某个 Stage 的局部范围，当前 Step 可以直接消费其它任务已经形成的正式结果，不要求全部相邻 Step 出现在同一 Task Sheet。

不得重新定义外部 Skill 的内部步骤、默认参数、方法选择、validation、official results 或文件生命周期。

### Results / 字段说明边界

当前 Skill 的 results、report format 或 schema 字段说明只定义**当前结果本身**，包括：

- 当前结果文件 / 对象是什么；
- 每个字段记录什么信息；
- 字段的取值、`null`、路径、枚举等语义；
- 为正确解释或验证当前结果所必需的结果内部约束。

当这些内容已经进入当前 Skill 的 `references/results.md` 后，该文件是详细结果接口说明的 owner；main `SKILL.md` 不再复制同一套字段与格式说明。其它 Skill 为了解释该正式结果可以按需读取 `results.md`，但读取不改变当前结果 owner。

不得借 results、report format、schema 示例或字段含义说明去规定：

- 相邻或后续 Skill 应如何消费某个字段；
- 下游根据该字段应执行什么操作、判断或转换；
- 其它 Skill 的 handoff、input interpretation、validation 或 official-result lifecycle。

某个下游 Skill 对输入结果有具体要求时，由该下游 Skill 自己的 Object requirements / input contract 定义。跨 Step 路由若属于实际存在的 Stage-wide orchestration，则由该 Stage main Skill 拥有；没有 Stage main 的 Stage 不因此新增一个 owner。当前结果 owner 只需把当前结果及其字段语义定义清楚。

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

- 无 Stage main，Task Execution Agent 直接进入 numbered Step Skills；
- 一个 Stage main Skill；
- Stage main Skill + references；
- Stage main Skill + 少量 execution-layer / capability Skills；
- Stage-specific execution object 结构，例如 Stage 4 run units。

物理布局服从科研职责。没有 current Skill 的 Step 不为目录对称创建空 package；已有内容迁移也不保留 role-based compatibility copy。
