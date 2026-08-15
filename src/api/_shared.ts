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
  ExamCountdown,
  DataExport,
  DataImportResult,
} from '@/types'

export type {
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
  ExamCountdown,
  DataExport,
  DataImportResult,
}
export type { RankType } from '@/constants'
import { mockService } from '@/mock/service'
import { clearToken, getToken } from '@/utils/auth'
import { API_BASE } from '@/utils/media'

export { mockService } from '@/mock/service'
export { clearToken, getToken } from '@/utils/auth'
export { uploadFile } from '@/utils/upload'
export { API_BASE } from '@/utils/media'

/** 仅当 USE_MOCK=true 时使用 Mock */
export const isMock = typeof USE_MOCK !== 'undefined' && USE_MOCK

export const BASE_URL = API_BASE

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

export async function request<T>(
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
