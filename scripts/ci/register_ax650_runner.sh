#!/usr/bin/env bash
set -euo pipefail

RUNNER_URL="${RUNNER_URL:-https://github.com/hlleng/ax-llm}"
RUNNER_NAME="${RUNNER_NAME:-ax650n-01}"
RUNNER_LABELS="${RUNNER_LABELS:-ax650,npu}"
RUNNER_DIR="${RUNNER_DIR:-/opt/actions-runner}"
RUNNER_USER="${RUNNER_USER:-github-runner}"
RUNNER_SERVICE_USER="${RUNNER_SERVICE_USER:-root}"
PROXY_URL="${PROXY_URL:-http://10.126.102.152:3128}"
RUNNER_TOKEN="${RUNNER_TOKEN:-}"

export http_proxy="${PROXY_URL}"
export https_proxy="${PROXY_URL}"
export HTTP_PROXY="${PROXY_URL}"
export HTTPS_PROXY="${PROXY_URL}"
export NO_PROXY="localhost,127.0.0.1"
export no_proxy="${NO_PROXY}"

if [ "$(id -u)" -ne 0 ]; then
    echo "请以 root 执行此脚本，以便创建 Runner 用户和 systemd 服务" >&2
    exit 1
fi

if ! id "${RUNNER_USER}" >/dev/null 2>&1; then
    useradd --system --create-home --shell /bin/bash "${RUNNER_USER}"
fi

if [ ! -f "${RUNNER_DIR}/config.sh" ]; then
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
fi

chown -R "${RUNNER_USER}:${RUNNER_USER}" "${RUNNER_DIR}"

if [ ! -e "${RUNNER_DIR}/.runner" ]; then
    if [ -z "${RUNNER_TOKEN}" ]; then
        echo "请在首次注册时通过环境变量提供 GitHub Runner 注册令牌" >&2
        exit 1
    fi
    export RUNNER_URL RUNNER_NAME RUNNER_LABELS RUNNER_DIR RUNNER_TOKEN
    su -s /bin/bash -p "${RUNNER_USER}" -c '
        cd "${RUNNER_DIR}"
        ./config.sh \
            --unattended \
            --url "${RUNNER_URL}" \
            --token "${RUNNER_TOKEN}" \
            --name "${RUNNER_NAME}" \
            --labels "${RUNNER_LABELS}" \
            --work "_work" \
            --replace
    '
else
    echo "复用已注册的 Runner: ${RUNNER_DIR}"
fi

cd "${RUNNER_DIR}"
./svc.sh install "${RUNNER_SERVICE_USER}"
service_name="$(systemctl list-unit-files 'actions.runner.*' --no-legend | awk 'NR == 1 {print $1}')"
if [ -z "${service_name}" ]; then
    echo "未找到 Runner systemd 服务" >&2
    exit 1
fi
mkdir -p "/etc/systemd/system/${service_name}.d"
cat > "/etc/systemd/system/${service_name}.d/proxy.conf" <<EOF
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
