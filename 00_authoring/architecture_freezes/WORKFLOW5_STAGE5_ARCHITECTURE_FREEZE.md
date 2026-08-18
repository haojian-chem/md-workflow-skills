# Stage 5 — Analysis architecture freeze

Status: **FROZEN — NO ACTIVE SKILL GENERATION APPROVED YET**

本文件记录 Stage 5 — Analysis 的冻结架构。Stage 5 的具体分析方法、`trjconv` / `make_ndx` 等能力内部规则与各能力 validation 由未来相应 Skill/Tool 独立维护；本文件不提前固定这些方法细节。

当前没有 active Stage 5 `SKILL.md`。未来正式生成时，Stage 5 main Skill 的 active entry 固定为：

`05_analysis/SKILL.md`

analysis capability inventory 的冻结设计：

`00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ANALYSIS_CAPABILITY_INVENTORY_FREEZE.md`

Stage 5 不设置编号化 sub-stage。此前 `5.1 Analysis planning and orchestration` 的职责已提升为 **Stage 5 main Skill 本身的职责**；`5.1` 不再是 current catalog identity。

Stage 5 不使用 `01_workflows/` / `02_operations/` / `02_validators/` 强制分类。未来正式生成时，一个 Stage 5 main Skill 覆盖 analysis planning and orchestration 主线；只有出现复杂且边界清晰的分析能力时，再增加 supporting Skill。

## 1. Stage 5 catalog

Stage 5 名称固定为：

```text
5 Analysis
```

Stage 5 不再设置：

```text
5.1 Analysis planning and orchestration
```

RMSD、RDF、PCA、trajectory preprocessing、index generation 等也不作为新的 `5.x` sub-stage；它们是 Stage 5 内部 plan items，并由对应 analysis Skill / Tool 自己拥有具体方法和 validation。

Stage 5 在 Task Sheet 中采用 **stage-level planning item**，不采用 Stage 4 的 project-level run-unit 模型。

## 2. Manager / Stage 5 responsibility boundary

Manager 只负责：

- 判断当前任务范围是否包含 Stage 5；
- 在初始 Task Sheet 中建立 `5 Analysis` stage-level 条目；
- 原样记录用户明确提出的分析目标、分析对象和约束；
- 用户明确指定 RMSD、RDF 等方法时原样保留。

Manager 不负责：

- 把研究目标自行展开成具体分析方法组合；
- 选择具体 analysis Skill / Tool；
- 查询 Stage 5 reuse；
- 决定 trajectory / ndx 的具体处理方式。

Stage 5 main Skill 负责：

- 理解当前分析目标；
- 读取 analysis capability inventory；
- 集中查询当前已有可复用分析结果和 prepared inputs；
- 做 Stage 5 reuse 核验；
- 将分析目标展开为完整 Stage 5 plan；
- 选择并调度对应 analysis capability / prepared-input producer；
- 维护 Task Sheet 中 Stage 5 条目内部的 plan items；
- 当执行证据破坏原计划前提时调整后续 plan。

具体 analysis Skill / Tool 负责自己的方法、执行细节、输出和 validation。

核心边界：

```text
Manager
→ 记录“用户要分析什么”

Stage 5 main Skill
→ 决定“本任务具体做哪些分析、需要哪些输入、如何组织这些分析”

analysis capability owner
→ 提供对应分析方法或确定性处理本身，并负责自己的输出 validation
```

## 3. Main-Skill guidance principle

未来 Stage 5 main Skill 是 Agent guide，不是 parser / dispatcher engine。

规则：

- Stage 5 main Skill 可以直接读取和理解当前 Task Sheet、索引和实际科研文件；
- capability inventory 用于发现已有 analysis Skill / Tool，不是强制 parser；
- 具体 Tool 只有在其确定性能力对当前任务真正有价值时调用；
- 不为了形式化把简单文件理解强制转换成额外 schema/workflow；
- 具体 analysis Skill 的内部规则只由该 Skill 自己拥有，Stage 5 main Skill 不复制。

## 4. One-pass Stage 5 planning

Stage 5 main Skill 在进入 Stage 5 时集中完成一次当前资源查询、reuse 核验和整体规划：

```text
read Task Sheet Stage 5 requirement
→ read analysis capability inventory
→ query existing formal analysis results
→ query trajectory_index.yaml / ndx_index.yaml when relevant
→ determine reusable inputs/results
→ determine missing prepared inputs
→ include trjconv / make_ndx or other required producers in the same plan
→ pre-assign intended use/dependency of future outputs
→ write the complete current plan into Task Sheet
→ execute the plan
```

正常执行过程中，不为每个后续 plan item 重新进行一轮全局 reuse 查询。

如果前置执行失败、实际产物不满足规划条件、用户修改分析要求或其他证据破坏当前 plan 前提，Stage 5 main Skill 才重新调整尚未完成的后续 plan。

## 5. Plan item model

Stage 5 main Skill 在 Task Sheet 的 `5 Analysis` 条目内追加编号化 plan items。

编号规则：

- 使用当前 Stage 5 条目内部局部整数编号 `1, 2, 3, ...`；
- 不使用 `5.1`、`5.1.1`、`analysis.1` 等 project-level identity；
- plan item 一旦加入，编号固定；
- 原则上不删除、不重编号；
- 不再执行的项目优先标记 `已终止`；
- 新增项目使用下一个整数编号。

plan item 状态只使用：

```text
未完成
已完成
已终止
```

每个 plan item 的规划期最小结构：

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

- `capability`：引用 analysis capability inventory 中的条目名；该条目可指向 Skill、Tool 或其它已登记 capability owner；
- `inputs`：当前 item 实际消费的输入；已有文件记录完整路径；
- `settings`：capability-specific 当前任务设置，不建立 Stage 5 通用子 schema；
- `status`：`未完成 / 已完成 / 已终止`；
- `path`：该 item 相关文件的完整存放目录，用于查询定位，不指向单个结果文件；
- `results`：completion-time 可选字段，只记录当前 item 已通过对应 capability owner validation 的关键正式结果/产物入口；不要求罗列目录内全部输出文件。

`path` 与 `results` 的职责不同：

```text
path
→ 当前 plan item 的相关文件目录 / 恢复定位入口

results
→ 当前 item 最终确认有效、值得直接定位或供后续 item 消费的关键结果/产物
```

`results` 不建立统一 Stage 5 子 schema；具体键和值按 capability 的正式产物语义记录。例如：

```yaml
results:
  data: /full/path/to/rmsd.xvg
```

或：

```yaml
results:
  trajectory: /full/path/to/processed.xtc
```

只有对应 capability owner 已完成 validation 后，才把产物作为正式 `results` 记录。失败、未完成或仅用于 debug 的中间文件不因为存在于 `path` 下就进入 `results`。

如果输入尚未生成，但已经由当前 plan 前置项目负责产生，使用直观描述记录依赖，例如：

```text
trajectory: 使用第 1 项生成的处理后轨迹
index: 使用第 2 项生成的 ndx 文件
```

不要求 `from_item` / `output_role` 等专门 schema。

## 6. Multiple trajectories / grouped analyses

一个 plan item 对应一次统一定义的分析。

如果多条 trajectory 作为同一次分析共同处理：

- 可以在一个 plan item 中记录多条 trajectory；
- 共同 topology/reference 类输入只记录一套；
- 共用一套当前分析 settings。

如果用户要求分别分析，或不同输入需要不同关键 settings，则拆成多个 plan items。

最终 `inputs` 记录解析后的实际文件路径，不用单独 `source: md.N` 代替具体输入。`md.N` 等逻辑对象只作为 Stage 5 main Skill 查找实际文件时的线索。

## 7. Analysis capability inventory

Stage 5 main Skill 使用一个 Stage 5 analysis capability inventory 作为能力发现入口；正式文件仅在 Skill generation 获批后建立/启用。

未来正式文件名：

`05_analysis/references/analysis_capability_inventory.yaml`

冻结设计见：

`00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ANALYSIS_CAPABILITY_INVENTORY_FREEZE.md`

Inventory 是能力发现入口，不是新的调度层。

每个实际可用条目至少记录：

```yaml
name:
purpose:
required_files:
skill:
```

`name` 是 plan item 的 `capability` 引用名。

`required_files` 记录“文件角色 + 可接受文件类型”，不绑定具体项目文件名。可以在执行中生成的辅助文件不应仅因为可能需要就被写成 hard required file。

Inventory 不复制具体 analysis capability owner 的方法、命令、selection、preprocessing 或 validation 细节。

## 8. Prepared-input indexes

项目级 Stage 5 索引目录：

```text
<project_root>/05_analysis/indexes/
├── trajectory_index.yaml
└── ndx_index.yaml
```

### 8.1 `trajectory_index.yaml`

维护者：负责产生处理后 trajectory 的 `trjconv` Skill/Tool。

Stage 5 main Skill 只查询、核验和使用，不负责生成 trajectory、决定其存放位置或登记索引。

当前最小记录方向：

```yaml
- path: /full/path/to/processed.xtc
  input_trajectory: /full/path/to/input.xtc
  atom_order_reference: /full/path/to/system.tpr
  output_selection: System
  processing:
    # only conditions relevant to reuse
```

`processing` 按实际处理内容记录影响 reuse 的信息，例如 PBC/center/fit、`dt`、time range 等；不要求所有 trajectory 使用完全相同字段。

### 8.2 `ndx_index.yaml`

维护者：`make_ndx` Skill/Tool。

Stage 5 main Skill 只查询、核验和使用，不负责生成 `.ndx`、决定其存放位置或登记索引。

最小结构固定为：

```yaml
- path: /full/path/to/analysis.ndx
  tpr: /full/path/to/reference.tpr
```

不在索引中复制 `.ndx` 已经保存的 group 名、group definition 或 atom indices。

`.ndx` reuse 判断当前冻结为：

```text
current tpr == indexed tpr
→ 可复用

different tpr
+ 两份 tpr 所属 run unit 在 04_md_simulation/run_unit.yaml 中记录同一个 top
→ 可复用

different top
→ 不复用
```

默认不追加 atom count / atom ordering 的第二层核验。

Stage 5 只消费 Stage 4 current run-unit topology lineage；Stage 4 如何维护该字段由 Stage 4 自己的 current Skill/freeze 拥有。

## 9. Validation ownership

Stage 5 不设置统一 Validator layer，也不要求 Stage 5 main Skill 重新验证所有具体能力输出。

各 concrete capability owner 对自己的输出负责 validation，例如：

```text
trjconv    → 自己生成的 trajectory
make_ndx   → 自己生成的 ndx
RMSD Skill → RMSD 执行及输出
RDF Skill  → RDF 执行及输出
...
```

Stage 5 main Skill 只负责 planning/orchestration 层一致性。只有对应 capability owner 确认输出有效后，相关 plan item 才进入 `已完成`，其关键正式产物才按需写入 `results`。

## 10. Project result registration

Stage 5 在 `project_result_index.md` 中登记到“分析事项”粒度：

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

Task Sheet 中的 `results` 是当前 item 的直接恢复/依赖入口；`project_result_index.md` 仍只承担跨任务正式结果检索，不要求把每个 item 的全部 `results` 内容复制成 project-level 明细。

不把每个 `.xvg/.csv/.dat/.png/.xtc/.ndx` 单独复制成 project-level 结果索引项。

是否额外汇总多个分析结果、进行综合解释或生成报告，由当前用户任务决定，不是 Stage 5 main Skill 的固定职责。

## 11. Stage completion

Stage 5 可以完成的前提：

- 当前分析目标所需 plan items 已完成，或有明确理由进入 `已终止`；
- 每个 `已完成` item 已通过对应 capability owner 自己的 validation；
- 需要直接恢复或供后续 item 消费的关键正式产物已按需记录在对应 `results`；
- 需要保留的分析事项已经按上述边界登记到 `project_result_index.md`。

## 12. Explicitly rejected defaults

不得默认：

- 为 analysis planning and orchestration 再建立 `5.1` wrapper sub-stage；
- 把 RMSD / RDF / PCA 等拆成 `5.1 / 5.2 / 5.3 / ...`；
- 增加 Structural / Interaction / Conformational 等仅用于分类的中间执行层；
- 为 Stage 5 建立类似 Stage 4 `run_unit.yaml` 的 project-level analysis-unit identity；
- 让 Manager 代替 Stage 5 main Skill 设计具体分析方法组合；
- 让 Stage 5 main Skill 维护 `trjconv` / `make_ndx` 产生文件的生命周期；
- 使用统一 `prepared_input_index.yaml` 同时由多个 producer 维护；
- 用 `source: md.N` 替代最终实际输入文件路径；
- 用单一 `object` 字段承载全部分析对象语义；
- 强制所有分析使用统一 `range / dt / target` schema；
- 强制 Stage 5 main Skill 固定进行结果汇总；
- 建立统一 Stage 5 Validator layer；
- 为了旧目录分类把 Stage 5 拆到 `01_workflows/` 和 `02_operations/`；
- 把 Agent 锁进无必要 parser / wrapper / dispatcher 链。

此前以 `5.1 Analysis planning and orchestration` 为 identity 的详细 freeze 已被本 Stage-level freeze 接管，并移入 `00_authoring/archive/stage5_history/` 仅供历史追溯。
