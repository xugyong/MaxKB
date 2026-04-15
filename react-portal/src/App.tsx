import { useEffect, useMemo, useState } from 'react'
import { apiRequest, buildUrl } from './api'

type Page = 'knowledge' | 'chat'

type KnowledgeItem = {
  id: string
  name: string
  desc: string
  status?: string
}

type DocumentItem = {
  id: string
  name: string
  status?: string
  status_meta?: Record<string, unknown>
  create_time?: string
}

type ChatSession = {
  id: string
  abstract: string
  create_time?: string
  update_time?: string
}

type ChatRecord = {
  id: string
  problem_text: string
  answer_text: string
  create_time?: string
}

type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

type KnowledgeListResponse = { items: KnowledgeItem[] }
type DocumentListResponse = { items: DocumentItem[] }
type SessionListResponse = { items: ChatSession[] }
type RecordListResponse = { items: ChatRecord[] }
type CreateKnowledgeResponse = { knowledge_id: string }
type CreateDocumentResponse = { document_id: string; status?: string }
type ChatCompletionResponse = { answer?: string; session_id?: string; sources?: unknown[] }

export default function App() {
  const [page, setPage] = useState<Page>('knowledge')
  const [workspaceId, setWorkspaceId] = useState('default')
  const [apiToken, setApiToken] = useState('')
  const [knowledgeList, setKnowledgeList] = useState<KnowledgeItem[]>([])
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [records, setRecords] = useState<ChatRecord[]>([])
  const [activeKnowledgeId, setActiveKnowledgeId] = useState('')
  const [activeSessionId, setActiveSessionId] = useState('')
  const [knowledgeName, setKnowledgeName] = useState('')
  const [knowledgeDesc, setKnowledgeDesc] = useState('')
  const [textContent, setTextContent] = useState('')
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [question, setQuestion] = useState('')
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [answer, setAnswer] = useState('')
  const authHeaders = useMemo(() => (apiToken ? { Authorization: `Bearer ${apiToken}` } : {}), [apiToken])

  async function loadKnowledge() {
    const data = await apiRequest<KnowledgeListResponse>(buildUrl(`/api/open/v1/workspaces/${workspaceId}/knowledgebases`), undefined, apiToken)
    setKnowledgeList(data.data?.items || [])
  }

  async function loadDocuments(knowledgeId: string) {
    if (!knowledgeId) return
    const data = await apiRequest<DocumentListResponse>(buildUrl(`/api/open/v1/workspaces/${workspaceId}/knowledgebases/${knowledgeId}/documents`), undefined, apiToken)
    setDocuments(data.data?.items || [])
  }

  async function loadSessions() {
    const params = new URLSearchParams()
    params.set('application_id', activeKnowledgeId || workspaceId)
    const data = await apiRequest<SessionListResponse>(buildUrl(`/api/open/v1/chat/sessions?${params.toString()}`), undefined, apiToken)
    setSessions(data.data?.items || [])
  }

  async function loadRecords(sessionId: string) {
    if (!sessionId) return
    const data = await apiRequest<RecordListResponse>(buildUrl(`/api/open/v1/chat/sessions/${sessionId}/messages`), undefined, apiToken)
    setRecords(data.data?.items || [])
  }

  useEffect(() => {
    loadKnowledge()
  }, [])

  async function createKnowledge() {
    const data = await apiRequest<CreateKnowledgeResponse>(buildUrl(`/api/open/v1/workspaces/${workspaceId}/knowledgebases`), {
      method: 'POST',
      body: JSON.stringify({ name: knowledgeName, desc: knowledgeDesc }),
    }, apiToken)
    setKnowledgeName('')
    setKnowledgeDesc('')
    if (data.data?.knowledge_id) {
      setActiveKnowledgeId(data.data.knowledge_id)
    }
    await loadKnowledge()
  }

  async function uploadTextDocument() {
    if (!activeKnowledgeId) return
    await apiRequest<CreateDocumentResponse>(buildUrl(`/api/open/v1/workspaces/${workspaceId}/knowledgebases/${activeKnowledgeId}/documents`), {
      method: 'POST',
      body: JSON.stringify({ name: uploadFile?.name || 'text-document', text: textContent }),
    }, apiToken)
    setTextContent('')
    await loadDocuments(activeKnowledgeId)
  }

  async function uploadFileDocument() {
    if (!activeKnowledgeId || !uploadFile) return
    const form = new FormData()
    form.append('file', uploadFile)
    form.append('name', uploadFile.name)
    const data = await apiRequest<CreateDocumentResponse>(buildUrl(`/api/open/v1/workspaces/${workspaceId}/knowledgebases/${activeKnowledgeId}/documents`), {
      method: 'POST',
      body: form,
      headers: authHeaders,
    }, apiToken)
    if (data.data?.document_id) {
      setUploadFile(null)
    }
    await loadDocuments(activeKnowledgeId)
  }

  async function reprocessDocument(documentId: string) {
    if (!activeKnowledgeId) return
    await apiRequest(buildUrl(`/api/open/v1/workspaces/${workspaceId}/knowledgebases/${activeKnowledgeId}/documents/${documentId}/reprocess`), {
      method: 'POST',
      body: JSON.stringify({}),
    }, apiToken)
    await loadDocuments(activeKnowledgeId)
  }

  async function deleteDocument(documentId: string) {
    if (!activeKnowledgeId) return
    await apiRequest(buildUrl(`/api/open/v1/workspaces/${workspaceId}/knowledgebases/${activeKnowledgeId}/documents/${documentId}`), {
      method: 'DELETE',
    }, apiToken)
    await loadDocuments(activeKnowledgeId)
  }

  async function askQuestion() {
    const currentMessages: ChatMessage[] = [...chatMessages, { role: 'user', content: question }]
    setChatMessages(currentMessages)
    const data = await apiRequest<ChatCompletionResponse>(buildUrl(`/api/open/v1/chat/completions`), {
      method: 'POST',
      body: JSON.stringify({
        application_id: activeKnowledgeId || workspaceId,
        stream: false,
        messages: currentMessages,
      }),
    }, apiToken)
    const nextAnswer = data.data?.answer || data.message || '(empty)'
    setAnswer(nextAnswer)
    setChatMessages([...currentMessages, { role: 'assistant', content: nextAnswer }])
    setQuestion('')
    await loadSessions()
  }

  async function openSession(sessionId: string) {
    setActiveSessionId(sessionId)
    await loadRecords(sessionId)
  }

  return (
    <div className="app-shell">
      <div className="container">
        <div className="hero">
          <div>
            <span className="badge">MaxKB React Portal</span>
            <h1>知识库上传 + 问答</h1>
            <p>独立 React 前端，直接对接本地 Docker 后端。</p>
          </div>
          <div className="tabs">
            <button className={`tab ${page === 'knowledge' ? 'active' : ''}`} onClick={() => setPage('knowledge')}>知识库</button>
            <button className={`tab ${page === 'chat' ? 'active' : ''}`} onClick={() => setPage('chat')}>问答</button>
          </div>
        </div>

        <div className="panel" style={{ marginBottom: 16 }}>
          <div className="grid-2">
            <label>
              <span>workspace_id</span>
              <input value={workspaceId} onChange={(e) => setWorkspaceId(e.target.value)} />
            </label>
            <label>
              <span>Bearer API Token</span>
              <input value={apiToken} onChange={(e) => setApiToken(e.target.value)} placeholder="可留空，用于后续认证" />
            </label>
          </div>
        </div>

        {page === 'knowledge' ? (
          <div className="stack">
            <div className="panel">
              <div className="panel-head">
                <h2>创建知识库</h2>
                <button className="primary" onClick={createKnowledge} disabled={!knowledgeName}>创建</button>
              </div>
              <div className="grid-2">
                <label>
                  <span>名称</span>
                  <input value={knowledgeName} onChange={(e) => setKnowledgeName(e.target.value)} placeholder="例如：产品知识库" />
                </label>
                <label>
                  <span>描述</span>
                  <input value={knowledgeDesc} onChange={(e) => setKnowledgeDesc(e.target.value)} placeholder="可选" />
                </label>
              </div>
            </div>

            <div className="panel">
              <div className="panel-head">
                <h2>知识库列表</h2>
                <button onClick={loadKnowledge}>刷新</button>
              </div>
              <div className="table">
                {knowledgeList.length === 0 ? (
                  <div className="empty">暂无知识库</div>
                ) : knowledgeList.map((item) => (
                  <button
                    key={item.id}
                    className={`list-card ${activeKnowledgeId === item.id ? 'active' : ''}`}
                    onClick={() => {
                      setActiveKnowledgeId(item.id)
                      loadDocuments(item.id)
                    }}
                  >
                    <div>
                      <div><strong>{item.name}</strong></div>
                      <div className="muted">{item.desc || '无描述'}</div>
                    </div>
                    <div className="meta">
                      <span>{item.status || 'unknown'}</span>
                      <small>{item.id}</small>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="panel">
              <div className="panel-head">
                <h2>文档上传与管理</h2>
                <button onClick={() => loadDocuments(activeKnowledgeId)} disabled={!activeKnowledgeId}>刷新文档</button>
              </div>
              <div className="grid-2">
                <label>
                  <span>当前知识库</span>
                  <input value={activeKnowledgeId} onChange={(e) => setActiveKnowledgeId(e.target.value)} placeholder="点击知识库后自动填充" />
                </label>
                <label>
                  <span>文件上传</span>
                  <input type="file" onChange={(e) => setUploadFile(e.target.files?.[0] || null)} />
                </label>
              </div>
              <div className="row">
                <button className="primary" onClick={uploadFileDocument} disabled={!activeKnowledgeId || !uploadFile}>上传文件</button>
              </div>
              <div style={{ marginTop: 16 }}>
                <label>
                  <span>文本内容</span>
                  <textarea rows={8} value={textContent} onChange={(e) => setTextContent(e.target.value)} placeholder="粘贴内容后可直接创建文本文档" />
                </label>
                <div className="row">
                  <button className="primary" onClick={uploadTextDocument} disabled={!activeKnowledgeId || !textContent.trim()}>上传文本</button>
                </div>
              </div>
            </div>

            <div className="panel">
              <div className="panel-head">
                <h2>文档列表</h2>
                <span className="hint">知识库：{activeKnowledgeId || '未选择'}</span>
              </div>
              <div className="table">
                {documents.length === 0 ? (
                  <div className="empty">暂无文档</div>
                ) : documents.map((doc) => (
                  <div key={doc.id} className="doc-card">
                    <div>
                      <div><strong>{doc.name}</strong></div>
                      <div className="muted">状态：{doc.status || 'unknown'}</div>
                      <div className="muted">{doc.id}</div>
                    </div>
                    <div className="row" style={{ margin: 0, width: 'auto' }}>
                      <button onClick={() => reprocessDocument(doc.id)}>重处理</button>
                      <button onClick={() => deleteDocument(doc.id)}>删除</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="stack">
            <div className="panel">
              <div className="panel-head">
                <h2>问答</h2>
                <button onClick={loadSessions}>刷新会话</button>
              </div>
              <div className="grid-2">
                <label>
                  <span>知识库 / 应用 ID</span>
                  <input value={activeKnowledgeId} onChange={(e) => setActiveKnowledgeId(e.target.value)} placeholder="用于问答调用" />
                </label>
                <label>
                  <span>问题</span>
                  <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="输入你的问题" />
                </label>
              </div>
              <div className="row">
                <button className="primary" onClick={askQuestion} disabled={!question.trim()}>发送</button>
              </div>
              <div style={{ marginTop: 14 }} className="muted">最新回答：{answer || '暂无'}</div>
            </div>

            <div className="panel">
              <div className="panel-head">
                <h2>当前会话</h2>
                <span className="hint">activeSessionId: {activeSessionId || 'none'}</span>
              </div>
              <div className="chat-box">
                {chatMessages.length === 0 ? (
                  <div className="empty">还没有聊天记录</div>
                ) : chatMessages.map((msg, index) => (
                  <div key={index} className={`bubble ${msg.role}`}>
                    <div className="role">{msg.role}</div>
                    <div>{msg.content}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel">
              <div className="panel-head">
                <h2>会话历史</h2>
                <span className="hint">共 {sessions.length} 条</span>
              </div>
              <div className="table">
                {sessions.length === 0 ? (
                  <div className="empty">暂无会话</div>
                ) : sessions.map((session) => (
                  <button key={session.id} className={`list-card ${activeSessionId === session.id ? 'active' : ''}`} onClick={() => openSession(session.id)}>
                    <div>
                      <div><strong>{session.abstract || '未命名会话'}</strong></div>
                      <div className="muted">{session.id}</div>
                    </div>
                    <div className="meta">
                      <span>{session.update_time || session.create_time || '-'}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="panel">
              <div className="panel-head">
                <h2>会话消息</h2>
                <span className="hint">{activeSessionId || '未选择会话'}</span>
              </div>
              <div className="chat-box">
                {records.length === 0 ? (
                  <div className="empty">点击会话查看消息</div>
                ) : records.map((record) => (
                  <div key={record.id} className="bubble assistant">
                    <div className="role">Q</div>
                    <div style={{ marginBottom: 8 }}>{record.problem_text}</div>
                    <div className="role">A</div>
                    <div>{record.answer_text}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
