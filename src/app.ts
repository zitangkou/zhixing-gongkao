import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createPersistedState } from 'pinia-plugin-persistedstate'
import Taro from '@tarojs/taro'
import '@nutui/nutui-taro/dist/style.css'
import '@nutui/icons-vue-taro/dist/style_iconfont.css'
import './app.scss'
import { bootstrapApp } from '@/utils/bootstrap'
import { useSettingsStore } from '@/store/settings'
import { applyTheme } from '@/utils/theme'
import { ensureFeedbackHost } from '@/utils/feedbackHost'

/** 尽早读本地偏好，减少首屏闪白 */
function applyThemeFromStorage() {
  try {
    const raw = Taro.getStorageSync('settings')
    if (!raw) return
    const data = typeof raw === 'string' ? JSON.parse(raw) : raw
    if (data?.darkMode) applyTheme(true)
  } catch {
    /* ignore */
  }
}
applyThemeFromStorage()

const pinia = createPinia()
pinia.use(
  createPersistedState({
    storage: {
      getItem(key: string) {
        const value = Taro.getStorageSync(key)
        return value === '' || value === undefined ? null : value
      },
      setItem(key: string, value: string) {
        Taro.setStorageSync(key, value)
      },
    },
  }),
)

const App = createApp({
  onShow() {
    useSettingsStore().hydrateTheme()
    ensureFeedbackHost()
    bootstrapApp()
  },
})

// H5 尽早挂载反馈层，避免首屏 toast 落到原生难看实现
ensureFeedbackHost()

App.use(pinia)

export default App
