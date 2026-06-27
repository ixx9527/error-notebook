const { request } = require('../../utils/api')
const { formatDate, getSubjectClass } = require('../../utils/util')

Page({
  data: {
    todayCount: 0,
    todayItems: [],
    stats: {},
    loading: true,
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    const app = getApp()
    const loggedIn = await app.ensureLogin()
    if (!loggedIn) {
      this.setData({ loading: false })
      return
    }

    try {
      const [reviewRes, statsRes] = await Promise.all([
        request({ url: '/api/review/today', showLoading: false }),
        request({ url: '/api/stats/summary', showLoading: false }),
      ])

      const todayItems = (reviewRes.data.items || []).map((item) => ({
        ...item,
        subjectClass: getSubjectClass(item.subject),
      }))

      this.setData({
        todayCount: reviewRes.data.total || 0,
        todayItems,
        stats: statsRes.data || {},
        loading: false,
      })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  goUpload() {
    wx.navigateTo({ url: '/pages/upload/upload' })
  },

  goReview() {
    if (this.data.todayCount === 0) {
      wx.showToast({ title: '今天没有待复习的错题', icon: 'none' })
      return
    }
    wx.navigateTo({ url: '/pages/review/review' })
  },

  goErrorList() {
    wx.switchTab({ url: '/pages/error-list/error-list' })
  },

  goStats() {
    wx.navigateTo({ url: '/pages/stats/stats' })
  },
})
