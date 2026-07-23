# runtime_schema_validator Validation

日期：2026-07-23

## 验证对象

```text
Tool code blob SHA: 7f22d0419b16bdd5cb6e4a7bcf433da4703ff36b
Test code blob SHA: cfe72649429a616c6581cf1ebd33f0fdc2615349
Tool version: 0.1.0
```

GitHub 中上述两个 blob 的内容被按原样重建到隔离的本地文件系统中执行。没有修改测试逻辑，也没有将未执行结果记为通过。

## 可执行测试

命令：

```bash
pytest -q 04_evals/runtime_schema_validator/test_validate.py
```

结果：

```text
.....                                                                    [100%]
5 passed in 10.02s
```

覆盖：

- FAST 不扫描无关的无效记录；
- FULL 能发现项目范围内的无效记录；
- 缺失直接引用返回 FAIL；
- candidate actual-to-logical path overlay；
- schema hash 变化使 cache 失效；
- warm cache 命中。

正向、负向和 candidate overlay fixtures 均通过，未观察到 negative fixture false PASS。

## 性能基准

环境：

```text
Python 3.13.5
PyYAML 6.0.3
jsonschema 4.26.0
pytest 9.0.2
```

使用两个 synthetic contracts、一个 project state 和一个 Workstream state；每类运行 3 次，记录 Tool 自身返回的 `elapsed_ms`。

```yaml
fast_cold_ms:
  median: 5.977
  min: 5.800
  max: 6.008
fast_warm_ms:
  median: 3.311
  min: 3.229
  max: 3.315
full_warm_ms:
  median: 4.181
  min: 3.836
  max: 4.888
runs_each: 3
```

这些数值是小型 synthetic fixture 的工具级基准，不代表大型真实项目 FULL 扫描耗时；它们证明 schema 校验本身不应以分钟计。

## 发布判定

`runtime_schema_validator` 已满足当前注册表中的激活条件：

- executable fixtures 通过；
- FAST/FULL benchmark 已记录；
- candidate overlay test 通过；
- negative fixtures 未出现 false PASS。

允许将 `runtime_schema_validator` 0.1.0 标记为 `ACTIVE`，作为 FAST/FULL runtime validation 的默认确定性实现。

仍待完成的是 Manager 端到端集成测试；该事项不阻止 Tool 自身成为 ACTIVE，但 Manager 和完整工作流仍保持 draft。