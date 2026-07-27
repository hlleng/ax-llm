# AX650 Runner 部署

板端 Runner 仅注册到 `hlleng/ax-llm`，标签固定为 `self-hosted`、`linux`、`arm64`、`ax650`、`npu`。不要将该 Runner 授权给不可信仓库或外部 Pull Request。

在 GitHub 仓库的 `Settings -> Actions -> Runners -> New self-hosted runner` 生成一次性注册令牌后，在板端执行：

```bash
export http_proxy=http://10.126.102.152:3128
export https_proxy=http://10.126.102.152:3128
git clone --depth 1 --branch axllm https://github.com/hlleng/ax-llm.git /opt/ax-llm
cd /opt/ax-llm
RUNNER_TOKEN='一次性注册令牌' bash scripts/ci/register_ax650_runner.sh
```

脚本通过 `10.126.102.152:3128` 访问 GitHub，并为 systemd 服务设置代理。注册令牌不会写入脚本、工作流或 systemd 配置。

验证服务状态：

```bash
systemctl status actions.runner.*
```

模型验证工作流将模型缓存到 `/mnt/ssd/llm_smoke`，不会使用 GitHub Actions 的临时工作目录保存大模型。Qwen3-0.6B 的首个验证固定使用 Hugging Face revision `9bd240869b5ec6f28964a635cd421a80fcad9dc8`。
