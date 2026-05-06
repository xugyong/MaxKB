# MaxKB 小程序开发需求说明书 v1

## 1. 文档信息

- 文档名称：MaxKB 小程序开发需求说明书 v1
- 目标平台：统一小程序
- 基础工程：`MaxKB/miniprogram`
- 参考来源：`MaxKB/ui/src/views/chat/README.md`
- 目标版本：MVP

---

## 2. 项目背景

MaxKB Web 端已具备完整的对话页面能力，包括：

- 多会话管理
- 流式问答
- 历史记录
- 消息详情
- 分享能力
- 用户输入表单
- 主题定制

本项目需要基于现有小程序脚手架，开发一版可用的小程序聊天应用，优先覆盖核心对话链路，并尽量保持与 Web 端一致的交互体验。

---

## 3. 项目目标

### 3.1 业务目标

- 在小程序中实现基础 AI 对话能力
- 支持历史会话管理
- 支持流式回复展示
- 支持分享与消息详情查看
- 支持前置用户输入表单

### 3.2 技术目标

- 基于 `MaxKB/miniprogram` 脚手架实现
- 兼容统一小程序运行环境
- 与后端 API 完成可联调闭环
- 为后续扩展附件、反馈、语音等能力保留接口设计空间

---

## 4. 范围说明

### 4.1 第一版必须实现的功能

1. 聊天主页面
2. 流式消息发送与展示
3. 历史会话列表
4. 新建会话
5. 删除会话
6. 清空会话
7. 会话切换
8. 消息历史分页加载
9. 分享链接生成与复制
10. 用户输入表单
11. 消息详情查看（执行详情或知识来源，至少实现一个）
12. 应用主题配置展示

### 4.2 第一版暂不强制实现的功能

- PDF / HTML / Markdown 导出
- 点赞 / 点踩反馈
- 语音输入 / 语音播报
- 高级附件上传与预览
- 复杂权限体系
- PC 版右侧详情面板的完整复刻

---

## 5. 小程序平台确认

### 5.1 平台类型

- 目标为统一小程序
- 当前工程以 `MaxKB/miniprogram` 为基础
- 页面体验优先对齐 Web 端移动版聊天页

### 5.2 平台能力假设

开发默认支持以下能力：

- 页面跳转
- 请求接口
- 本地缓存
- 消息列表滚动
- 基础弹层 / 抽屉
- 复制文本 / 链接
- 分享能力
- 文件上传

### 5.3 需重点确认的平台限制

以下能力需在开发前确认可用性：

- 流式响应处理
- 长连接 / SSE / chunked response
- 录音与语音识别
- 文件预览
- 小程序分享卡片
- 统一小程序环境对网络请求的限制

---

## 6. 必做功能列表

### 6.1 聊天主页面

页面应包含：

- 顶部应用信息栏
- 消息列表区域
- 输入框区域
- 发送按钮
- 回到底部按钮
- 加载中状态

### 6.2 历史会话管理

应支持：

- 历史会话列表展示
- 切换历史会话
- 新建会话
- 删除单个会话
- 清空全部会话
- 会话标题展示

### 6.3 消息能力

应支持：

- 用户输入问题
- 流式显示回答
- 消息状态展示
- 历史消息分页加载
- 上拉加载更早记录

### 6.4 详情能力

至少实现以下一种：

- 执行详情
- 知识来源详情

若资源允许，建议优先实现执行详情。

### 6.5 分享能力

应支持：

- 生成分享链接
- 复制分享链接
- 打开分享页后查看内容

### 6.6 用户输入表单

若后端工作流要求前置输入，需支持：

- 首次进入展示表单
- 表单字段校验
- 表单数据缓存
- 未完成表单时禁止发送消息

---

## 7. 登录与鉴权方式

### 7.1 推荐方案

建议采用以下两种方式之一：

#### 方案 A：匿名访问 + accessToken

适用于公开聊天场景。

流程：

1. 用户进入小程序
2. 调用匿名认证接口
3. 后端返回 `accessToken`
4. 后续请求携带 `accessToken`

#### 方案 B：账号登录

适用于需要用户身份管理的场景。

流程：

1. 用户完成登录
2. 获取 token
3. 进入聊天页面并调用接口

### 7.2 请求鉴权要求

建议所有接口统一使用以下方式之一：

- `Authorization: Bearer <token>`
- 或后端约定的 `accessToken`

### 7.3 需要后端明确的规则

- token 获取方式
- token 过期与刷新机制
- 分享页是否免登录
- 匿名用户是否允许创建会话
- 上传接口是否需要鉴权

---

## 8. 流式接口协议样例

### 8.1 发送消息接口

```http
POST /chat_message/{chat_id}
Content-Type: application/json
Authorization: Bearer <token>
```

### 8.2 请求体样例

```json
{
  "content": "帮我总结这篇文档",
  "files": [],
  "stream": true,
  "user_input": {
    "company_name": "Finogeeks",
    "industry": "互联网"
  }
}
```

### 8.3 推荐流式协议

为便于小程序端实现，建议后端明确为以下一种：

- SSE
- chunked JSON
- WebSocket
- 自定义分片 JSON

建议优先采用 **分片 JSON** 或 **SSE**。

### 8.4 推荐分片消息格式

#### 开始回答

```json
{
  "event": "start",
  "chat_id": "chat_202604270001",
  "record_id": "record_90001"
}
```

#### 增量文本

```json
{
  "event": "delta",
  "record_id": "record_90001",
  "content": "你可以先创建知识库，"
}
```

#### 来源信息

```json
{
  "event": "source",
  "record_id": "record_90001",
  "source_list": [
    {
      "paragraph_id": "para_1001",
      "document_name": "产品使用手册",
      "score": 0.92,
      "content": "先创建知识库，再上传文档。"
    }
  ]
}
```

#### 执行详情

```json
{
  "event": "execution_detail",
  "record_id": "record_90001",
  "execution_details": [
    {
      "node_id": "search-knowledge-node",
      "node_name": "知识库检索",
      "status": "success"
    }
  ]
}
```

#### 结束回答

```json
{
  "event": "end",
  "record_id": "record_90001",
  "status": 200
}
```

#### 错误

```json
{
  "event": "error",
  "record_id": "record_90001",
  "status": 500,
  "message": "模型服务不可用"
}
```

### 8.5 前端处理规则

- `start`：创建本地临时消息
- `delta`：持续拼接回答文本
- `source`：补充来源数据
- `execution_detail`：补充执行详情数据
- `end`：标记回答完成
- `error`：展示错误状态，允许重试

---

## 9. 消息 / 会话数据返回样例

### 9.1 应用信息返回样例

```json
{
  "id": "app_10001",
  "name": "MaxKB 智能助手",
  "icon": "https://example.com/icon.png",
  "chat_background": "https://example.com/bg.png",
  "show_history": true,
  "custom_theme": {
    "theme_color": "#3370FF",
    "header_font_color": "#FFFFFF"
  }
}
```

### 9.2 会话列表返回样例

```json
{
  "count": 12,
  "page": 1,
  "size": 20,
  "list": [
    {
      "id": "chat_202604270001",
      "abstract": "如何生成知识库文档？",
      "create_time": "2026-04-27 10:12:30",
      "update_time": "2026-04-27 10:14:18"
    }
  ]
}
```

### 9.3 单个会话消息列表返回样例

```json
{
  "chat_id": "chat_202604270001",
  "count": 2,
  "page": 1,
  "size": 20,
  "list": [
    {
      "id": "record_90001",
      "chat_id": "chat_202604270001",
      "record_id": 90001,
      "problem_text": "如何生成知识库文档？",
      "answer_text": "你可以先创建知识库，然后上传文档。",
      "answer_text_list": [
        [
          {
            "type": "text",
            "content": "你可以先创建知识库，然后上传文档。"
          }
        ]
      ],
      "status": 200,
      "write_ed": true,
      "is_stop": false,
      "vote_status": "-1",
      "reasoning_content": "",
      "source_list": [
        {
          "paragraph_id": "para_1001",
          "document_name": "产品使用手册",
          "score": 0.92,
          "content": "先创建知识库，再上传文档。"
        }
      ],
      "execution_details": [
        {
          "node_id": "search-knowledge-node",
          "node_name": "知识库检索",
          "status": "success"
        }
      ]
    }
  ]
}
```

### 9.4 单条消息详情返回样例

```json
{
  "id": "record_90001",
  "chat_id": "chat_202604270001",
  "record_id": 90001,
  "problem_text": "如何生成知识库文档？",
  "answer_text": "你可以先创建知识库，然后上传文档。",
  "source_list": [
    {
      "paragraph_id": "para_1001",
      "document_name": "产品使用手册",
      "score": 0.92,
      "content": "先创建知识库，再上传文档。"
    }
  ],
  "execution_details": [
    {
      "node_id": "search-knowledge-node",
      "node_name": "知识库检索",
      "status": "success",
      "output": {
        "hits": 3
      }
    }
  ]
}
```

### 9.5 新建会话返回样例

```json
{
  "chat_id": "chat_202604270001",
  "status": 200
}
```

### 9.6 分享链接返回样例

```json
{
  "link": "share_8f3c2a1b"
}
```

---

## 10. 页面结构建议

### 10.1 页面组成

建议小程序至少包含以下模块：

- 聊天主页面
- 历史会话抽屉
- 消息详情弹层
- 用户输入表单弹层
- 分享选择模式

### 10.2 推荐组件划分

- `ChatPage`
- `ChatHeader`
- `ChatMessageList`
- `ChatMessageItem`
- `ChatInputBar`
- `HistoryDrawer`
- `MessageDetailDrawer`
- `UserInputFormPopup`
- `ShareSelectBar`

---

## 11. 状态定义建议

### 11.1 页面状态

- `loading`
- `ready`
- `empty`
- `error`

### 11.2 会话状态

- `new`
- `existing`
- `sending`
- `failed`

### 11.3 面板状态

- `none`
- `history`
- `detail`
- `share`
- `userForm`

### 11.4 消息状态

- `writing`
- `done`
- `stopped`
- `failed`

---

## 12. 联调优先级建议

建议按以下顺序接入：

1. 应用信息接口
2. 历史会话列表接口
3. 单会话消息列表接口
4. 新建会话接口
5. 流式消息接口
6. 分享接口
7. 删除 / 清空接口
8. 消息详情接口
9. 用户输入表单配置
10. 上传接口

---

## 13. 里程碑建议

### 阶段 1：最小闭环

目标：可聊天、可看历史、可切换会话、可流式回复。

### 阶段 2：补齐核心产品能力

目标：分享、详情、表单、历史分页完善。

### 阶段 3：增强能力

目标：附件、反馈、语音、导出等扩展功能。

---

## 14. 验收标准

### 14.1 功能验收

- 可正常进入聊天页
- 可发送消息并看到流式回复
- 可查看历史会话并切换
- 可新建、删除、清空会话
- 可生成并复制分享链接
- 可展示用户输入表单
- 可查看至少一种消息详情

### 14.2 体验验收

- 新消息自动滚动到底部
- 上滑不强制打断用户阅读
- 流式输出过程可见
- 错误状态可重试
- 空状态与加载状态清晰

### 14.3 接口验收

- 请求参数与返回字段一致
- 流式协议可被小程序稳定消费
- 分享页可以独立打开
- 历史分页可正确翻页

---

## 15. 待确认事项

以下内容需要在开发前最终确认：

- 统一小程序平台的具体能力边界
- 流式返回协议的最终格式
- 登录 / 鉴权方式
- 分享页是否免登录
- 是否需要附件上传 MVP
- 详情面板是否优先做执行详情或知识来源

---

## 16. 结论

本需求说明书已覆盖 MaxKB 小程序第一版开发所需的最小信息集。只要补齐接口协议、鉴权方式和平台能力边界，即可进入正式开发与联调阶段。
