"""模板化账号运营：固定栏目、跨平台发布包与双审核状态。"""
import json
from sqlalchemy.orm import Session
from app.models import ContentOperationTemplate, ContentPublishPackage, gen_id
from app.schemas import ContentPublishPackageCreate, ContentPublishPackageUpdate
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
    row = ContentPublishPackage(
        id=gen_id("cpp"), product_key=body.productKey, template_id=template.id,
        source_type=body.sourceType, source_id=body.sourceId, source_title=body.sourceTitle,
        campaign_key=body.campaignKey, deep_link=body.deepLink,
        variants_json=json.dumps(body.variants, ensure_ascii=False), planned_at=body.plannedAt,
    )
    db.add(row); db.commit(); db.refresh(row)
    return package_out(row)


def transition_package(db: Session, package_id: str, target: str, note: str = "") -> dict:
    row = db.get(ContentPublishPackage, package_id)
    if not row:
        raise ValueError("发布包不存在")
    if target not in TRANSITIONS.get(row.status, set()):
        raise ValueError(f"发布包状态 {row.status} 不能变更为 {target}")
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
    if "variants" in data:
        template = db.get(ContentOperationTemplate, row.template_id)
        unknown = set(data.pop("variants") or {}) - set(_loads(template.channels_json, []))
        if unknown: raise ValueError(f"模板不支持渠道: {', '.join(sorted(unknown))}")
        row.variants_json = json.dumps(body.variants or {}, ensure_ascii=False)
    for key, value in data.items(): setattr(row, mapping.get(key, key), value)
    db.commit(); db.refresh(row)
    return package_out(row)
