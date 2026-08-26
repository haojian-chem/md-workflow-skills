# Workflow 2 Stage 2 — 2.3 几何优化固定原子规则冻结

Status: CURRENT AUTHORING REFERENCE

本文件保存 `2.3 Topology-linked nonstandard parameterization` 中几何优化阶段已经敲定的固定原子科学规则。

参数化模型建立规则读取：

`WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_CONSTRUCTION_FREEZE.md`

2.3 环节结构及量化计算主线读取：

`WORKFLOW2_STAGE2_2.3_PARAMETERIZATION_MODEL_FREEZE.md`

## 1. 一般规则

几何优化时，对因模型截取或外围环境缺失而需要保留原有空间约束的原子固定其坐标，以避免参数化模型边界或外围基团发生由环境缺失导致的明显非物理松弛，同时保留需要描述的局部化学结构进行优化的自由度。

## 2. 已确定的体系规则

### 2.1 蛋白质体系

固定封端甲基所对应的边界 Cα；封端新增 H 不固定。

### 2.2 HEM

固定 HEM 两个羧基取代基上的 4 个 O 原子。

## 3. 尚未敲定

核酸体系的固定原子范围尚未敲定。
