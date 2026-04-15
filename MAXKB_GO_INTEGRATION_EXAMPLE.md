# MaxKB 第三方接入文档（示例）

> 本文档已并入主接入文档体系。封板与验收请以 `MAXKB_THIRD_PARTY_INTEGRATION.md` 为准；本文保留为 Go 侧实现示例与参考。

---

## 1. 推荐架构

```text
小程序 / 管理后台
    ↓
你的 Go 后台（统一鉴权、权限、日志、业务映射）
    ↓
MaxKB Open API
```

### 原则
- 小程序不直接访问 MaxKB
- Go 后台持有 MaxKB 的 API Key
- Go 后台对外提供稳定业务接口
- MaxKB 只做 AI 能力层

---

## 2. 你需要准备的 MaxKB 信息

### 必须有
- `workspace_id`
- `application_id`
- `api_key`（MaxKB 的 Bearer Token）
- 目标知识库 ID（如果你要做管理）

### 可选
- `chat_id`：用于延续会话
- `user_id`：你自己系统里的用户 ID
- `tenant_id`：你自己系统里的租户 ID

---

## 3. 问答接口

### 请求地址
```text
POST /api/open/v1/chat/completions
```

### 请求头
```http
Authorization: Bearer <MAXKB_API_KEY>
Content-Type: application/json
```

### 请求体
```json
{
  "application_id": "019d8eab-65db-7a03-8b73-ad5178fc69e1",
  "chat_id": "",
  "stream": false,
  "re_chat": false,
  "messages": [
    {
      "role": "user",
      "content": "上海南的文档怎么上传？"
    }
  ]
}
```

### 返回体
```json
{
  "code": 0,
  "message": "chat completion ok",
  "data": {
    "session_id": "019d8eab-65db-7a03-8b73-ad5178fc69e1",
    "message_id": "019d8eab-65db-7a03-8b73-ad5178fc69e2",
    "answer": "...",
    "sources": [],
    "usage": {
      "message_tokens": 10,
      "answer_tokens": 120,
      "total_tokens": 130
    },
    "finish_reason": "stop",
    "stream": false,
    "status": "ok"
  }
}
```

---

## 4. Go 侧完整调用示例

下面给一个可直接改造的 `net/http` 示例。

### 4.1 定义请求与响应结构

```go
package maxkb

type ChatMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ChatCompletionRequest struct {
	ApplicationID string        `json:"application_id"`
	ChatID        string        `json:"chat_id,omitempty"`
	Stream        bool          `json:"stream"`
	ReChat        bool          `json:"re_chat"`
	Messages      []ChatMessage `json:"messages"`
}

type ChatCompletionResponse struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
	Data    struct {
		SessionID     string `json:"session_id"`
		MessageID     string `json:"message_id"`
		Answer        string `json:"answer"`
		FinishReason  string `json:"finish_reason"`
		Status        string `json:"status"`
		Stream        bool   `json:"stream"`
		Usage         struct {
			MessageTokens int `json:"message_tokens"`
			AnswerTokens   int `json:"answer_tokens"`
			TotalTokens    int `json:"total_tokens"`
		} `json:"usage"`
		Sources []any `json:"sources"`
	} `json:"data"`
}
```

### 4.2 封装 MaxKB Client

```go
package maxkb

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type Client struct {
	BaseURL string
	APIKey  string
	HTTP    *http.Client
}

func NewClient(baseURL, apiKey string) *Client {
	return &Client{
		BaseURL: baseURL,
		APIKey:  apiKey,
		HTTP: &http.Client{
			Timeout: 120 * time.Second,
		},
	}
}

func (c *Client) Ask(reqBody ChatCompletionRequest) (*ChatCompletionResponse, error) {
	payload, err := json.Marshal(reqBody)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest("POST", c.BaseURL+"/api/open/v1/chat/completions", bytes.NewReader(payload))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+c.APIKey)

	resp, err := c.HTTP.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("maxkb http error: %d, body=%s", resp.StatusCode, string(body))
	}

	var out ChatCompletionResponse
	if err := json.Unmarshal(body, &out); err != nil {
		return nil, err
	}

	if out.Code != 0 {
		return nil, fmt.Errorf("maxkb api error: %s", out.Message)
	}

	return &out, nil
}
```

### 4.3 业务层调用

```go
package service

import "your-module/maxkb"

func AskKnowledgeBase() error {
	client := maxkb.NewClient("http://localhost:8080", "your-maxkb-api-key")

	resp, err := client.Ask(maxkb.ChatCompletionRequest{
		ApplicationID: "019d8eab-65db-7a03-8b73-ad5178fc69e1",
		Stream:        false,
		ReChat:        false,
		Messages: []maxkb.ChatMessage{{
			Role:    "user",
			Content: "上海南的文档怎么上传？",
		}},
	})
	if err != nil {
		return err
	}

	println("answer:", resp.Data.Answer)
	println("session:", resp.Data.SessionID)
	return nil
}
```

---

## 5. Go 侧建议的业务流程

### 5.1 用户发起问答
1. 小程序调用 Go 后台
2. Go 后台校验用户登录态
3. Go 后台根据用户所属租户，找到对应 `application_id`
4. Go 后台调用 MaxKB `chat/completions`
5. Go 后台把答案返回给小程序
6. Go 后台保存 session 和 message 映射

### 5.2 知识库上传
1. 管理后台创建知识库
2. Go 后台先做文件格式校验
3. Go 后台调用 MaxKB 创建知识库/上传文档
4. Go 后台记录 `knowledge_id` 和 `document_id`
5. 后台轮询文档状态
6. 前端展示状态

---

## 6. 推荐的 Go 数据表

### `maxkb_application_bindings`
- `id`
- `tenant_id`
- `workspace_id`
- `application_id`
- `api_key_id`
- `status`
- `created_at`

### `maxkb_chat_sessions`
- `id`
- `tenant_id`
- `user_id`
- `application_id`
- `maxkb_chat_id`
- `created_at`

### `maxkb_chat_messages`
- `id`
- `session_id`
- `role`
- `content`
- `maxkb_message_id`
- `created_at`

---

## 7. 错误处理建议

### MaxKB 返回 `401`
- API Key 不对
- key 已过期
- key 没有权限

### MaxKB 返回 `500`
- 应用不存在
- 应用未发布
- 模型不可用
- 知识库/文档配置问题

### Go 侧建议转译
- `401` -> 未登录 / 无权限
- `403` -> 禁止访问
- `404` -> 资源不存在
- `500` -> AI 服务异常

---

## 8. 你们落地时的推荐顺序

1. 先接 `chat/completions`
2. 再接知识库管理
3. 再接文档上传
4. 再接会话历史
5. 最后做权限和审计

---

## 9. 最后一句话

**Go 负责业务，MaxKB 负责 AI，前端只调用 Go。**

这是最稳的第三方接入方式。
