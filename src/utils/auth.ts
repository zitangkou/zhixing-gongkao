import Taro from '@tarojs/taro'

const TOKEN_KEY = 'zhengkao_token'

export function getToken(): string {
  return Taro.getStorageSync(TOKEN_KEY) || ''
}

export function setToken(token: string): void {
  Taro.setStorageSync(TOKEN_KEY, token)
}

export function clearToken(): void {
  Taro.removeStorageSync(TOKEN_KEY)
}

export function isLoggedIn(): boolean {
  return !!getToken()
}

export function isAuthPageRoute(route?: string): boolean {
  return !!route?.includes('pages/auth/')
}
