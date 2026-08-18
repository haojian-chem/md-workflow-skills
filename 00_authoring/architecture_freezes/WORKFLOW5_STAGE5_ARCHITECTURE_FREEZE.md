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

具体 analysis capability owner 负责自己的方法、执行细节、输出、validation，以及哪些正式结果文件允许进入项目级结果登记。

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

新加入当前 Stage 5 plan、尚未完成或终止的 item 默认记为 `未完成`。Stage 5 不再为 plan item 增加统一的 `待执行 / 执行中 / 失败` 等额外状态。

规划期最小结构：

```text
编号
capability
inputs
settings
status
path    # 当前 Task 实际执行该 item 时必填；direct reuse 且当前 Task 不执行时可省略
```

完成或终止时可按需增加：

```text
results
reason
```

其中 `reason` 在 `status: 已终止` 时必须记录。

字段语义：

- `capability`：analysis capability inventory 中的条目名；可指向 Skill、Tool 或其他已登记 owner；
- `inputs`：当前 plan item 所要求或对应的输入。实际执行时记录当前执行实际消费的输入；direct reuse 时仍记录当前需求对应的输入，用于与候选既有结果进行等价性判断。已有文件记录完整路径；
- `settings`：当前 plan item 定义的 capability-specific 分析设置。实际执行时对应当前执行设置；direct reuse 时仍记录当前需求要求的设置，用于与候选既有结果比较。不建立 Stage 5 通用子 schema；
- `status`：`未完成 / 已完成 / 已终止`；
- `path`：当前 Task 实际执行该 item 时，记录 item 相关文件的完整目录，用于查询和恢复，不指向单个结果文件；若该 item 因 direct reuse 在当前 Task 中不执行，则可省略 `path`；
- `results`：可选字段，记录已经通过对应 capability owner validation、值得直接定位或供后续 item 消费的关键正式结果/产物入口；direct reuse 时可指向被复用的既有正式结果；
- `reason`：终止原因；direct reuse 时应说明已有正式结果已满足当前需求，并可注明其原 Task / result entry。

因此 direct reuse 虽然当前 Task 不执行该 capability，`inputs` 和 `settings` 仍然保留；它们描述的是**当前需求**，不是把旧任务的执行参数复制成当前执行记录。候选旧结果自己的 inputs / settings 应从其原 Task / result record 追溯，并与当前 item 比较。

当执行失败、validation 不通过或后续证据要求调整计划时，**Stage 5 不规定“必须修改原 item”或“必须终止并新建 item”的统一判据**。具体处理方式由实际使用 Stage 5 Skill 的 Agent 或用户结合当前任务判断。Stage 5 只要求调整后的 Task Sheet 保持可追溯：已有编号不重排；若 item 进入 `已终止`，必须记录 `reason`；当前 plan 必须继续准确反映尚需执行的工作与有效依赖关系。

`path` 与 `results` 的边界：

```text
path    → 当前 Task 实际执行 item 的工作/文件目录与恢复定位入口
results → 已确认有效、值得直接定位或供后续 item 消费的关键正式产物；direct reuse 时承担既有正式结果定位
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

### 5.1 Task-local directory layout

Stage 5 不建立类似 Stage 4 `run_unit.yaml` 的 project-level run-unit 索引。每个实际执行 Stage 5 的 Task 使用自己的 analysis 工作目录：

```text
<project_root>/05_analysis/<task_id>/
```

其中 `<task_id>` 与 Task Sheet / `task_index.md` 中的任务编号一致，例如 `T001`。

当前 Task 内实际执行的 plan item 默认使用：

```text
<project_root>/05_analysis/<task_id>/<编号>.<capability名>/
```

例如：

```text
05_analysis/T001/1.rmsd/
05_analysis/T001/2.rdf/
```

该目录即普通实际执行 item 的默认 `path`。如果 direct reuse 导致当前 item 不执行，则不创建无用 task-local item 目录，`path` 可省略。

这是默认工作目录组织，不把 capability 的产物生命周期收归 Stage 5 main Skill。某 capability 若有额外的集中管理产物要求，由对应 capability owner 的 Skill / README 定义实际产物存放与登记规则。

`trjconv` 属于当前已知需要对 processed trajectory 做额外集中管理和登记的 capability：Stage 5 保留 task-local plan item / 工作记录，但 trajectory 的集中存放、允许登记的 trajectory 文件以及登记动作由 `trjconv` capability owner 定义。

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
entry:
```

- `name`：plan item 的 `capability` 引用名；
- `purpose`：能力用途；
- `required_files`：输入角色 + 可接受文件类型，不绑定项目具体文件名；
- `entry`：该 capability 的实际入口，可指向 Skill guide、Tool 或其它已登记能力入口。

首批 Stage 5 capability 的 authoring / implementation 集合固定为：

```text
trjconv
make_ndx
rmsd
rmsf
hbond
rdf
```

这些名称定义首批需要为 Stage 5 准备的能力集合，但**不因写入 freeze 就自动成为 active inventory entry**。只有对应 capability 的实际 `entry` 已形成并可引用时，才能将该条目写入正式 `analysis_capability_inventory.yaml`。

不增加统一 `type: skill/tool/script` 分类字段。Stage 5 只需要能从 `entry` 找到并调用/遵循对应 capability，不为了分类建立额外 schema。

可以执行时生成的辅助文件，不因为“可能需要”就写成 hard required file。

Inventory 是能力发现入口，不复制具体 capability 的方法、命令、selection、preprocessing、validation 或结果登记白名单。

Inventory 只支持 capability discovery 和初步输入匹配；**不得把 inventory 当作 capability 的完整执行接口**。凡某 capability 被纳入当前 Stage 5 plan，Stage 5 main Skill 必须先读取其 `entry`，再最终确定该 plan item 的 `inputs`、`settings` 和 dependencies。selection/reference 条件、关键 settings、正式输出语义、允许进入项目级结果登记的文件，以及其它 capability-specific 要求均由对应 `entry` / capability README 拥有，不复制进 inventory。

### 7.1 Capability gaps

如果当前分析需求没有合适的已登记 capability，Stage 5 不为该缺失能力创建对应的 Stage 5 plan item，也不创建虚构 capability / inventory entry。该未覆盖需求或 capability gap **可以继续记录在 Task Sheet 中，但应位于 Stage 5 plan items 区域之外**，用于保留当前任务上下文和后续处理状态。

下列事项由用户与 Agent 在 Stage 5 Skill 责任之外共同完成：

- 用户明确指定的方法尚无对应 capability；
- 或现有 capability 均不能可靠覆盖当前分析目标。

Task Sheet 中如何表达和维护这类边界外事项，由当前 Agent / 用户结合任务决定；Stage 5 不为其定义专属 item schema、状态机或工作目录规则。

如果后续通过独立的 capability authoring / update 已形成实际可引用的 `entry`，且当前任务仍需要该分析，Stage 5 再重新读取 inventory / `entry`，按正常规则创建相应 plan item。

“记录并学习用户与 Agent 完成 capability gap 时形成的流程，并据此辅助补充 capability”保留为 **future update direction**；本次 Stage 5 设计与实现不包含该 learning / capability-supplement mechanism。

## 8. Reuse and prepared inputs

### 8.1 `trajectory_index.yaml`

Stage 5 对 `trjconv` 产生、具有后续复用价值的 processed trajectory 保留额外的 project-level 登记入口：

```text
<project_root>/05_analysis/indexes/trajectory_index.yaml
```

该索引由 `trjconv` capability owner 维护。Stage 5 main Skill 只查询、核验和使用，不负责生成 trajectory、决定集中存放位置、决定哪些 trajectory 文件可登记，或维护该索引。

`trjconv` capability owner 的 Skill / README 应拥有：

- processed trajectory 的集中管理规则；
- 哪些 trajectory 文件允许进入该索引；
- 登记所需的 reuse-relevant metadata；
- 具体登记动作与 validation 前提。

Stage 5 freeze 只保留索引存在及其消费边界，不复制 `trjconv` owner 的具体登记文件白名单。

processed trajectory reuse 时，Stage 5 至少检查以下六类因素：

1. 来源体系 / atom-order reference；
2. 原子集合 / output selection；
3. PBC 处理；
4. center / fit / orientation 处理；
5. 时间范围；
6. 时间采样 / frame spacing。

具体兼容要求由 consuming analysis capability 拥有；Stage 5 不另建一套统一 preprocessing 判据。

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

### 8.3 Existing formal analysis result reuse

Stage 5 查询 `project_result_index.md` 中已有正式分析事项后，对候选结果至少检查以下六类因素：

1. 分析目标 / result semantics；
2. 分析对象 / selection；
3. 来源数据与分析范围；
4. capability / method；
5. 关键 settings；
6. validation / result completeness。

Stage 5 不为所有分析建立统一 settings schema；具体哪些 settings 会改变结果语义，由对应 capability owner 定义。

复用结果分为三种：

```text
direct reuse
→ 旧正式结果本身已完整回答当前需求

reuse as input
→ 旧结果可作为当前新 plan item 的输入，避免重复前置分析，但当前任务仍需要新的处理

rerun
→ 旧结果不能可靠满足当前需求，需要重新执行相应 analysis capability
```

对应当前 Task Sheet 的记录规则：

```text
direct reuse
→ 当前 plan 仍保留对应 item
→ inputs / settings 记录当前需求，用于与既有结果做 reuse 等价性判断
→ status: 已终止
→ reason 说明已有正式结果直接满足当前需求，并注明复用来源
→ results 指向被复用且已 validation 的正式结果/入口
→ 当前 Task 不执行该 item 时，path 可省略

reuse as input
→ 不为“复用动作”单独建立 plan item
→ 当前新的处理 item 直接在 inputs 中消费旧正式结果

rerun
→ 正常建立并执行当前 analysis item
```

如果候选信息不足，先追溯其 Task Sheet / Stage 5 plan item / `results` / 实际结果文件；仍无法确认时，不把该旧结果自动判定为等价的 direct reuse。

## 9. Validation ownership

Stage 5 不设置统一 Validator layer，也不重新验证所有具体能力输出。

例如：

```text
trjconv    → 自己生成的 trajectory
make_ndx   → 自己生成的 ndx
RMSD Skill → RMSD 执行及输出
RDF Skill  → RDF 执行及输出
```

只有对应 capability owner 确认当前执行输出有效后，实际执行的相关 plan item 才进入 `已完成`，关键正式产物才按需写入 `results`。direct reuse item 不因当前 Task 未执行而进入 `已完成`；它保持 `已终止`，并引用此前已经 validation 的正式结果。

Stage 5 main Skill 只核验 orchestration 一致性：目标覆盖、capability/inputs/settings/依赖充分、编号和状态一致；后续项不得依赖没有产生或引用有效所需输入的已终止前置项。若已终止项属于 direct reuse 且其 `results` 已明确指向有效正式结果，则该结果可以被后续 item 使用。

## 10. Project result registration

`project_result_index.md` 对 Stage 5 采用**白名单制**。

白名单 ownership 下放到各 analysis capability：每个 capability 在自己的 Skill / README 中声明哪些通过 validation 的正式结果文件允许登记到 `project_result_index.md`。Stage 5 main Skill 不维护集中式文件白名单，也不自行扩大某 capability 的可登记文件集合。

因此：

```text
capability owner 明确列为可登记
+ 当前产物已满足该 owner 的 validation / 登记前提
→ 可以登记到 project_result_index.md

未被 capability owner 明确列入白名单
→ 不得因为文件存在、位于 results 中或“可能以后有用”而登记
```

项目级登记仍应能够追溯到对应 Task Sheet / Stage 5 plan item，并定位当前 capability、inputs、settings、状态以及被登记的白名单结果文件。Task Sheet 的 `results` 可以比 project-level 白名单更宽，用于当前任务恢复与依赖；`project_result_index.md` 只保留各 capability 明确允许登记的正式结果。

`trjconv` 的 processed trajectory 额外登记规则由其 capability owner 定义；`trajectory_index.yaml` 与 `project_result_index.md` 是不同用途的登记入口，不由 Stage 5 main Skill把两者合并成统一文件清单。

是否额外汇总多个分析结果、综合解释或生成报告，由当前用户任务决定，不是 Stage 5 固定完成职责。

## 11. Stage 5 Skill completion boundary

Stage 5 main Skill 只判断**自己负责的 Stage 5 plan items** 是否已经处理到可结束当前 Skill 职责的状态，不负责据此宣称整个 `5 Analysis` 或整个 Task 已完成。

Stage 5 main Skill 结束自身当前职责前，应确认：

- 当前 Stage 5 plan items 中没有仍需由 Stage 5 继续推进的 `未完成` item；
- 每个 `已完成` item 已通过对应 capability owner 的 validation；
- direct reuse 导致的 `已终止` item 已明确引用此前通过 validation、且足以满足当前 item 需求的正式结果；
- 其它 `已终止` item 已记录明确 `reason`，并保持依赖关系可追溯；
- 需要直接恢复或供后续 item 消费的关键正式产物已按需写入 `results`；
- 对应 capability owner 白名单要求登记的正式结果文件已经按规则登记到 `project_result_index.md`。

Task Sheet 中如果仍有位于 Stage 5 plan items 区域之外的 capability gap、其它边界外事项或未解决任务要求，是否因此使整个 `5 Analysis` / Task 继续保持未完成，由当前 Task Execution Agent / 用户结合任务单判断。Stage 5 main Skill 不为这些边界外事项定义完成判据，也不因自己的 plan items 已处理完就自动修改整个 Stage / Task 的完成状态。

因失败、取消、validation 失败或其它原因导致原计划不能继续时，由当前 Agent 或用户判断是调整既有 item、终止 item 后新增计划项，还是修改/取消相应目标；Stage 5 不固定这一决策方式。

## 12. Explicitly rejected defaults

不得默认：

- 为 analysis planning and orchestration 再建立 `5.1` wrapper；
- 把 RMSD / RDF / PCA 等拆成新的 `5.x`；
- 增加 Structural / Interaction / Conformational 等仅用于分类的执行层；
- 为 Stage 5 建立类似 Stage 4 `run_unit.yaml` 的 project-level analysis-unit identity；
- 让 Manager 代替 Stage 5 main Skill 设计具体分析方法组合；
- 让 Stage 5 main Skill 接管 `trjconv` / `make_ndx` 文件生命周期；
- 由 Stage 5 main Skill集中定义各 capability 的 `project_result_index.md` 文件白名单；
- 把未被 capability owner 明确允许的文件登记进 `project_result_index.md`；
- 在缺少 capability 时让 Stage 5 main Skill 临时接管该方法的设计、执行或 validation；
- 为 capability gap 创建虚构 Stage 5 plan item、capability 或 inventory entry；
- 由 Stage 5 main Skill 根据自己 plan items 的状态直接判定整个 `5 Analysis` / Task 已完成；
- 为 plan item 失败后的修改/终止/新建方式建立统一自动判据；
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