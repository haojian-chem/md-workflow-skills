# Workflow 5 / Stage 5 analysis capability inventory freeze

Status: **FROZEN AUTHORING REFERENCE — NOT AN ACTIVE INVENTORY**

本文件保留 Stage 5 在正式 Skill generation 获批前已经敲定的 analysis capability inventory 设计。它不是 runtime inventory；正式 inventory 只在 Stage 5 Skill generation 获批后创建/启用。

未来正式文件名固定为：

`05_analysis/references/analysis_capability_inventory.yaml`

这里统一使用 **capability**，因为 Stage 5 可发现和调度的能力可以由科研/技术 Skill、确定性 Tool 或其它已登记能力 owner 提供；不能把所有 capability 都抽象成 Skill 或 Tool。

冻结内容：

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

Inventory 只做 capability discovery，不复制具体 capability owner 的方法、命令、selection、preprocessing、validation 或结果生命周期。

Source pre-authorization blob: `12749eadc032daba95685c3fd450af0633613371`.
