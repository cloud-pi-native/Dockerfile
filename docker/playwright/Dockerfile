# Stage 1: Build & install dependencies
FROM docker.io/node:22-bullseye-slim as builder

RUN apt-get update && apt-get install -y git

WORKDIR /workspace
RUN git clone https://github.com/cloud-pi-native/console.git && \
    cd console && \
    git checkout Test/playwright-on-real-cluster && \
    corepack enable && corepack prepare pnpm@10.5.2 --activate && \
    pnpm install --filter @cpn-console/playwright... --frozen-lockfile

# Stage 2: Minimal runtime image
FROM docker.io/node:22-bullseye-slim as build

WORKDIR /workspace
COPY --from=builder /workspace/console/playwright ./playwright
COPY --from=builder /workspace/console/package.json ./package.json
COPY --from=builder /workspace/console/node_modules/ ./node_modules/

RUN corepack enable && corepack prepare pnpm@10.5.2 --activate && \
    cd playwright && pnpm exec playwright install --with-deps

CMD ["/bin/sh"]
