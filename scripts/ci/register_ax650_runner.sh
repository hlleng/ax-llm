#!/usr/bin/env bash
set -euo pipefail

: "${RUNNER_TOKEN:?请在执行时通过环境变量提供 GitHub Runner 注册令牌}"

RUNNER_URL="${RUNNER_URL:-https://github.com/hlleng/ax-llm}"
RUNNER_NAME="${RUNNER_NAME:-ax650n-01}"
RUNNER_LABELS="${RUNNER_LABELS:-ax650,npu}"
RUNNER_DIR="${RUNNER_DIR:-/opt/actions-runner}"
PROXY_URL="${PROXY_URL:-http://10.126.102.152:3128}"

export http_proxy="${PROXY_URL}"
export https_proxy="${PROXY_URL}"
export HTTP_PROXY="${PROXY_URL}"
export HTTPS_PROXY="${PROXY_URL}"
export NO_PROXY="localhost,127.0.0.1"
export no_proxy="${NO_PROXY}"

if [ -e "${RUNNER_DIR}" ]; then
    echo "Runner 目录已存在: ${RUNNER_DIR}" >&2
    exit 1
fi

mkdir -p "${RUNNER_DIR}"
cd "${RUNNER_DIR}"
runner_version="$(curl -fsSL https://api.github.com/repos/actions/runner/releases/latest | sed -n 's/.*"tag_name": "v\([^"]*\)".*/\1/p' | head -n 1)"
if [ -z "${runner_version}" ]; then
    echo "无法获取 GitHub Actions Runner 版本" >&2
    exit 1
fi

runner_archive="actions-runner-linux-arm64-${runner_version}.tar.gz"
curl -fL --retry 5 -o "${runner_archive}" "https://github.com/actions/runner/releases/download/v${runner_version}/${runner_archive}"
tar xzf "${runner_archive}"
rm "${runner_archive}"

./config.sh \
    --unattended \
    --url "${RUNNER_URL}" \
    --token "${RUNNER_TOKEN}" \
    --name "${RUNNER_NAME}" \
    --labels "${RUNNER_LABELS}" \
    --work "_work" \
    --replace

./svc.sh install root
mkdir -p /etc/systemd/system/actions.runner.service.d
cat > /etc/systemd/system/actions.runner.service.d/proxy.conf <<EOF
[Service]
Environment=http_proxy=${PROXY_URL}
Environment=https_proxy=${PROXY_URL}
Environment=HTTP_PROXY=${PROXY_URL}
Environment=HTTPS_PROXY=${PROXY_URL}
Environment=NO_PROXY=localhost,127.0.0.1
Environment=no_proxy=localhost,127.0.0.1
EOF
systemctl daemon-reload
./svc.sh start
./svc.sh status
