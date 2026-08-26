# Workflow 2 Stage 2 — 2.3 电荷拟合科学规则冻结

Status: CURRENT AUTHORING REFERENCE

本文件保存 `2.3 Topology-linked nonstandard parameterization` 中已经敲定的电荷拟合科学规则，作为后续正式 Skill generation 时“电荷拟合并生成 `parameterization.chg`”环节的详细 authoring input。

量化计算主线与 2.3 环节结构、正式结果记录读取：

`WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_FREEZE.md`

## 1. 电荷拟合对象与输入

电荷拟合使用当前参数化模型以及相应的静电势数据。

本次需要在最终拓扑中采用 2.3 新电荷的真实 residue 集合由当前 2.3 的 `charge_modification_scope` 确定。

`Q_expected` 使用当前体系信息中已经确定的该电荷修改范围预期总电荷；不在电荷拟合环节重新推断该化学状态的总电荷。

实际采用的 RESP / RESP2 方案及其具体设置应与当前选定的力场和参数化框架相适应，并记录实际使用的拟合设置。

## 2. 电荷拟合所需 SP 任务

SP 任务由当前采用的电荷拟合策略确定，并在几何优化后的参数化模型结构上执行，用于获得对应的静电势数据。

### 2.1 RESP

采用 RESP 时，按当前所选 RESP / 力场参数化方案要求设置用于 RESP 电荷拟合的 SP 任务，并获得相应静电势数据。

### 2.2 RESP2

采用 RESP2 时，在同一个几何优化后结构上分别设置：

```text
gas-phase SP
solvent-phase SP
```

分别获得气相和溶剂环境下的静电势数据，用于后续两套 RESP fitting。

## 3. RESP

采用 RESP 时：

1. 使用相应 SP 计算得到的静电势数据进行 unconstrained RESP；
2. 另进行 total-charge constrained RESP，使 `charge_modification_scope` 对应原子的总电荷等于 `Q_expected`；
3. constrained RESP 结果作为后续参数化和最终拓扑电荷更新使用的结果；
4. unconstrained RESP 结果用于对 constrained 结果进行比较和质量判断；
5. 不通过后处理 CAP 电荷重新分配或其它归一化方式改变 constrained RESP 结果。

至少记录：

```text
Q_expected
Q_unconstrained
DeltaQ_unconstrained
Q_constrained
DeltaQ_constrained
MAE
RMSE
L_inf
```

## 4. RESP2

采用 RESP2 时，使用同一个几何优化后结构上得到的气相和溶剂环境静电势数据分别完成对应 RESP fitting。

RESP2 所依赖的每一次 RESP fitting 均按与当前 `charge_modification_scope` 相同的总电荷约束进行 constrained fitting；相应 unconstrained fitting 保留用于比较和质量判断。

完成各自 constrained RESP fitting 后，按实际采用的 RESP2 混合参数得到最终 RESP2 电荷。

RESP2 混合后：

- 不再增加额外的总电荷约束拟合；
- 不做 post-mixing charge normalization；
- 最终结果直接作为后续参数化和最终拓扑电荷更新使用的电荷结果。

## 5. `parameterization.chg`

`parameterization.chg` 保存本次 2.3 电荷拟合后供 Sobtop 参数化使用的原子电荷，并与参数化模型已经确定的 atom order 保持可确定的一一对应。

对于最终体系，只有 `topology_linked_parameterization_result.yaml.charge_modification_scope` 中列出的真实 residue 使用本次 2.3 新电荷；仅作为参数化模型外围环境或 CAP 环境保留的部分不因此成为最终拓扑的电荷修改对象。

## 6. 向 2.5 的交付语义

2.3 在 `topology_linked_parameterization_result.yaml` 中登记：

- `parameterization.chg`；
- `charge_modification_scope`。

2.5 使用这两项信息定位需要更新的最终原子并应用 2.3 已完成的电荷拟合结果；2.5 不重新执行 RESP / RESP2，不重新确定 `charge_modification_scope`，也不对 2.3 电荷结果做额外归一化。
