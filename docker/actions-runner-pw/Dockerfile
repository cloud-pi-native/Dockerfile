ARG BASE_IMAGE=ghcr.io/actions/actions-runner:latest

FROM ${BASE_IMAGE} AS build

ARG COMPOSE_VERSION=v2.40.0
ARG NODE_MAJOR=26
ARG PW_VERSION=1.59.1

USER root

# Browsers path
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright

# 1) Plugin Docker Compose V2
RUN mkdir -p /usr/local/lib/docker/cli-plugins && \
    curl -fsSL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-$(uname -m)" \
      -o /usr/local/lib/docker/cli-plugins/docker-compose && \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# 2) Node.js
RUN curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# 3) pnpm via corepack
RUN corepack enable

# 4) System Deps + Playwright browsers
RUN apt-get update && \
    npx --yes playwright@${PW_VERSION} install --with-deps chromium firefox && \
    chown -R runner:runner /opt/ms-playwright && \
    chmod -R u+rwX /opt/ms-playwright && \
    rm -rf /var/lib/apt/lists/*

USER runner
