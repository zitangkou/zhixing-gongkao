import Taro from '@tarojs/taro'

export function showToast(title: string) {
  return Taro.showToast({ title, icon: 'none', duration: 2200 })
}

export async function showConfirm(content: string): Promise<boolean> {
  const result = await Taro.showModal({ title: '请确认', content, confirmColor: '#D0021B' })
  return result.confirm
}
