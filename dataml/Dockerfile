# Dockerfile for NVIDIA PyTorch, SSH, R, and Julia

# Placeholder for NVIDIA PyTorch base image
# Please replace with the actual image, e.g., FROM nvcr.io/nvidia/pytorch:23.05-py3
ARG PYTORCH_IMAGE
FROM $PYTORCH_IMAGE

LABEL maintainer="ml-docker-env"
LABEL description="ML environment with R and Julia based on NVIDIA PyTorch image"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install common tools and SSH server
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    ca-certificates \
    build-essential \
    pkg-config \
    git \
    vim \
    openssh-server \
    libfontconfig1-dev \
    libfreetype6-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    && mkdir -p /var/run/sshd \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's@session\\s*required\\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set default root password (can be overridden by environment variable)
ENV ROOT_PASSWORD=docker
RUN echo "root:${ROOT_PASSWORD}" | chpasswd

# Install R (latest version)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg \
    && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9 || apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9 \
    && add-apt-repository "deb https://cloud.r-project.org/bin/linux/ubuntu $(lsb_release -cs)-cran40/" \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    r-base \
    r-base-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Pre-install common R packages
RUN R -e "install.packages(c('tidyverse', 'caret', 'randomForest', 'xgboost', 'ggplot2', 'dplyr'), repos='https://cloud.r-project.org/')"

# Install Julia (latest stable version dynamically)
ENV JULIA_MAJOR_MINOR=1.12
RUN JULIA_URL_BASE="https://julialang-s3.julialang.org/bin/linux/x64/${JULIA_MAJOR_MINOR}" \
    && JULIA_VERSION=$(curl -s "${JULIA_URL_BASE}/" | grep -oP 'julia-\\K\d+\.\d+\.\d+(?=-linux-x86_64\.tar\.gz)' | sort -V | tail -n 1) \
    && echo "Installing Julia ${JULIA_VERSION}" \
    && wget -q "${JULIA_URL_BASE}/julia-${JULIA_VERSION}-linux-x86_64.tar.gz" -O /tmp/julia.tar.gz \
    && tar -xzf /tmp/julia.tar.gz -C /usr/local --strip-components=1 \
    && rm /tmp/julia.tar.gz

# Pre-install common Julia packages
RUN julia -e 'using Pkg; Pkg.add(["DataFrames", "CSV", "Flux", "GLM", "Plots", "StatsBase"])'

ENV PATH=$PATH:/usr/local/julia/bin
ENV JULIAdepot=/opt/julia

EXPOSE 22 8888 6006 8787

# Create start script
RUN echo '#!/bin/bash\n\
service ssh start\n\
echo "SSH server started on port 22"\n\
echo "Root password: ${ROOT_PASSWORD}"\n\
exec "$@"' > /usr/local/bin/start.sh \
    && chmod +x /usr/local/bin/start.sh

WORKDIR /workspace

CMD ["/usr/local/bin/start.sh", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--allow-root", "--no-browser", "--NotebookApp.token=''"