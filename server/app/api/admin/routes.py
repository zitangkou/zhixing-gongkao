import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, require_permission
from app.core.permissions import PERMISSIONS, ROLE_PERMISSIONS
from app.core.response import ApiResponse
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models import AdminUser, AppUser, Article, Category, Question, Role, SystemSetting, gen_id
from app.models import CorpusItem, EventImpression, HealthDailyLog, HealthUserState
from app.models import DushuBook, DushuDailyLog, DushuPersonCard, DushuBookSummary
from app.schemas import (
    AdminLogin,
    AdminToken,
    AdminUserOut,
    AppUserOut,
    AppUserUpdate,
    ArticleCreate,
    ArticleInferMetadataBody,
    ArticleUpdate,
    ArticleBatchCategory,
    ArticleBatchIds,
    ArticleBatchPublish,
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    KnowledgeNodeCreate,
    KnowledgeNodeOut,
    KnowledgeNodeUpdate,
    KnowledgeTreeOut,
    ExamPaperCreate,
    ExamPaperOut,
    ExamPaperUpdate,
    ExamQuestionCreate,
    ExamQuestionOut,
    ExamQuestionUpdate,
    EnglishArticleCreate,
    EnglishArticleOut,
    EnglishArticleUpdate,
    GrammarLessonCreate,
    GrammarLessonOut,
    PhoneticLessonCreate,
    PhoneticLessonOut,
    SpeakingLessonCreate,
    SpeakingLessonOut,
    PlanTemplateCreate,
    PlanTemplateOut,
    PlanTemplateUpdate,
    QuestionBatchApprove,
    QuestionBatchDelete,
    QuestionCreate,
    QuestionUpdate,
    AiGenerateQuestionsBody,
    ImportArticleMarkdownBody,
    ImportQuestionsBody,
    RoleOut,
    SettingOut,
    SettingUpdate,
    RmrbArticleCreate,
    RmrbArticleUpdate,
    ShenlunArgumentMethodCreate,
    ShenlunArgumentMethodUpdate,
    ShenlunSentenceTypeCreate,
    ShenlunSentenceTypeUpdate,
    ShenlunSkeletonTemplateCreate,
    ShenlunSkeletonTemplateUpdate,
    ShenlunTermCategoryCreate,
    ShenlunTermCategoryUpdate,
    ZiliaoFormulaCreate,
    ZiliaoFormulaImportBody,
    ZiliaoFormulaUpdate,
    ZiliaoQuestionTypeCreate,
    ZiliaoQuestionTypeUpdate,
    ZiliaoTrickCreate,
    ZiliaoTrickUpdate,
)
from app.services.category_service import build_category_tree, sync_article_category
# from app.services.crawler import run_daily_crawl  # 爬虫已关闭
from app.services.ai.llm_client import LlmError
from app.services.ai.question_generator import run_ai_question_generation
from app.services.question_factory import add_generated_questions, add_imported_questions
from app.services.question_import import parse_questions_markdown
from app.services.article_import import parse_article_markdown
from app.services.article_metadata import infer_article_metadata, merge_article_fields
from app.services.article_service import delete_article_record
from app.services.question_service import delete_question_record, delete_questions_for_article
from app.services.section_parser import build_sections_from_content, sections_to_content
from app.services.serializers import article_to_out, build_mind_map, question_to_out
from app.services.serializers import parse_json
from app.services.knowledge_service import (
    create_node as create_knowledge_node,
    delete_node as delete_knowledge_node,
    get_tree as get_knowledge_tree,
    list_trees as list_knowledge_trees,
    save_uploaded_md,
    sync_knowledge,
    sync_status as knowledge_sync_status,
    update_node as update_knowledge_node,
)
from app.services.plan_service import (
    copy_day_templates as copy_plan_day_templates,
    create_template as create_plan_template,
    delete_template as delete_plan_template,
    list_templates as list_plan_templates,
    replace_default_templates,
    seed_default_templates,
    sync_templates_to_pending_tasks,
    update_template as update_plan_template,
)
from app.services.exam_service import (
    batch_create_questions as batch_create_exam_questions,
    create_paper as create_exam_paper,
    create_question as create_exam_question,
    delete_paper as delete_exam_paper,
    delete_question as delete_exam_question,
    get_paper as get_exam_paper,
    list_papers as list_exam_papers,
    update_paper as update_exam_paper,
    update_question as update_exam_question,
)
from app.services.exam_import import parse_import as parse_exam_import
from app.services.english_service import (
    create_article as create_english_article,
    create_grammar_lesson as create_grammar_lesson_svc,
    create_speaking_lesson as create_speaking_lesson_svc,
    delete_article as delete_english_article,
    delete_grammar_lesson as delete_grammar_lesson_svc,
    delete_speaking_lesson as delete_speaking_lesson_svc,
    list_articles as list_english_articles,
    list_grammar_lessons as list_grammar_lessons_admin,
    list_speaking_lessons as list_speaking_lessons_admin,
    update_article as update_english_article,
    update_grammar_lesson as update_grammar_lesson_svc,
    update_speaking_lesson as update_speaking_lesson_svc,
)
from app.services.ziliao_service import (
    create_formula as create_ziliao_formula,
    create_trick as create_ziliao_trick,
    create_type as create_ziliao_type,
    delete_formula as delete_ziliao_formula,
    delete_trick as delete_ziliao_trick,
    delete_type as delete_ziliao_type,
    import_formulas_from_json as import_ziliao_formulas_from_json,
    list_formulas as list_ziliao_formulas_admin,
    list_tricks as list_ziliao_tricks_admin,
    list_types as list_ziliao_types_admin,
    seed_sample_drill_paper,
    seed_ziliao_resources,
    update_formula as update_ziliao_formula,
    update_trick as update_ziliao_trick,
    update_type as update_ziliao_type,
)
from app.services.phonetic_service import (
    create_phonetic as create_phonetic_svc,
    delete_phonetic as delete_phonetic_svc,
    list_phonetics as list_phonetics_admin,
    seed_default_phonetics,
    update_phonetic as update_phonetic_svc,
)
from app.services.rmrb_service import (
    create_article as create_rmrb_article,
    delete_article as delete_rmrb_article,
    list_articles as list_rmrb_articles_admin,
    update_article as update_rmrb_article,
)
from app.services.rmrb_meta_service import (
    create_argument_method as create_rmrb_argument_method,
    create_sentence_type as create_rmrb_sentence_type,
    create_skeleton_template as create_rmrb_skeleton,
    create_term_category as create_rmrb_term_category,
    delete_argument_method as delete_rmrb_argument_method,
    delete_sentence_type as delete_rmrb_sentence_type,
    delete_skeleton_template as delete_rmrb_skeleton,
    delete_term_category as delete_rmrb_term_category,
    get_meta as get_rmrb_meta,
    list_argument_methods as list_rmrb_argument_methods,
    list_sentence_types as list_rmrb_sentence_types,
    list_skeleton_templates as list_rmrb_skeletons,
    list_term_categories as list_rmrb_term_categories,
    update_argument_method as update_rmrb_argument_method,
    update_sentence_type as update_rmrb_sentence_type,
    update_skeleton_template as update_rmrb_skeleton,
    update_term_category as update_rmrb_term_category,
)

router = APIRouter(prefix="/admin", tags=["管理后台"])


@router.post("/auth/login")
def admin_login(body: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.username == body.username).first()
    if not admin or not verify_password(body.password, admin.password_hash):
        return ApiResponse.fail("用户名或密码错误", code=401)
    if not admin.is_active:
        return ApiResponse.fail("账号已禁用", code=403)
    perms = parse_json(admin.role.permissions, [])
    token = create_access_token(admin.username)
    return ApiResponse.ok(
        AdminToken(
            access_token=token,
            username=admin.username,
            role=admin.role.code,
            permissions=perms,
        ).model_dump()
    )


@router.get("/auth/me")
def admin_me(admin: AdminUser = Depends(get_current_admin)):
    perms = parse_json(admin.role.permissions, [])
    return ApiResponse.ok(
        AdminUserOut(
            id=admin.id,
            username=admin.username,
            nickname=admin.nickname,
            role_code=admin.role.code,
            is_active=admin.is_active,
            created_at=admin.created_at,
            permissions=perms,
        ).model_dump()
    )


# ---- 文章管理 ----
@router.get("/articles")
def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    status: str | None = None,
    _admin=Depends(require_permission("article:read")),
    db: Session = Depends(get_db),
):
    q = db.query(Article)
    if keyword:
        q = q.filter(Article.title.contains(keyword))
    if status:
        q = q.filter(Article.status == status)
    total = q.count()
    rows = q.order_by(Article.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ApiResponse.ok({
        "total": total,
        "items": [article_to_out(a).model_dump() for a in rows],
    })


@router.get("/articles/{article_id}")
def get_article(
    article_id: str,
    _admin=Depends(require_permission("article:read")),
    db: Session = Depends(get_db),
):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404, "文章不存在")
    return ApiResponse.ok(article_to_out(article).model_dump())


@router.post("/articles/infer-metadata")
def infer_article_metadata_api(
    body: ArticleInferMetadataBody,
    _admin=Depends(require_permission("article:write")),
    db: Session = Depends(get_db),
):
    result = infer_article_metadata(db, content=body.content, title=body.title)
    return ApiResponse.ok({
        "title": result["title"],
        "content": result["content"],
        "source": result["source"],
        "sourceUrl": result["source_url"],
        "publishDate": result["publish_date"],
        "summary": result["summary"],
        "tags": result["tags"],
        "categoryId": result["category_id"],
        "categoryName": result["category_name"],
        "importance": result["importance"],
    })


@router.post("/articles")
def create_article(
    body: ArticleCreate,
    _admin=Depends(require_permission("article:write")),
    db: Session = Depends(get_db),
):
    merged = merge_article_fields(
        db,
        title=body.title,
        source=body.source,
        source_url=body.source_url,
        publish_date=body.publish_date,
        summary=body.summary,
        content=body.content,
        tags=body.tags,
        category_id=body.category_id,
        importance=body.importance,
    )
    mind = body.mind_map or build_mind_map(merged["title"], merged["content"] or merged["summary"])
    sections = body.sections or build_sections_from_content(merged["title"], merged["content"] or merged["summary"])
    content = merged["content"] or sections_to_content(sections)
    article = Article(
        title=merged["title"],
        source=merged["source"],
        source_url=merged["source_url"],
        publish_date=merged["publish_date"],
        summary=merged["summary"],
        content=content,
        sections=json.dumps(sections, ensure_ascii=False),
        tags=json.dumps(merged["tags"], ensure_ascii=False),
        mind_map=json.dumps(mind, ensure_ascii=False),
        importance=merged["importance"],
        status=body.status,
        allow_quiz=body.allow_quiz,
        is_published=body.is_published,
        is_daily=body.is_daily,
    )
    db.add(article)
    db.flush()
    sync_article_category(db, article, merged["category_id"])
    if body.auto_generate_questions:
        add_generated_questions(db, article, pending=True, origin="manual")
    db.commit()
    db.refresh(article)
    return ApiResponse.ok(article_to_out(article).model_dump())


@router.post("/articles/import-markdown")
def import_article_markdown(
    body: ImportArticleMarkdownBody,
    _admin=Depends(require_permission("article:write")),
    db: Session = Depends(get_db),
):
    try:
        parsed, parse_errors = parse_article_markdown(body.markdown)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)

    merged = merge_article_fields(
        db,
        title=parsed["title"],
        source=body.source,
        source_url="",
        publish_date=body.publish_date,
        summary=parsed["summary"],
        content=parsed["content"],
        tags=body.tags,
        category_id=body.category_id,
        importance=5 if body.is_featured else 3,
    )
    if body.is_featured and "重点必读" not in merged["tags"]:
        merged["tags"] = [*merged["tags"], "重点必读"]

    mind = build_mind_map(merged["title"], merged["content"] or merged["summary"])
    article = Article(
        title=merged["title"],
        source=merged["source"],
        source_url=merged["source_url"],
        publish_date=merged["publish_date"],
        summary=merged["summary"],
        content=parsed["content"],
        sections=json.dumps(parsed["sections"], ensure_ascii=False),
        tags=json.dumps(merged["tags"], ensure_ascii=False),
        mind_map=json.dumps(mind, ensure_ascii=False),
        importance=merged["importance"],
        status=body.status,
        allow_quiz=True,
        is_published=body.status == "published",
        is_daily=False,
        is_featured=body.is_featured,
    )
    db.add(article)
    db.flush()
    sync_article_category(db, article, merged["category_id"])
    db.commit()
    db.refresh(article)

    out = article_to_out(article).model_dump()
    out["stats"] = parsed["stats"]
    out["parse_warnings"] = parse_errors
    msg = (
        f"已导入：{parsed['stats']['chapters']} 章、"
        f"{parsed['stats']['sections']} 节、"
        f"{parsed['stats']['paragraphs']} 段"
    )
    if parse_errors:
        msg += f"（{len(parse_errors)} 条解析提示）"
    return ApiResponse.ok(out, message=msg)


@router.put("/articles/{article_id}")
def update_article(
    article_id: str,
    body: ArticleUpdate,
    _admin=Depends(require_permission("article:write")),
    db: Session = Depends(get_db),
):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404, "文章不存在")
    data = body.model_dump(exclude_unset=True)
    category_id = data.pop("category_id", None) if "category_id" in data else None
    has_category_update = "category_id" in body.model_dump(exclude_unset=True)
    if "tags" in data:
        article.tags = json.dumps(data.pop("tags"), ensure_ascii=False)
    if "mind_map" in data:
        article.mind_map = json.dumps(data.pop("mind_map"), ensure_ascii=False)
    if "sections" in data:
        sections = data.pop("sections")
        article.sections = json.dumps(sections, ensure_ascii=False)
        if "content" not in data:
            article.content = sections_to_content(sections)
    for k, v in data.items():
        setattr(article, k, v)
    if has_category_update:
        sync_article_category(db, article, category_id)
    if article.status == "published":
        article.is_published = True
    elif article.status in ("pending", "draft", "rejected"):
        article.is_published = False
        if article.status == "rejected":
            article.is_daily = False
    db.commit()
    return ApiResponse.ok(article_to_out(article).model_dump())


@router.post("/articles/{article_id}/approve")
def approve_article(
    article_id: str,
    _admin=Depends(require_permission("article:write")),
    db: Session = Depends(get_db),
):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404, "文章不存在")
    article.status = "published"
    article.is_published = True
    db.commit()
    return ApiResponse.ok(article_to_out(article).model_dump(), message="文章已发布")


@router.post("/articles/{article_id}/reject")
def reject_article(
    article_id: str,
    _admin=Depends(require_permission("article:write")),
    db: Session = Depends(get_db),
):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404, "文章不存在")
    article.status = "rejected"
    article.is_published = False
    article.is_daily = False
    db.commit()
    return ApiResponse.ok(article_to_out(article).model_dump(), message="文章已驳回")


@router.post("/articles/batch-approve")
def batch_approve_articles(
    body: ArticleBatchPublish,
    _admin=Depends(require_permission("article:write")),
    db: Session = Depends(get_db),
):
    if not body.article_ids:
        return ApiResponse.ok({"article_count": 0, "question_count": 0})
    articles = db.query(Article).filter(Article.id.in_(body.article_ids)).all()
    q_count = 0
    for article in articles:
        article.status = "published"
        article.is_published = True
        if body.approve_questions:
            rows = (
                db.query(Question)
                .filter(Question.article_id == article.id, Question.status == "pending")
                .all()
            )
            for q in rows:
                q.status = "approved"
                q.is_active = True
            q_count += len(rows)
    db.commit()
    msg = f"已发布 {len(articles)} 篇文章"
    if body.approve_questions and q_count:
        msg += f"，并审核通过 {q_count} 道题目"
    return ApiResponse.ok({"article_count": len(articles), "question_count": q_count}, message=msg)


@router.post("/articles/batch-reject")
def batch_reject_articles(
    body: ArticleBatchIds,
    _admin=Depends(require_permission("article:write")),
    db: Session = Depends(get_db),
):
    if not body.article_ids:
        return ApiResponse.ok({"count": 0})
    rows = db.query(Article).filter(Article.id.in_(body.article_ids)).all()
    for article in rows:
        article.status = "rejected"
        article.is_published = False
        article.is_daily = False
    db.commit()
    return ApiResponse.ok({"count": len(rows)}, message=f"已驳回 {len(rows)} 篇文章")


@router.post("/articles/batch-category")
def batch_set_article_category(
    body: ArticleBatchCategory,
    _admin=Depends(require_permission("article:write")),
    db: Session = Depends(get_db),
):
    if not body.article_ids:
        return ApiResponse.ok({"count": 0})
    rows = db.query(Article).filter(Article.id.in_(body.article_ids)).all()
    for article in rows:
        sync_article_category(db, article, body.category_id)
    db.commit()
    return ApiResponse.ok({"count": len(rows)}, message=f"已更新 {len(rows)} 篇文章分类")


@router.post("/articles/batch-delete")
def batch_delete_articles(
    body: ArticleBatchIds,
    _admin=Depends(require_permission("article:write")),
    db: Session = Depends(get_db),
):
    if not body.article_ids:
        return ApiResponse.ok({"count": 0})
    rows = db.query(Article).filter(Article.id.in_(body.article_ids)).all()
    for article in rows:
        delete_article_record(db, article)
    db.commit()
    return ApiResponse.ok({"count": len(rows)}, message=f"已删除 {len(rows)} 篇文章")


@router.post("/articles/{article_id}/approve-questions")
def approve_article_questions(
    article_id: str,
    _admin=Depends(require_permission("question:write")),
    db: Session = Depends(get_db),
):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404, "文章不存在")
    rows = (
        db.query(Question)
        .filter(Question.article_id == article_id, Question.status == "pending")
        .all()
    )
    for q in rows:
        q.status = "approved"
        q.is_active = True
    db.commit()
    return ApiResponse.ok({"count": len(rows)}, message=f"已通过 {len(rows)} 道题目")


@router.post("/articles/{article_id}/generate-questions-ai")
def generate_questions_ai(
    article_id: str,
    body: AiGenerateQuestionsBody,
    _admin=Depends(require_permission("question:write")),
    db: Session = Depends(get_db),
):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404, "文章不存在")
    total = body.single + body.multiple + body.judge
    if total <= 0:
        return ApiResponse.fail("请至少生成 1 道题", code=400)
    try:
        result = run_ai_question_generation(
            db,
            article,
            section_ids=body.section_ids,
            single=body.single,
            multiple=body.multiple,
            judge=body.judge,
        )
    except LlmError as e:
        return ApiResponse.fail(str(e), code=400)
    msg = f"已生成 {result['count']} 道待审核 AI 题目"
    if result.get("validation_warnings"):
        msg += f"（{len(result['validation_warnings'])} 条校验提示）"
    return ApiResponse.ok(result, message=msg)


@router.post("/articles/{article_id}/import-questions")
def import_questions(
    article_id: str,
    body: ImportQuestionsBody,
    _admin=Depends(require_permission("question:write")),
    db: Session = Depends(get_db),
):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404, "文章不存在")

    parsed, parse_errors = parse_questions_markdown(body.markdown)
    if not parsed:
        msg = "；".join(parse_errors[:8]) if parse_errors else "未解析到题目"
        return ApiResponse.fail(msg, code=400)

    if body.replace_existing:
        delete_questions_for_article(db, article_id)

    count = add_imported_questions(db, article, parsed, pending=body.pending)
    db.commit()
    result = {"count": count, "parse_warnings": parse_errors}
    msg = f"已导入 {count} 道题目"
    if parse_errors:
        msg += f"（{len(parse_errors)} 条解析提示）"
    return ApiResponse.ok(result, message=msg)


@router.delete("/articles/{article_id}")
def delete_article(article_id: str, _admin=Depends(require_permission("article:write")), db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404, "文章不存在")
    delete_article_record(db, article)
    db.commit()
    return ApiResponse.ok(None, message="已删除")


# ---- 试题管理 ----
@router.get("/questions")
def list_questions_admin(
    article_id: str | None = None,
    page: int = 1,
    page_size: int = Query(20, ge=1, le=200),
    _admin=Depends(require_permission("question:read")),
    db: Session = Depends(get_db),
):
    q = db.query(Question)
    if article_id:
        q = q.filter(Question.article_id == article_id)
    total = q.count()
    pending_total = 0
    if article_id:
        pending_total = (
            db.query(Question)
            .filter(Question.article_id == article_id, Question.status == "pending")
            .count()
        )
    rows = q.order_by(Question.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ApiResponse.ok({
        "total": total,
        "pending_total": pending_total,
        "items": [question_to_out(r).model_dump() for r in rows],
    })


@router.post("/questions")
def create_question(body: QuestionCreate, _admin=Depends(require_permission("question:write")), db: Session = Depends(get_db)):
    status = body.status or "approved"
    q = Question(
        article_id=body.article_id,
        type=body.type,
        stem=body.stem,
        options=json.dumps(body.options, ensure_ascii=False),
        correct_answer=json.dumps(body.correct_answer, ensure_ascii=False)
        if isinstance(body.correct_answer, list)
        else str(body.correct_answer),
        analysis=body.analysis,
        source_sentence=body.source_sentence,
        status=status,
        origin=body.origin or "manual",
        is_active=body.is_active if body.is_active is not None else status == "approved",
    )
    db.add(q)
    db.commit()
    return ApiResponse.ok(question_to_out(q).model_dump())


@router.put("/questions/{question_id}")
def update_question(
    question_id: str,
    body: QuestionUpdate,
    _admin=Depends(require_permission("question:write")),
    db: Session = Depends(get_db),
):
    q = db.get(Question, question_id)
    if not q:
        raise HTTPException(404, "题目不存在")
    data = body.model_dump(exclude_unset=True)
    if "options" in data:
        q.options = json.dumps(data.pop("options"), ensure_ascii=False)
    if "correct_answer" in data:
        ca = data.pop("correct_answer")
        q.correct_answer = json.dumps(ca, ensure_ascii=False) if isinstance(ca, list) else str(ca)
    for k, v in data.items():
        setattr(q, k, v)
    if q.status == "approved":
        q.is_active = True
    db.commit()
    return ApiResponse.ok(question_to_out(q).model_dump())


@router.post("/questions/batch-approve")
def batch_approve_questions(
    body: QuestionBatchApprove,
    _admin=Depends(require_permission("question:write")),
    db: Session = Depends(get_db),
):
    if not body.question_ids:
        return ApiResponse.ok({"count": 0})
    rows = db.query(Question).filter(Question.id.in_(body.question_ids)).all()
    for q in rows:
        q.status = "approved"
        q.is_active = True
    db.commit()
    return ApiResponse.ok({"count": len(rows)}, message=f"已通过 {len(rows)} 道题目")


@router.post("/questions/batch-delete")
def batch_delete_questions(
    body: QuestionBatchDelete,
    _admin=Depends(require_permission("question:write")),
    db: Session = Depends(get_db),
):
    if not body.question_ids:
        return ApiResponse.ok({"count": 0})
    rows = db.query(Question).filter(Question.id.in_(body.question_ids)).all()
    for q in rows:
        delete_question_record(db, q)
    db.commit()
    return ApiResponse.ok({"count": len(rows)}, message=f"已删除 {len(rows)} 道题目")


@router.delete("/questions/{question_id}")
def delete_question(question_id: str, _admin=Depends(require_permission("question:write")), db: Session = Depends(get_db)):
    q = db.get(Question, question_id)
    if not q:
        raise HTTPException(404, "题目不存在")
    delete_question_record(db, q)
    db.commit()
    return ApiResponse.ok(None, message="已删除")


# ---- 分类管理 ----
@router.get("/categories")
def list_categories_admin(
    _admin=Depends(require_permission("article:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(build_category_tree(db, active_only=False))


@router.post("/categories")
def create_category(
    body: CategoryCreate,
    _admin=Depends(require_permission("article:write")),
    db: Session = Depends(get_db),
):
    cat = Category(
        id=gen_id("cat"),
        name=body.name,
        parent_id=body.parent_id,
        sort_order=body.sort_order,
    )
    db.add(cat)
    db.commit()
    return ApiResponse.ok({
        "id": cat.id,
        "name": cat.name,
        "parentId": cat.parent_id,
        "sortOrder": cat.sort_order,
        "children": [],
    })


@router.put("/categories/{category_id}")
def update_category(
    category_id: str,
    body: CategoryUpdate,
    _admin=Depends(require_permission("article:write")),
    db: Session = Depends(get_db),
):
    cat = db.get(Category, category_id)
    if not cat:
        raise HTTPException(404, "分类不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    db.commit()
    return ApiResponse.ok({
        "id": cat.id,
        "name": cat.name,
        "parentId": cat.parent_id,
        "sortOrder": cat.sort_order,
    })


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: str,
    _admin=Depends(require_permission("article:write")),
    db: Session = Depends(get_db),
):
    cat = db.get(Category, category_id)
    if not cat:
        raise HTTPException(404, "分类不存在")
    child = db.query(Category).filter(Category.parent_id == category_id).first()
    if child:
        return ApiResponse.fail("请先删除子分类", code=400)
    used = db.query(Article).filter(Article.category_id == category_id).first()
    if used:
        return ApiResponse.fail("分类已被文章使用", code=400)
    db.delete(cat)
    db.commit()
    return ApiResponse.ok(None, message="已删除")


# ---- 用户管理 ----
@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin=Depends(require_permission("user:read")),
    db: Session = Depends(get_db),
):
    q = db.query(AppUser).order_by(AppUser.created_at.desc())
    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()
    return ApiResponse.ok({
        "total": total,
        "items": [
            AppUserOut(
                id=u.id, nickname=u.nickname, avatar=u.avatar, points=u.points,
                is_member=u.is_member, is_active=u.is_active, created_at=u.created_at,
            ).model_dump()
            for u in rows
        ],
    })


@router.put("/users/{user_id}")
def update_user(user_id: str, body: AppUserUpdate, _admin=Depends(require_permission("user:write")), db: Session = Depends(get_db)):
    user = db.get(AppUser, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    return ApiResponse.ok(AppUserOut(
        id=user.id, nickname=user.nickname, avatar=user.avatar, points=user.points,
        is_member=user.is_member, is_active=user.is_active, created_at=user.created_at,
    ).model_dump())


# ---- 系统设置 ----
@router.get("/settings")
def list_settings(_admin=Depends(require_permission("setting:read")), db: Session = Depends(get_db)):
    rows = db.query(SystemSetting).all()
    return ApiResponse.ok([SettingOut(key=r.key, value=r.value, description=r.description).model_dump() for r in rows])


@router.put("/settings/{key}")
def update_setting(key: str, body: SettingUpdate, _admin=Depends(require_permission("setting:write")), db: Session = Depends(get_db)):
    row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not row:
        raise HTTPException(404, "设置项不存在")
    row.value = body.value
    db.commit()
    return ApiResponse.ok(SettingOut(key=row.key, value=row.value, description=row.description).model_dump())


# ---- 权限与角色 ----
@router.get("/roles")
def list_roles(_admin=Depends(require_permission("admin:read")), db: Session = Depends(get_db)):
    rows = db.query(Role).all()
    return ApiResponse.ok([
        RoleOut(id=r.id, code=r.code, name=r.name, permissions=parse_json(r.permissions, [])).model_dump()
        for r in rows
    ])


@router.get("/permissions")
def list_permissions(_admin=Depends(require_permission("admin:read"))):
    return ApiResponse.ok(PERMISSIONS)


@router.get("/roles/matrix")
def role_matrix(_admin=Depends(require_permission("admin:read"))):
    return ApiResponse.ok(ROLE_PERMISSIONS)


# ---- 爬虫（已关闭）----
# @router.post("/crawler/run")
# def trigger_crawl(_admin=Depends(require_permission("crawler:run")), db: Session = Depends(get_db)):
#     log = run_daily_crawl(db)
#     return ApiResponse.ok(CrawlLogOut(
#         id=log.id, source=log.source, status=log.status,
#         fetched_count=log.fetched_count, new_count=log.new_count,
#         message=log.message, started_at=log.started_at, finished_at=log.finished_at,
#     ).model_dump())
#
#
# @router.get("/crawler/logs")
# def crawl_logs(limit: int = 20, _admin=Depends(require_permission("crawler:read")), db: Session = Depends(get_db)):
#     rows = db.query(CrawlLog).order_by(CrawlLog.started_at.desc()).limit(limit).all()
#     return ApiResponse.ok([
#         CrawlLogOut(
#             id=r.id, source=r.source, status=r.status,
#             fetched_count=r.fetched_count, new_count=r.new_count,
#             message=r.message, started_at=r.started_at, finished_at=r.finished_at,
#         ).model_dump()
#         for r in rows
#     ])


# ===== 知识框架管理 =====


@router.get("/knowledge/trees")
def admin_knowledge_trees(_admin=Depends(require_permission("knowledge:read")), db: Session = Depends(get_db)):
    return ApiResponse.ok([t.model_dump() for t in list_knowledge_trees(db)])


@router.get("/knowledge/tree/{tree_key}")
def admin_knowledge_tree_detail(
    tree_key: str,
    _admin=Depends(require_permission("knowledge:read")),
    db: Session = Depends(get_db),
):
    t = get_knowledge_tree(db, tree_key)
    if not t:
        return ApiResponse.fail("知识树不存在", code=404)
    return ApiResponse.ok(t.model_dump())


@router.get("/knowledge/status")
def admin_knowledge_status(_admin=Depends(require_permission("knowledge:read")), db: Session = Depends(get_db)):
    return ApiResponse.ok(knowledge_sync_status(db))


@router.post("/knowledge/sync")
def admin_knowledge_sync(
    tree_key: str | None = None,
    _admin=Depends(require_permission("knowledge:write")),
    db: Session = Depends(get_db),
):
    result = sync_knowledge(db, only_tree_key=tree_key)
    if "error" in result:
        return ApiResponse.fail(result["error"], code=400)
    return ApiResponse.ok(result)


@router.post("/knowledge/upload-md")
async def admin_knowledge_upload_md(
    file: UploadFile = File(...),
    sync: bool = True,
    _admin=Depends(require_permission("knowledge:write")),
    db: Session = Depends(get_db),
):
    raw = await file.read()
    if not raw:
        return ApiResponse.fail("文件为空", code=400)
    if len(raw) > 1 * 1024 * 1024:
        return ApiResponse.fail("md 文件不能超过 1MB", code=400)
    name = file.filename or ""
    saved_path, err = save_uploaded_md(name, raw)
    if err:
        return ApiResponse.fail(err, code=400)
    tree_key = Path(name).stem
    sync_result: dict = {}
    if sync:
        sync_result = sync_knowledge(db, only_tree_key=tree_key)
        if "error" in sync_result:
            return ApiResponse.fail(sync_result["error"], code=400)
    return ApiResponse.ok({"savedPath": saved_path, "treeKey": tree_key, "sync": sync_result})


@router.post("/knowledge/node")
def admin_knowledge_create_node(
    body: KnowledgeNodeCreate,
    _admin=Depends(require_permission("knowledge:write")),
    db: Session = Depends(get_db),
):
    out = create_knowledge_node(db, body)
    if not out:
        return ApiResponse.fail("创建失败，父节点不存在或不匹配", code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/knowledge/node/{node_id}")
def admin_knowledge_update_node(
    node_id: str,
    body: KnowledgeNodeUpdate,
    _admin=Depends(require_permission("knowledge:write")),
    db: Session = Depends(get_db),
):
    out = update_knowledge_node(db, node_id, body)
    if not out:
        return ApiResponse.fail("节点不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/knowledge/node/{node_id}")
def admin_knowledge_delete_node(
    node_id: str,
    _admin=Depends(require_permission("knowledge:write")),
    db: Session = Depends(get_db),
):
    if not delete_knowledge_node(db, node_id):
        return ApiResponse.fail("节点不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.delete("/knowledge/tree/{tree_key}")
def admin_knowledge_delete_tree(
    tree_key: str,
    _admin=Depends(require_permission("knowledge:write")),
    db: Session = Depends(get_db),
):
    """删除整棵知识树（含所有节点，不删本地 md 文件）"""
    from sqlalchemy import text as _text

    from app.models import KnowledgeNode

    rows = db.query(KnowledgeNode).filter(KnowledgeNode.tree_key == tree_key).all()
    if not rows:
        return ApiResponse.fail("知识树不存在", code=404)
    db.execute(_text("UPDATE knowledge_nodes SET parent_id = NULL WHERE tree_key = :tk"), {"tk": tree_key})
    db.execute(_text("DELETE FROM knowledge_nodes WHERE tree_key = :tk"), {"tk": tree_key})
    db.commit()
    return ApiResponse.ok({"ok": True, "deleted": len(rows)})


# ===== 学习计划模板 =====


@router.get("/plan/templates")
def admin_plan_templates(
    day_type: str | None = None,
    _admin=Depends(require_permission("plan:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([t.model_dump() for t in list_plan_templates(db, day_type)])


@router.post("/plan/templates/seed")
def admin_plan_seed(
    _admin=Depends(require_permission("plan:write")),
    db: Session = Depends(get_db),
):
    """重新 seed 默认模板（不会清空已有，仅当表空时填充）"""
    seed_default_templates(db)
    return ApiResponse.ok({"ok": True})


@router.post("/plan/templates/replace-defaults")
def admin_plan_replace_defaults(
    reset_week_tasks: bool = Query(True, description="是否清空本自然周用户任务以便按新模板重建"),
    _admin=Depends(require_permission("plan:write")),
    db: Session = Depends(get_db),
):
    """用内置周计划覆盖全部模板，并可选重建本周用户任务"""
    result = replace_default_templates(db, reset_week_tasks=reset_week_tasks)
    return ApiResponse.ok(result)


@router.post("/plan/templates/copy-day")
def admin_plan_copy_day(
    from_day: str = Query(..., description="源日 mon~sun"),
    to_day: str = Query(..., description="目标日 mon~sun"),
    replace: bool = Query(True, description="是否先清空目标日再写入"),
    _admin=Depends(require_permission("plan:write")),
    db: Session = Depends(get_db),
):
    """将某一天的计划模板复制到另一天"""
    try:
        result = copy_plan_day_templates(db, from_day=from_day, to_day=to_day, replace=replace)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(result)


@router.post("/plan/templates/sync-pending")
def admin_plan_sync_pending(
    day_type: str | None = Query(None, description="mon~sun，空=全部"),
    horizon_days: int = Query(14, ge=0, le=60),
    _admin=Depends(require_permission("plan:write")),
    db: Session = Depends(get_db),
):
    """手动把模板同步到今天起未开始的用户日清单"""
    try:
        result = sync_templates_to_pending_tasks(db, day_type, horizon_days=horizon_days)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(result)


@router.post("/plan/template")
def admin_plan_create_template(
    body: PlanTemplateCreate,
    _admin=Depends(require_permission("plan:write")),
    db: Session = Depends(get_db),
):
    valid_keys = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
    if body.dayType not in valid_keys:
        return ApiResponse.fail("dayType 必须是 mon/tue/wed/thu/fri/sat/sun", code=400)
    out = create_plan_template(db, body)
    return ApiResponse.ok(out.model_dump())


@router.put("/plan/template/{template_id}")
def admin_plan_update_template(
    template_id: str,
    body: PlanTemplateUpdate,
    _admin=Depends(require_permission("plan:write")),
    db: Session = Depends(get_db),
):
    out = update_plan_template(db, template_id, body)
    if not out:
        return ApiResponse.fail("模板不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/plan/template/{template_id}")
def admin_plan_delete_template(
    template_id: str,
    _admin=Depends(require_permission("plan:write")),
    db: Session = Depends(get_db),
):
    if not delete_plan_template(db, template_id):
        return ApiResponse.fail("模板不存在", code=404)
    return ApiResponse.ok({"ok": True})


# ===== 试卷题库管理 =====


@router.get("/exam/papers")
def admin_exam_papers(
    exam_type: str | None = None,
    subject: str | None = None,
    year: int | None = None,
    is_published: bool | None = None,
    _admin=Depends(require_permission("exam:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([p.model_dump() for p in list_exam_papers(
        db, exam_type=exam_type, subject=subject, year=year, is_published=is_published
    )])


@router.post("/exam/paper")
def admin_exam_create_paper(
    body: ExamPaperCreate,
    _admin=Depends(require_permission("exam:write")),
    db: Session = Depends(get_db),
):
    out = create_exam_paper(db, body)
    return ApiResponse.ok(out.model_dump())


@router.put("/exam/paper/{paper_id}")
def admin_exam_update_paper(
    paper_id: str,
    body: ExamPaperUpdate,
    _admin=Depends(require_permission("exam:write")),
    db: Session = Depends(get_db),
):
    out = update_exam_paper(db, paper_id, body)
    if not out:
        return ApiResponse.fail("试卷不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/exam/paper/{paper_id}")
def admin_exam_delete_paper(
    paper_id: str,
    _admin=Depends(require_permission("exam:write")),
    db: Session = Depends(get_db),
):
    if not delete_exam_paper(db, paper_id):
        return ApiResponse.fail("试卷不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.post("/exam/paper/{paper_id}/question")
def admin_exam_create_question(
    paper_id: str,
    body: ExamQuestionCreate,
    _admin=Depends(require_permission("exam:write")),
    db: Session = Depends(get_db),
):
    out = create_exam_question(db, paper_id, body)
    if not out:
        return ApiResponse.fail("试卷不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.put("/exam/question/{question_id}")
def admin_exam_update_question(
    question_id: str,
    body: ExamQuestionUpdate,
    _admin=Depends(require_permission("exam:write")),
    db: Session = Depends(get_db),
):
    out = update_exam_question(db, question_id, body)
    if not out:
        return ApiResponse.fail("题目不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/exam/question/{question_id}")
def admin_exam_delete_question(
    question_id: str,
    _admin=Depends(require_permission("exam:write")),
    db: Session = Depends(get_db),
):
    if not delete_exam_question(db, question_id):
        return ApiResponse.fail("题目不存在", code=404)
    return ApiResponse.ok({"ok": True})


class ExamImportPreviewBody(BaseModel):
    """不实际导入，先预览解析结果"""
    fileName: str
    content: str


@router.post("/exam/paper/{paper_id}/import-preview")
def admin_exam_import_preview(
    paper_id: str,
    body: ExamImportPreviewBody,
    _admin=Depends(require_permission("exam:write")),
    db: Session = Depends(get_db),
):
    p = get_exam_paper(db, paper_id)
    if not p:
        return ApiResponse.fail("试卷不存在", code=404)
    questions, errors = parse_exam_import(body.fileName, body.content)
    return ApiResponse.ok({
        "parsed": len(questions),
        "errors": errors,
        "preview": questions[:5],
        "totalCount": len(questions),
    })


class ExamImportConfirmBody(BaseModel):
    fileName: str
    content: str


@router.post("/exam/paper/{paper_id}/import")
def admin_exam_import(
    paper_id: str,
    body: ExamImportConfirmBody,
    _admin=Depends(require_permission("exam:write")),
    db: Session = Depends(get_db),
):
    p = get_exam_paper(db, paper_id)
    if not p:
        return ApiResponse.fail("试卷不存在", code=404)
    questions, errors = parse_exam_import(body.fileName, body.content)
    if not questions:
        return ApiResponse.fail(errors[0] if errors else "未解析到题目", code=400)
    result = batch_create_exam_questions(db, paper_id, questions)
    if not result.get("ok"):
        return ApiResponse.fail(result.get("error", "导入失败"), code=400)
    return ApiResponse.ok(result)


@router.post("/exam/paper/upload")
async def admin_exam_upload(
    file: UploadFile = File(...),
    _admin=Depends(require_permission("exam:write")),
):
    """上传题库文件（仅解析，不入库，返回解析结果供预览）"""
    raw = await file.read()
    if not raw:
        return ApiResponse.fail("文件为空", code=400)
    if len(raw) > 2 * 1024 * 1024:
        return ApiResponse.fail("文件不能超过 2MB", code=400)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("gbk")
        except UnicodeDecodeError:
            return ApiResponse.fail("文件编码不支持，请用 UTF-8", code=400)
    questions, errors = parse_exam_import(file.filename or "", text)
    return ApiResponse.ok({
        "fileName": file.filename,
        "parsed": len(questions),
        "errors": errors,
        "preview": questions[:5],
        "totalCount": len(questions),
        "questions": questions,
    })


# ===== 英语学习内容管理 =====


# 文章
@router.get("/english/articles")
def admin_english_articles(
    level: str | None = None,
    _admin=Depends(require_permission("english:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([a.model_dump() for a in list_english_articles(db, level=level, is_published=None)])


@router.post("/english/article")
def admin_english_create_article(
    body: EnglishArticleCreate,
    _admin=Depends(require_permission("english:write")),
    db: Session = Depends(get_db),
):
    out = create_english_article(db, body)
    return ApiResponse.ok(out.model_dump())


@router.put("/english/article/{article_id}")
def admin_english_update_article(
    article_id: str,
    body: EnglishArticleUpdate,
    _admin=Depends(require_permission("english:write")),
    db: Session = Depends(get_db),
):
    out = update_english_article(db, article_id, body)
    if not out:
        return ApiResponse.fail("文章不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/english/article/{article_id}")
def admin_english_delete_article(
    article_id: str,
    _admin=Depends(require_permission("english:write")),
    db: Session = Depends(get_db),
):
    if not delete_english_article(db, article_id):
        return ApiResponse.fail("文章不存在", code=404)
    return ApiResponse.ok({"ok": True})


# 口语
@router.get("/english/speaking")
def admin_english_speaking_list(
    _admin=Depends(require_permission("english:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([s.model_dump() for s in list_speaking_lessons_admin(db)])


@router.post("/english/speaking")
def admin_english_create_speaking(
    body: SpeakingLessonCreate,
    _admin=Depends(require_permission("english:write")),
    db: Session = Depends(get_db),
):
    out = create_speaking_lesson_svc(db, body)
    return ApiResponse.ok(out.model_dump())


@router.put("/english/speaking/{lesson_id}")
def admin_english_update_speaking(
    lesson_id: str,
    body: dict,
    _admin=Depends(require_permission("english:write")),
    db: Session = Depends(get_db),
):
    out = update_speaking_lesson_svc(db, lesson_id, body)
    if not out:
        return ApiResponse.fail("课程不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/english/speaking/{lesson_id}")
def admin_english_delete_speaking(
    lesson_id: str,
    _admin=Depends(require_permission("english:write")),
    db: Session = Depends(get_db),
):
    if not delete_speaking_lesson_svc(db, lesson_id):
        return ApiResponse.fail("课程不存在", code=404)
    return ApiResponse.ok({"ok": True})


# 语法
@router.get("/english/grammar")
def admin_english_grammar_list(
    _admin=Depends(require_permission("english:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([g.model_dump() for g in list_grammar_lessons_admin(db)])


@router.post("/english/grammar")
def admin_english_create_grammar(
    body: GrammarLessonCreate,
    _admin=Depends(require_permission("english:write")),
    db: Session = Depends(get_db),
):
    out = create_grammar_lesson_svc(db, body)
    return ApiResponse.ok(out.model_dump())


@router.put("/english/grammar/{lesson_id}")
def admin_english_update_grammar(
    lesson_id: str,
    body: dict,
    _admin=Depends(require_permission("english:write")),
    db: Session = Depends(get_db),
):
    out = update_grammar_lesson_svc(db, lesson_id, body)
    if not out:
        return ApiResponse.fail("课程不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/english/grammar/{lesson_id}")
def admin_english_delete_grammar(
    lesson_id: str,
    _admin=Depends(require_permission("english:write")),
    db: Session = Depends(get_db),
):
    if not delete_grammar_lesson_svc(db, lesson_id):
        return ApiResponse.fail("课程不存在", code=404)
    return ApiResponse.ok({"ok": True})


# ===== 音标管理 =====


@router.get("/english/phonetics")
def admin_phonetics_list(
    category: str | None = None,
    _admin=Depends(require_permission("english:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([p.model_dump() for p in list_phonetics_admin(db, category)])


@router.post("/english/phonetic")
def admin_phonetic_create(
    body: PhoneticLessonCreate,
    _admin=Depends(require_permission("english:write")),
    db: Session = Depends(get_db),
):
    out = create_phonetic_svc(db, body)
    return ApiResponse.ok(out.model_dump())


@router.put("/english/phonetic/{lesson_id}")
def admin_phonetic_update(
    lesson_id: str,
    body: dict,
    _admin=Depends(require_permission("english:write")),
    db: Session = Depends(get_db),
):
    out = update_phonetic_svc(db, lesson_id, body)
    if not out:
        return ApiResponse.fail("音标不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/english/phonetic/{lesson_id}")
def admin_phonetic_delete(
    lesson_id: str,
    _admin=Depends(require_permission("english:write")),
    db: Session = Depends(get_db),
):
    if not delete_phonetic_svc(db, lesson_id):
        return ApiResponse.fail("音标不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.post("/english/phonetics/seed")
def admin_phonetics_seed(
    _admin=Depends(require_permission("english:write")),
    db: Session = Depends(get_db),
):
    seed_default_phonetics(db)
    return ApiResponse.ok({"ok": True})


# ===== 人民日报模块 =====


@router.get("/rmrb/articles")
def admin_rmrb_articles(
    tag: str | None = None,
    _admin=Depends(require_permission("rmrb:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(
        [a.model_dump() for a in list_rmrb_articles_admin(db, published_only=False, tag=tag)]
    )


@router.post("/rmrb/article")
def admin_rmrb_create_article(
    body: RmrbArticleCreate,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    if not (body.title or "").strip():
        return ApiResponse.fail("标题不能为空", code=400)
    out = create_rmrb_article(db, body)
    return ApiResponse.ok(out.model_dump())


@router.put("/rmrb/article/{article_id}")
def admin_rmrb_update_article(
    article_id: str,
    body: RmrbArticleUpdate,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    out = update_rmrb_article(db, article_id, body)
    if not out:
        return ApiResponse.fail("文章不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/rmrb/article/{article_id}")
def admin_rmrb_delete_article(
    article_id: str,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    if not delete_rmrb_article(db, article_id):
        return ApiResponse.fail("文章不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.get("/rmrb/meta")
def admin_rmrb_meta(
    _admin=Depends(require_permission("rmrb:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(get_rmrb_meta(db, enabled_only=False).model_dump())


# ---- 规范词分类 ----

@router.get("/rmrb/term-categories")
def admin_rmrb_term_categories(
    _admin=Depends(require_permission("rmrb:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([c.model_dump() for c in list_rmrb_term_categories(db)])


@router.post("/rmrb/term-categories")
def admin_rmrb_create_term_category(
    body: ShenlunTermCategoryCreate,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    try:
        out = create_rmrb_term_category(db, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/rmrb/term-categories/{cat_id}")
def admin_rmrb_update_term_category(
    cat_id: str,
    body: ShenlunTermCategoryUpdate,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    try:
        out = update_rmrb_term_category(db, cat_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("分类不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/rmrb/term-categories/{cat_id}")
def admin_rmrb_delete_term_category(
    cat_id: str,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    if not delete_rmrb_term_category(db, cat_id):
        return ApiResponse.fail("分类不存在", code=404)
    return ApiResponse.ok({"ok": True})


# ---- 骨架模版 ----

@router.get("/rmrb/skeleton-templates")
def admin_rmrb_skeletons(
    _admin=Depends(require_permission("rmrb:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([t.model_dump() for t in list_rmrb_skeletons(db)])


@router.post("/rmrb/skeleton-templates")
def admin_rmrb_create_skeleton(
    body: ShenlunSkeletonTemplateCreate,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    try:
        out = create_rmrb_skeleton(db, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/rmrb/skeleton-templates/{tpl_id}")
def admin_rmrb_update_skeleton(
    tpl_id: str,
    body: ShenlunSkeletonTemplateUpdate,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    try:
        out = update_rmrb_skeleton(db, tpl_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("模版不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/rmrb/skeleton-templates/{tpl_id}")
def admin_rmrb_delete_skeleton(
    tpl_id: str,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    if not delete_rmrb_skeleton(db, tpl_id):
        return ApiResponse.fail("模版不存在", code=404)
    return ApiResponse.ok({"ok": True})


# ---- 句式类型 ----

@router.get("/rmrb/sentence-types")
def admin_rmrb_sentence_types(
    _admin=Depends(require_permission("rmrb:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([t.model_dump() for t in list_rmrb_sentence_types(db)])


@router.post("/rmrb/sentence-types")
def admin_rmrb_create_sentence_type(
    body: ShenlunSentenceTypeCreate,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    try:
        out = create_rmrb_sentence_type(db, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/rmrb/sentence-types/{type_id}")
def admin_rmrb_update_sentence_type(
    type_id: str,
    body: ShenlunSentenceTypeUpdate,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    try:
        out = update_rmrb_sentence_type(db, type_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("类型不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/rmrb/sentence-types/{type_id}")
def admin_rmrb_delete_sentence_type(
    type_id: str,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    if not delete_rmrb_sentence_type(db, type_id):
        return ApiResponse.fail("类型不存在", code=404)
    return ApiResponse.ok({"ok": True})


# ---- 论证方法 ----

@router.get("/rmrb/argument-methods")
def admin_rmrb_argument_methods(
    _admin=Depends(require_permission("rmrb:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([t.model_dump() for t in list_rmrb_argument_methods(db)])


@router.post("/rmrb/argument-methods")
def admin_rmrb_create_argument_method(
    body: ShenlunArgumentMethodCreate,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    try:
        out = create_rmrb_argument_method(db, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/rmrb/argument-methods/{method_id}")
def admin_rmrb_update_argument_method(
    method_id: str,
    body: ShenlunArgumentMethodUpdate,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    try:
        out = update_rmrb_argument_method(db, method_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("方法不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/rmrb/argument-methods/{method_id}")
def admin_rmrb_delete_argument_method(
    method_id: str,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    if not delete_rmrb_argument_method(db, method_id):
        return ApiResponse.fail("方法不存在", code=404)
    return ApiResponse.ok({"ok": True})


# ===== 资料分析管理 =====


@router.get("/ziliao/formulas")
def admin_ziliao_formulas(
    _admin=Depends(require_permission("ziliao:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([x.model_dump() for x in list_ziliao_formulas_admin(db, published_only=False)])


@router.post("/ziliao/formulas")
def admin_ziliao_create_formula(
    body: ZiliaoFormulaCreate,
    _admin=Depends(require_permission("ziliao:write")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(create_ziliao_formula(db, body).model_dump())


@router.post("/ziliao/formulas/import-json")
def admin_ziliao_import_formulas_json(
    body: ZiliaoFormulaImportBody,
    _admin=Depends(require_permission("ziliao:write")),
    db: Session = Depends(get_db),
):
    result = import_ziliao_formulas_from_json(
        db,
        body.content,
        overwrite=body.overwrite,
        publish_default=body.publishDefault,
    )
    return ApiResponse.ok(result.model_dump())


@router.post("/ziliao/formulas/upload-json")
async def admin_ziliao_upload_formulas_json(
    file: UploadFile = File(...),
    overwrite: bool = Query(True),
    publish_default: bool = Query(True),
    _admin=Depends(require_permission("ziliao:write")),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".json"):
        return ApiResponse.fail("仅支持 .json 文件")
    data = await file.read()
    if len(data) > 2 * 1024 * 1024:
        return ApiResponse.fail("文件不能超过 2MB")
    try:
        content = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return ApiResponse.fail("文件必须使用 UTF-8 编码")
    result = import_ziliao_formulas_from_json(
        db,
        content,
        overwrite=overwrite,
        publish_default=publish_default,
    )
    return ApiResponse.ok(result.model_dump())


@router.put("/ziliao/formulas/{formula_id}")
def admin_ziliao_update_formula(
    formula_id: str,
    body: ZiliaoFormulaUpdate,
    _admin=Depends(require_permission("ziliao:write")),
    db: Session = Depends(get_db),
):
    out = update_ziliao_formula(db, formula_id, body)
    if not out:
        return ApiResponse.fail("公式不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/ziliao/formulas/{formula_id}")
def admin_ziliao_delete_formula(
    formula_id: str,
    _admin=Depends(require_permission("ziliao:write")),
    db: Session = Depends(get_db),
):
    if not delete_ziliao_formula(db, formula_id):
        return ApiResponse.fail("公式不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.get("/ziliao/types")
def admin_ziliao_types(
    _admin=Depends(require_permission("ziliao:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([x.model_dump() for x in list_ziliao_types_admin(db, published_only=False)])


@router.post("/ziliao/types")
def admin_ziliao_create_type(
    body: ZiliaoQuestionTypeCreate,
    _admin=Depends(require_permission("ziliao:write")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(create_ziliao_type(db, body).model_dump())


@router.put("/ziliao/types/{type_id}")
def admin_ziliao_update_type(
    type_id: str,
    body: ZiliaoQuestionTypeUpdate,
    _admin=Depends(require_permission("ziliao:write")),
    db: Session = Depends(get_db),
):
    out = update_ziliao_type(db, type_id, body)
    if not out:
        return ApiResponse.fail("题型不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/ziliao/types/{type_id}")
def admin_ziliao_delete_type(
    type_id: str,
    _admin=Depends(require_permission("ziliao:write")),
    db: Session = Depends(get_db),
):
    if not delete_ziliao_type(db, type_id):
        return ApiResponse.fail("题型不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.get("/ziliao/tricks")
def admin_ziliao_tricks(
    _admin=Depends(require_permission("ziliao:read")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([x.model_dump() for x in list_ziliao_tricks_admin(db, published_only=False)])


@router.post("/ziliao/tricks")
def admin_ziliao_create_trick(
    body: ZiliaoTrickCreate,
    _admin=Depends(require_permission("ziliao:write")),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(create_ziliao_trick(db, body).model_dump())


@router.put("/ziliao/tricks/{trick_id}")
def admin_ziliao_update_trick(
    trick_id: str,
    body: ZiliaoTrickUpdate,
    _admin=Depends(require_permission("ziliao:write")),
    db: Session = Depends(get_db),
):
    out = update_ziliao_trick(db, trick_id, body)
    if not out:
        return ApiResponse.fail("技巧不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/ziliao/tricks/{trick_id}")
def admin_ziliao_delete_trick(
    trick_id: str,
    _admin=Depends(require_permission("ziliao:write")),
    db: Session = Depends(get_db),
):
    if not delete_ziliao_trick(db, trick_id):
        return ApiResponse.fail("技巧不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.post("/ziliao/seed")
def admin_ziliao_seed(
    force: bool = Query(False),
    _admin=Depends(require_permission("ziliao:write")),
    db: Session = Depends(get_db),
):
    counts = seed_ziliao_resources(db, force=force)
    seeded_paper = seed_sample_drill_paper(db)
    return ApiResponse.ok({**counts, "samplePaper": seeded_paper})


@router.get("/ziliao/import-guide")
def admin_ziliao_import_guide(
    _admin=Depends(require_permission("ziliao:read")),
):
    path = Path(__file__).resolve().parents[3] / "data" / "ziliao" / "IMPORT.md"
    text = path.read_text(encoding="utf-8") if path.exists() else "导入规范文件缺失：server/data/ziliao/IMPORT.md"
    return ApiResponse.ok({"markdown": text, "examplePath": "server/data/ziliao/examples/guokao-style-sample.md"})


# ---- 三刀解剖导入 ----

class ThreeKnifeImportBody(BaseModel):
    markdown: str
    userId: str | None = None  # 指定用户；为空则用管理员关联的默认用户


@router.post("/rmrb/import-three-knife")
def admin_rmrb_import_three_knife(
    body: ThreeKnifeImportBody,
    _admin=Depends(require_permission("rmrb:write")),
    db: Session = Depends(get_db),
):
    """解析三刀解剖 Markdown 并存入开采本（ShenlunMineLog）。"""
    from app.services.shenlun_import_service import parse_three_knife_markdown
    from app.services.shenlun_service import upsert_mine

    md = (body.markdown or "").strip()
    if not md:
        return ApiResponse.fail("Markdown 内容不能为空", code=400)

    # 确定目标用户
    if body.userId:
        user = db.get(AppUser, body.userId)
        if not user:
            return ApiResponse.fail("指定用户不存在", code=404)
    else:
        # 取第一个管理员关联用户或系统第一个用户
        user = db.query(AppUser).first()
        if not user:
            return ApiResponse.fail("系统中暂无用户", code=400)

    try:
        parsed = parse_three_knife_markdown(md)
    except Exception as e:
        return ApiResponse.fail(f"Markdown 解析失败：{e}", code=400)

    if not parsed.articleTitle:
        return ApiResponse.fail("未能从 Markdown 中解析出文章标题", code=400)

    out = upsert_mine(db, user, parsed)
    return ApiResponse.ok({
        "mine": out.model_dump(),
        "summary": {
            "articleTitle": parsed.articleTitle,
            "mineDate": parsed.mineDate,
            "termsCount": len(parsed.terms),
            "quotesCount": len(parsed.quotes),
            "verbsCount": len(parsed.verbs),
            "pointsCount": len(parsed.argument.points) if parsed.argument else 0,
            "templatesCount": len(parsed.templates),
        },
    })


@router.post("/rmrb/preview-three-knife")
def admin_rmrb_preview_three_knife(
    body: ThreeKnifeImportBody,
    _admin=Depends(require_permission("rmrb:read")),
):
    """仅解析不保存，返回结构化预览。"""
    from app.services.shenlun_import_service import parse_three_knife_markdown

    md = (body.markdown or "").strip()
    if not md:
        return ApiResponse.fail("Markdown 内容不能为空", code=400)

    try:
        parsed = parse_three_knife_markdown(md)
    except Exception as e:
        return ApiResponse.fail(f"Markdown 解析失败：{e}", code=400)

    return ApiResponse.ok({
        "parsed": parsed.model_dump(),
        "summary": {
            "articleTitle": parsed.articleTitle,
            "mineDate": parsed.mineDate,
            "termsCount": len(parsed.terms),
            "quotesCount": len(parsed.quotes),
            "verbsCount": len(parsed.verbs),
            "pointsCount": len(parsed.argument.points) if parsed.argument else 0,
            "templatesCount": len(parsed.templates),
        },
    })


# ============================================================
# 语料本管理（corpus）
# ============================================================

@router.get("/corpus/items")
def admin_corpus_items(
    user_id: str | None = None,
    status: str | None = None,
    kind: str | None = None,
    q: str | None = None,
    _admin=Depends(require_permission("corpus:read")),
    db: Session = Depends(get_db),
):
    """跨用户查看语料本条目。"""
    query = db.query(CorpusItem)
    if user_id:
        query = query.filter(CorpusItem.user_id == user_id)
    if status:
        query = query.filter(CorpusItem.status == status)
    if kind:
        query = query.filter(CorpusItem.kind == kind)
    if q:
        query = query.filter(CorpusItem.original.contains(q))
    items = query.order_by(CorpusItem.created_at.desc()).limit(200).all()
    from app.services.corpus_service import _item_out
    return ApiResponse.ok([_item_out(i).model_dump() for i in items])


@router.get("/corpus/stats")
def admin_corpus_stats(
    user_id: str | None = None,
    _admin=Depends(require_permission("corpus:read")),
    db: Session = Depends(get_db),
):
    """语料本统计（可按用户筛选）。"""
    from sqlalchemy import func
    base = db.query(CorpusItem.status, func.count(CorpusItem.id))
    if user_id:
        base = base.filter(CorpusItem.user_id == user_id)
    rows = base.group_by(CorpusItem.status).all()
    stats = {s: c for s, c in rows}
    return ApiResponse.ok({
        "total": sum(stats.values()),
        "inbox": stats.get("inbox", 0),
        "clarified": stats.get("clarified", 0),
        "owned": stats.get("owned", 0),
        "used": stats.get("used", 0),
    })


@router.put("/corpus/item/{item_id}")
def admin_corpus_update_item(
    item_id: str,
    body: dict,
    _admin=Depends(require_permission("corpus:write")),
    db: Session = Depends(get_db),
):
    """管理员编辑语料条目（状态/标签/备注等）。"""
    item = db.get(CorpusItem, item_id)
    if not item:
        return ApiResponse.fail("条目不存在", code=404)
    allowed = {"status", "plain_note", "rewrite", "practice", "tags_json", "kind", "source_type", "source_title"}
    for k, v in body.items():
        if k in allowed:
            setattr(item, k, v)
    db.commit()
    db.refresh(item)
    from app.services.corpus_service import _item_out
    return ApiResponse.ok(_item_out(item).model_dump())


@router.delete("/corpus/item/{item_id}")
def admin_corpus_delete_item(
    item_id: str,
    _admin=Depends(require_permission("corpus:write")),
    db: Session = Depends(get_db),
):
    item = db.get(CorpusItem, item_id)
    if not item:
        return ApiResponse.fail("条目不存在", code=404)
    db.delete(item)
    db.commit()
    return ApiResponse.ok({"ok": True})


# ============================================================
# 时事事件管理（events）
# ============================================================

@router.get("/events/list")
def admin_events_list(
    user_id: str | None = None,
    tree_key: str | None = None,
    q: str | None = None,
    _admin=Depends(require_permission("events:read")),
    db: Session = Depends(get_db),
):
    """跨用户查看时事事件。"""
    query = db.query(EventImpression)
    if user_id:
        query = query.filter(EventImpression.user_id == user_id)
    if tree_key:
        query = query.filter(EventImpression.knowledge_tree_key == tree_key)
    if q:
        query = query.filter(EventImpression.title.contains(q))
    items = query.order_by(EventImpression.event_date.desc()).limit(200).all()
    from app.services.event_impression_service import _to_out
    return ApiResponse.ok([_to_out(i).model_dump() for i in items])


@router.get("/events/hub")
def admin_events_hub(
    user_id: str,
    _admin=Depends(require_permission("events:read")),
    db: Session = Depends(get_db),
):
    """指定用户的事件中心概览。"""
    user = db.get(AppUser, user_id)
    if not user:
        return ApiResponse.fail("用户不存在", code=404)
    from app.services.event_impression_service import get_hub
    return ApiResponse.ok(get_hub(db, user).model_dump())


@router.put("/events/{event_id}")
def admin_events_update(
    event_id: str,
    body: dict,
    _admin=Depends(require_permission("events:write")),
    db: Session = Depends(get_db),
):
    ev = db.get(EventImpression, event_id)
    if not ev:
        return ApiResponse.fail("事件不存在", code=404)
    allowed = {"title", "event_date", "place", "core_content", "note",
               "knowledge_node_id", "knowledge_tree_key", "knowledge_path"}
    for k, v in body.items():
        if k in allowed:
            setattr(ev, k, v)
    db.commit()
    db.refresh(ev)
    from app.services.event_impression_service import _to_out
    return ApiResponse.ok(_to_out(ev).model_dump())


@router.delete("/events/{event_id}")
def admin_events_delete(
    event_id: str,
    _admin=Depends(require_permission("events:write")),
    db: Session = Depends(get_db),
):
    ev = db.get(EventImpression, event_id)
    if not ev:
        return ApiResponse.fail("事件不存在", code=404)
    db.delete(ev)
    db.commit()
    return ApiResponse.ok({"ok": True})


# ============================================================
# 健康数据看板（health）
# ============================================================

@router.get("/health/users")
def admin_health_users(
    _admin=Depends(require_permission("health:read")),
    db: Session = Depends(get_db),
):
    """所有开启健康计划的用户及其阶段进度。"""
    states = db.query(HealthUserState).all()
    out = []
    for s in states:
        user = db.get(AppUser, s.user_id)
        out.append({
            "userId": s.user_id,
            "nickname": user.nickname if user else "",
            "programStartDate": s.program_start_date,
            "privateFocus": s.private_focus,
        })
    return ApiResponse.ok(out)


@router.get("/health/overview")
def admin_health_overview(
    user_id: str,
    _admin=Depends(require_permission("health:read")),
    db: Session = Depends(get_db),
):
    """指定用户的健康总览。"""
    user = db.get(AppUser, user_id)
    if not user:
        return ApiResponse.fail("用户不存在", code=404)
    from app.services.health_service import get_overview
    return ApiResponse.ok(get_overview(db, user).model_dump())


@router.get("/health/daily")
def admin_health_daily(
    user_id: str,
    start: str | None = None,
    end: str | None = None,
    _admin=Depends(require_permission("health:read")),
    db: Session = Depends(get_db),
):
    """指定用户的每日打卡记录（支持日期范围）。"""
    user = db.get(AppUser, user_id)
    if not user:
        return ApiResponse.fail("用户不存在", code=404)
    if start and end:
        from app.services.health_service import list_daily_range
        logs = list_daily_range(db, user, start, end)
    else:
        from app.services.health_service import get_daily
        log = get_daily(db, user)
        logs = [log] if log else []
    return ApiResponse.ok([l.model_dump() for l in logs])


@router.get("/health/phases")
def admin_health_phases(
    _admin=Depends(require_permission("health:read")),
):
    """8 周阶段计划定义（全局）。"""
    from app.services.health_service import list_phases
    return ApiResponse.ok([p.model_dump() for p in list_phases()])


# ============================================================
# 读书内容管理（dushu）
# ============================================================

@router.get("/dushu/books")
def admin_dushu_books(
    user_id: str | None = None,
    status: str | None = None,
    _admin=Depends(require_permission("dushu:read")),
    db: Session = Depends(get_db),
):
    """跨用户查看书架。"""
    query = db.query(DushuBook)
    if user_id:
        query = query.filter(DushuBook.user_id == user_id)
    if status:
        query = query.filter(DushuBook.status == status)
    books = query.order_by(DushuBook.created_at.desc()).all()
    from app.services.dushu_service import _book_out
    return ApiResponse.ok([_book_out(b).model_dump() for b in books])


@router.get("/dushu/daily")
def admin_dushu_daily(
    user_id: str,
    book_id: str | None = None,
    _admin=Depends(require_permission("dushu:read")),
    db: Session = Depends(get_db),
):
    """指定用户的每日阅读输出卡。"""
    user = db.get(AppUser, user_id)
    if not user:
        return ApiResponse.fail("用户不存在", code=404)
    from app.services.dushu_service import list_daily
    return ApiResponse.ok([d.model_dump() for d in list_daily(db, user, book_id)])


@router.get("/dushu/persons")
def admin_dushu_persons(
    user_id: str,
    book_id: str | None = None,
    _admin=Depends(require_permission("dushu:read")),
    db: Session = Depends(get_db),
):
    """指定用户的历史人物卡。"""
    user = db.get(AppUser, user_id)
    if not user:
        return ApiResponse.fail("用户不存在", code=404)
    from app.services.dushu_service import list_persons
    return ApiResponse.ok([p.model_dump() for p in list_persons(db, user, book_id)])


@router.get("/dushu/summaries")
def admin_dushu_summaries(
    user_id: str,
    _admin=Depends(require_permission("dushu:read")),
    db: Session = Depends(get_db),
):
    """指定用户的一书一页总结。"""
    user = db.get(AppUser, user_id)
    if not user:
        return ApiResponse.fail("用户不存在", code=404)
    from app.services.dushu_service import list_summaries
    return ApiResponse.ok([s.model_dump() for s in list_summaries(db, user)])


@router.get("/dushu/stats")
def admin_dushu_stats(
    user_id: str,
    _admin=Depends(require_permission("dushu:read")),
    db: Session = Depends(get_db),
):
    """指定用户的读书统计。"""
    user = db.get(AppUser, user_id)
    if not user:
        return ApiResponse.fail("用户不存在", code=404)
    from app.services.dushu_service import get_stats
    return ApiResponse.ok(get_stats(db, user).model_dump())


@router.put("/dushu/book/{book_id}")
def admin_dushu_update_book(
    book_id: str,
    body: dict,
    _admin=Depends(require_permission("dushu:write")),
    db: Session = Depends(get_db),
):
    book = db.get(DushuBook, book_id)
    if not book:
        return ApiResponse.fail("书籍不存在", code=404)
    allowed = {"title", "author", "category", "status", "current_chapter", "cover_note"}
    for k, v in body.items():
        if k in allowed:
            setattr(book, k, v)
    db.commit()
    db.refresh(book)
    from app.services.dushu_service import _book_out
    return ApiResponse.ok(_book_out(book).model_dump())


@router.delete("/dushu/book/{book_id}")
def admin_dushu_delete_book(
    book_id: str,
    _admin=Depends(require_permission("dushu:write")),
    db: Session = Depends(get_db),
):
    book = db.get(DushuBook, book_id)
    if not book:
        return ApiResponse.fail("书籍不存在", code=404)
    # 级联删除关联的日志、人物卡、总结
    db.query(DushuDailyLog).filter(DushuDailyLog.book_id == book_id).delete()
    db.query(DushuPersonCard).filter(DushuPersonCard.book_id == book_id).delete()
    db.query(DushuBookSummary).filter(DushuBookSummary.book_id == book_id).delete()
    db.delete(book)
    db.commit()
    return ApiResponse.ok({"ok": True})
