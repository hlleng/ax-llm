# AX650 模型清单验证

模型清单位于 `tests/ax650_models.json`。每条记录必须固定 `model_id` 与 Hugging Face `revision`，避免上游更新改变既有验证结果。

字段说明：

- `key`：工作流手动选择的唯一标识。
- `enabled`：`false` 的模型不会进入 `all` 验证。
- `input`：支持 `text`、`image`、`video`、`audio`。
- `fixture`：非文本模型的本地测试文件，相对仓库根目录。
- `dynamic_load_pool`：动态加载时常驻的层数，设为 `0` 表示关闭。

工作流输入 `model=all` 时按清单顺序串行运行所有已启用模型；输入具体 `key` 时只运行一个模型。每个模型都是独立的 `llm_smoke` 进程，退出后检查 CMM 是否在 64 MB 容差内恢复。超出容差时停止后续模型，防止资源泄漏扩大。

多模态的简单验证只检查真实媒体输入能完成一次 NPU 推理并输出 `[SMOKE OK]`。文本语义、图片理解质量和音视频内容准确性需要针对具体模型补充基准夹具与断言。
