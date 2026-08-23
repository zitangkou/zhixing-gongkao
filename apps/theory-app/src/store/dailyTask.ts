import { defineStore } from 'pinia'
import { api, type DailyLearningTask } from '@/api'

export const useDailyTaskStore = defineStore('theory-daily-task', {
  state: () => ({ task: null as DailyLearningTask | null, loading: false, starting: false, message: '' }),
  getters: {
    progressPercent: (state) => {
      if (!state.task) return 0
      if (state.task.progress.state === 'completed') return 100
      return Math.round((state.task.progress.currentStep * 100) / Math.max(state.task.progress.totalSteps, 1))
    },
  },
  actions: {
    async load() {
      this.loading = true
      this.message = ''
      const response = await api.getDailyTasks()
      this.loading = false
      if (response.code !== 0 || !response.data) {
        this.message = response.message
        return
      }
      this.task =
        response.data.tasks.find((item) => item.progress.state === 'in_progress') ||
        response.data.tasks.find((item) => item.progress.state !== 'completed') ||
        response.data.tasks[0] ||
        null
    },
    async start() {
      if (!this.task || this.task.progress.state !== 'not_started') return true
      this.starting = true
      const response = await api.updateDailyTask(this.task.id, { event: 'start' })
      this.starting = false
      if (response.code !== 0 || !response.data) {
        this.message = response.message
        return false
      }
      this.task = response.data
      return true
    },
  },
})
