# Stage 1: Build & install dependencies
FROM docker.io/node:22-bullseye-slim as builder

WORKDIR /workspace
RUN apt-get update && apt-get install --no-install-recommends -y git ca-certificates && \
    git clone --depth 1 --branch develop https://github.com/cloud-pi-native/console.git && \
    cd console && \
    corepack enable && corepack prepare pnpm@10.5.2 --activate && \
    pnpm install --filter @cpn-console/playwright --frozen-lockfile

# Stage 2: Minimal runtime image
FROM docker.io/node:22-bullseye-slim as build

ENV PNPM_HOME=/workspace \
    PATH="$PNPM_HOME:$PATH" \
    PLAYWRIGHT_BROWSERS_PATH=/workspace/.playwright \
    COREPACK_ENABLE_DOWNLOAD_PROMPT=0
WORKDIR /workspace

COPY --from=builder /workspace/console/playwright/ ./playwright/
COPY --from=builder /workspace/console/package.json ./package.json
COPY --from=builder /workspace/console/node_modules/ ./node_modules/
COPY files/playwright.sh ./playwright.sh 

RUN apt-get update && \ 
    apt-get install --no-install-recommends -y \ 
       ca-certificates \
       bash \
       curl && \
    corepack enable && corepack prepare pnpm@10.5.2 --activate && \
    cd playwright && pnpm exec playwright install --with-deps && \
    chown -R 1000:0 /workspace && \
    chmod -R g=u /workspace && \
    rm -rf /root/.cache /tmp/* /var/lib/apt/lists/*

USER 1000

CMD ["/bin/bash"]
