const { login, getToken, clearToken } = require('./utils/auth')

App({
  globalData: {
    token: null,
    userId: null,
    userInfo: null,
    theme: 'light',
  },

  onLaunch() {
    const token = getToken()
    if (token) {
      this.globalData.token = token
      this.globalData.userId = wx.getStorageSync('user_id')
    }
    this.globalData.theme = wx.getSystemInfoSync().theme || 'light'
    wx.onThemeChange((res) => {
      this.globalData.theme = res.theme
    })
  },

  isGuest() {
    return !this.globalData.token
  },

  getTheme() {
    return this.globalData.theme
  },

  async ensureLogin() {
    if (this.globalData.token) return true

    try {
      const res = await login()
      this.globalData.token = res.token
      this.globalData.userId = res.user_id
      return true
    } catch (e) {
      console.error('登录失败', e)
      wx.showToast({ title: '登录失败', icon: 'none' })
      return false
    }
  },
})
