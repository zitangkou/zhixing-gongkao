import type {
  AnswerResult,
  ApiRes,
  Article,
  PayOrder,
  PointsLog,
  Question,
  RankItem,
  RankType,
  RechargePackage,
  ReviewTask,
  StudyRecord,
  UserInfo,
} from '@/types'
import { mockArticles, mockRankUsers, mockRechargePackages } from '@/mock/articles'
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
  shadowing: [] as import('@/types').UserSpeakingSentence[],
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
  ledgerExpenses: [] as import('@/types').LedgerExpense[],
  ledgerLoans: [] as import('@/types').LedgerLoan[],
  ledgerRepayments: [] as import('@/types').LedgerRepayment[],
  wealthSnapshots: [] as import('@/types').WealthSnapshot[],
  wealthPrinciples: [] as import('@/types').WealthPrinciple[],
  wealthJournals: [] as import('@/types').WealthJournal[],
  manualWrongs: [] as import('@/types').ManualWrong[],
  vocabs: null as import('@/types').UserVocab[] | null,
  planTasksByDate: {} as Record<string, import('@/types').PlanTask[]>,
  planReviewsByDate: {} as Record<string, import('@/types').DailyReview>,
}

const WEALTH_LAYER_LABELS: Record<number, string> = {
  1: '硬规则（不能违反）',
  2: '股票原则',
  3: '买入条件',
  4: '卖出条件',
}

const WEALTH_PART_LABELS: Record<string, string> = {
  cash: '现金',
  deposit: '存款',
  fund: '基金',
  stock: '股票',
  other: '其它',
}

function toCents(amount?: unknown, amountCents?: unknown): number {
  if (amountCents !== undefined && amountCents !== null && amountCents !== '') {
    return Math.max(0, Math.round(Number(amountCents)))
  }
  if (amount !== undefined && amount !== null && amount !== '') {
    return Math.max(0, Math.round(Number(amount) * 100))
  }
  return 0
}

function fromCents(cents: number): number {
  return Math.round(cents) / 100
}

function buildWealthAllocations(parts: Record<string, number>): import('@/types').WealthAllocationItem[] {
  const total = Object.values(parts).reduce((s, n) => s + n, 0)
  return Object.entries(parts)
    .filter(([, cents]) => cents > 0)
    .map(([key, cents]) => ({
      key,
      label: WEALTH_PART_LABELS[key] || key,
      amountCents: cents,
      amount: fromCents(cents),
      percent: total ? Math.round((cents / total) * 1000) / 10 : 0,
    }))
}

function recalcLoan(loan: import('@/types').LedgerLoan): import('@/types').LedgerLoan {
  const repayments = mockState.ledgerRepayments.filter((r) => r.loanId === loan.id)
  const repaidCents = repayments.reduce((s, r) => s + r.amountCents, 0)
  const remainingCents = Math.max(0, loan.principalCents - repaidCents)
  return {
    ...loan,
    repaidCents,
    repaid: fromCents(repaidCents),
    remainingCents,
    remaining: fromCents(remainingCents),
    status: remainingCents <= 0 ? 'settled' : 'open',
    repayments,
    updatedAt: new Date().toISOString(),
  }
}

function ensureVocabs(): import('@/types').UserVocab[] {
  if (!mockState.vocabs) {
    mockState.vocabs = [
      {
        id: 'uv1',
        word: 'improve',
        phonetic: "/ɪmˈpruːv/",
        meaning: '改进',
        pos: 'v',
        exampleSentence: 'I want to improve my English.',
        articleId: null,
        familiarity: 2,
        reviewCount: 1,
        nextReviewAt: new Date().toISOString(),
        mastered: false,
        createdAt: new Date().toISOString(),
      },
    ]
  }
  return mockState.vocabs
}

function ok<T>(data: T, message = 'success'): ApiRes<T> {
  return { code: 0, data, message }
}

const mockRmrb = {
  mines: [] as import('@/types').ShenlunMineLog[],
  terms: [] as import('@/types').ShenlunNormTerm[],
  drills: [] as import('@/types').ShenlunDrillLog[],
}

const mockHealth: { log: import('@/types').HealthDailyLog | null } = { log: null }

const mockDushu = {
  books: [
    {
      id: 'book-demo',
      title: '人类简史',
      author: '尤瓦尔·赫拉利',
      category: '历史',
      status: 'reading',
      currentChapter: '第一章',
      coverNote: 'Mock 示例书',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
  ] as import('@/types').DushuBook[],
  daily: [] as import('@/types').DushuDailyLog[],
  persons: [] as import('@/types').DushuPersonCard[],
  summaries: [] as import('@/types').DushuBookSummary[],
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

  async getRechargePackages(): Promise<ApiRes<RechargePackage[]>> {
    await delay()
    return ok(mockRechargePackages)
  },

  async createPayOrder(packageId: string): Promise<ApiRes<PayOrder>> {
    await delay()
    const pkg = mockRechargePackages.find((p) => p.id === packageId)
    if (!pkg) {
      return { code: 404, data: null as unknown as PayOrder, message: '套餐不存在' }
    }
    return ok({
      orderId: `order-${Date.now()}`,
      amount: pkg.price,
      payUrl: `mock://pay?orderId=order-${Date.now()}&amount=${pkg.price}`,
    })
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
    const vocabReviewCount = ensureVocabs().filter((v) => !v.mastered).length
    const manualWrongCount = mockState.manualWrongs.filter((w) => !w.mastered).length
    return ok({
      knowledgeDueCount: 2,
      articleReviewCount: 0,
      corpusInboxCount: 0,
      vocabReviewCount,
      articleWrongCount: 1,
      manualWrongCount,
      wrongReviewCount: 1,
      wrongWaitingCount: 2,
      wrongRecommendCount: 1,
      tvExpressionDueCount: 0,
      totalCount: 3 + vocabReviewCount + manualWrongCount,
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
  async listEnglishArticles(): Promise<ApiRes<import('@/types').EnglishArticle[]>> {
    await delay(200)
    return ok([
      {
        id: 'enart-mock-1', title: 'How to Improve Spoken English', source: 'BBC',
        level: 'B1', content: 'Practice every day...', vocabHighlights: [{ word: 'improve', meaning: '改进', pos: 'v', sentence: 'improve your English' }],
        audioUrl: '', tags: ['spoken'], difficulty: 3, isPublished: true, readCount: 12, createdAt: new Date().toISOString(),
      },
    ])
  },
  async getEnglishArticle(id: string): Promise<ApiRes<import('@/types').EnglishArticle>> {
    await delay(100)
    const r = await this.listEnglishArticles()
    const hit = (r.data || []).find((a) => a.id === id)
    return hit
      ? ok(hit)
      : { code: 404, data: null as unknown as import('@/types').EnglishArticle, message: '不存在' }
  },
  async listVocabs(_status?: string): Promise<ApiRes<import('@/types').UserVocab[]>> {
    await delay(200)
    let rows = [...ensureVocabs()]
    if (_status === 'mastered') rows = rows.filter((v) => v.mastered)
    else if (_status === 'learning') rows = rows.filter((v) => !v.mastered)
    return ok(rows)
  },
  async addVocab(data: {
    word: string
    phonetic?: string
    meaning?: string
    pos?: string
    exampleSentence?: string
    articleId?: string
  }): Promise<ApiRes<import('@/types').UserVocab>> {
    await delay(100)
    const row: import('@/types').UserVocab = {
      id: `uv-${Date.now()}`,
      word: data.word,
      phonetic: data.phonetic || '',
      meaning: data.meaning || '',
      pos: data.pos || '',
      exampleSentence: data.exampleSentence || '',
      articleId: data.articleId || null,
      familiarity: 1,
      reviewCount: 0,
      nextReviewAt: null,
      mastered: false,
      createdAt: new Date().toISOString(),
    }
    ensureVocabs().unshift(row)
    return ok(row)
  },
  async updateVocab(id: string, data: {
    familiarity?: number
    mastered?: boolean
    meaning?: string
    exampleSentence?: string
    phonetic?: string
    pos?: string
  }): Promise<ApiRes<import('@/types').UserVocab>> {
    await delay(100)
    const list = ensureVocabs()
    const idx = list.findIndex((v) => v.id === id)
    if (idx < 0) {
      return { code: 404, data: null as unknown as import('@/types').UserVocab, message: '不存在' }
    }
    const cur = list[idx]
    const next: import('@/types').UserVocab = {
      ...cur,
      ...(data.familiarity !== undefined ? { familiarity: data.familiarity } : {}),
      ...(data.mastered !== undefined ? { mastered: data.mastered } : {}),
      ...(data.meaning !== undefined ? { meaning: data.meaning } : {}),
      ...(data.exampleSentence !== undefined ? { exampleSentence: data.exampleSentence } : {}),
      ...(data.phonetic !== undefined ? { phonetic: data.phonetic } : {}),
      ...(data.pos !== undefined ? { pos: data.pos } : {}),
    }
    list[idx] = next
    return ok(next)
  },
  async deleteVocab(id: string): Promise<ApiRes<{ ok: boolean }>> {
    await delay(100)
    const list = ensureVocabs()
    const idx = list.findIndex((v) => v.id === id)
    if (idx >= 0) list.splice(idx, 1)
    return ok({ ok: true })
  },
  async listShadowing(): Promise<ApiRes<import('@/types').UserSpeakingSentence[]>> {
    await delay(100)
    return ok(mockState.shadowing)
  },
  async addShadowing(data: {
    sentence: string
    note?: string
    articleId?: string
    articleTitle?: string
  }): Promise<ApiRes<import('@/types').UserSpeakingSentence>> {
    await delay(100)
    const row = {
      id: `uss-${Date.now()}`,
      sentence: data.sentence,
      note: data.note || '',
      articleId: data.articleId || null,
      articleTitle: data.articleTitle || '',
      recordingUrl: '',
      practiceCount: 0,
      lastPracticeAt: null,
      createdAt: new Date().toISOString(),
    }
    mockState.shadowing.unshift(row)
    return ok(row)
  },
  async updateShadowing(id: string, data: {
    note?: string
    recordingUrl?: string
    practiced?: boolean
  }): Promise<ApiRes<import('@/types').UserSpeakingSentence>> {
    await delay(100)
    const idx = mockState.shadowing.findIndex((x) => x.id === id)
    const cur = idx >= 0 ? mockState.shadowing[idx] : {
      id, sentence: '', note: '', articleId: null, articleTitle: '',
      recordingUrl: '', practiceCount: 0, lastPracticeAt: null, createdAt: new Date().toISOString(),
    }
    const next = {
      ...cur,
      note: data.note ?? cur.note,
      recordingUrl: data.recordingUrl ?? cur.recordingUrl,
      practiceCount: data.practiced ? cur.practiceCount + 1 : cur.practiceCount,
      lastPracticeAt: data.practiced ? new Date().toISOString() : cur.lastPracticeAt,
    }
    if (idx >= 0) mockState.shadowing[idx] = next
    return ok(next)
  },
  async deleteShadowing(id: string): Promise<ApiRes<{ ok: boolean }>> {
    await delay(100)
    mockState.shadowing = mockState.shadowing.filter((x) => x.id !== id)
    return ok({ ok: true })
  },
  async listSpeakingLessons(): Promise<ApiRes<import('@/types').SpeakingLesson[]>> {
    await delay(200)
    return ok([
      { id: 'spk1', title: 'At the Airport', topic: 'travel', level: 'B1', dialogue: [{ speaker: 'A', en: 'Where is check-in?', zh: '登机柜台在哪？' }], keySentences: [{ en: 'Could you tell me where... is?', zh: '请问...在哪？', pattern: '问路' }], tips: '注意礼貌用语', isPublished: true, createdAt: new Date().toISOString() },
    ])
  },
  async getSpeakingLesson(id: string): Promise<ApiRes<import('@/types').SpeakingLesson>> {
    await delay(100)
    const r = await this.listSpeakingLessons()
    return ok(r.data![0])
  },
  async listSpeakingAttempts(_lessonId: string): Promise<ApiRes<import('@/types').SpeakingAttempt[]>> {
    await delay(100)
    return ok([])
  },
  async createSpeakingAttempt(data: { lessonId: string; selfRating?: number }): Promise<ApiRes<import('@/types').SpeakingAttempt>> {
    await delay(100)
    return ok({ id: `spa-${Date.now()}`, lessonId: data.lessonId, recordingUrl: '', selfRating: data.selfRating || 0, note: '', createdAt: new Date().toISOString() })
  },
  async listGrammarLessons(): Promise<ApiRes<import('@/types').GrammarLesson[]>> {
    await delay(200)
    return ok([
      { id: 'gm1', title: '现在完成时', category: '时态', level: 'B1', explanation: 'have/has + 过去分词', examples: [{ en: 'I have finished.', zh: '我完成了。' }], commonMistakes: [{ wrong: 'I have finished it yesterday.', correct: 'I finished it yesterday.', note: '不与具体过去时间连用' }], sortOrder: 0, isPublished: true, createdAt: new Date().toISOString() },
    ])
  },
  async getGrammarLesson(id: string): Promise<ApiRes<import('@/types').GrammarLesson>> {
    await delay(100)
    const r = await this.listGrammarLessons()
    return ok(r.data![0])
  },
  async updateGrammarProgress(lessonId: string, status: string): Promise<ApiRes<{ lessonId: string; status: string; lastStudyAt: string | null }>> {
    await delay(100)
    return ok({ lessonId, status, lastStudyAt: new Date().toISOString() })
  },
  async addEnglishLog(_data: { logType: string }): Promise<ApiRes<{ ok: boolean; id: string }>> {
    await delay(100)
    return ok({ ok: true, id: `log-${Date.now()}` })
  },
  async getEnglishStats(): Promise<ApiRes<import('@/types').EnglishStats>> {
    await delay(200)
    return ok({
      todayMinutes: 25, weekMinutes: 120, newVocabCount: 3, reviewVocabCount: 2,
      speakingCount: 1, grammarMasteredCount: 1, grammarLearningCount: 2, articleReadCount: 1,
      recentLogs: [{ id: 'l1', logType: 'article', durationSec: 300, wordsLearned: 3, sentencesPracticed: 0, studyDate: new Date().toISOString().slice(0, 10), note: '' }],
    })
  },

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
  async getDushuStats(): Promise<ApiRes<import('@/types').DushuStats>> {
    await delay(100)
    const reading = mockDushu.books.find((b) => b.status === 'reading')
    return ok({
      weekReadDays: 3,
      weekReadTarget: 7,
      weekOutputCount: mockDushu.daily.length,
      todayDone: mockDushu.daily.some((d) => d.logDate === new Date().toISOString().slice(0, 10)),
      readingBookTitle: reading?.title || '',
      bookCount: mockDushu.books.length,
      personCardCount: mockDushu.persons.length,
    })
  },
  async listDushuBooks(status?: string): Promise<ApiRes<import('@/types').DushuBook[]>> {
    await delay(100)
    const list = status ? mockDushu.books.filter((b) => b.status === status) : mockDushu.books
    return ok([...list])
  },
  async getDushuBook(id: string): Promise<ApiRes<import('@/types').DushuBook>> {
    await delay(100)
    const hit = mockDushu.books.find((b) => b.id === id)
    return hit ? ok(hit) : { code: 404, data: null as unknown as import('@/types').DushuBook, message: 'not found' }
  },
  async createDushuBook(data: Partial<import('@/types').DushuBook> & { title: string }): Promise<ApiRes<import('@/types').DushuBook>> {
    await delay(100)
    const now = new Date().toISOString()
    const row: import('@/types').DushuBook = {
      id: `book-${Date.now()}`,
      title: data.title,
      author: data.author || '',
      category: data.category || '其他',
      status: data.status || 'reading',
      currentChapter: data.currentChapter || '',
      coverNote: data.coverNote || '',
      createdAt: now,
      updatedAt: now,
    }
    mockDushu.books.unshift(row)
    return ok(row)
  },
  async updateDushuBook(id: string, data: Partial<import('@/types').DushuBook>): Promise<ApiRes<import('@/types').DushuBook>> {
    await delay(100)
    const row = mockDushu.books.find((b) => b.id === id)
    if (!row) return { code: 404, data: null as unknown as import('@/types').DushuBook, message: 'not found' }
    Object.assign(row, data, { updatedAt: new Date().toISOString() })
    return ok(row)
  },
  async deleteDushuBook(id: string): Promise<ApiRes<{ ok: boolean }>> {
    await delay(100)
    mockDushu.books = mockDushu.books.filter((b) => b.id !== id)
    return ok({ ok: true })
  },
  async listDushuDaily(bookId?: string): Promise<ApiRes<import('@/types').DushuDailyLog[]>> {
    await delay(100)
    const list = bookId ? mockDushu.daily.filter((d) => d.bookId === bookId) : mockDushu.daily
    return ok([...list])
  },
  async getDushuDailyByDate(date: string, bookId?: string): Promise<ApiRes<import('@/types').DushuDailyLog | null>> {
    await delay(100)
    const hit = mockDushu.daily.find((d) => d.logDate === date && (!bookId || d.bookId === bookId))
    return ok(hit || null)
  },
  async upsertDushuDaily(data: {
    bookId: string
    logDate?: string
    chapter?: string
    goal?: string
    output?: Record<string, string>
    oralNote?: string
    tags?: string
    durationMin?: number
  }): Promise<ApiRes<import('@/types').DushuDailyLog>> {
    await delay(100)
    const now = new Date().toISOString()
    const logDate = data.logDate || now.slice(0, 10)
    const book = mockDushu.books.find((b) => b.id === data.bookId)
    let row = mockDushu.daily.find((d) => d.bookId === data.bookId && d.logDate === logDate)
    if (!row) {
      row = {
        id: `daily-${Date.now()}`,
        bookId: data.bookId,
        bookTitle: book?.title || '',
        bookCategory: book?.category || '',
        logDate,
        chapter: data.chapter || '',
        goal: data.goal || '',
        output: data.output || {},
        oralNote: data.oralNote || '',
        tags: data.tags || '',
        durationMin: data.durationMin || 0,
        createdAt: now,
        updatedAt: now,
      }
      mockDushu.daily.unshift(row)
    } else {
      Object.assign(row, data, { updatedAt: now })
    }
    return ok(row)
  },
  async deleteDushuDaily(id: string): Promise<ApiRes<{ ok: boolean }>> {
    await delay(100)
    mockDushu.daily = mockDushu.daily.filter((d) => d.id !== id)
    return ok({ ok: true })
  },
  async listDushuPersons(bookId?: string): Promise<ApiRes<import('@/types').DushuPersonCard[]>> {
    await delay(100)
    const list = bookId ? mockDushu.persons.filter((p) => p.bookId === bookId) : mockDushu.persons
    return ok([...list])
  },
  async createDushuPerson(data: {
    bookId: string
    name: string
    trait?: string
    success?: string
    failure?: string
    lesson?: string
    tags?: string
  }): Promise<ApiRes<import('@/types').DushuPersonCard>> {
    await delay(100)
    const book = mockDushu.books.find((b) => b.id === data.bookId)
    const now = new Date().toISOString()
    const row: import('@/types').DushuPersonCard = {
      id: `person-${Date.now()}`,
      bookId: data.bookId,
      bookTitle: book?.title || '',
      name: data.name,
      trait: data.trait || '',
      success: data.success || '',
      failure: data.failure || '',
      lesson: data.lesson || '',
      tags: data.tags || '',
      createdAt: now,
      updatedAt: now,
    }
    mockDushu.persons.unshift(row)
    return ok(row)
  },
  async updateDushuPerson(id: string, data: Partial<import('@/types').DushuPersonCard>): Promise<ApiRes<import('@/types').DushuPersonCard>> {
    await delay(100)
    const row = mockDushu.persons.find((p) => p.id === id)
    if (!row) return { code: 404, data: null as unknown as import('@/types').DushuPersonCard, message: 'not found' }
    Object.assign(row, data, { updatedAt: new Date().toISOString() })
    return ok(row)
  },
  async deleteDushuPerson(id: string): Promise<ApiRes<{ ok: boolean }>> {
    await delay(100)
    mockDushu.persons = mockDushu.persons.filter((p) => p.id !== id)
    return ok({ ok: true })
  },
  async listDushuSummaries(): Promise<ApiRes<import('@/types').DushuBookSummary[]>> {
    await delay(100)
    return ok([...mockDushu.summaries])
  },
  async getDushuSummary(bookId: string): Promise<ApiRes<import('@/types').DushuBookSummary | null>> {
    await delay(100)
    return ok(mockDushu.summaries.find((s) => s.bookId === bookId) || null)
  },
  async upsertDushuSummary(data: {
    bookId: string
    coreQuestion?: string
    skeleton?: string
    insights?: string[]
    story?: string
    model?: string
    action?: string
  }): Promise<ApiRes<import('@/types').DushuBookSummary>> {
    await delay(100)
    const now = new Date().toISOString()
    const book = mockDushu.books.find((b) => b.id === data.bookId)
    let row = mockDushu.summaries.find((s) => s.bookId === data.bookId)
    if (!row) {
      row = {
        id: `sum-${Date.now()}`,
        bookId: data.bookId,
        bookTitle: book?.title || '',
        coreQuestion: data.coreQuestion || '',
        skeleton: data.skeleton || '',
        insights: data.insights || [],
        story: data.story || '',
        model: data.model || '',
        action: data.action || '',
        createdAt: now,
        updatedAt: now,
      }
      mockDushu.summaries.unshift(row)
    } else {
      Object.assign(row, data, { updatedAt: now })
    }
    return ok(row)
  },

  // ===== 健康 mock =====
  async getHealthOverview(): Promise<ApiRes<import('@/types').HealthOverview>> {
    await delay(150)
    const today = new Date().toISOString().slice(0, 10)
    const labels = ['一', '二', '三', '四', '五', '六', '日']
    const monday = new Date()
    monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7))
    const mk = (vals: number[]) =>
      labels.map((label, i) => {
        const d = new Date(monday)
        d.setDate(monday.getDate() + i)
        const date = d.toISOString().slice(0, 10)
        return { date, label, value: vals[i] || 0, isToday: date === today }
      })
    const phase = {
      phase: 1,
      weekStart: 1,
      weekEnd: 2,
      title: '恢复心理能量',
      goal: '不解决社交，只恢复身体和精神。',
      principle: '先充电。',
      focusSkills: ['energy', 'cbt', 'exposure_micro'],
    }
    const tasks = [
      { id: 'p1-walk', phase: 1, domain: 'body', skill: 'energy', skillLabel: '能量恢复', title: '散步 20～30 分钟', detail: '不戴耳机', optional: false },
      { id: 'p1-cbt', phase: 1, domain: 'mind', skill: 'cbt', skillLabel: '想法练习', title: '焦虑五问', detail: '写 5 分钟', optional: false },
      { id: 'p1-three', phase: 1, domain: 'mind', skill: 'exposure_micro', skillLabel: '小暴露', title: '主动说三句短话', detail: '谢谢即可', optional: false },
    ]
    return ok({
      programStartDate: today,
      weekIndex: 1,
      phase,
      todayCheckedIn: !!mockHealth.log,
      streakDays: mockHealth.log ? 1 : 0,
      todayTasks: tasks,
      todayLog: mockHealth.log,
      weekMood: mk([5, 6, 5, 7, 6, 4, 5]),
      weekEnergy: mk([4, 5, 4, 5, 5, 3, 4]),
      weekStomach: mk([6, 7, 6, 7, 7, 5, 6]),
      weekSkin: mk([3, 3, 4, 3, 2, 4, 3]),
      weekDampness: mk([4, 4, 5, 4, 3, 5, 4]),
      weekMindStats: {
        exposureTaskCompletions: 2,
        cbtDays: 1,
        avgAnxiety: 4,
        avgEnergy: 4.5,
        socialCountSum: 6,
      },
      lowEnergyHint: false,
      softTips: [],
      privateFocus: '',
      disclaimer: '本模块仅供自我观察与习惯管理，不能替代医疗或心理咨询。',
    })
  },
  async listHealthPhases(): Promise<ApiRes<import('@/types').HealthPhase[]>> {
    await delay(50)
    return ok([
      { phase: 1, weekStart: 1, weekEnd: 2, title: '恢复心理能量', goal: '先充电', principle: '不逼社交', focusSkills: ['energy'] },
      { phase: 2, weekStart: 3, weekEnd: 4, title: '降低社交焦虑', goal: '小暴露', principle: '打招呼即可', focusSkills: ['exposure_micro'] },
      { phase: 3, weekStart: 5, weekEnd: 6, title: '真正开始聊天', goal: '好奇', principle: '一个问题', focusSkills: ['exposure_talk'] },
      { phase: 4, weekStart: 7, weekEnd: 8, title: '突破舒适区', goal: '完成即可', principle: '允许冷场', focusSkills: ['exposure_stretch'] },
    ])
  },
  async listHealthTasks(_phase?: number): Promise<ApiRes<import('@/types').HealthTask[]>> {
    const ov = await this.getHealthOverview()
    return ok(ov.data!.todayTasks)
  },
  async getHealthDaily(_date?: string): Promise<ApiRes<import('@/types').HealthDailyLog | null>> {
    await delay(50)
    return ok(mockHealth.log)
  },
  async listHealthDailyWeek(): Promise<ApiRes<import('@/types').HealthDailyLog[]>> {
    await delay(50)
    return ok(mockHealth.log ? [mockHealth.log] : [])
  },
  async upsertHealthDaily(data: Partial<import('@/types').HealthDailyLog> & { logDate?: string }): Promise<ApiRes<import('@/types').HealthDailyLog>> {
    await delay(100)
    const today = new Date().toISOString().slice(0, 10)
    const emptyCbt = { anxious: '', why: '', worst: '', probability: '', acceptable: '', nextStep: '' }
    const emptyRum = { triggered: false, stoppedInTime: false, note: '' }
    const emptyRev = { bestThing: '', tomorrowGoal: '', bodyAssessment: '' }
    const emptyMeal = { eaten: false, items: '', light: false, time: '', score: 0, feel: '' }
    const emptyMeals = {
      breakfast: { ...emptyMeal },
      lunch: { ...emptyMeal },
      dinner: { ...emptyMeal },
      snack: { ...emptyMeal },
      waterCups: 0,
      note: '',
    }
    const emptyStool = { times: 0, form: '', ease: '', urineOk: true, note: '' }
    const prev = mockHealth.log
    const meals = data.meals
      ? {
          breakfast: { ...emptyMeal, ...(prev?.meals?.breakfast || {}), ...(data.meals.breakfast || {}) },
          lunch: { ...emptyMeal, ...(prev?.meals?.lunch || {}), ...(data.meals.lunch || {}) },
          dinner: { ...emptyMeal, ...(prev?.meals?.dinner || {}), ...(data.meals.dinner || {}) },
          snack: { ...emptyMeal, ...(prev?.meals?.snack || {}), ...(data.meals.snack || {}) },
          waterCups: data.meals.waterCups ?? prev?.meals?.waterCups ?? 0,
          note: data.meals.note ?? prev?.meals?.note ?? '',
        }
      : (prev?.meals || emptyMeals)
    const stool = data.stool ? { ...emptyStool, ...(prev?.stool || {}), ...data.stool } : (prev?.stool || emptyStool)
    const eatenN = [meals.breakfast, meals.lunch, meals.dinner].filter((m) => m.eaten).length
    let bodyAssessment = '记录已保存。'
    if (eatenN < 3) bodyAssessment = `正餐记录 ${eatenN}/3，节律偏碎；`
    else bodyAssessment = '三餐有记录；'
    if (stool.times === 0) bodyAssessment += '排便未记或未排。'
    else if (stool.form === 'hard') bodyAssessment += '便偏干，注意饮水与走动。'
    else bodyAssessment += `排便 ${stool.times} 次，大体可观察。`
    mockHealth.log = {
      id: prev?.id || `hdl-${Date.now()}`,
      logDate: data.logDate || today,
      mood: data.mood ?? prev?.mood ?? 0,
      sleepQuality: data.sleepQuality ?? prev?.sleepQuality ?? 0,
      sleepBefore23: data.sleepBefore23 ?? prev?.sleepBefore23 ?? false,
      mealsRegular: data.mealsRegular ?? prev?.mealsRegular ?? eatenN >= 3,
      mealsLight: data.mealsLight ?? prev?.mealsLight ?? false,
      weekendLieFlat: data.weekendLieFlat ?? prev?.weekendLieFlat ?? false,
      habitNote: data.habitNote ?? prev?.habitNote ?? '',
      meals,
      stool,
      stomach: data.stomach ?? prev?.stomach ?? 0,
      dampness: data.dampness ?? prev?.dampness ?? 0,
      skin: data.skin ?? prev?.skin ?? 0,
      skinItch: data.skinItch ?? prev?.skinItch ?? false,
      skinFlare: data.skinFlare ?? prev?.skinFlare ?? false,
      walkMin: data.walkMin ?? prev?.walkMin ?? 0,
      bodyNote: data.bodyNote ?? prev?.bodyNote ?? '',
      anxiety: data.anxiety ?? prev?.anxiety ?? 0,
      energy: data.energy ?? prev?.energy ?? 0,
      socialCount: data.socialCount ?? prev?.socialCount ?? 0,
      studyMin: data.studyMin ?? prev?.studyMin ?? 0,
      tasksDone: data.tasksDone ?? prev?.tasksDone ?? [],
      cbt: { ...emptyCbt, ...(prev?.cbt || {}), ...(data.cbt || {}) },
      rumination: { ...emptyRum, ...(prev?.rumination || {}), ...(data.rumination || {}) },
      review: {
        ...emptyRev,
        ...(prev?.review || {}),
        ...(data.review || {}),
        bodyAssessment: data.review?.bodyAssessment || bodyAssessment,
      },
      bodyAssessment,
    }
    return ok(mockHealth.log)
  },
  async resetHealthProgram(): Promise<ApiRes<{ programStartDate: string }>> {
    await delay(50)
    const today = new Date().toISOString().slice(0, 10)
    return ok({ programStartDate: today })
  },

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
        { key: 'english', name: '英语', percent: 57, detail: '本周 120 分钟 · 语法掌握 1' },
        { key: 'dushu', name: '读书', percent: 43, detail: '本周阅读 3 天 · 输出 2 次' },
        { key: 'wrong', name: '错题消化', percent: 40, detail: '行测掌握 4/10 · 文章错题 6' },
      ],
    })
  },

  // 音标 mock
  async listPhonetics(): Promise<ApiRes<import('@/types').PhoneticLesson[]>> {
    await delay(200)
    return ok([
      { id: 'ph1', symbol: '/iː/', category: 'unit_vowel', description: '长元音', mouthShape: '嘴角微笑', tips: '类似中文「衣」', exampleWords: [{ word: 'see', meaning: '看见' }, { word: 'tree', meaning: '树' }], commonSpellings: ['ee', 'ea'], sortOrder: 1, isPublished: true },
      { id: 'ph2', symbol: '/p/', category: 'consonant', description: '清辅音', mouthShape: '双唇紧闭', tips: '送气', exampleWords: [{ word: 'pen', meaning: '钢笔' }, { word: 'apple', meaning: '苹果' }], commonSpellings: ['p', 'pp'], sortOrder: 21, isPublished: true },
    ])
  },
  async getPhoneticProgress(): Promise<ApiRes<import('@/types').PhoneticProgressMap>> {
    await delay(100)
    return ok({})
  },
  async updatePhoneticProgress(lessonId: string, status: string): Promise<ApiRes<{ lessonId: string; status: string; practicedCount: number }>> {
    await delay(100)
    return ok({ lessonId, status, practicedCount: 1 })
  },

  // ===== 记账 mock =====
  async getLedgerOverview(month?: string): Promise<ApiRes<import('@/types').LedgerOverview>> {
    await delay(80)
    const m = month || new Date().toISOString().slice(0, 7)
    const today = new Date().toISOString().slice(0, 10)
    const monthRows = mockState.ledgerExpenses.filter((e) => e.occurDate.startsWith(m))
    const todayRows = mockState.ledgerExpenses.filter((e) => e.occurDate === today)
    const monthExpenseCents = monthRows.reduce((s, e) => s + e.amountCents, 0)
    const todayExpenseCents = todayRows.reduce((s, e) => s + e.amountCents, 0)
    const openLoans = mockState.ledgerLoans.filter((l) => l.status !== 'settled')
    const remainingCents = openLoans.reduce((s, l) => s + l.remainingCents, 0)
    const catMap = new Map<string, { amountCents: number; count: number }>()
    monthRows.forEach((e) => {
      const cur = catMap.get(e.category) || { amountCents: 0, count: 0 }
      cur.amountCents += e.amountCents
      cur.count += 1
      catMap.set(e.category, cur)
    })
    const categories = Array.from(catMap.entries()).map(([category, v]) => ({
      category,
      amountCents: v.amountCents,
      amount: fromCents(v.amountCents),
      percent: monthExpenseCents ? Math.round((v.amountCents / monthExpenseCents) * 1000) / 10 : 0,
      count: v.count,
    }))
    return ok({
      month: m,
      monthExpenseCents,
      monthExpense: fromCents(monthExpenseCents),
      todayExpenseCents,
      todayExpense: fromCents(todayExpenseCents),
      openLoanCount: openLoans.length,
      remainingCents,
      remaining: fromCents(remainingCents),
      categories,
      expenseCategories: ['餐饮', '交通', '日用', '住房', '学习', '医疗', '娱乐', '人情', '其他'],
      repayMethods: ['微信', '支付宝', '现金', '银行转账', '其他'],
    })
  },
  async listLedgerExpenses(month?: string): Promise<ApiRes<import('@/types').LedgerExpense[]>> {
    await delay(80)
    let rows = [...mockState.ledgerExpenses]
    if (month) rows = rows.filter((e) => e.occurDate.startsWith(month))
    return ok(rows)
  },
  async getLedgerExpense(id: string): Promise<ApiRes<import('@/types').LedgerExpense>> {
    await delay(80)
    const hit = mockState.ledgerExpenses.find((e) => e.id === id)
    return hit
      ? ok(hit)
      : { code: 404, data: null as unknown as import('@/types').LedgerExpense, message: 'not found' }
  },
  async createLedgerExpense(data: Record<string, unknown>): Promise<ApiRes<import('@/types').LedgerExpense>> {
    await delay(80)
    const amountCents = toCents(data.amount, data.amountCents)
    const now = new Date().toISOString()
    const row: import('@/types').LedgerExpense = {
      id: `lex-${Date.now()}`,
      amountCents,
      amount: fromCents(amountCents),
      occurDate: String(data.occurDate || now.slice(0, 10)),
      category: String(data.category || '其他'),
      note: String(data.note || ''),
      images: (data.images as string[]) || [],
      createdAt: now,
      updatedAt: now,
    }
    mockState.ledgerExpenses.unshift(row)
    return ok(row)
  },
  async updateLedgerExpense(id: string, data: Record<string, unknown>): Promise<ApiRes<import('@/types').LedgerExpense>> {
    await delay(80)
    const idx = mockState.ledgerExpenses.findIndex((e) => e.id === id)
    if (idx < 0) {
      return { code: 404, data: null as unknown as import('@/types').LedgerExpense, message: 'not found' }
    }
    const cur = mockState.ledgerExpenses[idx]
    const amountCents =
      data.amount !== undefined || data.amountCents !== undefined
        ? toCents(data.amount, data.amountCents)
        : cur.amountCents
    const next: import('@/types').LedgerExpense = {
      ...cur,
      amountCents,
      amount: fromCents(amountCents),
      occurDate: data.occurDate !== undefined ? String(data.occurDate) : cur.occurDate,
      category: data.category !== undefined ? String(data.category) : cur.category,
      note: data.note !== undefined ? String(data.note) : cur.note,
      images: data.images !== undefined ? (data.images as string[]) : cur.images,
      updatedAt: new Date().toISOString(),
    }
    mockState.ledgerExpenses[idx] = next
    return ok(next)
  },
  async deleteLedgerExpense(id: string): Promise<ApiRes<{ ok: boolean }>> {
    await delay(50)
    const idx = mockState.ledgerExpenses.findIndex((e) => e.id === id)
    if (idx >= 0) mockState.ledgerExpenses.splice(idx, 1)
    return ok({ ok: true })
  },
  async listLedgerLoans(
    status?: string,
    counterparty?: string,
  ): Promise<ApiRes<import('@/types').LedgerLoan[]>> {
    await delay(80)
    let rows = mockState.ledgerLoans.map((l) => recalcLoan(l))
    mockState.ledgerLoans = rows
    if (status) rows = rows.filter((l) => l.status === status)
    if (counterparty) rows = rows.filter((l) => l.counterparty === counterparty)
    return ok(rows)
  },
  async listLedgerCounterparties(): Promise<ApiRes<import('@/types').LedgerCounterparty[]>> {
    await delay(80)
    const map = new Map<string, import('@/types').LedgerCounterparty>()
    mockState.ledgerLoans.forEach((loan) => {
      const l = recalcLoan(loan)
      const cur = map.get(l.counterparty) || {
        name: l.counterparty,
        loanCount: 0,
        openCount: 0,
        principalCents: 0,
        principal: 0,
        repaidCents: 0,
        repaid: 0,
        remainingCents: 0,
        remaining: 0,
        lastLendDate: '',
      }
      cur.loanCount += 1
      if (l.status !== 'settled') cur.openCount += 1
      cur.principalCents += l.principalCents
      cur.principal = fromCents(cur.principalCents)
      cur.repaidCents += l.repaidCents
      cur.repaid = fromCents(cur.repaidCents)
      cur.remainingCents += l.remainingCents
      cur.remaining = fromCents(cur.remainingCents)
      if (!cur.lastLendDate || l.lendDate > cur.lastLendDate) cur.lastLendDate = l.lendDate
      map.set(l.counterparty, cur)
    })
    return ok(Array.from(map.values()))
  },
  async getLedgerLoan(id: string): Promise<ApiRes<import('@/types').LedgerLoan>> {
    await delay(80)
    const idx = mockState.ledgerLoans.findIndex((l) => l.id === id)
    if (idx < 0) {
      return { code: 404, data: null as unknown as import('@/types').LedgerLoan, message: 'not found' }
    }
    const loan = recalcLoan(mockState.ledgerLoans[idx])
    mockState.ledgerLoans[idx] = loan
    return ok(loan)
  },
  async createLedgerLoan(data: Record<string, unknown>): Promise<ApiRes<import('@/types').LedgerLoan>> {
    await delay(80)
    const principalCents = toCents(data.amount, data.amountCents)
    const now = new Date().toISOString()
    const row: import('@/types').LedgerLoan = {
      id: `lln-${Date.now()}`,
      counterparty: String(data.counterparty || ''),
      principalCents,
      principal: fromCents(principalCents),
      repaidCents: 0,
      repaid: 0,
      remainingCents: principalCents,
      remaining: fromCents(principalCents),
      lendDate: String(data.lendDate || now.slice(0, 10)),
      dueDate: String(data.dueDate || ''),
      status: 'open',
      note: String(data.note || ''),
      images: (data.images as string[]) || [],
      repayments: [],
      createdAt: now,
      updatedAt: now,
    }
    mockState.ledgerLoans.unshift(row)
    return ok(row)
  },
  async updateLedgerLoan(id: string, data: Record<string, unknown>): Promise<ApiRes<import('@/types').LedgerLoan>> {
    await delay(80)
    const idx = mockState.ledgerLoans.findIndex((l) => l.id === id)
    if (idx < 0) {
      return { code: 404, data: null as unknown as import('@/types').LedgerLoan, message: 'not found' }
    }
    const cur = mockState.ledgerLoans[idx]
    const principalCents =
      data.amount !== undefined || data.amountCents !== undefined
        ? toCents(data.amount, data.amountCents)
        : cur.principalCents
    mockState.ledgerLoans[idx] = {
      ...cur,
      counterparty: data.counterparty !== undefined ? String(data.counterparty) : cur.counterparty,
      principalCents,
      principal: fromCents(principalCents),
      lendDate: data.lendDate !== undefined ? String(data.lendDate) : cur.lendDate,
      dueDate: data.dueDate !== undefined ? String(data.dueDate) : cur.dueDate,
      note: data.note !== undefined ? String(data.note) : cur.note,
      images: data.images !== undefined ? (data.images as string[]) : cur.images,
      updatedAt: new Date().toISOString(),
    }
    const next = recalcLoan(mockState.ledgerLoans[idx])
    mockState.ledgerLoans[idx] = next
    return ok(next)
  },
  async deleteLedgerLoan(id: string): Promise<ApiRes<{ ok: boolean }>> {
    await delay(50)
    const idx = mockState.ledgerLoans.findIndex((l) => l.id === id)
    if (idx >= 0) mockState.ledgerLoans.splice(idx, 1)
    mockState.ledgerRepayments = mockState.ledgerRepayments.filter((r) => r.loanId !== id)
    return ok({ ok: true })
  },
  async createLedgerRepayment(loanId: string, data: Record<string, unknown>): Promise<ApiRes<import('@/types').LedgerRepayment>> {
    await delay(80)
    const amountCents = toCents(data.amount, data.amountCents)
    const now = new Date().toISOString()
    const row: import('@/types').LedgerRepayment = {
      id: `lrp-${Date.now()}`,
      loanId,
      amountCents,
      amount: fromCents(amountCents),
      repayDate: String(data.repayDate || now.slice(0, 10)),
      method: String(data.method || '微信'),
      note: String(data.note || ''),
      images: (data.images as string[]) || [],
      createdAt: now,
      updatedAt: now,
    }
    mockState.ledgerRepayments.unshift(row)
    const loanIdx = mockState.ledgerLoans.findIndex((l) => l.id === loanId)
    if (loanIdx >= 0) mockState.ledgerLoans[loanIdx] = recalcLoan(mockState.ledgerLoans[loanIdx])
    return ok(row)
  },
  async updateLedgerRepayment(id: string, data: Record<string, unknown>): Promise<ApiRes<import('@/types').LedgerRepayment>> {
    await delay(80)
    const idx = mockState.ledgerRepayments.findIndex((r) => r.id === id)
    if (idx < 0) {
      return { code: 404, data: null as unknown as import('@/types').LedgerRepayment, message: 'not found' }
    }
    const cur = mockState.ledgerRepayments[idx]
    const amountCents =
      data.amount !== undefined || data.amountCents !== undefined
        ? toCents(data.amount, data.amountCents)
        : cur.amountCents
    const next: import('@/types').LedgerRepayment = {
      ...cur,
      amountCents,
      amount: fromCents(amountCents),
      repayDate: data.repayDate !== undefined ? String(data.repayDate) : cur.repayDate,
      method: data.method !== undefined ? String(data.method) : cur.method,
      note: data.note !== undefined ? String(data.note) : cur.note,
      images: data.images !== undefined ? (data.images as string[]) : cur.images,
      updatedAt: new Date().toISOString(),
    }
    mockState.ledgerRepayments[idx] = next
    const loanIdx = mockState.ledgerLoans.findIndex((l) => l.id === next.loanId)
    if (loanIdx >= 0) mockState.ledgerLoans[loanIdx] = recalcLoan(mockState.ledgerLoans[loanIdx])
    return ok(next)
  },
  async deleteLedgerRepayment(id: string): Promise<ApiRes<{ ok: boolean }>> {
    await delay(50)
    const idx = mockState.ledgerRepayments.findIndex((r) => r.id === id)
    if (idx >= 0) {
      const loanId = mockState.ledgerRepayments[idx].loanId
      mockState.ledgerRepayments.splice(idx, 1)
      const loanIdx = mockState.ledgerLoans.findIndex((l) => l.id === loanId)
      if (loanIdx >= 0) mockState.ledgerLoans[loanIdx] = recalcLoan(mockState.ledgerLoans[loanIdx])
    }
    return ok({ ok: true })
  },

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

  async getWealthHub(): Promise<ApiRes<import('@/types').WealthHub>> {
    await delay(40)
    const snaps = [...mockState.wealthSnapshots].sort((a, b) => (a.snapDate < b.snapDate ? 1 : -1))
    const weekAgo = new Date()
    weekAgo.setDate(weekAgo.getDate() - 7)
    const weekStart = weekAgo.toISOString().slice(0, 10)
    const weekJournals = mockState.wealthJournals.filter((j) => j.tradeDate >= weekStart)
    return ok({
      latestSnapshot: snaps[0] || null,
      principleCount: mockState.wealthPrinciples.length,
      journalCount: mockState.wealthJournals.length,
      weekTradeCount: weekJournals.length,
      weekWinCount: weekJournals.filter((j) => j.resultTag === 'win').length,
      weekLossCount: weekJournals.filter((j) => j.resultTag === 'loss').length,
    })
  },
  async listWealthSnapshots(): Promise<ApiRes<import('@/types').WealthSnapshot[]>> {
    await delay(30)
    return ok([...mockState.wealthSnapshots].sort((a, b) => (a.snapDate < b.snapDate ? 1 : -1)))
  },
  async getWealthSnapshot(id: string): Promise<ApiRes<import('@/types').WealthSnapshot>> {
    const hit = mockState.wealthSnapshots.find((s) => s.id === id)
    return hit
      ? ok(hit)
      : { code: 404, data: null as any, message: '不存在' }
  },
  async createWealthSnapshot(data: Record<string, unknown>): Promise<ApiRes<import('@/types').WealthSnapshot>> {
    await delay(40)
    const now = new Date().toISOString()
    const parts = {
      cash: toCents(data.cash, data.cashCents),
      deposit: toCents(data.deposit, data.depositCents),
      fund: toCents(data.fund, data.fundCents),
      stock: toCents(data.stock, data.stockCents),
      other: toCents(data.other, data.otherCents),
    }
    const totalCents = Object.values(parts).reduce((s, n) => s + n, 0)
    const row: import('@/types').WealthSnapshot = {
      id: `wsp-${Date.now()}`,
      snapDate: String(data.snapDate || now.slice(0, 10)),
      cashCents: parts.cash,
      depositCents: parts.deposit,
      fundCents: parts.fund,
      stockCents: parts.stock,
      otherCents: parts.other,
      cash: fromCents(parts.cash),
      deposit: fromCents(parts.deposit),
      fund: fromCents(parts.fund),
      stock: fromCents(parts.stock),
      other: fromCents(parts.other),
      totalCents,
      total: fromCents(totalCents),
      allocations: buildWealthAllocations(parts),
      note: String(data.note || ''),
      createdAt: now,
      updatedAt: now,
    }
    mockState.wealthSnapshots.unshift(row)
    return ok(row)
  },
  async updateWealthSnapshot(id: string, data: Record<string, unknown>) {
    await delay(40)
    const idx = mockState.wealthSnapshots.findIndex((s) => s.id === id)
    if (idx < 0) {
      return { code: 404, data: null as any, message: '不存在' }
    }
    const cur = mockState.wealthSnapshots[idx]
    const parts = {
      cash: data.cash !== undefined || data.cashCents !== undefined
        ? toCents(data.cash, data.cashCents)
        : cur.cashCents,
      deposit: data.deposit !== undefined || data.depositCents !== undefined
        ? toCents(data.deposit, data.depositCents)
        : cur.depositCents,
      fund: data.fund !== undefined || data.fundCents !== undefined
        ? toCents(data.fund, data.fundCents)
        : cur.fundCents,
      stock: data.stock !== undefined || data.stockCents !== undefined
        ? toCents(data.stock, data.stockCents)
        : cur.stockCents,
      other: data.other !== undefined || data.otherCents !== undefined
        ? toCents(data.other, data.otherCents)
        : cur.otherCents,
    }
    const totalCents = Object.values(parts).reduce((s, n) => s + n, 0)
    const next: import('@/types').WealthSnapshot = {
      ...cur,
      snapDate: data.snapDate !== undefined ? String(data.snapDate) : cur.snapDate,
      cashCents: parts.cash,
      depositCents: parts.deposit,
      fundCents: parts.fund,
      stockCents: parts.stock,
      otherCents: parts.other,
      cash: fromCents(parts.cash),
      deposit: fromCents(parts.deposit),
      fund: fromCents(parts.fund),
      stock: fromCents(parts.stock),
      other: fromCents(parts.other),
      totalCents,
      total: fromCents(totalCents),
      allocations: buildWealthAllocations(parts),
      note: data.note !== undefined ? String(data.note) : cur.note,
      updatedAt: new Date().toISOString(),
    }
    mockState.wealthSnapshots[idx] = next
    return ok(next)
  },
  async deleteWealthSnapshot(id: string): Promise<ApiRes<{ ok: boolean }>> {
    const idx = mockState.wealthSnapshots.findIndex((s) => s.id === id)
    if (idx >= 0) mockState.wealthSnapshots.splice(idx, 1)
    return ok({ ok: true })
  },
  async listWealthPrinciples(): Promise<ApiRes<import('@/types').WealthPrinciple[]>> {
    return ok([...mockState.wealthPrinciples])
  },
  async createWealthPrinciple(data: Record<string, unknown>): Promise<ApiRes<import('@/types').WealthPrinciple>> {
    const now = new Date().toISOString()
    const layer = Number(data.layer || 1)
    const row: import('@/types').WealthPrinciple = {
      id: `wpr-${Date.now()}`,
      layer,
      layerLabel: WEALTH_LAYER_LABELS[layer] || '',
      title: String(data.title || ''),
      content: String(data.content || ''),
      sortOrder: Number(data.sortOrder || 0),
      isEnabled: data.isEnabled !== false,
      createdAt: now,
      updatedAt: now,
    }
    mockState.wealthPrinciples.unshift(row)
    return ok(row)
  },
  async updateWealthPrinciple(id: string, data: Record<string, unknown>) {
    const idx = mockState.wealthPrinciples.findIndex((p) => p.id === id)
    if (idx < 0) {
      return { code: 404, data: null as any, message: '不存在' }
    }
    const cur = mockState.wealthPrinciples[idx]
    const layer = data.layer !== undefined ? Number(data.layer) : cur.layer
    const next: import('@/types').WealthPrinciple = {
      ...cur,
      layer,
      layerLabel: WEALTH_LAYER_LABELS[layer] || cur.layerLabel,
      title: data.title !== undefined ? String(data.title) : cur.title,
      content: data.content !== undefined ? String(data.content) : cur.content,
      sortOrder: data.sortOrder !== undefined ? Number(data.sortOrder) : cur.sortOrder,
      isEnabled: data.isEnabled !== undefined ? !!data.isEnabled : cur.isEnabled,
      updatedAt: new Date().toISOString(),
    }
    mockState.wealthPrinciples[idx] = next
    return ok(next)
  },
  async deleteWealthPrinciple(id: string): Promise<ApiRes<{ ok: boolean }>> {
    const idx = mockState.wealthPrinciples.findIndex((p) => p.id === id)
    if (idx >= 0) mockState.wealthPrinciples.splice(idx, 1)
    return ok({ ok: true })
  },
  async listWealthJournals(): Promise<ApiRes<import('@/types').WealthJournal[]>> {
    return ok([...mockState.wealthJournals])
  },
  async getWealthJournal(id: string): Promise<ApiRes<import('@/types').WealthJournal>> {
    const hit = mockState.wealthJournals.find((j) => j.id === id)
    return hit
      ? ok(hit)
      : { code: 404, data: null as any, message: '不存在' }
  },
  async createWealthJournal(data: Record<string, unknown>): Promise<ApiRes<import('@/types').WealthJournal>> {
    const now = new Date().toISOString()
    const row: import('@/types').WealthJournal = {
      id: `wjn-${Date.now()}`,
      side: String(data.side || 'buy'),
      symbol: String(data.symbol || ''),
      name: String(data.name || ''),
      tradeDate: String(data.tradeDate || now.slice(0, 10)),
      price: Number(data.price || 0),
      positionPct: Number(data.positionPct || 0),
      reasons: (data.reasons as string[]) || [],
      reasonNote: String(data.reasonNote || ''),
      riskNote: String(data.riskNote || ''),
      stopLoss: Number(data.stopLoss || 0),
      targetPrice: Number(data.targetPrice || 0),
      emotion: String(data.emotion || 'ok'),
      confidence: Number(data.confidence || 3),
      sleepHours: Number(data.sleepHours || 0),
      workStress: Number(data.workStress || 0),
      hadQuarrel: !!data.hadQuarrel,
      followedPlan: (data.followedPlan as boolean | null) ?? null,
      checklistOk: !!data.checklistOk,
      resultTag: String(data.resultTag || ''),
      note: String(data.note || ''),
      createdAt: now,
      updatedAt: now,
    }
    mockState.wealthJournals.unshift(row)
    return ok(row)
  },
  async updateWealthJournal(id: string, data: Record<string, unknown>) {
    const idx = mockState.wealthJournals.findIndex((j) => j.id === id)
    if (idx < 0) {
      return { code: 404, data: null as any, message: '不存在' }
    }
    const cur = mockState.wealthJournals[idx]
    const next: import('@/types').WealthJournal = {
      ...cur,
      ...(data.side !== undefined ? { side: String(data.side) } : {}),
      ...(data.symbol !== undefined ? { symbol: String(data.symbol) } : {}),
      ...(data.name !== undefined ? { name: String(data.name) } : {}),
      ...(data.tradeDate !== undefined ? { tradeDate: String(data.tradeDate) } : {}),
      ...(data.price !== undefined ? { price: Number(data.price) } : {}),
      ...(data.positionPct !== undefined ? { positionPct: Number(data.positionPct) } : {}),
      ...(data.reasons !== undefined ? { reasons: data.reasons as string[] } : {}),
      ...(data.reasonNote !== undefined ? { reasonNote: String(data.reasonNote) } : {}),
      ...(data.riskNote !== undefined ? { riskNote: String(data.riskNote) } : {}),
      ...(data.stopLoss !== undefined ? { stopLoss: Number(data.stopLoss) } : {}),
      ...(data.targetPrice !== undefined ? { targetPrice: Number(data.targetPrice) } : {}),
      ...(data.emotion !== undefined ? { emotion: String(data.emotion) } : {}),
      ...(data.confidence !== undefined ? { confidence: Number(data.confidence) } : {}),
      ...(data.sleepHours !== undefined ? { sleepHours: Number(data.sleepHours) } : {}),
      ...(data.workStress !== undefined ? { workStress: Number(data.workStress) } : {}),
      ...(data.hadQuarrel !== undefined ? { hadQuarrel: !!data.hadQuarrel } : {}),
      ...(data.followedPlan !== undefined ? { followedPlan: data.followedPlan as boolean | null } : {}),
      ...(data.checklistOk !== undefined ? { checklistOk: !!data.checklistOk } : {}),
      ...(data.resultTag !== undefined ? { resultTag: String(data.resultTag) } : {}),
      ...(data.note !== undefined ? { note: String(data.note) } : {}),
      updatedAt: new Date().toISOString(),
    }
    mockState.wealthJournals[idx] = next
    return ok(next)
  },
  async deleteWealthJournal(id: string): Promise<ApiRes<{ ok: boolean }>> {
    const idx = mockState.wealthJournals.findIndex((j) => j.id === id)
    if (idx >= 0) mockState.wealthJournals.splice(idx, 1)
    return ok({ ok: true })
  },
  async getWealthReview(): Promise<ApiRes<import('@/types').WealthReview>> {
    const today = new Date().toISOString().slice(0, 10)
    return ok({
      weekStart: today,
      weekEnd: today,
      tradeCount: 0,
      buyCount: 0,
      sellCount: 0,
      winCount: 0,
      lossCount: 0,
      followedPlanCount: 0,
      brokePlanCount: 0,
      topWinReasons: [],
      topLossReasons: [],
      emotionStats: [],
      buyReasonPresets: [],
      sellReasonPresets: [],
      layerLabels: {},
    })
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
}

export { questionBank }
