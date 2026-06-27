const { request } = require('../../utils/api')
const { getSubjectClass } = require('../../utils/util')

Page({
  data: {
    items: [],
    currentIndex: 0,
    showAnswer: false,
    showRating: false,
    completed: false,
    totalCompleted: 0,
  },

  onLoad() {
    this.loadTodayReview()
  },

  async loadTodayReview() {
    try {
      const res = await request({ url: '/api/review/today' })
      const items = (res.data.items || []).map((item) => ({
        ...item,
        subjectClass: getSubjectClass(item.subject),
      }))
      this.setData({ items })

      if (items.length === 0) {
        wx.showToast({ title: '今天没有待复习的题目', icon: 'none' })
      }
    } catch (e) {}
  },

  toggleAnswer() {
    this.setData({ showAnswer: true })
  },

  rateMastery(e) {
    const level = e.currentTarget.dataset.level
    this.submitReview(level)
  },

  async submitReview(masteryLevel) {
    const { items, currentIndex } = this.data
    const item = items[currentIndex]

    try {
      await request({
        url: `/api/review/${item.plan_id}/complete`,
        method: 'POST',
        data: { mastery_level: masteryLevel },
      })

      this.setData({
        totalCompleted: this.data.totalCompleted + 1,
        showAnswer: false,
      })

      if (currentIndex + 1 < items.length) {
        this.setData({
          currentIndex: currentIndex + 1,
          showAnswer: false,
          showRating: false,
        })
      } else {
        this.setData({ completed: true })
      }
    } catch (e) {}
  },

  goHome() {
    wx.navigateBack()
  },
})
