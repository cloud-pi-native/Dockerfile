# Stage 1: Build & install dependencies
FROM node:22-bullseye-slim AS builder

RUN apt-get update && apt-get install -y git

WORKDIR /workspace
RUN git clone https://github.com/cloud-pi-native/console.git && \
    cd console && \
    git checkout Test/playwright-on-real-cluster && \
    corepack enable && corepack prepare pnpm@10.5.2 --activate && \
    pnpm install

# Stage 2: Minimal runtime image
FROM mcr.microsoft.com/playwright:v1.55.0-noble as build

# Copy only the test folder and node_modules
WORKDIR /workspace
COPY --from=builder /workspace/console/playwright ./playwright
COPY --from=builder /workspace/console/package.json ./package.json
COPY --from=builder /workspace/console/pnpm-lock.yaml ./pnpm-lock.yaml
COPY --from=builder /workspace/console/node_modules/ ./node_modules/

RUN corepack enable && corepack prepare pnpm@10.5.2 --activate && \
    cd playwright && pnpm exec playwright install --with-deps

#CMD ["pnpm", "exec", "playwright", "test"]
CMD ["/bin/sh"]
