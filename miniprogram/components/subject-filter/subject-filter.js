Component({
  properties: {
    subjects: { type: Array, value: ['全部', '数学', '语文', '英语'] },
    current: { type: String, value: '' },
  },

  methods: {
    onSelect(e) {
      const subject = e.currentTarget.dataset.subject
      this.triggerEvent('change', { subject })
    },
  },
})
