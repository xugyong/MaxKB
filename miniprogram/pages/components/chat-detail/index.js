Component({
  properties: {
    title: {
      type: String,
      value: ''
    },
    type: {
      type: String,
      value: 'execution'
    },
    list: {
      type: Array,
      value: []
    }
  },
  methods: {
    close() {
      this.triggerEvent('close')
    }
  }
})
