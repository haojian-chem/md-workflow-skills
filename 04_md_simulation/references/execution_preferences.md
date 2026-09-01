# Stage 4 execution preferences

Status: CURRENT USER EXECUTION PREFERENCES

本文件记录 Stage 4 本地计算执行时的用户倾向。它不是模拟科学参数规范，也不改变 `.mdp`、run-unit、reuse、continuation 或 validation 的 scientific semantics。

Stage 4 main Skill 在需要生成 / 执行 `gmx_mdrun.sh` 时读取本文件。实际执行时：

1. 先采用当前 Task / 用户本轮明确指定的执行要求；
2. 没有新的明确要求时，采用本文件记录的用户倾向；
3. 当前硬件、GROMACS build、体系或作业环境与某项倾向不兼容时，由执行 Agent 按实际环境调整，不为了机械保持倾向而执行无效命令；
4. 如果调整只影响计算资源和运行方式、不改变科学模拟条件，可以直接调整并记录实际命令；
5. 如果调整会改变 scientific run definition，则回到对应 Stage 4 / run-specific Skill 的科学规则处理。

最终实际 `gmx mdrun` 命令始终以当前 run unit 中保存的 `gmx_mdrun.sh` 为准。

## Current local execution tendencies

### Common

本地 GROMACS 任务默认倾向：

```text
-nt 12
```

若当前资源分配、硬件拓扑或运行环境不适合 12 threads，按实际资源调整。

### Energy minimization

EM 本地执行倾向：

```text
foreground execution
-maxh 0.08
```

`-maxh 0.08` 只用于限制一次本地 Agent 调用的 wall-clock 占用，不是 EM convergence criterion。若当前任务需要持续运行到收敛、采用外部作业环境，或该限制会妨碍实际完成，则不使用或调整该值。

EM 默认不主动加入：

```text
-update gpu
-pin on
```

除非当前 GROMACS / GPU 环境实际需要且支持。

### NVT / NPT / production MD

较长的 NVT / NPT / production MD 本地任务倾向使用：

```text
tmux
```

并在当前 GPU / GROMACS build 支持且适合时倾向使用：

```text
-update gpu
-pin on
```

这些选项是执行资源倾向，不是 NVT / NPT / production scientific requirement。若当前环境不支持、CPU-only、更适合其它 offload 方式或调度系统已经管理 pinning / resources，则按实际环境调整。

NVT / NPT / production MD 不默认继承 EM 的短 `-maxh 0.08` 倾向。

## Maintenance

用户后续明确改变本地执行偏好时更新本文件，而不是把同一偏好分别复制到 4.1 / 4.2 / 4.3。

临时只针对某个 run unit 的资源要求记录在当前任务 / 实际执行命令中，不因为一次例外修改本文件的长期倾向。
