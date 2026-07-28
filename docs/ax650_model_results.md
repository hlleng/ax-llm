# AX650 模型冒烟测试结果

该文件由 GitHub Actions 在模型冒烟测试成功后自动追加。每个表格记录一次成功验证，便于观察模型版本、性能和板端资源变化。

- CMM：`/proc/ax_proc/mem_cmm_info` 中的可用 CMM，单位 MiB，记录 `llm_smoke` 完成后的数值。
- DDR：`/proc/meminfo` 中的 `MemAvailable`，单位 MiB，记录 `llm_smoke` 完成后的数值。
- FLASH：模型目录实际文件大小，以及 `/mnt/ssd/llm_smoke` 所在文件系统在测试后的可用容量。
- CMM 和 DDR 是测试结束后的快照，不代表测试过程中的峰值占用。


## 2026-07-28 17:17:31 CST

- 模式：`smoke`
- 源码提交：`a9cdbbc3754477a551067c048931821d28f82178`
- 工作流：https://github.com/hlleng/ax-llm/actions/runs/30345534911

| 模型 | Revision | 输入 | CMM 可用 (MiB) | DDR 可用 (MiB) | FLASH | 耗时 (s) | 结果 |
|---|---|---|---:|---:|---|---:|---|
| AXERA-TECH/Qwen3-0.6B | `9bd240869b5ec6f28964a635cd421a80fcad9dc8` | text | 4339.6 | 2950.7 | 模型 1077.8 MiB; 可用 192.39 GiB | 13.480 | passed |
| AXERA-TECH/Qwen3-1.7B | `f77a4ab10991c6476dafb111371960d6cdce5e6f` | text | 4339.6 | 3019.6 | 模型 2915.9 MiB; 可用 192.39 GiB | 30.412 | passed |
| AXERA-TECH/Qwen3-VL-2B-Instruct-GPTQ-Int4 | `87bba71b6380f3d1402760625af0b0229441a93a` | image | 4339.6 | 3020.6 | 模型 4297.4 MiB; 可用 192.39 GiB | 27.258 | passed |
| AXERA-TECH/MiniCPM5-1B | `59d74f7ce4028c2a5f15318ddf8e777ef73695ec` | text | 4339.6 | 3014.0 | 模型 1464.2 MiB; 可用 192.39 GiB | 13.722 | passed |


## 2026-07-28 17:34:40 CST

- 模式：`scan-updates`
- 源码提交：`f74b80b860dbb5d437576db8ec5c4a5993a3e487`
- 工作流：https://github.com/hlleng/ax-llm/actions/runs/30346487549

| 模型 | Revision | 输入 | CMM 可用 (MiB) | DDR 可用 (MiB) | FLASH | 耗时 (s) | 结果 |
|---|---|---|---:|---:|---|---:|---|
| AXERA-TECH/MiniCPM5-1B | `adf420c18a443904ab88a1b88aa3f9389eafa575` | text | 4339.6 | 2786.2 | 模型 1464.2 MiB; 可用 190.96 GiB | 13.421 | passed |
