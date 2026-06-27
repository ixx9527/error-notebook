Component({
  properties: {
    type: { type: String, value: 'bar' }, // bar | pie
    data: { type: Array, value: [] },
    title: { type: String, value: '' },
    width: { type: Number, value: 300 },
    height: { type: Number, value: 200 },
  },

  observers: {
    'data': function () {
      this.draw()
    },
  },

  lifetimes: {
    attached() {
      this.initCanvas()
    },
  },

  data: {
    ctx: null,
    canvasWidth: 0,
    canvasHeight: 0,
  },

  methods: {
    initCanvas() {
      const query = this.createSelectorQuery()
      query.select('#chartCanvas')
        .fields({ node: true, size: true })
        .exec((res) => {
          if (!res[0]) return
          const canvas = res[0].node
          const ctx = canvas.getContext('2d')
          const dpr = wx.getWindowInfo().pixelRatio
          canvas.width = res[0].width * dpr
          canvas.height = res[0].height * dpr
          ctx.scale(dpr, dpr)
          this.setData({ ctx, canvasWidth: res[0].width, canvasHeight: res[0].height })
          this.draw()
        })
    },

    draw() {
      const { ctx, canvasWidth, canvasHeight } = this.data
      if (!ctx) return

      ctx.clearRect(0, 0, canvasWidth, canvasHeight)

      if (this.data.type === 'bar') {
        this.drawBar(ctx, canvasWidth, canvasHeight)
      } else if (this.data.type === 'pie') {
        this.drawPie(ctx, canvasWidth, canvasHeight)
      }
    },

    drawBar(ctx, w, h) {
      const data = this.data.data
      if (!data.length) return

      const padding = { top: 20, right: 10, bottom: 40, left: 30 }
      const chartW = w - padding.left - padding.right
      const chartH = h - padding.top - padding.bottom
      const maxVal = Math.max(...data.map((d) => d.value), 1)
      const barW = Math.min(30, (chartW / data.length) * 0.6)
      const gap = chartW / data.length

      const colors = ['#4A90D9', '#E67E22', '#27AE60', '#E74C3C', '#9B59B6', '#1ABC9C']

      ctx.font = '10px sans-serif'
      ctx.fillStyle = '#999'
      ctx.textAlign = 'center'

      data.forEach((d, i) => {
        const x = padding.left + i * gap + gap / 2 - barW / 2
        const barH = (d.value / maxVal) * chartH
        const y = padding.top + chartH - barH

        ctx.fillStyle = colors[i % colors.length]
        ctx.beginPath()
        ctx.roundRect(x, y, barW, barH, [3, 3, 0, 0])
        ctx.fill()

        ctx.fillStyle = '#666'
        ctx.fillText(d.value, x + barW / 2, y - 4)

        ctx.fillStyle = '#999'
        const label = d.label.length > 4 ? d.label.slice(0, 4) : d.label
        ctx.fillText(label, padding.left + i * gap + gap / 2, h - padding.bottom + 14)
      })

      ctx.strokeStyle = '#eee'
      ctx.beginPath()
      ctx.moveTo(padding.left, padding.top + chartH)
      ctx.lineTo(w - padding.right, padding.top + chartH)
      ctx.stroke()
    },

    drawPie(ctx, w, h) {
      const data = this.data.data
      if (!data.length) return

      const total = data.reduce((sum, d) => sum + d.value, 0)
      if (total === 0) return

      const cx = w / 2
      const cy = h / 2
      const r = Math.min(w, h) / 2 - 30
      const colors = ['#4A90D9', '#E67E22', '#27AE60', '#E74C3C', '#9B59B6', '#1ABC9C']

      let startAngle = -Math.PI / 2

      data.forEach((d, i) => {
        const sliceAngle = (d.value / total) * Math.PI * 2
        const endAngle = startAngle + sliceAngle

        ctx.fillStyle = colors[i % colors.length]
        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.arc(cx, cy, r, startAngle, endAngle)
        ctx.closePath()
        ctx.fill()

        const midAngle = startAngle + sliceAngle / 2
        const labelR = r + 16
        const lx = cx + Math.cos(midAngle) * labelR
        const ly = cy + Math.sin(midAngle) * labelR

        ctx.fillStyle = '#666'
        ctx.font = '10px sans-serif'
        ctx.textAlign = midAngle > Math.PI / 2 && midAngle < Math.PI * 1.5 ? 'right' : 'left'
        const pct = Math.round((d.value / total) * 100)
        ctx.fillText(`${d.label} ${pct}%`, lx, ly)

        startAngle = endAngle
      })
    },
  },
})
