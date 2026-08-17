# Evaluation infrastructure

`evals/` 保存测试、fixtures、validation evidence 和 benchmark；它不是 Scientific Skill root，也不占用 MD Workflow Stage 编号。

当前目录中仍可能保留尚未迁移完的 Legacy eval suites。只有与 current Skill / Tool 接口已经同步并通过验证的 suite 才能作为 current acceptance evidence。

新增测试按实际 owner / capability 组织，例如：

```text
evals/<skill-or-tool-name>/
```

Legacy runtime/tool 测试后续按其 owner 迁移或归档，不应因为位于 `evals/` 就被视为 current authority。
