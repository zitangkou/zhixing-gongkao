import http, { getData } from './http'

export interface EnglishArticle {
  id: string
  title: string
  source: string
  level: string
  content: string
  vocabHighlights: { word: string; meaning: string; pos: string; sentence: string }[]
  audioUrl: string
  tags: string[]
  difficulty: number
  isPublished: boolean
  readCount: number
  createdAt: string
}

export interface SpeakingLesson {
  id: string
  title: string
  topic: string
  level: string
  dialogue: { speaker: string; en: string; zh: string }[]
  keySentences: { en: string; zh: string; pattern: string }[]
  tips: string
  isPublished: boolean
  createdAt: string
}

export interface GrammarLesson {
  id: string
  title: string
  category: string
  level: string
  explanation: string
  examples: { en: string; zh: string }[]
  commonMistakes: { wrong: string; correct: string; note: string }[]
  sortOrder: number
  isPublished: boolean
  createdAt: string
}

// 文章
export function fetchEnglishArticles() {
  return getData<EnglishArticle[]>(http.get('/admin/english/articles'))
}

export function createEnglishArticle(data: any) {
  return getData<EnglishArticle>(http.post('/admin/english/article', data))
}

export function updateEnglishArticle(id: string, data: any) {
  return getData<EnglishArticle>(http.put(`/admin/english/article/${id}`, data))
}

export function deleteEnglishArticle(id: string) {
  return getData<{ ok: boolean }>(http.delete(`/admin/english/article/${id}`))
}

// 口语
export function fetchSpeakingLessons() {
  return getData<SpeakingLesson[]>(http.get('/admin/english/speaking'))
}

export function createSpeakingLesson(data: any) {
  return getData<SpeakingLesson>(http.post('/admin/english/speaking', data))
}

export function updateSpeakingLesson(id: string, data: any) {
  return getData<SpeakingLesson>(http.put(`/admin/english/speaking/${id}`, data))
}

export function deleteSpeakingLesson(id: string) {
  return getData<{ ok: boolean }>(http.delete(`/admin/english/speaking/${id}`))
}

// 语法
export function fetchGrammarLessons() {
  return getData<GrammarLesson[]>(http.get('/admin/english/grammar'))
}

export function createGrammarLesson(data: any) {
  return getData<GrammarLesson>(http.post('/admin/english/grammar', data))
}

export function updateGrammarLesson(id: string, data: any) {
  return getData<GrammarLesson>(http.put(`/admin/english/grammar/${id}`, data))
}

export function deleteGrammarLesson(id: string) {
  return getData<{ ok: boolean }>(http.delete(`/admin/english/grammar/${id}`))
}
