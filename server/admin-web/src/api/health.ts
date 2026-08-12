import http, { getData } from './http'

export interface HealthUser {
  userId: string
  nickname: string
  programStartDate: string
  privateFocus: string
}

export interface HealthOverview {
  currentWeek: number
  currentPhase: number
  phaseName: string
  bodyScore: number
  cbtScore: number
  streak: number
  totalDays: number
  weeklyTrend: { week: number; body: number; cbt: number }[]
}

export interface HealthDailyLog {
  id: string
  userId: string
  logDate: string
  sleepHours: number
  sleepQuality: number
  exerciseMinutes: number
  exerciseType: string
  meals: Record<string, unknown>
  stool: Record<string, unknown>
  cbtDone: boolean
  ruminationLevel: number
  bodyScore: number
  cbtScore: number
  note: string
}

export interface HealthPhase {
  phase: number
  name: string
  weeks: string
  focus: string
  tasks: { id: string; label: string; description: string }[]
}

export const listHealthUsers = () => getData<HealthUser[]>(http.get('/admin/health/users'))

export const getHealthOverview = (userId: string) =>
  getData<HealthOverview>(http.get('/admin/health/overview', { params: { userId } }))

export const getHealthDaily = (userId: string, start?: string, end?: string) =>
  getData<HealthDailyLog[]>(http.get('/admin/health/daily', { params: { userId, start, end } }))

export const listHealthPhases = () => getData<HealthPhase[]>(http.get('/admin/health/phases'))
