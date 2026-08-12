import type {
  AnswerResult,
  ApiRes,
  Article,
  PointsLog,
  Question,
  RankItem,
  ReviewTask,
  StudyRecord,
  UserInfo,
} from '@/types'
import type { RankType } from '@/constants'
import { mockArticles, mockRankUsers } from '@/mock/articles'
import { buildQuestionBank, checkAnswer } from '@/utils/questionGenerator'
import { calcSignStreak, formatDate, generateReviewTasks } from '@/utils/memoryCurve'
import { POINTS_RULES } from '@/constants'

const questionBank = buildQuestionBank(mockArticles)

const mockCorpusItems: import('@/types').CorpusItem[] = []

function shuffle<T>(arr: T[]): T[] {
  const copy = [...arr]
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy
}

/** 模拟延迟 */
const delay = (ms = 300) => new Promise((r) => setTimeout(r, ms))

const mockZiliaoMaterial =
  '2023年，某市新能源汽车产量为 48 万辆，同比增长 25%；其中纯电动汽车产量 36 万辆，同比增长 20%。同年该市汽车总产量 120 万辆，同比增长 10%。'

const mockZiliao = {
  todaySets: 0,
  todayCorrect: 0,
  todayTotal: 0,
  formulas: [
    {
      id: 'zf_mock_1',
      code: 'F001',
      name: '增长率',
      category: '增长',
      definition: '反映现期相对基期的增长快慢。',
      latex: 'r=\\dfrac{A_{1}-A_{0}}{A_{0}}',
      formulaPlain: '增长率 = (现期 − 基期) / 基期',
      scenarios: '同比增长多少、增幅是多少',
      pitfalls: '分母是基期不是现期',
      relatedTypeCodes: ['T001'],
      relatedTrickCodes: ['K001'],
      keywords: ['增长率'],
      examFreq: 5,
      sortOrder: 1,
      isPublished: true,
    },
  ] as import('@/types').ZiliaoFormula[],
  types: [
    {
      id: 'zt_mock_1',
      code: 'T001',
      name: '增长率计算',
      category: '增长',
      description: '直接求同比/环比增长率',
      ability: '定位数据 + 公式计算',
      difficulty: 2,
      examFreq: 5,
      formulaCodes: ['F001'],
      trickCodes: ['K001'],
      keywords: ['增长率'],
      sortOrder: 1,
      isPublished: true,
    },
  ] as import('@/types').ZiliaoQuestionType[],
  tricks: [
    {
      id: 'zk_mock_1',
      code: 'K001',
      name: '首数法',
      category: '直除',
      principle: '只看商的前几位数字，快速锁定选项。',
      whenToUse: '选项首位不同',
      whenNot: '选项非常接近',
      errorNote: '一般可保证首位正确',
      formulaCodes: ['F001'],
      example: '150÷998 ≈ 15%',
      sortOrder: 1,
      isPublished: true,
    },
  ] as import('@/types').ZiliaoTrick[],
  drill: {
    setId: 'ziliao_sample_paper:mockmat',
    paperId: 'ziliao_sample_paper',
    paperTitle: '资料分析专项样例（入门）',
    material: mockZiliaoMaterial,
    questions: [
      {
        id: 'eq_mock_1',
        section: '资料分析',
        sortOrder: 1,
        type: 'single',
        material: mockZiliaoMaterial,
        stem: '2023年该市新能源汽车产量比上年增长了多少万辆？',
        options: ['8.4', '9.6', '12.0', '14.4'],
        difficulty: 2,
      },
      {
        id: 'eq_mock_2',
        section: '资料分析',
        sortOrder: 2,
        type: 'single',
        material: mockZiliaoMaterial,
        stem: '2023年纯电动汽车产量占新能源汽车产量的比重约为？',
        options: ['65%', '75%', '80%', '85%'],
        difficulty: 2,
      },
    ],
  } as import('@/types').ZiliaoDrillSetDetail,
  correctMap: { eq_mock_1: 'B', eq_mock_2: 'B' } as Record<string, string>,
  analysisMap: {
    eq_mock_1: '基期=48/1.25=38.4，增长量=9.6。选 B。',
    eq_mock_2: '36/48=75%。选 B。',
  } as Record<string, string>,
}

/** 内存态 Mock 存储 */
const mockState = {
  points: 120,
  pointsLogs: [] as PointsLog[],
  signStatus: {} as Record<string, boolean>,
  readArticles: new Set<string>(),
  studyRecords: [] as StudyRecord[],
  sectionReadMap: {} as Record<string, string[]>,
  wrongQuestions: new Map<string, { question: Question; wrongCount: number; lastWrongAt: string; userAnswer?: string | string[] }>(),
  quizAttempts: [] as Array<{
    userId: string
    articleId?: string
    mode: string
    total: number
    correct: number
    accuracy: number
  }>,
  userInfo: {
    id: 'self',
    nickname: '知行学员',
    avatar: '',
    email: '',
    phone: '',
    isMember: false,
  } as UserInfo,
  events: null as import('@/types').EventImpression[] | null,
  countdown: null as import('@/types').ExamCountdown | null,
  manualWrongs: [] as import('@/types').ManualWrong[],
  planTasksByDate: {} as Record<string, import('@/types').PlanTask[]>,
  planReviewsByDate: {} as Record<string, import('@/types').DailyReview>,
}

function ok<T>(data: T, message = 'success'): ApiRes<T> {
  return { code: 0, data, message }
}

const mockRmrb = {
  mines: [] as import('@/types').ShenlunMineLog[],
  terms: [] as import('@/types').ShenlunNormTerm[],
  drills: [] as import('@/types').ShenlunDrillLog[],
}

function addPointsLog(amount: number, source: string, description: string, type: 'income' | 'expense' = 'income') {
  mockState.points += type === 'income' ? amount : -amount
  mockState.pointsLogs.unshift({
    id: `log-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    amount,
    type,
    source,
    description,
    createdAt: new Date().toISOString(),
  })
}

export const mockService = {
  async register(
    username: string,
    password: string,
    passwordConfirm?: string,
  ): Promise<ApiRes<import('@/api').AuthResult>> {
    await delay()
    if (password.length < 6) {
      return { code: 400, data: null as unknown as import('@/api').AuthResult, message: '密码至少 6 位' }
    }
    if (passwordConfirm && password !== passwordConfirm) {
      return { code: 400, data: null as unknown as import('@/api').AuthResult, message: '两次输入的密码不一致' }
    }
    mockState.userInfo = {
      id: `u-${username}`,
      username,
      nickname: username,
      avatar: '',
      email: '',
      phone: '',
      isMember: false,
    }
    const user = await this.getUserMe()
    return ok({
      access_token: 'mock-token',
      token_type: 'bearer',
      user: user.data,
    })
  },

  async login(username: string, _password: string): Promise<ApiRes<import('@/api').AuthResult>> {
    await delay()
    mockState.userInfo = {
      id: `u-${username}`,
      username,
      nickname: username,
      avatar: '',
      email: '',
      phone: '',
      isMember: false,
    }
    const user = await this.getUserMe()
    return ok({
      access_token: 'mock-token',
      token_type: 'bearer',
      user: user.data,
    })
  },

  async getUserMe(): Promise<ApiRes<import('@/api').UserMeData>> {
    await delay()
    const today = formatDate()
    return ok({
      id: mockState.userInfo.id,
      username: mockState.userInfo.username,
      nickname: mockState.userInfo.nickname,
      avatar: mockState.userInfo.avatar,
      email: mockState.userInfo.email || '',
      phone: mockState.userInfo.phone || '',
      isMember: mockState.userInfo.isMember,
      points: mockState.points,
      hasSignedToday: !!mockState.signStatus[today],
      signDates: Object.keys(mockState.signStatus).filter((k) => mockState.signStatus[k]),
    })
  },

  async updateProfile(data: {
    nickname?: string
    email?: string
    phone?: string
  }): Promise<ApiRes<import('@/api').UserMeData>> {
    await delay()
    if (data.nickname !== undefined) {
      const name = data.nickname.trim()
      if (!name) return { code: 400, data: null as unknown as import('@/api').UserMeData, message: '昵称不能为空' }
      mockState.userInfo.nickname = name
    }
    if (data.email !== undefined) mockState.userInfo.email = data.email.trim()
    if (data.phone !== undefined) mockState.userInfo.phone = data.phone.trim()
    return this.getUserMe()
  },

  async changePassword(data: {
    oldPassword: string
    newPassword: string
    newPasswordConfirm: string
  }): Promise<ApiRes<{ ok: boolean }>> {
    await delay()
    if (data.newPassword.length < 6) {
      return { code: 400, data: null as unknown as { ok: boolean }, message: '密码至少 6 位' }
    }
    if (data.newPassword !== data.newPasswordConfirm) {
      return { code: 400, data: null as unknown as { ok: boolean }, message: '两次输入的新密码不一致' }
    }
    if (!data.oldPassword) {
      return { code: 400, data: null as unknown as { ok: boolean }, message: '请输入原密码' }
    }
    return ok({ ok: true })
  },

  async uploadAvatar(filePath: string): Promise<ApiRes<import('@/api').UserMeData>> {
    await delay()
    mockState.userInfo.avatar = filePath
    return this.getUserMe()
  },

  async getDailyArticles(): Promise<ApiRes<Article[]>> {
    await delay()
    const today = formatDate()
    const sorted = [...mockArticles].sort(
      (a, b) => Number(Boolean(b.isFeatured)) - Number(Boolean(a.isFeatured)),
    )
    return ok(sorted.map((a) => ({ ...a, publishDate: a.isFeatured ? a.publishDate : today })))
  },

  async getRecommendedArticles(offset = 0, limit = 5): Promise<ApiRes<import('@/types').ArticleListPage>> {
    await delay()
    const pool = [...mockArticles]
      .filter((a) => !a.isFeatured)
      .sort((a, b) => {
        const byDate = b.publishDate.localeCompare(a.publishDate)
        if (byDate) return byDate
        return String(b.id).localeCompare(String(a.id))
      })
    const items = pool.slice(offset, offset + limit)
    return ok({
      items,
      total: pool.length,
      hasMore: offset + items.length < pool.length,
    })
  },

  async getArticleDetail(id: string): Promise<ApiRes<Article | null>> {
    await delay()
    const article = mockArticles.find((a) => a.id === id)
    return ok(article || null, article ? 'success' : '文章不存在')
  },

  async getQuestions(articleId: string): Promise<ApiRes<Question[]>> {
    await delay()
    const questions = questionBank.get(articleId) || []
    return ok(questions)
  },

  async getQuizByMode(mode: string, count = 10): Promise<ApiRes<Question[]>> {
    await delay()
    const all: Question[] = []
    questionBank.forEach((qs) => all.push(...qs))
    if (!all.length) return ok([])
    if (mode === 'timeline') {
      const sortedArticles = [...mockArticles].sort((a, b) => b.publishDate.localeCompare(a.publishDate))
      const recentIds = new Set(sortedArticles.slice(0, 3).map((a) => a.id))
      const filtered = all.filter((q) => recentIds.has(q.articleId))
      const pool = filtered.length ? filtered : all
      return ok(shuffle(pool).slice(0, count))
    }
    if (mode === 'key') {
      const keyIds = new Set(mockArticles.filter((a) => (a.importance || 0) >= 4 || a.isFeatured).map((a) => a.id))
      const filtered = all.filter((q) => keyIds.has(q.articleId))
      const pool = filtered.length ? filtered : all
      return ok(shuffle(pool).slice(0, count))
    }
    return ok(shuffle(all).slice(0, count))
  },

  async submitAnswer(
    questionId: string,
    answer: string | string[],
  ): Promise<ApiRes<AnswerResult>> {
    await delay()
    let target: Question | undefined
    for (const qs of questionBank.values()) {
      target = qs.find((q) => q.id === questionId)
      if (target) break
    }
    if (!target) {
      return { code: 404, data: null as unknown as AnswerResult, message: '题目不存在' }
    }

    const correct = checkAnswer(target, answer)
    let pointsEarned = 0
    if (correct) {
      pointsEarned = POINTS_RULES.CORRECT_ANSWER
      addPointsLog(pointsEarned, '答题', `答对：${target.stem.slice(0, 20)}...`)
    } else {
      const existing = mockState.wrongQuestions.get(questionId)
      mockState.wrongQuestions.set(questionId, {
        question: target,
        wrongCount: (existing?.wrongCount || 0) + 1,
        lastWrongAt: new Date().toISOString(),
        userAnswer: answer,
      })
    }

    return ok({
      correct,
      analysis: target.analysis,
      correctAnswer: target.correctAnswer,
      pointsEarned,
    })
  },

  async getReviewTasks(records: StudyRecord[]): Promise<ApiRes<ReviewTask[]>> {
    await delay()
    const merged = records.length ? records : mockState.studyRecords
    const tasks = generateReviewTasks(merged, mockArticles)
    return ok(tasks)
  },

  async getWrongQuestions(): Promise<ApiRes<import('@/types').WrongQuestionRecord[]>> {
    await delay()
    const list = Array.from(mockState.wrongQuestions.values()).map((record) => {
      const article = mockArticles.find((a) => a.id === record.question.articleId)
      return {
        question: record.question,
        wrongCount: record.wrongCount,
        lastWrongAt: record.lastWrongAt,
        userAnswer: record.userAnswer,
        articleTitle: article?.title || '未知文章',
        tag: article?.tags[0] || '综合',
      }
    })
    return ok(list)
  },

  async redoWrongQuestion(
    questionId: string,
    answer: string | string[],
  ): Promise<ApiRes<AnswerResult>> {
    await delay()
    const item = mockState.wrongQuestions.get(questionId)
    if (!item) {
      return { code: 404, data: null as unknown as AnswerResult, message: '题目不存在' }
    }
    const correct = checkAnswer(item.question, answer)
    let pointsEarned = 0
    if (correct) {
      mockState.wrongQuestions.delete(questionId)
      pointsEarned = POINTS_RULES.WRONG_REVIEW
      addPointsLog(pointsEarned, '复习', '错题复习答对')
    }
    return ok({
      correct,
      analysis: item.question.analysis,
      correctAnswer: item.question.correctAnswer,
      pointsEarned,
    })
  },

  async removeWrongQuestion(questionId: string): Promise<ApiRes<null>> {
    await delay()
    if (!mockState.wrongQuestions.has(questionId)) {
      return { code: 404, data: null, message: '错题记录不存在' }
    }
    mockState.wrongQuestions.delete(questionId)
    return ok(null)
  },

  async getStudyRecords(): Promise<ApiRes<StudyRecord[]>> {
    await delay()
    return ok(mockState.studyRecords)
  },

  async getSectionReads(): Promise<ApiRes<Record<string, string[]>>> {
    await delay()
    return ok(mockState.sectionReadMap)
  },

  async markSectionRead(articleId: string, sectionId: string): Promise<ApiRes<null>> {
    await delay()
    const list = mockState.sectionReadMap[articleId] || []
    if (!list.includes(sectionId)) {
      mockState.sectionReadMap[articleId] = [...list, sectionId]
    }
    return ok(null)
  },

  async signIn(): Promise<ApiRes<{ points: number; streak: number }>> {
    await delay()
    const today = formatDate()
    if (mockState.signStatus[today]) {
      return { code: 400, data: { points: 0, streak: 0 }, message: '今日已签到' }
    }
    mockState.signStatus[today] = true
    const streak = calcSignStreak(mockState.signStatus, today)
    let points = POINTS_RULES.SIGN_BASE
    if (streak >= 7 && streak % 7 === 0) {
      points += POINTS_RULES.SIGN_STREAK_BONUS
    }
    addPointsLog(points, '签到', `第${streak}天连续签到`)
    return ok({ points, streak })
  },

  async getPointsLog(): Promise<ApiRes<PointsLog[]>> {
    await delay()
    return ok(mockState.pointsLogs)
  },

  async getPoints(): Promise<ApiRes<number>> {
    await delay()
    return ok(mockState.points)
  },

  async getRankList(type: RankType): Promise<ApiRes<RankItem[]>> {
    await delay()
    const factor = type === 'daily' ? 0.1 : type === 'weekly' ? 0.3 : type === 'monthly' ? 0.6 : 1
    const list = mockRankUsers
      .map((u, i) => ({
        rank: i + 1,
        ...u,
        score: u.userId === 'self' ? mockState.points : Math.round(u.score * factor),
        isSelf: u.userId === 'self',
      }))
      .sort((a, b) => b.score - a.score)
      .map((item, i) => ({ ...item, rank: i + 1 }))

    return ok(list)
  },

  async completeQuiz(data: {
    articleId?: string
    mode: string
    total: number
    correct: number
  }): Promise<ApiRes<import('@/types').QuizCompleteResult>> {
    await delay()
    const accuracy = data.total > 0 ? Math.round((data.correct / data.total) * 100) : 0
    mockState.quizAttempts.push({
      userId: 'self',
      articleId: data.articleId,
      mode: data.mode,
      total: data.total,
      correct: data.correct,
      accuracy,
    })
    const same = mockState.quizAttempts.filter(
      (a) => a.articleId === data.articleId && a.mode === data.mode,
    )
    const bestByUser = new Map<string, number>()
    same.forEach((a) => {
      const prev = bestByUser.get(a.userId) ?? 0
      if (a.accuracy > prev) bestByUser.set(a.userId, a.accuracy)
    })
    const sorted = [...bestByUser.entries()].sort((a, b) => b[1] - a[1])
    const rank = sorted.findIndex(([uid]) => uid === 'self') + 1 || sorted.length + 1
    const prevBest = Math.max(
      0,
      ...same.filter((a) => a.userId === 'self').map((a) => a.accuracy),
    )
    return ok({
      accuracy,
      rank: rank || 1,
      totalParticipants: bestByUser.size || 1,
      bestAccuracy: prevBest,
    })
  },

  async getQuizRank(
    articleId?: string,
    mode = 'article',
  ): Promise<ApiRes<import('@/types').QuizRankItem[]>> {
    await delay()
    const same = mockState.quizAttempts.filter(
      (a) => a.articleId === articleId && a.mode === mode,
    )
    const bestByUser = new Map<string, (typeof same)[0]>()
    same.forEach((a) => {
      const prev = bestByUser.get(a.userId)
      if (!prev || a.accuracy > prev.accuracy) bestByUser.set(a.userId, a)
    })
    const list = [...bestByUser.values()]
      .sort((a, b) => b.accuracy - a.accuracy || b.correct - a.correct)
      .slice(0, 20)
      .map((a, i) => ({
        rank: i + 1,
        userId: a.userId,
        nickname: a.userId === 'self' ? mockState.userInfo.nickname : `学员${i + 1}`,
        avatar: '',
        accuracy: a.accuracy,
        correctCount: a.correct,
        totalCount: a.total,
        isSelf: a.userId === 'self',
      }))
    return ok(list)
  },

  async markArticleRead(articleId: string): Promise<ApiRes<{ points: number }>> {
    await delay()
    if (mockState.readArticles.has(articleId)) {
      return ok({ points: 0 })
    }
    mockState.readArticles.add(articleId)
    const existing = mockState.studyRecords.find((r) => r.articleId === articleId)
    if (!existing) {
      mockState.studyRecords.push({
        articleId,
        studyDate: formatDate(),
        reviewCount: 0,
        mastered: false,
      })
    }
    addPointsLog(POINTS_RULES.READ_ARTICLE, '阅读', '完成文章阅读')
    return ok({ points: POINTS_RULES.READ_ARTICLE })
  },

  async completeReview(articleId: string): Promise<ApiRes<void>> {
    await delay()
    const record = mockState.studyRecords.find((r) => r.articleId === articleId)
    if (record) {
      record.reviewCount++
      record.lastReviewDate = formatDate()
      if (record.reviewCount >= 6) record.mastered = true
    }
    return ok(undefined as void)
  },



  async submitFeedback(_content: string): Promise<ApiRes<{ adopted: boolean }>> {
    await delay(500)
    const adopted = Math.random() > 0.5
    if (adopted) {
      addPointsLog(POINTS_RULES.FEEDBACK_ADOPTED, '反馈', '纠错反馈被采纳')
    }
    return ok({ adopted })
  },

  // ===== 每日学习清单（mock） =====
  async getTodayPlan(): Promise<ApiRes<import('@/types').DayPlan>> {
    await delay(200)
    return this.getDayPlan(formatDate())
  },
  async getDayPlan(date: string): Promise<ApiRes<import('@/types').DayPlan>> {
    await delay(200)
    const isWeekend = [0, 6].includes(new Date(date).getDay())
    if (!mockState.planTasksByDate[date]) {
      const tmpl = isWeekend
        ? [
            { timeSlot: '07:30-09:00', subject: '行测', content: '行测套题模拟（第1段）', expectedMinutes: 90 },
            { timeSlot: '09:30-11:00', subject: '行测', content: '行测套题模拟（第2段）', expectedMinutes: 90 },
            { timeSlot: '11:00-12:00', subject: '行测', content: '套题对答案 + 错题录入', expectedMinutes: 60 },
            { timeSlot: '13:30-15:00', subject: '申论', content: '申论大作文 / 小题练笔', expectedMinutes: 90 },
            { timeSlot: '15:00-17:00', subject: '健身', content: '健身 / 滑板', expectedMinutes: 120 },
            { timeSlot: '17:00-18:00', subject: '英语', content: '英语口语对话练习', expectedMinutes: 60 },
            { timeSlot: '19:00-21:00', subject: '行测', content: '弱项专项 + 错题复盘', expectedMinutes: 120 },
            { timeSlot: '21:00-22:00', subject: '复盘', content: '当日/本周复盘 + 下周计划', expectedMinutes: 60 },
          ]
        : [
            { timeSlot: '06:45-07:45', subject: '行测', content: '晨间行测刷题', expectedMinutes: 35 },
            { timeSlot: '08:00-08:30', subject: '英语', content: '早饭+散步：英语跟读 20min', expectedMinutes: 20 },
            { timeSlot: '12:00-12:30', subject: '阅读', content: '自由阅读（史记）', expectedMinutes: 30 },
            { timeSlot: '12:30-13:00', subject: '休息', content: '午休', expectedMinutes: 30 },
            { timeSlot: '17:30-18:00', subject: '英语', content: '晚饭+散步：英语跟读 20min', expectedMinutes: 20 },
            { timeSlot: '18:00-19:00', subject: '申论', content: '申论专项', expectedMinutes: 60 },
            { timeSlot: '19:00-20:00', subject: '行测', content: '行测错题复盘', expectedMinutes: 60 },
            { timeSlot: '20:00-21:00', subject: '行测', content: '行测新题刷题', expectedMinutes: 60 },
            { timeSlot: '21:00-21:30', subject: '英语', content: '英语口语主动练习', expectedMinutes: 30 },
            { timeSlot: '21:30-22:00', subject: '复盘', content: '当日复盘 + 明日计划', expectedMinutes: 30 },
          ]
      mockState.planTasksByDate[date] = tmpl.map((t, i) => ({
        id: `pt-${date}-${i}`,
        planDate: date,
        timeSlot: t.timeSlot,
        subject: t.subject,
        content: t.content,
        priority: 3,
        expectedMinutes: t.expectedMinutes,
        actualMinutes: 0,
        status: 'pending' as const,
        sortOrder: i,
        note: '',
      }))
    }
    const tasks = mockState.planTasksByDate[date]
    const doneCount = tasks.filter((t) => t.status === 'done').length
    const totalCount = tasks.length
    const completion = totalCount ? Math.round((doneCount / totalCount) * 100) : 0
    const expectedMinutes = tasks.reduce((s, t) => s + t.expectedMinutes, 0)
    const actualMinutes = tasks.reduce((s, t) => s + (t.actualMinutes || 0), 0)
    const review = mockState.planReviewsByDate[date] || null
    return ok({ date, isWeekend, tasks, completion, doneCount, totalCount, expectedMinutes, actualMinutes, review })
  },
  async getWeekPlan(): Promise<ApiRes<import('@/types').DayPlan[]>> {
    await delay(200)
    const today = new Date()
    const out: import('@/types').DayPlan[] = []
    for (let i = 6; i >= 0; i--) {
      const d = new Date(today)
      d.setDate(d.getDate() - i)
      const r = await this.getDayPlan(d.toISOString().slice(0, 10))
      out.push(r.data)
    }
    return ok(out)
  },
  async updatePlanTask(taskId: string, data: { status?: string; actualMinutes?: number; note?: string }): Promise<ApiRes<import('@/types').PlanTask>> {
    await delay(100)
    const dateFromId = /^pt-(\d{4}-\d{2}-\d{2})-/.exec(taskId)?.[1]
    if (dateFromId && !mockState.planTasksByDate[dateFromId]) {
      await this.getDayPlan(dateFromId)
    }
    for (const date of Object.keys(mockState.planTasksByDate)) {
      const tasks = mockState.planTasksByDate[date]
      const idx = tasks.findIndex((t) => t.id === taskId)
      if (idx < 0) continue
      const cur = tasks[idx]
      const next: import('@/types').PlanTask = {
        ...cur,
        status: data.status !== undefined
          ? (data.status as 'pending' | 'done' | 'skipped')
          : cur.status,
        actualMinutes: data.actualMinutes !== undefined ? data.actualMinutes : cur.actualMinutes,
        note: data.note !== undefined ? data.note : cur.note,
      }
      tasks[idx] = next
      return ok(next)
    }
    return { code: 404, data: null as unknown as import('@/types').PlanTask, message: '任务不存在' }
  },
  async addPlanTask(data: { planDate: string; content: string; timeSlot?: string; subject?: string; expectedMinutes?: number }): Promise<ApiRes<import('@/types').PlanTask>> {
    await delay(100)
    await this.getDayPlan(data.planDate)
    const tasks = mockState.planTasksByDate[data.planDate]
    const task: import('@/types').PlanTask = {
      id: `pt-${Date.now()}`,
      planDate: data.planDate,
      timeSlot: data.timeSlot || '',
      subject: data.subject || '',
      content: data.content,
      priority: 3,
      expectedMinutes: data.expectedMinutes || 0,
      actualMinutes: 0,
      status: 'pending',
      sortOrder: tasks.length,
      note: '',
    }
    tasks.push(task)
    return ok(task)
  },
  async deletePlanTask(taskId: string): Promise<ApiRes<{ ok: boolean }>> {
    await delay(100)
    for (const date of Object.keys(mockState.planTasksByDate)) {
      const tasks = mockState.planTasksByDate[date]
      const idx = tasks.findIndex((t) => t.id === taskId)
      if (idx >= 0) {
        tasks.splice(idx, 1)
        break
      }
    }
    return ok({ ok: true })
  },
  async upsertReview(data: import('@/types').DailyReview): Promise<ApiRes<import('@/types').DailyReview>> {
    await delay(100)
    const reviewDate = data.reviewDate || formatDate()
    const prev = mockState.planReviewsByDate[reviewDate]
    const review: import('@/types').DailyReview = {
      reviewDate,
      completion: data.completion ?? prev?.completion ?? 0,
      totalMinutes: data.totalMinutes ?? prev?.totalMinutes ?? 0,
      weakPoint: data.weakPoint ?? prev?.weakPoint ?? '',
      tomorrowFocus: data.tomorrowFocus ?? prev?.tomorrowFocus ?? '',
      mood: (data.mood ?? prev?.mood ?? '') as import('@/types').DailyReview['mood'],
      note: data.note ?? prev?.note ?? '',
    }
    mockState.planReviewsByDate[reviewDate] = review
    return ok(review)
  },

  // ===== 知识框架（mock，简单返回内置树） =====
  async getKnowledgeTrees(): Promise<ApiRes<import('@/types').KnowledgeTree[]>> {
    await delay(200)
    return ok([
      { treeKey: '申论', title: '申论', nodes: [
        { id: 'k1', treeKey: '申论', parentId: null, title: '提出对策题', content: '', depth: 0, sortOrder: 0, path: '申论/提出对策题', children: [
          { id: 'k1-1', treeKey: '申论', parentId: 'k1', title: '单一型对策', content: '仅提出解决措施', depth: 1, sortOrder: 0, path: '申论/提出对策题/单一型对策', children: null },
          { id: 'k1-2', treeKey: '申论', parentId: 'k1', title: '复合型对策', content: '先概括问题或原因，再提出对策', depth: 1, sortOrder: 1, path: '申论/提出对策题/复合型对策', children: null },
        ] },
        { id: 'k2', treeKey: '申论', parentId: null, title: '归纳概括题', content: '', depth: 0, sortOrder: 1, path: '申论/归纳概括题', children: null },
      ] },
    ])
  },
  async getKnowledgeTree(treeKey: string): Promise<ApiRes<import('@/types').KnowledgeTree>> {
    const r = await this.getKnowledgeTrees()
    const t = r.data?.find((x) => x.treeKey === treeKey)
    return t ? ok(t) : { code: 404, data: null as unknown as import('@/types').KnowledgeTree, message: '不存在' }
  },
  async syncKnowledge(): Promise<ApiRes<Record<string, number>>> {
    await delay(200)
    return ok({ '申论': 514, '判断推理': 350 })
  },
  async updateKnowledgeNode(id: string, data: { myNote?: string; isStarred?: boolean }): Promise<ApiRes<import('@/types').KnowledgeNode>> {
    await delay(100)
    return ok({
      id,
      treeKey: '申论',
      parentId: null,
      title: '测试',
      content: '',
      myNote: data.myNote || '',
      isStarred: data.isStarred || false,
      depth: 0,
      sortOrder: 0,
      path: '测试',
      children: null,
    })
  },

  async getReviewHub(): Promise<ApiRes<import('@/types').ReviewHub>> {
    await delay(100)
    const manualWrongCount = mockState.manualWrongs.filter((w) => !w.mastered).length
    return ok({
      knowledgeDueCount: 2,
      articleReviewCount: 0,
      corpusInboxCount: 0,
      articleWrongCount: 1,
      manualWrongCount,
      wrongReviewCount: 1,
      wrongWaitingCount: 2,
      wrongRecommendCount: 1,
      totalCount: 3 + manualWrongCount,
    })
  },

  async getKnowledgeReviewDue(): Promise<ApiRes<import('@/types').KnowledgeReviewDue>> {
    await delay(100)
    return ok({
      dueCount: 2,
      candidates: [
        {
          id: 'k1-1',
          title: '单一型对策',
          path: '申论/提出对策题/单一型对策',
          treeKey: '申论',
          content: '仅提出解决措施',
          myNote: '',
          masteryLevel: 'new',
          hint: '仅提出解决…',
        },
      ],
    })
  },

  async createKnowledgeReviewSession(count = 5): Promise<ApiRes<import('@/types').KnowledgeReviewSession>> {
    await delay(100)
    const due = await this.getKnowledgeReviewDue()
    return ok({ cards: (due.data?.candidates || []).slice(0, count) })
  },

  async answerKnowledgeReview(
    nodeId: string,
    result: import('@/types').KnowledgeReviewResult,
  ): Promise<ApiRes<import('@/types').KnowledgeReviewAnswer>> {
    await delay(100)
    const mastery =
      result === 'easy' ? 'mastered' : result === 'good' ? 'familiar' : 'learning'
    return ok({
      id: nodeId,
      masteryLevel: mastery,
      nextReviewAt: new Date().toISOString(),
      reviewCount: 1,
      lastReviewedAt: new Date().toISOString(),
    })
  },

  // ===== 手动错题（mock） =====
  async listManualWrongs(): Promise<ApiRes<import('@/types').ManualWrong[]>> {
    await delay(200)
    return ok([...mockState.manualWrongs])
  },
  async createManualWrong(data: {
    subject?: string
    questionType?: string
    stem?: string
    options?: string
    myAnswer?: string
    correctAnswer?: string
    analysis?: string
    note?: string
    wrongReason?: string
    images?: string[]
    source?: string
    knowledgeNodeId?: string | null
    knowledgeTreeKey?: string
    knowledgePath?: string
  }): Promise<ApiRes<import('@/types').ManualWrong>> {
    await delay(200)
    const row: import('@/types').ManualWrong = {
      id: `mw-${Date.now()}`,
      subject: data.subject || '',
      questionType: data.questionType || '',
      stem: data.stem || '',
      options: data.options || '',
      myAnswer: data.myAnswer || '',
      correctAnswer: data.correctAnswer || '',
      analysis: data.analysis || '',
      wrongReason: data.wrongReason || '',
      note: data.note || '',
      images: data.images || [],
      source: (data.source as 'manual' | 'photo' | 'ocr') || 'manual',
      knowledgeNodeId: data.knowledgeNodeId || null,
      knowledgeTreeKey: data.knowledgeTreeKey || '',
      knowledgePath: data.knowledgePath || '',
      reviewCount: 0,
      mastered: false,
      lastWrongAt: new Date().toISOString(),
      createdAt: new Date().toISOString(),
    }
    mockState.manualWrongs.unshift(row)
    return ok(row)
  },
  async updateManualWrong(id: string, data: {
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
  }): Promise<ApiRes<import('@/types').ManualWrong>> {
    await delay(100)
    const idx = mockState.manualWrongs.findIndex((w) => w.id === id)
    if (idx < 0) {
      return { code: 404, data: null as unknown as import('@/types').ManualWrong, message: '不存在' }
    }
    const cur = mockState.manualWrongs[idx]
    const next: import('@/types').ManualWrong = {
      ...cur,
      ...(data.subject !== undefined ? { subject: data.subject } : {}),
      ...(data.questionType !== undefined ? { questionType: data.questionType } : {}),
      ...(data.stem !== undefined ? { stem: data.stem } : {}),
      ...(data.options !== undefined ? { options: data.options } : {}),
      ...(data.myAnswer !== undefined ? { myAnswer: data.myAnswer } : {}),
      ...(data.correctAnswer !== undefined ? { correctAnswer: data.correctAnswer } : {}),
      ...(data.analysis !== undefined ? { analysis: data.analysis } : {}),
      ...(data.wrongReason !== undefined ? { wrongReason: data.wrongReason } : {}),
      ...(data.note !== undefined ? { note: data.note } : {}),
      ...(data.mastered !== undefined ? { mastered: data.mastered } : {}),
      ...(data.reviewCount !== undefined
        ? { reviewCount: (cur.reviewCount || 0) + (data.reviewCount || 0) }
        : {}),
      ...(data.images !== undefined ? { images: data.images } : {}),
      ...(data.knowledgeNodeId !== undefined ? { knowledgeNodeId: data.knowledgeNodeId } : {}),
      ...(data.knowledgeTreeKey !== undefined ? { knowledgeTreeKey: data.knowledgeTreeKey } : {}),
      ...(data.knowledgePath !== undefined ? { knowledgePath: data.knowledgePath } : {}),
      lastWrongAt: new Date().toISOString(),
    }
    mockState.manualWrongs[idx] = next
    return ok(next)
  },
  async deleteManualWrong(id: string): Promise<ApiRes<{ ok: boolean }>> {
    await delay(100)
    const idx = mockState.manualWrongs.findIndex((w) => w.id === id)
    if (idx >= 0) mockState.manualWrongs.splice(idx, 1)
    return ok({ ok: true })
  },

  // ===== 真题/题库（mock） =====
  async listExamPapers(): Promise<ApiRes<import('@/types').ExamPaper[]>> {
    await delay(200)
    return ok([
      {
        id: 'paper-mock-1', title: '2024 国考行测地市级', examType: 'real', subject: '行测',
        year: 2024, region: '国考', level: '地市级', totalCount: 135, timeLimitMin: 120,
        tags: ['行测', '真题'], isPublished: true, isFree: true, sortOrder: 0,
        description: '2024年国家公务员考试行测地市级真题', createdAt: new Date().toISOString(),
      },
    ])
  },
  async getExamPaperDetail(paperId: string): Promise<ApiRes<import('@/types').ExamPaperDetail>> {
    await delay(200)
    return ok({
      id: paperId, title: 'mock 试卷', examType: 'real', subject: '行测',
      year: 2024, region: '国考', level: '', totalCount: 2, timeLimitMin: 60,
      tags: [], isPublished: true, isFree: true,
      description: '', sections: [
        { section: '常识判断', questions: [
          { id: 'eq1', paperId, section: '常识判断', sectionIndex: 1, sortOrder: 1, type: 'single', material: '', stem: '首都？', options: ['北京','上海','广州','深圳'], correctAnswer: '北京', analysis: '', difficulty: 3, knowledgeTags: [], isActive: true },
        ] },
      ],
    })
  },
  async startExam(paperId: string): Promise<ApiRes<import('@/types').ExamStartResult>> {
    await delay(200)
    return ok({
      attemptId: `ea-mock-${Date.now()}`, paperId, paperTitle: 'mock 试卷',
      timeLimitMin: 60, totalCount: 1, startedAt: new Date().toISOString(),
      questions: [
        { id: 'eq1', section: '常识判断', sortOrder: 1, type: 'single', material: '', stem: '首都？', options: ['北京','上海','广州','深圳'], myAnswer: '', marked: false, timeUsedSec: 0 },
      ],
    })
  },
  async submitExamAnswer(_attemptId: string, _data: { questionId: string; answer: string | string[] }): Promise<ApiRes<{ ok: boolean }>> {
    await delay(50)
    return ok({ ok: true })
  },
  async submitExam(attemptId: string): Promise<ApiRes<import('@/types').ExamAttemptDetail>> {
    await delay(200)
    return ok({
      id: attemptId, paperId: 'paper-mock-1', paperTitle: 'mock 试卷',
      startedAt: new Date().toISOString(), finishedAt: new Date().toISOString(),
      timeUsedSec: 300, totalCount: 1, answeredCount: 1, correctCount: 1, score: 1, isFinished: true,
      answers: [
        { questionId: 'eq1', section: '常识判断', sortOrder: 1, stem: '首都？', options: ['北京','上海','广州','深圳'], correctAnswer: '北京', analysis: '', userAnswer: '北京', isCorrect: true, answered: true, timeUsedSec: 30, marked: false },
      ],
      sectionStats: [{ section: '常识判断', total: 1, correct: 1, answered: 1, accuracy: 100 }],
    })
  },
  async listExamAttempts(_paperId?: string): Promise<ApiRes<import('@/types').ExamAttempt[]>> {
    await delay(200)
    return ok([])
  },
  async getExamAttemptDetail(attemptId: string): Promise<ApiRes<import('@/types').ExamAttemptDetail>> {
    return this.submitExam(attemptId)
  },

  // ===== 英语学习（mock） =====

  // ===== 人民日报 mock =====
  async getRmrbMeta(): Promise<ApiRes<import('@/types').ShenlunMeta>> {
    await delay(100)
    return ok({
      termCategories: [
        { id: 'c1', name: '问题与积弊', kind: 'term', sortOrder: 5, isEnabled: true },
        { id: 'c2', name: '治理方法与理念', kind: 'term', sortOrder: 8, isEnabled: true },
        { id: 'c3', name: '成效与目标', kind: 'term', sortOrder: 12, isEnabled: true },
        { id: 'c4', name: '其他', kind: 'term', sortOrder: 99, isEnabled: true },
      ],
      verbCategories: [
        { id: 'v1', name: '治理动作', kind: 'verb', sortOrder: 10, isEnabled: true },
        { id: 'v2', name: '分析评价', kind: 'verb', sortOrder: 20, isEnabled: true },
        { id: 'v3', name: '动词其他', kind: 'verb', sortOrder: 99, isEnabled: true },
      ],
      skeletonTemplates: [
        {
          id: 'sk1',
          name: '总分论点型',
          description: '总论点 → 分论点 → 总结',
          mode: 'points',
          structure: {
            mode: 'points',
            fields: [],
            overviewLabel: '总论点',
            pointFields: [{ key: 'title', label: '分论点', placeholder: '' }],
          },
          sortOrder: 0,
          isEnabled: true,
        },
      ],
      sentenceTypes: [
        { id: 'st1', code: 'dialectic', name: '对比转折型', tip: '', sortOrder: 0, isEnabled: true },
        { id: 'st2', code: 'quote', name: '金句型', tip: '', sortOrder: 1, isEnabled: true },
      ],
      argumentMethodPresets: [
        {
          name: '点例排比 + 类比延伸',
          scope: 'point',
          note: '点例各一句话；3个排比',
          template: '提出分论点 → 列举3个案例 → 提炼共性 → 类比延伸 → 总结',
        },
        {
          name: '总—分—分—总',
          scope: 'overview',
          note: '全文结构',
          template: '现象引题 → 总论点 → 分论点 → 总结升华',
        },
      ],
    })
  },
  async createRmrbSkeletonTemplate(data: {
    name: string
    description?: string
    mode?: string
    structure?: import('@/types').ShenlunSkeletonStructure
    sortOrder?: number
    isEnabled?: boolean
  }): Promise<ApiRes<import('@/types').ShenlunSkeletonTemplate>> {
    await delay(100)
    return ok({
      id: `sk-${Date.now()}`,
      name: data.name,
      description: data.description || '',
      mode: data.mode || 'default',
      structure: data.structure || { mode: 'default', fields: [], pointFields: [] },
      sortOrder: data.sortOrder ?? 0,
      isEnabled: data.isEnabled !== false,
    })
  },
  async createRmrbTermCategory(data: {
    name: string
    kind?: string
    sortOrder?: number
    isEnabled?: boolean
  }): Promise<ApiRes<import('@/types').ShenlunTermCategory>> {
    await delay(100)
    return ok({
      id: `cat-${Date.now()}`,
      name: data.name,
      kind: data.kind || 'term',
      sortOrder: data.sortOrder ?? 0,
      isEnabled: data.isEnabled !== false,
    })
  },
  async getRmrbStats(): Promise<ApiRes<import('@/types').ShenlunStats>> {
    await delay(100)
    return ok({
      weekMineDays: 3,
      weekMineTarget: 7,
      termCount: mockRmrb.terms.length,
      learningTermCount: mockRmrb.terms.filter((t) => !t.mastered).length,
      todayMined: mockRmrb.mines.some((m) => m.mineDate === new Date().toISOString().slice(0, 10)),
      weekDrillCount: mockRmrb.drills.length,
    })
  },
  async listRmrbArticles(tag?: string): Promise<ApiRes<import('@/types').RmrbArticle[]>> {
    await delay(100)
    const all: import('@/types').RmrbArticle[] = [
      {
        id: 'rmrb1',
        title: '示例时评：以实干开新局',
        source: '人民日报',
        publishDate: '2026-07-01',
        summary: 'Mock 文章摘要',
        content: '这是一篇用于本地 Mock 的人民日报示例正文。',
        tags: ['政绩观', '高质量发展'],
        isPublished: true,
        sortOrder: 0,
        readCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ]
    return ok(tag ? all.filter((a) => (a.tags || []).includes(tag)) : all)
  },
  async getRmrbArticle(id: string): Promise<ApiRes<import('@/types').RmrbArticle>> {
    await delay(100)
    const list = await this.listRmrbArticles()
    const hit = list.data?.find((a) => a.id === id) || list.data?.[0]
    return hit ? ok(hit) : { code: 404, data: null as unknown as import('@/types').RmrbArticle, message: 'not found' }
  },
  async listRmrbMines(): Promise<ApiRes<import('@/types').ShenlunMineLog[]>> {
    await delay(100)
    return ok([...mockRmrb.mines])
  },
  async getRmrbMine(id: string): Promise<ApiRes<import('@/types').ShenlunMineLog>> {
    await delay(100)
    const hit = mockRmrb.mines.find((m) => m.id === id)
    return hit ? ok(hit) : { code: 404, data: null as unknown as import('@/types').ShenlunMineLog, message: 'not found' }
  },
  async getRmrbMineByDate(date: string): Promise<ApiRes<import('@/types').ShenlunMineLog>> {
    await delay(100)
    const hit = mockRmrb.mines.find((m) => m.mineDate === date)
    return hit
      ? ok(hit)
      : { code: 404, data: null as unknown as import('@/types').ShenlunMineLog, message: 'not found' }
  },
  async upsertRmrbMine(data: Record<string, unknown>): Promise<ApiRes<import('@/types').ShenlunMineLog>> {
    await delay(100)
    const now = new Date().toISOString()
    const mineDate = String(data.mineDate || now.slice(0, 10))
    let row = mockRmrb.mines.find((m) => m.mineDate === mineDate)
    if (!row) {
      row = {
        id: `mine-${Date.now()}`,
        mineDate,
        articleId: (data.articleId as string) || null,
        articleTitle: String(data.articleTitle || ''),
        sourceExcerpt: String(data.sourceExcerpt || ''),
        argumentChain: String(data.argumentChain || ''),
        templateSentence: String(data.templateSentence || ''),
        terms: (data.terms as import('@/types').ShenlunMineTermItem[]) || [],
        quotes: (data.quotes as import('@/types').ShenlunQuoteItem[]) || [],
        verbs: (data.verbs as import('@/types').ShenlunVerbItem[]) || [],
        argument: (data.argument as import('@/types').ShenlunArgumentSkeleton) || {
          templateId: '',
          templateName: '',
          mode: 'default',
          overview: '',
          conclusion: '',
          fields: [],
          points: [],
        },
        templates: (data.templates as import('@/types').ShenlunTemplateItem[]) || [],
        createdAt: now,
        updatedAt: now,
      }
      mockRmrb.mines.unshift(row)
    } else {
      Object.assign(row, data, { updatedAt: now })
    }
    return ok(row)
  },
  async updateRmrbMine(id: string, data: Record<string, unknown>): Promise<ApiRes<import('@/types').ShenlunMineLog>> {
    await delay(100)
    const row = mockRmrb.mines.find((m) => m.id === id)
    if (!row) return { code: 404, data: null as unknown as import('@/types').ShenlunMineLog, message: 'not found' }
    Object.assign(row, data, { updatedAt: new Date().toISOString() })
    return ok(row)
  },
  async deleteRmrbMine(id: string): Promise<ApiRes<{ ok: boolean }>> {
    await delay(100)
    mockRmrb.mines = mockRmrb.mines.filter((m) => m.id !== id)
    return ok({ ok: true })
  },
  async listRmrbTerms(): Promise<ApiRes<import('@/types').ShenlunNormTerm[]>> {
    await delay(100)
    return ok([...mockRmrb.terms])
  },
  async addRmrbTerm(data: {
    term: string
    category?: string
    usageNote?: string
    sourceTitle?: string
    exampleSentence?: string
    articleId?: string | null
  }): Promise<ApiRes<import('@/types').ShenlunNormTerm>> {
    await delay(100)
    const row: import('@/types').ShenlunNormTerm = {
      id: `term-${Date.now()}`,
      term: data.term,
      category: data.category || 'norm',
      usageNote: data.usageNote || '',
      sourceTitle: data.sourceTitle || '',
      exampleSentence: data.exampleSentence || '',
      articleId: data.articleId ?? null,
      familiarity: 1,
      mastered: false,
      createdAt: new Date().toISOString(),
    }
    mockRmrb.terms.unshift(row)
    return ok(row)
  },
  async updateRmrbTerm(id: string, data: Record<string, unknown>): Promise<ApiRes<import('@/types').ShenlunNormTerm>> {
    await delay(100)
    const row = mockRmrb.terms.find((t) => t.id === id)
    if (!row) return { code: 404, data: null as unknown as import('@/types').ShenlunNormTerm, message: 'not found' }
    Object.assign(row, data)
    return ok(row)
  },
  async deleteRmrbTerm(id: string): Promise<ApiRes<{ ok: boolean }>> {
    await delay(100)
    mockRmrb.terms = mockRmrb.terms.filter((t) => t.id !== id)
    return ok({ ok: true })
  },
  async listRmrbDrills(): Promise<ApiRes<import('@/types').ShenlunDrillLog[]>> {
    await delay(100)
    return ok([...mockRmrb.drills])
  },
  async addRmrbDrill(data: {
    drillType: 'sentence' | 'imitate' | 'oral'
    content: string
    prompt?: string
    refMineId?: string | null
    refTermIds?: string[]
  }): Promise<ApiRes<import('@/types').ShenlunDrillLog>> {
    await delay(100)
    const row: import('@/types').ShenlunDrillLog = {
      id: `drill-${Date.now()}`,
      drillType: data.drillType,
      content: data.content,
      prompt: data.prompt || '',
      refMineId: data.refMineId ?? null,
      refTermIds: data.refTermIds || [],
      createdAt: new Date().toISOString(),
    }
    mockRmrb.drills.unshift(row)
    return ok(row)
  },

  // ===== 读书 mock =====

  // ===== 健康 mock =====

  async getGrowthOverview(): Promise<ApiRes<import('@/types').GrowthOverview>> {
    await delay(200)
    const today = new Date()
    const monday = new Date(today)
    monday.setDate(today.getDate() - ((today.getDay() + 6) % 7))
    const labels = ['一', '二', '三', '四', '五', '六', '日']
    const mins = [45, 60, 30, 90, 50, 20, 40]
    const weekBars = labels.map((label, i) => {
      const d = new Date(monday)
      d.setDate(monday.getDate() + i)
      const date = d.toISOString().slice(0, 10)
      return {
        date,
        label,
        minutes: mins[i],
        isToday: date === today.toISOString().slice(0, 10),
      }
    })
    return ok({
      signStreak: 5,
      signDays: 28,
      points: mockState.points,
      weekMinutes: mins.reduce((a, b) => a + b, 0),
      weekQuizTotal: 40,
      weekQuizCorrect: 32,
      articleReadCount: 12,
      examFinishedCount: 2,
      weekBars,
      domains: [
        { key: 'plan', name: '计划执行', percent: 70, detail: '本周 7/10 项' },
        { key: 'shenlun', name: '申论·人民日报', percent: 57, detail: '本周开采 4 天 · 词库 36' },
        { key: 'ziliao', name: '资料分析', percent: 50, detail: '今日 5/10 · 本周 3 套' },
        { key: 'wrong', name: '错题消化', percent: 40, detail: '行测掌握 4/10 · 文章错题 6' },
        { key: 'signin', name: '连续签到', percent: 83, detail: '连续 25 天' },
      ],
    })
  },

  // 音标 mock

  // ===== 记账 mock =====

  // ===== 语料本（内存） =====
  async getCorpusStats(): Promise<ApiRes<import('@/types').CorpusStats>> {
    await delay(40)
    const items = mockCorpusItems
    const counts = { inbox: 0, clarified: 0, owned: 0, used: 0 }
    items.forEach((i) => {
      const k = i.status in counts ? (i.status as keyof typeof counts) : 'inbox'
      counts[k] += 1
    })
    return ok({
      inboxCount: counts.inbox,
      clarifiedCount: counts.clarified,
      ownedCount: counts.owned,
      usedCount: counts.used,
      total: items.length,
      kinds: ['词', '专名', '成语', '诗典', '短语', '句', '结构'],
      sourceTypes: ['报纸', '视频', '播客', '书', '聊天', '其他'],
      tagPresets: ['民生', '治理', '收束', '过渡', '对比', '金句', '问题', '对策', '其他'],
    })
  },
  async listCorpusItems(status?: string): Promise<ApiRes<import('@/types').CorpusItem[]>> {
    await delay(40)
    let rows = [...mockCorpusItems]
    if (status && status !== 'all') rows = rows.filter((i) => i.status === status)
    return ok(rows)
  },
  async getCorpusItem(id: string): Promise<ApiRes<import('@/types').CorpusItem>> {
    await delay(30)
    const item = mockCorpusItems.find((i) => i.id === id)
    if (!item) return { code: 404, data: null as any, message: '不存在' }
    return ok(item)
  },
  async createCorpusItem(data: Record<string, unknown>): Promise<ApiRes<import('@/types').CorpusItem>> {
    await delay(50)
    const now = new Date().toISOString()
    const rewrite = String(data.rewrite || '')
    const practice = String(data.practice || '')
    const plainNote = String(data.plainNote || '')
    const tags = (data.tags as string[]) || []
    let status: import('@/types').CorpusStatus = 'inbox'
    if (practice.trim()) status = 'used'
    else if (rewrite.trim()) status = 'owned'
    else if (plainNote.trim() || tags.length) status = 'clarified'
    const item: import('@/types').CorpusItem = {
      id: `cps-${Date.now()}`,
      original: String(data.original || ''),
      kind: String(data.kind || '句'),
      sourceType: String(data.sourceType || '其他'),
      sourceTitle: String(data.sourceTitle || ''),
      tags,
      plainNote,
      rewrite,
      practice,
      status,
      usedCount: 0,
      promotedTermId: null,
      knowledgeNodeId: (data.knowledgeNodeId as string) || null,
      knowledgeTreeKey: String(data.knowledgeTreeKey || ''),
      knowledgePath: String(data.knowledgePath || ''),
      createdAt: now,
      updatedAt: now,
    }
    mockCorpusItems.unshift(item)
    return ok(item)
  },
  async updateCorpusItem(id: string, data: Record<string, unknown>): Promise<ApiRes<import('@/types').CorpusItem>> {
    await delay(50)
    const idx = mockCorpusItems.findIndex((i) => i.id === id)
    if (idx < 0) return { code: 404, data: null as any, message: '不存在' }
    const cur = { ...mockCorpusItems[idx], ...data, updatedAt: new Date().toISOString() } as import('@/types').CorpusItem
    if (data.markUsed) cur.usedCount = (cur.usedCount || 0) + 1
    if (cur.usedCount > 0 || (cur.practice || '').trim()) cur.status = 'used'
    else if ((cur.rewrite || '').trim()) cur.status = 'owned'
    else if ((cur.plainNote || '').trim() || (cur.tags || []).length) cur.status = 'clarified'
    else cur.status = 'inbox'
    mockCorpusItems[idx] = cur
    return ok(cur)
  },
  async deleteCorpusItem(id: string): Promise<ApiRes<{ ok: boolean }>> {
    await delay(40)
    const idx = mockCorpusItems.findIndex((i) => i.id === id)
    if (idx >= 0) mockCorpusItems.splice(idx, 1)
    return ok({ ok: true })
  },
  async promoteCorpusToTerm(id: string): Promise<ApiRes<import('@/types').CorpusItem>> {
    return this.updateCorpusItem(id, { markUsed: true, promotedTermId: `snt-mock-${id}` })
  },


  async getEventHub(): Promise<ApiRes<import('@/types').EventHub>> {
    await delay(80)
    const list = (await this.listEvents()).data || []
    const linked = list.filter((e) => e.knowledgePath || e.knowledgeTreeKey)
    return ok({
      total: list.length,
      linkedCount: linked.length,
      unlinkedCount: list.length - linked.length,
      recentCount: list.length,
      frameworkGroups: linked.length
        ? [{
            treeKey: linked[0].knowledgeTreeKey,
            path: linked[0].knowledgePath,
            label: `${linked[0].knowledgeTreeKey} / ${linked[0].knowledgePath}`,
            count: linked.length,
            items: linked,
          }]
        : [],
    })
  },

  _ensureMockEvents() {
    if (!mockState.events) {
      const now = new Date().toISOString()
      mockState.events = [
        {
          id: 'ei-demo-1',
          title: '神舟十号飞船发射成功',
          eventDate: '2013-06-11',
          place: '酒泉卫星发射中心',
          coreContent: '载人飞船发射成功，聂海胜、张晓光、王亚平执行任务；王亚平完成首次太空授课。',
          note: '可与神舟系列、载人航天工程对照记忆。',
          knowledgeNodeId: null,
          knowledgeTreeKey: '航天常识',
          knowledgePath: '神舟系列',
          createdAt: now,
          updatedAt: now,
        },
      ] as import('@/types').EventImpression[]
    }
    return mockState.events as import('@/types').EventImpression[]
  },

  async listEvents(params?: {
    treeKey?: string
    path?: string
    unlinked?: boolean
  }): Promise<ApiRes<import('@/types').EventImpression[]>> {
    await delay(80)
    let rows = [...this._ensureMockEvents()]
    if (params?.unlinked) {
      rows = rows.filter((e) => !e.knowledgePath && !e.knowledgeTreeKey)
    } else {
      if (params?.treeKey) rows = rows.filter((e) => e.knowledgeTreeKey === params.treeKey)
      if (params?.path) {
        const p = params.path
        rows = rows.filter((e) => e.knowledgePath === p || e.knowledgePath?.startsWith(`${p}/`))
      }
    }
    return ok(rows)
  },

  async getEvent(id: string): Promise<ApiRes<import('@/types').EventImpression>> {
    const hit = this._ensureMockEvents().find((e) => e.id === id)
    return hit
      ? ok(hit)
      : { code: 404, data: null as unknown as import('@/types').EventImpression, message: '不存在' }
  },

  async createEvent(data: {
    title: string
    eventDate?: string
    place?: string
    coreContent?: string
    note?: string
    knowledgeNodeId?: string | null
    knowledgeTreeKey?: string
    knowledgePath?: string
  }): Promise<ApiRes<import('@/types').EventImpression>> {
    const now = new Date().toISOString()
    const item: import('@/types').EventImpression = {
      id: `ei-${Date.now()}`,
      title: data.title,
      eventDate: data.eventDate || now.slice(0, 10),
      place: data.place || '',
      coreContent: data.coreContent || '',
      note: data.note || '',
      knowledgeNodeId: data.knowledgeNodeId || null,
      knowledgeTreeKey: data.knowledgeTreeKey || '',
      knowledgePath: data.knowledgePath || '',
      createdAt: now,
      updatedAt: now,
    }
    this._ensureMockEvents().unshift(item)
    return ok(item)
  },

  async updateEvent(id: string, data: Record<string, unknown>) {
    const list = this._ensureMockEvents()
    const idx = list.findIndex((e) => e.id === id)
    if (idx < 0) {
      return { code: 404, data: null as unknown as import('@/types').EventImpression, message: '不存在' }
    }
    list[idx] = {
      ...list[idx],
      ...data,
      updatedAt: new Date().toISOString(),
    } as import('@/types').EventImpression
    return ok(list[idx])
  },

  async deleteEvent(id: string): Promise<ApiRes<{ ok: boolean }>> {
    const list = this._ensureMockEvents()
    const idx = list.findIndex((e) => e.id === id)
    if (idx >= 0) list.splice(idx, 1)
    return ok({ ok: true })
  },

  getStudyRecords(): StudyRecord[] {
    return mockState.studyRecords
  },

  getWrongQuestionsMap() {
    return mockState.wrongQuestions
  },

  getSignStatus() {
    return mockState.signStatus
  },

  getUserInfo(): UserInfo {
    return mockState.userInfo
  },

  getPointsState(): number {
    return mockState.points
  },

  // ===== 资料分析 Mock =====

  async getZiliaoOverview(): Promise<ApiRes<import('@/types').ZiliaoOverview>> {
    await delay(100)
    return {
      code: 0,
      message: 'ok',
      data: {
        formulaCount: mockZiliao.formulas.length,
        typeCount: mockZiliao.types.length,
        trickCount: mockZiliao.tricks.length,
        drillSetCount: 1,
        todaySets: mockZiliao.todaySets,
        todayCorrect: mockZiliao.todayCorrect,
        todayTotal: mockZiliao.todayTotal,
        weekSets: mockZiliao.todaySets,
        hasRealDrill: false,
        usingSampleOnly: true,
        weakTypes: [
          {
            id: mockZiliao.types[0].id,
            code: mockZiliao.types[0].code,
            name: mockZiliao.types[0].name,
            category: mockZiliao.types[0].category,
            attemptCount: 0,
            correctCount: 0,
            totalCount: 0,
            accuracy: null,
            reason: '尚未专项练习',
          },
        ],
      },
    }
  },

  async listZiliaoFormulas(): Promise<ApiRes<import('@/types').ZiliaoFormula[]>> {
    await delay(100)
    return { code: 0, message: 'ok', data: mockZiliao.formulas }
  },

  async getZiliaoFormula(id: string): Promise<ApiRes<import('@/types').ZiliaoFormula>> {
    await delay(80)
    const item = mockZiliao.formulas.find((f) => f.id === id)
    return item
      ? { code: 0, message: 'ok', data: item }
      : { code: 404, message: '不存在', data: null as any }
  },

  async listZiliaoTypes(): Promise<ApiRes<import('@/types').ZiliaoQuestionType[]>> {
    await delay(100)
    return { code: 0, message: 'ok', data: mockZiliao.types }
  },

  async getZiliaoType(id: string): Promise<ApiRes<import('@/types').ZiliaoQuestionType>> {
    await delay(80)
    const item = mockZiliao.types.find((t) => t.id === id)
    return item
      ? { code: 0, message: 'ok', data: item }
      : { code: 404, message: '不存在', data: null as any }
  },

  async listZiliaoTricks(): Promise<ApiRes<import('@/types').ZiliaoTrick[]>> {
    await delay(100)
    return { code: 0, message: 'ok', data: mockZiliao.tricks }
  },

  async getZiliaoTrick(id: string): Promise<ApiRes<import('@/types').ZiliaoTrick>> {
    await delay(80)
    const item = mockZiliao.tricks.find((t) => t.id === id)
    return item
      ? { code: 0, message: 'ok', data: item }
      : { code: 404, message: '不存在', data: null as any }
  },

  async listZiliaoDrillSets(_typeCode?: string): Promise<ApiRes<import('@/types').ZiliaoDrillSet[]>> {
    await delay(100)
    return {
      code: 0,
      message: 'ok',
      data: [
        {
          setId: mockZiliao.drill.setId,
          paperId: mockZiliao.drill.paperId,
          paperTitle: mockZiliao.drill.paperTitle,
          materialPreview: mockZiliao.drill.material.slice(0, 80),
          questionCount: mockZiliao.drill.questions.length,
          section: '资料分析',
          typeHints: ['增长量', '比重'],
          isSample: true,
        },
      ],
    }
  },

  async getZiliaoDrillSet(setId: string): Promise<ApiRes<import('@/types').ZiliaoDrillSetDetail>> {
    await delay(100)
    if (setId !== mockZiliao.drill.setId) {
      return { code: 404, message: '不存在', data: null as any }
    }
    return { code: 0, message: 'ok', data: mockZiliao.drill }
  },

  async submitZiliaoDrill(data: {
    setId: string
    answers: { questionId: string; userAnswer: string | string[] }[]
    timeUsedSec?: number
    typeCode?: string
    saveWrongs?: boolean
  }): Promise<ApiRes<import('@/types').ZiliaoDrillSubmitResult>> {
    await delay(150)
    const ansMap = Object.fromEntries(data.answers.map((a) => [a.questionId, a.userAnswer]))
    const wrongs: import('@/types').ZiliaoDrillSubmitResult['wrongs'] = []
    let correct = 0
    for (const q of mockZiliao.drill.questions) {
      const u = String(ansMap[q.id] || '').toUpperCase()
      const c = mockZiliao.correctMap[q.id]
      if (u === c) correct += 1
      else {
        wrongs.push({
          questionId: q.id,
          stem: q.stem,
          material: mockZiliao.drill.material,
          options: q.options,
          userAnswer: u,
          correctAnswer: c,
          analysis: mockZiliao.analysisMap[q.id] || '',
        })
      }
    }
    mockZiliao.todaySets += 1
    mockZiliao.todayCorrect += correct
    mockZiliao.todayTotal += mockZiliao.drill.questions.length
    return {
      code: 0,
      message: 'ok',
      data: {
        setId: data.setId,
        totalCount: mockZiliao.drill.questions.length,
        correctCount: correct,
        timeUsedSec: data.timeUsedSec || 0,
        wrongs,
        savedWrongCount: data.saveWrongs === false ? 0 : wrongs.length,
      },
    }
  },

  async getCountdown(): Promise<ApiRes<import('@/types').ExamCountdown | null>> {
    await delay(100)
    return ok(mockState.countdown)
  },

  async saveCountdown(data: { examName: string; examDate: string; note?: string }): Promise<ApiRes<import('@/types').ExamCountdown>> {
    await delay(100)
    const daysLeft = Math.max(0, Math.ceil((new Date(data.examDate).getTime() - Date.now()) / 86400000))
    mockState.countdown = {
      id: 'ecd_mock',
      examName: data.examName,
      examDate: data.examDate,
      note: data.note || '',
      daysLeft,
      updatedAt: new Date().toISOString(),
    }
    return ok(mockState.countdown)
  },

  async deleteCountdown(): Promise<ApiRes<{ deleted: boolean }>> {
    await delay(100)
    mockState.countdown = null
    return ok({ deleted: true })
  },
}

export { questionBank }
