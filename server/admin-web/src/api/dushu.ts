import http, { getData } from './http'

export interface DushuBook {
  id: string
  userId: string
  title: string
  author: string
  category: string
  status: string
  currentChapter: string
  coverNote: string
  createdAt: string
  updatedAt: string
}

export interface DushuDailyLog {
  id: string
  userId: string
  bookId: string
  bookTitle: string
  logDate: string
  chapter: string
  outputCard: string
  reflection: string
  createdAt: string
}

export interface DushuPersonCard {
  id: string
  userId: string
  bookId: string
  bookTitle: string
  name: string
  era: string
  role: string
  keyEvents: string
  evaluation: string
  createdAt: string
}

export interface DushuBookSummary {
  id: string
  userId: string
  bookId: string
  bookTitle: string
  onePageSummary: string
  mindMap: string
  updatedAt: string
}

export interface DushuStats {
  totalBooks: number
  readingBooks: number
  finishedBooks: number
  totalDailyLogs: number
  totalPersons: number
  totalSummaries: number
}

export const listDushuBooks = (params?: { userId?: string; status?: string }) =>
  getData<DushuBook[]>(http.get('/admin/dushu/books', { params }))

export const listDushuDaily = (userId: string, bookId?: string) =>
  getData<DushuDailyLog[]>(http.get('/admin/dushu/daily', { params: { userId, bookId } }))

export const listDushuPersons = (userId: string, bookId?: string) =>
  getData<DushuPersonCard[]>(http.get('/admin/dushu/persons', { params: { userId, bookId } }))

export const listDushuSummaries = (userId: string) =>
  getData<DushuBookSummary[]>(http.get('/admin/dushu/summaries', { params: { userId } }))

export const getDushuStats = (userId: string) =>
  getData<DushuStats>(http.get('/admin/dushu/stats', { params: { userId } }))

export const updateDushuBook = (id: string, data: Record<string, unknown>) =>
  getData<DushuBook>(http.put(`/admin/dushu/book/${id}`, data))

export const deleteDushuBook = (id: string) => getData(http.delete(`/admin/dushu/book/${id}`))
