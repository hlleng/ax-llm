# AX650 模型冒烟测试结果

该文件由 GitHub Actions 在模型冒烟测试成功后自动追加。每个表格记录一次成功验证，便于观察模型版本、性能和板端资源变化。

- CMM：`/proc/ax_proc/mem_cmm_info` 中的可用 CMM，单位 MiB，记录 `llm_smoke` 运行前 -> 运行后。
- DDR：`/proc/meminfo` 中的 `MemAvailable`，单位 MiB，记录运行前 -> 运行后。
- FLASH：模型目录实际文件大小，以及 `/mnt/ssd/llm_smoke` 所在文件系统在测试后的可用容量。
- 这些数据是前后快照，不代表测试过程中的峰值占用。


## 2026-07-28 17:17:31 CST

- 模式：`smoke`
- 源码提交：`a9cdbbc3754477a551067c048931821d28f82178`
- 工作流：https://github.com/hlleng/ax-llm/actions/runs/30345534911

| 模型 | Revision | 输入 | Decode (tok/s) | CMM 可用 (MiB，前 -> 后) | DDR 可用 (MiB，前 -> 后) | FLASH | 耗时 (s) | 结果 |
|---|---|---|---:|---|---|---|---:|---|
| AXERA-TECH/Qwen3-0.6B | `9bd240869b5ec6f28964a635cd421a80fcad9dc8` | text | 1.21 | 4339.6 -> 4339.6 | 2922.4 -> 2950.7 | 模型 1077.8 MiB; 可用 192.39 GiB | 13.480 | passed |
| AXERA-TECH/Qwen3-1.7B | `f77a4ab10991c6476dafb111371960d6cdce5e6f` | text | 0.50 | 4339.6 -> 4339.6 | 2952.8 -> 3019.6 | 模型 2915.9 MiB; 可用 192.39 GiB | 30.412 | passed |
| AXERA-TECH/Qwen3-VL-2B-Instruct-GPTQ-Int4 | `87bba71b6380f3d1402760625af0b0229441a93a` | image | 0.72 | 4339.6 -> 4339.6 | 3019.4 -> 3020.6 | 模型 4297.4 MiB; 可用 192.39 GiB | 27.258 | passed |
| AXERA-TECH/MiniCPM5-1B | `59d74f7ce4028c2a5f15318ddf8e777ef73695ec` | text | 1.01 | 4339.6 -> 4339.6 | 3008.8 -> 3014.0 | 模型 1464.2 MiB; 可用 192.39 GiB | 13.722 | passed |
