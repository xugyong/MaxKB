const api = require('../../utils/api')

const normalizeHistoryItem = item => ({
  id: item.id,
  title: item.abstract,
  updateTime: item.update_time || item.updateTime || ''
})

const normalizeApplicationDetail = raw => {
  const data = (raw && raw.data && typeof raw.data === 'object' ? raw.data : raw) || {}
  return data
}

const normalizePrologueMessage = (applicationDetail, appName) => {
  const prologue =
    applicationDetail.prologue ||
    applicationDetail.prolog ||
    applicationDetail.welcome_message ||
    applicationDetail.chat_prologue ||
    applicationDetail.greeting ||
    applicationDetail.opening_text ||
    applicationDetail.opening ||
    applicationDetail.prologue_content ||
    applicationDetail.model_setting?.prologue ||
    ''
  if (!prologue) return null
  return {
    id: `prologue_${Date.now()}`,
    role: 'assistant',
    content: prologue,
    time: '',
    status: 'done',
    sourceList: [],
    detailList: [],
    isPrologue: true,
    appName: appName || ''
  }
}

const normalizeMessageItem = item => ([
  {
    id: `${item.id || item.record_id || Date.now()}_user`,
    recordId: item.record_id,
    chatId: item.chat_id,
    role: 'user',
    content: item.problem_text || '',
    time: item.create_time || '刚刚'
  },
  {
    id: `${item.id || item.record_id || Date.now()}_assistant`,
    recordId: item.record_id,
    chatId: item.chat_id,
    role: 'assistant',
    content: item.answer_text || '',
    time: item.create_time || '',
    status: item.write_ed ? 'done' : 'writing',
    sourceList: (item.source_list || []).map(source => ({
      title: source.document_name,
      score: String(source.score)
    })),
    detailList: (item.execution_details || []).map(detail => ({
      label: detail.node_name,
      value: detail.status
    })),
    sourceRaw: item.source_list || [],
    detailRaw: item.execution_details || []
  }
].filter(msg => msg.content))

const normalizeRecordList = response => {
  const rawList = (response && response.data && (response.data.records || response.data.list)) || response.list || response.records || []
  return rawList
}

const expandRecordList = response => normalizeRecordList(response).flatMap(normalizeMessageItem)
const expandRecordItems = records => (Array.isArray(records) ? records : []).flatMap(normalizeMessageItem)

const fetchAllChatRecords = async (apiClient, chatId, pageSize = 50, maxPages = 20) => {
  let page = 1
  let allRecords = []
  for (let i = 0; i < maxPages; i += 1) {
    // eslint-disable-next-line no-await-in-loop
    const response = await apiClient.getChatRecordList(chatId, { page, size: pageSize })
    const records = normalizeRecordList(response)
    allRecords = allRecords.concat(records)
    if (!records.length || records.length < pageSize) {
      break
    }
    page += 1
  }
  return allRecords
}

const buildRenderMessageList = (messageList, prologueMessage, showPrologue) => {
  const list = Array.isArray(messageList) ? messageList.slice() : []
  if (showPrologue && prologueMessage) {
    const exists = list.some(item => item && item.isPrologue)
    if (!exists) {
      return [prologueMessage].concat(list)
    }
  }
  return list
}

const buildHistoryPrologueMessage = (appInfo, chatId) => {
  const prologue = appInfo && appInfo.prologue ? appInfo.prologue : ''
  if (!prologue) return null
  return {
    id: `history_prologue_${chatId || 'default'}`,
    role: 'assistant',
    content: prologue,
    time: '',
    status: 'done',
    sourceList: [],
    detailList: [],
    isPrologue: true,
    isLocalPrologue: true
  }
}

const createUserMessage = content => ({
  id: `msg_${Date.now()}`,
  role: 'user',
  content,
  time: '刚刚'
})

const createAssistantPlaceholder = () => ({
  id: `msg_${Date.now()}_assistant`,
  role: 'assistant',
  content: '',
  time: '刚刚',
  status: 'writing',
  sourceList: [],
  detailList: []
})

Page({
  shouldShowPrologue() {
    return Boolean(this.data.currentChatId === '' || this.data.currentChatId === 'new')
  },

  syncRenderMessageList(messageList = this.data.messageList, prologueMessage = this.data.prologueMessage, showPrologue = this.shouldShowPrologue()) {
    const renderMessageList = buildRenderMessageList(messageList, prologueMessage, showPrologue)
    this.setData({ renderMessageList })
    return renderMessageList
  },

  data: {
    appInfo: {
      id: '',
      name: 'MaxKB 智能助手',
      icon: '',
      themeColor: '#3370FF',
      headerFontColor: '#FFFFFF',
      backgroundImage: '',
      prologue: ''
    },
    currentChatId: '',
    currentChatTitle: 'MaxKB 智能助手',
    historyVisible: false,
    historyAnimationVisible: false,
    detailVisible: false,
    detailTitle: '执行详情',
    detailType: 'execution',
    userFormVisible: false,
    selectingMode: false,
    inputValue: '',
    isSending: false,
    isLoading: true,
    showBackToBottom: false,
    historyList: [],
    messageList: [],
    renderMessageList: [],
    detailList: [],
    prologueMessage: null,
    currentStreamMessageId: '',
    userFormConfig: [],
    userFormData: {},
    formData: {},
    apiFormData: {},
    footerBottom: 0,
    safeAreaBottom: 0,
    keyboardHeight: 367,
    keyboardLayoutTimer: null,
    currentItem: 'bottom',
    scrollBottomId: 'bottom',
    streamScrollTick: 0,
    thinkingTimer: null,
    thinkingText: '',
    thinkingVisible: false
  },

  async onLoad() {
    const info = wx.getSystemInfoSync()
    this._platform = info.platform
    this._system = info.system
    await this.bootstrap()
  },

  onReady() {
    return
  },

  setSafeBottom() {
    const systemInfo = ft.getSystemInfoSync ? ft.getSystemInfoSync() : {}
    let safeAreaBottom = 0
    if (systemInfo.safeAreaInsets && typeof systemInfo.safeAreaInsets.bottom === 'number') {
      safeAreaBottom = systemInfo.safeAreaInsets.bottom
    } else if (systemInfo.safeArea) {
      safeAreaBottom = Math.max(0, (systemInfo.screenHeight || 0) - (systemInfo.safeArea.bottom || 0))
    }
    console.log('safeAreaBottom', safeAreaBottom)
    this._safeAreaBottom = safeAreaBottom
    this.setData({
      safeAreaBottom
    })
  },

  async bootstrap() {
    this.setData({ isLoading: true })
    this.setSafeBottom()
    try {
      const accessToken = ft.getStorageSync('chatAccessToken') || 'd0e8767f2db84541'
      const authResult = await api.authenticate(accessToken)
      const [applicationDetailRaw, chatList] = await Promise.all([
        api.getApplicationDetail(),
        api.getChatList({ page: 1, size: 20 })
      ])

      const applicationDetail = normalizeApplicationDetail(applicationDetailRaw)
      console.log('[bootstrap] applicationDetail raw', applicationDetailRaw)
      console.log('[bootstrap] applicationDetail normalized', applicationDetail)
      console.log('[bootstrap] chatList', chatList)

      const historyList = ((chatList && chatList.data && (chatList.data.records || chatList.data.list)) || chatList.list || chatList.records || []).map(normalizeHistoryItem)
      const currentChat = historyList.length ? historyList[0] : null
      const currentChatId = currentChat ? currentChat.id : ''
      const currentChatTitle = currentChat ? currentChat.title : this.data.currentChatTitle
      const recordList = currentChatId ? await fetchAllChatRecords(api, currentChatId, 50, 20) : []
      const messageList = expandRecordItems(recordList)
      const detailList = messageList.length ? (messageList[messageList.length - 1].detailList || []) : []
      const prologueMessage = normalizePrologueMessage(applicationDetail, applicationDetail.name || this.data.appInfo.name)
      const userFormConfig = this.extractUserFormConfig(applicationDetail)

      console.log('[bootstrap] prologue candidate', prologueMessage)

      this.setData({
        appInfo: Object.assign({}, this.data.appInfo, {
          id: applicationDetail.id,
          name: applicationDetail.name || this.data.appInfo.name,
          icon: applicationDetail.icon || '',
          backgroundImage: applicationDetail.chat_background || '',
          themeColor: (applicationDetail.custom_theme && applicationDetail.custom_theme.theme_color) || this.data.appInfo.themeColor,
          headerFontColor: (applicationDetail.custom_theme && applicationDetail.custom_theme.header_font_color) || this.data.appInfo.headerFontColor,
          prologue: prologueMessage ? prologueMessage.content : ''
        }),
        historyList,
        currentChatId,
        currentChatTitle,
        messageList,
        detailList,
        userFormConfig,
        prologueMessage,
        isLoading: false,
        authProfile: authResult.profile,
        authType: authResult.authenticationType,
        chatToken: authResult.token
      })
      this.syncRenderMessageList(messageList, prologueMessage)
    } catch (error) {
      console.error('[bootstrap failed]', error)
      this.setData({
        isLoading: false
      })
      ft.showToast({
        title: '初始化失败',
        icon: 'none'
      })
    }
  },

  startThinkingAnimation() {
    if (this.data.thinkingTimer) {
      clearInterval(this.data.thinkingTimer)
    }
    const frames = ['···', '•··', '••·', '•••', '••·', '•··']
    let index = 0
    this.setData({
      thinkingText: frames[index],
      thinkingVisible: true
    })
    const timer = setInterval(() => {
      index = (index + 1) % frames.length
      this.setData({ thinkingText: frames[index] })
    }, 180)
    this.setData({ thinkingTimer: timer })
  },

  stopThinkingAnimation() {
    if (this.data.thinkingTimer) {
      clearInterval(this.data.thinkingTimer)
    }
    this.setData({
      thinkingTimer: null,
      thinkingText: '',
      thinkingVisible: false
    })
  },

  hideThinkingDuringStream() {
    this.setData({ thinkingVisible: false })
  },

  async switchChat(e) {
    const chatId = e && e.detail ? e.detail.id : ''
    if (!chatId || chatId === this.data.currentChatId) {
      this.setData({ historyVisible: false })
      if (this.historyAnimationTimer) {
        clearTimeout(this.historyAnimationTimer)
      }
      this.historyAnimationTimer = setTimeout(() => {
        this.setData({ historyAnimationVisible: false })
      }, 240)
      return
    }

    this.setData({ isLoading: true, historyVisible: false, detailVisible: false })
    if (this.historyAnimationTimer) {
      clearTimeout(this.historyAnimationTimer)
    }
    this.historyAnimationTimer = setTimeout(() => {
      this.setData({ historyAnimationVisible: false })
    }, 240)

    try {
      const [recordList, chatList] = await Promise.all([
        fetchAllChatRecords(api, chatId, 50, 20),
        api.getChatList({ page: 1, size: 20 })
      ])
      const historyList = normalizeRecordList(chatList).map(normalizeHistoryItem)
      const selectedChat = historyList.find(item => item.id === chatId) || null
      const nextTitle = (selectedChat && selectedChat.title) || this.data.currentChatTitle
      const expandedMessages = expandRecordItems(recordList)
      this.setData({
        currentChatId: chatId,
        currentChatTitle: nextTitle,
        historyList,
        messageList: expandedMessages,
        detailList: expandedMessages.length ? (expandedMessages[expandedMessages.length - 1].detailList || []) : [],
        isLoading: false,
        showBackToBottom: false
      })
      this.syncRenderMessageList(expandedMessages, this.data.prologueMessage)
      if (ft.setNavigationBarTitle) {
        ft.setNavigationBarTitle({ title: nextTitle })
      }
    } catch (error) {
      this.setData({ isLoading: false })
      ft.showToast({ title: '切换会话失败', icon: 'none' })
    }
  },

  async openMessageDetail(e) {
    const recordId = e && e.currentTarget && e.currentTarget.dataset ? e.currentTarget.dataset.recordId : ''
    const detailType = e && e.currentTarget && e.currentTarget.dataset ? e.currentTarget.dataset.type : 'execution'
    if (!recordId) {
      return
    }

    const detail = await api.getChatRecordDetail(this.data.currentChatId, recordId)
    if (!detail) {
      return
    }

    const executionDetails = Array.isArray(detail.execution_details) ? detail.execution_details : []
    const sourceList = Array.isArray(detail.source_list) ? detail.source_list : []
    const list = detailType === 'execution'
      ? executionDetails.map(item => ({ label: item.node_name, value: item.status }))
      : sourceList.map(item => ({ label: item.document_name, value: item.content }))

    this.setData({
      detailVisible: true,
      historyVisible: false,
      detailTitle: detailType === 'execution' ? '执行详情' : '知识来源',
      detailType,
      detailList: list
    })
  },

  onInputChange(e) {
    const value = e && e.detail ? e.detail.value : ''
    this.setData({
      inputValue: value
    })
  },

  onInputFocus() {
    this.scrollToLatestMessage()
  },

  onInputBlur() {
    if (this.data.keyboardLayoutTimer) {
      clearTimeout(this.data.keyboardLayoutTimer)
      this.data.keyboardLayoutTimer = null
    }
    this.setData({ footerBottom: 0, safeAreaBottom: Number(this._safeAreaBottom) || 0 })
  },

  onKeyboardHeightChange(e) {
    const height = Math.max(0, Number(e && e.detail && e.detail.height) || 0)
    if (this.data.keyboardLayoutTimer) {
      clearTimeout(this.data.keyboardLayoutTimer)
      this.data.keyboardLayoutTimer = null
    }
    this.setData({
      safeAreaBottom: 0
    })
    this.data.keyboardLayoutTimer = setTimeout(() => {
      this.applyStableKeyboardLayout(height)
    }, 120)
  },

  applyStableKeyboardLayout(keyboardHeight) {
    const safeAreaBottom = Number(this._safeAreaBottom) || 0
    const footerBottom = Math.max(0, keyboardHeight - safeAreaBottom)

    this.setData({
      footerBottom,
      currentItem: 'bottom'
    })

    if (keyboardHeight > 0) {
      this.scrollToLatestMessage(0)
      this.scrollToLatestMessage(160)
    }
  },

  onMessageListScroll() {
    if (this.data.isSending) {
      this.scrollToLatestMessage(120)
    }
  },

  async onSend(e) {
    const value = ((e && e.detail && e.detail.value) || this.data.inputValue || '').trim()
    if (!value || this.data.isSending) {
      if (value && !this.data.isSending) {
        this.scrollToLatestMessage()
      }
      return
    }

    const userMessage = createUserMessage(value)
    const assistantMessage = createAssistantPlaceholder()
    const messageList = this.data.messageList.concat(userMessage, assistantMessage)
    const userInput = this.collectUserInputData()

    this.setData({
      messageList,
      inputValue: '',
      isSending: true,
      showBackToBottom: false,
      currentStreamMessageId: assistantMessage.id,
      thinkingVisible: true,
      thinkingText: '···',
      currentItem: 'bottom',
      pendingInputValue: value
    })
    this.syncRenderMessageList(messageList, this.data.prologueMessage)
    this.scrollToLatestMessage(0)
    this.startThinkingAnimation()

    try {
      let chatId = this.data.currentChatId
      if (!chatId || chatId === 'new') {
        const openResult = await api.openChat()
        chatId = openResult && openResult.chat_id ? openResult.chat_id : ''
        if (!chatId) {
          throw new Error(`open chat failed: ${JSON.stringify(openResult)}`)
        }
        this.setData({ currentChatId: chatId, currentItem: 'bottom' })
        this.syncRenderMessageList(messageList, this.data.prologueMessage)
      }

      const requestBody = {
        message: value,
        stream: true,
        re_chat: false,
        ...userInput,
        form_data: {
          ...(this.data.formData || {}),
          ...(this.data.apiFormData || {}),
          ...userInput
        }
      }

      await api.streamChatMessage(chatId, requestBody, {
        onStart: response => {
          this.setData({
            currentChatId: response.chat_id || chatId,
            detailList: [
              { label: 'record_id', value: String(response.record_id || '') },
              { label: 'chat_id', value: String(response.chat_id || chatId) }
            ],
            currentItem: 'bottom'
          })
        },

        onDelta: chunk => {
          this.hideThinkingDuringStream()
          this.appendAssistantChunk(assistantMessage.id, chunk)
        },
        onSource: sourceEvent => {
          const nextMessageList = this.data.messageList.map(item => {
            if (item.id !== assistantMessage.id) {
              return item
            }
            return Object.assign({}, item, {
              sourceList: (sourceEvent.source_list || []).map(source => ({
                title: source.document_name,
                score: String(source.score)
              })),
              sourceRaw: sourceEvent.source_list || []
            })
          })
          this.setData({ messageList: nextMessageList })
          this.syncRenderMessageList(nextMessageList, this.data.prologueMessage)
        },
        onExecutionDetail: executionEvent => {
          const nextMessageList = this.data.messageList.map(item => {
            if (item.id !== assistantMessage.id) {
              return item
            }
            return Object.assign({}, item, {
              detailList: (executionEvent.execution_details || []).map(detail => ({
                label: detail.node_name,
                value: detail.status
              })),
              detailRaw: executionEvent.execution_details || []
            })
          })
          this.setData({ messageList: nextMessageList })
          this.syncRenderMessageList(nextMessageList, this.data.prologueMessage)
        },
        onEnd: endEvent => {
          if (endEvent && endEvent.record_id) {
            this.setData({
              detailList: [
                { label: 'record_id', value: String(endEvent.record_id) },
                { label: 'chat_id', value: String(endEvent.chat_id || chatId) }
              ]
            })
          }
          this.stopThinkingAnimation()
          this.finishAssistantMessage(assistantMessage.id)
        },
        onError: () => {
          this.stopThinkingAnimation()
          this.failAssistantMessage(assistantMessage.id)
          this.handleSendFailure(value, assistantMessage.id, '发送失败，请检查网络后重试')
        }
      })
    } catch (error) {
      console.error('[send failed]', error)
      this.stopThinkingAnimation()
      this.failAssistantMessage(assistantMessage.id)
      this.handleSendFailure(value, assistantMessage.id, '发送失败，请检查网络后重试')
    }
  },

  handleSendFailure(value, messageId, toastText) {
    const fallbackValue = value || this.data.pendingInputValue || ''
    if (fallbackValue) {
      this.setData({
        inputValue: fallbackValue,
        pendingInputValue: fallbackValue,
        showBackToBottom: false,
        currentItem: 'bottom'
      })
      this.resetSendState()
      this.syncRenderMessageList(this.data.messageList, this.data.prologueMessage)
      this.scrollToLatestMessage()
    } else {
      this.setData({
        showBackToBottom: false,
        currentItem: 'bottom'
      })
      this.resetSendState()
    }
    if (toastText) {
      ft.showToast({ title: toastText, icon: 'none' })
    }
  },

  collectUserInputData() {
    return this.data.userFormData || {}
  },

  collectChatExtraData() {
    return {
      ...(this.data.formData || {}),
      ...(this.data.apiFormData || {})
    }
  },

  appendAssistantChunk(messageId, chunk) {
    const nextMessageList = this.data.messageList.map(item => {
      if (item.id !== messageId) {
        return item
      }
      return Object.assign({}, item, {
        content: `${item.content || ''}${chunk}`,
        status: 'writing'
      })
    })
    this.setData({ messageList: nextMessageList })
    this.syncRenderMessageList(nextMessageList, this.data.prologueMessage)
    this.scheduleStreamScrollToBottom()
  },

  scheduleStreamScrollToBottom() {
    if (this.streamScrollTimer) {
      return
    }
    this.streamScrollTimer = setTimeout(() => {
      this.streamScrollTimer = null
      this.scrollToLatestMessage(0)
    }, 50)
  },

  finishAssistantMessage(messageId) {
    const nextMessageList = this.data.messageList.map(item => {
      if (item.id !== messageId) {
        return item
      }
      return Object.assign({}, item, {
        status: 'done'
      })
    })
    this.setData({
      messageList: nextMessageList,
      isSending: false,
      currentStreamMessageId: '',
      currentItem: 'bottom'
    })
    this.syncRenderMessageList(nextMessageList, this.data.prologueMessage)
    this.scrollToLatestMessage(0)
  },

  failAssistantMessage(messageId) {
    const nextMessageList = this.data.messageList.map(item => {
      if (item.id !== messageId) {
        return item
      }
      return Object.assign({}, item, {
        status: 'failed',
        content: item.content || '发送失败，请重试'
      })
    })
    this.setData({
      messageList: nextMessageList,
      isSending: false,
      currentStreamMessageId: '',
      currentItem: 'bottom'
    })
    this.syncRenderMessageList(nextMessageList, this.data.prologueMessage)
  },

  async toggleHistory() {
    if (this.data.historyVisible) {
      this.setData({
        historyVisible: false
      })
      if (this.historyAnimationTimer) {
        clearTimeout(this.historyAnimationTimer)
      }
      this.historyAnimationTimer = setTimeout(() => {
        this.setData({
          historyAnimationVisible: false,
          detailVisible: false,
          userFormVisible: false,
          selectingMode: false
        })
      }, 240)
      return
    }

    if (this.historyAnimationTimer) {
      clearTimeout(this.historyAnimationTimer)
    }
    this.setData({
      historyAnimationVisible: true,
      historyVisible: true,
      detailVisible: false,
      userFormVisible: false,
      selectingMode: false
    })

    try {
      await this.refreshHistoryList()
    } catch (error) {
      console.error('[refreshHistoryList failed in toggleHistory]', error)
      this.setData({ historyList: this.data.historyList || [] })
    }
  },

  showDetail() {
    return
  },

  hideDetail() {
    this.setData({
      detailVisible: false
    })
  },

  toggleUserForm() {
    this.setData({
      userFormVisible: !this.data.userFormVisible,
      historyVisible: false,
      historyAnimationVisible: false,
      detailVisible: false
    })
  },

  enterSelectMode() {
    this.setData({ selectingMode: true })
  },

  exitSelectMode() {
    this.setData({ selectingMode: false })
  },

  extractUserFormConfig(applicationDetail) {
    const nodes = (applicationDetail.work_flow && applicationDetail.work_flow.nodes) || []
    const baseNode = nodes.find(node => node.id === 'base-node') || {}
    const properties = baseNode.properties || {}
    return properties.user_input_field_list || []
  },

  updateUserFormField(e) {
    const key = e && e.currentTarget && e.currentTarget.dataset ? e.currentTarget.dataset.key : ''
    const value = e && e.detail ? e.detail.value : ''
    if (!key) {
      return
    }
    this.setData({
      userFormData: Object.assign({}, this.data.userFormData, {
        [key]: value
      })
    })
  },

  confirmUserForm() {
    this.setData({
      userFormVisible: false
    })
  },

  async newChat() {
    console.log('[newChat] start')
    try {
      const result = await api.openChat()
      console.log('[newChat] open result', result)
      const chatId = result && result.chat_id ? result.chat_id : ''
      const title = '新会话'

      const messageList = this.data.prologueMessage ? [this.data.prologueMessage] : []
      this.setData({
        currentChatId: chatId,
        currentChatTitle: title,
        messageList,
        historyVisible: false,
        historyAnimationVisible: false,
        detailVisible: false,
        selectingMode: false,
        inputValue: '',
        detailList: [],
        showBackToBottom: false
      })
      this.syncRenderMessageList(messageList, this.data.prologueMessage)
      if (ft.setNavigationBarTitle) {
        ft.setNavigationBarTitle({ title })
      }

      if (chatId) {
        try {
          const recordList = await fetchAllChatRecords(api, chatId, 50, 20)
          const expandedMessages = expandRecordItems(recordList)
          if (expandedMessages.length && this.data.currentChatId === chatId) {
            this.setData({
              messageList: expandedMessages,
              detailList: expandedMessages[expandedMessages.length - 1].detailList || []
            })
            this.syncRenderMessageList(expandedMessages, this.data.prologueMessage, true)
          }
        } catch (error) {
          console.error('[newChat record refresh failed]', error)
        }
      }
    } catch (error) {
      console.error('[newChat open failed]', error)
      ft.showToast({ title: '新建会话失败', icon: 'none' })
    }
  },

  async renameChat(e) {
    const chatId = e && e.detail ? e.detail.id : ''
    const titleFromMenu = e && e.detail ? e.detail.title : ''
    const target = this.data.historyList.find(item => item.id === chatId)
    const newTitle = titleFromMenu || await this.promptChatTitle(target ? target.title : '')
    if (!chatId || !newTitle) {
      return
    }

    try {
      await api.modifyChat(chatId, { abstract: newTitle })
      const historyList = await this.refreshHistoryList()
      if (this.data.currentChatId === chatId) {
        this.setData({ currentChatTitle: newTitle })
        if (ft.setNavigationBarTitle) {
          ft.setNavigationBarTitle({ title: newTitle })
        }
      }
      this.setData({ historyList })
      ft.showToast({ title: '重命名成功', icon: 'none' })
    } catch (error) {
      console.error('[renameChat failed]', error)
      ft.showToast({ title: '重命名失败', icon: 'none' })
    }
  },

  async removeChat(e) {
    const chatId = e && e.detail ? e.detail.id : ''
    if (!chatId) {
      return
    }

    const confirm = await this.confirmAction('确认删除该会话吗？')
    if (!confirm) {
      return
    }

    try {
      await api.deleteChat(chatId)
      const historyList = await this.refreshHistoryList()
      if (this.data.currentChatId === chatId) {
        const nextChat = historyList[0] || null
        if (nextChat) {
          const recordList = await fetchAllChatRecords(api, nextChat.id, 50, 20)
          const expandedMessages = expandRecordItems(recordList)
          this.setData({
            currentChatId: nextChat.id,
            currentChatTitle: nextChat.title,
            messageList: expandedMessages,
            detailList: expandedMessages.length ? (expandedMessages[expandedMessages.length - 1].detailList || []) : []
          })
          this.syncRenderMessageList(expandedMessages, this.data.prologueMessage)
          if (ft.setNavigationBarTitle) {
            ft.setNavigationBarTitle({ title: nextChat.title })
          }
        } else {
          this.setData({ currentChatId: '', currentChatTitle: 'MaxKB 智能助手', messageList: [], detailList: [] })
          this.syncRenderMessageList([], this.data.prologueMessage)
          if (ft.setNavigationBarTitle) {
            ft.setNavigationBarTitle({ title: 'MaxKB 智能助手' })
          }
        }
      }
      this.setData({ historyList })
      ft.showToast({ title: '删除成功', icon: 'none' })
    } catch (error) {
      console.error('[removeChat failed]', error)
      ft.showToast({ title: '删除失败', icon: 'none' })
    }
  },

  async refreshHistoryList() {
    const chatList = await api.getChatList({ page: 1, size: 20 })
    const historyList = normalizeRecordList(chatList).map(normalizeHistoryItem)
    this.setData({ historyList })
    return historyList
  },

  shouldShowPrologue() {
    return Boolean(this.data.prologueMessage)
  },

  syncRenderMessageList(messageList = this.data.messageList, prologueMessage = this.data.prologueMessage) {
    const renderMessageList = buildRenderMessageList(messageList, prologueMessage, this.shouldShowPrologue())
    this.setData({ renderMessageList })
    return renderMessageList
  },

  confirmAction(content) {
    return new Promise(resolve => {
      ft.showModal({
        title: '提示',
        content,
        success: res => resolve(Boolean(res && res.confirm)),
        fail: () => resolve(false)
      })
    })
  },

  scrollToBottom() {
    this.scrollToLatestMessage()
  },

  scrollToLatestMessage(delay = 30) {
    const doScroll = () => {
      const streamScrollTick = this.data.streamScrollTick + 1
      const scrollBottomId = `bottom_${streamScrollTick}`
      this.setData({
        streamScrollTick,
        scrollBottomId,
        currentItem: scrollBottomId,
        showBackToBottom: false
      })
    }

    if (delay > 0) {
      setTimeout(doScroll, delay)
    } else {
      doScroll()
    }
  },

  resetSendState() {
    this.setData({
      isSending: false,
      currentStreamMessageId: ''
    })
  },

  onUnload() {
    if (this.data.keyboardLayoutTimer) {
      clearTimeout(this.data.keyboardLayoutTimer)
    }
    if (this.streamScrollTimer) {
      clearTimeout(this.streamScrollTimer)
      this.streamScrollTimer = null
    }
    if (this.historyAnimationTimer) {
      clearTimeout(this.historyAnimationTimer)
    }
    this.stopThinkingAnimation()
  }
})
