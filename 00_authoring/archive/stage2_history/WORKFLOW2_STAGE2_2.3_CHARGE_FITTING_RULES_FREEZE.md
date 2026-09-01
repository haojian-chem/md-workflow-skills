# Workflow 2 Stage 2 — 2.3 电荷拟合科学规则冻结

Status: CURRENT AUTHORING REFERENCE

本文件保存 `2.3 Topology-linked nonstandard parameterization` 中已经敲定的电荷拟合科学规则，作为后续正式 Skill generation 时“电荷拟合并生成 `parameterization.chg`”环节的详细 authoring input。

量化计算主线与 2.3 环节结构、正式结果记录读取：

`WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_FREEZE.md`

## 1. 电荷拟合对象与输入

电荷拟合对象为当前参数化模型。

本次需要在最终拓扑中采用 2.3 新电荷的真实 residue 集合由当前 2.3 已经确定的 `charge_modification_scope` 给出；电荷拟合环节读取并使用该范围，不重新确定范围。

`Q_expected` 表示 `charge_modification_scope` 所覆盖真实 residue 在当前化学状态下应具有的预期总电荷。根据当前体系组成、质子化状态、拓扑连接及已经确认的化学状态进行判断；现有信息不能唯一确定时，向用户确认。

当前 RESP / RESP2 拟合使用 Multiwfn。其它拟合方法或软件不作为当前已冻结主路径。

## 2. 电荷拟合所需 SP 计算

SP 计算在几何优化后的参数化模型结构上进行，用于获得当前电荷拟合所需结果。

SP 默认采用比 OPT 高一级的计算水平，具体方法、基组和其它设置根据当前体系与参数化要求确定并记录。默认读取 OPT 波函数作为初始猜测。

### 2.1 RESP

采用 RESP 时，在同一个几何优化后结构上进行一次 SP 计算。该 SP 根据当前 RESP / 参数化方案采用气相或隐式溶剂模型。

### 2.2 RESP2

采用 RESP2 时，在同一个几何优化后结构上分别进行：

```text
gas-phase SP
implicit-solvent SP
```

两次 SP 分别提供后续气相 RESP 与隐式溶剂 RESP 所需结果。

### 2.3 SP 检查

每个用于电荷拟合的 SP 结果至少检查：

- `<S²>`；
- OPT 与该 SP 原子自旋布居差异的 `MAE`、`RMSE` 和 `L_inf`。

用于后续 Multiwfn 拟合的 SP 结果文件 / 波函数文件应保留，并记录在 `charge_fitting_result.yaml`。

## 3. RESP

每个 RESP 使用同一个对应 SP 结果分别完成两次完整的 two-stage RESP fitting：

```text
without charge_modification_scope total-charge constraint
with charge_modification_scope total-charge constraint toward Q_expected
```

两次拟合除是否施加上述总电荷约束外，采用相同的 RESP 拟合方案与其它拟合设置。

有总电荷约束的 two-stage RESP 以 `Q_expected` 为目标；最终结果是否与 `Q_expected` 完全一致不预设，通过实际拟合后的总电荷检查记录。

每个 RESP 至少记录：

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

其中：

- `Q_unconstrained` / `Q_constrained`：两套最终原子电荷在 `charge_modification_scope` 上的总电荷；
- `DeltaQ_unconstrained` / `DeltaQ_constrained`：相对 `Q_expected` 的偏差；
- `MAE`、`RMSE`、`L_inf`：两套完整 two-stage RESP 最终逐原子电荷之间的差异。

两次 RESP 均生成各自的 `.chg` 结果文件。采用哪套结果进入后续参数化由执行 Agent 根据当前检查结果与参数化要求判断，不在本 freeze 中固定。

## 4. RESP2

RESP2 由同一个几何优化后结构上的气相 SP 和隐式溶剂 SP 分别进行 RESP，再按权重组合对应电荷结果。

### 4.1 四次 RESP

气相和隐式溶剂各自均按第 3 节完成两次完整的 two-stage RESP fitting：

```text
gas phase
├─ unconstrained two-stage RESP
└─ constrained two-stage RESP

implicit solvent
├─ unconstrained two-stage RESP
└─ constrained two-stage RESP
```

因此 RESP2 共保留四个 RESP `.chg` 结果文件，并分别完成对应 RESP 检查。

### 4.2 气相 / 隐式溶剂拟合约束一致性

参与同一组 RESP2 混合的气相和隐式溶剂 RESP 必须使用一致的电荷拟合约束设置：

```text
gas unconstrained RESP
+
implicit-solvent unconstrained RESP
→ unconstrained RESP2

gas constrained RESP
+
implicit-solvent constrained RESP
→ constrained RESP2
```

有约束组合中，两次 RESP 对 `charge_modification_scope` 使用相同的目标 `Q_expected`。不得将气相 unconstrained 与隐式溶剂 constrained，或气相 constrained 与隐式溶剂 unconstrained 交叉混合。

### 4.3 RESP2 混合

对应气相 / 隐式溶剂 RESP 原子电荷按实际采用的 RESP2 权重组合。默认采用气相与隐式溶剂等权混合，即 `0.5 / 0.5`。

分别生成：

```text
unconstrained RESP2 .chg
constrained RESP2 .chg
```

采用哪套 RESP2 结果进入后续参数化由执行 Agent 根据当前检查结果与参数化要求判断，不在本 freeze 中固定。

### 4.4 RESP2 检查

除气相和隐式溶剂各自已经完成的 RESP 检查外，额外比较：

```text
gas unconstrained RESP ↔ implicit-solvent unconstrained RESP
MAE / RMSE / L_inf

gas constrained RESP ↔ implicit-solvent constrained RESP
MAE / RMSE / L_inf
```

不额外固定 unconstrained RESP2 与 constrained RESP2 两套混合结果之间的逐原子电荷比较。

两套 RESP2 混合结果还分别记录其在 `charge_modification_scope` 上的总电荷及相对 `Q_expected` 的偏差：

```text
Q_unconstrained
DeltaQ_unconstrained
Q_constrained
DeltaQ_constrained
```

## 5. `charge_fitting_result.yaml`

电荷拟合环节生成独立正式结果文件：

```text
charge_fitting_result.yaml
```

该结果文件至少记录：

- 实际 SP 结果文件 / 波函数文件；
- 实际采用的拟合软件、RESP / RESP2 方法及拟合设置；
- RESP2 采用时的实际混合权重；
- 各次 RESP 产生的 `.chg` 文件；
- RESP2 采用时生成的两套 RESP2 `.chg` 文件；
- 第 2–4 节规定的检查结果；
- 最终被选中用于生成 `parameterization.chg` 的实际 `.chg` 文件。

结果文件和依赖文件路径按仓库级 `references/task_execution_rules.md` 的正式结果路径规则记录。`references` 可记录当前结果实际依赖的文件，也可定义本结果文件多个字段共同复用的公共绝对路径引用。

RESP2 情况下可采用以下组织方式；实际文件 basename 不在本 freeze 中统一固定：

```yaml
references:
  CHARGE_FITTING_PATH: /absolute/path/to/charge_fitting
  PARAMETERIZATION_MODEL: /absolute/path/to/parameterization_model.mol2
  OPT_RESULT: /absolute/path/to/opt_result

method:
  software: Multiwfn
  fitting_method: RESP2
  resp_scheme: two-stage
  resp2_weights:
    gas_phase: 0.5
    implicit_solvent: 0.5

results:
  sp:
    gas_phase: ${CHARGE_FITTING_PATH}/gas_sp_file
    implicit_solvent: ${CHARGE_FITTING_PATH}/implicit_solvent_sp_file

  resp:
    gas_unconstrained: ${CHARGE_FITTING_PATH}/gas_unconstrained.chg
    gas_constrained: ${CHARGE_FITTING_PATH}/gas_constrained.chg
    implicit_solvent_unconstrained: ${CHARGE_FITTING_PATH}/implicit_solvent_unconstrained.chg
    implicit_solvent_constrained: ${CHARGE_FITTING_PATH}/implicit_solvent_constrained.chg

  resp2:
    unconstrained: ${CHARGE_FITTING_PATH}/resp2_unconstrained.chg
    constrained: ${CHARGE_FITTING_PATH}/resp2_constrained.chg

selected_charge_file: ${CHARGE_FITTING_PATH}/<actual-selected-charge-file>.chg

checks:
  sp:
    gas_phase:
      S^2: <value>
      opt_sp_spin_population:
        MAE: <value>
        RMSE: <value>
        L_inf: <value>
    implicit_solvent:
      S^2: <value>
      opt_sp_spin_population:
        MAE: <value>
        RMSE: <value>
        L_inf: <value>

  resp:
    gas_phase:
      Q_expected: <value>
      Q_unconstrained: <value>
      DeltaQ_unconstrained: <value>
      Q_constrained: <value>
      DeltaQ_constrained: <value>
      constrained_vs_unconstrained:
        MAE: <value>
        RMSE: <value>
        L_inf: <value>
    implicit_solvent:
      Q_expected: <value>
      Q_unconstrained: <value>
      DeltaQ_unconstrained: <value>
      Q_constrained: <value>
      DeltaQ_constrained: <value>
      constrained_vs_unconstrained:
        MAE: <value>
        RMSE: <value>
        L_inf: <value>

  resp2:
    Q_unconstrained: <value>
    DeltaQ_unconstrained: <value>
    Q_constrained: <value>
    DeltaQ_constrained: <value>
    gas_vs_implicit_solvent_unconstrained:
      MAE: <value>
      RMSE: <value>
      L_inf: <value>
    gas_vs_implicit_solvent_constrained:
      MAE: <value>
      RMSE: <value>
      L_inf: <value>
```

采用 RESP 而非 RESP2 时，只记录当前实际存在的 SP、RESP 结果与对应检查，不制造未执行的 RESP2 空字段。

## 6. `parameterization.chg`

执行 Agent 根据当前检查结果与参数化要求选择实际采用的电荷结果；`charge_fitting_result.yaml.selected_charge_file` 记录该实际 `.chg` 文件。

`parameterization.chg` 保存最终供 Sobtop 参数化使用的原子电荷，并与参数化模型已经确定的 atom order 保持可确定的一一对应。

对于最终体系，只有 `topology_linked_parameterization_result.yaml.charge_modification_scope` 中列出的真实 residue 使用本次 2.3 新电荷；仅作为参数化模型外围环境或 CAP 环境保留的部分不因此成为最终拓扑的电荷修改对象。

## 7. 向 2.5 的交付语义

2.3 在 `topology_linked_parameterization_result.yaml` 中登记：

- `parameterization.chg`；
- `charge_fitting_result.yaml`；
- `charge_modification_scope`。

2.5 使用 `parameterization.chg` 与 `charge_modification_scope` 定位需要更新的最终原子并应用 2.3 已完成的电荷拟合结果；2.5 不重新执行 RESP / RESP2，也不重新确定 `charge_modification_scope`。
