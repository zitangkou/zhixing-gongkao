from fastapi import APIRouter, Depends, File, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_app_user
from app.core.response import ApiResponse
from app.database import get_db
from app.models import AppUser, Article, PointsLog, Question, RechargePackage, SignRecord
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
    ExamPaperCreate,
    ExamPaperOut,
    ExamPaperUpdate,
    ExamQuestionCreate,
    ExamQuestionOut,
    ExamQuestionUpdate,
    EnglishArticleCreate,
    EnglishArticleOut,
    EnglishArticleUpdate,
    EnglishStatsOut,
    EnglishStudyLogCreate,
    GrammarLessonCreate,
    GrammarLessonOut,
    GrammarProgressOut,
    GrammarProgressUpdate,
    KnowledgeNodeUpdate,
    KnowledgeReviewAnswerBody,
    KnowledgeReviewSessionBody,
    KnowledgeTreeOut,
    ManualWrongCreate,
    ManualWrongOut,
    ManualWrongUpdate,
    PhoneticLessonOut,
    SpeakingAttemptCreate,
    SpeakingAttemptOut,
    SpeakingLessonCreate,
    SpeakingLessonOut,
    UserSpeakingSentenceAdd,
    UserSpeakingSentenceOut,
    UserSpeakingSentenceUpdate,
    UserVocabAdd,
    UserVocabOut,
    UserVocabUpdate,
    ShenlunMineLogUpdate,
    ShenlunMineLogUpsert,
    ShenlunNormTermAdd,
    ShenlunNormTermUpdate,
    ShenlunDrillCreate,
    ShenlunSkeletonTemplateCreate,
    ShenlunTermCategoryCreate,
    DushuBookCreate,
    DushuBookUpdate,
    DushuDailyLogUpsert,
    DushuPersonCardCreate,
    DushuPersonCardUpdate,
    DushuBookSummaryUpsert,
    HealthDailyLogUpsert,
    LedgerExpenseCreate,
    LedgerExpenseUpdate,
    LedgerLoanCreate,
    LedgerLoanUpdate,
    LedgerRepaymentCreate,
    LedgerRepaymentUpdate,
    CorpusItemCreate,
    CorpusItemUpdate,
    EventImpressionCreate,
    EventImpressionUpdate,
    TvEpisodeCreate,
    TvEpisodeUpdate,
    TvExpressionCreate,
    TvExpressionUpdate,
    TvSceneCreate,
    TvSceneUpdate,
    TvShowCreate,
    TvShowUpdate,
    TvStudySessionUpdate,
    WealthJournalCreate,
    WealthJournalUpdate,
    WealthPrincipleCreate,
    WealthPrincipleUpdate,
    WealthSnapshotCreate,
    WealthSnapshotUpdate,
    PayOrderOut,
    PlanTaskCreate,
    PlanTaskOut,
    PlanTaskUpdate,
    PointsLogOut,
    QuizCompleteBody,
    QuizCompleteResult,
    QuizRankItemOut,
    QuizStatsOut,
    RankItemOut,
    RechargePackageOut,
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
from app.services.english_service import (
    add_shadowing as add_user_shadowing,
    add_study_log as add_english_log,
    add_vocab as add_user_vocab,
    create_speaking_attempt as create_speaking_attempt_svc,
    delete_shadowing as delete_user_shadowing,
    delete_vocab as delete_user_vocab,
    get_article as get_english_article,
    get_grammar_lesson as get_grammar_lesson_pub,
    get_speaking_lesson as get_speaking_lesson_pub,
    get_stats as get_english_stats,
    list_articles as list_english_articles_pub,
    list_grammar_lessons as list_grammar_lessons_pub,
    list_shadowing as list_user_shadowing,
    list_speaking_attempts as list_speaking_attempts_pub,
    list_speaking_lessons as list_speaking_lessons_pub,
    list_vocabs as list_user_vocabs,
    update_grammar_progress as update_grammar_progress_pub,
    update_shadowing as update_user_shadowing,
    update_vocab as update_user_vocab,
)
from app.services.phonetic_service import (
    get_phonetic as get_phonetic_pub,
    get_phonetic_progress as get_phonetic_progress_pub,
    list_phonetics as list_phonetics_pub,
    update_phonetic_progress as update_phonetic_progress_pub,
)
from app.services.tv_english_service import (
    create_episode as tv_create_episode,
    create_expression as tv_create_expression,
    create_scene as tv_create_scene,
    create_show as tv_create_show,
    delete_episode as tv_delete_episode,
    delete_expression as tv_delete_expression,
    delete_scene as tv_delete_scene,
    delete_show as tv_delete_show,
    get_hub as tv_get_hub,
    get_or_create_session as tv_get_session,
    get_scene as tv_get_scene,
    get_weekly_review as tv_get_weekly,
    list_episodes as tv_list_episodes,
    list_expressions as tv_list_expressions,
    list_scenes as tv_list_scenes,
    list_shows as tv_list_shows,
    review_expression as tv_review_expression,
    update_episode as tv_update_episode,
    update_expression as tv_update_expression,
    update_scene as tv_update_scene,
    update_session as tv_update_session,
    update_show as tv_update_show,
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
from app.services.dushu_service import (
    create_book as create_dushu_book,
    create_person as create_dushu_person,
    delete_book as delete_dushu_book,
    delete_daily as delete_dushu_daily,
    delete_person as delete_dushu_person,
    get_book as get_dushu_book,
    get_daily_by_date as get_dushu_daily_by_date,
    get_stats as get_dushu_stats,
    get_summary as get_dushu_summary,
    list_books as list_dushu_books,
    list_daily as list_dushu_daily,
    list_persons as list_dushu_persons,
    list_summaries as list_dushu_summaries,
    update_book as update_dushu_book,
    update_person as update_dushu_person,
    upsert_daily as upsert_dushu_daily,
    upsert_summary as upsert_dushu_summary,
)
from app.services.growth_service import get_growth_overview
from app.services.health_service import (
    get_daily as get_health_daily,
    get_overview as get_health_overview,
    list_daily_range as list_health_daily_range,
    list_phases as list_health_phases,
    reset_program as reset_health_program,
    tasks_for_phase as health_tasks_for_phase,
    update_private_focus as update_health_private_focus,
    upsert_daily as upsert_health_daily,
)
from app.services.ledger_service import (
    create_expense as create_ledger_expense,
    create_loan as create_ledger_loan,
    create_repayment as create_ledger_repayment,
    delete_expense as delete_ledger_expense,
    delete_loan as delete_ledger_loan,
    delete_repayment as delete_ledger_repayment,
    get_expense as get_ledger_expense,
    get_loan as get_ledger_loan,
    get_overview as get_ledger_overview,
    list_counterparties as list_ledger_counterparties,
    list_expenses as list_ledger_expenses,
    list_loans as list_ledger_loans,
    update_expense as update_ledger_expense,
    update_loan as update_ledger_loan,
    update_repayment as update_ledger_repayment,
)
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
from app.services.wealth_service import (
    create_journal as create_wealth_journal,
    create_principle as create_wealth_principle,
    create_snapshot as create_wealth_snapshot,
    delete_journal as delete_wealth_journal,
    delete_principle as delete_wealth_principle,
    delete_snapshot as delete_wealth_snapshot,
    get_hub as get_wealth_hub,
    get_journal as get_wealth_journal,
    get_review as get_wealth_review,
    get_snapshot as get_wealth_snapshot,
    list_journals as list_wealth_journals,
    list_principles as list_wealth_principles,
    list_snapshots as list_wealth_snapshots,
    update_journal as update_wealth_journal,
    update_principle as update_wealth_principle,
    update_snapshot as update_wealth_snapshot,
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


class RechargeBody(BaseModel):
    packageId: str


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


@router.get("/recharge/packages")
def recharge_packages(db: Session = Depends(get_db)):
    rows = db.query(RechargePackage).filter(RechargePackage.is_active.is_(True)).order_by(RechargePackage.sort_order).all()
    return ApiResponse.ok([
        RechargePackageOut(id=r.id, points=r.points, price=r.price, label=r.label).model_dump() for r in rows
    ])


@router.post("/recharge")
def create_order(body: RechargeBody, db: Session = Depends(get_db)):
    import time

    pkg = db.get(RechargePackage, body.packageId)
    amount = pkg.price if pkg else 600
    order_id = f"order-{int(time.time())}"
    return ApiResponse.ok(
        PayOrderOut(orderId=order_id, amount=amount, payUrl=f"mock://pay?orderId={order_id}").model_dump()
    )


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


@router.get("/english/articles")
def english_articles(
    level: str | None = None,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([a.model_dump() for a in list_english_articles_pub(db, level=level)])


@router.get("/english/article/{article_id}")
def english_article_detail(
    article_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    a = get_english_article(db, article_id)
    if not a:
        return ApiResponse.fail("文章不存在", code=404)
    # 记录阅读日志
    add_english_log(
        db, user,
        EnglishStudyLogCreate(logType="article", refId=article_id, durationSec=0),
    )
    return ApiResponse.ok(a.model_dump())


# 生词本
@router.get("/english/vocab")
def english_vocab_list(
    status: str | None = None,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([v.model_dump() for v in list_user_vocabs(db, user, status=status)])


@router.post("/english/vocab")
def english_vocab_add(
    body: UserVocabAdd,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = add_user_vocab(db, user, body)
    return ApiResponse.ok(out.model_dump())


@router.put("/english/vocab/{vocab_id}")
def english_vocab_update(
    vocab_id: str,
    body: UserVocabUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = update_user_vocab(db, user, vocab_id, body)
    if not out:
        return ApiResponse.fail("生词不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/english/vocab/{vocab_id}")
def english_vocab_delete(
    vocab_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_user_vocab(db, user, vocab_id):
        return ApiResponse.fail("生词不存在", code=404)
    return ApiResponse.ok({"ok": True})


# 发音代理（edge-tts 优先，有道兜底）
@router.get("/english/pronounce")
def english_pronounce(text: str = Query(...), accent: str = Query("us")):
    """返回英文 mp3：优先 Microsoft edge-tts，失败回退有道。"""
    from fastapi.responses import Response

    from app.services.tts_service import synthesize_english

    cleaned = (text or "").strip()
    if not cleaned:
        return ApiResponse.fail("文本为空", code=400)
    try:
        raw = synthesize_english(cleaned, accent)
        if not raw:
            return ApiResponse.fail("发音服务暂不可用", code=502)
        return Response(
            content=raw,
            media_type="audio/mpeg",
            headers={"Cache-Control": "public, max-age=86400"},
        )
    except Exception as e:
        return ApiResponse.fail(f"获取发音失败: {e}", code=502)


# 跟读本（文章收藏句子）
@router.get("/english/shadowing")
def english_shadowing_list(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([s.model_dump() for s in list_user_shadowing(db, user)])


@router.post("/english/shadowing")
def english_shadowing_add(
    body: UserSpeakingSentenceAdd,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = add_user_shadowing(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/english/shadowing/{sentence_id}")
def english_shadowing_update(
    sentence_id: str,
    body: UserSpeakingSentenceUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = update_user_shadowing(db, user, sentence_id, body)
    if not out:
        return ApiResponse.fail("句子不存在", code=404)
    if body.practiced:
        add_english_log(
            db, user,
            EnglishStudyLogCreate(
                logType="speaking", refId=sentence_id,
                durationSec=0, sentencesPracticed=1,
            ),
        )
    return ApiResponse.ok(out.model_dump())


@router.delete("/english/shadowing/{sentence_id}")
def english_shadowing_delete(
    sentence_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_user_shadowing(db, user, sentence_id):
        return ApiResponse.fail("句子不存在", code=404)
    return ApiResponse.ok({"ok": True})


# 口语课程（可选）
@router.get("/english/speaking")
def english_speaking_list(
    topic: str | None = None,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([s.model_dump() for s in list_speaking_lessons_pub(db, topic=topic)])


@router.get("/english/speaking/{lesson_id}")
def english_speaking_detail(
    lesson_id: str,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    s = get_speaking_lesson_pub(db, lesson_id)
    if not s:
        return ApiResponse.fail("课程不存在", code=404)
    return ApiResponse.ok(s.model_dump())


@router.get("/english/speaking/{lesson_id}/attempts")
def english_speaking_attempts(
    lesson_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([a.model_dump() for a in list_speaking_attempts_pub(db, user, lesson_id)])


@router.post("/english/speaking/attempt")
def english_speaking_attempt_create(
    body: SpeakingAttemptCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = create_speaking_attempt_svc(db, user, body)
    add_english_log(
        db, user,
        EnglishStudyLogCreate(
            logType="speaking", refId=body.lessonId,
            durationSec=0, sentencesPracticed=1,
        ),
    )
    return ApiResponse.ok(out.model_dump())


# 语法
@router.get("/english/grammar")
def english_grammar_list(
    category: str | None = None,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([g.model_dump() for g in list_grammar_lessons_pub(db, category=category)])


@router.get("/english/grammar/{lesson_id}")
def english_grammar_detail(
    lesson_id: str,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    g = get_grammar_lesson_pub(db, lesson_id)
    if not g:
        return ApiResponse.fail("课程不存在", code=404)
    return ApiResponse.ok(g.model_dump())


@router.put("/english/grammar/{lesson_id}/progress")
def english_grammar_progress_update(
    lesson_id: str,
    body: GrammarProgressUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = update_grammar_progress_pub(db, user, lesson_id, body)
    add_english_log(
        db, user,
        EnglishStudyLogCreate(logType="grammar", refId=lesson_id, durationSec=0),
    )
    return ApiResponse.ok(out.model_dump())


# 学习记录
@router.post("/english/log")
def english_log_add(
    body: EnglishStudyLogCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = add_english_log(db, user, body)
    return ApiResponse.ok(out)


@router.get("/english/stats")
def english_stats(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(get_english_stats(db, user).model_dump())


# 口语录音上传
@router.post("/english/speaking/upload")
async def english_speaking_upload(
    file: UploadFile = File(...),
    user: AppUser = Depends(get_app_user),
):
    from pathlib import Path
    from uuid import uuid4

    content_type = (file.content_type or "").lower()
    allowed = {
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/aac": ".aac",
        "audio/mp4": ".m4a",
        "audio/x-m4a": ".m4a",
    }
    ext = allowed.get(content_type, ".m4a")
    raw = await file.read()
    if not raw:
        return ApiResponse.fail("文件为空", code=400)
    if len(raw) > 5 * 1024 * 1024:
        return ApiResponse.fail("录音不能超过 5MB", code=400)

    upload_dir = Path(__file__).resolve().parents[3] / "data" / "uploads" / "speaking"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{user.id}_{uuid4().hex[:12]}{ext}"
    dest = upload_dir / filename
    dest.write_bytes(raw)
    url = f"/uploads/speaking/{filename}"
    return ApiResponse.ok({"url": url})


# ===== 音标学习 =====


@router.get("/english/phonetics")
def english_phonetics_list(
    category: str | None = None,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([p.model_dump() for p in list_phonetics_pub(db, category)])


@router.get("/english/phonetic/{lesson_id}")
def english_phonetic_detail(
    lesson_id: str,
    _user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    p = get_phonetic_pub(db, lesson_id)
    if not p:
        return ApiResponse.fail("音标不存在", code=404)
    return ApiResponse.ok(p.model_dump())


@router.get("/english/phonetics/progress")
def english_phonetics_progress(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(get_phonetic_progress_pub(db, user))


@router.put("/english/phonetic/{lesson_id}/progress")
def english_phonetic_progress_update(
    lesson_id: str,
    body: dict,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    status = body.get("status", "learning")
    result = update_phonetic_progress_pub(db, user, lesson_id, status)
    add_english_log(
        db, user,
        EnglishStudyLogCreate(logType="phonetic", refId=lesson_id, durationSec=0),
    )
    return ApiResponse.ok(result)


# ===== 美剧口语训练 =====


@router.get("/english/tv/hub")
def english_tv_hub(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(tv_get_hub(db, user).model_dump())


@router.get("/english/tv/weekly")
def english_tv_weekly(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(tv_get_weekly(db, user).model_dump())


@router.get("/english/tv/shows")
def english_tv_shows(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([x.model_dump() for x in tv_list_shows(db, user)])


@router.post("/english/tv/shows")
def english_tv_show_create(
    body: TvShowCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = tv_create_show(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/english/tv/shows/{show_id}")
def english_tv_show_update(
    show_id: str,
    body: TvShowUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = tv_update_show(db, user, show_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("剧目不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/english/tv/shows/{show_id}")
def english_tv_show_delete(
    show_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not tv_delete_show(db, user, show_id):
        return ApiResponse.fail("剧目不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.get("/english/tv/shows/{show_id}/episodes")
def english_tv_episodes(
    show_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([x.model_dump() for x in tv_list_episodes(db, user, show_id)])


@router.post("/english/tv/episodes")
def english_tv_episode_create(
    body: TvEpisodeCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = tv_create_episode(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/english/tv/episodes/{episode_id}")
def english_tv_episode_update(
    episode_id: str,
    body: TvEpisodeUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = tv_update_episode(db, user, episode_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("剧集不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/english/tv/episodes/{episode_id}")
def english_tv_episode_delete(
    episode_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not tv_delete_episode(db, user, episode_id):
        return ApiResponse.fail("剧集不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.get("/english/tv/episodes/{episode_id}/scenes")
def english_tv_scenes(
    episode_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([x.model_dump() for x in tv_list_scenes(db, user, episode_id)])


@router.post("/english/tv/scenes")
def english_tv_scene_create(
    body: TvSceneCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = tv_create_scene(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.get("/english/tv/scenes/{scene_id}")
def english_tv_scene_detail(
    scene_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = tv_get_scene(db, user, scene_id)
    if not out:
        return ApiResponse.fail("场景不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.put("/english/tv/scenes/{scene_id}")
def english_tv_scene_update(
    scene_id: str,
    body: TvSceneUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = tv_update_scene(db, user, scene_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("场景不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/english/tv/scenes/{scene_id}")
def english_tv_scene_delete(
    scene_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not tv_delete_scene(db, user, scene_id):
        return ApiResponse.fail("场景不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.get("/english/tv/scenes/{scene_id}/session")
def english_tv_session_get(
    scene_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = tv_get_session(db, user, scene_id)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/english/tv/scenes/{scene_id}/session")
def english_tv_session_update(
    scene_id: str,
    body: TvStudySessionUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = tv_update_session(db, user, scene_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.get("/english/tv/expressions")
def english_tv_expressions(
    status: str | None = Query(None),
    sceneId: str | None = Query(None),
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(
        [x.model_dump() for x in tv_list_expressions(db, user, status=status, scene_id=sceneId)]
    )


@router.get("/english/tv/expressions/due")
def english_tv_expressions_due(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(
        [x.model_dump() for x in tv_list_expressions(db, user, status="review")]
    )


@router.post("/english/tv/expressions")
def english_tv_expression_create(
    body: TvExpressionCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = tv_create_expression(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/english/tv/expressions/{expr_id}")
def english_tv_expression_update(
    expr_id: str,
    body: TvExpressionUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = tv_update_expression(db, user, expr_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("表达卡不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.post("/english/tv/expressions/{expr_id}/review")
def english_tv_expression_review(
    expr_id: str,
    body: dict,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    result = (body or {}).get("result", "good")
    out = tv_review_expression(db, user, expr_id, result=result)
    if not out:
        return ApiResponse.fail("表达卡不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/english/tv/expressions/{expr_id}")
def english_tv_expression_delete(
    expr_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not tv_delete_expression(db, user, expr_id):
        return ApiResponse.fail("表达卡不存在", code=404)
    return ApiResponse.ok({"ok": True})


# ===== 语音识别 ASR（默认前端免费 Web Speech；可选云） =====


@router.get("/asr/status")
def asr_status_api(
    _user: AppUser = Depends(get_app_user),
):
    from app.services.asr_service import asr_status

    return ApiResponse.ok(asr_status())


@router.post("/asr/transcribe")
async def asr_transcribe(
    file: UploadFile = File(...),
    _user: AppUser = Depends(get_app_user),
):
    from app.services.asr_service import asr_status, transcribe_audio

    st = asr_status()
    if not st.get("cloudAvailable"):
        return ApiResponse.fail(
            "云 ASR 未配置。当前请使用浏览器免费语音识别；或设置 ASR_PROVIDER=aliyun|tencent",
            code=400,
        )
    raw = await file.read()
    if not raw:
        return ApiResponse.fail("空音频", code=400)
    if len(raw) > 6 * 1024 * 1024:
        return ApiResponse.fail("音频过大（建议 60 秒内）", code=400)
    try:
        text = transcribe_audio(
            raw,
            content_type=file.content_type or "audio/webm",
            filename=file.filename or "speech.webm",
        )
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    except Exception as e:
        return ApiResponse.fail(f"识别失败：{e}", code=500)
    return ApiResponse.ok({"text": text, "engine": st.get("provider")})


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


@router.get("/dushu/stats")
def dushu_stats(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(get_dushu_stats(db, user).model_dump())


@router.get("/growth/overview")
def growth_overview(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    """知行足迹：个人成长总览"""
    return ApiResponse.ok(get_growth_overview(db, user).model_dump())


# ===== 健康模块 =====


@router.get("/health/overview")
def health_overview(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(get_health_overview(db, user).model_dump())


@router.get("/health/phases")
def health_phases(user: AppUser = Depends(get_app_user)):
    return ApiResponse.ok([p.model_dump() for p in list_health_phases()])


@router.get("/health/tasks")
def health_tasks(
    phase: int | None = None,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if phase is None:
        ov = get_health_overview(db, user)
        phase = ov.phase.phase
    return ApiResponse.ok([t.model_dump() for t in health_tasks_for_phase(phase)])


@router.get("/health/daily")
def health_daily_get(
    date: str | None = None,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = get_health_daily(db, user, date)
    return ApiResponse.ok(out.model_dump() if out else None)


@router.get("/health/daily/week")
def health_daily_week(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    from datetime import timedelta
    from app.timezone import now as tz_now

    d = tz_now().date()
    monday = d - timedelta(days=d.weekday())
    start = monday.strftime("%Y-%m-%d")
    end = (monday + timedelta(days=6)).strftime("%Y-%m-%d")
    return ApiResponse.ok([x.model_dump() for x in list_health_daily_range(db, user, start, end)])


@router.post("/health/daily")
def health_daily_upsert(
    body: HealthDailyLogUpsert,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(upsert_health_daily(db, user, body).model_dump())


@router.post("/health/program/reset")
def health_program_reset(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    st = reset_health_program(db, user)
    return ApiResponse.ok({"programStartDate": st.program_start_date})


class HealthFocusBody(BaseModel):
    text: str = ""


@router.put("/health/focus")
def health_focus_update(
    body: HealthFocusBody,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok({"privateFocus": update_health_private_focus(db, user, body.text)})


@router.get("/dushu/books")
def dushu_books_list(
    status: str | None = None,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([b.model_dump() for b in list_dushu_books(db, user, status)])


@router.post("/dushu/books")
def dushu_book_create(
    body: DushuBookCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = create_dushu_book(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.get("/dushu/books/{book_id}")
def dushu_book_detail(
    book_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = get_dushu_book(db, user, book_id)
    if not out:
        return ApiResponse.fail("书籍不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.put("/dushu/books/{book_id}")
def dushu_book_update(
    book_id: str,
    body: DushuBookUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = update_dushu_book(db, user, book_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("书籍不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/dushu/books/{book_id}")
def dushu_book_delete(
    book_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_dushu_book(db, user, book_id):
        return ApiResponse.fail("书籍不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.get("/dushu/daily")
def dushu_daily_list(
    book_id: str | None = None,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([d.model_dump() for d in list_dushu_daily(db, user, book_id)])


@router.get("/dushu/daily/by-date/{log_date}")
def dushu_daily_by_date(
    log_date: str,
    book_id: str | None = None,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = get_dushu_daily_by_date(db, user, log_date, book_id)
    return ApiResponse.ok(out.model_dump() if out else None)


@router.post("/dushu/daily")
def dushu_daily_upsert(
    body: DushuDailyLogUpsert,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = upsert_dushu_daily(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.delete("/dushu/daily/{log_id}")
def dushu_daily_delete(
    log_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_dushu_daily(db, user, log_id):
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.get("/dushu/persons")
def dushu_persons_list(
    book_id: str | None = None,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([p.model_dump() for p in list_dushu_persons(db, user, book_id)])


@router.post("/dushu/persons")
def dushu_person_create(
    body: DushuPersonCardCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = create_dushu_person(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/dushu/persons/{card_id}")
def dushu_person_update(
    card_id: str,
    body: DushuPersonCardUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = update_dushu_person(db, user, card_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("人物卡不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/dushu/persons/{card_id}")
def dushu_person_delete(
    card_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_dushu_person(db, user, card_id):
        return ApiResponse.fail("人物卡不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.get("/dushu/summaries")
def dushu_summaries_list(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([s.model_dump() for s in list_dushu_summaries(db, user)])


@router.get("/dushu/summaries/{book_id}")
def dushu_summary_detail(
    book_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = get_dushu_summary(db, user, book_id)
    return ApiResponse.ok(out.model_dump() if out else None)


@router.post("/dushu/summaries")
def dushu_summary_upsert(
    body: DushuBookSummaryUpsert,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = upsert_dushu_summary(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


# ===== 记账模块 =====


@router.get("/ledger/overview")
def ledger_overview(
    month: str | None = Query(None),
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(get_ledger_overview(db, user, month).model_dump())


@router.get("/ledger/expenses")
def ledger_expenses_list(
    month: str | None = Query(None),
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([e.model_dump() for e in list_ledger_expenses(db, user, month)])


@router.get("/ledger/expenses/{expense_id}")
def ledger_expense_detail(
    expense_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = get_ledger_expense(db, user, expense_id)
    if not out:
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.post("/ledger/expenses")
def ledger_expense_create(
    body: LedgerExpenseCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = create_ledger_expense(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/ledger/expenses/{expense_id}")
def ledger_expense_update(
    expense_id: str,
    body: LedgerExpenseUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = update_ledger_expense(db, user, expense_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/ledger/expenses/{expense_id}")
def ledger_expense_delete(
    expense_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_ledger_expense(db, user, expense_id):
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.get("/ledger/loans")
def ledger_loans_list(
    status: str | None = Query(None),
    counterparty: str | None = Query(None),
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(
        [x.model_dump() for x in list_ledger_loans(db, user, status, counterparty)]
    )


@router.get("/ledger/counterparties")
def ledger_counterparties_list(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    """按对方汇总：一共欠多少、几笔未结清"""
    return ApiResponse.ok([x.model_dump() for x in list_ledger_counterparties(db, user)])


@router.get("/ledger/loans/{loan_id}")
def ledger_loan_detail(
    loan_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = get_ledger_loan(db, user, loan_id)
    if not out:
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.post("/ledger/loans")
def ledger_loan_create(
    body: LedgerLoanCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = create_ledger_loan(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/ledger/loans/{loan_id}")
def ledger_loan_update(
    loan_id: str,
    body: LedgerLoanUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = update_ledger_loan(db, user, loan_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/ledger/loans/{loan_id}")
def ledger_loan_delete(
    loan_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_ledger_loan(db, user, loan_id):
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.post("/ledger/loans/{loan_id}/repayments")
def ledger_repay_create(
    loan_id: str,
    body: LedgerRepaymentCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = create_ledger_repayment(db, user, loan_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/ledger/repayments/{repay_id}")
def ledger_repay_update(
    repay_id: str,
    body: LedgerRepaymentUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = update_ledger_repayment(db, user, repay_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/ledger/repayments/{repay_id}")
def ledger_repay_delete(
    repay_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_ledger_repayment(db, user, repay_id):
        return ApiResponse.fail("记录不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.post("/ledger/upload")
async def ledger_upload(
    file: UploadFile = File(...),
    user: AppUser = Depends(get_app_user),
):
    """凭据/小票图片上传"""
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
    raw = await file.read()
    if not raw:
        return ApiResponse.fail("文件为空", code=400)
    if len(raw) > 5 * 1024 * 1024:
        return ApiResponse.fail("图片不能超过 5MB", code=400)
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
        elif raw[:8] == b"\x89PNG\r\n\x1a\n":
            ext = ".png"
        elif raw[:3] == b"GIF":
            ext = ".gif"
        elif len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
            ext = ".webp"
        elif raw[:2] == b"\xff\xd8":
            ext = ".jpg"
        else:
            return ApiResponse.fail("仅支持 jpg/png/webp/gif 图片", code=400)

    upload_dir = Path(__file__).resolve().parents[3] / "data" / "uploads" / "ledger"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{user.id}_{uuid4().hex[:12]}{ext}"
    dest = upload_dir / filename
    dest.write_bytes(raw)
    return ApiResponse.ok({"url": f"/uploads/ledger/{filename}"})


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


@router.get("/wealth/hub")
def wealth_hub(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(get_wealth_hub(db, user).model_dump())


@router.get("/wealth/snapshots")
def wealth_snapshots_list(
    limit: int = Query(30, ge=1, le=100),
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([s.model_dump() for s in list_wealth_snapshots(db, user, limit)])


@router.get("/wealth/snapshots/{snap_id}")
def wealth_snapshot_detail(
    snap_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = get_wealth_snapshot(db, user, snap_id)
    if not out:
        return ApiResponse.fail("快照不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.post("/wealth/snapshots")
def wealth_snapshot_create(
    body: WealthSnapshotCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(create_wealth_snapshot(db, user, body).model_dump())


@router.put("/wealth/snapshots/{snap_id}")
def wealth_snapshot_update(
    snap_id: str,
    body: WealthSnapshotUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = update_wealth_snapshot(db, user, snap_id, body)
    if not out:
        return ApiResponse.fail("快照不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/wealth/snapshots/{snap_id}")
def wealth_snapshot_delete(
    snap_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_wealth_snapshot(db, user, snap_id):
        return ApiResponse.fail("快照不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.get("/wealth/principles")
def wealth_principles_list(
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([p.model_dump() for p in list_wealth_principles(db, user)])


@router.post("/wealth/principles")
def wealth_principle_create(
    body: WealthPrincipleCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = create_wealth_principle(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/wealth/principles/{principle_id}")
def wealth_principle_update(
    principle_id: str,
    body: WealthPrincipleUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = update_wealth_principle(db, user, principle_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("原则不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/wealth/principles/{principle_id}")
def wealth_principle_delete(
    principle_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_wealth_principle(db, user, principle_id):
        return ApiResponse.fail("原则不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.get("/wealth/journals")
def wealth_journals_list(
    side: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok([j.model_dump() for j in list_wealth_journals(db, user, side, limit)])


@router.get("/wealth/journals/{journal_id}")
def wealth_journal_detail(
    journal_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    out = get_wealth_journal(db, user, journal_id)
    if not out:
        return ApiResponse.fail("日志不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.post("/wealth/journals")
def wealth_journal_create(
    body: WealthJournalCreate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = create_wealth_journal(db, user, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    return ApiResponse.ok(out.model_dump())


@router.put("/wealth/journals/{journal_id}")
def wealth_journal_update(
    journal_id: str,
    body: WealthJournalUpdate,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    try:
        out = update_wealth_journal(db, user, journal_id, body)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
    if not out:
        return ApiResponse.fail("日志不存在", code=404)
    return ApiResponse.ok(out.model_dump())


@router.delete("/wealth/journals/{journal_id}")
def wealth_journal_delete(
    journal_id: str,
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    if not delete_wealth_journal(db, user, journal_id):
        return ApiResponse.fail("日志不存在", code=404)
    return ApiResponse.ok({"ok": True})


@router.get("/wealth/review")
def wealth_review(
    weekStart: str | None = Query(None),
    user: AppUser = Depends(get_app_user),
    db: Session = Depends(get_db),
):
    return ApiResponse.ok(get_wealth_review(db, user, weekStart).model_dump())


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
