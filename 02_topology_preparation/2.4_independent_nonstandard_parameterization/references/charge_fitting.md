# 2.4 电荷拟合

## 电荷拟合对象

电荷拟合对象为代表实例的完整参数化模型。

参数化模型的总电荷已经在量化计算前根据当前实际化学状态确定。2.4 的 RESP / RESP2 以该完整分子的总电荷为电荷总和依据，不建立 2.3 针对 `charge_modification_scope` 的无约束 / 有约束并行拟合与候选结果比较。

当前 RESP / RESP2 拟合使用 Multiwfn。

## SP 计算

SP 计算在几何优化后的代表实例结构上进行。

SP 默认采用比 OPT 高一级的计算水平；具体方法、基组和其它设置根据当前分子与参数化要求确定并记录。默认读取 OPT 波函数作为初始猜测。

### RESP

采用 RESP 时，在同一个几何优化后结构上进行一次 SP 计算。该 SP 根据当前 RESP / 参数化方案采用气相或隐式溶剂模型。

### RESP2

采用 RESP2 时，在同一个几何优化后结构上分别进行：

```text
气相 SP
隐式溶剂 SP
```

两次 SP 分别提供后续气相 RESP 与隐式溶剂 RESP 所需结果。

### SP 检查

每个用于电荷拟合的 SP 结果至少检查：

- `<S²>`；
- OPT 与该 SP 原子自旋布居差异的 `MAE`、`RMSE` 和 `L_inf`。

用于后续 Multiwfn 拟合的 SP 结果文件 / 波函数文件应保留，并记录在 `charge_fitting_result.yaml`。

## RESP

根据当前采用的两阶段 RESP 方案，对对应 SP 结果完成一次完整的两阶段 RESP 拟合，并使最终原子电荷总和符合代表实例参数化模型已经确定的分子总电荷。

至少记录：

```text
Q_expected
Q_fitted
DeltaQ
```

其中：

- `Q_expected`：代表实例参数化模型已经确定的分子总电荷；
- `Q_fitted`：最终 RESP 原子电荷总和；
- `DeltaQ`：`Q_fitted - Q_expected`。

保存实际 RESP `.chg` 结果文件。

## RESP2

RESP2 使用同一个几何优化后结构上的气相 SP 与隐式溶剂 SP 分别完成两阶段 RESP，再按当前 RESP2 权重组合对应原子电荷。

气相 RESP 与隐式溶剂 RESP 均以代表实例已经确定的同一个分子总电荷为电荷总和依据。

对应气相 / 隐式溶剂 RESP 原子电荷按实际采用的 RESP2 权重组合。默认采用气相与隐式溶剂等权混合，即 `0.5 / 0.5`。

除分别记录气相和隐式溶剂 RESP 的 `Q_expected / Q_fitted / DeltaQ` 外，额外比较两套 RESP 逐原子电荷差异：

```text
MAE
RMSE
L_inf
```

生成实际采用权重组合后的 RESP2 `.chg`，并记录组合结果的：

```text
Q_expected
Q_fitted
DeltaQ
```

## `charge_fitting_result.yaml`

电荷拟合生成：

```text
charge_fitting_result.yaml
```

该文件至少记录：

- 实际 SP 结果文件 / 波函数文件；
- 实际采用的拟合软件、RESP / RESP2 方法及拟合设置；
- RESP2 采用时的实际混合权重；
- 实际产生并用于最终结果的 RESP / RESP2 `.chg` 文件；
- SP 与电荷拟合检查结果；
- 最终被选中用于生成 `parameterization.chg` 的实际 `.chg` 文件。

采用 RESP 而非 RESP2 时，只记录实际存在的 SP、RESP 结果与检查，不生成未执行的 RESP2 空字段。

## `parameterization.chg`

根据检查通过并被选中的实际电荷结果生成：

```text
parameterization.chg
```

`parameterization.chg` 保存最终供 Sobtop 参数化使用的代表实例原子电荷，并与 `parameterization_model.mol2` 已经确定的原子顺序保持可确定的一一对应。
