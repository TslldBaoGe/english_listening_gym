import { defineStore } from 'pinia'
import api from '../api'

export const useSettingsStore = defineStore('settings', {
  state: () => ({ difficulty: 'L1', topic: 'daily life', voice: 'aria', rate: 1.0, loaded: false }),
  actions: {
    async load() {
      if (this.loaded) return
      const { data } = await api.getSettings()
      Object.assign(this, data, { rate: Number(data.rate) })
      this.loaded = true
    },
    async save(patch) {
      const { data } = await api.putSettings(patch)
      Object.assign(this, data, { rate: Number(data.rate) })
    },
  },
})
