# 1.3 Chain and Component Selection — Redesign Integration Draft

> 状态：**DRAFT / 等待另一个 1.3 编写窗口同步后合并冻结**
>
> 本文件是当前 1.3 重设计的**整合草案**，用于承接已经确认的设计约束，并为另一个窗口即将同步的 1.3 成果提供对照框架。
>
> 它不是运行时 Skill，不替代：
>
> - `02_operations/chain_and_component_selection/SKILL.md`
> - `02_validators/chain_and_component_selection_validator/SKILL.md`
>
> 也不表示 1.3 已完成 Lightweight Runtime v2 迁移。
>
> **同步原则：**另一个窗口同步后，先逐项对照本草案中的“已冻结约束 / 待合并项 / 冲突项”，再修改正式 1.3 文件；不要同时维护两套并行设计。

---

## 1. 当前定位

1.3 位于结构准备阶段：

```text
1.2 component_and_residue_classification
→ 1.3 chain_and_component_selection
→ 1.4 altloc_occupancy_resolution
```

Step 基础工作目录：

```text
01_structure_preparation/03_chain_and_component_selection/
```

当前任务实际执行目录：

```text
01_structure_preparation/03_chain_and_component_selection/<task_id>/
```

目录职责遵循 Lightweight Runtime v2：

```text
项目初始化
→ 可以建立到 03_chain_and_component_selection/ 基础目录

Manager
→ 在 Task Sheet 中记录 <base>/<task_id>/
→ 不创建 <task_id>/

Task Execution Agent
→ 进入 1.3 后先做 reuse 检查
→ 只有确实需要执行新的 1.3 时才创建 <task_id>/
→ 若直接复用已有 1.3 正式结果，不创建空目录
```

---

## 2. Step purpose

1.3 的核心目的：

> 将用户对“后续结构中需要保留什么”的自然语言要求，解析为明确、可执行、可验证的 **chain + residue retain specification**，然后据此生成一个或多个用户明确要求的结构结果。

1.3 不替用户决定研究对象；它只把用户已经表达的研究对象选择转成正式 selection specification，并在表达存在歧义或冲突时向用户确认。

---

## 3. 上游对象与输入边界

1.3 至少需要：

```text
1.2 classification_result.yaml
对应的结构文件
用户的 retain 描述
```

其中：

- `classification_result.yaml` 必须来自已完成的 1.2；
- 结构文件必须与该 classification result 所描述的结构身份一致；
- 用户描述是 1.3 的研究对象选择来源。

1.3 必须消费 1.2 已经物化的：

```text
chain / component / residue / relation information
opaque IDs
```

硬规则：

- 不重新执行 1.2 分类；
- 不重新实现或猜测 1.2 opaque ID 算法；
- 不根据 basename、链名习惯、残基命名习惯等隐式线索绕开 1.2 身份信息；
- 如果自然语言中的对象无法唯一映射到 1.2 已知对象，必须确认，而不是猜测。

---

## 4. 用户操作层级：只保留 chain + residue

本次重设计把用户可直接表达的选择层级限制为：

```text
chain
residue
```

不要求用户直接使用 `component_id` 作为第三种选择语法。

1.2 的 component / relation 信息继续用于：

- chain / residue 身份解析；
- 关联关系理解；
- selection 合法性核验；
- 后续映射 / provenance。

但 1.3 最终的用户选择语义应归一化为：

```text
保留哪些完整 chain
保留哪些 chain 中的哪些 residue
```

---

## 5. Selection specification：只记录 retain

selection specification 只表达：

> **需要保留什么。**

不设计成同时维护：

```text
retain
remove
```

两套互补规则。

原因：

- 用户目标是定义后续研究对象；
- retain 集合已经足够确定输出；
- retain/remove 双向同时存在会增加冲突和优先级问题；
- 不需要引入隐式补集逻辑。

概念结构：

```text
output structure
├── retain complete chain A
├── retain chain B residues 100-150
└── retain chain C residues 27, 35, 42
```

最终 YAML 字段名、ID 表达、范围格式等由另一个 1.3 窗口同步成果与本草案合并后冻结。

---

## 6. 自然语言 → retain specification

### 6.1 整条链

需要支持：

```text
保留 A 链
保留 A、B 链
只保留链 A 和 C
保留 chain A
```

归一化为完整 chain retain。

### 6.2 链内连续残基范围

需要支持：

```text
保留 A 链 100–150
保留 A 链的 100 到 150 号残基
保留 A:100-150
```

归一化时必须同时保留：

```text
chain identity
residue range
```

不能只保存裸 `100-150`。

### 6.3 单个或离散残基

需要支持：

```text
保留 A 链 100
保留 A 链 100、105、110
```

归一化为 chain + residue 集合。

### 6.4 同一链多个 residue 片段

原则上应允许表达：

```text
保留 A 链 10-30 和 80-100
```

最终 schema 是保存为多个 range、显式 residue list，还是规范化后的统一 residue selector，由同步后的 1.3 设计冻结。

### 6.5 insertion code / 非连续编号

如果结构中存在 insertion code、非连续 residue numbering 或同号 residue 无法仅靠普通整数唯一定位：

- 必须使用 1.2 已物化的 residue 身份；
- 不允许仅凭“100 号残基”猜测唯一对象；
- 无法唯一对应时触发用户确认。

---

## 7. 必须触发用户确认的表达

### 7.1 完整 chain 与该 chain 子集同时出现

例如：

```text
保留 A 链
以及
保留 A 链 100–150
```

不能自动合并，也不能默认以更宽或更窄范围覆盖另一条要求。

因为至少可能表示：

1. 用户要完整 A 链，而 100–150 只是强调区域；
2. 用户实际只要 A:100–150，前面的“保留 A 链”只是宽泛表达。

因此必须确认。

### 7.2 对象不能唯一映射

例如：

- chain 名称在当前 model 中不唯一；
- residue 编号由于 insertion code 等原因存在多义；
- 用户说“那个配体旁边的残基”但没有可唯一解析的正式身份；
- 用户描述与 1.2 分类对象明显冲突。

这类情况不能通过推测解决。

### 7.3 多结构拆分意图不明确

例如：

```text
保留 A、B、C
```

默认是同一个输出结构，不得自行理解成 A-only / B-only / C-only 三个结构。

只有用户明确说“分别保存”“建立多个结构”“结构1/结构2/结构3”等，才进入多结构输出。

---

## 8. 单结构 / 多结构输出

### 8.1 默认：单结构

如果用户没有明确要求拆分，所有 retain selection 都属于**同一个输出结构**。

例如：

```text
保留 A 链和 B 链 50-80
```

表示：

```text
一个输出结构
├── A complete chain
└── B residues 50-80
```

### 8.2 多结构必须由用户显式要求

有效表达例如：

```text
把 A、B、C 分别保存成三个结构
建立 3 个结构：结构1保留A，结构2保留B，结构3保留C
生成 A-only 和 B-only 两套结构
```

每个输出结构必须有自己的完整 retain specification。

不得使用：

```text
剩余部分
其他链
其余残基
```

这类隐式补集作为正式 selection specification。

### 8.3 一个 1.3 Step 可以产生多个正式结构结果

只要用户明确要求多结构输出，当前 1.3 可以一次产生多个正式结构结果，不必人为拆成多个 Task。

具体：

- 输出文件命名；
- manifest 组织；
- result index 登记方式；
- Validator 如何逐结构验收；

等待同步后冻结。

---

## 9. 1.3 明确不负责的内容

1.3 不负责：

- altLoc / occupancy resolution；
- missing-region completion；
- protonation；
- 原子级 selector；
- atom name 筛选；
- 化学键编辑；
- 主动拆断共价键；
- topology 生成；
- residue / component 重新分类；
- 帮用户决定科研上应该选择哪条链或哪些残基。

如果 selection 会触碰确认的共价关系、跨边界关系或其他科学约束，1.3 可以检测并阻止不合法执行，但不能静默改变用户 retain specification 来“修好”它。

---

## 10. Lightweight reuse 方向

1.3 的 reuse 判断必须发生在当前 Task 真正进入 1.3 时。

当前已确定的核心等价条件至少包括：

```text
同一被选择结构身份
+ 同一 1.2 classification identity
+ 同一 retain selection specification
+ 同一单结构 / 多结构输出语义
+ 用户未明确要求重新生成或建立对照结果
```

其中“同一 retain selection specification”必须比较**归一化后的正式 specification**，不能仅比较原始自然语言字符串。

明确可复用：

```text
→ 直接引用已有正式 1.3 结果
→ 不复制结果
→ 不创建当前任务空的 1.3/<task_id>/ 目录
```

明确不可复用：

```text
→ 正常执行新的 1.3
```

缺少足够信息判断是否等价：

```text
→ 当前 Task Execution Agent 询问用户
```

最终 reuse conditions 等待同步后正式冻结。

---

## 11. Operation / Validator 边界草案

当前 1.3 仍采用：

```text
Operation + dedicated Validator
```

但不再采用 Legacy `OPERATION_WITH_VALIDATOR task unit` / subagent closure 语义。

### Operation 预期拥有

```text
purpose
object requirements
reuse conditions
自然语言要求到正式 selection specification 的执行入口
selection execution rules
official structure / mapping / manifest outputs
```

Operation 负责真正产生选择后的结构结果。

### Validator 预期拥有

```text
validation requirements
selection specification 与实际输出一致性检查
结构身份 / retained chain-residue coverage 检查
禁止出现未请求对象的检查
必要 relation / mapping consistency 检查
独立 validation report
```

Validator 不应重新解析用户自然语言并重新生成另一份 selection interpretation；它应验证**已经冻结的 formal selection specification 是否被正确执行**。

Operation 与 Validator 的精确 owner 关系等待同步后用 content map 冻结。

---

## 12. Official results 草案

当前可预期的正式结果类别：

```text
formal selection specification
selected structure file(s)
selection provenance / manifest
必要的 selection mapping
Validator 的正式 validation result/report（若设计为项目级正式结果）
```

但以下内容仍待另窗口同步后冻结：

- `selection_spec.yaml` 是否本身作为 official result；
- 单结构输出固定文件名；
- 多结构输出命名规则；
- manifest 和 mapping 是否分别保留；
- Validator report 是否登记到 `project_result_index.md`；
- 多结构结果在 result index 中的描述规则。

当前不要提前修改正式 1.3 脚本去适配未经冻结的文件名。

---

## 13. 与旧 1.3 实现的关系

当前正式目录：

```text
02_operations/chain_and_component_selection/
02_validators/chain_and_component_selection_validator/
```

及 2026-07-31 PASS 只作为历史实现参考。

旧实现中存在的下列内容不自动继承：

```text
complete-component-only user selection semantics
Legacy subagent_task / subagent_result
Workstream
Manager artifact registration
runtime closure
route/event/state machinery
旧 selection_spec 设计
```

可以复用的只能是经过重新检查后仍符合新语义的：

- 科学规则；
- deterministic parser / writer；
- mapping / relation preservation 逻辑；
- schema 片段；
- 测试 fixture。

不能因为代码已经存在就默认其设计继续有效。

---

## 14. 另一个 1.3 窗口同步后的合并检查表

同步后逐项对照：

```text
[ ] 用户操作层级是否只保留 chain + residue
[ ] specification 是否只表达 retain，而不是 retain/remove 双轨
[ ] 是否支持完整 chain
[ ] 是否支持 chain 内 residue range
[ ] 是否支持离散 residue
[ ] chain + 该 chain 子集冲突是否强制确认
[ ] 多结构是否只在用户明确拆分时出现
[ ] 多结构每个输出是否有独立完整 specification
[ ] 是否直接使用 1.2 opaque IDs，不重建身份算法
[ ] 是否符合 <base>/<task_id>/ 目录策略
[ ] reuse 是否基于正式归一化 selection，而不是自然语言字符串
[ ] Operation 是否执行 specification，而不是自己替用户决定研究对象
[ ] Validator 是否验证 formal specification，而不是重新解释用户自然语言
[ ] official results 是否已经明确
[ ] Legacy runtime contract 是否全部退出默认接口
[ ] 旧脚本/fixture 哪些保留、哪些淘汰已经明确
```

出现冲突时：

```text
优先确认科学语义
→ 再确认 Lightweight runtime interface
→ 最后修改正式 Skill / schema / script
```

不要为了快速同步而直接把另窗口文件整体覆盖进正式 1.3。

---

## 15. 当前待冻结项

另一个 1.3 窗口同步后，重点只需要处理仍未冻结的部分：

```text
selection_spec.yaml 最终 schema
自然语言解析到 formal selector 的精确规范
共价 / relation 跨 selection boundary 规则
Operation / Validator 精确 owner
单结构 / 多结构文件命名
selection manifest / mapping 设计
reuse conditions 最终版
official results 最终版
result index 多结构登记方式
真实 1.2 → 1.3 regression / acceptance
```

完成这些项目后，才能把 1.3 状态从：

```text
redesign draft recorded
implementation incomplete
lightweight migration pending
```

提升为正式实现状态。

---

## 16. 1.3 完成后的下一项架构工作

1.3 同步并冻结后，下一步不直接继续写 2.x / 3.x 具体 Skill。

先确定：

```text
Workflow 2：topology preparation
Workflow 3：MD preparation
```

各自应该拆成哪些 `2.x` / `3.x` 子环节，以及每个子环节的职责粒度、条件属性和基础工作目录。

这一步只确定**子环节分配 / 编号 / 边界**，暂不把具体科学规则提前写进 `workflow_plan_index.yaml`。
