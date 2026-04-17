# MaxKB 本地开发调试指南

本文档用于说明如何在本地启动、调试和验收 MaxKB 项目。目标是让后续开发者能够快速在本机完成：

- 后端启动
- 前后端一体化启动
- 接口联调
- 验收脚本执行
- 常见问题排查

---

## 1. 环境说明

### 1.1 推荐环境

- macOS / Linux
- Python 3.11
- Docker Desktop
- Docker Compose
- 已安装 `curl`

### 1.2 本地依赖

本项目本地调试通常会用到：

- PostgreSQL
- Redis
- Django 后端
- Nginx
- 前端静态资源

---

## 2. 本地启动方式

项目提供两种本地启动方式：

1. **开发模式**：适合改代码、调接口、快速验证
2. **一体化模式**：适合模拟生产环境，前后端 + 数据库 + Redis 一次性启动

---

## 3. 开发模式启动

开发模式适合后端代码修改后的快速调试。

### 3.1 进入虚拟环境

如果已经存在 `.venv`，直接激活即可：

```bash
source .venv/bin/activate
```

### 3.2 启动后端

使用脚本启动：

```bash
./run_local_dev.sh run
```

脚本会自动：

- 激活虚拟环境
- 尝试从本地 Docker 容器读取 PostgreSQL / Redis 密码
- 在本机启动 Django 开发服务（默认 `0.0.0.0:8080`）

**重要说明：**

- `./run_local_dev.sh run` **不会**启动或重启 Docker 里的 `maxkb` 容器
- 如果你把 Docker 的 `maxkb` 容器删掉了，执行 `run` 也不会把它拉起来
- `run` 只是本地 Python 进程，不是 Docker 编排命令

### 3.3 启动后端前的依赖要求

默认情况下，脚本会尝试连接本地：

- PostgreSQL `127.0.0.1:5432`
- Redis `127.0.0.1:6379`

如果你本地已经启动了 Docker 容器，脚本会自动读取容器里的环境变量。

---

## 4. 一体化启动方式

如果你想要尽量接近生产环境，可以使用一体化方式：

```bash
chmod +x run_local_all.sh
./run_local_all.sh up
```

### 4.1 一体化模式启动内容

`docker-compose.yml` 会一次启动：

- `postgres`
- `redis`
- `maxkb`

其中 `maxkb` 容器内部会启动：

- 后端服务
- Nginx
- 前端静态页面代理

### 4.2 一体化模式访问地址

启动成功后常用地址如下：

- 管理后台：`http://127.0.0.1:8090/admin/`
- Chat 页面：`http://127.0.0.1:8090/chat/`
- Tool 页面：`http://127.0.0.1:8090/tool/`
- Open API 健康检查：`http://127.0.0.1:8090/api/open/v1/health`
- 后端直连端口：`http://127.0.0.1:8080/`

### 4.3 常用命令

```bash
./run_local_all.sh up
./run_local_all.sh ps
./run_local_all.sh logs
./run_local_all.sh down
./run_local_all.sh rebuild
./run_local_all.sh health
```

### 4.4 `up` 和 `rebuild` 的区别

- `up`：只启动，不重新构建镜像
- `rebuild`：重新构建镜像后再启动

如果只是重启本地环境，推荐用 `up`。
如果你修改了代码，需要更新镜像，推荐用 `rebuild`。

注意：如果本地 PostgreSQL 之前已经初始化过，新增的 `pgvector` 初始化脚本只会在空数据卷首次启动时执行；
如果你已经遇到过 `type "vector" does not exist`，建议先删除 `maxkb-postgres-data` 卷再执行 `rebuild`，让数据库重新初始化并自动创建扩展。

### 4.5 `run` 和 Docker 的关系

`./run_local_dev.sh run` 只是启动本机 Django 服务，不会操作 Docker 容器。

这个脚本现在会先检查并尝试释放 `8080` 端口，避免你本机启动时遇到端口占用。

这意味着：

- 如果 Docker 里的 `maxkb` 容器还在跑，本机的 `run` 会先尝试把占用 `8080` 的进程停掉，再启动 Django
- 如果你把 Docker 里的 `maxkb` 容器删掉了，`run` 也不会自动把它重建回来
- 想要 Docker 容器重新起来，需要使用 `./run_local_all.sh up` 或 `./run_local_all.sh rebuild`

### 4.5 本地验收脚本

可以使用本地验收脚本一次性检查常见接口是否可用：

```bash
python test_maxkb_local_smoke.py \
  --base-url http://127.0.0.1:8090 \
  --prefix /admin \
  --username admin \
  --password admin
```

如果你已经配置了 Open API Key，也可以附加：

```bash
python test_maxkb_local_smoke.py \
  --base-url http://127.0.0.1:8090 \
  --prefix /admin \
  --username admin \
  --password admin \
  --api-key "$MAXKB_API_KEY" \
  --application-id "$MAXKB_APPLICATION_ID"
```

---

## 5. 数据库和 Redis

### 5.1 本地 Docker 容器

本地常用的容器名：

- PostgreSQL：`maxkb-postgres`
- Redis：`maxkb-redis`

### 5.2 如何查看数据库密码

查看 PostgreSQL 容器环境变量：

```bash
docker inspect maxkb-postgres
```

重点关注：

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`

查看 Redis 容器环境变量：

```bash
docker inspect maxkb-redis
```

重点关注：

- `REDIS_PASSWORD`
- 或者启动命令中的 `--requirepass`

### 5.3 脚本自动读取

`run_local_dev.sh` 会自动读取这些 Docker 容器中的配置，并映射为：

- `MAXKB_DB_USER`
- `MAXKB_DB_PASSWORD`
- `MAXKB_DB_NAME`
- `MAXKB_REDIS_PASSWORD`

因此大多数情况下无需手工设置。

---

## 6. 验收与调试

### 6.1 健康检查

启动后可以先验证 Open API：

```bash
curl http://127.0.0.1:8080/api/open/v1/health
```

或者一体化模式下：

```bash
curl http://127.0.0.1:8090/api/open/v1/health
```

### 6.2 端到端验收脚本

项目中提供了验收脚本：

```bash
python3 test_maxkb_end_to_end.py
```

它会检查：

- 健康检查
- 知识库创建
- 知识库查询
- 文档上传
- 多格式文件上传
- 文档列表
- `chat/completions`
- 会话列表
- 会话消息
- 失败场景与错误码

### 6.3 生产级问答质量校验

如果你要验证问答是否满足生产标准，需要重点确认：

- `answer` 不是占位内容
- `sources` 非空且有实际来源
- `usage.total_tokens` 真实且大于 0

---

## 7. 常见问题

### 7.1 Django 启动时报数据库认证失败

现象：

```text
password authentication failed for user "postgres"
```

处理：

- 检查 PostgreSQL 容器用户名和密码
- 确认 `MAXKB_DB_USER` 和 `MAXKB_DB_PASSWORD` 是否正确
- 如果使用 Docker 容器，建议让脚本自动读取容器环境变量

### 7.2 Django 启动时报 Redis Authentication required

现象：

```text
redis.exceptions.AuthenticationError: Authentication required.
```

处理：

- 检查 Redis 容器是否启用了密码
- 确认 `MAXKB_REDIS_PASSWORD` 是否正确
- 一般可通过 `docker inspect maxkb-redis` 查看

### 7.3 `ui/dist` 不存在

现象：

```text
The directory '.../ui/dist' in the STATICFILES_DIRS setting does not exist.
```

说明：

- 前端静态资源还没有构建
- 如果只调后端 API，不影响启动
- 如果要看完整前端页面，需要构建前端资源

### 7.4 `ffmpeg` 警告

现象：

```text
Couldn't find ffmpeg or avconv
```

说明：

- 音频相关能力可能受影响
- 不影响基础 Web 启动

---

## 8. 推荐开发流程

### 8.1 改后端代码

1. 修改代码
2. 启动开发模式：`./run_local_dev.sh run`
3. 调接口验证
4. 跑验收脚本

### 8.2 改前后端整体流程

1. 修改代码
2. 使用一体化模式：`./run_local_all.sh rebuild`
3. 打开浏览器验证页面
4. 跑 Open API 验收

### 8.3 只重启不重建

如果代码没有改动，只是想重启环境：

```bash
./run_local_all.sh up
```

---

## 9. 目录与脚本说明

### 9.1 相关脚本

- `run_local_dev.sh`
  - 本地开发模式启动脚本
  - 适合后端开发调试

- `run_local_all.sh`
  - 一体化启动脚本
  - 适合模拟生产环境

- `test_maxkb_end_to_end.py`
  - 端到端验收脚本

### 9.2 生产相关文件

- `installer/Dockerfile`
- `installer/nginx.conf`
- `installer/start-all.sh`
- `installer/start-with-nginx.sh`

这些文件属于生产构建链路，正常情况下不需要在本地手工修改。

---

## 10. 注意事项

- 本地调试脚本仅用于开发和测试
- 生产发布仍应走现有 CI/CD 和部署流程
- 不要把 API Key、数据库密码直接提交到公共仓库
- 如果修改了后端核心逻辑，建议重新跑一遍验收脚本

---

## 11. 快速开始

### 开发模式

```bash
./run_local_dev.sh run
```

### 一体化模式

```bash
./run_local_all.sh up
```

### 验收

```bash
python3 test_maxkb_end_to_end.py
```

---

## 12. 结束语

如果你只是想快速验证接口和页面，推荐直接用一体化模式。
如果你要改代码并快速看效果，推荐用开发模式。

两者配合使用，基本可以覆盖本地调试的全部场景。
