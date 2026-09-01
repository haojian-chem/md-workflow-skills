# Workflow 5 / Stage 5 analysis capability inventory freeze

Status: **FROZEN AUTHORING REFERENCE — STAGE 5 IMPLEMENTATION IN PROGRESS**

本文件保留 Stage 5 analysis capability inventory 的 authoring baseline。Stage 5 当前已经存在正式 runtime inventory：

`05_analysis/references/analysis_capability_inventory.yaml`

但 Stage 5 整体 authoring / capability implementation 尚未完成，因此本 freeze 继续保留在 current `architecture_freezes/`，不归档。

已实现部分始终以 current runtime inventory 与对应 capability entry 为准；本 freeze 不覆盖 current implementation。

这里统一使用 **capability**，因为 Stage 5 可发现和调度的能力可以由科研/技术 Skill、确定性 Tool 或其它已登记能力 owner 提供；不能把所有 capability 都抽象成 Skill 或 Tool。

## Current implementation status

当前已经进入正式 inventory 的 capability：

```text
trjconv
trjcat
make_ndx
```

这些条目的 current entry 由正式 runtime inventory 定位。

当前已知仍待后续 authoring / implementation 的分析能力方向包括：

```text
rmsd
rmsf
hbond
rdf
```

这些名称表示当前已知的后续建设方向，不构成 Stage 5 的固定 completion catalog，也不限制未来增加其它分析 capability。Stage 5 是否整体完成由实际建设状态决定，不以完成某一固定列表自动判定。

`trjconv` 与 `trjcat` 保持独立 capability：`trjconv` 负责单轨迹转换/处理，`trjcat` 负责多轨迹拼接；不把 `trjcat` 作为 `trjconv` 的内部命令步骤隐藏。

只有对应 capability 的实际 `entry` 已形成并可引用时，才能把该条目加入正式 runtime inventory；不得为计划中的 capability 建 placeholder entry。

## Inventory structure baseline

正式 runtime inventory 保持轻量 discovery interface：

```yaml
# Stage 5 analysis capability inventory.
#
# This is a discovery aid for the Stage 5 main Skill, not a parser or mandatory
# dispatcher schema. Add an entry only when the referenced capability entry
# exists and is intended to be discoverable by Stage 5.
#
# Minimum fields:
# - name
# - purpose
# - required_files
# - entry
#
# required_files records file roles and acceptable file types; it does not bind
# project-specific file names or duplicate the referenced capability owner's
# execution rules.
[]
```

字段语义：

- `name`：Stage 5 plan item 的 `capability` 引用名；
- `purpose`：能力用途；
- `required_files`：输入角色与可接受文件类型，不绑定项目具体文件名；
- `entry`：该 capability 的实际入口，可指向 Skill guide、Tool 或其它已登记能力入口。

不增加统一 `type: skill/tool/script` 分类字段。Stage 5 只需要能从 `entry` 找到并调用/遵循对应 capability，不为了分类建立额外 schema。

Inventory 只做 capability discovery，不复制具体 capability owner 的方法、命令、selection、preprocessing、validation、结果生命周期或项目级结果登记文件白名单。

各 capability 哪些正式结果文件允许登记到 `project_result_index.md`，由对应 capability owner 在自己的 Skill / README 中定义；inventory 不新增 `registered_files`、`result_whitelist` 等集中字段，也不复制这些文件清单。

## Shared trajectory-management baseline

`trjconv` / `trjcat` 产生的正式 processed / concatenated trajectory 共享同一套集中 trajectory 管理接口。两者拥有同等的 `trajectory_index.yaml` 维护职责：各自只对自己生成并通过 validation、且满足其登记条件的 trajectory 进行登记或更新，不建立独立的 `trjconv` / `trjcat` trajectory indexes。

具体产物、命名、登记前提和写入规则由对应 capability owner 的 current Skill 拥有；Stage 5 inventory 只负责发现 capability entry。

## Capability gap

如果当前分析需求没有合适的已登记 capability，这只是 capability gap，不产生虚构 inventory entry。

缺失 capability 的具体方法设计、实现和 validation 不由 Stage 5 main Skill 临时伪造。相关需求可以保留在当前 Task Sheet 或更大的科研任务上下文中，待后续 capability authoring 完成后，再由实际承载该分析工作的 Task Sheet 按 current Stage 5 规则登记和调用真实 entry。

从实际分析工作中发现新的稳定 capability 需求，可以作为后续 Stage 5 authoring 输入；只有在完成相应 capability authoring、形成真实可引用 entry 后，才更新正式 inventory。

Source pre-authorization blob: `12749eadc032daba95685c3fd450af0633613371`.
