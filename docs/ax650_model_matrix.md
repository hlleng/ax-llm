# AX650 模型清单验证

模型清单位于 `.github/tests/ax650_models.json`。每条记录必须固定 `model_id` 与 Hugging Face `revision`，避免上游更新改变既有验证结果。

字段说明：

- `key`：工作流手动选择的唯一标识。
- `enabled`：`false` 的模型不会进入 `all` 验证。
- `input`：支持 `text`、`image`、`video`、`audio`。
- `fixture`：非文本模型的本地测试文件，相对仓库根目录。
- `dynamic_load_pool`：动态加载时常驻的层数，设为 `0` 表示关闭。

工作流输入 `model=all` 时按清单顺序串行运行所有已启用模型；输入具体 `key` 时只运行一个模型。每个模型都是独立的 `llm_smoke` 进程，退出后检查 CMM 是否在 64 MB 容差内恢复。超出容差时停止后续模型，防止资源泄漏扩大。

多模态的简单验证只检查真实媒体输入能完成一次 NPU 推理并输出 `[SMOKE OK]`。文本语义、图片理解质量和音视频内容准确性需要针对具体模型补充基准夹具与断言。

## 夜间更新验证

工作流每天北京时间 00:00（GitHub Actions cron: `0 16 * * *`，UTC）扫描所有已启用模型的 Hugging Face 最新 revision。GitHub 的定时任务可能延后几分钟执行。

- 最新 revision 与清单中的 `revision` 相同：工作流成功结束，不构建、不下载模型，也不占用板卡。
- 最新 revision 不同：仅对发生变化的模型创建候选清单，并在板卡上串行冒烟验证。
- 所有候选模型通过：工作流使用 `github-actions[bot]` 将新的 revision 提交并推送至 `axllm` 分支。
- 任一候选模型失败，或验证期间分支发生变化：正式清单保持原 revision，不会自动升级。

手动触发工作流时，`smoke` 模式验证清单中已固定的 revision；`scan-updates` 模式执行与夜间任务相同的更新检测、验证和回写流程。新出现在 Hugging Face 组织中的模型不会自动纳入测试，必须先在清单中补齐输入类型、媒体夹具和运行参数。
