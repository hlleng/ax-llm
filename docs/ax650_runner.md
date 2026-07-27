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

脚本必须由 root 启动，并会创建 `github-runner` 系统用户，以该用户调用 `config.sh`，避免触发 Runner 的 root 配置限制。AX650 的 NPU 设备节点仅允许 root 访问，因此 systemd 服务默认以 root 运行；仓库中可调度到该 Runner 的工作流拥有板卡 root 权限，只能用于受信任分支和维护者。

## 代理修改

Runner 服务代理位于 `/etc/systemd/system/actions.runner.hlleng-ax-llm.ax650n-01.service.d/proxy.conf`，负责 Runner 与 GitHub 建立和保持连接。模型验证工作流也显式设置 `HTTP_PROXY` 与 `HTTPS_PROXY`，负责 Job 内的 artifact、Hugging Face 和脚本子进程网络访问。

更换代理时必须同步修改这两处，然后执行：

```bash
systemctl daemon-reload
systemctl restart actions.runner.hlleng-ax-llm.ax650n-01.service
```

不再使用代理时，删除该 `proxy.conf`，同时移除工作流的代理环境变量，再重启 Runner 服务。

验证服务状态：

```bash
systemctl status actions.runner.*
```

模型验证工作流将模型缓存到 `/mnt/ssd/llm_smoke`，不会使用 GitHub Actions 的临时工作目录保存大模型。Qwen3-0.6B 的首个验证固定使用 Hugging Face revision `9bd240869b5ec6f28964a635cd421a80fcad9dc8`。
