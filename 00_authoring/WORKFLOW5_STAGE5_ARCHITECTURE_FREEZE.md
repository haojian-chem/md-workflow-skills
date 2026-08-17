# Workflow 5 / Stage 5 architecture freeze

Status: FROZEN — GUIDE IMPLEMENTED, TOOL-SPECIFIC DETAILS PENDING

本文件记录 Stage 5 — Analysis 的冻结架构。Stage 5 的具体分析方法、`trjconv` / `make_ndx` 等工具内部规则与各工具 validation 由相应 Skill/Tool 后续独立维护；本文件不提前固定这些方法细节。

## 1. Stage 5 catalog

Stage 5 名称固定为：

```text
5 Analysis
```

Stage 5 只设置一个 sub-stage：

```text
5.1 Analysis planning and orchestration
```

Stage 5 继续采用普通 Task Sheet sub-stage 模式，不采用 Stage 4 的 project-level run-unit 模型。

## 2. Manager / 5.1 responsibility boundary

Manager 只负责：

- 判断当前任务范围是否包含 Stage 5；
- 在初始 Task Sheet 中建立 `5.1 Analysis planning and orchestration`；
- 原样记录用户明确提出的分析目标、分析对象和约束；
- 用户明确指定 RMSD、RDF 等方法时可以原样保留这些要求。

Manager 不负责：

- 把“结构稳定性”“相互作用变化”等研究目标自行展开成具体分析方法组合；
- 选择具体 analysis Skill / Tool；
- 查询 Stage 5 reuse；
- 决定 trajectory / ndx 的具体处理方式。

5.1 负责：

- 理解当前分析目标；
- 读取 analysis tool inventory；
- 集中查询当前已有可复用分析结果和 prepared inputs；
- 做 Stage 5 reuse 核验；
- 将分析目标展开为完整的 Stage 5 plan；
- 选择并调度对应 analysis Skill / prepared-input producer；
- 维护 Task Sheet 中 5.1 内部的 plan items；
- 当执行证据破坏原计划前提时调整后续 plan。

核心边界：

```text
Manager
→ 记录“用户要分析什么”

5.1
→ 决定“本任务具体做哪些分析、需要哪些输入、如何组织这些分析”

analysis Skill / Tool
→ 提供对应分析方法或确定性处理本身的科学/执行指导，并负责自己输出数据的 validation
```

## 3. One-pass Stage 5 planning

5.1 在进入 Stage 5 时集中完成一次当前资源查询、reuse 核验和整体规划：

```text
read Task Sheet Stage 5 requirement
→ read analysis tool inventory
→ query existing formal analysis results
→ query trajectory_index.yaml / ndx_index.yaml when relevant
→ determine reusable inputs/results
→ determine missing prepared inputs
→ include trjconv / make_ndx or other required producers in the same plan
→ pre-assign intended use/dependency of their future outputs
→ write the complete current plan into Task Sheet
→ execute the plan
```

正常执行过程中，不为每个后续 plan item 重新进行一轮全局 reuse 查询。

如果前置执行失败、实际产物不满足规划条件、用户修改分析要求或其他证据破坏当前 plan 的前提，5.1 才重新调整尚未完成的后续 plan。

## 4. Plan item model

5.1 在自己的 Task Sheet 条目内追加编号化 plan items。

编号规则：

- 使用当前 5.1 内部的局部整数编号 `1, 2, 3, ...`；
- 不使用 `5.1.1`、`analysis.1` 等 Workflow/project-level identity；
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

每个 plan item 的最小结构为：

```text
编号
tool
inputs
settings
status
path
```

字段语义：

- `tool`：直接引用 analysis tool inventory 中的条目名；
- `inputs`：当前项目实际消费的输入；已有文件记录完整文件路径；
- `settings`：tool-specific 的当前任务设置，不建立 Stage 5 通用子 schema；
- `status`：`未完成 / 已完成 / 已终止`；
- `path`：该 plan item 相关文件的完整存放目录，用于后续查询定位，不指向单个结果文件。

如果某个输入尚未生成，但已经由当前 plan 中的前置项目负责产生，使用直观描述记录依赖，例如：

```text
trajectory: 使用第 1 项生成的处理后轨迹
index: 使用第 2 项生成的 ndx 文件
```

不要求额外建立 `from_item` / `output_role` 等专门 schema。

## 5. Multiple trajectories / grouped analyses

一个 plan item 对应一次统一定义的分析。

如果多条 trajectory 作为同一次分析共同处理：

- 可以在一个 plan item 中记录多条 trajectory；
- 共同 topology/reference 类输入只记录一套；
- 共用一套当前分析 settings。

如果用户要求分别分析，或不同输入需要不同关键 settings，则拆成多个 plan items。

最终 `inputs` 记录解析后的实际文件路径，不用单独的 `source: md.N` 代替具体输入。`md.N` 等逻辑对象只可作为 5.1 查找实际文件时的线索。

## 6. Analysis tool inventory

5.1 使用静态 inventory：

```text
02_operations/analysis_planning_and_orchestration/references/analysis_tool_inventory.yaml
```

inventory 是能力发现入口，不是新的调度层。

每个实际可用条目至少记录：

```yaml
name:
purpose:
required_files:
skill:
```

`required_files` 记录“文件角色 + 可接受文件类型”，不绑定具体项目文件名。可以在执行中生成的辅助文件不应仅因为可能需要就被写成 hard required file。

inventory 不复制具体 analysis Skill 的方法、命令、selection、预处理或 validation 细节。

## 7. Prepared-input indexes

项目级 Stage 5 索引目录固定为：

```text
<project_root>/05_analysis/indexes/
├── trajectory_index.yaml
└── ndx_index.yaml
```

### 7.1 `trajectory_index.yaml`

维护者：负责产生处理后 trajectory 的 `trjconv` Tool/Skill。

5.1 只查询、核验和使用，不负责生成 trajectory、决定其存放位置或登记索引。

当前最小记录方向：

```yaml
- path: /full/path/to/processed.xtc
  input_trajectory: /full/path/to/input.xtc
  atom_order_reference: /full/path/to/system.tpr
  output_selection: System
  processing:
    # only processing conditions relevant to reuse
```

`processing` 按实际处理内容记录影响 reuse 的信息，例如 PBC/center/fit、`dt`、time range 等；不要求所有 trajectory 使用完全相同字段。

### 7.2 `ndx_index.yaml`

维护者：`make_ndx` Tool/Skill。

5.1 只查询、核验和使用，不负责生成 `.ndx`、决定其存放位置或登记索引。

最小结构固定为：

```yaml
- path: /full/path/to/analysis.ndx
  tpr: /full/path/to/reference.tpr
```

不在索引中复制 `.ndx` 已经保存的 group 名、group definition 或 atom indices。

`.ndx` reuse 判断：

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

Stage 4 的 `run_unit.yaml` 因此必须记录每个 run unit 实际用于 `grompp` 的主 `.top` 完整路径。

## 8. Tool / analysis Skill validation ownership

Stage 5 不设置统一 Validator sub-stage，也不要求 5.1 重新验证所有工具输出的数据有效性。

各工具/analysis Skill 对自己的输出负责 validation，例如：

```text
trjconv   → 自己生成的 trajectory
make_ndx  → 自己生成的 ndx
RMSD Skill → RMSD 执行及输出
RDF Skill  → RDF 执行及输出
...
```

5.1 只负责计划层一致性：只有对应工具工作完成并通过自身 validation 后，相关 plan item 才能进入 `已完成`。

## 9. Project result registration

Stage 5 在 `project_result_index.md` 中登记到“分析事项”粒度：

```text
对哪些对象
→ 做了哪些分析
→ 详细记录入口
```

详细记录入口应能追溯到对应 Task Sheet / 5.1 plan item，并进一步定位：

```text
tool
inputs
settings
status
path
```

不把每个 `.xvg/.csv/.dat/.png/.xtc/.ndx` 单独复制成 project-level 结果索引项。

是否进行多分析结果汇总、综合解释或生成报告由当前用户任务决定，不是 5.1 的固定职责。

## 10. Stage completion

5.1 可以完成的前提是：

- 当前 Task Sheet 中为满足用户分析目标所需的 plan items 已完成，或有明确理由进入 `已终止`；
- 每个 `已完成` item 已通过对应工具/analysis Skill 自己的 validation；
- Stage 5 需要保留的分析事项已经按上述边界登记到 `project_result_index.md`。

## 11. Explicitly rejected structures

默认不得：

- 把 RMSD / RDF / PCA 等分析方法拆成 `5.2 / 5.3 / ...`；
- 增加 Structural / Interaction / Conformational 等仅用于分类的中间执行层；
- 为 Stage 5 建立类似 Stage 4 `run_unit.yaml` 的 project-level analysis-unit identity；
- 让 Manager 代替 5.1 设计具体分析方法组合；
- 让 5.1 自己维护 `trjconv` / `make_ndx` 产生文件的生命周期；
- 使用一个统一 `prepared_input_index.yaml` 同时由多个 producer 维护；
- 用 `source: md.N` 替代最终实际输入文件路径；
- 用单一 `object` 字段承载全部分析对象语义；
- 强制所有分析使用统一的 `range / dt / target` schema；
- 强制 5.1 固定进行结果汇总；
- 建立统一 Stage 5 Validator layer。
