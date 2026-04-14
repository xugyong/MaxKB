可以，我给你出一版**方案二：长期架构设计**。

这个方案的目标是把 MaxKB 改造成三层结构：

1. **后台管理 API**
   给管理员、工作空间运营人员使用

2. **开放 API**
   给你自定义前端、第三方系统、外部访客使用

3. **内部服务层**
   统一承载知识库、文档解析、向量检索、问答生成等核心逻辑

当前实施进度：
- 已新增 `open_api` 模块骨架
- 已加入 `v1/health` 健康检查接口
- 下一步将补充认证、知识库、文档、问答接口

这样做的核心收益是：

- 前后端彻底解耦
- 开放接口更稳定
- 权限更清晰
- 后续可以支持多种前端形态
- 以后接第三方系统时不会污染后台接口

---

# 一、总体架构

建议把系统分成下面几层：

## 1）前端层
可以有多个前端：

- 管理后台前端
- 你的自定义知识库前端
- 第三方嵌入页
- 外部访客问答页

这些前端都不直接调内部业务接口，而是调统一 API 网关。

---

## 2）开放 API 层
建议新增一个独立模块，比如：

- `open_api`
- 或 `public_api`
- 或 `portal_api`

它负责：

- API 鉴权
- 参数校验
- 限流
- 返回统一格式
- 对接内部 service

它**不直接写业务逻辑**，只做“外部输入 -> 内部调用”的适配。

---

## 3）业务服务层
把核心业务收拢为 service：

- 知识库服务
- 文档服务
- 切分服务
- 向量化服务
- 检索服务
- 问答服务
- 会话服务
- 反馈服务

这样后台 API 和开放 API 都复用同一套服务，避免两边逻辑分叉。

---

## 4）数据层
继续沿用现有：

- Knowledge
- Document
- Paragraph
- Chat
- ChatRecord
- Application
- Workspace
- API Key / Token 相关模型

如果现有模型不够，再补开放 API 专属表：

- `OpenApiClient`
- `OpenApiToken`
- `PublicChatSession`
- `PublicAccessPolicy`

---

# 二、推荐的系统边界

我建议你明确三类接口域名/前缀：

## 1）后台管理接口
例如：

- `/api/admin/...`

只给后台管理员或工作空间成员使用。

---

## 2）开放前端接口
例如：

- `/api/open/...`

这是你要重点做的。  
给自定义前端、第三方站点、外部 JS SDK 调用。

---

## 3）内部服务接口
例如：

- `/api/internal/...`

只给系统内部模块调用，不暴露给前端。

---

# 三、开放 API 的设计目标

方案二的核心不是“把现有接口暴露出去”，而是：

> 重新设计一套面向前端的稳定 API 套餐

这个套餐要满足：

- 前端可以创建知识库
- 前端可以上传文档
- 前端可以发起知识问答
- 前端可以拿到引用来源
- 前端可以查看会话历史
- 前端可以做反馈
- 前端可以匿名或半匿名接入

---

# 四、开放 API 的模块拆分

建议拆成 6 个模块。

---

## 模块 1：认证与访问控制

### 目标
让前端页面安全接入，区分不同用户/应用/知识库权限。

### 建议支持的认证方式
优先级从高到低：

1. **用户登录 token**
   给登录用户使用
2. **API Key**
   给第三方系统集成使用
3. **访问令牌 access token**
   给单个前端页面、单个知识库使用
4. **匿名访问**
   仅允许白名单能力，比如只问答、不上传

### 建议能力
- 登录
- 刷新 token
- 获取当前身份
- 获取权限范围
- token 续期
- token 吊销
- IP 白名单
- 限流

---

## 模块 2：知识库管理

### 前端需要的能力
- 新建知识库
- 查看知识库列表
- 查看知识库详情
- 编辑知识库
- 删除知识库
- 查询知识库状态
- 查询知识库统计

### 建议接口
- `GET /api/open/workspaces/{workspace_id}/knowledgebases`
- `POST /api/open/workspaces/{workspace_id}/knowledgebases`
- `GET /api/open/workspaces/{workspace_id}/knowledgebases/{knowledge_id}`
- `PUT /api/open/workspaces/{workspace_id}/knowledgebases/{knowledge_id}`
- `DELETE /api/open/workspaces/{workspace_id}/knowledgebases/{knowledge_id}`

### 返回数据建议
知识库详情至少包含：

- id
- name
- description
- type
- status
- document_count
- paragraph_count
- updated_at
- permissions

---

## 模块 3：文档上传与处理

这是“上传知识库”的核心。

### 前端应该支持的上传方式
建议逐步支持：

1. 文件上传
2. 批量文件上传
3. 文本粘贴
4. FAQ 导入
5. URL 抓取
6. 结构化 JSON 导入

### 建议接口
- `POST /api/open/workspaces/{workspace_id}/knowledgebases/{knowledge_id}/documents`
- `GET /api/open/workspaces/{workspace_id}/knowledgebases/{knowledge_id}/documents`
- `GET /api/open/workspaces/{workspace_id}/knowledgebases/{knowledge_id}/documents/{document_id}`
- `DELETE /api/open/workspaces/{workspace_id}/knowledgebases/{knowledge_id}/documents/{document_id}`
- `POST /api/open/workspaces/{workspace_id}/knowledgebases/{knowledge_id}/documents/{document_id}/reprocess`
- `POST /api/open/workspaces/{workspace_id}/knowledgebases/{knowledge_id}/documents/batch_delete`

### 文档处理状态
前端特别需要这些状态：

- uploaded
- parsing
- chunking
- embedding
- ready
- failed

### 处理建议
文档上传后不要同步阻塞，推荐：

- 上传立即返回 `document_id`
- 后台异步解析
- 前端轮询状态或接收 websocket 通知
- 失败时返回详细错误原因

---

## 模块 4：问答与检索

这是前端页面最重要的第二部分。

### 建议问答模式
1. **知识库问答**
   直接对某个知识库提问
2. **应用问答**
   对一个已配置好的应用提问
3. **检索模式**
   只返回相关片段，不直接生成答案
4. **流式问答**
   前端体验更好
5. **带引用问答**
   返回答案 + 来源片段

### 建议接口
- `POST /api/open/chat/completions`
- `POST /api/open/knowledgebases/{knowledge_id}/chat/completions`
- `POST /api/open/chat/sessions`
- `GET /api/open/chat/sessions/{session_id}`
- `GET /api/open/chat/sessions/{session_id}/messages`
- `POST /api/open/chat/sessions/{session_id}/feedback`
- `POST /api/open/search`

### 推荐请求体
问答请求建议包含：

- question
- session_id
- knowledge_id
- user_id
- stream
- top_k
- temperature
- max_tokens
- return_sources
- return_trace

### 推荐响应体
- answer
- session_id
- message_id
- sources
- tokens
- latency
- confidence
- status

---

## 模块 5：会话与历史记录

前端做知识问答界面，一定会需要：

- 会话列表
- 单会话消息列表
- 删除会话
- 重命名会话
- 标记收藏
- 清空历史

### 建议接口
- `GET /api/open/chat/sessions`
- `POST /api/open/chat/sessions`
- `GET /api/open/chat/sessions/{session_id}`
- `DELETE /api/open/chat/sessions/{session_id}`
- `PATCH /api/open/chat/sessions/{session_id}`
- `GET /api/open/chat/sessions/{session_id}/messages`

---

## 模块 6：反馈与监控

如果你要做真正可运营的知识库问答前端，反馈非常重要。

### 建议能力
- 点赞/点踩
- 纠错反馈
- 无答案反馈
- 命中问题标记
- 问题分类
- 记录用户满意度

### 建议接口
- `POST /api/open/chat/messages/{message_id}/feedback`
- `POST /api/open/chat/messages/{message_id}/report`
- `GET /api/open/stats/usage`
- `GET /api/open/stats/qa_quality`

---

# 五、推荐技术实现方式

## 1）新增独立 app
建议新增：

- `apps/open_api/`

目录可以长这样：

- `views/`
- `serializers/`
- `permissions/`
- `services/`
- `urls.py`
- `schemas/`
- `tests/`

---

## 2）把业务逻辑抽成 service
比如：

- `KnowledgeService`
- `DocumentService`
- `ChatService`
- `RetrievalService`
- `EmbeddingService`
- `AccessControlService`

### 原则
- View 只做 HTTP 适配
- Serializer 做输入输出校验
- Service 做业务编排
- Model 做数据存储

---

## 3）统一返回格式
建议开放 API 使用固定结构，例如：

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "request_id": "xxx"
}
```

失败时统一：

```json
{
  "code": 40001,
  "message": "token expired",
  "data": null
}
```

这样前端好处理，SDK 也好封装。

---

## 4）统一错误码
建议定义：

- `10001` 鉴权失败
- `10002` 权限不足
- `20001` 参数错误
- `20002` 资源不存在
- `30001` 文档上传失败
- `30002` 文档解析失败
- `40001` 问答失败
- `40002` 模型调用失败
- `50001` 系统内部错误

---

# 六、数据库和权限设计建议

## 1）权限模型
建议不是简单的“用户能不能访问”，而是细分为：

- workspace 级权限
- knowledgebase 级权限
- document 级权限
- chat session 级权限
- API key 级权限

---

## 2）API Key 设计
建议新增 API Key 模型，至少包括：

- id
- name
- key_hash
- workspace_id
- knowledge_id（可选）
- scopes
- expired_at
- status
- last_used_at
- created_by

### scopes 例子
- `knowledge:read`
- `knowledge:write`
- `document:upload`
- `document:delete`
- `chat:ask`
- `chat:history`
- `chat:feedback`

---

## 3）匿名前端场景
如果你希望外部网页可以直接问答，不想登录，那么建议给每个知识库签发一个：

- `public_access_token`

这个 token 只能做：

- 问答
- 检索
- 查看公开会话

不能做：

- 上传
- 删除
- 修改配置

---

# 七、前端页面怎么接

你自定义前端建议做成 3 个页面域：

## 1）知识库管理页
功能：

- 新建知识库
- 上传文件
- 查看处理进度
- 列出文档
- 删除文档

---

## 2）知识问答页
功能：

- 选择知识库
- 输入问题
- 流式返回
- 展示引用来源
- 查看历史对话

---

## 3）运营分析页
功能：

- 总问答量
- 命中率
- 无答案率
- 用户满意度
- 热门问题
- 高频失败文档

---

# 八、开发顺序建议

我建议按下面顺序落地。

## 第一阶段
做最小可用闭环：

1. API 鉴权
2. 创建知识库
3. 上传文档
4. 文档状态查询
5. 问答接口
6. 流式问答
7. 历史会话

这个阶段完成后，前端就能跑起来。

---

## 第二阶段
补齐运营能力：

1. 文档批量上传
2. 删除与重建
3. 引用来源
4. 点赞点踩
5. 会话管理
6. 统计报表

---

## 第三阶段
增强开放能力：

1. API Key 管理
2. 匿名访问
3. Webhook
4. SDK
5. OpenAPI 文档
6. 速率限制与审计

---

# 九、建议的接口分层图

你可以理解成下面这样：

```text
前端页面
   ↓
Open API 层
   ↓
Service 层
   ↓
知识库/文档/问答/检索核心逻辑
   ↓
数据库 + 向量库 + 模型服务
```

---

# 十、我建议你最终落地成这 4 个核心模块

如果你准备正式开发，我建议先按这 4 个模块开工：

### 1. `open_auth`
负责：
- token
- api key
- 权限

### 2. `open_knowledge`
负责：
- 知识库管理
- 文档上传
- 文档状态
- 删除重建

### 3. `open_chat`
负责：
- 问答
- 流式输出
- 会话
- 历史消息

### 4. `open_analytics`
负责：
- 反馈
- 统计
- 质量监控

---

# 十一、最推荐的落地方案

如果你问我“最稳妥的方案二怎么做”，我会建议：

1. **不要直接暴露现有后台接口**
2. **新建 `open_api` 模块**
3. **统一使用 token / api key 鉴权**
4. **知识库上传和问答作为两个主入口**
5. **所有业务逻辑复用现有 service**
6. **所有开放接口统一做版本号，例如 `/api/open/v1/...`**

---

如果你愿意，我下一步可以直接继续帮你产出下面任意一种内容：

1. **`open_api` 模块的目录结构设计**
2. **开放接口清单（按请求/响应字段详细列出）**
3. **数据库表设计**
4. **后端 Django 实现骨架**
5. **前端页面交互流程图**

