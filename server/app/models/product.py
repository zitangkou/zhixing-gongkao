"""多产品共享学习任务模型。"""

from datetime import datetime

from app.models.base import (
    Base,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Mapped,
    gen_id,
    mapped_column,
    utcnow,
)


class DailyLearningTask(Base):
    """按产品和日期编排的学习任务。"""

    __tablename__ = "daily_learning_tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("dlt"))
    product_key: Mapped[str] = mapped_column(String(32), index=True)
    task_date: Mapped[str] = mapped_column(String(10), index=True)
    task_type: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(String(512), default="")
    content_type: Mapped[str] = mapped_column(String(32), default="")
    content_id: Mapped[str] = mapped_column(String(32), default="", index=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=15)
    total_steps: Mapped[int] = mapped_column(Integer, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="draft", index=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class UserDailyTaskProgress(Base):
    """用户任务状态与草稿；服务端是跨端断点恢复的真值源。"""

    __tablename__ = "user_daily_task_progress"
    __table_args__ = (UniqueConstraint("user_id", "task_id", name="uq_user_daily_task"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("dtp"))
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("daily_learning_tasks.id"), index=True)
    product_key: Mapped[str] = mapped_column(String(32), index=True)
    state: Mapped[str] = mapped_column(String(16), default="not_started", index=True)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    total_steps: Mapped[int] = mapped_column(Integer, default=1)
    draft_json: Mapped[str] = mapped_column(Text, default="{}")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
