const { mockApplicationDetail, mockChatList, mockChatRecordList, mockShareLink } = require('./mock-data')
const { createApplicationDetail, createChatSummary, createRecordItem } = require('./chat-model')

const DEFAULT_TIMEOUT = 15000
const STREAM_TIMEOUT = 600000
const decoder = typeof TextDecoder !== 'undefined' ? new TextDecoder('utf-8') : null

const config = {
  baseURL: 'http://localhost:3001/chat/api',
  tokenKey: 'accessToken',
  useMock: false
}

const request = options => {
  const token = ft.getStorageSync(config.tokenKey)
  const language = ft.getStorageSync('language') || 'zh-CN'
  const header = Object.assign(
    {
      'Content-Type': 'application/json',
      'Accept-Language': language
    },
    options.header || {}
  )

  if (token && !options.skipAuth) {
    header.authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    ft.request({
      url: `${config.baseURL}${options.url}`,
      method: options.method || 'GET',
      data: options.data || {},
      params: options.params || {},
      header,
      timeout: options.timeout || DEFAULT_TIMEOUT,
      success: res => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
          return
        }
        reject({
          message: res.data && res.data.message ? res.data.message : '请求失败',
          statusCode: res.statusCode,
          data: res.data,
          url: `${config.baseURL}${options.url}`,
          method: options.method || 'GET'
        })
      },
      fail: error => {
        reject({
          message: error && error.message ? error.message : '网络请求失败',
          raw: error,
          url: `${config.baseURL}${options.url}`,
          method: options.method || 'GET'
        })
      }
    })
  })
}

const api = {
  setBaseURL(baseURL) {
    config.baseURL = baseURL || 'http://localhost:3001/chat/api'
  },

  async chatProfile(accessToken) {
    return request({ url: '/profile', params: { access_token: accessToken }, skipAuth: true })
  },

  async anonymousAuthentication(accessToken) {
    return request({
      url: '/auth/anonymous',
      method: 'POST',
      data: { access_token: accessToken }
    })
  },

  async passwordAuthentication(accessToken, password) {
    return request({
      url: '/auth/password',
      method: 'POST',
      data: { access_token: accessToken, password }
    })
  },

  async login(accessToken, payload) {
    return request({
      url: `/auth/login/${accessToken}`,
      method: 'POST',
      data: payload
    })
  },

  async ldapLogin(accessToken, payload) {
    return request({
      url: `/auth/ldap/login/${accessToken}`,
      method: 'POST',
      data: payload
    })
  },

  async authenticate(accessToken, payload = {}) {
    const profile = await this.chatProfile(accessToken)
    const authenticationType = String(
      profile && (profile.authentication_type || profile.authentication || 'anonymous')
    ).toLowerCase()

    let authResponse = null
    let token = null

    if (
      authenticationType === 'anonymous' ||
      authenticationType === 'anonymous_user' ||
      authenticationType === 'chat_anonymous_user'
    ) {
      authResponse = await this.anonymousAuthentication(accessToken)
    } else if (authenticationType === 'password') {
      if (payload.password) {
        authResponse = await this.passwordAuthentication(accessToken, payload.password)
      }
    } else if (authenticationType === 'login') {
      if (payload.loginRequest) {
        authResponse = await this.login(accessToken, payload.loginRequest)
      }
    } else if (authenticationType === 'ldap') {
      if (payload.loginRequest) {
        authResponse = await this.ldapLogin(accessToken, payload.loginRequest)
      }
    }

    token =
      (authResponse && authResponse.token) ||
      (authResponse && authResponse.data && authResponse.data.token) ||
      (authResponse && authResponse.data) ||
      authResponse ||
      this.getToken()

    if (token) {
      this.setToken(token)
    }

    return {
      profile,
      token,
      authenticationType,
      authResponse
    }
  },

  setToken(token) {
    ft.setStorageSync(config.tokenKey, token)
    ft.setStorageSync('accessToken', token)
  },

  getToken() {
    return ft.getStorageSync(config.tokenKey) || ft.getStorageSync('accessToken')
  },

  clearToken() {
    ft.removeStorageSync(config.tokenKey)
    ft.removeStorageSync('accessToken')
  },

  setUseMock(useMock) {
    config.useMock = Boolean(useMock)
  },

  async getApplicationDetail() {
    if (config.useMock) {
      return createApplicationDetail(mockApplicationDetail)
    }
    return request({ url: '/application/profile' })
  },

  async getChatList(params = {}) {
    const page = params.page || 1
    const size = params.size || 20
    if (config.useMock) {
      const start = (page - 1) * size
      const list = mockChatList.slice(start, start + size).map(createChatSummary)
      return {
        count: mockChatList.length,
        page,
        size,
        list
      }
    }
    return request({ url: `/historical_conversation/${page}/${size}` })
  },

  async getChatRecordList(chatId, params = {}) {
    const page = params.page || 1
    const size = params.size || 20
    if (config.useMock) {
      const recordList = mockChatRecordList[chatId] || []
      const start = (page - 1) * size
      return {
        chat_id: chatId,
        count: recordList.length,
        page,
        size,
        list: recordList.slice(start, start + size).map(createRecordItem)
      }
    }
    return request({ url: `/historical_conversation_record/${chatId}/${page}/${size}` })
  },

  async openChat() {
    if (config.useMock) {
      return {
        chat_id: `chat_${Date.now()}`,
        status: 200
      }
    }
    const res = await request({ url: '/open' })
    const chatId =
      (res && res.chat_id) ||
      (res && res.data && res.data.chat_id) ||
      (res && res.data) ||
      (typeof res === 'string' ? res : '')
    return {
      chat_id: chatId,
      raw: res
    }
  },

  async modifyChat(chatId, data = {}) {
    if (config.useMock) {
      return {
        status: 200,
        chat_id: chatId,
        data
      }
    }
    return request({
      url: `/historical_conversation/${chatId}`,
      method: 'PUT',
      data
    })
  },

  async deleteChat(chatId) {
    if (config.useMock) {
      return {
        status: 200,
        chat_id: chatId
      }
    }
    return request({
      url: `/historical_conversation/${chatId}`,
      method: 'DELETE'
    })
  },

  async getChatRecordDetail(chatId, recordId) {
    if (config.useMock) {
      const recordList = mockChatRecordList[chatId] || []
      const record = recordList.find(item => String(item.record_id) === String(recordId)) || null
      return record ? createRecordItem(record) : null
    }
    return request({ url: `/historical_conversation/${chatId}/record/${recordId}` })
  },

  async sendChatMessage(chatId, payload = {}) {
    if (config.useMock) {
      return {
        chat_id: chatId,
        record_id: `record_${Date.now()}`,
        stream: true,
        payload
      }
    }
    return request({
      url: `/chat_message/${chatId}`,
      method: 'POST',
      data: payload,
      timeout: STREAM_TIMEOUT
    })
  },

  streamChatMessage(chatId, payload = {}, handlers = {}) {
    if (config.useMock) {
      const chunks = ['正在', '模拟', '流式', '返回…']
      return this.sendChatMessage(chatId, payload).then(response => {
        handlers.onStart && handlers.onStart(response)
        let index = 0
        const timer = setInterval(() => {
          if (index < chunks.length) {
            handlers.onDelta && handlers.onDelta(chunks[index], response)
            index += 1
            return
          }
          clearInterval(timer)
          handlers.onEnd && handlers.onEnd({
            event: 'end',
            chat_id: response.chat_id,
            record_id: response.record_id,
            is_end: true
          })
        }, 180)

        return {
          response,
          cancel: () => clearInterval(timer)
        }
      })
    }

    return new Promise((resolve, reject) => {
      const requestTask = ft.request({
        url: `${config.baseURL}/chat_message/${chatId}`,
        method: 'POST',
        data: payload,
        header: {
          'Content-Type': 'application/json',
          'Accept-Language': ft.getStorageSync('language') || 'zh-CN',
          authorization: ft.getStorageSync(config.tokenKey)
            ? `Bearer ${ft.getStorageSync(config.tokenKey)}`
            : '',
          Accept: 'application/json, text/plain, */*'
        },
        timeout: STREAM_TIMEOUT,
        enableChunked: true,
        success: response => {
          if (response.statusCode >= 200 && response.statusCode < 300) {
            resolve({
              response: response.data,
              cancel: () => requestTask.abort()
            })
            return
          }
          handlers.onError && handlers.onError(response)
          reject(response)
        },
        fail: error => {
          handlers.onError && handlers.onError(error)
          reject(error)
        }
      })

      handlers.onStart && handlers.onStart({ chat_id: chatId })

      if (requestTask && typeof requestTask.onChunkReceived === 'function') {
        requestTask.onChunkReceived(event => {
          const chunkText = this.decodeChunk(event && event.data)
          if (!chunkText) {
            return
          }
          this.consumeStreamText(chunkText, handlers)
        })
      }

      resolve({
        response: requestTask,
        cancel: () => {
          if (requestTask && typeof requestTask.abort === 'function') {
            requestTask.abort()
          }
        }
      })
    })
  },

  decodeChunk(data) {
    if (!data) {
      return ''
    }
    if (typeof data === 'string') {
      return data
    }
    if (data instanceof ArrayBuffer && decoder) {
      try {
        return decoder.decode(new Uint8Array(data), { stream: true })
      } catch (error) {
        return ''
      }
    }
    if (typeof data === 'object' && data.buffer instanceof ArrayBuffer && decoder) {
      try {
        return decoder.decode(new Uint8Array(data.buffer), { stream: true })
      } catch (error) {
        return ''
      }
    }
    return ''
  },

  consumeStreamText(chunkText, handlers) {
    const text = String(chunkText || '').trim()
    if (!text) {
      return
    }

    const lines = text
      .split(/\r?\n/)
      .map(line => line.trim())
      .filter(Boolean)

    lines.forEach(line => {
      const payload = line.startsWith('data:') ? line.replace(/^data:\s*/, '') : line
      if (!payload || payload === '[DONE]') {
        handlers.onEnd && handlers.onEnd({ event: 'end', is_end: true })
        return
      }

      let parsed = null
      try {
        parsed = JSON.parse(payload)
      } catch (error) {
        parsed = { event: 'delta', content: payload }
      }

      if (parsed.code === 500) {
        handlers.onError && handlers.onError(parsed)
        return
      }

      if (parsed.event === 'start') {
        handlers.onStart && handlers.onStart(parsed)
        return
      }
      if (parsed.event === 'delta') {
        handlers.onDelta && handlers.onDelta(parsed.content || '', parsed)
        return
      }
      if (parsed.event === 'source') {
        handlers.onSource && handlers.onSource(parsed)
        return
      }
      if (parsed.event === 'execution_detail') {
        handlers.onExecutionDetail && handlers.onExecutionDetail(parsed)
        return
      }
      if (parsed.event === 'end' || parsed.is_end) {
        handlers.onEnd && handlers.onEnd(parsed)
        return
      }
      handlers.onDelta && handlers.onDelta(parsed.content || '', parsed)
    })
  },

  async createShareLink() {
    if (config.useMock) {
      return mockShareLink
    }
    return request({ url: '/share/link' })
  }
}

module.exports = api
