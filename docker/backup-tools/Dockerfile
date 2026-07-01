ARG BASE_IMAGE=docker.io/alpine:3.22.1

FROM ${BASE_IMAGE} AS build

RUN apk update && \
    apk add --no-cache \
        bash \
        curl \
        jq \
        kubectl \
        minio-client && \
    ln -sf /usr/bin/mcli /usr/local/bin/mc

RUN mkdir -p /workspace && \
    chown -R 1000:0 /workspace && \
    chmod -R g=u /workspace

ENV HOME=/workspace
WORKDIR /workspace
USER 1000

CMD ["/bin/bash"]
