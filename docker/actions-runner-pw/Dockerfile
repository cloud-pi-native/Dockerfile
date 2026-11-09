ARG BASE_IMAGE=ghcr.io/actions/actions-runner:latest

FROM ${BASE_IMAGE} AS build

ARG COMPOSE_VERSION=v2.40.0
ARG NODE_MAJOR=26
ARG PW_VERSION=1.65.0

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

# 3) PNPM
# Il ne faut plus installer PNPM depuis Corepack !
# (cf: https://github.com/pnpm/pnpm/issues/11732#issuecomment-5267508169)
ENV SHELL="bash"
RUN npx get-pnpm
ENV PATH="/home/node/.local/share/pnpm/bin:$PATH"

# 4) System Deps + Playwright browsers
RUN apt-get update

RUN npx --yes playwright@${PW_VERSION} install --with-deps chromium firefox

RUN chown -R runner:runner /opt/ms-playwright && \
    chmod -R u+rwX /opt/ms-playwright && \
    rm -rf /var/lib/apt/lists/*

USER runner
