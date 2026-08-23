# 1.2 可选确定性辅助工具

1.2 的科学检查由 Agent 依据 `../SKILL.md` 与 `../references/classification_rules.md` 直接完成。本目录不提供固定分类、CCD 解析、缺失残基、共价连接、金属配位或最终结果构建 pipeline。

当前只保留：

```text
selection_identity.py
```

它只负责已经确定科学语义后的稳定身份物化：

```text
residue_id
component_id
endpoint_id
relation_id
```

该脚本只使用 Python 标准库，不读取 CCD、力场、结构文件或项目关系定义，也不进行分类、几何判断或用户确认。

Agent 可以在需要确保跨结果身份格式完全一致时调用或导入该 helper；如果当前环境不能直接运行它，但 Agent 能可靠物化满足当前 schema 与 identity rules 的同一类稳定身份，不因 helper 不可用而阻断 1.2 科学检查。

正式结果字段、问题类型和 reference provenance 仍由 `../schemas/` 与 `../references/result_recording_rules.md` 约束，不能以 helper 输出替代 1.2 validation。
