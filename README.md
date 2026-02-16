# ML Docker Environment

基于 NVIDIA TensorFlow 的机器学习 Docker 镜像，预装了 SSH Server、R 和 Julia。

## 功能特性

- **基础镜像**: NVIDIA TensorFlow 25.01-py3（包含 CUDA、cuDNN、TensorFlow）
- **编程语言**:
  - Python 3 (TensorFlow、PyTorch 等预装)
  - R 4.x (含 tidyverse、caret、randomForest 等常用包)
  - Julia 1.10.0 (含 DataFrames、Flux、GLM 等常用包)
- **服务**:
  - SSH Server (端口 22)
  - Jupyter Lab (端口 8888)
- **适用平台**: linux/amd64

## 快速开始

### 1. 拉取镜像

```bash
docker pull ghcr.io/your-username/ml-docker-env:latest
```

### 2. 运行容器

```bash
docker run --gpus all -it -p 2222:22 -p 8888:8888 \
  -v $(pwd)/workspace:/workspace/data \
  ghcr.io/your-username/ml-docker-env:latest
```

### 3. 访问服务

- **SSH**: `ssh -p 2222 root@localhost` (默认密码: `docker`)
- **Jupyter Lab**: 打开浏览器访问 `http://localhost:8888`

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ROOT_PASSWORD` | `docker` | SSH root 密码 |

修改密码示例：
```bash
docker run -e ROOT_PASSWORD=mypassword ghcr.io/your-username/ml-docker-env:latest
```

## 预装包

### R 包
- tidyverse
- caret
- randomForest
- xgboost
- ggplot2
- dplyr

### Julia 包
- DataFrames
- CSV
- Flux
- GLM
- Plots
- StatsBase

## 构建

### 通过 GitHub Actions 自动构建

推送到主分支或打标签即可触发构建：

```bash
git tag v1.0.0
git push origin v1.0.0
```

### 本地构建

```bash
docker build -t ml-docker-env:latest .
```

## 端口说明

| 端口 | 服务 |
|------|------|
| 22 | SSH |
| 8888 | Jupyter Lab |
| 6006 | TensorBoard |
| 8787 | RStudio Server (需额外安装) |

## 许可证

MIT
