# ShipGate fresh-machine integration smoke test image.
FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1

# git: init + incremental checks; curl: binary downloads; node/npm: markdownlint; go: yamlfmt
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    nodejs \
    npm \
    golang-go \
    && rm -rf /var/lib/apt/lists/*

# Seed common binaries on PATH so shipgate install links them without GitHub API calls.
RUN curl -fsSL "https://github.com/mvdan/sh/releases/download/v3.12.0/shfmt_v3.12.0_linux_amd64" \
      -o /usr/local/bin/shfmt \
    && chmod +x /usr/local/bin/shfmt \
    && curl -fsSL "https://github.com/gitleaks/gitleaks/releases/download/v8.28.0/gitleaks_8.28.0_linux_x64.tar.gz" \
      | tar -xz -C /usr/local/bin gitleaks \
    && go install github.com/google/yamlfmt/cmd/yamlfmt@latest \
    && install -m 0755 /root/go/bin/yamlfmt /usr/local/bin/yamlfmt

WORKDIR /workspace

COPY pyproject.toml /workspace/shipgate-pkg/
COPY src/ /workspace/shipgate-pkg/src/

RUN pip install /workspace/shipgate-pkg/

COPY scripts/docker-test/run-integration.sh /workspace/run-integration.sh
RUN chmod +x /workspace/run-integration.sh

COPY docker/dogfood-staging/ /workspace/dogfood/

ENTRYPOINT ["/workspace/run-integration.sh"]
