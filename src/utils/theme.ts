import Taro from '@tarojs/taro'

const THEME_CLASS = 'theme-dark'
const isH5 = process.env.TARO_ENV === 'h5'

function setDomTheme(dark: boolean) {
  if (typeof document === 'undefined') return
  const roots = [document.documentElement, document.body, document.getElementById('app')].filter(
    Boolean,
  ) as HTMLElement[]
  for (const el of roots) {
    el.classList.toggle(THEME_CLASS, dark)
  }
}

/** 吞掉小程序专有 API 在 H5 上的 Promise 拒绝 */
function callNative(fn: () => unknown) {
  try {
    const ret = fn()
    if (ret && typeof (ret as Promise<unknown>).then === 'function') {
      ;(ret as Promise<unknown>).catch(() => {})
    }
  } catch {
    /* 部分环境无对应 API */
  }
}

/** 同步导航栏 / 窗口背景（小程序原生；H5 仅改 DOM） */
function setNativeChrome(dark: boolean) {
  callNative(() =>
    Taro.setNavigationBarColor({
      frontColor: '#ffffff',
      backgroundColor: dark ? '#8B0000' : '#D0021B',
      animation: { duration: 200, timingFunc: 'easeIn' },
    }),
  )
  // 下拉背景色 / 文字样式仅小程序支持，H5 会抛「暂时不支持 API」
  if (isH5) return
  callNative(() =>
    Taro.setBackgroundColor({
      backgroundColor: dark ? '#121212' : '#f3f4f6',
      backgroundColorTop: dark ? '#121212' : '#f3f4f6',
      backgroundColorBottom: dark ? '#121212' : '#f3f4f6',
    }),
  )
  callNative(() =>
    Taro.setBackgroundTextStyle({ textStyle: dark ? 'light' : 'dark' }),
  )
}

/** 应用深色 / 浅色主题到 DOM 与原生壳 */
export function applyTheme(dark: boolean) {
  setDomTheme(dark)
  setNativeChrome(dark)
}
