# Dockerfile for NVIDIA PyTorch, SSH, R, and Julia

# Placeholder for NVIDIA PyTorch base image
# Please replace with the actual image, e.g., FROM nvcr.io/nvidia/pytorch:23.05-py3
ARG PYTORCH_IMAGE=nvcr.io/nvidia/pytorch:23.05-py3
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
        libfontconfig1-dev \
    libfreetype6-dev \
    libharfbuzz-dev \
    libfribidi-dev \
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
        libfontconfig1-dev \
    libfreetype6-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    && rm -rf /var/lib/apt/lists/*

# Pre-install common R packages
ENV PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:/usr/lib/pkgconfig
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/lib
ENV PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:/usr/lib/pkgconfig
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/lib
RUN R -e "install.packages(c('tidyverse', 'caret', 'randomForest', 'xgboost', 'ggplot2', 'dplyr'), repos='https://cloud.r-project.org/')"