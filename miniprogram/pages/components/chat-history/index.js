Component({
  properties: {
    list: {
      type: Array,
      value: []
    },
    visible: {
      type: Boolean,
      value: false
    }
  },
  data: {
    activeMenuId: '',
    renamingId: '',
    renameValue: ''
  },
  methods: {
    noop() {},
    close() {
      this.setData({ activeMenuId: '', renamingId: '' })
      this.triggerEvent('close')
    },
    create() {
      this.triggerEvent('create')
    },
    select(e) {
      const id = e && e.currentTarget && e.currentTarget.dataset ? e.currentTarget.dataset.id : ''
      if (!id) return
      this.setData({ activeMenuId: '', renamingId: '' })
      this.triggerEvent('select', { id }, { bubbles: true, composed: true })
    },
    toggleMenu(e) {
      const id = e && e.currentTarget && e.currentTarget.dataset ? e.currentTarget.dataset.id : ''
      if (!id) return
      this.setData({
        activeMenuId: this.data.activeMenuId === id ? '' : id,
        renamingId: ''
      })
    },
    openRename(e) {
      const id = e && e.currentTarget && e.currentTarget.dataset ? e.currentTarget.dataset.id : ''
      if (!id) return
      const target = (this.data.list || []).find(item => item.id === id)
      this.setData({
        activeMenuId: '',
        renamingId: id,
        renameValue: target ? (target.title || '') : ''
      })
    },
    onRenameInput(e) {
      const value = e && e.detail ? e.detail.value : ''
      this.setData({ renameValue: value })
    },
    cancelRename() {
      this.setData({ renamingId: '', renameValue: '' })
    },
    confirmRename() {
      const id = this.data.renamingId
      const title = String(this.data.renameValue || '').trim()
      if (!id || !title) return
      this.setData({ renamingId: '', renameValue: '' })
      this.triggerEvent('rename', { id, title }, { bubbles: true, composed: true })
    },
    remove(e) {
      const id = e && e.currentTarget && e.currentTarget.dataset ? e.currentTarget.dataset.id : ''
      this.setData({ activeMenuId: '', renamingId: '' })
      this.triggerEvent('remove', { id }, { bubbles: true, composed: true })
    }
  }
})
