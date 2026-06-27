const { uploadFile, request } = require('../../utils/api')
const { BASE_URL, getToken } = require('../../utils/api')

Page({
  data: {
    imagePath: '',
    recognizing: false,
    recognized: false,
    results: [],
    currentStep: 'choose',
  },

  chooseImage() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      sizeType: ['compressed'],
      success: (res) => {
        this.setData({
          imagePath: res.tempFiles[0].tempFilePath,
          currentStep: 'preview',
        })
      },
    })
  },

  retake() {
    this.setData({
      imagePath: '',
      recognized: false,
      results: [],
      currentStep: 'choose',
    })
  },

  async startRecognize() {
    if (!this.data.imagePath) return
    this.setData({ recognizing: true })

    try {
      const taskId = await this.uploadAsync()
      await this.pollResult(taskId)
    } catch (e) {
      this.setData({ recognizing: false })
      wx.showToast({ title: '识别失败，请重试', icon: 'none' })
    }
  },

  uploadAsync() {
    return new Promise((resolve, reject) => {
      const token = getToken()
      wx.uploadFile({
        url: `${BASE_URL}/api/errors/upload/async`,
        filePath: this.data.imagePath,
        name: 'image',
        header: { Authorization: token ? `Bearer ${token}` : '' },
        success(res) {
          if (res.statusCode === 200) {
            const data = JSON.parse(res.data)
            resolve(data.data.task_id)
          } else {
            reject(new Error('上传失败'))
          }
        },
        fail: reject,
      })
    })
  },

  pollResult(taskId) {
    return new Promise((resolve, reject) => {
      const maxAttempts = 60
      let attempt = 0

      const poll = async () => {
        attempt++
        try {
          const res = await request({
            url: `/api/errors/upload/status/${taskId}`,
            showLoading: false,
          })
          const task = res.data

          if (task.status === 'completed') {
            this.setData({
              recognizing: false,
              recognized: true,
              results: task.data || [],
              currentStep: 'result',
            })
            this.requestSubscribe()
            resolve()
          } else if (task.status === 'failed') {
            reject(new Error(task.error || '识别失败'))
          } else if (attempt < maxAttempts) {
            setTimeout(poll, 2000)
          } else {
            reject(new Error('处理超时'))
          }
        } catch (e) {
          reject(e)
        }
      }

      poll()
    })
  },

  requestSubscribe() {
    const tmplIds = ['tmpl_review_reminder_1']
    wx.requestSubscribeMessage({
      tmplIds,
      success: (res) => {
        const accepted = tmplIds.filter((id) => res[id] === 'accept')
        if (accepted.length > 0) {
          request({
            url: '/api/notify/subscribe',
            method: 'POST',
            data: { template_ids: accepted },
            showLoading: false,
          }).catch(() => {})
        }
      },
      fail() {},
    })
  },

  onSubjectChange(e) {
    const idx = e.currentTarget.dataset.idx
    const subjects = ['语文', '数学', '英语', '其他']
    wx.showActionSheet({
      itemList: subjects,
      success: (res) => {
        this.setData({ [`results[${idx}].subject`]: subjects[res.tapIndex] })
      },
    })
  },

  onFieldInput(e) {
    const { idx, field } = e.currentTarget.dataset
    this.setData({ [`results[${idx}].${field}`]: e.detail.value })
  },

  confirmSave() {
    wx.showToast({ title: '已保存', icon: 'success' })
    setTimeout(() => wx.navigateBack(), 1000)
  },

  goBack() {
    if (this.data.currentStep === 'result') {
      this.setData({ currentStep: 'preview', recognized: false, results: [] })
    } else {
      this.retake()
    }
  },
})
