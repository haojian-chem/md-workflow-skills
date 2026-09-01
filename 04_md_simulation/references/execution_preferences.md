# Stage 4 execution preferences

Status: CURRENT USER EXECUTION PREFERENCES

本文件记录 Stage 4 本地计算执行时的用户倾向。它不是模拟科学参数规范，也不改变 `.mdp`、run-unit、reuse、continuation 或 validation 的科学语义。

Stage 4 main Skill 在需要生成 / 执行 `gmx_mdrun.sh` 时读取本文件。实际执行时：

1. 先采用当前 Task Sheet / 用户本轮明确指定的执行要求；
2. 没有新的明确要求时，采用本文件中适用于当前运行类别的用户倾向；
3. 当前硬件、GROMACS build、体系或作业环境与某项倾向不兼容时，由执行 Agent 按实际环境调整，不为了机械保持倾向而执行无效命令；
4. 如果调整只影响计算资源和运行方式、不改变科学模拟条件，可以直接调整并记录实际命令；
5. 如果调整会改变当前模拟区段的科学定义，则回到对应 Stage 4 / run-specific Skill 的科学规则处理。

最终实际 `gmx mdrun` 命令始终以当前 run unit 中保存的 `gmx_mdrun.sh` 为准。

## 适用范围

当前倾向的适用范围固定为：

| 执行倾向 | EM | NVT | NPT | Production MD |
|---|---:|---:|---:|---:|
| 运行方式 | 前台运行 | `tmux` 会话 | `tmux` 会话 | `tmux` 会话 |
| `-nt 12` | 是 | 是 | 是 | 是 |
| `-maxh 0.08` | 是 | 否 | 否 | 否 |
| `-update gpu` | 默认不加 | 是，环境适合时 | 是，环境适合时 | 是，环境适合时 |
| `-pin on` | 默认不加 | 是，环境适合时 | 是，环境适合时 | 是，环境适合时 |

这里的“是”表示当前用户倾向的适用范围，不表示当前环境必须机械使用该选项。

## 所有 Stage 4 `mdrun` 运行类别

以下倾向适用于当前 Stage 4 的全部 `mdrun` 运行类别：

```text
EM
NVT
NPT
Production MD
```

默认线程倾向：

```text
-nt 12
```

若当前资源分配、硬件拓扑或运行环境不适合 12 个线程，按实际资源调整。

## 运行方式

运行方式按运行类别区分：

- EM：前台运行；
- NVT / NPT / Production MD：在 `tmux` 会话中运行。

当前作业环境已经由其它调度系统负责作业保持时，可以按实际环境调整运行方式。

## 仅适用于 EM

以下倾向只适用于 EM：

```text
-maxh 0.08
```

`-maxh 0.08` 只用于限制一次本地 Agent 调用的 wall-clock 占用，不是 EM convergence criterion。若当前 EM 需要持续运行到收敛、采用外部作业环境，或该限制会妨碍实际完成，则不使用或调整该值。

EM 默认不主动加入：

```text
-update gpu
-pin on
```

除非当前 GROMACS / GPU 环境实际需要且支持。

## 仅适用于 NVT / NPT / Production MD

在当前 GPU / GROMACS build 支持且适合时，NVT、NPT 和 Production MD 倾向使用：

```text
-update gpu
-pin on
```

这些选项是执行资源倾向，不是科学模拟要求。若当前环境不支持、仅使用 CPU、更适合其它 GPU 卸载方式，或调度系统已经管理线程绑定 / 资源分配，则按实际环境调整。

NVT / NPT / Production MD 不继承 EM-only 的短 `-maxh 0.08` 倾向。

## Maintenance

用户后续明确改变长期本地执行偏好时更新本文件，而不是把同一偏好分别复制到 4.1 / 4.2 / 4.3。

临时只针对某个 run unit 的资源要求记录在当前 Task Sheet / 实际执行命令中，不因为一次例外修改本文件的长期倾向。
