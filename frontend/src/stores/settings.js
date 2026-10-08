import { defineStore } from 'pinia'
import api from '../api'

export const useSettingsStore = defineStore('settings', {
  state: () => ({ difficulty: 'L1', topic: 'daily life', voice: 'aria', rate: 1.0,
                  topics: [], loaded: false,
                  // 循环播放是纯前端偏好，直接存本机
                  loop: localStorage.getItem('el-loop') === '1' }),
  actions: {
    setLoop(v) {
      this.loop = !!v
      localStorage.setItem('el-loop', this.loop ? '1' : '0')
    },
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
    /** 把用过的主题记进主题列表（01 练习页临时输入的主题也会进下拉框） */
    async rememberTopic(name) {
      const t = String(name || '').trim()
      if (!t || (this.topics || []).includes(t)) return
      await this.save({ topics: [...(this.topics || []), t] })
    },
  },
})
