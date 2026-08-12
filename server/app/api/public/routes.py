from fastapi import APIRouter, Depends, File, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_app_user
from app.core.response import ApiResponse
from app.database import get_db
from app.models import AppUser, Article, PointsLog, Question, SignRecord
from app.services.activity_service import record_event
from app.schemas import (
    AnswerResult,
    AnswerSubmit,
    AppAuthToken,
    AppLoginBody,
    AppRegisterBody,
    AppUserPasswordChange,
    AppUserProfileUpdate,
    DailyReviewUpsert,
    DayPlanOut,
    ExamAnswerSubmit,
    ExamCountdownOut,
    ExamCountdownUpsert,
    ExamPaperCreate,
    ExamPaperOut,
    ExamPaperUpdate,
    ExamQuestionCreate,
    ExamQuestionOut,
    ExamQuestionUpdate,
    KnowledgeNodeUpdate,
    KnowledgeReviewAnswerBody,
    KnowledgeReviewSessionBody,
    KnowledgeTreeOut,
    ManualWrongCreate,
    ManualWrongOut,
    ManualWrongUpdate,
    ShenlunMineLogUpdate,
    ShenlunMineLogUpsert,
    ShenlunNormTermAdd,
    ShenlunNormTermUpdate,
    ShenlunDrillCreate,
    ShenlunSkeletonTemplateCreate,
    ShenlunTermCategoryCreate,
    CorpusItemCreate,
    CorpusItemUpdate,
    EventImpressionCreate,
    EventImpressionUpdate,
    PlanTaskCreate,
    PlanTaskOut,
    PlanTaskUpdate,
    PointsLogOut,
    QuizCompleteBody,
    QuizCompleteResult,
    QuizRankItemOut,
    QuizStatsOut,
    RankItemOut,
    ReviewCompleteBody,
    SectionReadBody,
    StudyRecordOut,
    UserMeOut,
    WrongRedoBody,
    ZiliaoDrillSubmitIn,
)
from app.services.auth_service import (
    authenticate_user,
    change_user_password,
    issue_app_token,
    register_user,
    update_user_profile,
)
from app.services.category_service import build_category_tree
from app.services.countdown_service import delete_countdown, get_countdown, upsert_countdown
from app.services.knowledge_service import (
    get_tree as get_knowledge_tree,
    list_trees as list_knowledge_trees,
    save_uploaded_md,
    sync_knowledge,
    sync_status as knowledge_sync_status,
    update_node as update_knowledge_node,
)
from app.services.knowledge_review_service import (
    answer_review as answer_knowledge_review,
    create_session as create_knowledge_review_session,
    get_due as get_knowledge_review_due,
)
from app.services.review_hub_service import get_review_hub
from app.services.manual_wrong_service import (
    create_wrong,
    delete_wrong,
    list_wrongs,
    review_wrong as review_manual_wrong,
    update_wrong,
)
from app.services.exam_service import (
    finish_attempt as finish_exam_attempt,
    get_attempt_detail as get_exam_attempt_detail,
    get_paper_detail as get_exam_paper_detail,
    list_papers as list_exam_papers,
    list_user_attempts as list_exam_attempts,
    start_attempt as start_exam_attempt,
    submit_answer as submit_exam_answer,
)
from app.services.ziliao_service import (
    get_drill_set as get_ziliao_drill_set,
    get_formula as get_ziliao_formula,
    get_overview as get_ziliao_overview,
    get_trick as get_ziliao_trick,
    get_type as get_ziliao_type,
    list_drill_sets as list_ziliao_drill_sets,
    list_formulas as list_ziliao_formulas,
    list_tricks as list_ziliao_tricks,
    list_types as list_ziliao_types,
    submit_drill as submit_ziliao_drill,
)
from app.services.rmrb_service import (
    get_article as get_rmrb_article,
    list_articles as list_rmrb_articles,
)
from app.services.rmrb_meta_service import (
    create_skeleton_template as create_rmrb_skeleton,
    create_term_category as create_rmrb_term_category,
    get_meta as get_rmrb_meta,
)
from app.services.growth_service import get_growth_overview
from app.services.corpus_service import (
    create_item as create_corpus_item,
    delete_item as delete_corpus_item,
    get_item as get_corpus_item,
    get_stats as get_corpus_stats,
    list_items as list_corpus_items,
    promote_to_term as promote_corpus_to_term,
    update_item as update_corpus_item,
)
from app.services.event_impression_service import (
    create_event as create_event_impression,
    delete_event as delete_event_impression,
    get_event as get_event_impression,
    get_hub as get_event_hub,
    list_events as list_event_impressions,
    update_event as update_event_impression,
)
from app.services.shenlun_service import (
    add_drill as add_shenlun_drill,
    add_term as add_shenlun_term,
    delete_mine as delete_shenlun_mine,
    delete_term as delete_shenlun_term,
    get_mine as get_shenlun_mine,
    get_mine_by_date as get_shenlun_mine_by_date,
    get_stats as get_shenlun_stats,
    list_drills as list_shenlun_drills,
    list_mines as list_shenlun_mines,
    list_terms as list_shenlun_terms,
    update_mine as update_shenlun_mine,
    update_term as update_shenlun_term,
    upsert_mine as upsert_shenlun_mine,
)
from app.services.plan_service import (
    add_task,
    delete_task,
    get_day_plan,
    list_recent_days,
    update_task,
    upsert_review,
)
from app.services.category_service import build_category_tree
from app.services.quiz_service import pick_questions, pick_timeline_questions
from app.services.serializers import article_to_out, parse_correct_answer, question_to_out
from app.services.study_service import (
    complete_review,
    generate_review_tasks,
    get_section_read_map,
    list_study_records,
    mark_section_read,
    upsert_study_record,
)
from app.services.user_service import add_points_log, build_user_me_out, calc_sign_streak, check_answer, record_wrong
from app.services.wrong_service import (
    apply_wrong_redo_result,
    list_wrong_questions,
    remove_wrong,
)
from app.services.quiz_stats_service import get_quiz_rank, get_user_quiz_stats, submit_quiz_attempt

router = APIRouter(prefix="/api", tags=["公开接口"])


class FeedbackBody(BaseModel):
    content: str


@router.get("/config")
def public_config():
    """公开配置（无需登录），供前端控制注册入口等。"""
    from app.config import get_settings
    s = get_settings()
    return ApiResponse.ok({"allowRegister": bool(s.allow_register)})


@router.post("/auth/register")
def app_register(body: AppRegisterBody, db: Session = Depends(get_db)):
    from app.config import get_settings
    if not get_settings().allow_register:
        return ApiResponse.fail("当前未开放注册，请联系管理员开通账号", code=403)
    user, err = register_user(db, body.username, body.password, body.passwordConfirm)
    if err or not user:
        return ApiResponse.fail(err or "注册失败", code=400)
    token = issue_app_token(user)
    me = build_user_me_out(db, user)
    return ApiResponse.ok(
        AppAuthToken(access_token=token, user=me).model_dump()
    )


@router.post("/auth/login")
def app_login(body: AppLoginBody, db: Session = Depends(get_db)):
    user, err = authenticate_user(db, body.username, body.password)
    if err or not user:
        return ApiResponse.fail(err or "登录失败", code=401)
    token = issue_app_token(user)
    me = build_user_me_out(db, user)
    return ApiResponse.ok(
        AppAuthToken(access_token=token, user=me).model_dump()
    )


@router.get("/user/me")
def user_me(user: AppUser = Depends(get_app_user), db: Session = Depends(get_db)):
    return ApiResponse.ok(build_user_me_out(db, user).model_dump())


@router.put("/user/me")
def update_me(
    body: AppUserProfileUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_unset=True)
    if not data:
        return ApiResponse.fail("没有需要更新的内容", code=400)
    updated, err = update_user_profile(db, user, **data)
    if err or not updated:
        return ApiResponse.fail(err or "更新失败", code=400)
    return ApiResponse.ok(build_user_me_out(db, updated).model_dump())


@router.post("/user/password")
def change_password(
    body: AppUserPasswordChange,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    err = change_user_password(
        db,
        user,
        body.oldPassword,
        body.newPassword,
        body.newPasswordConfirm,
    )
    if err:
        return ApiResponse.fail(err, code=400)
    return ApiResponse.ok({"ok": True})


@router.post("/user/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    from pathlib import Path
    from uuid import uuid4

    content_type = (file.content_type or "").lower()
    allowed = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    ext = allowed.get(content_type)
    if not ext:
        name = (file.filename or "").lower()
        if name.endswith(".png"):
            ext = ".png"
        elif name.endswith(".webp"):
            ext = ".webp"
        elif name.endswith(".gif"):
            ext = ".gif"
        elif name.endswith(".jpg") or name.endswith(".jpeg"):
            ext = ".jpg"
        else:
            return ApiResponse.fail("仅支持 jpg/png/webp/gif 图片", code=400)

    raw = await file.read()
    if not raw:
        return ApiResponse.fail("文件为空", code=400)
    if len(raw) > 2 * 1024 * 1024:
        return ApiResponse.fail("头像不能超过 2MB", code=400)

    avatar_dir = Path(__file__).resolve().parents[3] / "data" / "uploads" / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{user.id}_{uuid4().hex[:12]}{ext}"
    dest = avatar_dir / filename
    dest.write_bytes(raw)

    user.avatar = f"/uploads/avatars/{filename}"
    db.commit()
    db.refresh(user)
    return ApiResponse.ok(build_user_me_out(db, user).model_dump())


@router.get("/articles/daily")
def daily_articles(db: Session = Depends(get_db)):
    rows = (
        db.query(Article)
        .filter(
            Article.is_published.is_(True),
            Article.status == "published",
            Article.is_daily.is_(True),
        )
        .order_by(Article.is_featured.desc(), Article.publish_date.desc(), Article.created_at.desc())
        .all()
    )
    if not rows:
        rows = (
            db.query(Article)
            .filter(Article.is_published.is_(True), Article.status == "published")
            .order_by(Article.created_at.desc())
            .limit(3)
            .all()
        )
    return ApiResponse.ok([article_to_out(a).model_dump() for a in rows])


@router.get("/articles/recommended")
def recommended_articles(
    offset: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
):
    base = (
        db.query(Article)
        .filter(
            Article.is_published.is_(True),
            Article.status == "published",
            Article.is_featured.is_(False),
        )
        .order_by(Article.publish_date.desc(), Article.created_at.desc())
    )
    total = base.count()
    rows = base.offset(offset).limit(limit).all()
    items = [article_to_out(a).model_dump() for a in rows]
    return ApiResponse.ok(
        {
            "items": items,
            "total": total,
            "hasMore": offset + len(rows) < total,
        }
    )


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    return ApiResponse.ok(build_category_tree(db))


@router.get("/quiz")
def quiz_by_mode(
    mode: str = Query("random"),
    count: int = Query(10, ge=1, le=30),
    categoryId: str | None = None,
    days: int = Query(14, ge=1, le=90),
    db: Session = Depends(get_db),
):
    if mode == "timeline":
        rows = pick_timeline_questions(db, count, days)
    elif mode == "key":
        rows = pick_questions(db, count, categoryId, min_importance=4)
    else:
        rows = pick_questions(db, count, categoryId)
    if not rows:
        return ApiResponse.fail("暂无可用题目", code=404)
    return ApiResponse.ok([question_to_out(q).model_dump() for q in rows])


@router.get("/articles/{article_id}")
def article_detail(article_id: str, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article or not article.is_published or article.status != "published":
        return ApiResponse.fail("文章不存在", code=404)
    return ApiResponse.ok(article_to_out(article).model_dump())


@router.post("/articles/{article_id}/read")
def mark_read(
    article_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    article = db.get(Article, article_id)
    if not article:
        return ApiResponse.fail("文章不存在", code=404)

    _, created = upsert_study_record(db, user.id, article_id)
    points = 0
    if created:
        article.read_count += 1
        add_points_log(db, user, 3, "阅读", f"完成文章阅读")
        points = 3
    else:
        db.commit()
    return ApiResponse.ok({"points": points})


@router.get("/questions")
def list_questions(articleId: str = Query(...), db: Session = Depends(get_db)):
    article = db.get(Article, articleId)
    if not article or not article.allow_quiz or article.status != "published":
        return ApiResponse.ok([])
    rows = (
        db.query(Question)
        .filter(
            Question.article_id == articleId,
            Question.is_active.is_(True),
            Question.status == "approved",
        )
        .all()
    )
    return ApiResponse.ok([question_to_out(q).model_dump() for q in rows])


@router.post("/answer")
def submit_answer(body: AnswerSubmit, user: AppUser = Depends(get_app_user), db: Session = Depends(get_db)):
    q = db.get(Question, body.questionId)
    if not q or not q.is_active or getattr(q, "status", "approved") != "approved":
        return ApiResponse.fail("题目不存在", code=404)
    correct = check_answer(q, body.answer)
    points = 0
    if correct:
        add_points_log(db, user, 2, "答题", "答对题目")
        points = 2
    else:
        record_wrong(db, user.id, q.id, body.answer)
    db.refresh(user)
    correct_answer = parse_correct_answer(q.correct_answer or "")
    return ApiResponse.ok(
        AnswerResult(
            correct=correct,
            analysis=q.analysis,
            correctAnswer=correct_answer,
            pointsEarned=points,
        ).model_dump()
    )


@router.get("/wrong")
def wrong_list(
    status: str = "review",
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    """status: review（今日到期，默认）| waiting | all"""
    if status not in ("review", "waiting", "all"):
        status = "review"
    return ApiResponse.ok(list_wrong_questions(db, user.id, status=status))


@router.delete("/wrong/{question_id}")
def wrong_remove(
    question_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    removed = remove_wrong(db, user.id, question_id)
    if not removed:
        return ApiResponse.fail("错题记录不存在", code=404)
    return ApiResponse.ok(None)


@router.post("/wrong/redo")
def wrong_redo(body: WrongRedoBody, user: AppUser = Depends(get_app_user), db: Session = Depends(get_db)):
    q = db.get(Question, body.questionId)
    if not q:
        return ApiResponse.fail("题目不存在", code=404)
    correct = check_answer(q, body.answer)
    points = 0
    outcome = apply_wrong_redo_result(db, user.id, q.id, correct)
    if correct:
        if outcome == "removed":
            add_points_log(db, user, 5, "复习", "错题掌握（记忆曲线完成）")
            points = 5
        elif outcome == "scheduled":
            add_points_log(db, user, 3, "复习", "错题复习答对，已安排下次复习")
            points = 3
    db.refresh(user)
    correct_answer = parse_correct_answer(q.correct_answer or "")
    return ApiResponse.ok(
        AnswerResult(
            correct=correct,
            analysis=q.analysis,
            correctAnswer=correct_answer,
            pointsEarned=points,
        ).model_dump()
    )


@router.get("/study/records")
def study_records(user: AppUser = Depends(get_app_user), db: Session = Depends(get_db)):
    return ApiResponse.ok(list_study_records(db, user.id))


@router.get("/study/section-reads")
def section_reads(user: AppUser = Depends(get_app_user), db: Session = Depends(get_db)):
    return ApiResponse.ok(get_section_read_map(db, user.id))


@router.post("/study/sections/read")
def section_read(
    body: SectionReadBody,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    mark_section_read(db, user.id, body.articleId, body.sectionId)
    return ApiResponse.ok(None)


@router.post("/signin")
def sign_in(user: AppUser = Depends(get_app_user), db: Session = Depends(get_db)):
    from app.timezone import today as today_str

    today = today_str()
    exists = (
        db.query(SignRecord)
        .filter(SignRecord.user_id == user.id, SignRecord.sign_date == today)
        .first()
    )
    if exists:
        return ApiResponse.fail("今日已签到", code=400, data={"points": 0, "streak": 0})

    db.add(SignRecord(user_id=user.id, sign_date=today, points=5))
    db.commit()
    record_event(db, user.id, "sign_in", {"points": 5})
    streak = calc_sign_streak(db, user.id, today)
    points = 5 + (10 if streak >= 7 and streak % 7 == 0 else 0)
    add_points_log(db, user, points, "签到", f"第{streak}天连续签到")
    db.refresh(user)
    return ApiResponse.ok({"points": points, "streak": streak})


@router.get("/points")
def get_points(user: AppUser = Depends(get_app_user), db: Session = Depends(get_db)):
    db.refresh(user)
    return ApiResponse.ok(user.points)


@router.get("/points/log")
def points_log(user: AppUser = Depends(get_app_user), db: Session = Depends(get_db)):
    rows = (
        db.query(PointsLog)
        .filter(PointsLog.user_id == user.id)
        .order_by(PointsLog.created_at.desc())
        .limit(100)
        .all()
    )
    data = [
        PointsLogOut(
            id=r.id,
            amount=r.amount,
            type=r.log_type,
            source=r.source,
            description=r.description,
            createdAt=r.created_at.isoformat(),
        ).model_dump()
        for r in rows
    ]
    return ApiResponse.ok(data)


@router.post("/quiz/complete")
def quiz_complete(
    body: QuizCompleteBody,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if body.correct > body.total:
        return ApiResponse.fail("正确题数不能超过总题数", code=400)
    data = submit_quiz_attempt(
        db,
        user.id,
        article_id=body.articleId,
        quiz_mode=body.mode,
        total=body.total,
        correct=body.correct,
    )
    return ApiResponse.ok(QuizCompleteResult(**data).model_dump())


@router.get("/quiz/rank")
def quiz_rank(
    articleId: str | None = Query(None),
    mode: str = Query("article"),
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    items = get_quiz_rank(db, article_id=articleId, quiz_mode=mode, limit=20)
    for item in items:
        item["isSelf"] = item["userId"] == user.id
    return ApiResponse.ok(items)


@router.get("/quiz/stats")
def quiz_stats(
    articleId: str | None = Query(None),
    mode: str = Query("article"),
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    stats = get_user_quiz_stats(db, user.id, article_id=articleId, quiz_mode=mode)
    if not stats:
        return ApiResponse.ok(None)
    return ApiResponse.ok(QuizStatsOut(**stats).model_dump())


@router.get("/rank")
def rank_list(
    type: str = Query("weekly"),
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    factor = {"daily": 0.1, "weekly": 0.3, "monthly": 0.6, "total": 1.0}.get(type, 0.3)
    users = (
        db.query(AppUser)
        .filter(AppUser.is_active.is_(True), AppUser.username.isnot(None))
        .order_by(AppUser.points.desc())
        .limit(20)
        .all()
    )
    items = [
        RankItemOut(
            rank=i + 1,
            userId=u.id,
            nickname=u.nickname,
            avatar=u.avatar,
            score=int(u.points * factor),
            isSelf=u.id == user.id,
        ).model_dump()
        for i, u in enumerate(users)
    ]
    return ApiResponse.ok(items)






@router.post("/feedback")
def feedback(body: FeedbackBody, user: AppUser = Depends(get_app_user), db: Session = Depends(get_db)):
    import random

    adopted = random.random() > 0.5
    if adopted:
        add_points_log(db, user, 10, "反馈", "纠错反馈被采纳")
    db.refresh(user)
    return ApiResponse.ok({"adopted": adopted})


@router.get("/review")
def review_tasks(user: AppUser = Depends(get_app_user), db: Session = Depends(get_db)):
    return ApiResponse.ok(generate_review_tasks(db, user.id))


@router.post("/review/complete")
def complete_review_task(
    body: ReviewCompleteBody,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    complete_review(db, user.id, body.articleId)
    return ApiResponse.ok(None)


@router.get("/review/hub")
def review_hub(user: AppUser = Depends(get_app_user), db: Session = Depends(get_db)):
    return ApiResponse.ok(get_review_hub(db, user).model_dump())


# ===== 每日学习清单 =====


@router.get("/plan/today")
def plan_today(user: AppUser = Depends(get_app_user), db: Session = Depends(get_db)):
    from app.services.plan_service import _today_str

    return ApiResponse.ok(get_day_plan(db, user, _today_str()).model_dump())


@router.get("/plan/day/{date_str}")
def plan_day(date_str: str, user: AppUser = Depends(get_app_user), db: Session = Depends(get_db)):
    return ApiResponse.ok(get_day_plan(db, user, date_str).model_dump())


@router.get("/plan/week")
def plan_week(user: AppUser = Depends(get_app_user), db: Session = Depends(get_db)):
    return ApiResponse.ok([d.model_dump() for d in list_recent_days(db, user, 7)])


@router.put("/plan/task/{task_id}")
def plan_task_update(
    task_id: str,
    body: PlanTaskUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = update_task(db, user, task_id, body)
    if not out:
        return ApiResponse.fail("任务不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.post("/plan/task")
def plan_task_add(
    body: PlanTaskCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = add_task(db, user, body)
    return ApiResponse.ok(out.model_dump())


@router.delete("/plan/task/{task_id}")
def plan_task_delete(
    task_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_task(db, user, task_id):
        return ApiResponse.fail("任务不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.post("/plan/review")
def plan_review_upsert(
    body: DailyReviewUpsert,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = upsert_review(db, user, body)
    return ApiResponse.ok(out.model_dump())


# ===== 知识框架 =====


@router.get("/knowledge/trees")
def knowledge_trees(db: Session = Depends(get_db)):
    return ApiResponse.ok([t.model_dump() for t in list_knowledge_trees(db)])


@router.get("/knowledge/tree/{tree_key}")
def knowledge_tree_detail(tree_key: str, db: Session = Depends(get_db)):
    t = get_knowledge_tree(db, tree_key)
    if not t:
        return ApiResponse.fail("知识树不存在", code=404)
    return ApiResponse.ok(t.model_dump())


@router.post("/knowledge/sync")
def knowledge_sync(
    tree_key: str | None = None,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    result = sync_knowledge(db, only_tree_key=tree_key)
    if "error" in result:
        return ApiResponse.fail(result["error"], code=400)
    return ApiResponse.ok(result)


@router.get("/knowledge/status")
def knowledge_status(db: Session = Depends(get_db)):
    return ApiResponse.ok(knowledge_sync_status(db))


@router.put("/knowledge/node/{node_id}")
def knowledge_node_update(
    node_id: str,
    body: KnowledgeNodeUpdate,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    """App 端只能改 my_note / is_starred / content（不能改 title 等结构）"""
    # 限制只能改 my_note / is_starred / content
    data = body.model_dump(exclude_unset=True)
    safe = {}
    if "myNote" in data:
        safe["myNote"] = data["myNote"]
    if "isStarred" in data:
        safe["isStarred"] = data["isStarred"]
    if "content" in data:
        safe["content"] = data["content"]
    if not safe:
        return ApiResponse.fail("没有可更新的字段", code=400)
    out = update_knowledge_node(db, node_id, KnowledgeNodeUpdate(**safe))
    if not out:
        return ApiResponse.fail("节点不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.get("/knowledge/review/due")
def knowledge_review_due(
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(get_knowledge_review_due(db).model_dump())


@router.post("/knowledge/review/session")
def knowledge_review_session(
    body: KnowledgeReviewSessionBody,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(create_knowledge_review_session(db, body.count).model_dump())


@router.post("/knowledge/review/answer")
def knowledge_review_answer(
    body: KnowledgeReviewAnswerBody,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = answer_knowledge_review(db, body.nodeId, body.result)
    if not out:
        return ApiResponse.fail("节点不存在或结果无效", code=400)
    return ApiResponse.ok(out.model_dump())


# ===== 手动错题 =====


@router.get("/manual-wrong")
def manual_wrong_list(
    subject: str | None = None,
    mastered: bool | None = None,
    status: str | None = None,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    """status: review（今日到期）| waiting | 不传则不过滤到期"""
    if status and status not in ("review", "waiting", "all"):
        status = None
    if status == "all":
        status = None
    return ApiResponse.ok(
        [w.model_dump() for w in list_wrongs(db, user, subject, mastered, status=status)]
    )


@router.post("/manual-wrong")
def manual_wrong_create(
    body: ManualWrongCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = create_wrong(db, user, body)
    return ApiResponse.ok(out.model_dump())


@router.post("/manual-wrong/{wrong_id}/review")
def manual_wrong_review(
    wrong_id: str,
    result: str = "good",
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    """result: good（推进间隔）| again（重置）"""
    out = review_manual_wrong(db, user, wrong_id, result)
    if not out:
        return ApiResponse.fail("错题不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.put("/manual-wrong/{wrong_id}")
def manual_wrong_update(
    wrong_id: str,
    body: ManualWrongUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = update_wrong(db, user, wrong_id, body)
    if not out:
        return ApiResponse.fail("错题不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/manual-wrong/{wrong_id}")
def manual_wrong_delete(
    wrong_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_wrong(db, user, wrong_id):
        return ApiResponse.fail("错题不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.post("/manual-wrong/upload")
async def manual_wrong_upload(
    file: UploadFile = File(...),
    user: AppUser = Depends(get_app_user),
):
    from uuid import uuid4

    from app.upload_paths import detect_image_ext, is_heic_like, uploads_subdir

    raw = await file.read()
    if not raw:
        return ApiResponse.fail("文件为空", code=400)
    if len(raw) > 5 * 1024 * 1024:
        return ApiResponse.fail("图片不能超过 5MB", code=400)

    if is_heic_like(file.content_type or "", file.filename or "", raw):
        return ApiResponse.fail("暂不支持 HEIC/HEIF，请用相册选图并选「最兼容」或先转为 jpg/png", code=400)

    ext = detect_image_ext(file.content_type or "", file.filename or "", raw)
    if not ext:
        return ApiResponse.fail("仅支持 jpg/png/webp/gif 图片", code=400)

    try:
        upload_dir = uploads_subdir("wrong")
        filename = f"{user.id}_{uuid4().hex[:12]}{ext}"
        dest = upload_dir / filename
        dest.write_bytes(raw)
    except OSError as e:
        return ApiResponse.fail(f"保存失败：{e}", code=500)

    return ApiResponse.ok({"url": f"/uploads/wrong/{filename}"})


# ===== 真题/题库 =====


@router.get("/exam/papers")
def exam_papers(
    exam_type: str | None = None,
    subject: str | None = None,
    year: int | None = None,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([p.model_dump() for p in list_exam_papers(
        db, exam_type=exam_type, subject=subject, year=year, is_published=True
    )])


@router.get("/exam/paper/{paper_id}")
def exam_paper_detail(
    paper_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    detail = get_exam_paper_detail(db, paper_id)
    if not detail:
        return ApiResponse.fail("试卷不存在", code=404)
    return ApiResponse.ok(detail.model_dump())


@router.post("/exam/start/{paper_id}")
def exam_start(
    paper_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    result = start_exam_attempt(db, user, paper_id)
    if not result:
        return ApiResponse.fail("试卷不存在或未发布", code=404)
    return ApiResponse.ok(result)


@router.post("/exam/answer")
def exam_answer(
    body: ExamAnswerSubmit,
    attempt_id: str = Query(...),
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = submit_exam_answer(db, user, attempt_id, body)
    if not out:
        return ApiResponse.fail("作答失败，attempt 不存在或已交卷", code=400)
    return ApiResponse.ok(out)


@router.post("/exam/submit")
def exam_submit(
    attempt_id: str = Query(...),
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    detail = finish_exam_attempt(db, user, attempt_id)
    if not detail:
        return ApiResponse.fail("交卷失败，attempt 不存在", code=400)
    return ApiResponse.ok(detail.model_dump())


@router.get("/exam/attempts")
def exam_attempts(
    paper_id: str | None = None,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([a.model_dump() for a in list_exam_attempts(db, user, paper_id)])


@router.get("/exam/attempt/{attempt_id}")
def exam_attempt_detail(
    attempt_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    detail = get_exam_attempt_detail(db, user, attempt_id)
    if not detail:
        return ApiResponse.fail("作答记录不存在", code=404)
    return ApiResponse.ok(detail.model_dump())


# ===== 英语学习 =====






# 生词本








# 发音代理（edge-tts 优先，有道兜底）


# 跟读本（文章收藏句子）








# 口语课程（可选）








# 语法






# 学习记录




# 口语录音上传


# ===== 音标学习 =====










# ===== 美剧口语训练 =====
















































# ===== 语音识别 ASR（默认前端免费 Web Speech；可选云） =====






# ===== 人民日报模块（独立：时评 / 开采本 / 规范词） =====


@router.get("/rmrb/meta")
def rmrb_meta(
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    """三刀解剖元数据：规范词分类 / 骨架模版 / 句式类型"""
    return ApiResponse.ok(get_rmrb_meta(db, enabled_only=True).model_dump())


@router.post("/rmrb/skeleton-templates")
def rmrb_skeleton_create(
    body: ShenlunSkeletonTemplateCreate,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    """用户在三刀页快捷新增骨架模版"""
    try:
        out = create_rmrb_skeleton(db, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.post("/rmrb/term-categories")
def rmrb_term_category_create(
    body: ShenlunTermCategoryCreate,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    """移动端快捷新增规范词/动词分类（kind: term | verb）"""
    try:
        out = create_rmrb_term_category(db, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.get("/rmrb/stats")
def rmrb_stats(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(get_shenlun_stats(db, user).model_dump())


@router.get("/rmrb/articles")
def rmrb_articles_list(
    tag: str | None = None,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(
        [a.model_dump() for a in list_rmrb_articles(db, published_only=True, tag=tag)]
    )


@router.get("/rmrb/articles/{article_id}")
def rmrb_article_detail(
    article_id: str,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    a = get_rmrb_article(db, article_id, bump_read=True)
    if not a or not a.isPublished:
        return ApiResponse.fail("文章不存在", code=404)
    return ApiResponse.ok(a.model_dump())


@router.get("/rmrb/mines")
def rmrb_mines_list(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([m.model_dump() for m in list_shenlun_mines(db, user)])


@router.get("/rmrb/mines/by-date/{mine_date}")
def rmrb_mine_by_date(
    mine_date: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    m = get_shenlun_mine_by_date(db, user, mine_date)
    if not m:
        return ApiResponse.fail("当日尚无开采记录", code=404)
    return ApiResponse.ok(m.model_dump())


@router.get("/rmrb/mines/{mine_id}")
def rmrb_mine_detail(
    mine_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    m = get_shenlun_mine(db, user, mine_id)
    if not m:
        return ApiResponse.fail("开采记录不存在", code=404)
    return ApiResponse.ok(m.model_dump())


@router.post("/rmrb/mines")
def rmrb_mine_upsert(
    body: ShenlunMineLogUpsert,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = upsert_shenlun_mine(db, user, body)
    return ApiResponse.ok(out.model_dump())


@router.put("/rmrb/mines/{mine_id}")
def rmrb_mine_update(
    mine_id: str,
    body: ShenlunMineLogUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = update_shenlun_mine(db, user, mine_id, body)
    if not out:
        return ApiResponse.fail("开采记录不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/rmrb/mines/{mine_id}")
def rmrb_mine_delete(
    mine_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_shenlun_mine(db, user, mine_id):
        return ApiResponse.fail("开采记录不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.get("/rmrb/terms")
def rmrb_terms_list(
    status: str | None = None,
    category: str | None = None,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(
        [t.model_dump() for t in list_shenlun_terms(db, user, status=status, category=category)]
    )


@router.post("/rmrb/terms")
def rmrb_term_add(
    body: ShenlunNormTermAdd,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = add_shenlun_term(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/rmrb/terms/{term_id}")
def rmrb_term_update(
    term_id: str,
    body: ShenlunNormTermUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = update_shenlun_term(db, user, term_id, body)
    if not out:
        return ApiResponse.fail("规范词不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/rmrb/terms/{term_id}")
def rmrb_term_delete(
    term_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_shenlun_term(db, user, term_id):
        return ApiResponse.fail("规范词不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.get("/rmrb/drills")
def rmrb_drills_list(
    drill_type: str | None = None,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([d.model_dump() for d in list_shenlun_drills(db, user, drill_type)])


@router.post("/rmrb/drills")
def rmrb_drill_add(
    body: ShenlunDrillCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = add_shenlun_drill(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


# ===== 读书模块 =====




@router.get("/growth/overview")
def growth_overview(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    """知行足迹：个人成长总览"""
    return ApiResponse.ok(get_growth_overview(db, user).model_dump())


# ===== 健康模块 =====
















class HealthFocusBody(BaseModel):
    text: str = ""




































# ===== 记账模块 =====


































# ===== 语料本 =====


@router.get("/corpus/stats")
def corpus_stats(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(get_corpus_stats(db, user).model_dump())


@router.get("/corpus/items")
def corpus_items_list(
    status: str | None = Query(None),
    limit: int = Query(100, ge=1, le=200),
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([i.model_dump() for i in list_corpus_items(db, user, status, limit)])


@router.get("/corpus/items/{item_id}")
def corpus_item_detail(
    item_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = get_corpus_item(db, user, item_id)
    if not out:
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.post("/corpus/items")
def corpus_item_create(
    body: CorpusItemCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = create_corpus_item(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/corpus/items/{item_id}")
def corpus_item_update(
    item_id: str,
    body: CorpusItemUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = update_corpus_item(db, user, item_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/corpus/items/{item_id}")
def corpus_item_delete(
    item_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_corpus_item(db, user, item_id):
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.post("/corpus/items/{item_id}/promote-term")
def corpus_item_promote_term(
    item_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = promote_corpus_to_term(db, user, item_id)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok(out.model_dump())


# ===== 财富 / 投资大脑 =====


































# ===== 时事新闻 · 事件印象 =====


@router.get("/events/hub")
def events_hub(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(get_event_hub(db, user).model_dump())


@router.get("/events")
def events_list(
    treeKey: str | None = Query(None),
    path: str | None = Query(None),
    unlinked: bool = Query(False),
    limit: int = Query(100, ge=1, le=200),
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(
        [
            e.model_dump()
            for e in list_event_impressions(
                db, user, tree_key=treeKey, path=path, unlinked=unlinked, limit=limit
            )
        ]
    )


@router.get("/events/{event_id}")
def events_detail(
    event_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = get_event_impression(db, user, event_id)
    if not out:
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.post("/events")
def events_create(
    body: EventImpressionCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = create_event_impression(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/events/{event_id}")
def events_update(
    event_id: str,
    body: EventImpressionUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = update_event_impression(db, user, event_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/events/{event_id}")
def events_delete(
    event_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_event_impression(db, user, event_id):
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok({"ok": True})


# ===== 资料分析 =====


@router.get("/ziliao/overview")
def ziliao_overview(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(get_ziliao_overview(db, user.id).model_dump())


@router.get("/ziliao/formulas")
def ziliao_formulas(
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([x.model_dump() for x in list_ziliao_formulas(db)])


@router.get("/ziliao/formulas/{formula_id}")
def ziliao_formula_detail(
    formula_id: str,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = get_ziliao_formula(db, formula_id)
    if not out:
        return ApiResponse.fail("公式不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.get("/ziliao/types")
def ziliao_types(
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([x.model_dump() for x in list_ziliao_types(db)])


@router.get("/ziliao/types/{type_id}")
def ziliao_type_detail(
    type_id: str,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = get_ziliao_type(db, type_id)
    if not out:
        return ApiResponse.fail("题型不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.get("/ziliao/tricks")
def ziliao_tricks(
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([x.model_dump() for x in list_ziliao_tricks(db)])


@router.get("/ziliao/tricks/{trick_id}")
def ziliao_trick_detail(
    trick_id: str,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = get_ziliao_trick(db, trick_id)
    if not out:
        return ApiResponse.fail("技巧不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.get("/ziliao/drill/sets")
def ziliao_drill_sets(
    typeCode: str | None = None,
    includeSample: bool | None = None,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(
        [
            x.model_dump()
            for x in list_ziliao_drill_sets(db, type_code=typeCode, include_sample=includeSample)
        ]
    )


@router.get("/ziliao/drill/set/{set_id}")
def ziliao_drill_set_detail(
    set_id: str,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = get_ziliao_drill_set(db, set_id)
    if not out:
        return ApiResponse.fail("练习组不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.post("/ziliao/drill/submit")
def ziliao_drill_submit(
    body: ZiliaoDrillSubmitIn,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = submit_ziliao_drill(db, user, body)
    if not out:
        return ApiResponse.fail("练习组不存在", code=404)
    return ApiResponse.ok(out.model_dump())


# ===== 考试倒计时 =====

@router.get("/countdown")
def countdown_get(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = get_countdown(db, user)
    return ApiResponse.ok(out.model_dump() if out else None)


@router.put("/countdown")
def countdown_upsert(
    body: ExamCountdownUpsert,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = upsert_countdown(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.delete("/countdown")
def countdown_delete(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    deleted = delete_countdown(db, user)
    if not deleted:
        return ApiResponse.fail("尚未设置考试倒计时", code=404)
    return ApiResponse.ok({"deleted": True})
