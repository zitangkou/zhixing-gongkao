"""账号内容运营模板、发布包与双审核记录。"""
from datetime import datetime
from app.models.base import Base, DateTime, ForeignKey, Integer, Mapped, String, Text, gen_id, mapped_column, relationship, utcnow


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
    slot_values_json: Mapped[str] = mapped_column(Text, default="{}")
    variants_json: Mapped[str] = mapped_column(Text, default="{}")
    review_note: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(24), default="draft", index=True)
    planned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    review_records: Mapped[list["ContentReviewRecord"]] = relationship(
        back_populates="package",
        cascade="all, delete-orphan",
        order_by="ContentReviewRecord.created_at",
    )


class ContentReviewRecord(Base):
    """教研/运营审核的不可覆盖留痕。"""

    __tablename__ = "content_review_records"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: gen_id("crr"))
    package_id: Mapped[str] = mapped_column(ForeignKey("content_publish_packages.id"), index=True)
    stage: Mapped[str] = mapped_column(String(24), index=True)  # teaching | operations
    decision: Mapped[str] = mapped_column(String(16), index=True)  # approved | rejected
    checklist_json: Mapped[str] = mapped_column(Text, default="{}")
    note: Mapped[str] = mapped_column(Text, default="")
    reviewer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reviewer_username: Mapped[str] = mapped_column(String(64), default="")
    reviewer_name: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    package: Mapped[ContentPublishPackage] = relationship(back_populates="review_records")
