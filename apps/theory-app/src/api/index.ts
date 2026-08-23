import Taro from '@tarojs/taro'
import { getToken } from '@/utils/auth'

export interface ApiResponse<T> {
  code: number
  data: T | null
  message: string
}

export type DailyTaskState = 'not_started' | 'in_progress' | 'submitted' | 'reviewed' | 'completed'
export type DailyTaskEvent = 'start' | 'save' | 'submit' | 'review' | 'complete'

export interface DailyLearningTask {
  id: string
  productKey: 'theory'
  taskDate: string
  taskType: string
  title: string
  description: string
  contentType: string
  contentId: string
  estimatedMinutes: number
  totalSteps: number
  sortOrder: number
  metadata: Record<string, unknown>
  progress: {
    state: DailyTaskState
    currentStep: number
    totalSteps: number
    draft: Record<string, unknown>
    updatedAt?: string
  }
}

export interface DailyTaskList {
  date: string
  productKey: 'theory'
  completion: number
  completedCount: number
  totalCount: number
  estimatedMinutes: number
  tasks: DailyLearningTask[]
}

async function request<T>(path: string, options: { method?: 'GET' | 'POST'; data?: unknown; auth?: boolean } = {}): Promise<ApiResponse<T>> {
  const token = options.auth === false ? '' : getToken()
  try {
    const response = await Taro.request<ApiResponse<T>>({
      url: `${API_BASE_URL}${path}`,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        'X-Product-Key': PRODUCT_KEY,
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
    if (response.statusCode === 401 || response.statusCode === 403) {
      return { code: response.statusCode, data: null, message: '登录后同步你的今日学习包' }
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      return { code: response.statusCode, data: null, message: `服务暂不可用（${response.statusCode}）` }
    }
    return response.data
  } catch {
    return { code: -1, data: null, message: '暂时无法连接学习服务' }
  }
}

export const api = {
  login(username: string, password: string) {
    return request<{ access_token: string; token_type: string }>('/api/auth/login', {
      method: 'POST', data: { username, password }, auth: false,
    })
  },
  getDailyTasks(date?: string) {
    const query = date ? `?date=${encodeURIComponent(date)}` : ''
    return request<DailyTaskList>(`/api/product/daily-tasks${query}`)
  },
  updateDailyTask(taskId: string, payload: { event: DailyTaskEvent; currentStep?: number; draft?: Record<string, unknown> }) {
    return request<DailyLearningTask>(`/api/product/daily-tasks/${taskId}/progress`, { method: 'POST', data: payload })
  },
}
