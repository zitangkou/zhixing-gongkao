import Taro from '@tarojs/taro'

const TOKEN_KEY = 'zhengkao_token'

export function getToken(): string { return Taro.getStorageSync(TOKEN_KEY) || '' }
export function setToken(token: string) { Taro.setStorageSync(TOKEN_KEY, token) }
export function isLoggedIn() { return !!getToken() }
