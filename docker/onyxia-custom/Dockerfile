# Stage 1: Build stage
FROM debian:trixie-slim AS builder

ARG KUBECTL_VERSION=v1.30.1
ARG SOPS_VERSION=v3.9.0
ARG TF_VERSION=1.9.5
ARG PACKER_VERSION=1.11.1
ARG YQ_VERSION=v4.44.3
ARG TSH_VERSION=v18.0.2
ARG HELM_DOCS_VERSION=1.14.2

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    unzip \
    jq \
    tar \
    git \
    sudo

# Install Helm
RUN curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install kubectl
RUN curl -Lo /kubectl https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl && \
    chmod +x /kubectl

# Install kubectl-df-pv
RUN curl https://krew.sh/df-pv | bash 

# Install kubectl-cnpg
RUN curl https://krew.sh/cnpg | bash 

# Install kubectl-sick-pods
RUN curl https://krew.sh/sick-pods | bash 

# Install kubectl-oomd
RUN curl https://krew.sh/oomd | bash 

# Install kubectl-kubescape
RUN curl https://krew.sh/kubescape | bash 

# Install kubectl-ktop
RUN curl https://krew.sh/ktop | bash 

# Install kubectl-node-resource
RUN curl https://krew.sh/node-resource | bash 

# Install k9s 
RUN curl -sS https://webinstall.dev/k9s | bash

# Install SOPS
RUN curl -LO https://github.com/getsops/sops/releases/download/${SOPS_VERSION}/sops-${SOPS_VERSION}.linux.amd64 && \
    chmod +x sops-${SOPS_VERSION}.linux.amd64 && \
    mv sops-${SOPS_VERSION}.linux.amd64 /sops

# Install Terraform
RUN curl -LO https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_amd64.zip && \
    unzip terraform_${TF_VERSION}_linux_amd64.zip -d / && \
    chmod +x /terraform

# Install Packer
RUN curl -LO https://releases.hashicorp.com/packer/${PACKER_VERSION}/packer_${PACKER_VERSION}_linux_amd64.zip && \
    unzip -o packer_${PACKER_VERSION}_linux_amd64.zip -d / && \
    chmod +x /packer

# Install yq
RUN curl -LO https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/yq_linux_amd64.tar.gz && \
    tar -xzf yq_linux_amd64.tar.gz && \
    mv yq_linux_amd64 /yq && \
    chmod +x /yq

# Install Teleport tsh
RUN curl -O https://cdn.teleport.dev/teleport-${TSH_VERSION}-linux-amd64-bin.tar.gz && \
    tar -xzf teleport-${TSH_VERSION}-linux-amd64-bin.tar.gz && \
    mv teleport/tsh /tsh && \
    chmod +x /tsh

# Install Helm-docs
RUN curl -LO https://github.com/norwoodj/helm-docs/releases/download/v${HELM_DOCS_VERSION}/helm-docs_${HELM_DOCS_VERSION}_Linux_x86_64.tar.gz && \
    tar -xzf helm-docs_${HELM_DOCS_VERSION}_Linux_x86_64.tar.gz && \
    chmod +x helm-docs

# Stage 2: Final image
FROM debian:trixie-slim as build 

# System-wide configuration
SHELL ["/bin/bash", "-c"]
ENV SHELL="/bin/bash"
ENV DEBIAN_FRONTEND="noninteractive"

# Setup user & workspace
ENV USERNAME="onyxia"
ENV UID="1000"
ENV GROUPNAME="users"
ENV GID="100"
ENV HOME="/home/${USERNAME}"
ENV WORKSPACE_DIR="${HOME}/work"
RUN groupmod -g ${GID} ${GROUPNAME} && \
    # Setup custom user with sudo rights
    useradd ${USERNAME} --uid=${UID} -g ${GROUPNAME} --groups sudo -r --no-log-init --create-home && \
    # Create workspace
    mkdir ${WORKSPACE_DIR} && \
    # Disable default sudo message when opening shell
    touch ${HOME}/.sudo_as_admin_successful
WORKDIR ${WORKSPACE_DIR}

# Copy tools from builder
COPY --from=builder /usr/local/bin/helm /usr/local/bin/helm
COPY --from=builder /kubectl /usr/local/bin/kubectl
COPY --from=builder /root/.krew/bin/kubectl-df_pv /usr/local/bin/df-pv
COPY --from=builder /root/.krew/bin/kubectl-cnpg /usr/local/bin/cnpg
COPY --from=builder /root/.krew/bin/kubectl-sick_pods /usr/local/bin/sick-pods
COPY --from=builder /root/.krew/bin/kubectl-oomd /usr/local/bin/oomd
COPY --from=builder /root/.krew/bin/kubectl-kubescape /usr/local/bin/kubescape
COPY --from=builder /root/.krew/bin/kubectl-ktop /usr/local/bin/ktop
COPY --from=builder /root/.krew/bin/kubectl-node_resource /usr/local/bin/node-resource
COPY --from=builder /root/.local/bin/k9s /usr/local/bin/k9s
COPY --from=builder /sops /usr/local/bin/sops
COPY --from=builder /terraform /usr/local/bin/terraform
COPY --from=builder /packer /usr/local/bin/packer
COPY --from=builder /yq /usr/local/bin/yq
COPY --from=builder /tsh /usr/local/bin/tsh
COPY --from=builder /helm-docs /usr/local/bin/helm-docs

# Copy settings
COPY files/onyxia-init.sh /opt/onyxia-init.sh
COPY files/install-vscode-extensions.sh /opt/install-vscode-extensions.sh
COPY files/vimrc.template ${HOME}/.vimrc
COPY files/bash_aliases.template ${HOME}/.bash_aliases
COPY files/requirements.txt /tmp/requirements.txt

USER root

RUN chmod -R +x /opt/ && \
    # Fix permissions
    chown -R ${USERNAME}:${GROUPNAME} ${HOME} && \
    chmod +x /opt/onyxia-init.sh && \
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    # Install system package
    apt update && apt install -y --no-install-recommends \
    sudo \
    tzdata \
    ssh \
    vim \
    less \
    git \
    curl \
    iproute2 \
    nmap \
    netcat-openbsd \
    dnsutils \
    build-essential \
    python3-dev \
    libyaml-dev \
    python3-pip \
    s3cmd \
    jq \
    tree \
    bash-completion \
    locales \
    proxytunnel && \
    locale-gen && \
    update-locale LANG=en_US.UTF-8 && \
    echo 'onyxia ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

ARG USER_CONFIG_DIR="${HOME}/.local/share/code-server/User"
ARG REMOTE_CONFIG_DIR="${HOME}/.local/share/code-server/Machine"

# Install VSCode
RUN curl -fsSL https://code-server.dev/install.sh | bash && \
    mkdir -p ${USER_CONFIG_DIR} ${REMOTE_CONFIG_DIR}

# Copy custom VSCode settings
COPY --chown=${USERNAME}:${GROUPNAME} files/User.json ${USER_CONFIG_DIR}/settings.json
COPY --chown=${USERNAME}:${GROUPNAME} files/Remote.json ${REMOTE_CONFIG_DIR}/settings.json

# VSCode extensions and language-specific configuration
RUN /opt/install-vscode-extensions.sh && \
    # Fix permissions
    chown -R ${USERNAME}:${GROUPNAME} ${HOME}

# Install Python packages globally
RUN find /usr/lib -name EXTERNALLY-MANAGED -exec rm -f {} \; && \
    pip3 install --no-cache-dir -r /tmp/requirements.txt

USER 1000

# Install Ansible collections
RUN ansible-galaxy collection install community.general kubernetes.core ansible.utils

# Install Node.js v22 and pnpm v10 with Volta
RUN curl https://get.volta.sh | bash && \
    export VOLTA_HOME="$HOME/.volta" && \
    export PATH="$VOLTA_HOME/bin:$PATH" && \
    volta install node@22 && \
    volta install pnpm@10

ENV VOLTA_HOME="/home/${USERNAME}/.volta"
ENV PATH="${VOLTA_HOME}/bin:${PATH}"

# Remove build tools to shrink image
RUN sudo apt purge -y build-essential python3-dev libyaml-dev && \
    sudo apt autoremove -y && sudo apt clean && \
    sudo rm -rf /var/lib/apt/lists/* /root/.cache/pip /tmp/* /opt/install-vscode-extensions.sh

ENV LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en

CMD ["/bin/bash"]
