const { request, BASE_URL } = require('../../utils/api')
const { getToken } = require('../../utils/auth')

Page({
  data: {
    tab: 'normal',
    subjects: ['', '数学', '语文', '英语'],
    subjectIndex: 0,
    dateFrom: '',
    dateTo: '',
    year: 0,
    month: 0,
    children: [],
    childIndex: 0,
    exporting: false,
  },

  onLoad() {
    const now = new Date()
    this.setData({ year: now.getFullYear(), month: now.getMonth() + 1 })
    this.loadChildren()
  },

  async loadChildren() {
    try {
      const res = await request({ url: '/api/children', showLoading: false })
      this.setData({ children: [{ id: '', name: '全部' }, ...(res.data || [])] })
    } catch (e) {
      this.setData({ children: [{ id: '', name: '全部' }] })
    }
  },

  switchTab(e) {
    this.setData({ tab: e.currentTarget.dataset.tab })
  },

  onSubjectChange(e) { this.setData({ subjectIndex: e.detail.value }) },
  onDateFromChange(e) { this.setData({ dateFrom: e.detail.value }) },
  onDateToChange(e) { this.setData({ dateTo: e.detail.value }) },
  onYearChange(e) { this.setData({ year: parseInt(e.detail.value) }) },
  onMonthChange(e) { this.setData({ month: parseInt(e.detail.value) }) },
  onChildChange(e) { this.setData({ childIndex: e.detail.value }) },

  getExportUrl() {
    const { tab, subjectIndex, subjects, dateFrom, dateTo, year, month, children, childIndex } = this.data
    const child = children[childIndex]
    const childParam = child && child.id ? `&child_id=${child.id}` : ''

    if (tab === 'monthly') {
      return `${BASE_URL}/api/export/monthly-report?year=${year}&month=${month}${childParam}`
    }

    let url = `${BASE_URL}/api/export/pdf`
    const params = []
    if (subjects[subjectIndex]) params.push(`subject=${encodeURIComponent(subjects[subjectIndex])}`)
    if (dateFrom) params.push(`date_from=${dateFrom}`)
    if (dateTo) params.push(`date_to=${dateTo}`)
    if (childParam) params.push(childParam.slice(1))
    if (params.length) url += '?' + params.join('&')
    return url
  },

  async exportPdf() {
    const url = this.getExportUrl()
    this.setData({ exporting: true })

    const token = getToken()
    const that = this

    wx.downloadFile({
      url,
      header: { Authorization: token ? `Bearer ${token}` : '' },
      success(res) {
        that.setData({ exporting: false })
        if (res.statusCode === 200) {
          wx.openDocument({ filePath: res.tempFilePath, fileType: 'pdf', showMenu: true })
        } else {
          wx.showToast({ title: '导出失败', icon: 'none' })
        }
      },
      fail() {
        that.setData({ exporting: false })
        wx.showToast({ title: '网络错误', icon: 'none' })
      },
    })
  },
})
