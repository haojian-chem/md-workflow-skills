# 渐进披露

Codex 初始依赖 Skill 的 `name`、`description` 和路径判断是否加载完整 Skill，因此 description 必须前置用途、触发词和排除边界。

## 主文件

主 `SKILL.md` 应能快速回答：

- 何时使用；
- 当前 Skill 只做什么；
- 需要哪些输入；
- 何时阻塞或暂停；
- 产生什么输出；
- 读取哪个共享 contract。

## 按需读取 reference

`SKILL.md` 必须说明加载条件，例如：

```text
仅检测到金属离子时读取 references/coordination_detection_registry.yaml。
```

不得要求启动时读取整个 `references/`。

## 规模建议

- Manager：150–300 行；
- Workflow：80–180 行；
- Operation：80–200 行；
- Validator：100–250 行；
- 编写指导 Skill：150–300 行。

超过范围不是自动错误，但必须检查重复、字段表、长示例和职责混入。
