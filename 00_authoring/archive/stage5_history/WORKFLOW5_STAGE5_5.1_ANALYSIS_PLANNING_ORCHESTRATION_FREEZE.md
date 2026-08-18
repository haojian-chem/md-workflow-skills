---
name: analysis
description: Stage 5 — Analysis 主 Skill。指导 Agent 处理 5.1 Analysis planning and orchestration：理解用户分析目标、查询已有可复用分析资源、形成编号化 plan items、选择并调度具体 analysis Skill / prepared-input producer，并维护 Stage 5 结果追溯。
---

# Stage 5 — Analysis

## Purpose

Stage 5 只包含一个 Task Sheet sub-stage：

```text
5.1 Analysis planning and orchestration
```

本 Skill 是 Stage 5 的 main guide。它指导 Agent 如何把用户的分析需求组织成可执行计划，并协调具体分析能力；不把 Agent 锁进固定 parser、固定工具链或额外 dispatcher。

具体 RMSD、RDF、PCA、trajectory preprocessing、index generation 等不是新的 `5.x` sub-stage，而是 5.1 内部 plan items，并由相应 analysis Skill / Tool 自己拥有具体方法和 validation。

详细冻结架构：

`00_authoring/architecture_freezes/WORKFLOW5_STAGE5_ARCHITECTURE_FREEZE.md`

## Responsibility boundary

### Manager

如果任务范围包含 Stage 5，Manager 只负责：

- 在 Task Sheet 中建立 `5.1 Analysis planning and orchestration`；
- 原样记录用户明确提出的分析目标、分析对象和约束；
- 用户明确指定 RMSD、RDF 等方法时原样保留。

Manager 不进一步选择具体分析方法组合、selection、trajectory preprocessing 或 Stage 5 reuse。

### 5.1

5.1 负责：

- 理解当前分析目标；
- 读取 analysis tool inventory；
- 集中查询已有正式分析结果和 prepared-input indexes；
- 做 Stage 5 reuse 核验；
- 将分析目标展开为完整 plan；
- 选择并调度对应 analysis Skill / prepared-input producer；
- 维护 Task Sheet 中编号化 plan items；
- 当执行证据破坏原计划前提时调整后续 plan。

### Concrete analysis Skill / Tool

具体 analysis Skill / Tool 负责自己的方法、执行细节、输出和 validation。

本 Skill 只记录它们的能力接口和调用关系，不重新定义其内部规则。

## Inputs / evidence

进入 5.1 时至少需要理解：

- 当前 Task Sheet 中的 5.1 条目；
- 用户明确的分析目标、对象和约束；
- `references/analysis_tool_inventory.yaml`；
- `project_result_index.md` 中与当前 Stage 5 需求有关的正式分析结果入口；
- 需要 prepared trajectory 时，项目 `05_analysis/indexes/trajectory_index.yaml`（如存在）；
- 需要 `.ndx` 时，项目 `05_analysis/indexes/ndx_index.yaml`（如存在）；
- 解析候选输入所需的实际文件；
- 涉及 Stage 4 TPR/topology lineage 时，项目 `04_md_simulation/run_unit.yaml`。

这些文件可以由 Agent 直接读取理解。除非具体分析方法/Tool 明确需要，不要求先经过额外 parser 才允许判断。

## Analysis capability discovery

能力清单：

`references/analysis_tool_inventory.yaml`

每个实际可用条目至少记录：

```yaml
name:
purpose:
required_files:
skill:
```

其中：

- `name`：Task Sheet plan item 的 `tool` 引用名；
- `purpose`：该能力用于什么分析/处理；
- `required_files`：调用前需要的文件角色与可接受类型；
- `skill`：具体 guide 路径。

Inventory 是**能力发现入口**，不是 parser 或强制 workflow engine。具体方法、命令、selection、preprocessing、validation 由条目指向的 Skill/Tool 自己拥有。

如果当前需要的分析能力不存在于 inventory，不在本 Skill 中临时伪造另一 Skill 的内部规则；应根据任务复杂度决定是直接在当前明确能力范围内处理，还是提出/建立新的 dedicated analysis Skill，并由对应 authoring 过程维护。

## One-pass planning and reuse

5.1 在生成当前完整 Stage 5 plan 时集中做一次资源查询与 reuse 核验：

```text
理解用户分析需求
→ 读取 capability inventory
→ 查询已有正式分析结果
→ 按需查询 trajectory_index.yaml / ndx_index.yaml
→ 判断哪些已有结果/输入可复用
→ 判断缺少哪些 prepared inputs
→ 把当前 Task Sheet 中将由前置 plan item 生成的文件一起纳入考虑
→ 建立完整 plan 和输入用途/依赖
→ 写入 Task Sheet
→ 开始调度执行
```

正常 plan 建立后，不在每个 item 启动前重新进行一轮全局 reuse 查询。

只有以下情况才重新调整尚未完成的后续 plan：

- 前置执行失败；
- 实际生成结果不满足原计划条件；
- 用户修改分析需求；
- 其他证据破坏当前 plan 的前提。

对具体分析结果是否可复用，使用对应 analysis Skill 的科学判据；对 prepared input 是否可复用，使用对应 producer/index 规则。

统一判断：

```text
明确满足 → 复用
明确不满足 → 安排新的分析/producer
信息不足 → 当前 Task Execution Agent 向用户确认
用户明确要求重做/对照 → 跳过自动复用
```

## Plan item model

5.1 在自己的 Task Sheet 条目内追加 plan items。

编号：

```text
1
2
3
...
```

规则：

- 编号只在当前 5.1 内有效；
- 一旦加入，编号固定；
- 原则上不删除、不重编号；
- 不再执行时标记 `已终止`；
- 新增项使用下一个整数。

状态只使用：

```text
未完成
已完成
已终止
```

每项最小结构：

```text
编号
tool
inputs
settings
status
path
```

### `tool`

引用 analysis tool inventory 中的 `name`。

### `inputs`

已有文件写实际完整路径，不用 `source: md.N` 代替具体输入。

如果输入尚未生成但已由当前 plan 前置项负责产生，使用直观描述，例如：

```text
trajectory: 使用第 1 项生成的处理后轨迹
index: 使用第 2 项生成的 ndx 文件
```

不强制 `from_item` / `output_role` schema。

### `settings`

只记录使当前 plan item 足够明确的 tool-specific 设置。

`dt`、time range、reference、selection、fit 要求等是否存在，由当前 analysis Skill / Tool 和实际任务决定；Stage 5 不建立统一固定字段集。

### `path`

记录当前 plan item 相关文件的**完整存放目录**，用于查询和恢复，不指向单个结果文件。

Producer Tool 的实际输出位置由该 producer 的 guide/规则负责；5.1 不替它猜路径。

## Multiple trajectories

一个 plan item 对应一次统一定义的分析。

如果多条 trajectory 作为同一次分析共同处理，且共享关键 settings：

- 可以在一个 item 中记录多条 trajectory；
- 共同 topology/reference 类输入只记录一套；
- 使用同一套 settings。

如果用户要求分别分析，或关键 settings 不同，则拆成多个 plan items。

## Prepared trajectory index

项目索引：

`<project_root>/05_analysis/indexes/trajectory_index.yaml`

维护者：负责产生处理后 trajectory 的 `trjconv` Skill/Tool。

5.1 只负责：

- 查询；
- 根据当前分析要求核验是否可复用；
- 将可用完整路径写入 plan；
- 缺少适用 trajectory 时，在 plan 中安排 `trjconv`。

`trjconv` 自己负责生成、存放、validation 和更新 trajectory index。

当前索引最小方向：

```yaml
- path: /full/path/to/processed.xtc
  input_trajectory: /full/path/to/input.xtc
  atom_order_reference: /full/path/to/system.tpr
  output_selection: System
  processing:
    # only conditions relevant to reuse
```

`processing` 可按实际记录 PBC/center/fit、`dt`、time range 等，不要求所有条目完全同 schema。

## `.ndx` index

项目索引：

`<project_root>/05_analysis/indexes/ndx_index.yaml`

维护者：`make_ndx` Skill/Tool。

5.1 只负责查询、核验、使用；缺少适用 `.ndx` 时在 plan 中安排 `make_ndx`。

最小记录：

```yaml
- path: /full/path/to/analysis.ndx
  tpr: /full/path/to/reference.tpr
```

不在索引中复制 `.ndx` 内部 groups。

Reuse：

```text
current tpr == indexed tpr
→ 可复用

different tpr
+ 两份 tpr 所属 run unit 在 04_md_simulation/run_unit.yaml 中记录 same top
→ 可复用

different top
→ 不复用
```

默认不增加 atom count / atom ordering 的第二层核验。

因此 Stage 4 `run_unit.yaml` 需要记录每个 run unit 实际 `grompp` 使用的主 `.top` 完整路径。

## Validation ownership

Stage 5 不设置统一 validation Skill。

```text
trjconv     → 自己生成的 trajectory
make_ndx    → 自己生成的 ndx
RMSD Skill  → RMSD 执行及输出
RDF Skill   → RDF 执行及输出
...
```

各能力 owner 负责自己的输出 validation。

5.1 只做 planning/orchestration 层核验：

- plan 覆盖当前用户目标；
- 每个 item 的 tool/inputs/settings/依赖足以交给对应能力；
- 编号和状态一致；
- 后续项没有依赖已终止或未产生所需输入的前置项；
- 只有对应 Tool/analysis Skill 确认输出有效后，item 才标记 `已完成`。

5.1 不重新计算或重复验证各工具已经拥有的科学数据 validation。

## Project result registration

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

不把每个 `.xvg/.csv/.dat/.png/.xtc/.ndx` 逐个复制成 project-level 结果项。

## Completion

5.1 可以完成的前提：

- 满足当前用户目标所需 plan items 已完成，或有明确理由进入 `已终止`；
- 每个 `已完成` item 已通过对应 Tool/analysis Skill 自己的 validation；
- 需要保留的分析事项已登记到 `project_result_index.md`。

多分析结果汇总、综合解释或报告生成由当前用户任务决定，不是固定完成条件。

## Explicitly rejected defaults

不得默认：

- 把 RMSD / RDF / PCA 拆成 `5.2 / 5.3 / ...`；
- 增加 Structural / Interaction / Conformational 等仅用于分类的执行层；
- 为 Stage 5 建 project-level analysis-unit identity；
- 让 Manager 代替 5.1 设计具体方法；
- 让 5.1 接管 `trjconv` / `make_ndx` 的文件生命周期；
- 用统一 `prepared_input_index.yaml` 让多个 producer 共同维护；
- 用 `source: md.N` 代替实际输入路径；
- 用单一 `object` 字段承载全部分析语义；
- 强制所有分析使用统一 `range / dt / target` schema；
- 强制 5.1 做结果汇总；
- 为了目录分类再建立 Workflow / Operation / Validator 层；
- 把 Agent 锁进无必要 parser / dispatcher / wrapper 链。
