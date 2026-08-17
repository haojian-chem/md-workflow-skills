# 多窗口编写启动检查

Status: CURRENT

只有以下项目全部通过，才适合把某个 Skill 交给独立网页窗口。

## 当前架构

- [ ] 已读取 `00_authoring/AUTHORING_RULES.md`；
- [ ] 已读取 current `SYNC_STATUS.md`；
- [ ] 已确认当前 Skill 使用 main-Skill + on-demand supporting/reference 模型；
- [ ] 未要求 Workflow / Operation / Validator 强制分类；
- [ ] 未把 Agent 锁进 Legacy Workstream / route / event / transaction runtime；
- [ ] 已明确 Skill 是指导 Agent 处理任务，不是 parser/workflow gate。

## 目标 Skill

- [ ] 当前 main responsibility 已确认；
- [ ] 当前 Skill 的 input/evidence、reuse、execution、validation、handoff 已有清楚边界；
- [ ] supporting Skill 仅在复杂且边界清晰时拆分；
- [ ] content map 已确认；
- [ ] `write_paths` 已确认且无重叠。

## 读取上下文

- [ ] 已读取直接上游 Skill；
- [ ] 已读取直接下游 Skill；
- [ ] 已读取当前输入/输出依赖的 supporting Skill / Tool guide；
- [ ] 已检查相邻职责是否存在重复或冲突；
- [ ] 已理解：读取外部 Skill 不等于拥有修改权或定义权。

## 写入所有权

- [ ] 当前窗口只修改分配的 `write_paths`；
- [ ] 共享 authoring/index/architecture 文件仍由 main window 修改；
- [ ] 未通过“在自己 Skill 中复制外部规则”规避 ownership；
- [ ] 如果发现外部 Skill 需要修改，准备提交 cross-skill finding / handoff。

## Rule ownership / 去重

新增或修改规则前使用：

`references/content_ownership_and_deduplication.md`

- [ ] 每条新增规则都确认属于当前 Skill 自己的职责；
- [ ] 外部已有 owner 的规则只引用，没有复制或改写成第二份规范；
- [ ] 外部规则缺失/冲突时记录 finding，没有在当前 Skill 临时补一份；
- [ ] 当前 Skill 对外部 Skill 只保留必要的 `consume / require / handoff`；
- [ ] 不存在以后修改一条规则必须同步更新多个 owner 文件的情况；
- [ ] 没有形成 shadow specification。

## Parser / Tool 检查

- [ ] 没有把本可直接读取的输入强制经过 parser 才允许 Agent 理解；
- [ ] 没有为了形式化增加无必要 schema/dispatcher；
- [ ] 推荐 Tool 与强制科学方法已经区分；
- [ ] 只有确定性、重复、稳定、可测试的动作才优先 Tool 化。

## 内容归属

- [ ] 当前 Skill 没有定义其他 Skill 的内部步骤；
- [ ] 当前 Skill 没有定义其他 Skill 的默认参数；
- [ ] 当前 Skill 没有定义其他 Skill 的 validation / official results；
- [ ] 外部 Skill 只以接口/正式结果/能力形式被引用；
- [ ] 长但仍属于当前 Skill 的内容优先放 reference，而不是无必要拆 Skill。

## 交付前四问

- [ ] 我是否写了其他环节“应该怎么做”？
- [ ] 我是否复制或改写了另一个 owner 已经定义的规则？
- [ ] 是否存在同一规则需要多个文件同步维护？
- [ ] 外部内容是否可以进一步缩成接口引用而不重复其内部实现？

任一答案为“是”时，先解决越界/重复，再交付当前 Skill。

## 启动前回顾

- [ ] 已列出 `已做过 / 已否定 / 仍未验证`；
- [ ] 没有重新引入已经明确否定的架构；
- [ ] 当前窗口清楚自己的交付范围和 cross-skill findings 交接方式。
