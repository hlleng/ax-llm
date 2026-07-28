# AX650 模型冒烟测试结果

该文件由 GitHub Actions 在模型冒烟测试成功后自动追加。每个表格记录一次成功验证，便于观察模型版本、性能和板端资源变化。

- CMM：`/proc/ax_proc/mem_cmm_info` 中的可用 CMM，单位 MiB，记录 `llm_smoke` 运行前 -> 运行后。
- DDR：`/proc/meminfo` 中的 `MemAvailable`，单位 MiB，记录运行前 -> 运行后。
- FLASH：模型目录实际文件大小，以及 `/mnt/ssd/llm_smoke` 所在文件系统在测试后的可用容量。
- 这些数据是前后快照，不代表测试过程中的峰值占用。
