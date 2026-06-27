const { request } = require('../../utils/api')
const { getSubjectClass, formatDate } = require('../../utils/util')

Page({
  data: {
    id: null,
    question: null,
    editing: false,
    editData: {},
  },

  onLoad(options) {
    this.setData({ id: options.id })
    this.loadDetail()
  },

  async loadDetail() {
    try {
      const res = await request({ url: `/api/errors/${this.data.id}` })
      const q = res.data
      q.subjectClass = getSubjectClass(q.subject)
      q.createdDate = formatDate(q.created_at)
      this.setData({ question: q })
    } catch (e) {
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  startEdit() {
    const q = this.data.question
    this.setData({
      editing: true,
      editData: {
        subject: q.subject,
        topic: q.topic || '',
        question_text: q.question_text || '',
        student_answer: q.student_answer || '',
        correct_answer: q.correct_answer || '',
        error_type: q.error_type || '',
        error_analysis: q.error_analysis || '',
      },
    })
  },

  onEditInput(e) {
    const { field } = e.currentTarget.dataset
    this.setData({ [`editData.${field}`]: e.detail.value })
  },

  async saveEdit() {
    try {
      await request({
        url: `/api/errors/${this.data.id}`,
        method: 'PUT',
        data: this.data.editData,
      })
      this.setData({ editing: false })
      this.loadDetail()
      wx.showToast({ title: '已保存', icon: 'success' })
    } catch (e) {}
  },

  cancelEdit() {
    this.setData({ editing: false })
  },
})
