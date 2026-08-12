import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.timezone import now


def utcnow() -> datetime:
    """当前北京时间（保留旧名避免大量改名；DB 存的就是北京时间）"""
    return now()


def gen_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    permissions: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    admins: Mapped[list["AdminUser"]] = relationship(back_populates="role")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(String(64), default="管理员")
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    role: Mapped[Role] = relationship(back_populates="admins")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("cat"))
    parent_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("categories.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    parent: Mapped["Category | None"] = relationship(remote_side="Category.id", back_populates="children")
    children: Mapped[list["Category"]] = relationship(back_populates="parent")


class AppUser(Base):
    __tablename__ = "app_users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("u"))
    username: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    openid: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    nickname: Mapped[str] = mapped_column(String(64), default="政考学员")
    avatar: Mapped[str] = mapped_column(String(512), default="")
    email: Mapped[str] = mapped_column(String(128), default="")
    phone: Mapped[str] = mapped_column(String(20), default="")
    points: Mapped[int] = mapped_column(Integer, default=0)
    is_member: Mapped[bool] = mapped_column(Boolean, default=False)
    member_expire_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    points_logs: Mapped[list["PointsLog"]] = relationship(back_populates="user")
    sign_records: Mapped[list["SignRecord"]] = relationship(back_populates="user")


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("art"))
    title: Mapped[str] = mapped_column(String(256))
    source: Mapped[str] = mapped_column(String(64))
    source_url: Mapped[str] = mapped_column(String(512), default="")
    publish_date: Mapped[str] = mapped_column(String(10))
    summary: Mapped[str] = mapped_column(String(512))
    content: Mapped[str] = mapped_column(Text)
    sections: Mapped[str] = mapped_column(Text, default="[]")  # JSON 多层级小节
    tags: Mapped[str] = mapped_column(String(256), default="[]")  # JSON
    mind_map: Mapped[str] = mapped_column(Text, default="{}")  # JSON
    category_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("categories.id"), nullable=True, index=True)
    category_path: Mapped[str] = mapped_column(Text, default="[]")  # JSON
    importance: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    status: Mapped[str] = mapped_column(String(16), default="published")
    allow_quiz: Mapped[bool] = mapped_column(Boolean, default=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    is_daily: Mapped[bool] = mapped_column(Boolean, default=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    read_count: Mapped[int] = mapped_column(Integer, default=0)
    crawled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    questions: Mapped[list["Question"]] = relationship(back_populates="article")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("q"))
    article_id: Mapped[str] = mapped_column(ForeignKey("articles.id"), index=True)
    type: Mapped[str] = mapped_column(String(16))  # single | multiple | judge
    stem: Mapped[str] = mapped_column(Text)
    options: Mapped[str] = mapped_column(Text, default="[]")  # JSON
    correct_answer: Mapped[str] = mapped_column(Text)  # JSON string or plain
    analysis: Mapped[str] = mapped_column(Text)
    source_sentence: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="approved")  # pending | approved | rejected
    origin: Mapped[str] = mapped_column(String(16), default="manual")  # crawl_auto | manual | seed | ai
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    article: Mapped[Article] = relationship(back_populates="questions")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(String(256), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class CrawlLog(Base):
    __tablename__ = "crawl_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16))  # success | failed | partial
    fetched_count: Mapped[int] = mapped_column(Integer, default=0)
    new_count: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PointsLog(Base):
    __tablename__ = "points_logs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("log"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    log_type: Mapped[str] = mapped_column(String(16))  # income | expense
    source: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped[AppUser] = relationship(back_populates="points_logs")


class SignRecord(Base):
    __tablename__ = "sign_records"
    __table_args__ = (UniqueConstraint("user_id", "sign_date", name="uq_user_sign_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    sign_date: Mapped[str] = mapped_column(String(10))
    points: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped[AppUser] = relationship(back_populates="sign_records")


class WrongAnswer(Base):
    __tablename__ = "wrong_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    wrong_count: Mapped[int] = mapped_column(Integer, default=1)
    last_wrong_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    user_answer: Mapped[str] = mapped_column(Text, default="")
    # 艾宾浩斯调度：答对推进间隔，答错重置；跑完全部间隔后移除
    review_stage: Mapped[int] = mapped_column(Integer, default=0)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class StudyRecord(Base):
    __tablename__ = "study_records"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_user_article_study"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    article_id: Mapped[str] = mapped_column(ForeignKey("articles.id"), index=True)
    study_date: Mapped[str] = mapped_column(String(10))
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    last_review_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    mastered: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class SectionRead(Base):
    __tablename__ = "section_reads"
    __table_args__ = (UniqueConstraint("user_id", "article_id", "section_id", name="uq_user_section_read"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    article_id: Mapped[str] = mapped_column(ForeignKey("articles.id"), index=True)
    section_id: Mapped[str] = mapped_column(String(64))
    read_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("qa"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    article_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("articles.id"), nullable=True, index=True)
    quiz_mode: Mapped[str] = mapped_column(String(16), default="article")
    total_count: Mapped[int] = mapped_column(Integer)
    correct_count: Mapped[int] = mapped_column(Integer)
    accuracy: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class RechargePackage(Base):
    __tablename__ = "recharge_packages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("pkg"))
    label: Mapped[str] = mapped_column(String(32))
    points: Mapped[int] = mapped_column(Integer)
    price: Mapped[int] = mapped_column(Integer)  # 分
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class PlanTask(Base):
    """每日学习清单任务"""
    __tablename__ = "plan_tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("pt"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    plan_date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    time_slot: Mapped[str] = mapped_column(String(32), default="")  # 如 "06:45-07:45"
    subject: Mapped[str] = mapped_column(String(32), default="")  # 行测/申论/英语/健身/阅读
    content: Mapped[str] = mapped_column(String(256))
    priority: Mapped[int] = mapped_column(Integer, default=3)  # 1-5，重要级
    expected_minutes: Mapped[int] = mapped_column(Integer, default=0)
    actual_minutes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending | done | skipped
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class PlanTemplate(Base):
    """每日清单模板（后台维护，工作日/周末两套）"""
    __tablename__ = "plan_templates"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("plt"))
    day_type: Mapped[str] = mapped_column(String(16), index=True)  # weekday | weekend
    time_slot: Mapped[str] = mapped_column(String(32), default="")
    subject: Mapped[str] = mapped_column(String(32), default="")
    content: Mapped[str] = mapped_column(String(256))
    priority: Mapped[int] = mapped_column(Integer, default=3)
    expected_minutes: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class DailyReview(Base):
    """每日复盘"""
    __tablename__ = "daily_reviews"
    __table_args__ = (UniqueConstraint("user_id", "review_date", name="uq_user_review_date"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("dr"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    review_date: Mapped[str] = mapped_column(String(10))
    completion: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    total_minutes: Mapped[int] = mapped_column(Integer, default=0)
    weak_point: Mapped[str] = mapped_column(Text, default="")
    tomorrow_focus: Mapped[str] = mapped_column(Text, default="")
    mood: Mapped[str] = mapped_column(String(16), default="")  # good/ok/bad
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class KnowledgeNode(Base):
    """知识框架节点（由 Obsidian md 解析而来）"""
    __tablename__ = "knowledge_nodes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("kn"))
    tree_key: Mapped[str] = mapped_column(String(32), index=True)  # 如 "申论"、"判断推理"
    parent_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("knowledge_nodes.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(256))
    content: Mapped[str] = mapped_column(Text, default="")
    my_note: Mapped[str] = mapped_column(Text, default="")  # 用户在App/后台加的备注，同步时按 path 保留
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False)  # 标记重点
    # App 侧掌握度（Obsidian 同步时按 path 保留，不覆盖）
    mastery_level: Mapped[str] = mapped_column(String(16), default="new")  # new|learning|familiar|mastered
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    path: Mapped[str] = mapped_column(Text, default="")  # 父链路 "申论/题型/归纳概括题"
    source_file: Mapped[str] = mapped_column(String(128), default="")
    source_line: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ManualWrong(Base):
    """手动录入的错题（行测刷题，区别于App自动生成的 WrongAnswer）"""
    __tablename__ = "manual_wrongs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("mw"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    subject: Mapped[str] = mapped_column(String(32), default="")  # 常识/言语/数量/判断/资料/申论
    question_type: Mapped[str] = mapped_column(String(64), default="")
    stem: Mapped[str] = mapped_column(Text, default="")
    options: Mapped[str] = mapped_column(Text, default="")  # 文本
    my_answer: Mapped[str] = mapped_column(Text, default="")
    correct_answer: Mapped[str] = mapped_column(Text, default="")
    analysis: Mapped[str] = mapped_column(Text, default="")
    wrong_reason: Mapped[str] = mapped_column(String(64), default="")  # 粗心/方法不会/知识点盲/时间不够
    note: Mapped[str] = mapped_column(Text, default="")
    images: Mapped[str] = mapped_column(Text, default="[]")  # JSON array of URL
    source: Mapped[str] = mapped_column(String(32), default="manual")  # manual | photo | ocr
    # 关联知识框架（可选；path + tree_key 在节点重同步后可重绑 id）
    knowledge_node_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    knowledge_tree_key: Mapped[str] = mapped_column(String(32), default="")
    knowledge_path: Mapped[str] = mapped_column(Text, default="")  # 节点 path，如 选词填空/词语辨析
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    review_stage: Mapped[int] = mapped_column(Integer, default=0)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    mastered: Mapped[bool] = mapped_column(Boolean, default=False)
    last_wrong_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


# ===== 真题/题库模块 =====


class ExamPaper(Base):
    """试卷（真题 / 自定义 / 模拟卷）"""
    __tablename__ = "exam_papers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("paper"))
    title: Mapped[str] = mapped_column(String(128))
    exam_type: Mapped[str] = mapped_column(String(16), default="real")  # real | custom | mock
    subject: Mapped[str] = mapped_column(String(32), default="行测")  # 行测 / 申论 / 公基
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    region: Mapped[str] = mapped_column(String(64), default="")  # 国考 / 江苏 / 山东
    level: Mapped[str] = mapped_column(String(32), default="")  # 省级 / 地市级
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    time_limit_min: Mapped[int] = mapped_column(Integer, default=120)
    source_url: Mapped[str] = mapped_column(String(512), default="")
    tags: Mapped[str] = mapped_column(String(256), default="[]")  # JSON
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ExamQuestion(Base):
    """试卷题目（独立于 Question，避免污染原模型）"""
    __tablename__ = "exam_questions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("eq"))
    paper_id: Mapped[str] = mapped_column(ForeignKey("exam_papers.id"), index=True)
    section: Mapped[str] = mapped_column(String(32), default="")  # 常识判断 / 言语理解 / 数量关系 / 判断推理 / 资料分析
    section_index: Mapped[int] = mapped_column(Integer, default=0)  # 在该模块内的序号 1-20
    sort_order: Mapped[int] = mapped_column(Integer, default=0)  # 整卷顺序 1-135
    type: Mapped[str] = mapped_column(String(16), default="single")  # single | multiple | judge
    material: Mapped[str] = mapped_column(Text, default="")  # 共享材料（资料分析/逻辑题）
    stem: Mapped[str] = mapped_column(Text)
    options: Mapped[str] = mapped_column(Text, default="[]")  # JSON
    correct_answer: Mapped[str] = mapped_column(Text)  # JSON string or plain
    analysis: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    knowledge_tags: Mapped[str] = mapped_column(String(256), default="[]")  # JSON 旧标签，过渡用
    knowledge_node_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    knowledge_tree_key: Mapped[str] = mapped_column(String(32), default="")
    knowledge_path: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ExamAttempt(Base):
    """整卷作答记录"""
    __tablename__ = "exam_attempts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("ea"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    paper_id: Mapped[str] = mapped_column(ForeignKey("exam_papers.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    time_used_sec: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    answered_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[int] = mapped_column(Integer, default=0)
    is_finished: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ExamAnswer(Base):
    """每题作答明细"""
    __tablename__ = "exam_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("exam_attempts.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("exam_questions.id"), index=True)
    user_answer: Mapped[str] = mapped_column(Text, default="")  # JSON
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    time_used_sec: Mapped[int] = mapped_column(Integer, default=0)
    marked: Mapped[bool] = mapped_column(Boolean, default=False)  # 考生标记存疑
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


# ===== 英语学习模块 =====


class EnglishArticle(Base):
    """英文文章（带生词高亮）"""
    __tablename__ = "english_articles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("enart"))
    title: Mapped[str] = mapped_column(String(256))
    source: Mapped[str] = mapped_column(String(64), default="")  # BBC / VOA / China Daily
    level: Mapped[str] = mapped_column(String(8), default="B1")  # A2/B1/B2/C1
    content: Mapped[str] = mapped_column(Text)
    vocab_highlights: Mapped[str] = mapped_column(Text, default="[]")  # JSON [{word, meaning, pos, sentence}]
    audio_url: Mapped[str] = mapped_column(String(512), default="")
    tags: Mapped[str] = mapped_column(String(256), default="[]")  # JSON
    difficulty: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    read_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class UserVocab(Base):
    """用户生词本"""
    __tablename__ = "user_vocabs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("uv"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    word: Mapped[str] = mapped_column(String(128), index=True)
    phonetic: Mapped[str] = mapped_column(String(128), default="")  # 音标
    meaning: Mapped[str] = mapped_column(String(256), default="")  # 中文释义
    pos: Mapped[str] = mapped_column(String(32), default="")  # 词性 n/v/adj
    example_sentence: Mapped[str] = mapped_column(Text, default="")
    article_id: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 来源文章
    familiarity: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    mastered: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class UserSpeakingSentence(Base):
    """用户跟读本（从文章收藏的句子）"""
    __tablename__ = "user_speaking_sentences"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("uss"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    sentence: Mapped[str] = mapped_column(Text)
    note: Mapped[str] = mapped_column(Text, default="")
    article_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    article_title: Mapped[str] = mapped_column(String(256), default="")
    recording_url: Mapped[str] = mapped_column(String(512), default="")
    practice_count: Mapped[int] = mapped_column(Integer, default=0)
    last_practice_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class SpeakingLesson(Base):
    """口语课程（可选精品课，日常跟读走 UserSpeakingSentence）"""
    __tablename__ = "speaking_lessons"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("spk"))
    title: Mapped[str] = mapped_column(String(128))
    topic: Mapped[str] = mapped_column(String(32), default="daily")  # daily/work/travel/exam
    level: Mapped[str] = mapped_column(String(8), default="B1")
    dialogue: Mapped[str] = mapped_column(Text, default="[]")  # JSON [{speaker, en, zh}]
    key_sentences: Mapped[str] = mapped_column(Text, default="[]")  # JSON [{en, zh, pattern}]
    tips: Mapped[str] = mapped_column(Text, default="")
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SpeakingAttempt(Base):
    """口语练习记录"""
    __tablename__ = "speaking_attempts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("spa"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("speaking_lessons.id"), index=True)
    recording_url: Mapped[str] = mapped_column(String(512), default="")
    self_rating: Mapped[int] = mapped_column(Integer, default=0)  # 1-5
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class GrammarLesson(Base):
    """语法课程"""
    __tablename__ = "grammar_lessons"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("gm"))
    title: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(32), default="")  # 时态/从句/虚拟语气/句式
    level: Mapped[str] = mapped_column(String(8), default="B1")
    explanation: Mapped[str] = mapped_column(Text, default="")
    examples: Mapped[str] = mapped_column(Text, default="[]")  # JSON [{en, zh}]
    common_mistakes: Mapped[str] = mapped_column(Text, default="[]")  # JSON [{wrong, correct, note}]
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class GrammarProgress(Base):
    """语法学习进度"""
    __tablename__ = "grammar_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_grammar_lesson"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("gmp"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("grammar_lessons.id"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="learning")  # learning | mastered
    last_study_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class EnglishStudyLog(Base):
    """英语学习记录统一表"""
    __tablename__ = "english_study_logs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("enlog"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    log_type: Mapped[str] = mapped_column(String(16), default="article")  # article/speaking/grammar/vocab/phonetic
    ref_id: Mapped[str] = mapped_column(String(32), default="")
    duration_sec: Mapped[int] = mapped_column(Integer, default=0)
    words_learned: Mapped[int] = mapped_column(Integer, default=0)
    sentences_practiced: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str] = mapped_column(Text, default="")
    study_date: Mapped[str] = mapped_column(String(10), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


# ===== 音标学习（DJ 音标体系） =====


class PhoneticLesson(Base):
    """英语音标（DJ 体系 48 个）"""
    __tablename__ = "phonetic_lessons"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("ph"))
    symbol: Mapped[str] = mapped_column(String(16))  # 如 /iː/、/æ/、/p/
    category: Mapped[str] = mapped_column(String(16), default="consonant")  # unit_vowel / diphthong / consonant
    description: Mapped[str] = mapped_column(Text, default="")  # 发音说明
    mouth_shape: Mapped[str] = mapped_column(Text, default="")  # 口型/舌位说明
    tips: Mapped[str] = mapped_column(Text, default="")  # 发音技巧
    example_words: Mapped[str] = mapped_column(Text, default="[]")  # JSON [{word, meaning}]
    common_spellings: Mapped[str] = mapped_column(Text, default="[]")  # JSON 常见拼写字母组合 ["ee","ea"]
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class PhoneticProgress(Base):
    """音标学习进度"""
    __tablename__ = "phonetic_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_phonetic_lesson"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("php"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("phonetic_lessons.id"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="learning")  # learning | mastered
    practiced_count: Mapped[int] = mapped_column(Integer, default=0)
    last_practice_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


# ===== 美剧口语训练 =====


class TvShow(Base):
    """美剧 · 用户自建剧目"""
    __tablename__ = "tv_shows"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("tvs"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    title: Mapped[str] = mapped_column(String(128))
    stage: Mapped[str] = mapped_column(String(16), default="beginner")  # beginner/intermediate/advanced
    reason: Mapped[str] = mapped_column(Text, default="")  # 为何选这部
    note: Mapped[str] = mapped_column(Text, default="")
    cover_url: Mapped[str] = mapped_column(String(512), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class TvEpisode(Base):
    """美剧 · 某一集"""
    __tablename__ = "tv_episodes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("tve"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    show_id: Mapped[str] = mapped_column(ForeignKey("tv_shows.id"), index=True)
    season: Mapped[int] = mapped_column(Integer, default=1)
    episode: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(256), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="todo")  # todo/learning/done
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class TvScene(Base):
    """美剧 · 精学片段（3~5 分钟）"""
    __tablename__ = "tv_scenes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("tvsc"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    episode_id: Mapped[str] = mapped_column(ForeignKey("tv_episodes.id"), index=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    time_range: Mapped[str] = mapped_column(String(64), default="")  # 如 12:30-15:00
    scene_summary: Mapped[str] = mapped_column(Text, default="")  # 一句话场景
    target_count: Mapped[int] = mapped_column(Integer, default=3)  # 目标句型数
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class TvDialogueLine(Base):
    """美剧 · 场景对白"""
    __tablename__ = "tv_dialogue_lines"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("tvdl"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    scene_id: Mapped[str] = mapped_column(ForeignKey("tv_scenes.id"), index=True)
    speaker: Mapped[str] = mapped_column(String(64), default="")
    en: Mapped[str] = mapped_column(Text, default="")
    zh: Mapped[str] = mapped_column(Text, default="")
    phonetic_note: Mapped[str] = mapped_column(Text, default="")  # 连读/弱读
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class TvExpression(Base):
    """美剧 · 万能口语句型卡（用户级 + SRS）"""
    __tablename__ = "tv_expressions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("tvex"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    scene_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    episode_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    show_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    phrase: Mapped[str] = mapped_column(Text, default="")
    meaning: Mapped[str] = mapped_column(Text, default="")
    usage_scene: Mapped[str] = mapped_column(Text, default="")  # 使用场景
    similar: Mapped[str] = mapped_column(Text, default="")  # 类似表达
    my_example: Mapped[str] = mapped_column(Text, default="")
    life_use: Mapped[str] = mapped_column(Text, default="")
    source_line: Mapped[str] = mapped_column(Text, default="")  # 来源原句
    review_stage: Mapped[int] = mapped_column(Integer, default=0)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    mastered: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class TvStudySession(Base):
    """美剧 · 场景精学会话（步骤勾选）"""
    __tablename__ = "tv_study_sessions"
    __table_args__ = (
        UniqueConstraint("user_id", "scene_id", "study_date", name="uq_tv_session_user_scene_date"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("tvss"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    scene_id: Mapped[str] = mapped_column(ForeignKey("tv_scenes.id"), index=True)
    episode_id: Mapped[str] = mapped_column(String(32), default="", index=True)
    study_date: Mapped[str] = mapped_column(String(10), index=True)
    step_blind: Mapped[bool] = mapped_column(Boolean, default=False)
    step_parse: Mapped[bool] = mapped_column(Boolean, default=False)
    step_shadow: Mapped[bool] = mapped_column(Boolean, default=False)
    step_retell: Mapped[bool] = mapped_column(Boolean, default=False)
    step_review: Mapped[bool] = mapped_column(Boolean, default=False)
    blind_note: Mapped[str] = mapped_column(Text, default="")
    retell_text: Mapped[str] = mapped_column(Text, default="")
    retell_seconds: Mapped[int] = mapped_column(Integer, default=0)
    duration_sec: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class RmrbArticle(Base):
    """人民日报模块 · 时评/评论文章（独立于首页文章流）"""
    __tablename__ = "rmrb_articles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("rmrb"))
    title: Mapped[str] = mapped_column(String(256))
    source: Mapped[str] = mapped_column(String(64), default="人民时评")  # 人民时评 / 评论
    publish_date: Mapped[str] = mapped_column(String(10), default="")  # YYYY-MM-DD
    summary: Mapped[str] = mapped_column(String(512), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    # 主题标签 JSON 数组，如 ["政绩观","乡村振兴"]
    tags: Mapped[str] = mapped_column(Text, default="[]")
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    read_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ShenlunMineLog(Base):
    """人民日报模块 · 开采本：一日一行（三刀解剖）"""
    __tablename__ = "shenlun_mine_logs"
    __table_args__ = (UniqueConstraint("user_id", "mine_date", name="uq_user_mine_date"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("sml"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    mine_date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    article_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    article_title: Mapped[str] = mapped_column(String(256), default="")
    source_excerpt: Mapped[str] = mapped_column(Text, default="")
    argument_chain: Mapped[str] = mapped_column(Text, default="")  # 总骨架摘要（兼容）
    template_sentence: Mapped[str] = mapped_column(Text, default="")  # 句式摘要（兼容）
    terms_json: Mapped[str] = mapped_column(Text, default="[]")  # JSON [{term,category,plainWord}]
    argument_json: Mapped[str] = mapped_column(Text, default="{}")  # JSON {overview,points[],...}
    templates_json: Mapped[str] = mapped_column(Text, default="[]")  # JSON [{type,original,template,imitate}]
    quotes_json: Mapped[str] = mapped_column(Text, default="[]")  # JSON [{text,source}] 经典金句
    verbs_json: Mapped[str] = mapped_column(Text, default="[]")  # JSON [{verb,usage,category}] 高频动词
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ShenlunNormTerm(Base):
    """申论规范词库（分类积累）"""
    __tablename__ = "shenlun_norm_terms"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("snt"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    term: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(32), default="其他")  # 发展理念/战略方法/...
    usage_note: Mapped[str] = mapped_column(String(256), default="")  # 兼容旧数据；新流程不再填写
    source_title: Mapped[str] = mapped_column(String(256), default="")
    example_sentence: Mapped[str] = mapped_column(Text, default="")
    article_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    familiarity: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    mastered: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ShenlunDrillLog(Base):
    """阶梯训练记录：造句 / 仿写 / 口述"""
    __tablename__ = "shenlun_drill_logs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("sdl"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    drill_type: Mapped[str] = mapped_column(String(16), index=True)  # sentence | imitate | oral
    content: Mapped[str] = mapped_column(Text, default="")
    prompt: Mapped[str] = mapped_column(Text, default="")  # 抽到的词/句式提示
    ref_mine_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ref_term_ids: Mapped[str] = mapped_column(Text, default="[]")  # JSON list[str]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ShenlunTermCategory(Base):
    """规范词 / 动词分类（后台与移动端可维护）"""
    __tablename__ = "shenlun_term_categories"
    __table_args__ = (UniqueConstraint("kind", "name", name="uq_shenlun_cat_kind_name"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("stc"))
    name: Mapped[str] = mapped_column(String(32), index=True)
    kind: Mapped[str] = mapped_column(String(16), default="term", index=True)  # term | verb
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ShenlunSkeletonTemplate(Base):
    """论证骨架模版（总分论点 / 问题-原因-对策 等）"""
    __tablename__ = "shenlun_skeleton_templates"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("skt"))
    name: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str] = mapped_column(String(256), default="")
    mode: Mapped[str] = mapped_column(String(16), default="linear")  # linear | points
    structure_json: Mapped[str] = mapped_column(Text, default="{}")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ShenlunSentenceType(Base):
    """万能句式类型（后台可维护，三刀第三刀下拉）"""
    __tablename__ = "shenlun_sentence_types"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("sst"))
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    tip: Mapped[str] = mapped_column(String(128), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ShenlunArgumentMethod(Base):
    """具体论证方法预设（后台可维护，三刀第二刀论证方法下拉）"""
    __tablename__ = "shenlun_argument_methods"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("sam"))
    name: Mapped[str] = mapped_column(String(128), index=True)
    scope: Mapped[str] = mapped_column(String(16), default="point")  # overview | point
    note: Mapped[str] = mapped_column(String(256), default="")
    template: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class DushuBook(Base):
    """读书模块 · 用户书架"""
    __tablename__ = "dushu_books"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("dbk"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    title: Mapped[str] = mapped_column(String(128))
    author: Mapped[str] = mapped_column(String(64), default="")
    category: Mapped[str] = mapped_column(String(16), default="历史")  # 历史/社会/心理/统计/文学/哲学/其他
    status: Mapped[str] = mapped_column(String(16), default="reading")  # reading|wishlist|done
    current_chapter: Mapped[str] = mapped_column(String(128), default="")
    cover_note: Mapped[str] = mapped_column(String(256), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class DushuDailyLog(Base):
    """读书模块 · 每日阅读输出卡"""
    __tablename__ = "dushu_daily_logs"
    __table_args__ = (UniqueConstraint("user_id", "log_date", "book_id", name="uq_dushu_user_date_book"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("ddl"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    book_id: Mapped[str] = mapped_column(ForeignKey("dushu_books.id"), index=True)
    log_date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    chapter: Mapped[str] = mapped_column(String(128), default="")
    goal: Mapped[str] = mapped_column(String(256), default="")  # 今天想搞懂什么
    output_json: Mapped[str] = mapped_column(Text, default="{}")  # 按类型模板
    oral_note: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[str] = mapped_column(String(256), default="")
    duration_min: Mapped[int] = mapped_column(Integer, default=60)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class DushuPersonCard(Base):
    """读书模块 · 历史人物卡"""
    __tablename__ = "dushu_person_cards"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("dpc"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    book_id: Mapped[str] = mapped_column(ForeignKey("dushu_books.id"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    trait: Mapped[str] = mapped_column(String(64), default="")  # 核心性格一词
    success: Mapped[str] = mapped_column(Text, default="")  # 成功决策
    failure: Mapped[str] = mapped_column(Text, default="")  # 致命失误
    lesson: Mapped[str] = mapped_column(Text, default="")  # 可用道理
    tags: Mapped[str] = mapped_column(String(256), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class DushuBookSummary(Base):
    """读书模块 · 一书一页"""
    __tablename__ = "dushu_book_summaries"
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_dushu_user_book_summary"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("dbs"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    book_id: Mapped[str] = mapped_column(ForeignKey("dushu_books.id"), index=True)
    core_question: Mapped[str] = mapped_column(String(256), default="")
    skeleton: Mapped[str] = mapped_column(Text, default="")  # 论证/章节逻辑链
    insights_json: Mapped[str] = mapped_column(Text, default="[]")  # 最多3条
    story: Mapped[str] = mapped_column(Text, default="")  # 最触动案例
    model: Mapped[str] = mapped_column(Text, default="")  # 可迁移模型
    action: Mapped[str] = mapped_column(Text, default="")  # 行动启发
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class HealthUserState(Base):
    """健康模块 · 用户阶段进度"""
    __tablename__ = "health_user_states"

    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), primary_key=True)
    program_start_date: Mapped[str] = mapped_column(String(10), default="")  # YYYY-MM-DD
    private_focus: Mapped[str] = mapped_column(Text, default="")  # 用户自填关注点摘要
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class HealthDailyLog(Base):
    """健康模块 · 每日打卡（心理/身体/习惯合一）"""
    __tablename__ = "health_daily_logs"
    __table_args__ = (UniqueConstraint("user_id", "log_date", name="uq_health_user_date"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("hdl"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    log_date: Mapped[str] = mapped_column(String(10), index=True)

    # 习惯
    mood: Mapped[int] = mapped_column(Integer, default=0)  # 1-10, 0=未填
    sleep_quality: Mapped[int] = mapped_column(Integer, default=0)  # 1-5
    sleep_before_23: Mapped[bool] = mapped_column(Boolean, default=False)
    meals_regular: Mapped[bool] = mapped_column(Boolean, default=False)
    meals_light: Mapped[bool] = mapped_column(Boolean, default=False)
    weekend_lie_flat: Mapped[bool] = mapped_column(Boolean, default=False)
    habit_note: Mapped[str] = mapped_column(Text, default="")
    # 详细饮食 / 排便清单（JSON）
    meals_json: Mapped[str] = mapped_column(Text, default="{}")
    stool_json: Mapped[str] = mapped_column(Text, default="{}")

    # 身体
    stomach: Mapped[int] = mapped_column(Integer, default=0)  # 1-10 越高越舒服
    dampness: Mapped[int] = mapped_column(Integer, default=0)  # 湿气主观感
    skin: Mapped[int] = mapped_column(Integer, default=0)  # 湿疹/皮炎严重度
    skin_itch: Mapped[bool] = mapped_column(Boolean, default=False)
    skin_flare: Mapped[bool] = mapped_column(Boolean, default=False)
    walk_min: Mapped[int] = mapped_column(Integer, default=0)
    body_note: Mapped[str] = mapped_column(Text, default="")

    # 心理
    anxiety: Mapped[int] = mapped_column(Integer, default=0)
    energy: Mapped[int] = mapped_column(Integer, default=0)  # 心理能量
    social_count: Mapped[int] = mapped_column(Integer, default=0)
    study_min: Mapped[int] = mapped_column(Integer, default=0)

    tasks_done_json: Mapped[str] = mapped_column(Text, default="[]")
    cbt_json: Mapped[str] = mapped_column(Text, default="{}")
    rumination_json: Mapped[str] = mapped_column(Text, default="{}")
    review_json: Mapped[str] = mapped_column(Text, default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class LedgerExpense(Base):
    """记账 · 日常支出"""
    __tablename__ = "ledger_expenses"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("lex"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, default=0)  # 分
    occur_date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    category: Mapped[str] = mapped_column(String(32), default="其他")
    note: Mapped[str] = mapped_column(Text, default="")
    images_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class LedgerLoan(Base):
    """记账 · 出借主单"""
    __tablename__ = "ledger_loans"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("lln"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    counterparty: Mapped[str] = mapped_column(String(64), default="")
    principal_cents: Mapped[int] = mapped_column(Integer, default=0)
    lend_date: Mapped[str] = mapped_column(String(10), index=True)
    due_date: Mapped[str] = mapped_column(String(10), default="")
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)  # open | settled
    note: Mapped[str] = mapped_column(Text, default="")
    voucher_images_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class LedgerRepayment(Base):
    """记账 · 归还流水"""
    __tablename__ = "ledger_repayments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("lrp"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    loan_id: Mapped[str] = mapped_column(ForeignKey("ledger_loans.id"), index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, default=0)
    repay_date: Mapped[str] = mapped_column(String(10), index=True)
    method: Mapped[str] = mapped_column(String(32), default="微信")
    note: Mapped[str] = mapped_column(Text, default="")
    voucher_images_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class EventImpression(Base):
    """时事新闻 · 事件印象（挂知识框架，加深考点联系）"""
    __tablename__ = "event_impressions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("ei"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    event_date: Mapped[str] = mapped_column(String(10), default="", index=True)  # YYYY-MM-DD
    place: Mapped[str] = mapped_column(String(128), default="")
    core_content: Mapped[str] = mapped_column(Text, default="")  # 核心印象/要点
    note: Mapped[str] = mapped_column(Text, default="")  # 补充联想（可选）
    # 挂知识框架：如 常识判断 / 航天常识/神舟系列
    knowledge_node_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    knowledge_tree_key: Mapped[str] = mapped_column(String(64), default="", index=True)
    knowledge_path: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class CorpusItem(Base):
    """语料本 · 跨来源词句素材（捕获 → 内化 → 运用）"""
    __tablename__ = "corpus_items"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("cps"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    original: Mapped[str] = mapped_column(Text, default="")  # 原文
    kind: Mapped[str] = mapped_column(String(16), default="句")  # 词|专名|成语|诗典|短语|句|结构
    source_type: Mapped[str] = mapped_column(String(16), default="其他")  # 报纸|视频|…
    source_title: Mapped[str] = mapped_column(String(256), default="")
    tags_json: Mapped[str] = mapped_column(Text, default="[]")  # 场景标签
    plain_note: Mapped[str] = mapped_column(Text, default="")  # 白话解释
    rewrite: Mapped[str] = mapped_column(Text, default="")  # 我的改写
    practice: Mapped[str] = mapped_column(Text, default="")  # 仿写/造句
    status: Mapped[str] = mapped_column(String(16), default="inbox", index=True)  # inbox|clarified|owned|used
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    promoted_term_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # 挂知识框架：专名/语料归入考点树，便于串联复习
    knowledge_node_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    knowledge_tree_key: Mapped[str] = mapped_column(String(64), default="", index=True)
    knowledge_path: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class WealthSnapshot(Base):
    """财富 · 资产快照（手动录入）"""
    __tablename__ = "wealth_snapshots"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("wsp"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    snap_date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    cash_cents: Mapped[int] = mapped_column(Integer, default=0)
    deposit_cents: Mapped[int] = mapped_column(Integer, default=0)
    fund_cents: Mapped[int] = mapped_column(Integer, default=0)
    stock_cents: Mapped[int] = mapped_column(Integer, default=0)
    other_cents: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class WealthPrinciple(Base):
    """财富 · 投资原则（分层方法论）"""
    __tablename__ = "wealth_principles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("wpr"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    layer: Mapped[int] = mapped_column(Integer, default=1, index=True)  # 1硬规则 2股票 3买入 4卖出
    title: Mapped[str] = mapped_column(String(128), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class WealthJournal(Base):
    """财富 · 投资日志（记录为什么买卖，而非成交撮合）"""
    __tablename__ = "wealth_journals"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("wjn"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    side: Mapped[str] = mapped_column(String(8), default="buy", index=True)  # buy | sell
    symbol: Mapped[str] = mapped_column(String(32), default="")
    name: Mapped[str] = mapped_column(String(64), default="")
    trade_date: Mapped[str] = mapped_column(String(10), index=True)
    price: Mapped[float] = mapped_column(default=0.0)  # 元
    position_pct: Mapped[float] = mapped_column(default=0.0)  # 仓位 %
    reasons_json: Mapped[str] = mapped_column(Text, default="[]")  # 买入/卖出原因标签
    reason_note: Mapped[str] = mapped_column(Text, default="")
    risk_note: Mapped[str] = mapped_column(Text, default="")
    stop_loss: Mapped[float] = mapped_column(default=0.0)
    target_price: Mapped[float] = mapped_column(default=0.0)
    emotion: Mapped[str] = mapped_column(String(16), default="normal")  # calm|happy|ok|anxious|angry
    confidence: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    sleep_hours: Mapped[float] = mapped_column(default=0.0)
    work_stress: Mapped[int] = mapped_column(Integer, default=0)  # 0-5
    had_quarrel: Mapped[bool] = mapped_column(Boolean, default=False)
    followed_plan: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    checklist_ok: Mapped[bool] = mapped_column(Boolean, default=False)  # 冷静期清单已确认
    result_tag: Mapped[str] = mapped_column(String(16), default="")  # win|loss|pending|""
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


# ===== 资料分析教学资源 + 专项刷题 =====


class ZiliaoFormula(Base):
    """资料分析 · 公式库"""
    __tablename__ = "ziliao_formulas"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("zf"))
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # F001
    name: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(32), default="")  # 增长/比重/倍数/...
    definition: Mapped[str] = mapped_column(Text, default="")
    latex: Mapped[str] = mapped_column(Text, default="")  # KaTeX / LaTeX 源码
    formula_plain: Mapped[str] = mapped_column(Text, default="")  # 中文可读式，兜底展示
    scenarios: Mapped[str] = mapped_column(Text, default="")  # 适用场景
    pitfalls: Mapped[str] = mapped_column(Text, default="")  # 易错点
    related_type_codes: Mapped[str] = mapped_column(Text, default="[]")  # JSON [type codes]
    related_trick_codes: Mapped[str] = mapped_column(Text, default="[]")  # JSON
    keywords: Mapped[str] = mapped_column(Text, default="[]")  # JSON
    exam_freq: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ZiliaoQuestionType(Base):
    """资料分析 · 题型模型"""
    __tablename__ = "ziliao_question_types"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("zt"))
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # T001
    name: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(32), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    ability: Mapped[str] = mapped_column(Text, default="")  # 考查能力
    difficulty: Mapped[int] = mapped_column(Integer, default=3)
    exam_freq: Mapped[int] = mapped_column(Integer, default=3)
    formula_codes: Mapped[str] = mapped_column(Text, default="[]")  # JSON
    trick_codes: Mapped[str] = mapped_column(Text, default="[]")  # JSON
    keywords: Mapped[str] = mapped_column(Text, default="[]")  # 用于材料组弱匹配
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ZiliaoTrick(Base):
    """资料分析 · 速算技巧"""
    __tablename__ = "ziliao_tricks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("zk"))
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # K001
    name: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(32), default="")
    principle: Mapped[str] = mapped_column(Text, default="")
    when_to_use: Mapped[str] = mapped_column(Text, default="")
    when_not: Mapped[str] = mapped_column(Text, default="")
    error_note: Mapped[str] = mapped_column(Text, default="")
    formula_codes: Mapped[str] = mapped_column(Text, default="[]")  # JSON
    example: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ZiliaoPracticeLog(Base):
    """资料分析 · 材料组练习记录"""
    __tablename__ = "ziliao_practice_logs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("zpl"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    set_id: Mapped[str] = mapped_column(String(64), index=True)
    paper_id: Mapped[str] = mapped_column(String(32), default="")
    type_code: Mapped[str] = mapped_column(String(32), default="")
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    time_used_sec: Mapped[int] = mapped_column(Integer, default=0)
    practice_date: Mapped[str] = mapped_column(String(10), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

