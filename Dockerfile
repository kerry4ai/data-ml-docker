FROM nvcr.io/nvidia/tensorflow:24.01-tf2-py3

# 维护者信息
LABEL maintainer="ml-docker-env"
LABEL description="ML environment with R and Julia based on NVIDIA TensorFlow image"

# 设置环境变量，避免交互式提示
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 1. 更新 apt 并安装必要工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    ca-certificates \
    build-essential \
    git \
    vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. 安装 SSH Server
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    && mkdir -p /var/run/sshd \
    # 配置 SSH 允许 root 登录（生产环境建议使用密钥）
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置默认 root 密码（可通过环境变量覆盖）
ENV ROOT_PASSWORD=docker
RUN echo "root:${ROOT_PASSWORD}" | chpasswd

# 3. 安装 R
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg \
    && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9 \
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

# 预安装常用 R 包
RUN R -e "install.packages(c('tidyverse', 'caret', 'randomForest', 'xgboost', 'ggplot2', 'dplyr'), repos='https://cloud.r-project.org/')"

# 4. 安装 Julia
ENV JULIA_VERSION=1.10.0
RUN wget -q https://julialang-s3.julialang.org/bin/linux/x64/${JULIA_VERSION%.*}/julia-${JULIA_VERSION}-linux-x86_64.tar.gz \
    && tar -xzf julia-${JULIA_VERSION}-linux-x86_64.tar.gz -C /usr/local --strip-components=1 \
    && rm julia-${JULIA_VERSION}-linux-x86_64.tar.gz

# 预安装常用 Julia 包
RUN julia -e 'using Pkg; Pkg.add(["DataFrames", "CSV", "Flux", "GLM", "Plots", "StatsBase"])'

# 设置环境变量
ENV PATH=$PATH:/usr/local/julia/bin
ENV JULIAdepot=/opt/julia

# 暴露端口
EXPOSE 22 8888 6006 8787

# 创建启动脚本
RUN echo '#!/bin/bash\n\
service ssh start\n\
echo "SSH server started on port 22"\n\
echo "Root password: ${ROOT_PASSWORD}"\n\
exec "$@"' > /usr/local/bin/start.sh \
    && chmod +x /usr/local/bin/start.sh

# 设置工作目录
WORKDIR /workspace

# 启动命令
CMD ["/usr/local/bin/start.sh", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--allow-root", "--no-browser", "--NotebookApp.token=''"]
