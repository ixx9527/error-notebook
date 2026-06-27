Component({
  properties: {
    question: { type: Object, value: {} },
    showTags: { type: Boolean, value: true },
    showTime: { type: Boolean, value: true },
  },

  data: {
    subjectClass: '',
  },

  observers: {
    'question.subject': function (subject) {
      const map = { '数学': 'subject-math', '语文': 'subject-chinese', '英语': 'subject-english' }
      this.setData({ subjectClass: map[subject] || 'subject-other' })
    },
  },

  methods: {
    onTap() {
      this.triggerEvent('tap', { id: this.data.question.id })
    },
  },
})
