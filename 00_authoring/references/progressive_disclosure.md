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
5. 是否存在真正复杂且可独立加载的 supporting responsibility。

长度本身不是拆 Skill 的充分理由；职责边界和按需加载收益才是。
