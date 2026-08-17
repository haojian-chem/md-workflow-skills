# Evaluation infrastructure

`evals/` 保存**current** tests、fixtures、validation evidence 和 benchmark；它不是 Scientific Skill root，也不占用 MD Workflow Stage 编号。

当前旧 role/runtime-dependent evaluation suites 已整体归档到：

```text
legacy/evals/
```

因此不得把 `legacy/evals/` 中历史 PASS 当作 current Skill / Tool 的验证证据。

新的 current evaluation 只有在已经同步到当前 Skill / Tool interface 时才进入本目录，例如：

```text
evals/<skill-or-tool-name>/
```

在某个历史 suite 完成 current-interface adaptation 前，宁可暂时不建立 current eval package，也不保留一个路径正确但语义已过期的测试副本。
