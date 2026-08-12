import { defineStore } from 'pinia'
import { applyTheme } from '@/utils/theme'

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    darkMode: false,
  }),

  actions: {
    setDarkMode(on: boolean) {
      this.darkMode = on
      applyTheme(on)
    },

    toggleDarkMode() {
      this.setDarkMode(!this.darkMode)
    },

    /** 启动时根据持久化状态套用主题 */
    hydrateTheme() {
      applyTheme(this.darkMode)
    },
  },

  persist: {
    pick: ['darkMode'],
  },
})
