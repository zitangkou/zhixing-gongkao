import * as d from '../_shared'

export const apiProduct = {
  getDailyTasks(date?: string): Promise<d.ApiRes<d.DailyTaskList>> {
    const query = date ? `?date=${encodeURIComponent(date)}` : ''
    return d.request<d.DailyTaskList>(`/api/product/daily-tasks${query}`)
  },

  updateDailyTaskProgress(
    taskId: string,
    payload: {
      event: d.DailyTaskEvent
      currentStep?: number
      totalSteps?: number
      draft?: Record<string, unknown>
    },
  ): Promise<d.ApiRes<d.DailyLearningTask>> {
    return d.request<d.DailyLearningTask>(`/api/product/daily-tasks/${taskId}/progress`, {
      method: 'POST',
      data: payload,
    })
  },
}
