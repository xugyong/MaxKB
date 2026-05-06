# `src/views/chat` 对话页面说明文档

本文档用于梳理 MaxKB 前端中的对话页面实现方式，供后续参考实现一个 **1:1 的微信小程序对话页**。这里重点不是讲业务概念，而是尽量把页面结构、交互、数据流、状态机和可复刻的 UI 细节讲清楚。

---

## 1. 对话页面的入口与整体结构

对话页面并不是单一页面，而是一个“根据模式动态切换的入口”。

### 1.1 总入口

入口文件是：

- `src/views/chat/index.vue`

它本身不直接渲染聊天界面，而是根据当前环境和参数动态切换模板：

- `pc`
- `mobile`
- `no-service`

### 1.2 模式选择逻辑

`src/views/chat/index.vue` 的核心逻辑如下：

- 如果当前应用可用，继续判断展示模式
- 如果 URL query 中没有 `mode`，或者 `mode=pc`：
  - 移动端设备使用 `mobile`
  - 非移动端使用 `pc`
- 如果 `mode` 明确指定，则按指定模式渲染
- 如果当前应用不可用，则渲染 `no-service`

也就是说，对话页面本质上是一个“容器入口”，真正的视觉和交互分别由 `pc/index.vue` 和 `mobile/index.vue` 承担。

---

## 2. 对话页面的三种页面形态

### 2.1 PC 版

文件：`src/views/chat/pc/index.vue`

这是功能最完整的版本，布局分成三块：

1. 左侧历史对话栏
2. 中间对话主区域
3. 右侧详情面板

PC 版适合桌面浏览器，信息密度高，功能最全。

### 2.2 移动版

文件：`src/views/chat/mobile/index.vue`

移动端是“单主区域 + 抽屉历史列表”的布局：

1. 顶部固定 Header
2. 中间聊天主区域
3. 历史记录使用抽屉展示

移动端更接近微信小程序的目标形态，因此如果要做 1:1 小程序，这一版是最值得重点参考的。

### 2.3 无服务页

文件：`src/views/chat/no-service/index.vue`

用于应用不可用、服务关闭或未配置时的兜底页面。

---

## 3. 对话页面的核心子组件

无论 PC 还是 Mobile，聊天主内容都来自同一个核心组件：

- `src/components/ai-chat/index.vue`

它负责：

- 展示欢迎语/前导内容
- 展示问题和回答列表
- 渲染流式回答
- 处理输入框、用户表单、上传文件
- 处理选中分享
- 处理滚动、回到底部、历史加载
- 处理回答中的知识来源、执行详情跳转

所以可以理解为：

- 页面壳子：`pc/index.vue`、`mobile/index.vue`
- 聊天引擎：`components/ai-chat/index.vue`

---

## 4. PC 对话页的详细结构

文件：`src/views/chat/pc/index.vue`

### 4.1 顶层容器

PC 页面最外层会动态注入主题变量：

- 主色 `--el-color-primary`
- 主色浅色系
- 背景图 `chat_background`

这意味着一个应用可以拥有自己的对话主题，包含：

- 主题色
- 头部文字色
- 聊天背景图

### 4.2 左侧历史面板

左侧由 `HistoryPanel` 组件渲染。

功能包括：

- 展示应用图标和应用名称
- 新建对话按钮
- 对话历史列表
- 清空全部历史
- 单条记录支持：
  - 分享
  - 编辑标题
  - 删除

#### 4.2.1 折叠能力

PC 左侧历史栏支持折叠：

- 折叠后只保留窄栏图标
- 展开后显示完整列表和操作按钮

这是典型的桌面端信息密集布局。

### 4.3 中间聊天主区域

右侧主区域顶部会显示：

- 当前会话名称
- 问题数量
- 分享按钮
- 导出按钮

中部是 `AiChat` 组件。

### 4.4 右侧详情面板

PC 版非常重要的一点，是它有一个右侧的“详情面板”。

这个面板会在以下场景打开：

- 查看某条消息的执行详情
- 查看知识来源
- 查看某篇段落文档

它的宽度默认是 400px。

#### 4.4.1 右侧详情面板类型

右侧面板分三类：

1. `executionDetail`
   - 展示模型调用、节点执行、工具调用等运行细节
2. `knowledgeSource`
   - 展示知识来源、命中段落等
3. `paragraphDocument`
   - 展示段落所属文档

#### 4.4.2 关闭方式

- 点击右上角关闭按钮
- 关闭后恢复聊天主区域全宽

### 4.5 PC 页面主要交互

#### 4.5.1 新建对话

点击左侧“新建对话”后：

- 清空当前会话消息
- 将当前会话切换为 `new`
- 重置标题为“创建对话”
- 收起右侧详情面板

#### 4.5.2 切换历史会话

点击左侧历史项后：

- 切换当前 chatId
- 清空当前列表并重新拉取消息记录
- 如果正在播放语音，取消暂停并恢复状态处理
- 关闭右侧详情面板

#### 4.5.3 分享

支持两种分享方式：

- 当前会话分享按钮
- 选中多条对话记录后分享

#### 4.5.4 导出

支持导出为：

- Markdown
- HTML
- PDF

#### 4.5.5 历史消息无限加载

当聊天记录滚动到顶部时，如果还有更多历史记录，会继续向上加载。

这个能力对长会话很重要。

---

## 5. Mobile 对话页的详细结构

文件：`src/views/chat/mobile/index.vue`

### 5.1 页面布局

移动端结构更适合小程序：

1. 顶部固定头部
2. 中间聊天主区
3. 历史记录抽屉

### 5.2 顶部 Header

Header 里包含：

- 左侧历史按钮
- 应用图标
- 应用名称
- 右侧新建对话按钮
- 右侧分享按钮

Header 使用固定定位，始终固定在顶部。

### 5.3 历史记录抽屉

移动端不使用 PC 左栏，而是用 `ChatHistoryDrawer`：

- 从侧边或底部抽出历史记录
- 适合手指操作
- 便于在小屏幕上切换会话

### 5.4 主聊天区域

移动端的聊天主体仍然是 `AiChat`，核心能力和 PC 保持一致：

- 看消息
- 继续对话
- 上拉加载历史消息
- 选中分享
- 查看来源和执行详情（取决于配置）

### 5.5 移动端视觉细节

移动端同样使用：

- 应用主题色
- 应用头部文字色
- 背景图

这保证小程序和 Web 视觉尽量一致。

---

## 6. `AiChat` 组件的内部结构

文件：`src/components/ai-chat/index.vue`

这是整个对话体验的核心。可以把它理解成“聊天列表 + 输入区 + 选择模式 + 辅助面板控制器”。

### 6.1 顶层分区

它内部主要分为：

1. 用户输入表单层
2. 聊天消息滚动层
3. 底部输入操作区
4. 控制组件

### 6.2 用户输入表单层

如果应用配置了“用户输入字段”或“API 输入字段”，聊天并不是一上来就能发消息，而是先展示一层表单。

这个表单可能在两种状态下出现：

- 首次进入时强制填写
- 点击输入区按钮后弹出/展示

#### 6.2.1 用户输入字段

来自应用工作流里的 `base-node` 配置：

- `user_input_field_list`
- `user_input_config.title`

如果这些字段存在，发送消息前必须先完成表单填写。

#### 6.2.2 API 输入字段

在 `debug-ai-chat` 模式下，还可能存在：

- `api_input_field_list`

这种模式常用于调试时传入额外参数。

#### 6.2.3 输入数据缓存

用户表单数据会被缓存到本地存储，key 与 `accessToken` 绑定。

也就是说，同一个会话再次打开时，可能会恢复上次填写内容。

### 6.3 消息展示层

消息区使用 `el-scrollbar` 包裹，按顺序渲染每一轮问答。

每条对话实际上分为两部分：

- `QuestionContent`：问题
- `AnswerContent`：回答

也就是说，一个聊天记录不是单个气泡，而是一个完整的“问 + 答”对。

### 6.4 选择模式

`AiChat` 支持“多选对话记录后分享”的模式。

进入选择模式后：

- 每条对话前出现勾选框
- 底部出现批量操作栏
- 可以全选/取消/复制分享链接

这个模式对于导出或分享很关键。

### 6.5 底部输入操作区

底部由 `ChatInputOperate` 组件负责。

它通常负责：

- 输入问题
- 上传附件
- 触发发送
- 选择模型/参数
- 触发录音、图片、文件等能力

### 6.6 控制组件

`Control` 组件通常放一些辅助控制，例如：

- 额外功能入口
- 录音/转写状态控制
- 其他全局聊天控制能力

---

## 7. 聊天记录的结构与状态流

### 7.1 一条聊天记录的基本结构

从代码可以看出，每条记录至少包含：

- `id`
- `problem_text`
- `answer_text`
- `answer_text_list`
- `buffer`
- `reasoning_content`
- `reasoning_content_buffer`
- `write_ed`
- `is_stop`
- `record_id`
- `chat_id`
- `vote_status`
- `status`
- `upload_meta`

### 7.2 消息状态

消息不是一次性生成完，而是典型的流式状态：

1. 创建一个临时记录
2. 先渲染问题
3. 后台开始流式接收回答
4. 边接收边写入回答内容
5. 完成后关闭写入状态

### 7.3 流式输出

发送消息时，后端返回的是流式响应。

前端通过读取 `response.body.getReader()`，再交给 `getWrite()` 处理。

这说明回答是“逐字/逐段输出”的，而不是等完整结果返回后再一次性渲染。

这点对小程序实现非常重要，因为它直接影响用户体验。

---

## 8. 对话列表中的关键交互

### 8.1 回答中的知识来源

回答组件里可以点击知识来源，打开右侧详情。

这意味着答案卡片不仅是纯文本，还带“引用来源”能力。

### 8.2 执行详情

回答支持查看执行详情，常用于：

- 工作流节点执行结果
- 调试过程
- 中间输出内容
- 工具调用详情

### 8.3 继续对话

对话页支持在已有会话中继续发消息，也支持创建新会话。

### 8.4 语音相关

代码里有 `speechSynthesis` 的处理，说明页面会考虑浏览器朗读或语音播放状态。

切换历史对话时，会尝试恢复或取消语音状态，避免播放残留。

---

## 9. 分享机制

分享是这个对话页面的一个重要能力。

### 9.1 会话分享

单个会话可以生成分享链接。

### 9.2 多条记录分享

进入选择模式后，可以选中同一会话里的多条消息，再生成分享链接。

### 9.3 分享结果

后端返回 `link` 后，前端会拼接成：

- `window.location.origin + '/chat/share/' + link`

也就是说，分享页面是一个独立可访问的公开链接。

---

## 10. 导出机制

PC 版支持导出当前对话记录：

- Markdown
- HTML
- PDF

### 10.1 Markdown 导出

每轮问答会导出成：

```md
# 问题

回答内容
```

### 10.2 HTML 导出

先拼 Markdown，再用 `marked` 转成 HTML。

### 10.3 PDF 导出

通过 `PdfExport` 组件基于聊天 DOM 生成 PDF。

这个能力对“归档会话”很有价值。

---

## 11. 历史记录加载机制

### 11.1 会话列表分页

左侧历史会话不是一次性加载完，而是分页加载。

### 11.2 聊天记录分页

单个会话的消息记录也支持分页。

### 11.3 上拉加载更多

当当前聊天记录滚动到顶部并且还有更多历史记录时，会继续加载更早的对话内容。

这是长会话必须具备的能力。

---

## 12. 主题系统

聊天页强依赖应用配置中的主题字段：

- `custom_theme.theme_color`
- `custom_theme.header_font_color`
- `chat_background`
- `icon`
- `name`

所以它不是固定 UI，而是可被应用级配置覆盖的。

对于微信小程序实现来说，这意味着：

- 可以做全局主题配置
- 可以在不同应用间切换皮肤
- 需要支持背景图和头部配色

---

## 13. 对于微信小程序 1:1 复刻的建议拆解

如果同事要做一个微信小程序版本，建议不要直接照搬代码结构，而是按“体验层”拆成以下模块。

### 13.1 页面结构建议

建议拆成以下几个小程序页面/组件：

1. **聊天首页**
   - 顶部应用信息
   - 消息列表
   - 底部输入框
2. **历史记录抽屉/弹层**
   - 历史会话列表
   - 新建会话
   - 清空历史
3. **消息详情面板**
   - 执行详情
   - 知识来源
   - 文档详情
4. **分享选择模式**
   - 多选消息
   - 生成分享链接
5. **用户表单页/弹层**
   - 首次进入表单
   - 自定义参数填写

### 13.2 小程序要特别注意的点

#### A. 流式回答

这是重中之重。

需要支持：

- 建立会话后立即出现“正在回答”状态
- 流式刷新回答内容
- 回答完成后稳定落地

#### B. 滚动体验

需要保证：

- 新消息自动滚到底部
- 历史消息上拉加载
- 用户主动上滑时不要强行打断阅读

#### C. 历史会话切换

切换会话后必须：

- 清空当前消息缓存
- 重新拉取记录
- 恢复标题与状态

#### D. 分享能力

小程序中可以做：

- 生成页面分享路径
- 支持选中部分消息分享

#### E. 主题可配置

不同应用主题、背景图、名称、头像都应该从后端配置下发。

---

## 14. 页面行为总结成一个完整链路

可以把整个对话页面理解成以下流程：

1. 进入聊天页面
2. 根据设备/模式切换 PC 或 Mobile
3. 拉取应用信息和历史会话列表
4. 默认进入“新会话”或上次会话
5. 如需用户输入，先展示表单
6. 用户发送消息
7. 创建临时消息记录
8. 后端流式返回回答
9. 前端逐步写入回答内容
10. 回答完成后刷新会话标题、来源、执行详情
11. 用户可切换历史、分享、导出、查看执行详情

---

## 15. 适合小程序复刻的 UI 重点

如果目标是“1:1”，建议优先复刻以下视觉/交互：

- 顶部应用名称与图标
- 新建对话入口
- 历史记录抽屉
- 问答气泡的纵向节奏
- 流式输出状态
- 分享选择模式
- 回到最新消息按钮
- 主题色和背景图
- 用户输入表单弹层
- 消息中的引用来源入口
- 消息执行详情入口

---

## 16. 参考源码索引

下面是这个文档对应的关键源码位置：

- `src/views/chat/index.vue`
- `src/views/chat/pc/index.vue`
- `src/views/chat/mobile/index.vue`
- `src/views/chat/component/HistoryPanel.vue`
- `src/views/chat/mobile/component/ChatHistoryDrawer.vue`
- `src/components/ai-chat/index.vue`
- `src/components/ai-chat/component/question-content/index.vue`
- `src/components/ai-chat/component/answer-content/index.vue`
- `src/components/ai-chat/component/chat-input-operate/index.vue`
- `src/components/ai-chat/component/user-form/index.vue`
- `src/components/ai-chat/component/prologue-content/index.vue`
- `src/components/ai-chat/component/knowledge-source-component/*`

---

## 17. 微信小程序实现拆解方案

下面这部分是给同事直接落地参考用的，目标是把 Web 端的对话能力拆成小程序可以实现的模块。

### 17.1 小程序页面结构拆分

建议拆成 4 个核心页面/弹层模块：

1. **聊天主页面**
   - 顶部应用信息栏
   - 消息列表
   - 底部输入区
   - 新消息/回到底部按钮
2. **历史会话抽屉**
   - 会话列表
   - 新建会话
   - 删除会话
   - 清空会话
3. **消息详情弹层**
   - 执行详情
   - 知识来源
   - 文档详情
4. **分享选择模式**
   - 进入多选状态
   - 勾选消息
   - 生成分享链接

如果需要更细，也可以把“首次用户输入表单”单独拆为一个全屏弹层或独立页面。

### 17.2 小程序页面与组件映射

建议把 Web 端能力映射成如下小程序组件：

- `ChatPage`
  - 对应 `src/views/chat/mobile/index.vue`
- `ChatHeader`
  - 顶部应用信息栏、历史入口、新建会话、分享入口
- `ChatMessageList`
  - 消息列表、流式渲染、上拉加载历史
- `ChatMessageItem`
  - 单轮问答结构，包含问题和回答
- `ChatInputBar`
  - 输入框、发送按钮、附件按钮、更多功能
- `HistoryDrawer`
  - 历史会话列表
- `MessageDetailDrawer`
  - 执行详情、知识来源、文档详情
- `UserInputFormPopup`
  - 首次用户输入/调试参数输入
- `ShareSelectBar`
  - 多选分享底部操作栏

### 17.3 数据模型拆分

建议小程序侧至少保留以下数据结构。

#### 17.3.1 应用配置 `applicationDetail`

来自后端应用详情，建议包含：

- `id`
- `name`
- `icon`
- `chat_background`
- `custom_theme.theme_color`
- `custom_theme.header_font_color`
- `show_history`
- `work_flow`
- `type`

这些字段决定整个聊天页的外观和输入规则。

#### 17.3.2 会话列表 `chatLogData`

每个会话至少包含：

- `id`
- `abstract`
- `create_time`
- `update_time`

其中 `abstract` 通常作为会话标题显示。

#### 17.3.3 消息列表 `currentRecordList`

每条消息建议保留：

- `id`
- `record_id`
- `chat_id`
- `problem_text`
- `answer_text`
- `answer_text_list`
- `status`
- `vote_status`
- `write_ed`
- `is_stop`
- `buffer`
- `reasoning_content`
- `reasoning_content_buffer`
- `upload_meta`
- `execution_details`
- `source` / `knowledge source` 相关字段

小程序可以不完全照搬所有字段，但至少要支持“问题、回答、流式状态、引用来源、执行详情”。

### 17.4 核心状态机

建议把对话页状态拆成下面几类。

#### 17.4.1 会话状态

- `new`：新会话，尚未生成 chatId
- `existing`：已存在会话
- `loading`：请求历史中
- `sending`：流式发送中
- `error`：发送失败

#### 17.4.2 展示状态

- `showHistoryDrawer`
- `showSelectionMode`
- `showUserInputForm`
- `showMessageDetail`
- `showBackToBottom`

#### 17.4.3 消息状态

- `writing`：流式输出中
- `done`：输出完成
- `stopped`：用户中断
- `failed`：回答失败

### 17.5 页面流程拆解

#### 17.5.1 进入页面

1. 拉取应用详情
2. 根据设备/模式确定页面布局
3. 拉取历史会话列表
4. 默认进入“新会话”或最近一次会话
5. 如果要求首次表单，先展示输入表单

#### 17.5.2 发送消息

1. 用户输入问题
2. 如有用户表单，先校验表单
3. 创建临时消息气泡
4. 请求后端打开 chatId
5. 建立流式连接发送消息
6. 边收边渲染回答文本
7. 接收完成后补齐执行详情、来源等信息
8. 刷新当前会话在历史列表中的标题

#### 17.5.3 切换会话

1. 点击历史会话
2. 清空当前消息列表
3. 拉取该会话第一页消息
4. 自动滚到底部
5. 若还有历史消息，支持上拉分页

#### 17.5.4 分享消息

1. 进入选择模式
2. 选中一个或多个消息
3. 调用分享接口生成链接
4. 复制链接或走小程序分享能力

#### 17.5.5 查看消息详情

1. 点击消息中的“来源”或“执行详情”入口
2. 打开底部弹层或侧边弹层
3. 拉取并展示详情数据

### 17.6 小程序 UI 还原重点

为了做到 1:1，建议优先还原这些视觉点：

- 顶部应用名 + 图标
- 头部主题色
- 聊天气泡间距和层级
- 流式输出过程中“正在生成”的状态
- 新消息自动滚底
- 右下角“回到底部”按钮
- 历史会话抽屉
- 分享选中态
- 用户输入弹层
- 消息内的执行详情/知识来源入口

### 17.7 小程序交互细节建议

#### A. 滚动策略

建议使用“用户阅读优先”的滚动规则：

- 当用户在底部附近时，新消息自动滚到底部
- 当用户手动上滑查看历史时，不要强制拉回底部
- 到达顶部时，自动加载更早消息

#### B. 输入策略

如果存在首次表单：

- 首次进入时强制展示
- 表单未完成前，不允许发送
- 表单数据本地缓存，便于再次打开时恢复

#### C. 流式渲染策略

建议把一条回答拆成“增量文本块”更新，不要等全部完成后再渲染。

#### D. 详情弹层策略

小程序里更建议使用：

- 底部抽屉
- 半屏弹层
- 全屏详情页

不要在主聊天页面里塞太多详情内容，以免影响阅读。

### 17.8 推荐的实现顺序

如果同事要快速落地，建议按下面顺序做：

1. **基础聊天页**
   - 头部
   - 消息列表
   - 输入框
2. **流式回复**
   - 打开会话
   - 逐步渲染回答
3. **历史会话**
   - 列表
   - 切换
   - 删除
4. **分享模式**
   - 多选
   - 分享链接
5. **来源/执行详情**
   - 半屏弹层
6. **用户输入表单**
   - 首次进入表单
   - 表单缓存
7. **主题定制**
   - 应用图标、主题色、背景图

### 17.9 与 Web 端差异的取舍

小程序复刻时，建议保留核心体验，但可以适度简化：

- PC 右侧详情面板可以改为底部抽屉
- 导出 PDF 可以先不做或后置
- 复杂的多选分享可先做单轮分享再扩展
- 语音朗读类能力可后置

---

## 18. 参考接口清单

下面整理的是对话页最直接相关的 API，方便小程序同事对接时建立接口表。

### 18.1 会话与消息

- `open`：打开新的对话 `GET /open`
- `chat`：发送消息流 `POST /chat_message/{chat_id}`
- `pageChat`：分页获取历史会话 `GET /historical_conversation/{page}/{size}`
- `pageChatRecord`：分页获取某会话消息 `GET /historical_conversation_record/{chat_id}/{page}/{size}`
- `getChatRecord`：获取某条消息详情 `GET /historical_conversation/{chat_id}/record/{record_id}`
- `deleteChat`：删除单个会话 `DELETE /historical_conversation/{chat_id}`
- `clearChat`：清空全部会话 `DELETE /historical_conversation/clear`
- `modifyChat`：修改会话标题 `PUT /historical_conversation/{chat_id}`

### 18.2 分享

- `postShareChat`：创建会话分享链接 `POST /{application_id}/chat/{chat_id}/share_chat`
- `getShareLink`：读取分享页内容 `GET /share/{link}`

### 18.3 用户认证与个人信息

- `chatProfile`：获取聊天应用认证信息
- `anonymousAuthentication`：匿名认证
- `passwordAuthentication`：密码认证
- `login`：登录
- `ldapLogin`：LDAP 登录
- `getCaptcha`：验证码
- `logout`：登出
- `getChatUserProfile`：获取当前聊天用户信息
- `resetCurrentPassword`：重置当前用户密码

### 18.4 附件与文件

- `postUploadFile`：上传文件
- `getFile`：获取文件 URL

### 18.5 语音能力

- `textToSpeech`：文本转语音
- `speechToText`：语音转文本

### 18.6 反馈

- `vote`：点赞、点踩、填写原因

这些接口足够支撑一个完整的对话小程序雏形。

---

## 19. 消息数据结构样例 JSON

下面给出一组更接近前端实际使用方式的样例数据，方便同事做微信小程序时直接对照字段设计。

### 19.1 应用配置 `applicationDetail`

```json
{
  "id": "app_10001",
  "name": "MaxKB 智能助手",
  "icon": "https://example.com/icon.png",
  "chat_background": "https://example.com/bg.png",
  "type": "workflow",
  "show_history": true,
  "custom_theme": {
    "theme_color": "#3370FF",
    "header_font_color": "#FFFFFF"
  },
  "work_flow": {
    "nodes": [
      {
        "id": "base-node",
        "properties": {
          "user_input_field_list": [
            {
              "field_key": "company_name",
              "label": "公司名称",
              "type": "text",
              "required": true,
              "placeholder": "请输入公司名称"
            },
            {
              "field_key": "industry",
              "label": "行业",
              "type": "select",
              "required": false,
              "options": [
                "互联网",
                "制造业",
                "金融",
                "教育"
              ]
            }
          ],
          "api_input_field_list": [
            {
              "field_key": "trace_id",
              "label": "Trace ID",
              "type": "text"
            }
          ],
          "user_input_config": {
            "title": "请先补充业务信息"
          }
        }
      }
    ]
  }
}
```

### 19.2 会话列表项 `chatLogData` 中的一条记录

```json
{
  "id": "chat_202604270001",
  "abstract": "如何生成知识库文档？",
  "create_time": "2026-04-27 10:12:30",
  "update_time": "2026-04-27 10:14:18"
}
```

### 19.3 消息列表 `currentRecordList` 中的一轮问答

```json
{
  "id": "temp_record_001",
  "record_id": 90001,
  "chat_id": "chat_202604270001",
  "problem_text": "如何生成知识库文档？",
  "answer_text": "",
  "answer_text_list": [[
    {
      "content": "你可以先创建知识库，然后上传文档，系统会自动切分并建立索引。",
      "type": "text"
    }
  ]],
  "buffer": [],
  "reasoning_content": "",
  "reasoning_content_buffer": [],
  "write_ed": true,
  "is_stop": false,
  "vote_status": "-1",
  "status": 200,
  "upload_meta": {
    "image_list": [],
    "document_list": [],
    "audio_list": [],
    "video_list": [],
    "other_list": []
  },
  "execution_details": [
    {
      "node_id": "search-knowledge-node",
      "node_name": "知识库检索",
      "status": "success",
      "start_time": "2026-04-27 10:13:01",
      "end_time": "2026-04-27 10:13:02",
      "output": {
        "hits": 3
      }
    }
  ],
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

### 19.4 流式中的临时消息体

```json
{
  "id": "local_17000001",
  "problem_text": "帮我总结一下这篇文档",
  "answer_text": "",
  "answer_text_list": [[]],
  "buffer": [],
  "reasoning_content": "",
  "reasoning_content_buffer": [],
  "write_ed": false,
  "is_stop": false,
  "record_id": "",
  "chat_id": "",
  "vote_status": "-1",
  "status": null,
  "upload_meta": {
    "image_list": [],
    "document_list": [],
    "audio_list": [],
    "video_list": [],
    "other_list": []
  }
}
```

### 19.5 分享接口返回示例

```json
{
  "link": "share_8f3c2a1b"
}
```

### 19.6 建议给小程序保留的最小字段集

如果是先做 MVP，建议至少保留这些字段：

- `applicationDetail.id`
- `applicationDetail.name`
- `applicationDetail.icon`
- `applicationDetail.chat_background`
- `applicationDetail.custom_theme.theme_color`
- `applicationDetail.custom_theme.header_font_color`
- `chatLogData.id`
- `chatLogData.abstract`
- `currentRecordList.id`
- `currentRecordList.record_id`
- `currentRecordList.chat_id`
- `currentRecordList.problem_text`
- `currentRecordList.answer_text`
- `currentRecordList.answer_text_list`
- `currentRecordList.execution_details`
- `currentRecordList.source_list`

---

## 20. 页面状态流转图 / 时序说明

下面把对话页的关键流程拆成“状态流转”和“时序步骤”，便于研发同事按图实现。

### 20.1 总体状态图

```text
[进入对话页]
      |
      v
[拉取应用信息]
      |
      +--> 应用不可用 ----> [No Service 页面]
      |
      v
[拉取历史会话列表]
      |
      v
[判断是否展示首次表单]
      |
      +--> 是 ----> [展示用户输入表单]
      |                 |
      |                 v
      |            [用户填写并确认]
      |                 |
      |                 v
      +--------------> [进入聊天主界面]
                        |
                        v
               [选择新会话 / 历史会话]
                        |
                        v
                 [展示消息列表]
                        |
                        v
                  [用户发送消息]
                        |
                        v
                [创建临时消息气泡]
                        |
                        v
                 [打开 chatId / 发送流式请求]
                        |
                        v
              [流式接收回答并增量渲染]
                        |
                        v
                [补齐来源、执行详情]
                        |
                        v
               [刷新历史标题 / 状态]
```

### 20.2 首次进入页面时序

```text
1. 进入 `/chat/:accessToken`
2. `src/views/chat/index.vue` 根据设备与 mode 选择 `pc` 或 `mobile`
3. 页面注入应用主题色、背景图、头部文字色
4. `AiChat` 拉取应用详情
5. `HistoryPanel` / `ChatHistoryDrawer` 拉取历史会话列表
6. 如果当前应用配置了用户输入字段，先展示首次输入表单
7. 表单确认后，进入聊天主界面
8. 默认会话为 `new`
```

### 20.3 发送消息时序

```text
1. 用户输入问题并点击发送
2. 如果存在用户表单，先校验表单
3. 读取并合并本地缓存的表单值
4. 若当前没有 `chatId`，先调用 open 接口获取新的会话 id
5. 在本地先插入一条临时消息
6. 立即在 UI 上展示“问题 + 正在生成的回答”
7. 调用流式聊天接口 `chat_message/{chat_id}`
8. 前端不断读取流式数据并更新 `answer_text`
9. 流式结束后，补齐 `execution_details`、`source_list` 等扩展信息
10. 若当前还是新会话，则刷新历史标题
11. 关闭 loading 状态
```

### 20.4 切换历史会话时序

```text
1. 用户点击左侧历史记录或抽屉中的会话
2. 关闭分享选择状态与详情面板
3. 清空当前消息列表
4. 设置新的 `currentChatId`
5. 拉取该会话第一页消息
6. 按时间正序回填到消息列表
7. 滚动到底部
8. 如果有更早记录，允许上拉继续加载
```

### 20.5 查看消息详情时序

```text
1. 用户点击回答中的“执行详情”或“知识来源”
2. 打开右侧面板（Web）或底部抽屉（小程序）
3. 判断详情类型：executionDetail / knowledgeSource / paragraphDocument
4. 请求对应详情数据
5. 渲染节点执行、来源段落或文档内容
6. 用户关闭面板，返回聊天主界面
```

### 20.6 分享时序

```text
1. 用户点击分享按钮，进入选择模式
2. 页面显示勾选框与底部批量操作栏
3. 用户选择若干条消息
4. 点击“生成分享链接”
5. 调用 `postShareChat`
6. 后端返回 `link`
7. 前端复制分享 URL 或交给小程序分享能力
8. 退出选择模式
```

### 20.7 推荐的研发状态机实现方式

建议小程序内部至少维护以下状态：

```json
{
  "pageStatus": "loading | ready | empty | error",
  "chatStatus": "new | existing | sending | failed",
  "panelStatus": "none | history | detail | share | userForm",
  "scrollStatus": "bottom | middle | topLoading",
  "selectionStatus": "normal | selecting",
  "inputStatus": "hidden | visible | validating"
}
```

### 20.8 研发实现要点总结

- **页面进入先拉应用配置**，再决定是否展示聊天主界面
- **发送消息必须先确认 chatId**，否则要先 open 再发
- **消息要按流式方式更新**，不要等整段返回后再一次性展示
- **历史与详情是两个独立侧通道**，不要混在聊天主列表里
- **分享模式是独立状态**，要与正常浏览状态互斥
- **用户输入表单是前置条件**，不要绕过校验直接发消息

---

## 21. 接口清单表格版

下面把对话页相关接口整理成表格，方便同事直接做接口对照和联调清单。

| 模块 | 接口名 | 方法 | 路径 | 主要用途 | 小程序建议 |
| --- | --- | --- | --- | --- | --- |
| 会话 | `open` | GET | `/open` | 打开新的会话，获取 `chatId` | 必做 |
| 会话 | `chat` | POST(流式) | `/chat_message/{chat_id}` | 发送问题并接收流式回答 | 必做 |
| 会话 | `pageChat` | GET | `/historical_conversation/{page}/{size}` | 拉取历史会话列表 | 必做 |
| 会话 | `pageChatRecord` | GET | `/historical_conversation_record/{chat_id}/{page}/{size}` | 拉取某会话消息列表 | 必做 |
| 会话 | `getChatRecord` | GET | `/historical_conversation/{chat_id}/record/{record_id}` | 获取单条消息详情 | 必做 |
| 会话 | `deleteChat` | DELETE | `/historical_conversation/{chat_id}` | 删除单个会话 | 必做 |
| 会话 | `clearChat` | DELETE | `/historical_conversation/clear` | 清空全部会话 | 必做 |
| 会话 | `modifyChat` | PUT | `/historical_conversation/{chat_id}` | 修改会话标题 | 必做 |
| 分享 | `postShareChat` | POST | `/{application_id}/chat/{chat_id}/share_chat` | 生成会话分享链接 | 必做 |
| 分享 | `getShareLink` | GET | `/share/{link}` | 打开分享页内容 | 必做 |
| 认证 | `chatProfile` | GET | `/profile` | 获取聊天应用认证信息 | 视场景 |
| 认证 | `anonymousAuthentication` | POST | `/auth/anonymous` | 匿名认证 | 视场景 |
| 认证 | `passwordAuthentication` | POST | `/auth/password` | 密码认证 | 视场景 |
| 认证 | `login` | POST | `/auth/login/{accessToken}` | 登录 | 视场景 |
| 认证 | `ldapLogin` | POST | `/auth/ldap/login/{accessToken}` | LDAP 登录 | 视场景 |
| 认证 | `getCaptcha` | GET | `/captcha` | 获取验证码 | 视场景 |
| 认证 | `logout` | POST | `/auth/logout` | 退出登录 | 视场景 |
| 用户 | `getChatUserProfile` | GET | `/chat_user/profile` | 获取当前聊天用户信息 | 推荐 |
| 用户 | `resetCurrentPassword` | POST | `/chat_user/current/reset_password` | 重置当前用户密码 | 视场景 |
| 附件 | `postUploadFile` | POST | `/oss/file` | 上传图片、文档、音频、视频等附件 | 必做 |
| 文件 | `getFile` | GET | `/oss/get_url/{application_id}` | 获取文件 URL | 视场景 |
| 语音 | `textToSpeech` | POST/下载 | `/text_to_speech` | 文本转语音 | 可后置 |
| 语音 | `speechToText` | POST | `/speech_to_text` | 语音转文本 | 可后置 |
| 反馈 | `vote` | PUT | `/vote/chat/{chat_id}/chat_record/{record_id}` | 点赞、点踩、反馈原因 | 推荐 |

### 21.1 小程序联调优先级建议

建议按下面顺序接入：

1. `pageChat`
2. `pageChatRecord`
3. `open`
4. `chat`
5. `postShareChat`
6. `modifyChat`
7. `deleteChat`
8. `clearChat`
9. `postUploadFile`
10. `getChatRecord`

这样可以先把“能聊、能看历史、能发消息”跑通，再补分享、附件和详情。

---

## 22. 小程序研发任务拆分表

下面是建议的小程序研发拆分，按“先能用、再完善、最后优化”的顺序组织。

| 阶段 | 任务 | 内容说明 | 依赖 | 预估优先级 |
| --- | --- | --- | --- | --- |
| 1 | 基础页面搭建 | 搭建聊天页、历史抽屉、详情弹层、分享态、用户输入弹层 | 无 | 最高 |
| 1 | 应用主题接入 | 接入应用名称、图标、主题色、头图、头部文字色 | 应用详情接口 | 最高 |
| 1 | 历史会话列表 | 拉取会话分页列表、点击切换、删除、清空 | `pageChat` / `deleteChat` / `clearChat` | 最高 |
| 1 | 消息列表展示 | 展示问题、回答、时间、基础气泡样式 | `pageChatRecord` | 最高 |
| 1 | 发送消息 | 输入问题、打开会话、流式接收回答、自动滚底 | `open` / `chat` | 最高 |
| 2 | 流式渲染优化 | 边接收边更新回答、处理中断/失败状态 | `chat` | 高 |
| 2 | 用户输入表单 | 首次进入表单、字段校验、本地缓存恢复 | 应用工作流配置 | 高 |
| 2 | 详情弹层 | 执行详情、知识来源、文档详情 | `getChatRecord` / 详情字段 | 高 |
| 2 | 分享模式 | 多选消息、生成分享链接、复制链接 | `postShareChat` | 高 |
| 2 | 上拉加载历史 | 消息顶部加载更早记录，保持滚动位置 | `pageChatRecord` | 高 |
| 3 | 附件上传 | 图片、文档、音频、视频上传与预览 | `postUploadFile` | 中 |
| 3 | 点赞点踩 | 消息反馈、原因填写、结果刷新 | `vote` | 中 |
| 3 | 语音能力 | 语音输入、语音播报、文本转语音 | `speechToText` / `textToSpeech` | 中 |
| 3 | 导出能力 | 导出 Markdown/HTML/PDF 或小程序替代方案 | 需额外设计 | 中 |
| 4 | UX 优化 | 空态、加载态、错误态、骨架屏、按钮反馈、滚动体验 | 前置功能完成 | 低 |
| 4 | 性能优化 | 长列表虚拟化、流式渲染节流、图片懒加载 | 前置功能完成 | 低 |

### 22.1 任务拆分建议说明

#### 第一阶段：先跑通最小闭环

目标是让用户在小程序里完成最基础的聊天闭环：

- 进入页面
- 看见应用信息
- 拉取历史
- 发送消息
- 收到流式回答
- 切换历史会话

这一阶段最关键，不要把精力放在复杂详情和装饰上。

#### 第二阶段：补齐对话产品能力

把原 Web 版里最有价值的能力补齐：

- 用户输入表单
- 执行详情
- 知识来源
- 分享模式
- 上拉加载历史

这一阶段之后，体验基本就接近 Web 版了。

#### 第三阶段：增强能力

如果排期允许，再补：

- 附件上传
- 点赞点踩
- 语音
- 导出

#### 第四阶段：做体验优化

最后统一打磨：

- 空态文案
- 错误态提示
- 流式动效
- 长列表性能
- 滚动细节

---

## 23. 最后结论

MaxKB 的对话页面不是简单的“聊天框”，而是一个包含以下能力的完整对话系统：

- 多端适配
- 应用主题定制
- 流式 AI 输出
- 历史会话管理
- 消息多选分享
- 导出
- 知识来源追踪
- 执行详情查看
- 首次用户输入表单
- 语音/滚动/播放状态处理

如果要做一个微信小程序 1:1 版本，建议以 **“聊天主线 + 历史抽屉 + 分享模式 + 详情弹层 + 用户表单”** 这几个模块去实现，基本就能覆盖原页面绝大部分核心体验。
