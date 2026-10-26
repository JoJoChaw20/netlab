FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    mininet \
    bridge-utils \
    iproute2 \
    iputils-ping \
    curl \
    python3 \
    python3-yaml \
    procps \
    traceroute \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /lab

CMD ["/bin/bash"]
