# Scientific Skill boundaries

Status: CURRENT

本文件定义当前科研 Skill 的职责组织方式。

核心原则：

```text
main Skill first
→ references when detail is long
→ supporting Skill only when boundary is complex and useful
→ deterministic Tool only for deterministic capability
```

当前设计不要求把科研 Skill 分类成 Workflow / Operation / Validator。

## 1. Main Skill

一个 main Skill 对应一个能够被 Task Execution Agent 直接理解和推进的科研职责。

它至少应让 Agent 知道：

- 当前目标；
- 当前输入 / 对象 / 证据；
- reuse 边界；
- 必须遵守的科学 / 技术规则；
- 可使用的工具或方法；
- validation；
- 结果和 handoff。

main Skill 可以同时包含执行、判断和结果 validation，只要这些内容属于同一个清楚职责。

不要为了“层次完整”把一个自然职责人工拆成 Operation + Validator 或 Workflow + Operation。

## 2. Stage-oriented active layout

当前 active 科研 Skill 默认按 Stage / 科学职责组织，例如：

```text
01_structure_preparation/
02_topology_preparation/
04_md_simulation/
05_analysis/
```

Stage root 可以拥有一个 main `SKILL.md`，并按实际复杂度包含 1.x / 2.x / 4.x 等 step/supporting Skills。

Stage 编号和 Task Sheet step 是科学流程 / 任务计划语义，不等于必须建立额外角色层。

历史 `01_workflows/`、`02_operations/`、`02_validators/` 已退出 active scientific Skill layout。需要保留的历史实现只用于 `00_authoring/archive/` 或 Git history；不得把这些旧根目录作为新 Skill 的落位模板。

## 3. Supporting Skill

只有复杂且边界清晰的部分才值得拆 supporting Skill。

适合拆分的情况：

- 可以独立按需加载；
- 有独立完整的科学 / 技术职责；
- 被多个 main Skill 复用；
- 需要独立测试或维护；
- 内容足够复杂，拆分能显著降低主 Skill 上下文。

不适合拆分的情况：

- 只有几条规则；
- 只是为了给 validation 单独一个文件；
- 只是为了匹配历史 Workflow / Operation / Validator 分类；
- 拆分后必须增加新的 dispatcher 才能工作；
- supporting Skill 只是把主 Skill 的同一段话重复一遍。

## 4. Reference

长但仍属于当前 Skill 的内容优先放 `references/`：

- 长科学规则；
- registry；
- 数据表；
- 选择规则；
- 方法说明；
- 大枚举；
- 只有特定条件下才需要读取的细节。

主 Skill 必须说明何时需要读取某 reference；不得默认启动时扫描整个 `references/`。

## 5. Validation ownership

Validation 默认跟随结果 owner。

```text
main Skill 产生 / 判断结果
→ main Skill 定义该结果如何验证
```

如果 validation 本身成为一个复杂、独立、可复用职责，才拆 supporting validation Skill。

Tool 对自己生成的确定性输出负责其机械 / 格式有效性；main Skill 仍负责判断这些输出是否满足当前科研任务。

## 6. Tool

Tool 是确定性能力组件：

```text
明确输入
→ deterministic action
→ 明确输出
```

Tool 不负责：

- 理解用户开放式意图；
- 选择科研目标；
- 规划整个任务；
- 决定其他 Skill 应该做什么；
- 通过 parser 结果垄断 Agent 对原始数据的理解。

Skill 可以推荐或调用 Tool，但除非科学 / 技术方法本身要求，不把 Tool 变成唯一允许路径。

## 7. External Skill boundary

Authoring 某个 Skill 时，应主动读取与它直接相关的其他 Skill 来理解接口。

当前 Skill 对外部 Skill 只记录：

```text
consume: 哪个正式结果 / 接口
require: 哪项已冻结能力
handoff: 当前输出如何被对方消费
```

不得记录外部 Skill 的完整内部实现。

发现外部 Skill 缺少必要规则时，提交 cross-skill finding，而不是在当前 Skill 中替它补规则。

## 8. Physical layout follows responsibility

一个 Stage 可以：

- 一个 main Skill 直接覆盖；
- 一个 main Skill + references；
- 一个 main Skill + 少量 step/supporting Skills；
- 在确有复杂执行对象时采用 Stage-specific 结构，例如 Stage 4 run units。

物理布局服从当前科学职责。没有 current Skill 的 Stage / step 不为了目录对称创建空 package；已有内容迁移时也不保留 role-based path compatibility copy。
