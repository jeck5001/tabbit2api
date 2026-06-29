# NAS 部署指南（Docker Compose + GitHub Actions）

本文档说明如何用 GitHub Actions 自动构建 Docker 镜像，并在 NAS 上通过 docker-compose 拉取镜像部署 Tabbit2API。

整体流程：

```
推送代码到 GitHub  ──►  GitHub Actions 构建镜像  ──►  推送到 GHCR  ──►  NAS 上 docker compose pull & up
```

---

## 一、GitHub Actions 自动构建镜像

工作流文件位于 `.github/workflows/docker-build.yml`，会在以下情况触发：

- 推送到 `main` 分支
- 打 tag（形如 `v1.0.0`）
- 在 GitHub 网页上手动触发（Actions 页面的 "Run workflow" 按钮）

构建产物会推送到 **GitHub Container Registry (GHCR)**，镜像地址为：

```
ghcr.io/jeck5001/tabbit2api:latest
```

打 tag 时还会额外生成版本号标签，如 `ghcr.io/jeck5001/tabbit2api:v1.0.0`。

### 不需要额外配置密钥

工作流使用 GitHub 自动注入的 `GITHUB_TOKEN` 登录 GHCR，无需手动配置 secrets。

### 让镜像可被 NAS 拉取（重要）

GHCR 镜像默认是 **私有** 的。首次构建成功后，需要做一次设置才能在 NAS 上顺利拉取，二选一：

**方案 A：把镜像设为公开（最简单）**

1. 打开 `https://github.com/jeck5001?tab=packages`
2. 点进 `tabbit2api` 这个 package
3. 右侧 "Package settings" → "Danger Zone" → "Change visibility" → 设为 **Public**

设为公开后，NAS 无需登录即可拉取。

**方案 B：保持私有，在 NAS 上登录后拉取**

在 NAS 上执行（用一个有 `read:packages` 权限的 Personal Access Token 作为密码）：

```bash
echo "<你的_PAT>" | docker login ghcr.io -u jeck5001 --password-stdin
```

---

## 二、NAS 上部署

### 1. 准备文件

把仓库里的 `docker-compose.deploy.yml` 上传到 NAS 的一个目录，比如 `/volume1/docker/tabbit2api/`。

也可以直接在 NAS 上新建该目录并把文件放进去。

### 2. 创建数据目录

```bash
cd /volume1/docker/tabbit2api      # 换成你的实际目录
mkdir -p ./data
```

配置文件 `config.json` 和运行数据会持久化在这个 `data` 目录里，容器重建不会丢失。

### 3. （可选）预置配置文件

如果想直接放好配置，把仓库里的 `config.json.example` 复制为 `data/config.json` 并填好内容：

```bash
cp config.json.example ./data/config.json
```

如果不预置，首次启动后通过 Web 管理面板配置即可（见第 5 步）。

### 4. 启动服务

```bash
docker compose -f docker-compose.deploy.yml pull
docker compose -f docker-compose.deploy.yml up -d
```

查看日志确认启动正常：

```bash
docker compose -f docker-compose.deploy.yml logs -f
```

### 5. 首次配置

浏览器访问管理面板：

```
http://<NAS_IP>:8800/admin
```

在这里设置管理密码、添加 Tabbit token 等。配置会写入 `data/config.json`。

服务的 API 端点：

- OpenAI 兼容：`http://<NAS_IP>:8800/v1/chat/completions`
- Claude Messages：`http://<NAS_IP>:8800/v1/messages`
- 模型列表：`http://<NAS_IP>:8800/v1/models`

---

## 三、更新到新版本

每次推送代码到 `main`，Actions 会自动构建新的 `latest` 镜像。NAS 上更新：

```bash
cd /volume1/docker/tabbit2api
docker compose -f docker-compose.deploy.yml pull
docker compose -f docker-compose.deploy.yml up -d
```

旧镜像清理（可选）：

```bash
docker image prune -f
```

---

## 四、常用命令

| 操作 | 命令 |
|------|------|
| 启动 | `docker compose -f docker-compose.deploy.yml up -d` |
| 停止 | `docker compose -f docker-compose.deploy.yml down` |
| 重启 | `docker compose -f docker-compose.deploy.yml restart` |
| 看日志 | `docker compose -f docker-compose.deploy.yml logs -f` |
| 看状态 | `docker compose -f docker-compose.deploy.yml ps` |
| 拉取新镜像 | `docker compose -f docker-compose.deploy.yml pull` |

---

## 五、修改端口

默认端口 8800。如需改成别的端口（比如 9000），有两种方式：

启动时临时指定：

```bash
PORT=9000 docker compose -f docker-compose.deploy.yml up -d
```

或在 `docker-compose.deploy.yml` 同目录创建 `.env` 文件：

```
PORT=9000
```

注意这里只改了宿主机映射端口，容器内部仍是 8800，无需改配置文件。

---

## 六、故障排查

**拉取镜像报 `denied` / `unauthorized`**
镜像还是私有的。按第一节"让镜像可被 NAS 拉取"设为公开，或在 NAS 上 `docker login ghcr.io`。

**架构不匹配 `exec format error`**
镜像构建的是 amd64（x86_64）。如果你的 NAS 是 ARM 架构（部分群晖/威联通用 ARM CPU），需要在 `.github/workflows/docker-build.yml` 的 `platforms` 里改为或加上 `linux/arm64` 重新构建。

**容器一直 unhealthy**
看日志 `docker compose -f docker-compose.deploy.yml logs`。多数是 config.json 未正确生成或 token 无效。确认 `data` 目录有写权限。

**访问 /admin 打不开**
确认防火墙/NAS 安全组放行了 8800 端口，且容器状态为 `running (healthy)`。
