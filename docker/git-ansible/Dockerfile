ARG BASE_IMAGE=docker.io/alpine:3.22.1

FROM ${BASE_IMAGE} AS build

RUN apk update && \
    apk add --no-cache \
        git \                                                                              
        yq \                                                                              
        py3-pip && \
    find /usr/lib -name EXTERNALLY-MANAGED -exec rm -f {} \;

RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir ansible pyyaml kubernetes python-gitlab jmespath hvac

RUN ansible-galaxy collection install community.general kubernetes.core

RUN mkdir -p /workspace && \
    chown -R 1000:0 /workspace && \
    chmod -R g=u /workspace

ENV HOME=/workspace
WORKDIR /workspace
USER 1000

CMD ["/bin/sh"]
