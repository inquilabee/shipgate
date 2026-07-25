# ShipGate fresh-machine integration smoke test image.
# Managed tool installs download catalog pins (GitHub/npm); network required at runtime.
FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1

# git: init + incremental checks; curl: HTTPS downloads; node/npm: binary npm tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY pyproject.toml /workspace/shipgate-pkg/
COPY src/ /workspace/shipgate-pkg/src/

RUN pip install /workspace/shipgate-pkg/

COPY scripts/docker-test/run-integration.sh /workspace/run-integration.sh
RUN chmod +x /workspace/run-integration.sh

COPY docker/dogfood-staging/ /workspace/dogfood/

ENTRYPOINT ["/workspace/run-integration.sh"]
