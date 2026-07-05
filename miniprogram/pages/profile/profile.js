const { request } = require('../../utils/api')
const { clearToken, showLoginDialog } = require('../../utils/auth')

Page({
  data: {
    isGuest: false,
    profile: {},
    children: [],
    editing: false,
    editData: {},
    gradeOptions: ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级'],
    showChildForm: false,
    childEditData: { name: '', grade: '' },
    editingChildId: null,
  },

  onShow() {
    const app = getApp()
    const isGuest = app.isGuest()
    this.setData({ isGuest })
    if (typeof this.getTabBar === 'function') {
      this.getTabBar().setData({ selected: 2, theme: app.getTheme() })
    }
    if (!isGuest) {
      this.loadProfile()
      this.loadChildren()
    }
  },

  goLogin() {
    const app = getApp()
    app.ensureLogin().then((ok) => {
      if (ok) {
        this.setData({ isGuest: false })
        this.loadProfile()
        this.loadChildren()
      }
    })
  },

  async loadProfile() {
    try {
      const res = await request({ url: '/api/users/profile', showLoading: false })
      this.setData({ profile: res.data || {} })
    } catch (e) {}
  },

  async loadChildren() {
    try {
      const res = await request({ url: '/api/children', showLoading: false })
      this.setData({ children: res.data || [] })
    } catch (e) {}
  },

  startEdit() {
    const p = this.data.profile
    this.setData({
      editing: true,
      editData: {
        nickname: p.nickname || '',
        child_name: p.child_name || '',
        child_grade: p.child_grade || '',
        serverchan_key: p.serverchan_key || '',
      },
    })
  },

  onEditInput(e) {
    const { field } = e.currentTarget.dataset
    this.setData({ [`editData.${field}`]: e.detail.value })
  },

  async saveEdit() {
    try {
      const res = await request({
        url: '/api/users/profile',
        method: 'PUT',
        data: this.data.editData,
      })
      this.setData({ profile: res.data, editing: false })
      wx.showToast({ title: '已保存', icon: 'success' })
    } catch (e) {}
  },

  cancelEdit() {
    this.setData({ editing: false })
  },

  showAddChild() {
    this.setData({ showChildForm: true, editingChildId: null, childEditData: { name: '', grade: '' } })
  },

  showEditChild(e) {
    const child = this.data.children.find((c) => c.id === e.currentTarget.dataset.id)
    if (child) {
      this.setData({
        showChildForm: true,
        editingChildId: child.id,
        childEditData: { name: child.name, grade: child.grade || '' },
      })
    }
  },

  onChildInput(e) {
    const { field } = e.currentTarget.dataset
    this.setData({ [`childEditData.${field}`]: e.detail.value })
  },

  async saveChild() {
    const { editingChildId, childEditData } = this.data
    try {
      if (editingChildId) {
        await request({
          url: `/api/children/${editingChildId}`,
          method: 'PUT',
          data: childEditData,
        })
      } else {
        await request({
          url: '/api/children',
          method: 'POST',
          data: childEditData,
        })
      }
      this.setData({ showChildForm: false })
      this.loadChildren()
      wx.showToast({ title: '已保存', icon: 'success' })
    } catch (e) {}
  },

  deleteChild(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认删除',
      content: '删除后该孩子的错题数据不会被删除',
      success: async (res) => {
        if (res.confirm) {
          await request({ url: `/api/children/${id}`, method: 'DELETE' })
          this.loadChildren()
        }
      },
    })
  },

  hideChildForm() {
    this.setData({ showChildForm: false })
  },

  goExport() {
    wx.navigateTo({ url: '/pages/export/export' })
  },

  goStats() {
    wx.navigateTo({ url: '/pages/stats/stats' })
  },

  logout() {
    wx.showModal({
      title: '确认退出',
      content: '退出后需要重新登录',
      success: (res) => {
        if (res.confirm) {
          clearToken()
          const app = getApp()
          app.globalData.token = null
          app.globalData.userId = null
          wx.reLaunch({ url: '/pages/index/index' })
        }
      },
    })
  },
})
