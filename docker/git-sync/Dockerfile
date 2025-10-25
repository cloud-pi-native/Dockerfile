ARG BASE_IMAGE=docker.io/debian:trixie-slim

FROM ${BASE_IMAGE} AS build

RUN apt-get update -y && apt install gpg wget git -y \
    && wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | tee /usr/share/keyrings/hashicorp-archive-keyring.gpg >/dev/null \
    && DISTRO=$(grep VERSION_CODENAME /etc/os-release | awk -F= '{print $2}') \
    && echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com ${DISTRO} main" | tee /etc/apt/sources.list.d/hashicorp.list \
    && apt-get update -y && apt-get install vault jq -y
