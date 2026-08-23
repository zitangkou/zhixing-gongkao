"""账号内容运营模板与发布包。"""
from datetime import datetime
from app.models.base import Base, DateTime, ForeignKey, Integer, Mapped, String, Text, gen_id, mapped_column, utcnow


class ContentOperationTemplate(Base):
    __tablename__ = "content_operation_templates"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("cot"))
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    product_key: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(256), default="")
    slots_json: Mapped[str] = mapped_column(Text, default="[]")
    channels_json: Mapped[str] = mapped_column(Text, default="[]")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="enabled", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ContentPublishPackage(Base):
    __tablename__ = "content_publish_packages"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("cpp"))
    product_key: Mapped[str] = mapped_column(String(32), index=True)
    template_id: Mapped[str] = mapped_column(ForeignKey("content_operation_templates.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(32), index=True)
    source_id: Mapped[str] = mapped_column(String(32), index=True)
    source_title: Mapped[str] = mapped_column(String(256), default="")
    campaign_key: Mapped[str] = mapped_column(String(64), default="", index=True)
    deep_link: Mapped[str] = mapped_column(String(512), default="")
    variants_json: Mapped[str] = mapped_column(Text, default="{}")
    review_note: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(24), default="draft", index=True)
    planned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
