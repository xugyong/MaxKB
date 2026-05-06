Component({
  properties: {
    value: {
      type: String,
      value: ''
    },
    loading: {
      type: Boolean,
      value: false
    }
  },
  methods: {
    openMenu() {
      this.triggerEvent('openmenu')
    },
    onInput(e) {
      this.triggerEvent('change', {
        value: e.detail.value
      })
    },
    send() {
      this.triggerEvent('send', {
        value: this.data.value
      })
    },
    onFocus(e) {
      this.triggerEvent('focus', e.detail)
    },
    onBlur(e) {
      this.triggerEvent('blur', e.detail)
    },
    onKeyboardHeightChange(e) {
      this.triggerEvent('keyboardheightchange', e.detail)
    }
  }
})
