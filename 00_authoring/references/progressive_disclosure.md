# 渐进披露

Status: CURRENT

主 `SKILL.md` 的目标是让 Agent 快速理解并推进当前职责，而不是在启动时加载全部细节。

## 1. 主文件应回答什么

主 `SKILL.md` 应能快速回答：

- 何时使用；
- 当前目标是什么；
- 当前 Skill 拥有什么、不拥有什么；
- 需要哪些输入/证据；
- reuse 怎么判断；
- 执行时有哪些必须遵守的规则；
- 怎样 validation；
- results 是什么；
- 什么情况下需要进一步读取 reference / supporting Skill / Tool guide。

## 2. Reference 按需读取

长规则、registry、数据表和条件性细节放 `references/`。

主 Skill 应说明加载条件，例如：

```text
检测到金属配位问题时，再读取 references/coordination_rules.md
```

复杂正式结果的详细接口说明也是渐进披露对象。结果包含多个正式文件、结构化字段、复杂定位关系或会被后续 Skill 直接查阅时，优先把详细结果说明放到：

```text
references/results.md
```

main `SKILL.md` 只保留正式结果摘要、入口和必要完成条件，并说明需要解释详细结果格式 / 字段时读取该文件。其它 Skill 如果只需要定位和解释上游结果，可以按需读取该 `results.md`，不必为此加载完整上游执行规则。

科研执行 Skill 共用的 validation、结果生成、结果内部 `references`、路径和 project-result registration 规则见仓库级 execution shared reference：

`../../references/result_generation_rules.md`

不得要求启动时默认扫描整个 `references/`。

## 3. Supporting Skill 的拆分条件

不要按 Workflow / Operation / Validator 类型拆文件。

只有一块内容：

- 足够复杂；
- 边界清晰；
- 可以独立加载；
- 有独立复用或测试价值；

才拆成 supporting Skill。

如果只是主 Skill 中的一段较长说明，优先 reference，而不是新 Skill。

## 4. 避免假性渐进披露

以下不算有效渐进披露：

```text
main Skill
→ 强制 dispatcher Skill
→ 强制 parser Skill
→ 才能读取实际文件
```

这只是增加 hop。

有效方式是：

```text
Agent 先读 main Skill
→ 只有当前任务真的需要时再读对应 detail/reference/supporting Skill
```

## 5. 规模判断

不再按 Workflow / Operation / Validator 给固定行数配额。

当主 Skill 明显过长时，优先检查：

1. 是否复制了其他 Skill 的内容；
2. 是否把长数据/registry 放错位置；
3. 是否包含大量示例；
4. 是否把 Tool 接口实现细节写进主 Skill；
5. 是否把复杂 results 的完整字段 / report format 留在 main Skill，而不是按需下放到 `references/results.md`；
6. 是否存在真正复杂且可独立加载的 supporting responsibility。

长度本身不是拆 Skill 的充分理由；职责边界和按需加载收益才是。
