# Workflow 5 / Stage 5 analysis capability inventory freeze

Status: **FROZEN AUTHORING REFERENCE — NOT AN ACTIVE INVENTORY**

本文件保留 Stage 5 在正式 Skill generation 获批前已经敲定的 analysis capability inventory 设计。它不是 runtime inventory；正式 inventory 只在 Stage 5 Skill generation 获批后创建/启用。

未来正式文件名固定为：

`05_analysis/references/analysis_capability_inventory.yaml`

这里统一使用 **capability**，因为 Stage 5 可发现和调度的能力可以由科研/技术 Skill、确定性 Tool 或其它已登记能力 owner 提供；不能把所有 capability 都抽象成 Skill 或 Tool。

首批 Stage 5 capability 的 authoring / implementation 集合固定为：

```text
trjconv
trjcat
make_ndx
rmsd
rmsf
hbond
rdf
```

其中 `trjconv` 与 `trjcat` 是独立 capability：`trjconv` 负责单轨迹转换/处理，`trjcat` 负责多轨迹拼接；不把 `trjcat` 作为 `trjconv` 的内部命令步骤隐藏。

这些名称定义首批需要为 Stage 5 准备的能力集合，但并不因为写入本 freeze 就自动成为 active inventory entry。只有对应 capability 的实际 `entry` 已形成并可引用时，才能把该条目加入正式 inventory。

冻结的 inventory 结构：

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

`trjconv` / `trjcat` 产生的正式 processed/concatenated trajectory 如需进入集中 trajectory 管理，由对应 capability owner 的 Skill / README 定义其产物与登记规则；Stage 5 inventory 只负责发现 capability entry，不在这里复制 `trajectory_index.yaml` 的具体写入规则。

如果当前需求没有合适的已登记 capability，这只是 capability gap，不产生虚构 inventory entry。具体缺失方法如何完成由用户与 Agent 在 Stage 5 Skill 责任之外处理；相关未覆盖需求可按 Stage 5 architecture freeze 的边界保留在 Task Sheet 的 Stage 5 plan items 区域之外。

“从已完成的 capability gap 流程中记录/学习经验，并据此补充 capability”保留为未来更新方向；**本次 Stage 5 设计不实现该学习/补充机制**。当前只有在另行完成 capability authoring、形成实际可引用的 `entry` 后，才可把该 capability 加入 inventory。

Source pre-authorization blob: `12749eadc032daba95685c3fd450af0633613371`.