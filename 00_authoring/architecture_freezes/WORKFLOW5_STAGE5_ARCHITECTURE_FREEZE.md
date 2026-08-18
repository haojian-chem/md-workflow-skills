# Stage 5 — Analysis architecture freeze

Status: **FROZEN — NO ACTIVE SKILL GENERATION APPROVED YET**

本文件记录 Stage 5 — Analysis 的 current architecture。当前没有 active Stage 5 `SKILL.md`；未来经用户明确批准后，main Skill 的 active entry 为：

`05_analysis/SKILL.md`

analysis capability inventory 的冻结设计：

`00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ANALYSIS_CAPABILITY_INVENTORY_FREEZE.md`

## 1. Stage 5 catalog

Stage 5 固定为：

```text
5 Analysis
```

Stage 5 **不设置编号化 sub-stage**。此前 `5.1 Analysis planning and orchestration` 的职责由 Stage 5 main Skill 本身承担；`5.1` 不再是 current catalog identity。

RMSD、RDF、PCA、trajectory preprocessing、index generation 等也不作为新的 `5.x`；它们是 Stage 5 内部 plan items，由对应 analysis capability owner 负责具体方法与 validation。

Stage 5 在 Task Sheet 中使用一个 `5 Analysis` stage-level 条目，不采用 Stage 4 的 project-level run-unit identity。

## 2. Manager / Stage 5 boundary

Manager 只负责：

- 判断任务范围是否包含 Stage 5；
- 在初始 Task Sheet 中建立 `5 Analysis`；
- 保留用户明确提出的分析目标、对象、约束；
- 用户明确指定 RMSD、RDF 等方法时原样保留。

Manager 不负责：

- 把研究目标展开成具体分析方法组合；
- 选择具体 analysis capability；
- 查询 Stage 5 reuse；
- 决定 trajectory / index 的具体处理方式。

Stage 5 main Skill 负责：

- 理解当前分析目标；
- 读取 analysis capability inventory；
- 集中查询已有可复用正式分析结果和 prepared inputs；
- 做 Stage 5 reuse 核验；
- 将目标展开为完整 Stage 5 plan；
- 选择并调度 analysis capability / prepared-input producer；
- 维护 `5 Analysis` 条目内部的 plan items；
- 当执行证据破坏原计划前提时调整尚未完成的后续 plan。

具体 analysis capability owner 负责自己的方法、执行细节、输出和 validation。

## 3. Main-Skill principle

Stage 5 main Skill 是 Agent guide，不是 parser / dispatcher engine。

- 可以直接读取和理解 Task Sheet、索引和实际科研文件；
- capability inventory 只用于发现已有能力，不是强制 parser；
- Tool 只有在其确定性能力对当前任务真正有价值时调用；
- 不为了形式化而强制引入额外 schema/workflow；
- 具体 capability 的内部规则只由对应 owner 自己拥有，Stage 5 main Skill 不复制。

## 4. One-pass planning

进入 Stage 5 时集中完成一次当前资源查询、reuse 核验和整体规划：

```text
read Task Sheet Stage 5 requirement
→ read analysis capability inventory
→ query existing formal analysis results
→ query trajectory_index.yaml when relevant
→ determine reusable inputs/results
→ determine missing required inputs
→ include trjconv / index-generation / other required producers when needed
→ pre-assign intended use/dependency of future outputs
→ write the complete current plan into Task Sheet
→ execute the plan
```

正常执行中，不为每个后续 item 重复全局 reuse 查询。

只有前置失败、实际产物不满足规划条件、用户修改需求或其他证据破坏当前 plan 前提时，才调整尚未完成的后续 plan。

## 5. Plan item model

Stage 5 main Skill 在 `5 Analysis` 条目内维护局部整数编号：`1, 2, 3, ...`。

规则：

- 不使用 `5.1`、`5.1.1`、`analysis.1` 等 project-level identity；
- item 一旦加入，编号固定；
- 原则上不删除、不重编号；
- 不再执行的 item 标记 `已终止`；
- 新增 item 使用下一个整数编号。

状态只使用：

```text
未完成
已完成
已终止
```

规划期最小结构：

```text
编号
capability
inputs
settings
status
path
```

完成时可按需增加：

```text
results
```

字段语义：

- `capability`：analysis capability inventory 中的条目名；可指向 Skill、Tool 或其他已登记 owner；
- `inputs`：当前 item 实际消费的输入；已有文件记录完整路径；
- `settings`：capability-specific 设置，不建立 Stage 5 通用子 schema；
- `status`：`未完成 / 已完成 / 已终止`；
- `path`：当前 item 相关文件的完整目录，用于查询和恢复，不指向单个结果文件；
- `results`：completion-time 可选字段，只记录已通过对应 capability owner validation 的关键正式结果/产物入口，不罗列目录内全部文件。

`path` 与 `results` 的边界：

```text
path    → item 工作/文件目录与恢复定位入口
results → 已确认有效、值得直接定位或供后续 item 消费的关键正式产物
```

`results` 不建立统一子 schema，可按 capability 的产物语义记录，例如：

```yaml
results:
  data: /full/path/to/rmsd.xvg
```

或：

```yaml
results:
  trajectory: /full/path/to/processed.xtc
```

如果输入尚未生成但由当前 plan 的前置 item 负责产生，使用直观依赖描述，例如：

```text
trajectory: 使用第 1 项生成的处理后轨迹
index: 使用第 2 项生成的 ndx 文件
```

不要求 `from_item` / `output_role` 等专门 schema。

## 6. Multiple trajectories / grouped analyses

一个 plan item 对应一次统一定义的分析。

多条 trajectory 可以放在同一 item 中，当且仅当它们属于同一次分析并共享关键 settings；共同 topology/reference 类输入只记录一套。

如果用户要求分别分析，或不同输入需要不同关键 settings，则拆成多个 plan items。

最终 `inputs` 记录解析后的实际文件路径；不使用 `source: md.N` 替代具体输入。`md.N` 等逻辑对象只作为查找实际文件时的线索。

## 7. Analysis capability inventory

未来正式 inventory：

`05_analysis/references/analysis_capability_inventory.yaml`

每个实际可用条目至少记录：

```yaml
name:
purpose:
required_files:
skill:
```

- `name`：plan item 的 `capability` 引用名；
- `purpose`：能力用途；
- `required_files`：输入角色 + 可接受文件类型，不绑定项目具体文件名；
- `skill`：对应 guide 路径。

可以执行时生成的辅助文件，不因为“可能需要”就写成 hard required file。

Inventory 是能力发现入口，不复制具体 capability 的方法、命令、selection、preprocessing 或 validation。

## 8. Prepared inputs and indexes

Stage 5 只为具有明确 project-level reuse 价值的 prepared input 建立项目级索引。当前冻结保留：

```text
<project_root>/05_analysis/indexes/trajectory_index.yaml
```

### 8.1 `trajectory_index.yaml`

维护者：负责产生处理后 trajectory 的 `trjconv` capability owner。

Stage 5 main Skill 只查询、核验和使用，不负责生成 trajectory、决定存放位置或登记索引。

最小记录方向：

```yaml
- path: /full/path/to/processed.xtc
  input_trajectory: /full/path/to/input.xtc
  atom_order_reference: /full/path/to/system.tpr
  output_selection: System
  processing:
    # only processing conditions relevant to reuse
```

`processing` 只记录影响 reuse 的实际处理条件，如 PBC/center/fit、`dt`、time range 等；不要求所有条目使用完全相同字段。

### 8.2 External index (`.ndx`) handling

Stage 5 **不建立 project-level `ndx_index.yaml`，也不执行跨 Task 的 `.ndx` 自动复用扫描/判定**。

同一个 topology / TPR lineage 只能说明体系来源相关，不能证明现有 `.ndx` 已包含当前分析需要的 group。真正判断复用仍需检查当前 capability 的 selection/group 语义；考虑到 `.ndx` 文件小且生成成本低，项目级 reuse/index 机制没有足够收益。

Stage 5 不维护“哪些分析需要 `.ndx`”的固定表。判断依据是当前 analysis capability 的输入要求：

```text
current capability 所需 selections / groups
→ 能否由该 capability 基于当前输入和其原生 selection/default-group 机制直接满足？

能
→ 不预生成外部 .ndx

不能，且 capability 明确需要外部 index 输入
→ 在当前 plan 中安排 index-generation capability
```

因此 Stage 5 判断的是**当前 capability 的 required inputs 是否已经满足**，而不是抽象判断“是否需要 group”。selection/group 能否直接表达、是否必须物化为 `.ndx`，由对应 capability owner 的接口/规则拥有。

当前 Task 内如果前置 item 已生成满足后续需求的 `.ndx`，后续多个 items 可以直接共享该 `results`；这是 Task 内显式依赖，不属于 project-level reuse。

如果用户明确提供现有 `.ndx`，可以作为候选输入交给对应 capability。是否包含所需 group、是否与当前分析输入兼容，由对应 capability owner 核验；满足则使用，不满足则在当前 plan 中生成新的 index。

## 9. Validation ownership

Stage 5 不设置统一 Validator layer，也不重新验证所有具体能力输出。

例如：

```text
trjconv    → 自己生成的 trajectory
make_ndx   → 自己生成的 ndx
RMSD Skill → RMSD 执行及输出
RDF Skill  → RDF 执行及输出
```

只有对应 capability owner 确认输出有效后，相关 plan item 才进入 `已完成`，关键正式产物才按需写入 `results`。

Stage 5 main Skill 只核验 orchestration 一致性：目标覆盖、capability/inputs/settings/依赖充分、编号和状态一致、后续项不依赖已终止或未产生所需输入的前置项。

## 10. Project result registration

`project_result_index.md` 按“分析事项”粒度登记：

```text
对哪些对象
→ 做了哪些分析
→ 详细记录入口
```

详细记录入口应能追溯到对应 Task Sheet / Stage 5 plan item，并进一步定位：

```text
capability
inputs
settings
status
path
results   # when present
```

Task Sheet 的 `results` 是当前 item 的直接恢复/依赖入口；`project_result_index.md` 只承担跨任务正式结果检索，不要求复制每个 item 的全部 `results`。

不把每个 `.xvg/.csv/.dat/.png/.xtc/.ndx` 单独复制成 project-level 索引项。

是否额外汇总多个分析结果、综合解释或生成报告，由当前用户任务决定，不是 Stage 5 固定完成职责。

## 11. Stage completion

Stage 5 可以完成的前提：

- 当前分析目标所需 plan items 已完成，或有明确理由进入 `已终止`；
- 每个 `已完成` item 已通过对应 capability owner 的 validation；
- 需要直接恢复或供后续 item 消费的关键正式产物已按需写入 `results`；
- 需要保留的分析事项已经按上述边界登记到 `project_result_index.md`。

## 12. Explicitly rejected defaults

不得默认：

- 为 analysis planning and orchestration 再建立 `5.1` wrapper；
- 把 RMSD / RDF / PCA 等拆成新的 `5.x`；
- 增加 Structural / Interaction / Conformational 等仅用于分类的执行层；
- 为 Stage 5 建立类似 Stage 4 `run_unit.yaml` 的 project-level analysis-unit identity；
- 让 Manager 代替 Stage 5 main Skill 设计具体分析方法组合；
- 让 Stage 5 main Skill 接管 `trjconv` / `make_ndx` 文件生命周期；
- 建立 project-level `ndx_index.yaml` 或 `.ndx` 自动复用判定机制；
- 使用统一 `prepared_input_index.yaml` 同时由多个 producer 维护；
- 用 `source: md.N` 替代最终实际输入文件路径；
- 用单一 `object` 字段承载全部分析对象语义；
- 强制所有分析使用统一 `range / dt / target` schema；
- 强制 Stage 5 main Skill 固定进行结果汇总；
- 建立统一 Stage 5 Validator layer；
- 为旧目录分类建立 Workflow / Operation / Validator 层；
- 把 Agent 锁进无必要 parser / wrapper / dispatcher 链。

此前以 `5.1 Analysis planning and orchestration` 为 identity 的详细 freeze 已被本 Stage-level freeze 接管；历史材料仅保留在 `00_authoring/archive/stage5_history/`。