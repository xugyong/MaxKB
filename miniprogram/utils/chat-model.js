const createEmptyUploadMeta = () => ({
  image_list: [],
  document_list: [],
  audio_list: [],
  video_list: [],
  other_list: []
})

const createApplicationDetail = data => ({
  id: data.id || '',
  name: data.name || 'MaxKB 智能助手',
  icon: data.icon || '',
  chat_background: data.chat_background || '',
  show_history: Boolean(data.show_history),
  custom_theme: {
    theme_color: (data.custom_theme && data.custom_theme.theme_color) || '#3370FF',
    header_font_color: (data.custom_theme && data.custom_theme.header_font_color) || '#FFFFFF'
  },
  user_input_config: data.user_input_config || { title: '请先补充业务信息' },
  work_flow: data.work_flow || { nodes: [] }
})

const createChatSummary = data => ({
  id: data.id || '',
  abstract: data.abstract || '',
  create_time: data.create_time || '',
  update_time: data.update_time || ''
})

const createSourceItem = data => ({
  paragraph_id: data.paragraph_id || '',
  document_name: data.document_name || '',
  score: Number(data.score || 0),
  content: data.content || ''
})

const createExecutionItem = data => ({
  node_id: data.node_id || '',
  node_name: data.node_name || '',
  status: data.status || '',
  start_time: data.start_time || '',
  end_time: data.end_time || '',
  output: data.output || {}
})

const createRecordItem = data => ({
  id: data.id || '',
  chat_id: data.chat_id || '',
  record_id: data.record_id || '',
  problem_text: data.problem_text || '',
  answer_text: data.answer_text || '',
  answer_text_list: data.answer_text_list || [[]],
  buffer: data.buffer || [],
  reasoning_content: data.reasoning_content || '',
  reasoning_content_buffer: data.reasoning_content_buffer || [],
  write_ed: Boolean(data.write_ed),
  is_stop: Boolean(data.is_stop),
  vote_status: data.vote_status || '-1',
  status: data.status || 0,
  upload_meta: data.upload_meta || createEmptyUploadMeta(),
  execution_details: (data.execution_details || []).map(createExecutionItem),
  source_list: (data.source_list || []).map(createSourceItem),
  create_time: data.create_time || ''
})

const createChatMessage = data => ({
  id: data.id || '',
  role: data.role || 'assistant',
  content: data.content || '',
  time: data.time || '',
  status: data.status || 'done',
  sourceList: data.sourceList || [],
  detailList: data.detailList || []
})

module.exports = {
  createEmptyUploadMeta,
  createApplicationDetail,
  createChatSummary,
  createSourceItem,
  createExecutionItem,
  createRecordItem,
  createChatMessage
}
