# MaxKB 本地开发指南

本地开发只记住一条命令：

```bash
bash run_local_dev.sh
```

它会自动完成：

- 启动 PostgreSQL 和 Redis
- 清理缓存
- 启动后端
- 启动前端
- 端口占用自动处理

改完代码后，再执行同一个命令即可看到最新效果。

## 说明

- 后端使用源码直接运行
- PostgreSQL 和 Redis 使用 Docker
- 前端使用开发模式启动
- 不需要手动打镜像

## 一体化模式

如果你需要生产式的一体化启动，继续使用 `run_local_all.sh` 即可。

## 常见问题

- 如果前端页面白屏，先确认后端和前端都已启动
- 如果端口被占用，脚本会自动释放
- 如果 `ui/dist` 不存在，表示这是开发模式，静态构建目录未生成，这是正常的

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
2. 直接执行：`./run_local_dev.sh`
3. 调接口验证
4. 前端马上看到效果

### 8.2 改前后端整体流程

1. 修改代码
2. 使用一体化模式：`./run_local_all.sh up`
3. 打开浏览器验证页面
4. 如果需要完整重新构建，再执行 `./run_local_all.sh rebuild`

### 8.3 只重启不重建

如果你改的是源码逻辑，直接再执行一次：

```bash
./run_local_dev.sh
```

---

## 9. 目录与脚本说明

### 9.1 相关脚本

- `run_local_dev.sh`
  - 唯一的源码开发启动脚本
  - 自动检查/启动 PostgreSQL 和 Redis
  - 清理缓存后直接启动源码

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

### 源码开发模式

```bash
./run_local_dev.sh db-up
./run_local_dev.sh run
```

如果修改了源码，再执行：

```bash
./run_local_dev.sh restart
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
