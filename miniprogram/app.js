const api = require('./utils/api')

App({
  globalData: {
    appName: 'MaxKB 智能助手'
  },

  onLaunch() {
    const logs = ft.getStorageSync('logs') || []
    logs.unshift(Date.now())
    ft.setStorageSync('logs', logs)

    api.setBaseURL('http://localhost:3001/chat/api')

    const accessToken = ft.getStorageSync('chatAccessToken') || 'd0e8767f2db84541'
    api.authenticate(accessToken).catch(() => {
      const fallbackToken = ft.getStorageSync('accessToken')
      if (fallbackToken) {
        api.setToken(fallbackToken)
      }
    })
  }
})
