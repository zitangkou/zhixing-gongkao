import Taro from '@tarojs/taro'

export function showToast(title: string) {
  return Taro.showToast({ title, icon: 'none', duration: 2200 })
}
