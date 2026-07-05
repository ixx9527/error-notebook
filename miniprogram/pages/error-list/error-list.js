const { request } = require('../../utils/api')
const { getSubjectClass, timeAgo } = require('../../utils/util')
const { showLoginDialog } = require('../../utils/auth')

Page({
  data: {
    items: [],
    total: 0,
    page: 1,
    pageSize: 20,
    loading: false,
    noMore: false,
    subject: '',
    subjects: ['', '数学', '语文', '英语'],
    subjectIndex: 0,
  },

  onShow() {
    const app = getApp()
    if (typeof this.getTabBar === 'function') {
      this.getTabBar().setData({ selected: 1, theme: app.getTheme() })
    }
    if (app.isGuest()) {
      showLoginDialog().then((ok) => {
        if (!ok) wx.switchTab({ url: '/pages/index/index' })
      })
      return
    }
    this.resetAndLoad()
  },

  onPullDownRefresh() {
    this.resetAndLoad().then(() => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    if (!this.data.noMore && !this.data.loading) {
      this.loadMore()
    }
  },

  async resetAndLoad() {
    this.setData({ items: [], page: 1, noMore: false })
    await this.loadMore()
  },

  async loadMore() {
    if (this.data.loading) return
    this.setData({ loading: true })

    try {
      const { page, pageSize, subject } = this.data
      let url = `/api/errors?page=${page}&page_size=${pageSize}`
      if (subject) url += `&subject=${encodeURIComponent(subject)}`

      const res = await request({ url, showLoading: false })
      const newItems = (res.data.items || []).map((item) => ({
        ...item,
        subjectClass: getSubjectClass(item.subject),
        timeAgo: timeAgo(item.created_at),
      }))

      const items = [...this.data.items, ...newItems]
      this.setData({
        items,
        total: res.data.total,
        page: page + 1,
        noMore: items.length >= res.data.total,
        loading: false,
      })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  onSubjectFilter(e) {
    const idx = e.detail.value
    this.setData({ subjectIndex: idx, subject: this.data.subjects[idx] })
    this.resetAndLoad()
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/error-detail/error-detail?id=${id}` })
  },

  deleteItem(e) {
    const id = e.currentTarget.dataset.id
    const idx = e.currentTarget.dataset.idx

    wx.showModal({
      title: '确认删除',
      content: '删除后不可恢复',
      success: async (res) => {
        if (res.confirm) {
          try {
            await request({ url: `/api/errors/${id}`, method: 'DELETE' })
            const items = [...this.data.items]
            items.splice(idx, 1)
            this.setData({ items, total: this.data.total - 1 })
            wx.showToast({ title: '已删除', icon: 'success' })
          } catch (e) {}
        }
      },
    })
  },
})
