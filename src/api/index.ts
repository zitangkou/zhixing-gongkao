import type {
  AnswerResult,
  ApiRes,
  Article,
  ArticleListPage,
  DayPlan,
  DailyReview,
  ExamPaper,
  ExamPaperDetail,
  ExamStartResult,
  ExamAttempt,
  ExamAttemptDetail,
  KnowledgeNode,
  KnowledgeReviewAnswer,
  KnowledgeReviewDue,
  KnowledgeReviewResult,
  KnowledgeReviewSession,
  KnowledgeTree,
  ManualWrong,
  ReviewHub,
  PlanTask,
  PointsLog,
  Question,
  QuizCompleteResult,
  QuizRankItem,
  RankItem,
  ReviewTask,
  StudyRecord,
  UserInfo,
  RmrbArticle,
  ShenlunMineLog,
  ShenlunMineTermItem,
  ShenlunQuoteItem,
  ShenlunVerbItem,
  ShenlunArgumentSkeleton,
  ShenlunTemplateItem,
  ShenlunNormTerm,
  ShenlunStats,
  ShenlunDrillLog,
  ShenlunMeta,
  ShenlunSkeletonTemplate,
  ShenlunSkeletonStructure,
  ShenlunTermCategory,
  GrowthOverview,
  CorpusItem,
  CorpusStats,
  EventHub,
  EventImpression,
  WrongQuestionRecord,
  ZiliaoDrillSet,
  ZiliaoDrillSetDetail,
  ZiliaoDrillSubmitResult,
  ZiliaoFormula,
  ZiliaoOverview,
  ZiliaoQuestionType,
  ZiliaoTrick,
} from '@/types'
import type { RankType } from '@/constants'
import { mockService } from '@/mock/service'
import { clearToken, getToken } from '@/utils/auth'
import { API_BASE } from '@/utils/media'
import { uploadFile } from '@/utils/upload'

/** 仅当 USE_MOCK=true 时使用 Mock */
export const isMock = typeof USE_MOCK !== 'undefined' && USE_MOCK

const BASE_URL = API_BASE

export interface UserMeData {
  id: string
  username?: string
  nickname: string
  avatar: string
  email?: string
  phone?: string
  isMember: boolean
  points: number
  hasSignedToday: boolean
  signDates: string[]
}

export interface AuthResult {
  access_token: string
  token_type: string
  user: UserMeData
}

async function request<T>(
  url: string,
  options?: { method?: string; data?: unknown; auth?: boolean },
): Promise<ApiRes<T>> {
  const needAuth = options?.auth !== false
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (needAuth && !isMock) {
    const token = getToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }
  try {
    const res = await fetch(`${BASE_URL}${url}`, {
      method: options?.method || 'GET',
      headers,
      body: options?.data ? JSON.stringify(options.data) : undefined,
    })
    if (res.status === 401 && needAuth) {
      clearToken()
      return { code: 401, data: null as T, message: '登录已过期，请重新登录' }
    }
    if (res.status === 403 && needAuth) {
      return { code: 403, data: null as T, message: '未登录或登录已失效，请重新登录' }
    }
    if (!res.ok) {
      const body = await res.json().catch(() => null)
      return {
        code: res.status,
        data: null as T,
        message: (body as ApiRes<T> | null)?.message || `HTTP ${res.status}`,
      }
    }
    return res.json()
  } catch (e) {
    const message = e instanceof Error ? e.message : '网络请求失败'
    return { code: -1, data: null as T, message }
  }
}

export const api = {
  getPublicConfig(): Promise<ApiRes<{ allowRegister: boolean }>> {
    if (isMock) {
      return Promise.resolve({ code: 0, data: { allowRegister: true }, message: 'ok' })
    }
    return request<{ allowRegister: boolean }>('/api/config', { auth: false })
  },

  register(username: string, password: string, passwordConfirm: string): Promise<ApiRes<AuthResult>> {
    return isMock
      ? mockService.register(username, password)
      : request<AuthResult>('/api/auth/register', {
          method: 'POST',
          data: { username, password, passwordConfirm },
          auth: false,
        })
  },

  login(username: string, password: string): Promise<ApiRes<AuthResult>> {
    return isMock
      ? mockService.login(username, password)
      : request<AuthResult>('/api/auth/login', {
          method: 'POST',
          data: { username, password },
          auth: false,
        })
  },

  getUserMe(): Promise<ApiRes<UserMeData>> {
    return isMock
      ? mockService.getUserMe()
      : request<UserMeData>('/api/user/me')
  },

  updateProfile(data: {
    nickname?: string
    email?: string
    phone?: string
  }): Promise<ApiRes<UserMeData>> {
    return isMock
      ? mockService.updateProfile(data)
      : request<UserMeData>('/api/user/me', { method: 'PUT', data })
  },

  changePassword(data: {
    oldPassword: string
    newPassword: string
    newPasswordConfirm: string
  }): Promise<ApiRes<{ ok: boolean }>> {
    return isMock
      ? mockService.changePassword(data)
      : request<{ ok: boolean }>('/api/user/password', { method: 'POST', data })
  },

  uploadAvatar(filePath: string, file?: File): Promise<ApiRes<UserMeData>> {
    if (isMock) return mockService.uploadAvatar(filePath)
    return uploadFile<UserMeData>(`${BASE_URL}/api/user/avatar`, filePath, { file })
  },

  getDailyArticles(): Promise<ApiRes<Article[]>> {
    return isMock ? mockService.getDailyArticles() : request('/api/articles/daily', { auth: false })
  },

  getRecommendedArticles(offset = 0, limit = 5): Promise<ApiRes<ArticleListPage>> {
    return isMock
      ? mockService.getRecommendedArticles(offset, limit)
      : request(`/api/articles/recommended?offset=${offset}&limit=${limit}`, { auth: false })
  },

  getArticleDetail(id: string): Promise<ApiRes<Article | null>> {
    return isMock
      ? mockService.getArticleDetail(id)
      : request(`/api/articles/${id}`, { auth: false })
  },

  getQuestions(articleId: string): Promise<ApiRes<Question[]>> {
    return isMock
      ? mockService.getQuestions(articleId)
      : request(`/api/questions?articleId=${articleId}`)
  },

  getQuizByMode(mode: string, count = 10): Promise<ApiRes<Question[]>> {
    return isMock
      ? mockService.getQuizByMode(mode, count)
      : request(`/api/quiz?mode=${mode}&count=${count}`)
  },

  submitAnswer(questionId: string, answer: string | string[]): Promise<ApiRes<AnswerResult>> {
    return isMock
      ? mockService.submitAnswer(questionId, answer)
      : request('/api/answer', { method: 'POST', data: { questionId, answer } })
  },

  getWrongQuestions(status: 'review' | 'waiting' | 'all' = 'review'): Promise<ApiRes<WrongQuestionRecord[]>> {
    return isMock
      ? mockService.getWrongQuestions()
      : request(`/api/wrong?status=${status}`)
  },

  redoWrongQuestion(questionId: string, answer: string | string[]): Promise<ApiRes<AnswerResult>> {
    return isMock
      ? mockService.redoWrongQuestion(questionId, answer)
      : request('/api/wrong/redo', { method: 'POST', data: { questionId, answer } })
  },

  removeWrongQuestion(questionId: string): Promise<ApiRes<null>> {
    return isMock
      ? mockService.removeWrongQuestion(questionId)
      : request(`/api/wrong/${questionId}`, { method: 'DELETE' })
  },

  getStudyRecords(): Promise<ApiRes<StudyRecord[]>> {
    return isMock ? mockService.getStudyRecords() : request('/api/study/records')
  },

  getSectionReads(): Promise<ApiRes<Record<string, string[]>>> {
    return isMock ? mockService.getSectionReads() : request('/api/study/section-reads')
  },

  markSectionRead(articleId: string, sectionId: string): Promise<ApiRes<null>> {
    return isMock
      ? mockService.markSectionRead(articleId, sectionId)
      : request('/api/study/sections/read', {
          method: 'POST',
          data: { articleId, sectionId },
        })
  },

  getReviewTasks(_records?: StudyRecord[]): Promise<ApiRes<ReviewTask[]>> {
    return isMock ? mockService.getReviewTasks(_records || []) : request('/api/review')
  },

  getReviewHub(): Promise<ApiRes<ReviewHub>> {
    return isMock ? mockService.getReviewHub() : request('/api/review/hub')
  },

  signIn(): Promise<ApiRes<{ points: number; streak: number }>> {
    return isMock ? mockService.signIn() : request('/api/signin', { method: 'POST' })
  },

  getPointsLog(): Promise<ApiRes<PointsLog[]>> {
    return isMock ? mockService.getPointsLog() : request('/api/points/log')
  },

  getPoints(): Promise<ApiRes<number>> {
    return isMock ? mockService.getPoints() : request('/api/points')
  },

  getRankList(type: RankType): Promise<ApiRes<RankItem[]>> {
    return isMock ? mockService.getRankList(type) : request(`/api/rank?type=${type}`)
  },

  completeQuiz(data: {
    articleId?: string
    mode: string
    total: number
    correct: number
  }): Promise<ApiRes<QuizCompleteResult>> {
    return isMock
      ? mockService.completeQuiz(data)
      : request('/api/quiz/complete', { method: 'POST', data })
  },

  getQuizRank(articleId?: string, mode = 'article'): Promise<ApiRes<QuizRankItem[]>> {
    const qs = new URLSearchParams({ mode })
    if (articleId) qs.set('articleId', articleId)
    return isMock
      ? mockService.getQuizRank(articleId, mode)
      : request(`/api/quiz/rank?${qs.toString()}`)
  },

  markArticleRead(articleId: string): Promise<ApiRes<{ points: number }>> {
    return isMock
      ? mockService.markArticleRead(articleId)
      : request(`/api/articles/${articleId}/read`, { method: 'POST' })
  },

  completeReview(articleId: string): Promise<ApiRes<void>> {
    return isMock
      ? mockService.completeReview(articleId)
      : request('/api/review/complete', { method: 'POST', data: { articleId } })
  },

  submitFeedback(content: string): Promise<ApiRes<{ adopted: boolean }>> {
    return isMock
      ? mockService.submitFeedback(content)
      : request('/api/feedback', { method: 'POST', data: { content } })
  },

  // ===== 每日学习清单 =====

  getTodayPlan(): Promise<ApiRes<DayPlan>> {
    return isMock ? mockService.getTodayPlan() : request('/api/plan/today')
  },

  getDayPlan(date: string): Promise<ApiRes<DayPlan>> {
    return isMock ? mockService.getDayPlan(date) : request(`/api/plan/day/${date}`)
  },

  getWeekPlan(): Promise<ApiRes<DayPlan[]>> {
    return isMock ? mockService.getWeekPlan() : request('/api/plan/week')
  },

  updatePlanTask(
    taskId: string,
    data: { status?: string; actualMinutes?: number; note?: string },
  ): Promise<ApiRes<PlanTask>> {
    return isMock
      ? mockService.updatePlanTask(taskId, data)
      : request(`/api/plan/task/${taskId}`, { method: 'PUT', data })
  },

  addPlanTask(data: {
    planDate: string
    timeSlot?: string
    subject?: string
    content: string
    expectedMinutes?: number
  }): Promise<ApiRes<PlanTask>> {
    return isMock ? mockService.addPlanTask(data) : request('/api/plan/task', { method: 'POST', data })
  },

  deletePlanTask(taskId: string): Promise<ApiRes<{ ok: boolean }>> {
    return isMock
      ? mockService.deletePlanTask(taskId)
      : request(`/api/plan/task/${taskId}`, { method: 'DELETE' })
  },

  upsertReview(data: {
    reviewDate: string
    completion?: number
    totalMinutes?: number
    weakPoint?: string
    tomorrowFocus?: string
    mood?: string
    note?: string
  }): Promise<ApiRes<DailyReview>> {
    return isMock
      ? mockService.upsertReview(data)
      : request('/api/plan/review', { method: 'POST', data })
  },

  // ===== 知识框架 =====

  getKnowledgeTrees(): Promise<ApiRes<KnowledgeTree[]>> {
    return isMock ? mockService.getKnowledgeTrees() : request('/api/knowledge/trees')
  },

  getKnowledgeTree(treeKey: string): Promise<ApiRes<KnowledgeTree>> {
    return isMock
      ? mockService.getKnowledgeTree(treeKey)
      : request(`/api/knowledge/tree/${treeKey}`)
  },

  syncKnowledge(treeKey?: string): Promise<ApiRes<Record<string, number>>> {
    return isMock
      ? mockService.syncKnowledge()
      : request(`/api/knowledge/sync${treeKey ? `?tree_key=${treeKey}` : ''}`, { method: 'POST' })
  },

  updateKnowledgeNode(
    id: string,
    data: { myNote?: string; isStarred?: boolean; content?: string },
  ): Promise<ApiRes<KnowledgeNode>> {
    return isMock
      ? mockService.updateKnowledgeNode(id, data)
      : request(`/api/knowledge/node/${id}`, { method: 'PUT', data })
  },

  getKnowledgeReviewDue(): Promise<ApiRes<KnowledgeReviewDue>> {
    return isMock ? mockService.getKnowledgeReviewDue() : request('/api/knowledge/review/due')
  },

  createKnowledgeReviewSession(count = 5): Promise<ApiRes<KnowledgeReviewSession>> {
    return isMock
      ? mockService.createKnowledgeReviewSession(count)
      : request('/api/knowledge/review/session', { method: 'POST', data: { count } })
  },

  answerKnowledgeReview(
    nodeId: string,
    result: KnowledgeReviewResult,
  ): Promise<ApiRes<KnowledgeReviewAnswer>> {
    return isMock
      ? mockService.answerKnowledgeReview(nodeId, result)
      : request('/api/knowledge/review/answer', { method: 'POST', data: { nodeId, result } })
  },

  // ===== 手动错题 =====

  listManualWrongs(
    subject?: string,
    mastered?: boolean,
    status?: 'review' | 'waiting' | 'all',
  ): Promise<ApiRes<ManualWrong[]>> {
    const qs = new URLSearchParams()
    if (subject) qs.set('subject', subject)
    if (mastered !== undefined) qs.set('mastered', String(mastered))
    if (status) qs.set('status', status)
    const q = qs.toString()
    return isMock
      ? mockService.listManualWrongs()
      : request(`/api/manual-wrong${q ? `?${q}` : ''}`)
  },

  reviewManualWrong(id: string, result: 'good' | 'again' = 'good'): Promise<ApiRes<ManualWrong>> {
    return isMock
      ? mockService.updateManualWrong(id, { reviewCount: 1 })
      : request(`/api/manual-wrong/${id}/review?result=${result}`, { method: 'POST' })
  },

  createManualWrong(data: {
    subject?: string
    questionType?: string
    stem?: string
    options?: string
    myAnswer?: string
    correctAnswer?: string
    analysis?: string
    wrongReason?: string
    note?: string
    source?: string
    images?: string[]
    knowledgeNodeId?: string | null
    knowledgeTreeKey?: string
    knowledgePath?: string
  }): Promise<ApiRes<ManualWrong>> {
    return isMock
      ? mockService.createManualWrong(data)
      : request('/api/manual-wrong', { method: 'POST', data })
  },

  updateManualWrong(
    id: string,
    data: {
      subject?: string
      questionType?: string
      stem?: string
      options?: string
      myAnswer?: string
      correctAnswer?: string
      analysis?: string
      wrongReason?: string
      note?: string
      mastered?: boolean
      reviewCount?: number
      images?: string[]
      knowledgeNodeId?: string | null
      knowledgeTreeKey?: string
      knowledgePath?: string
    },
  ): Promise<ApiRes<ManualWrong>> {
    return isMock
      ? mockService.updateManualWrong(id, data)
      : request(`/api/manual-wrong/${id}`, { method: 'PUT', data })
  },

  deleteManualWrong(id: string): Promise<ApiRes<{ ok: boolean }>> {
    return isMock
      ? mockService.deleteManualWrong(id)
      : request(`/api/manual-wrong/${id}`, { method: 'DELETE' })
  },

  uploadWrongImage(filePath: string, file?: File): Promise<ApiRes<{ url: string }>> {
    if (isMock) {
      return Promise.resolve({ code: 0, data: { url: filePath }, message: 'mock' })
    }
    return uploadFile<{ url: string }>(`${BASE_URL}/api/manual-wrong/upload`, filePath, { file })
  },

  // ===== 真题/题库 =====

  listExamPapers(params?: { examType?: string; subject?: string; year?: number }): Promise<ApiRes<ExamPaper[]>> {
    if (isMock) return mockService.listExamPapers()
    const qs = new URLSearchParams()
    if (params?.examType) qs.set('exam_type', params.examType)
    if (params?.subject) qs.set('subject', params.subject)
    if (params?.year) qs.set('year', String(params.year))
    const q = qs.toString()
    return request(`/api/exam/papers${q ? `?${q}` : ''}`)
  },

  getExamPaperDetail(paperId: string): Promise<ApiRes<ExamPaperDetail>> {
    return isMock
      ? mockService.getExamPaperDetail(paperId)
      : request(`/api/exam/paper/${paperId}`)
  },

  startExam(paperId: string): Promise<ApiRes<ExamStartResult>> {
    return isMock
      ? mockService.startExam(paperId)
      : request(`/api/exam/start/${paperId}`, { method: 'POST' })
  },

  submitExamAnswer(attemptId: string, data: { questionId: string; answer: string | string[]; timeUsedSec?: number; marked?: boolean }): Promise<ApiRes<{ ok: boolean }>> {
    return isMock
      ? mockService.submitExamAnswer(attemptId, data)
      : request(`/api/exam/answer?attempt_id=${attemptId}`, { method: 'POST', data })
  },

  submitExam(attemptId: string): Promise<ApiRes<ExamAttemptDetail>> {
    return isMock
      ? mockService.submitExam(attemptId)
      : request(`/api/exam/submit?attempt_id=${attemptId}`, { method: 'POST' })
  },

  listExamAttempts(paperId?: string): Promise<ApiRes<ExamAttempt[]>> {
    if (isMock) return mockService.listExamAttempts(paperId)
    const q = paperId ? `?paper_id=${paperId}` : ''
    return request(`/api/exam/attempts${q}`)
  },

  getExamAttemptDetail(attemptId: string): Promise<ApiRes<ExamAttemptDetail>> {
    return isMock
      ? mockService.getExamAttemptDetail(attemptId)
      : request(`/api/exam/attempt/${attemptId}`)
  },

  // ===== 英语学习 =====

  getRmrbMeta(): Promise<ApiRes<ShenlunMeta>> {
    return isMock ? mockService.getRmrbMeta() : request('/api/rmrb/meta')
  },

  createRmrbSkeletonTemplate(data: {
    name: string
    description?: string
    mode?: string
    structure?: ShenlunSkeletonStructure
    sortOrder?: number
    isEnabled?: boolean
  }): Promise<ApiRes<ShenlunSkeletonTemplate>> {
    return isMock
      ? mockService.createRmrbSkeletonTemplate(data)
      : request('/api/rmrb/skeleton-templates', { method: 'POST', data })
  },

  createRmrbTermCategory(data: {
    name: string
    kind?: 'term' | 'verb' | string
    sortOrder?: number
    isEnabled?: boolean
  }): Promise<ApiRes<ShenlunTermCategory>> {
    return isMock
      ? mockService.createRmrbTermCategory(data)
      : request('/api/rmrb/term-categories', { method: 'POST', data })
  },

  getRmrbStats(): Promise<ApiRes<ShenlunStats>> {
    return isMock ? mockService.getRmrbStats() : request('/api/rmrb/stats')
  },

  listRmrbArticles(tag?: string): Promise<ApiRes<RmrbArticle[]>> {
    if (isMock) return mockService.listRmrbArticles(tag)
    const q = tag ? `?tag=${encodeURIComponent(tag)}` : ''
    return request(`/api/rmrb/articles${q}`)
  },

  getRmrbArticle(id: string): Promise<ApiRes<RmrbArticle>> {
    return isMock ? mockService.getRmrbArticle(id) : request(`/api/rmrb/articles/${id}`)
  },

  listRmrbMines(): Promise<ApiRes<ShenlunMineLog[]>> {
    return isMock ? mockService.listRmrbMines() : request('/api/rmrb/mines')
  },

  getRmrbMine(id: string): Promise<ApiRes<ShenlunMineLog>> {
    return isMock ? mockService.getRmrbMine(id) : request(`/api/rmrb/mines/${id}`)
  },

  getRmrbMineByDate(date: string): Promise<ApiRes<ShenlunMineLog>> {
    return isMock ? mockService.getRmrbMineByDate(date) : request(`/api/rmrb/mines/by-date/${date}`)
  },

  upsertRmrbMine(data: {
    mineDate?: string
    articleId?: string | null
    articleTitle?: string
    sourceExcerpt?: string
    argumentChain?: string
    templateSentence?: string
    terms?: Array<ShenlunMineTermItem | string>
    quotes?: ShenlunQuoteItem[]
    verbs?: ShenlunVerbItem[]
    argument?: ShenlunArgumentSkeleton
    templates?: ShenlunTemplateItem[]
  }): Promise<ApiRes<ShenlunMineLog>> {
    return isMock ? mockService.upsertRmrbMine(data) : request('/api/rmrb/mines', { method: 'POST', data })
  },

  updateRmrbMine(id: string, data: Partial<{
    articleId: string | null
    articleTitle: string
    sourceExcerpt: string
    argumentChain: string
    templateSentence: string
    terms: Array<ShenlunMineTermItem | string>
    quotes: ShenlunQuoteItem[]
    verbs: ShenlunVerbItem[]
    argument: ShenlunArgumentSkeleton
    templates: ShenlunTemplateItem[]
  }>): Promise<ApiRes<ShenlunMineLog>> {
    return isMock
      ? mockService.updateRmrbMine(id, data)
      : request(`/api/rmrb/mines/${id}`, { method: 'PUT', data })
  },

  deleteRmrbMine(id: string): Promise<ApiRes<{ ok: boolean }>> {
    return isMock
      ? mockService.deleteRmrbMine(id)
      : request(`/api/rmrb/mines/${id}`, { method: 'DELETE' })
  },

  listRmrbTerms(status?: 'learning' | 'mastered', category?: string): Promise<ApiRes<ShenlunNormTerm[]>> {
    if (isMock) return mockService.listRmrbTerms()
    const qs = new URLSearchParams()
    if (status) qs.set('status', status)
    if (category) qs.set('category', category)
    const q = qs.toString() ? `?${qs}` : ''
    return request(`/api/rmrb/terms${q}`)
  },

  addRmrbTerm(data: {
    term: string
    category?: string
    usageNote?: string
    sourceTitle?: string
    exampleSentence?: string
    articleId?: string | null
  }): Promise<ApiRes<ShenlunNormTerm>> {
    return isMock ? mockService.addRmrbTerm(data) : request('/api/rmrb/terms', { method: 'POST', data })
  },

  updateRmrbTerm(id: string, data: Partial<{
    category: string
    usageNote: string
    exampleSentence: string
    familiarity: number
    mastered: boolean
    sourceTitle: string
  }>): Promise<ApiRes<ShenlunNormTerm>> {
    return isMock
      ? mockService.updateRmrbTerm(id, data)
      : request(`/api/rmrb/terms/${id}`, { method: 'PUT', data })
  },

  deleteRmrbTerm(id: string): Promise<ApiRes<{ ok: boolean }>> {
    return isMock
      ? mockService.deleteRmrbTerm(id)
      : request(`/api/rmrb/terms/${id}`, { method: 'DELETE' })
  },

  listRmrbDrills(drillType?: 'sentence' | 'imitate' | 'oral'): Promise<ApiRes<ShenlunDrillLog[]>> {
    if (isMock) return mockService.listRmrbDrills()
    const q = drillType ? `?drill_type=${drillType}` : ''
    return request(`/api/rmrb/drills${q}`)
  },

  addRmrbDrill(data: {
    drillType: 'sentence' | 'imitate' | 'oral'
    content: string
    prompt?: string
    refMineId?: string | null
    refTermIds?: string[]
  }): Promise<ApiRes<ShenlunDrillLog>> {
    return isMock ? mockService.addRmrbDrill(data) : request('/api/rmrb/drills', { method: 'POST', data })
  },

  // ===== 知行足迹 =====

  getGrowthOverview(): Promise<ApiRes<GrowthOverview>> {
    return isMock ? mockService.getGrowthOverview() : request('/api/growth/overview')
  },

  // ===== 健康模块 =====

  getCorpusStats(): Promise<ApiRes<CorpusStats>> {
    return isMock ? mockService.getCorpusStats() : request('/api/corpus/stats')
  },

  listCorpusItems(status?: string): Promise<ApiRes<CorpusItem[]>> {
    if (isMock) return mockService.listCorpusItems(status)
    const q = status ? `?status=${encodeURIComponent(status)}` : ''
    return request(`/api/corpus/items${q}`)
  },

  getCorpusItem(id: string): Promise<ApiRes<CorpusItem>> {
    return isMock ? mockService.getCorpusItem(id) : request(`/api/corpus/items/${id}`)
  },

  createCorpusItem(data: {
    original: string
    kind?: string
    sourceType?: string
    sourceTitle?: string
    tags?: string[]
    plainNote?: string
    rewrite?: string
    practice?: string
    knowledgeNodeId?: string | null
    knowledgeTreeKey?: string
    knowledgePath?: string
  }): Promise<ApiRes<CorpusItem>> {
    return isMock
      ? mockService.createCorpusItem(data)
      : request('/api/corpus/items', { method: 'POST', data })
  },

  updateCorpusItem(
    id: string,
    data: Partial<{
      original: string
      kind: string
      sourceType: string
      sourceTitle: string
      tags: string[]
      plainNote: string
      rewrite: string
      practice: string
      markUsed: boolean
      knowledgeNodeId: string | null
      knowledgeTreeKey: string
      knowledgePath: string
    }>,
  ): Promise<ApiRes<CorpusItem>> {
    return isMock
      ? mockService.updateCorpusItem(id, data)
      : request(`/api/corpus/items/${id}`, { method: 'PUT', data })
  },

  deleteCorpusItem(id: string): Promise<ApiRes<{ ok: boolean }>> {
    return isMock
      ? mockService.deleteCorpusItem(id)
      : request(`/api/corpus/items/${id}`, { method: 'DELETE' })
  },

  promoteCorpusToTerm(id: string): Promise<ApiRes<CorpusItem>> {
    return isMock
      ? mockService.promoteCorpusToTerm(id)
      : request(`/api/corpus/items/${id}/promote-term`, { method: 'POST' })
  },

  // ===== 财富 / 投资大脑 =====

  getEventHub(): Promise<ApiRes<EventHub>> {
    return isMock ? mockService.getEventHub() : request('/api/events/hub')
  },

  listEvents(params?: {
    treeKey?: string
    path?: string
    unlinked?: boolean
  }): Promise<ApiRes<EventImpression[]>> {
    if (isMock) return mockService.listEvents(params)
    const qs = new URLSearchParams()
    if (params?.treeKey) qs.set('treeKey', params.treeKey)
    if (params?.path) qs.set('path', params.path)
    if (params?.unlinked) qs.set('unlinked', 'true')
    const q = qs.toString()
    return request(`/api/events${q ? `?${q}` : ''}`)
  },

  getEvent(id: string): Promise<ApiRes<EventImpression>> {
    return isMock ? mockService.getEvent(id) : request(`/api/events/${id}`)
  },

  createEvent(data: {
    title: string
    eventDate?: string
    place?: string
    coreContent?: string
    note?: string
    knowledgeNodeId?: string | null
    knowledgeTreeKey?: string
    knowledgePath?: string
  }): Promise<ApiRes<EventImpression>> {
    return isMock
      ? mockService.createEvent(data)
      : request('/api/events', { method: 'POST', data })
  },

  updateEvent(
    id: string,
    data: Partial<{
      title: string
      eventDate: string
      place: string
      coreContent: string
      note: string
      knowledgeNodeId: string | null
      knowledgeTreeKey: string
      knowledgePath: string
    }>,
  ): Promise<ApiRes<EventImpression>> {
    return isMock
      ? mockService.updateEvent(id, data)
      : request(`/api/events/${id}`, { method: 'PUT', data })
  },

  deleteEvent(id: string): Promise<ApiRes<{ ok: boolean }>> {
    return isMock
      ? mockService.deleteEvent(id)
      : request(`/api/events/${id}`, { method: 'DELETE' })
  },

  // ===== 资料分析 =====

  getZiliaoOverview(): Promise<ApiRes<ZiliaoOverview>> {
    return isMock ? mockService.getZiliaoOverview() : request('/api/ziliao/overview')
  },

  listZiliaoFormulas(): Promise<ApiRes<ZiliaoFormula[]>> {
    return isMock ? mockService.listZiliaoFormulas() : request('/api/ziliao/formulas')
  },

  getZiliaoFormula(id: string): Promise<ApiRes<ZiliaoFormula>> {
    return isMock ? mockService.getZiliaoFormula(id) : request(`/api/ziliao/formulas/${id}`)
  },

  listZiliaoTypes(): Promise<ApiRes<ZiliaoQuestionType[]>> {
    return isMock ? mockService.listZiliaoTypes() : request('/api/ziliao/types')
  },

  getZiliaoType(id: string): Promise<ApiRes<ZiliaoQuestionType>> {
    return isMock ? mockService.getZiliaoType(id) : request(`/api/ziliao/types/${id}`)
  },

  listZiliaoTricks(): Promise<ApiRes<ZiliaoTrick[]>> {
    return isMock ? mockService.listZiliaoTricks() : request('/api/ziliao/tricks')
  },

  getZiliaoTrick(id: string): Promise<ApiRes<ZiliaoTrick>> {
    return isMock ? mockService.getZiliaoTrick(id) : request(`/api/ziliao/tricks/${id}`)
  },

  listZiliaoDrillSets(typeCode?: string, includeSample?: boolean): Promise<ApiRes<ZiliaoDrillSet[]>> {
    if (isMock) return mockService.listZiliaoDrillSets(typeCode)
    const qs: string[] = []
    if (typeCode) qs.push(`typeCode=${encodeURIComponent(typeCode)}`)
    if (includeSample !== undefined) qs.push(`includeSample=${includeSample ? 'true' : 'false'}`)
    const q = qs.length ? `?${qs.join('&')}` : ''
    return request(`/api/ziliao/drill/sets${q}`)
  },

  getZiliaoDrillSet(setId: string): Promise<ApiRes<ZiliaoDrillSetDetail>> {
    return isMock
      ? mockService.getZiliaoDrillSet(setId)
      : request(`/api/ziliao/drill/set/${encodeURIComponent(setId)}`)
  },

  submitZiliaoDrill(data: {
    setId: string
    answers: { questionId: string; userAnswer: string | string[] }[]
    timeUsedSec?: number
    typeCode?: string
    saveWrongs?: boolean
  }): Promise<ApiRes<ZiliaoDrillSubmitResult>> {
    return isMock
      ? mockService.submitZiliaoDrill(data)
      : request('/api/ziliao/drill/submit', { method: 'POST', data })
  },
}

export function initUserFromMock(): {
  userInfo: UserInfo
  points: number
  signStatus: Record<string, boolean>
} {
  return {
    userInfo: mockService.getUserInfo(),
    points: mockService.getPointsState(),
    signStatus: mockService.getSignStatus(),
  }
}
