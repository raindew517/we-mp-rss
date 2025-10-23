# 多架构 Docker 构建指南

本项目支持构建 `linux/amd64` 和 `linux/arm64` 两种架构的 Docker 镜像，适用于 x86_64 和 ARM64 (如 Apple Silicon Mac、ARM 服务器) 等不同架构的设备。

## 🚀 快速开始

### 方法一：使用增强版构建脚本（推荐）

#### Windows 用户
```bash
# 本地构建多架构镜像
.\dock_build_multiarch.bat

# 构建并推送到仓库
.\dock_build_multiarch.bat -p

# 构建后清理缓存
.\dock_build_multiarch.bat -p --clean
```

#### Linux/macOS 用户
```bash
# 给脚本执行权限
chmod +x dock_build_multiarch.sh

# 本地构建多架构镜像
./dock_build_multiarch.sh

# 构建并推送到仓库
./dock_build_multiarch.sh -p

# 构建后清理缓存
./dock_build_multiarch.sh -p --clean
```

### 方法二：使用原有脚本（已升级支持多架构）

#### Windows 用户
```bash
# 本地构建
.\dock_build.bat

# 构建并推送
.\dock_build.bat -p
```

### 方法三：使用 Docker Compose
```bash
# 构建多架构镜像
docker-compose -f docker-compose.multiarch.yml build

# 启动服务
docker-compose -f docker-compose.multiarch.yml up -d

# 查看日志
docker-compose -f docker-compose.multiarch.yml logs -f

# 停止服务
docker-compose -f docker-compose.multiarch.yml down
```

### 方法四：手动 Docker 命令
```bash
# 创建多架构构建器
docker buildx create --name multiarch --use --platform linux/amd64,linux/arm64

# 构建本地多架构镜像
docker buildx build --platform linux/amd64,linux/arm64 -t we-mp-rss:latest --load .

# 构建并推送多架构镜像
docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/rachelos/we-mp-rss:latest --push .
```

## 📋 系统要求

### Docker 版本要求
- Docker Engine 19.03 或更高版本
- Docker Buildx 插件（通常随 Docker Desktop 自动安装）

### 验证环境
```bash
# 检查 Docker 版本
docker --version

# 检查 Buildx 是否可用
docker buildx version

# 查看可用的构建器
docker buildx ls
```

## 🏗️ 构建器管理

### 创建专用构建器
```bash
# 创建支持多架构的构建器
docker buildx create --name multiarch --driver docker-container --use --platform linux/amd64,linux/arm64

# 启动构建器
docker buildx inspect --bootstrap
```

### 管理构建器
```bash
# 列出所有构建器
docker buildx ls

# 切换构建器
docker buildx use multiarch

# 删除构建器
docker buildx rm multiarch
```

## 🔍 镜像验证

### 查看镜像架构信息
```bash
# 查看本地镜像
docker image ls

# 检查镜像支持的架构
docker buildx imagetools inspect ghcr.io/rachelos/we-mp-rss:latest
```

### 运行测试
```bash
# 在不同架构上运行容器
docker run --rm --platform linux/amd64 we-mp-rss:latest python --version
docker run --rm --platform linux/arm64 we-mp-rss:latest python --version
```

## 🚀 自动化构建

### GitHub Actions
项目已配置 GitHub Actions 自动构建多架构镜像：
- 文件位置: `.github/workflows/docker-publish.yaml`
- 触发条件: 推送到 `main` 分支
- 支持架构: `linux/amd64`, `linux/arm64`
- 推送目标: `ghcr.io/rachelos/we-mp-rss:latest`

### 本地 CI/CD
可以使用提供的脚本集成到本地 CI/CD 流程中：
```bash
# 在 CI 环境中使用
./dock_build_multiarch.sh --push --clean
```

## 🐛 常见问题

### 1. 构建器创建失败
```bash
# 错误: failed to create builder
# 解决: 确保 Docker 版本足够新，并重启 Docker 服务
docker system prune -f
docker buildx prune -f
```

### 2. 跨架构构建缓慢
```bash
# 原因: 跨架构构建需要模拟，速度较慢
# 解决: 使用 GitHub Actions 或专用 ARM 构建机器
```

### 3. 推送权限问题
```bash
# 错误: unauthorized: authentication required
# 解决: 确保已登录到镜像仓库
docker login ghcr.io
```

### 4. 内存不足
```bash
# 错误: failed to solve: executor failed running
# 解决: 增加 Docker 内存限制或使用 --no-cache 参数
docker buildx build --no-cache --platform linux/amd64,linux/arm64 -t image:tag .
```

## 📚 相关资源

- [Docker Buildx 官方文档](https://docs.docker.com/buildx/)
- [多架构镜像最佳实践](https://docs.docker.com/desktop/multi-arch/)
- [GitHub Container Registry 使用指南](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

## 🤝 贡献

如果您在使用多架构构建时遇到问题或有改进建议，欢迎提交 Issue 或 Pull Request。