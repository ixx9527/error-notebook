const { request } = require('../../utils/api')
const { showLoginDialog } = require('../../utils/auth')

Page({
  data: {
    stats: {},
    trend: [],
    mastery: [],
    trendDays: 30,
    loading: true,
  },

  onShow() {
    const app = getApp()
    if (app.isGuest()) {
      showLoginDialog().then((ok) => {
        if (!ok) wx.navigateBack()
      })
      return
    }
    this.loadAll()
  },

  async loadAll() {
    try {
      const [statsRes, trendRes, masteryRes] = await Promise.all([
        request({ url: '/api/stats/summary', showLoading: false }),
        request({ url: `/api/stats/trend?days=${this.data.trendDays}`, showLoading: false }),
        request({ url: '/api/stats/mastery', showLoading: false }),
      ])

      const data = statsRes.data
      const subjectList = Object.entries(data.by_subject || {}).map(([name, count]) => ({
        name,
        count,
        percent: data.total_questions ? Math.round(count / data.total_questions * 100) : 0,
      }))

      const errorTypeList = Object.entries(data.by_error_type || {}).map(([name, count]) => ({
        name,
        count,
      }))

      const trend = trendRes.data || []
      const maxTrend = Math.max(...trend.map((d) => d.count), 1)
      const trendWithHeight = trend.map((d) => ({
        ...d,
        height: Math.max(2, (d.count / maxTrend) * 100),
      }))

      const mastery = masteryRes.data || []
      const maxMastery = Math.max(...mastery.map((d) => d.count), 1)
      const masteryWithWidth = mastery.map((d) => ({
        ...d,
        width: Math.max(2, (d.count / maxMastery) * 100),
      }))

      this.setData({
        stats: { ...data, subjectList, errorTypeList },
        trend: trendWithHeight,
        mastery: masteryWithWidth,
        subjectChartData: subjectList.map((s) => ({ label: s.name, value: s.count })),
        errorTypeChartData: errorTypeList.map((e) => ({ label: e.name, value: e.count })),
        chartWidth: 280,
        chartHeight: 180,
        loading: false,
      })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  switchTrend(e) {
    const days = e.currentTarget.dataset.days
    this.setData({ trendDays: days })
    this.loadAll()
  },
})
