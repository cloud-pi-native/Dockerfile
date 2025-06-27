ARG BASE_IMAGE=docker.io/alpine:3.22.0

FROM ${BASE_IMAGE} AS build

ARG USERNAME=user
ENV HOME=/home/${USERNAME}

RUN addgroup -g 1000 user && \
    adduser -D -u 1000 -G user -s /bin/sh user && \
    apk update && \
    apk add --no-cache \
        git \                                                                              
        py3-pip && \
    find /usr/lib -name EXTERNALLY-MANAGED -exec rm -f {} \;
         
WORKDIR ${HOME}
USER ${USERNAME}
         
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir ansible pyyaml kubernetes python-gitlab jmespath hvac

ENV PATH="${HOME}/.local/bin:$PATH"
RUN ansible-galaxy collection install community.general kubernetes.core
         
CMD ["/bin/sh"]
