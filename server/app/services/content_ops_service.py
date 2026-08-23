"""模板化账号运营：固定栏目、跨平台发布包与双审核状态。"""
import json
import re
from datetime import timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from sqlalchemy.orm import Session
from app.models import Article, ContentOperationTemplate, ContentPublishPackage, gen_id
from app.schemas import ContentPackageGenerateFromArticle, ContentPublishPackageCreate, ContentPublishPackageUpdate
from app.timezone import now

CHANNELS = ["xiaohongshu", "douyin", "bilibili", "wechat"]
DEFAULT_TEMPLATES = [
    ("shenlun_three_cut", "shenlun", "三刀拆解", ["标题", "原文", "骨架", "规范表达", "迁移练习"]),
    ("shenlun_expression", "shenlun", "规范表达", ["普通说法", "规范表达", "适用场景", "例句"]),
    ("shenlun_challenge", "shenlun", "找点挑战", ["材料", "任务", "参考要点", "易漏点"]),
    ("shenlun_clinic", "shenlun", "失分诊所", ["问题作答", "失分原因", "修改过程", "改后答案"]),
    ("theory_current", "theory", "时政考点", ["事实", "规范表述", "考法", "原文依据"]),
    ("theory_confusion", "theory", "易混辨析", ["表述A", "表述B", "差异", "依据"]),
    ("theory_option", "theory", "真题选项", ["题干", "选项", "干扰方式", "原文依据"]),
    ("theory_source", "theory", "理论原文怎么考", ["原文", "关键词", "命题角度", "练习题"]),
    ("wechat_daily_pack", "general", "公众号今日学习包", ["导语", "申论任务", "政治理论任务", "小程序入口"]),
    ("wechat_weekly_review", "general", "公众号一周学习复盘", ["本周主题", "高频错因", "表达清单", "下周任务"]),
]

TRANSITIONS = {
    "draft": {"teaching_review"},
    "teaching_review": {"ops_review", "rejected"},
    "ops_review": {"ready", "rejected"},
    "ready": {"published", "rejected"},
    "rejected": {"draft"},
    "published": set(),
}


def _loads(raw: str, fallback):
    try:
        return json.loads(raw or "")
    except (json.JSONDecodeError, TypeError):
        return fallback


def ensure_content_ops_defaults(db: Session) -> None:
    for order, (code, product, name, slots) in enumerate(DEFAULT_TEMPLATES):
        if db.query(ContentOperationTemplate).filter(ContentOperationTemplate.code == code).first():
            continue
        db.add(ContentOperationTemplate(
            id=gen_id("cot"), code=code, product_key=product, name=name,
            description="由审核后的教学母资产派生，发布前需完成教研与运营双审核",
            slots_json=json.dumps(slots, ensure_ascii=False),
            channels_json=json.dumps(CHANNELS, ensure_ascii=False), sort_order=order,
        ))
    db.commit()


def template_out(row: ContentOperationTemplate) -> dict:
    return {"id": row.id, "code": row.code, "productKey": row.product_key, "name": row.name,
            "description": row.description, "slots": _loads(row.slots_json, []),
            "channels": _loads(row.channels_json, []), "sortOrder": row.sort_order, "status": row.status}


def package_out(row: ContentPublishPackage) -> dict:
    return {"id": row.id, "productKey": row.product_key, "templateId": row.template_id,
            "sourceType": row.source_type, "sourceId": row.source_id, "sourceTitle": row.source_title,
            "campaignKey": row.campaign_key, "deepLink": row.deep_link,
            "slotValues": _loads(row.slot_values_json, {}),
            "variants": _loads(row.variants_json, {}), "reviewNote": row.review_note, "status": row.status,
            "plannedAt": row.planned_at, "publishedAt": row.published_at,
            "createdAt": row.created_at, "updatedAt": row.updated_at}


def create_package(db: Session, body: ContentPublishPackageCreate) -> dict:
    template = db.get(ContentOperationTemplate, body.templateId)
    if not template or template.status != "enabled":
        raise ValueError("运营模板不存在或未启用")
    if template.product_key not in (body.productKey, "general"):
        raise ValueError("模板与产品不匹配")
    unknown = set(body.variants) - set(_loads(template.channels_json, []))
    if unknown:
        raise ValueError(f"模板不支持渠道: {', '.join(sorted(unknown))}")
    unknown_slots = set(body.slotValues) - set(_loads(template.slots_json, []))
    if unknown_slots:
        raise ValueError(f"模板不存在槽位: {', '.join(sorted(unknown_slots))}")
    row = ContentPublishPackage(
        id=gen_id("cpp"), product_key=body.productKey, template_id=template.id,
        source_type=body.sourceType, source_id=body.sourceId, source_title=body.sourceTitle,
        campaign_key=body.campaignKey, deep_link=body.deepLink,
        slot_values_json=json.dumps(body.slotValues, ensure_ascii=False),
        variants_json=json.dumps(body.variants, ensure_ascii=False), planned_at=body.plannedAt,
    )
    db.add(row); db.commit(); db.refresh(row)
    return package_out(row)


def _plain_text(value: str, limit: int) -> str:
    text = re.sub(r"[#>*_`\[\]()]", " ", value or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _article_slot_values(article: Article, slots: list[str]) -> dict[str, str]:
    summary = _plain_text(article.summary or article.content, 360)
    excerpt = _plain_text(article.content or article.summary, 1200)
    evidence = " · ".join(part for part in (article.source, article.publish_date, article.title) if part)
    deterministic = {
        "标题": article.title,
        "原文": excerpt,
        "材料": excerpt,
        "短材料": excerpt,
        "事实": summary,
        "事件": summary,
        "日期": article.publish_date,
        "主体": article.source,
        "规范表述": summary,
        "原文依据": evidence,
        "依据": evidence,
        "导语": summary,
        "本周主题": article.title,
        "关键词": "、".join(_loads(article.tags, [])[:6]),
    }
    return {slot: deterministic.get(slot, "") for slot in slots}


def _tracked_link(base: str, channel: str) -> str:
    if not base:
        return base
    parts = urlsplit(base)
    query = [(key, value) for key, value in parse_qsl(parts.query) if key != "channel"]
    query.append(("channel", channel))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _article_variants(article: Article, template: ContentOperationTemplate, slots: dict[str, str], deep_link: str) -> dict:
    filled = [f"{name}：{value}" for name, value in slots.items() if value]
    missing = [name for name, value in slots.items() if not value]
    core = "\n\n".join(filled)
    missing_note = f"\n\n待教研补充：{'、'.join(missing)}" if missing else ""
    titles = {
        "xiaohongshu": f"{template.name}｜{article.title}",
        "douyin": f"{article.title}，考试会怎么考？",
        "bilibili": f"{template.name}：{article.title}",
        "wechat": f"今日学习｜{article.title}",
    }
    prefixes = {
        "xiaohongshu": "先收藏，再用一个考点框架读懂这篇材料。",
        "douyin": "这条内容用一分钟讲清一个可迁移的考试知识点。",
        "bilibili": "本期从原文、考点和迁移练习三个层次展开。",
        "wechat": "今天用一篇已审核文章完成一次结构化学习。",
    }
    return {
        channel: {
            "title": titles[channel][:80],
            "body": f"{prefixes[channel]}\n\n{core}{missing_note}",
            "ctaLink": _tracked_link(deep_link, channel),
            "generatedDraft": True,
        }
        for channel in _loads(template.channels_json, [])
    }


def generate_package_from_article(db: Session, body: ContentPackageGenerateFromArticle) -> dict:
    article = db.get(Article, body.articleId)
    if not article or article.status != "published" or not article.is_published:
        raise ValueError("只有已发布文章可以生成运营发布包")
    template = db.get(ContentOperationTemplate, body.templateId)
    if not template or template.status != "enabled":
        raise ValueError("运营模板不存在或未启用")
    if template.product_key not in (body.productKey, "general"):
        raise ValueError("模板与产品不匹配")
    duplicate = db.query(ContentPublishPackage).filter(
        ContentPublishPackage.source_type == "article",
        ContentPublishPackage.source_id == article.id,
        ContentPublishPackage.template_id == template.id,
        ContentPublishPackage.status != "rejected",
    ).first()
    if duplicate:
        raise ValueError("该文章已用此模板生成发布包，请直接编辑已有草稿")
    slots = _article_slot_values(article, _loads(template.slots_json, []))
    variants = _article_variants(article, template, slots, body.deepLink)
    return create_package(db, ContentPublishPackageCreate(
        productKey=body.productKey,
        templateId=template.id,
        sourceType="article",
        sourceId=article.id,
        sourceTitle=article.title,
        campaignKey=body.campaignKey,
        deepLink=body.deepLink,
        slotValues=slots,
        variants=variants,
        plannedAt=body.plannedAt,
    ))


def transition_package(db: Session, package_id: str, target: str, note: str = "") -> dict:
    row = db.get(ContentPublishPackage, package_id)
    if not row:
        raise ValueError("发布包不存在")
    if target not in TRANSITIONS.get(row.status, set()):
        raise ValueError(f"发布包状态 {row.status} 不能变更为 {target}")
    if target == "teaching_review":
        template = db.get(ContentOperationTemplate, row.template_id)
        values = _loads(row.slot_values_json, {})
        missing = [slot for slot in _loads(template.slots_json, []) if not str(values.get(slot, "")).strip()]
        if missing:
            raise ValueError(f"请先补齐模板槽位: {', '.join(missing)}")
    row.status = target; row.review_note = note.strip()
    if target == "published": row.published_at = now()
    db.commit(); db.refresh(row)
    return package_out(row)


def update_package(db: Session, package_id: str, body: ContentPublishPackageUpdate) -> dict:
    row = db.get(ContentPublishPackage, package_id)
    if not row:
        raise ValueError("发布包不存在")
    if row.status not in ("draft", "rejected"):
        raise ValueError("只有草稿或已驳回发布包可以编辑")
    data = body.model_dump(exclude_unset=True)
    mapping = {"sourceTitle": "source_title", "campaignKey": "campaign_key", "deepLink": "deep_link", "plannedAt": "planned_at"}
    if "slotValues" in data:
        template = db.get(ContentOperationTemplate, row.template_id)
        slot_values = data.pop("slotValues") or {}
        unknown = set(slot_values) - set(_loads(template.slots_json, []))
        if unknown: raise ValueError(f"模板不存在槽位: {', '.join(sorted(unknown))}")
        row.slot_values_json = json.dumps(slot_values, ensure_ascii=False)
    if "variants" in data:
        template = db.get(ContentOperationTemplate, row.template_id)
        unknown = set(data.pop("variants") or {}) - set(_loads(template.channels_json, []))
        if unknown: raise ValueError(f"模板不支持渠道: {', '.join(sorted(unknown))}")
        row.variants_json = json.dumps(body.variants or {}, ensure_ascii=False)
    for key, value in data.items(): setattr(row, mapping.get(key, key), value)
    db.commit(); db.refresh(row)
    return package_out(row)


def export_package(db: Session, package_id: str) -> dict:
    row = db.get(ContentPublishPackage, package_id)
    if not row:
        raise ValueError("发布包不存在")
    if row.status not in ("ready", "published"):
        raise ValueError("只有待发布或已发布的发布包可以导出")
    template = db.get(ContentOperationTemplate, row.template_id)
    variants = _loads(row.variants_json, {})
    return {
        "schemaVersion": "content-publish-package/v1",
        "generatedAt": now(),
        "template": template_out(template),
        "package": package_out(row),
        "channels": [
            {
                "channel": channel,
                "content": content,
                "deepLink": content.get("ctaLink") or row.deep_link,
                "plannedAt": row.planned_at,
                "manualPublishRequired": True,
            }
            for channel, content in variants.items()
        ],
        "checklist": ["核对标题与正文", "核对事实和原文依据", "核对小程序深链", "人工发布后回填已发布状态"],
    }


def content_ops_overview(db: Session, days: int = 7) -> dict:
    current = now().replace(tzinfo=None)
    start = current.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=days)
    rows = db.query(ContentPublishPackage).all()
    scheduled = [row for row in rows if row.planned_at and start <= row.planned_at < end]
    status_counts = {status: 0 for status in TRANSITIONS}
    for row in rows:
        status_counts[row.status] = status_counts.get(row.status, 0) + 1
    product_mix = {
        product: sum(1 for row in scheduled if row.product_key == product)
        for product in ("shenlun", "theory")
    }
    unplanned_drafts = sum(1 for row in rows if row.status in ("draft", "rejected") and not row.planned_at)
    review_backlog = status_counts.get("teaching_review", 0) + status_counts.get("ops_review", 0)
    ready_inventory = status_counts.get("ready", 0)
    alerts = []
    missing_products = [label for product, label in (("shenlun", "申论"), ("theory", "政治理论")) if product_mix[product] == 0]
    if missing_products:
        alerts.append({"level": "warning", "code": "product_mix_empty", "message": f"未来{days}天未安排{'、'.join(missing_products)}内容"})
    if ready_inventory == 0:
        alerts.append({"level": "warning", "code": "ready_empty", "message": "暂无待发布库存，请优先完成审核"})
    if unplanned_drafts:
        alerts.append({"level": "info", "code": "draft_unplanned", "message": f"{unplanned_drafts} 个草稿尚未排期"})
    if review_backlog >= 10:
        alerts.append({"level": "warning", "code": "review_backlog", "message": f"{review_backlog} 个发布包正在等待审核"})
    return {
        "windowDays": days,
        "windowStart": start,
        "windowEnd": end,
        "scheduledCount": len(scheduled),
        "readyInventory": ready_inventory,
        "reviewBacklog": review_backlog,
        "unplannedDrafts": unplanned_drafts,
        "productMix": product_mix,
        "statusCounts": status_counts,
        "alerts": alerts,
        "healthy": not any(item["level"] == "warning" for item in alerts),
    }
