import Taro from '@tarojs/taro'
import { clearToken, getToken } from '@/utils/auth'
import { getPlatform } from '@/utils/platform'
import type { ApiRes } from '@/types'

type UploadResult<T> = ApiRes<T>

/**
 * 跨端文件上传：H5 用 FormData+fetch（避免 blob 路径导致 uploadFile 失败），
 * 小程序用 Taro.uploadFile。
 */
export async function uploadFile<T>(
  url: string,
  filePath: string,
  options?: {
    name?: string
    /** H5 chooseImage 返回的原始 File，优先使用 */
    file?: File
  },
): Promise<UploadResult<T>> {
  const field = options?.name || 'file'
  const token = getToken()
  const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {}

  if (getPlatform() === 'h5') {
    try {
      let file = options?.file
      if (!file) {
        const blob = await fetch(filePath).then((r) => r.blob())
        const ext = (blob.type.split('/')[1] || 'jpeg').replace('jpeg', 'jpg')
        file = new File([blob], `upload.${ext}`, { type: blob.type || 'image/jpeg' })
      }
      const form = new FormData()
      form.append(field, file)
      const res = await fetch(url, { method: 'POST', headers, body: form })
      if (res.status === 401) {
        clearToken()
        return { code: 401, data: null as unknown as T, message: '登录已过期，请重新登录' }
      }
      const body = (await res.json()) as ApiRes<T>
      return body
    } catch (e) {
      return {
        code: -1,
        data: null as unknown as T,
        message: e instanceof Error ? e.message : '上传失败',
      }
    }
  }

  return new Promise((resolve) => {
    Taro.uploadFile({
      url,
      filePath,
      name: field,
      header: headers,
      success(res) {
        try {
          const body = JSON.parse(res.data) as ApiRes<T>
          if (res.statusCode === 401) {
            clearToken()
            resolve({ code: 401, data: null as unknown as T, message: '登录已过期，请重新登录' })
            return
          }
          resolve(body)
        } catch {
          resolve({ code: -1, data: null as unknown as T, message: '上传响应解析失败' })
        }
      },
      fail(err) {
        resolve({
          code: -1,
          data: null as unknown as T,
          message: (err as { errMsg?: string })?.errMsg || '上传失败',
        })
      },
    })
  })
}
