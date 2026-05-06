Component({
  properties: {
    config: {
      type: Array,
      value: []
    },
    value: {
      type: Object,
      value: {}
    }
  },
  methods: {
    close() {
      this.triggerEvent('close')
    },
    confirm() {
      this.triggerEvent('confirm')
    },
    change(e) {
      this.triggerEvent('change', e)
    }
  }
})
