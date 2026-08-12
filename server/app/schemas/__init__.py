import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MindMapNode(BaseModel):
    id: str
    title: str
    content: str | None = None
    children: list["MindMapNode"] | None = None


class ArticleSection(BaseModel):
    id: str
    title: str
    level: int
    content: str | None = None
    highlight: str | None = None
    children: list["ArticleSection"] | None = None


class ArticleOut(BaseModel):
    id: str
    title: str
    source: str
    publishDate: str
    summary: str
    sections: list[ArticleSection] = Field(default_factory=list)
    content: str
    tags: list[str]
    mindMap: MindMapNode
    readCount: int | None = None
    isFeatured: bool = False
    categoryId: str | None = None
    categoryName: str | None = None
    categoryPath: list[str] = Field(default_factory=list)
    importance: int = 3
    importanceLabel: str = "掌握"
    status: str = "published"
    allowQuiz: bool = True
    isDaily: bool = False


class CategoryOut(BaseModel):
    id: str
    name: str
    parentId: str | None = None
    sortOrder: int = 0
    children: list["CategoryOut"] = Field(default_factory=list)


class CategoryCreate(BaseModel):
    name: str
    parent_id: str | None = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = None
    parent_id: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class ArticleCreate(BaseModel):
    title: str
    source: str
    source_url: str = ""
    publish_date: str
    summary: str
    content: str = ""
    sections: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    mind_map: dict[str, Any] = Field(default_factory=dict)
    category_id: str | None = None
    importance: int = 3
    status: str = "draft"
    allow_quiz: bool = True
    is_published: bool = False
    is_daily: bool = False
    auto_generate_questions: bool = False


class ArticleInferMetadataBody(BaseModel):
    content: str = Field(min_length=1)
    title: str = ""


class ArticleInferMetadataOut(BaseModel):
    title: str
    content: str
    source: str
    source_url: str = ""
    publish_date: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    category_id: str | None = None
    category_name: str | None = None
    importance: int = 3


class ArticleUpdate(BaseModel):
    title: str | None = None
    source: str | None = None
    source_url: str | None = None
    publish_date: str | None = None
    summary: str | None = None
    content: str | None = None
    sections: list[dict[str, Any]] | None = None
    tags: list[str] | None = None
    mind_map: dict[str, Any] | None = None
    category_id: str | None = None
    importance: int | None = None
    status: str | None = None
    allow_quiz: bool | None = None
    is_published: bool | None = None
    is_daily: bool | None = None
    is_featured: bool | None = None


class QuestionOut(BaseModel):
    id: str
    articleId: str
    type: str
    stem: str
    options: list[str] | None = None
    correctAnswer: str | list[str]
    analysis: str
    sourceSentence: str
    status: str = "approved"
    origin: str = "manual"
    isActive: bool = True


class QuestionCreate(BaseModel):
    article_id: str
    type: str
    stem: str
    options: list[str] = Field(default_factory=list)
    correct_answer: str | list[str]
    analysis: str
    source_sentence: str = ""
    status: str = "approved"
    origin: str = "manual"
    is_active: bool = True


class QuestionUpdate(BaseModel):
    type: str | None = None
    stem: str | None = None
    options: list[str] | None = None
    correct_answer: str | list[str] | None = None
    analysis: str | None = None
    source_sentence: str | None = None
    status: str | None = None
    is_active: bool | None = None


class QuestionBatchApprove(BaseModel):
    question_ids: list[str] = Field(default_factory=list)


class QuestionBatchDelete(BaseModel):
    question_ids: list[str] = Field(default_factory=list)


class ArticleBatchIds(BaseModel):
    article_ids: list[str] = Field(default_factory=list)


class ArticleBatchPublish(BaseModel):
    article_ids: list[str] = Field(default_factory=list)
    approve_questions: bool = True


class ArticleBatchCategory(BaseModel):
    article_ids: list[str] = Field(default_factory=list)
    category_id: str | None = None


class AiGenerateQuestionsBody(BaseModel):
    section_ids: list[str] | None = None
    single: int = Field(default=8, ge=0, le=50)
    multiple: int = Field(default=4, ge=0, le=50)
    judge: int = Field(default=2, ge=0, le=20)


class ImportQuestionsBody(BaseModel):
    markdown: str = Field(min_length=10)
    pending: bool = True
    replace_existing: bool = False


class ImportArticleMarkdownBody(BaseModel):
    markdown: str = Field(min_length=20)
    status: str = "pending"
    category_id: str | None = None
    is_featured: bool = False
    source: str = ""
    publish_date: str = ""
    tags: list[str] = Field(default_factory=list)


class AnswerSubmit(BaseModel):
    questionId: str
    answer: str | list[str]


class AnswerResult(BaseModel):
    correct: bool
    analysis: str
    correctAnswer: str | list[str]
    pointsEarned: int


class PointsLogOut(BaseModel):
    id: str
    amount: int
    type: str
    source: str
    description: str
    createdAt: str


class RankItemOut(BaseModel):
    rank: int
    userId: str
    nickname: str
    avatar: str
    score: int
    isSelf: bool | None = None


class QuizCompleteBody(BaseModel):
    articleId: str | None = None
    mode: str = "article"
    total: int = Field(ge=1)
    correct: int = Field(ge=0)


class QuizCompleteResult(BaseModel):
    accuracy: int
    rank: int
    totalParticipants: int
    bestAccuracy: int | None = None


class QuizRankItemOut(BaseModel):
    rank: int
    userId: str
    nickname: str
    avatar: str
    accuracy: int
    correctCount: int
    totalCount: int
    isSelf: bool | None = None


class QuizStatsOut(BaseModel):
    attemptCount: int
    bestAccuracy: int
    bestCorrect: int
    bestTotal: int
    lastAccuracy: int
    rank: int
    totalParticipants: int






class UserMeOut(BaseModel):
    id: str
    username: str | None = None
    nickname: str
    avatar: str
    email: str = ""
    phone: str = ""
    isMember: bool
    points: int
    hasSignedToday: bool
    signDates: list[str]


class AppUserProfileUpdate(BaseModel):
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None


class AppUserPasswordChange(BaseModel):
    oldPassword: str
    newPassword: str
    newPasswordConfirm: str


class AppRegisterBody(BaseModel):
    username: str
    password: str
    passwordConfirm: str


class AppLoginBody(BaseModel):
    username: str
    password: str


class AppAuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserMeOut


class StudyRecordOut(BaseModel):
    articleId: str
    studyDate: str
    reviewCount: int
    lastReviewDate: str | None = None
    mastered: bool
    updatedAt: str | None = None


class SectionReadBody(BaseModel):
    articleId: str
    sectionId: str


class ReviewCompleteBody(BaseModel):
    articleId: str


class WrongRedoBody(BaseModel):
    questionId: str
    answer: str | list[str]


class AdminLogin(BaseModel):
    username: str
    password: str


class AdminToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    permissions: list[str]


class AdminUserOut(BaseModel):
    id: int
    username: str
    nickname: str
    role_code: str
    is_active: bool
    created_at: datetime
    permissions: list[str] = []


class AppUserOut(BaseModel):
    id: str
    nickname: str
    avatar: str
    points: int
    is_member: bool
    is_active: bool
    created_at: datetime


class AppUserUpdate(BaseModel):
    nickname: str | None = None
    points: int | None = None
    is_member: bool | None = None
    is_active: bool | None = None


class SettingOut(BaseModel):
    key: str
    value: str
    description: str


class SettingUpdate(BaseModel):
    value: str


class CrawlLogOut(BaseModel):
    id: int
    source: str
    status: str
    fetched_count: int
    new_count: int
    message: str
    started_at: datetime
    finished_at: datetime | None


class RoleOut(BaseModel):
    id: int
    code: str
    name: str
    permissions: list[str]


# ===== 每日学习清单 =====


class PlanTaskOut(BaseModel):
    id: str
    planDate: str
    timeSlot: str
    subject: str
    content: str
    priority: int = 3
    expectedMinutes: int
    actualMinutes: int
    status: str
    sortOrder: int
    note: str


class PlanTaskUpdate(BaseModel):
    status: str | None = None
    actualMinutes: int | None = None
    note: str | None = None


class PlanTaskCreate(BaseModel):
    planDate: str
    timeSlot: str = ""
    subject: str = ""
    content: str
    priority: int = 3
    expectedMinutes: int = 0


# ===== 学习计划模板 =====


class PlanTemplateOut(BaseModel):
    id: str
    dayType: str
    timeSlot: str
    subject: str
    content: str
    priority: int
    expectedMinutes: int
    sortOrder: int
    isActive: bool


class PlanTemplateCreate(BaseModel):
    dayType: str  # weekday | weekend
    timeSlot: str = ""
    subject: str = ""
    content: str
    priority: int = 3
    expectedMinutes: int = 0
    sortOrder: int = 0


class PlanTemplateUpdate(BaseModel):
    timeSlot: str | None = None
    subject: str | None = None
    content: str | None = None
    priority: int | None = None
    expectedMinutes: int | None = None
    sortOrder: int | None = None
    isActive: bool | None = None


class DailyReviewOut(BaseModel):
    reviewDate: str
    completion: int
    totalMinutes: int
    weakPoint: str
    tomorrowFocus: str
    mood: str
    note: str


class DailyReviewUpsert(BaseModel):
    reviewDate: str
    completion: int | None = None
    totalMinutes: int | None = None
    weakPoint: str | None = None
    tomorrowFocus: str | None = None
    mood: str | None = None
    note: str | None = None


class DayPlanOut(BaseModel):
    """单日清单 + 进度概览"""
    date: str
    isWeekend: bool
    tasks: list[PlanTaskOut]
    completion: int  # 0-100
    doneCount: int
    totalCount: int
    expectedMinutes: int
    actualMinutes: int
    review: DailyReviewOut | None = None


# ===== 知识框架 =====


class KnowledgeNodeOut(BaseModel):
    id: str
    treeKey: str
    parentId: str | None = None
    title: str
    content: str
    myNote: str = ""
    isStarred: bool = False
    masteryLevel: str = "new"
    nextReviewAt: datetime | None = None
    reviewCount: int = 0
    lastReviewedAt: datetime | None = None
    depth: int
    sortOrder: int
    path: str
    sourceFile: str = ""
    children: list["KnowledgeNodeOut"] | None = None


class KnowledgeTreeOut(BaseModel):
    treeKey: str
    title: str
    nodes: list[KnowledgeNodeOut]


class KnowledgeNodeUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    myNote: str | None = None
    isStarred: bool | None = None


class KnowledgeNodeCreate(BaseModel):
    treeKey: str
    parentId: str | None = None
    title: str
    content: str = ""


class KnowledgeReviewDueOut(BaseModel):
    dueCount: int
    candidates: list["KnowledgeReviewCardOut"] = []


class KnowledgeReviewCardOut(BaseModel):
    id: str
    title: str
    path: str
    treeKey: str
    content: str = ""
    myNote: str = ""
    masteryLevel: str = "new"
    hint: str | None = None


class KnowledgeReviewSessionBody(BaseModel):
    count: int = 5


class KnowledgeReviewSessionOut(BaseModel):
    cards: list[KnowledgeReviewCardOut]


class KnowledgeReviewAnswerBody(BaseModel):
    nodeId: str
    result: str  # again|hard|good|easy


class KnowledgeReviewAnswerOut(BaseModel):
    id: str
    masteryLevel: str
    nextReviewAt: datetime | None = None
    reviewCount: int
    lastReviewedAt: datetime | None = None


class ReviewHubOut(BaseModel):
    knowledgeDueCount: int = 0
    articleReviewCount: int = 0
    corpusInboxCount: int = 0
    articleWrongCount: int = 0
    manualWrongCount: int = 0
    wrongReviewCount: int = 0
    # 未到期错题：今日可跳过
    wrongWaitingCount: int = 0
    # 今日智能推荐题量（到期题封顶）
    wrongRecommendCount: int = 0
    # 全局复习调度：今日预算 / 今日推荐 / 积压
    todayBudget: int = 0
    todayRecommended: int = 0
    backlogCount: int = 0
    estimatedClearDays: int = 0
    reviewPlan: list[dict] = []
    totalCount: int = 0


# ===== 手动错题 =====


class ManualWrongOut(BaseModel):
    id: str
    subject: str
    questionType: str
    stem: str
    options: str
    myAnswer: str
    correctAnswer: str
    analysis: str
    wrongReason: str
    note: str
    images: list[str]
    source: str
    knowledgeNodeId: str | None = None
    knowledgeTreeKey: str = ""
    knowledgePath: str = ""
    reviewCount: int
    reviewStage: int = 0
    nextReviewAt: datetime | None = None
    due: bool = False
    mastered: bool
    lastWrongAt: datetime
    createdAt: datetime


class ManualWrongCreate(BaseModel):
    subject: str = ""
    questionType: str = ""
    stem: str = ""
    options: str = ""
    myAnswer: str = ""
    correctAnswer: str = ""
    analysis: str = ""
    wrongReason: str = ""
    note: str = ""
    source: str = "manual"  # manual | photo | ocr
    images: list[str] = []
    knowledgeNodeId: str | None = None
    knowledgeTreeKey: str = ""
    knowledgePath: str = ""


class ManualWrongUpdate(BaseModel):
    subject: str | None = None
    questionType: str | None = None
    stem: str | None = None
    options: str | None = None
    myAnswer: str | None = None
    correctAnswer: str | None = None
    analysis: str | None = None
    wrongReason: str | None = None
    note: str | None = None
    mastered: bool | None = None
    reviewCount: int | None = None
    images: list[str] | None = None
    knowledgeNodeId: str | None = None
    knowledgeTreeKey: str | None = None
    knowledgePath: str | None = None


# ===== 真题/题库模块 =====


class ExamPaperOut(BaseModel):
    id: str
    title: str
    examType: str
    subject: str
    year: int | None = None
    region: str
    level: str
    totalCount: int
    timeLimitMin: int
    tags: list[str]
    isPublished: bool
    isFree: bool
    sortOrder: int
    description: str
    createdAt: datetime


class ExamPaperCreate(BaseModel):
    title: str
    examType: str = "real"  # real | custom | mock
    subject: str = "行测"
    year: int | None = None
    region: str = ""
    level: str = ""
    timeLimitMin: int = 120
    tags: list[str] = []
    isPublished: bool = True
    isFree: bool = True
    sortOrder: int = 0
    description: str = ""


class ExamPaperUpdate(BaseModel):
    title: str | None = None
    examType: str | None = None
    subject: str | None = None
    year: int | None = None
    region: str | None = None
    level: str | None = None
    timeLimitMin: int | None = None
    tags: list[str] | None = None
    isPublished: bool | None = None
    isFree: bool | None = None
    sortOrder: int | None = None
    description: str | None = None


class ExamQuestionOut(BaseModel):
    id: str
    paperId: str
    section: str
    sectionIndex: int
    sortOrder: int
    type: str
    material: str
    stem: str
    options: list[str]
    correctAnswer: str | list[str]
    analysis: str
    difficulty: int
    knowledgeTags: list[str]
    knowledgeNodeId: str | None = None
    knowledgeTreeKey: str = ""
    knowledgePath: str = ""
    isActive: bool


class ExamQuestionCreate(BaseModel):
    section: str = ""
    sectionIndex: int = 0
    sortOrder: int = 0
    type: str = "single"
    material: str = ""
    stem: str
    options: list[str]
    correctAnswer: str | list[str]
    analysis: str = ""
    difficulty: int = 3
    knowledgeTags: list[str] = []
    knowledgeNodeId: str | None = None
    knowledgeTreeKey: str = ""
    knowledgePath: str = ""


class ExamQuestionUpdate(BaseModel):
    section: str | None = None
    sectionIndex: int | None = None
    sortOrder: int | None = None
    type: str | None = None
    material: str | None = None
    stem: str | None = None
    options: list[str] | None = None
    correctAnswer: str | list[str] | None = None
    analysis: str | None = None
    difficulty: int | None = None
    knowledgeTags: list[str] | None = None
    knowledgeNodeId: str | None = None
    knowledgeTreeKey: str | None = None
    knowledgePath: str | None = None
    isActive: bool | None = None


class ExamPaperDetailOut(BaseModel):
    """试卷详情（含所有题目，按 section 分组）"""
    id: str
    title: str
    examType: str
    subject: str
    year: int | None = None
    region: str
    level: str
    totalCount: int
    timeLimitMin: int
    tags: list[str]
    isPublished: bool
    isFree: bool
    description: str
    sections: list[dict]  # [{section, questions: [ExamQuestionOut]}]


class ExamAnswerSubmit(BaseModel):
    """单题作答提交"""
    questionId: str
    answer: str | list[str]
    timeUsedSec: int = 0
    marked: bool = False


class ExamAttemptOut(BaseModel):
    """作答记录"""
    id: str
    paperId: str
    paperTitle: str
    startedAt: datetime
    finishedAt: datetime | None
    timeUsedSec: int
    totalCount: int
    answeredCount: int
    correctCount: int
    score: int
    isFinished: bool


class ExamAttemptDetailOut(ExamAttemptOut):
    """作答详情（含每题对错）"""
    answers: list[dict]  # [{questionId, userAnswer, isCorrect, timeUsedSec, marked, stem, correctAnswer, analysis}]
    sectionStats: list[dict]  # [{section, total, correct, accuracy}]


# ===== 英语学习模块 =====












































RMRB_THEME_TAG_PRESETS = [
    "政绩观",
    "社会治理",
    "乡村振兴",
    "县域经济",
    "高质量发展",
    "民生保障",
    "作风建设",
    "基层减负",
    "科技创新",
    "文化建设",
    "生态文明",
    "依法治国",
]


class RmrbArticleOut(BaseModel):
    id: str
    title: str
    source: str
    publishDate: str
    summary: str
    content: str
    tags: list[str] = []
    isPublished: bool
    sortOrder: int
    readCount: int
    createdAt: datetime
    updatedAt: datetime


class RmrbArticleCreate(BaseModel):
    title: str
    source: str = "人民时评"
    publishDate: str = ""
    summary: str = ""
    content: str = ""
    tags: list[str] = []
    isPublished: bool = True
    sortOrder: int = 0


class RmrbArticleUpdate(BaseModel):
    title: str | None = None
    source: str | None = None
    publishDate: str | None = None
    summary: str | None = None
    content: str | None = None
    tags: list[str] | None = None
    isPublished: bool | None = None
    sortOrder: int | None = None


class ShenlunMineTermItem(BaseModel):
    term: str
    category: str = "其他"
    plainWord: str = ""


class ShenlunQuoteItem(BaseModel):
    text: str = ""
    source: str = ""  # 来源，如：清代万斯大
    meaning: str = ""  # 释义


class ShenlunVerbItem(BaseModel):
    verb: str = ""
    usage: str = ""
    category: str = "其他"


class ShenlunArgumentFieldValue(BaseModel):
    key: str
    label: str = ""
    content: str = ""


class ShenlunArgumentPoint(BaseModel):
    title: str = ""  # 分论点正文
    claim: str = ""  # 兼容旧数据
    evidence: str = ""
    summary: str = ""
    method: str = ""  # 论证方法名，如：点例排比 + 类比延伸
    methodNote: str = ""  # 方法说明
    template: str = ""  # 套用模板


class ShenlunArgumentSkeleton(BaseModel):
    templateId: str = ""
    templateName: str = ""
    mode: str = "points"  # linear | points
    overview: str = ""  # 总论点
    conclusion: str = ""  # 总结
    overviewMethod: str = ""  # 总论点论证方法
    overviewTemplate: str = ""  # 总论点论证模板
    fields: list[ShenlunArgumentFieldValue] = []
    points: list[ShenlunArgumentPoint] = []


class ShenlunTemplateItem(BaseModel):
    type: str = "dialectic"  # sentence type code
    typeName: str = ""
    original: str = ""
    template: str = ""
    imitate: str = ""


class ShenlunMineLogOut(BaseModel):
    id: str
    mineDate: str
    articleId: str | None = None
    articleTitle: str
    sourceExcerpt: str = ""
    argumentChain: str = ""
    templateSentence: str = ""
    terms: list[ShenlunMineTermItem] = []
    quotes: list[ShenlunQuoteItem] = []
    verbs: list[ShenlunVerbItem] = []
    argument: ShenlunArgumentSkeleton = ShenlunArgumentSkeleton()
    templates: list[ShenlunTemplateItem] = []
    createdAt: datetime
    updatedAt: datetime


class ShenlunMineLogUpsert(BaseModel):
    mineDate: str | None = None
    articleId: str | None = None
    articleTitle: str = ""
    sourceExcerpt: str = ""
    argumentChain: str = ""
    templateSentence: str = ""
    terms: list[ShenlunMineTermItem | str] = []
    quotes: list[ShenlunQuoteItem] = []
    verbs: list[ShenlunVerbItem] = []
    argument: ShenlunArgumentSkeleton | None = None
    templates: list[ShenlunTemplateItem] = []


class ShenlunMineLogUpdate(BaseModel):
    articleId: str | None = None
    articleTitle: str | None = None
    sourceExcerpt: str | None = None
    argumentChain: str | None = None
    templateSentence: str | None = None
    terms: list[ShenlunMineTermItem | str] | None = None
    quotes: list[ShenlunQuoteItem] | None = None
    verbs: list[ShenlunVerbItem] | None = None
    argument: ShenlunArgumentSkeleton | None = None
    templates: list[ShenlunTemplateItem] | None = None


class ShenlunSkeletonFieldDef(BaseModel):
    key: str
    label: str
    placeholder: str = ""


class ShenlunSkeletonStructure(BaseModel):
    mode: str = "linear"  # linear | points
    fields: list[ShenlunSkeletonFieldDef] = []
    overviewLabel: str = "全文总骨架"
    overviewPlaceholder: str = ""
    pointFields: list[ShenlunSkeletonFieldDef] = []


class ShenlunTermCategoryOut(BaseModel):
    id: str
    name: str
    kind: str = "term"  # term | verb
    sortOrder: int = 0
    isEnabled: bool = True


class ShenlunTermCategoryCreate(BaseModel):
    name: str
    kind: str = "term"
    sortOrder: int = 0
    isEnabled: bool = True


class ShenlunTermCategoryUpdate(BaseModel):
    name: str | None = None
    kind: str | None = None
    sortOrder: int | None = None
    isEnabled: bool | None = None


class ShenlunSkeletonTemplateOut(BaseModel):
    id: str
    name: str
    description: str = ""
    mode: str = "linear"
    structure: ShenlunSkeletonStructure
    sortOrder: int = 0
    isEnabled: bool = True


class ShenlunSkeletonTemplateCreate(BaseModel):
    name: str
    description: str = ""
    mode: str = "linear"
    structure: ShenlunSkeletonStructure | None = None
    sortOrder: int = 0
    isEnabled: bool = True


class ShenlunSkeletonTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    mode: str | None = None
    structure: ShenlunSkeletonStructure | None = None
    sortOrder: int | None = None
    isEnabled: bool | None = None


class ShenlunSentenceTypeOut(BaseModel):
    id: str
    code: str
    name: str
    tip: str = ""
    sortOrder: int = 0
    isEnabled: bool = True


class ShenlunSentenceTypeCreate(BaseModel):
    code: str
    name: str
    tip: str = ""
    sortOrder: int = 0
    isEnabled: bool = True


class ShenlunSentenceTypeUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    tip: str | None = None
    sortOrder: int | None = None
    isEnabled: bool | None = None


class ShenlunArgumentMethodOut(BaseModel):
    id: str
    name: str
    scope: str = "point"  # overview | point
    note: str = ""
    template: str = ""
    sortOrder: int = 0
    isEnabled: bool = True


class ShenlunArgumentMethodCreate(BaseModel):
    name: str
    scope: str = "point"
    note: str = ""
    template: str = ""
    sortOrder: int = 0
    isEnabled: bool = True


class ShenlunArgumentMethodUpdate(BaseModel):
    name: str | None = None
    scope: str | None = None
    note: str | None = None
    template: str | None = None
    sortOrder: int | None = None
    isEnabled: bool | None = None


class ShenlunMetaOut(BaseModel):
    termCategories: list[ShenlunTermCategoryOut] = []
    verbCategories: list[ShenlunTermCategoryOut] = []
    skeletonTemplates: list[ShenlunSkeletonTemplateOut] = []
    sentenceTypes: list[ShenlunSentenceTypeOut] = []
    argumentMethodPresets: list[ShenlunArgumentMethodOut] = []


class ShenlunNormTermOut(BaseModel):
    id: str
    term: str
    category: str = "其他"
    usageNote: str
    sourceTitle: str
    exampleSentence: str
    articleId: str | None = None
    familiarity: int
    mastered: bool
    createdAt: datetime


class ShenlunNormTermAdd(BaseModel):
    term: str
    category: str = "其他"
    usageNote: str = ""
    sourceTitle: str = ""
    exampleSentence: str = ""
    articleId: str | None = None


class ShenlunNormTermUpdate(BaseModel):
    category: str | None = None
    usageNote: str | None = None
    exampleSentence: str | None = None
    familiarity: int | None = None
    mastered: bool | None = None
    sourceTitle: str | None = None


class ShenlunStatsOut(BaseModel):
    weekMineDays: int
    weekMineTarget: int = 7
    termCount: int
    learningTermCount: int
    todayMined: bool
    weekDrillCount: int = 0


class ShenlunDrillLogOut(BaseModel):
    id: str
    drillType: str
    content: str
    prompt: str
    refMineId: str | None = None
    refTermIds: list[str] = []
    createdAt: datetime


class ShenlunDrillCreate(BaseModel):
    drillType: str  # sentence | imitate | oral
    content: str
    prompt: str = ""
    refMineId: str | None = None
    refTermIds: list[str] = []


# ===== 读书模块 =====
























class GrowthDayBar(BaseModel):
    date: str
    label: str
    minutes: int
    isToday: bool = False


class GrowthDomainProgress(BaseModel):
    key: str
    name: str
    percent: int
    detail: str = ""


class GrowthOverviewOut(BaseModel):
    signStreak: int
    signDays: int
    points: int
    weekMinutes: int
    weekQuizTotal: int
    weekQuizCorrect: int
    articleReadCount: int
    examFinishedCount: int
    weekBars: list[GrowthDayBar]
    domains: list[GrowthDomainProgress]


# ===== 健康模块 =====

























LEDGER_EXPENSE_CATEGORIES = [
    "餐饮",
    "交通",
    "日用",
    "住房",
    "学习",
    "医疗",
    "娱乐",
    "人情",
    "其他",
]

LEDGER_REPAY_METHODS = ["微信", "支付宝", "现金", "银行转账", "其他"]
























CORPUS_KINDS = ["词", "专名", "成语", "诗典", "短语", "句", "结构"]
CORPUS_SOURCE_TYPES = ["报纸", "视频", "播客", "书", "聊天", "其他"]
CORPUS_TAG_PRESETS = ["民生", "治理", "收束", "过渡", "对比", "金句", "问题", "对策", "其他"]
# 可晋升为申论规范词的类型
CORPUS_TERM_KINDS = ("词", "专名", "成语", "诗典", "短语")
CORPUS_STATUSES = ["inbox", "clarified", "owned", "used"]


class CorpusItemOut(BaseModel):
    id: str
    original: str
    kind: str = "句"
    sourceType: str = "其他"
    sourceTitle: str = ""
    tags: list[str] = []
    plainNote: str = ""
    rewrite: str = ""
    practice: str = ""
    status: str = "inbox"
    usedCount: int = 0
    promotedTermId: str | None = None
    knowledgeNodeId: str | None = None
    knowledgeTreeKey: str = ""
    knowledgePath: str = ""
    createdAt: datetime
    updatedAt: datetime


class CorpusItemCreate(BaseModel):
    original: str
    kind: str = "句"
    sourceType: str = "其他"
    sourceTitle: str = ""
    tags: list[str] = []
    plainNote: str = ""
    rewrite: str = ""
    practice: str = ""
    knowledgeNodeId: str | None = None
    knowledgeTreeKey: str = ""
    knowledgePath: str = ""


class CorpusItemUpdate(BaseModel):
    original: str | None = None
    kind: str | None = None
    sourceType: str | None = None
    sourceTitle: str | None = None
    tags: list[str] | None = None
    plainNote: str | None = None
    rewrite: str | None = None
    practice: str | None = None
    markUsed: bool | None = None
    knowledgeNodeId: str | None = None
    knowledgeTreeKey: str | None = None
    knowledgePath: str | None = None


class CorpusStatsOut(BaseModel):
    inboxCount: int = 0
    clarifiedCount: int = 0
    ownedCount: int = 0
    usedCount: int = 0
    total: int = 0
    kinds: list[str] = []
    sourceTypes: list[str] = []
    tagPresets: list[str] = []


# ===== 财富 / 投资大脑 =====

WEALTH_ASSET_KEYS = ["cash", "deposit", "fund", "stock", "other"]
WEALTH_ASSET_LABELS = {
    "cash": "现金",
    "deposit": "存款",
    "fund": "基金",
    "stock": "股票",
    "other": "其它",
}
WEALTH_LAYER_LABELS = {
    1: "硬规则（不能违反）",
    2: "股票原则",
    3: "买入条件",
    4: "卖出条件",
}
WEALTH_EMOTIONS = ["calm", "happy", "ok", "anxious", "angry"]
WEALTH_BUY_REASON_PRESETS = ["行业趋势", "基本面", "资金流入", "估值合理", "技术形态", "长期持有"]
WEALTH_SELL_REASON_PRESETS = ["达到目标", "逻辑失效", "资金需求", "情绪化", "止损", "减仓"]






























class EventImpressionOut(BaseModel):
    id: str
    title: str
    eventDate: str
    place: str
    coreContent: str
    note: str = ""
    knowledgeNodeId: str | None = None
    knowledgeTreeKey: str = ""
    knowledgePath: str = ""
    createdAt: datetime
    updatedAt: datetime


class EventImpressionCreate(BaseModel):
    title: str
    eventDate: str = ""
    place: str = ""
    coreContent: str = ""
    note: str = ""
    knowledgeNodeId: str | None = None
    knowledgeTreeKey: str = ""
    knowledgePath: str = ""


class EventImpressionUpdate(BaseModel):
    title: str | None = None
    eventDate: str | None = None
    place: str | None = None
    coreContent: str | None = None
    note: str | None = None
    knowledgeNodeId: str | None = None
    knowledgeTreeKey: str | None = None
    knowledgePath: str | None = None


class EventFrameworkGroup(BaseModel):
    treeKey: str
    path: str
    label: str
    count: int
    items: list[EventImpressionOut]


class EventHubOut(BaseModel):
    total: int = 0
    linkedCount: int = 0
    unlinkedCount: int = 0
    recentCount: int = 0  # 近 7 天
    frameworkGroups: list[EventFrameworkGroup] = []


# ===== 美剧口语训练 =====








































class ZiliaoFormulaOut(BaseModel):
    id: str
    code: str
    name: str
    category: str
    definition: str
    latex: str
    formulaPlain: str = ""
    scenarios: str
    pitfalls: str
    relatedTypeCodes: list[str] = []
    relatedTrickCodes: list[str] = []
    keywords: list[str] = []
    examFreq: int = 3
    sortOrder: int = 0
    isPublished: bool = True


class ZiliaoFormulaCreate(BaseModel):
    code: str
    name: str
    category: str = ""
    definition: str = ""
    latex: str = ""
    formulaPlain: str = ""
    scenarios: str = ""
    pitfalls: str = ""
    relatedTypeCodes: list[str] = []
    relatedTrickCodes: list[str] = []
    keywords: list[str] = []
    examFreq: int = 3
    sortOrder: int = 0
    isPublished: bool = True


class ZiliaoFormulaUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    category: str | None = None
    definition: str | None = None
    latex: str | None = None
    formulaPlain: str | None = None
    scenarios: str | None = None
    pitfalls: str | None = None
    relatedTypeCodes: list[str] | None = None
    relatedTrickCodes: list[str] | None = None
    keywords: list[str] | None = None
    examFreq: int | None = None
    sortOrder: int | None = None
    isPublished: bool | None = None


class ZiliaoFormulaImportBody(BaseModel):
    content: str
    overwrite: bool = True
    publishDefault: bool = True


class ZiliaoFormulaImportResult(BaseModel):
    total: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = []


class ZiliaoQuestionTypeOut(BaseModel):
    id: str
    code: str
    name: str
    category: str
    description: str
    ability: str
    difficulty: int = 3
    examFreq: int = 3
    formulaCodes: list[str] = []
    trickCodes: list[str] = []
    keywords: list[str] = []
    sortOrder: int = 0
    isPublished: bool = True


class ZiliaoQuestionTypeCreate(BaseModel):
    code: str
    name: str
    category: str = ""
    description: str = ""
    ability: str = ""
    difficulty: int = 3
    examFreq: int = 3
    formulaCodes: list[str] = []
    trickCodes: list[str] = []
    keywords: list[str] = []
    sortOrder: int = 0
    isPublished: bool = True


class ZiliaoQuestionTypeUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    category: str | None = None
    description: str | None = None
    ability: str | None = None
    difficulty: int | None = None
    examFreq: int | None = None
    formulaCodes: list[str] | None = None
    trickCodes: list[str] | None = None
    keywords: list[str] | None = None
    sortOrder: int | None = None
    isPublished: bool | None = None


class ZiliaoTrickOut(BaseModel):
    id: str
    code: str
    name: str
    category: str
    principle: str
    whenToUse: str
    whenNot: str
    errorNote: str
    formulaCodes: list[str] = []
    example: str
    sortOrder: int = 0
    isPublished: bool = True


class ZiliaoTrickCreate(BaseModel):
    code: str
    name: str
    category: str = ""
    principle: str = ""
    whenToUse: str = ""
    whenNot: str = ""
    errorNote: str = ""
    formulaCodes: list[str] = []
    example: str = ""
    sortOrder: int = 0
    isPublished: bool = True


class ZiliaoTrickUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    category: str | None = None
    principle: str | None = None
    whenToUse: str | None = None
    whenNot: str | None = None
    errorNote: str | None = None
    formulaCodes: list[str] | None = None
    example: str | None = None
    sortOrder: int | None = None
    isPublished: bool | None = None


class ZiliaoOverviewOut(BaseModel):
    formulaCount: int = 0
    typeCount: int = 0
    trickCount: int = 0
    drillSetCount: int = 0
    todaySets: int = 0
    todayCorrect: int = 0
    todayTotal: int = 0
    weekSets: int = 0
    hasRealDrill: bool = False
    usingSampleOnly: bool = False
    weakTypes: list["ZiliaoWeakTypeOut"] = []


class ZiliaoWeakTypeOut(BaseModel):
    id: str
    code: str
    name: str
    category: str = ""
    attemptCount: int = 0
    correctCount: int = 0
    totalCount: int = 0
    accuracy: float | None = None
    reason: str = ""


class ZiliaoDrillSetOut(BaseModel):
    setId: str
    paperId: str
    paperTitle: str
    materialPreview: str
    questionCount: int
    section: str = "资料分析"
    typeHints: list[str] = []
    isSample: bool = False


class ZiliaoDrillQuestionOut(BaseModel):
    id: str
    section: str
    sortOrder: int
    type: str
    material: str
    stem: str
    options: list[str]
    difficulty: int = 3


class ZiliaoDrillSetDetailOut(BaseModel):
    setId: str
    paperId: str
    paperTitle: str
    material: str
    questions: list[ZiliaoDrillQuestionOut]


class ZiliaoDrillAnswerItem(BaseModel):
    questionId: str
    userAnswer: str | list[str] = ""


class ZiliaoDrillSubmitIn(BaseModel):
    setId: str
    answers: list[ZiliaoDrillAnswerItem]
    timeUsedSec: int = 0
    typeCode: str = ""
    saveWrongs: bool = True


class ZiliaoDrillWrongItem(BaseModel):
    questionId: str
    stem: str
    material: str = ""
    options: list[str] = []
    userAnswer: str | list[str] = ""
    correctAnswer: str | list[str] = ""
    analysis: str = ""


class ZiliaoDrillSubmitOut(BaseModel):
    setId: str
    totalCount: int
    correctCount: int
    timeUsedSec: int
    wrongs: list[ZiliaoDrillWrongItem] = []
    savedWrongCount: int = 0
