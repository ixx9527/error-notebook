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

module.exports = { login, getToken, clearToken, isLoggedIn }
