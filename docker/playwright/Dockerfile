ARG BASE_IMAGE=docker.io/node:22-bullseye-slim

FROM ${BASE_IMAGE} AS build

RUN apt-get update && apt-get install -y \
    git
RUN corepack enable && corepack prepare pnpm@10.5.2 --activate

RUN mkdir -p /workspace && chown -R node:node /workspace
WORKDIR /workspace

RUN pnpm add -D playwright && \
    pnpm exec playwright install --with-deps

# Remove build tools to shrink image
RUN apt autoremove -y && apt clean && \
    rm -rf /var/lib/apt/lists/* /root/.cache/pip /tmp/* /opt/install-vscode-extensions.sh

USER node 

CMD ["/bin/sh"]
