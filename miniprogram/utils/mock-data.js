const mockApplicationDetail = {
  id: 'app_10001',
  name: 'MaxKB 智能助手',
  icon: '',
  chat_background: '',
  show_history: true,
  custom_theme: {
    theme_color: '#3370FF',
    header_font_color: '#FFFFFF'
  },
  user_input_config: {
    title: '请先补充业务信息'
  },
  prologue: '您好，我是 MaxKB 智能助手，有什么可以帮助您的？',
  work_flow: {
    nodes: [
      {
        id: 'base-node',
        properties: {
          user_input_field_list: [
            {
              field_key: 'company_name',
              label: '公司名称',
              type: 'text',
              required: true,
              placeholder: '请输入公司名称'
            },
            {
              field_key: 'industry',
              label: '行业',
              type: 'select',
              required: false,
              options: ['互联网', '制造业', '金融', '教育']
            }
          ]
        }
      }
    ]
  }
}

const mockChatList = [
  {
    id: 'chat_001',
    abstract: '如何生成知识库文档？',
    create_time: '2026-04-27 10:12:30',
    update_time: '10:14'
  },
  {
    id: 'chat_002',
    abstract: '工作流如何配置变量？',
    create_time: '2026-04-26 09:30:00',
    update_time: '昨天'
  }
]

const baseRecord = {
  status: 200,
  write_ed: true,
  is_stop: false,
  vote_status: '-1',
  reasoning_content: '',
  reasoning_content_buffer: [],
  buffer: [],
  upload_meta: {
    image_list: [],
    document_list: [],
    audio_list: [],
    video_list: [],
    other_list: []
  }
}

const mockChatRecordList = {
  chat_001: [
    {
      ...baseRecord,
      id: 'record_90001',
      chat_id: 'chat_001',
      record_id: 90001,
      problem_text: '如何生成知识库文档？',
      answer_text: '你可以先创建知识库，然后上传文档。',
      answer_text_list: [[{ type: 'text', content: '你可以先创建知识库，然后上传文档。' }]],
      source_list: [
        {
          paragraph_id: 'para_1001',
          document_name: '产品使用手册',
          score: 0.92,
          content: '先创建知识库，再上传文档。'
        }
      ],
      execution_details: [
        {
          node_id: 'search-knowledge-node',
          node_name: '知识库检索',
          status: 'success',
          output: { hits: 3 }
        }
      ]
    }
  ]
}

const mockShareLink = {
  link: 'share_8f3c2a1b'
}

module.exports = {
  mockApplicationDetail,
  mockChatList,
  mockChatRecordList,
  mockShareLink
}
