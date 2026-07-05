let localConfig = {}
try { localConfig = require('../config.local') } catch (e) {}
const BASE_URL = localConfig.BASE_URL || 'http://localhost:8000'

function getToken() {
  return wx.getStorageSync('token') || null
}

function request(options) {
  const { url, method = 'GET', data, header = {}, showLoading = true } = options

  return new Promise((resolve, reject) => {
    if (showLoading) {
      wx.showLoading({ title: '加载中...', mask: true })
    }

    const token = getToken()
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    wx.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        ...header,
      },
      success(res) {
        if (showLoading) wx.hideLoading()

        if (res.statusCode === 401) {
          wx.removeStorageSync('token')
          wx.removeStorageSync('user_id')
          wx.showToast({ title: '请重新登录', icon: 'none' })
          return reject(new Error('未授权'))
        }

        if (res.statusCode >= 400) {
          const msg = res.data?.detail || '请求失败'
          wx.showToast({ title: msg, icon: 'none' })
          return reject(new Error(msg))
        }

        resolve(res.data)
      },
      fail(err) {
        if (showLoading) wx.hideLoading()
        wx.showToast({ title: '网络错误', icon: 'none' })
        reject(err)
      },
    })
  })
}

function uploadFile(filePath, formData = {}) {
  return new Promise((resolve, reject) => {
    wx.showLoading({ title: '识别中...', mask: true })

    const token = getToken()

    wx.uploadFile({
      url: `${BASE_URL}/api/errors/upload`,
      filePath,
      name: 'image',
      formData,
      header: {
        Authorization: token ? `Bearer ${token}` : '',
      },
      success(res) {
        wx.hideLoading()
        if (res.statusCode === 200) {
          const data = JSON.parse(res.data)
          resolve(data)
        } else {
          wx.showToast({ title: '上传失败', icon: 'none' })
          reject(new Error('上传失败'))
        }
      },
      fail(err) {
        wx.hideLoading()
        wx.showToast({ title: '网络错误', icon: 'none' })
        reject(err)
      },
    })
  })
}

function guestUpload(filePath) {
  return new Promise((resolve, reject) => {
    wx.showLoading({ title: '识别中...', mask: true })

    wx.uploadFile({
      url: `${BASE_URL}/api/guest/demo-upload`,
      filePath,
      name: 'image',
      success(res) {
        wx.hideLoading()
        if (res.statusCode === 200) {
          const data = JSON.parse(res.data)
          resolve(data)
        } else if (res.statusCode === 429) {
          wx.showToast({ title: '体验次数已达上限，请注册后使用', icon: 'none' })
          reject(new Error('体验次数已达上限'))
        } else {
          const msg = JSON.parse(res.data).detail || '上传失败'
          wx.showToast({ title: msg, icon: 'none' })
          reject(new Error(msg))
        }
      },
      fail(err) {
        wx.hideLoading()
        wx.showToast({ title: '网络错误', icon: 'none' })
        reject(err)
      },
    })
  })
}

module.exports = { request, uploadFile, guestUpload, BASE_URL }
