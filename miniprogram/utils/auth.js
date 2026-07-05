const { request } = require('./api')

function login() {
  return new Promise((resolve, reject) => {
    wx.login({
      success(loginRes) {
        if (!loginRes.code) {
          return reject(new Error('wx.login 获取 code 失败'))
        }

        request({
          url: `/api/auth/login?code=${loginRes.code}`,
          method: 'POST',
          showLoading: false,
        })
          .then((res) => {
            const { token, user_id } = res.data
            wx.setStorageSync('token', token)
            wx.setStorageSync('user_id', user_id)
            resolve(res.data)
          })
          .catch(reject)
      },
      fail: reject,
    })
  })
}

function getToken() {
  return wx.getStorageSync('token') || null
}

function clearToken() {
  wx.removeStorageSync('token')
  wx.removeStorageSync('user_id')
}

function isLoggedIn() {
  return !!getToken()
}

function showLoginDialog() {
  return new Promise((resolve) => {
    wx.showModal({
      title: '登录后使用完整功能',
      content: '注册后可保存错题、智能复习、导出PDF等',
      confirmText: '立即登录',
      cancelText: '继续浏览',
      success(res) {
        if (res.confirm) {
          const app = getApp()
          app.ensureLogin().then((ok) => resolve(ok))
        } else {
          resolve(false)
        }
      },
      fail() {
        resolve(false)
      },
    })
  })
}

module.exports = { login, getToken, clearToken, isLoggedIn, showLoginDialog }
