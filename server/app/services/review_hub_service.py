"""今日复习中心：聚合各模块待复习/待内化数量。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AppUser, UserVocab
from app.schemas import ReviewHubOut
from app.services.corpus_service import get_stats as get_corpus_stats
from app.services.knowledge_review_service import count_due
from app.services.manual_wrong_service import (
    count_due_manual_wrongs,
    count_waiting_manual_wrongs,
)
from app.services.review_scheduler_service import MODULE_CAPS, build_review_plan
from app.services.study_service import generate_review_tasks
from app.services.tv_english_service import count_due_expressions
from app.services.wrong_service import (
    count_due_wrongs,
    count_waiting_wrongs,
)
from app.timezone import now


def get_review_hub(db: Session, user: AppUser) -> ReviewHubOut:
    knowledge_due = count_due(db)
    article_review = len(generate_review_tasks(db, user.id))
    corpus_inbox = get_corpus_stats(db, user).inboxCount

    now_naive = now().replace(tzinfo=None)
    vocab_review = (
        db.query(UserVocab)
        .filter(
            UserVocab.user_id == user.id,
            UserVocab.mastered.is_(False),
            (UserVocab.next_review_at.is_(None)) | (UserVocab.next_review_at <= now_naive),
        )
        .count()
    )

    # 只计今日到期，不把未到期错题算进待办
    article_wrong = count_due_wrongs(db, user.id)
    manual_wrong = count_due_manual_wrongs(db, user.id)
    wrong_review = article_wrong + manual_wrong
    wrong_waiting = count_waiting_wrongs(db, user.id) + count_waiting_manual_wrongs(db, user.id)
    wrong_recommend = min(wrong_review, MODULE_CAPS["wrong"])
    tv_expr_due = count_due_expressions(db, user.id)
    schedule = build_review_plan(
        [
            {"key": "wrong", "due": wrong_review, "cap": MODULE_CAPS["wrong"], "priority": 100},
            {"key": "knowledge", "due": knowledge_due, "cap": MODULE_CAPS["knowledge"], "priority": 90},
            {"key": "vocab", "due": vocab_review, "cap": MODULE_CAPS["vocab"], "priority": 70},
            {"key": "article", "due": article_review, "cap": MODULE_CAPS["article"], "priority": 60},
            {"key": "tv_expression", "due": tv_expr_due, "cap": MODULE_CAPS["tv_expression"], "priority": 50},
            {"key": "corpus", "due": corpus_inbox, "cap": MODULE_CAPS["corpus"], "priority": 40},
        ]
    )

    total = (
        knowledge_due
        + article_review
        + corpus_inbox
        + vocab_review
        + wrong_review
        + tv_expr_due
    )
    return ReviewHubOut(
        knowledgeDueCount=knowledge_due,
        articleReviewCount=article_review,
        corpusInboxCount=corpus_inbox,
        vocabReviewCount=vocab_review,
        articleWrongCount=article_wrong,
        manualWrongCount=manual_wrong,
        wrongReviewCount=wrong_review,
        wrongWaitingCount=wrong_waiting,
        wrongRecommendCount=wrong_recommend,
        tvExpressionDueCount=tv_expr_due,
        todayBudget=schedule["todayBudget"],
        todayRecommended=schedule["todayRecommended"],
        backlogCount=schedule["backlogCount"],
        estimatedClearDays=schedule["estimatedClearDays"],
        reviewPlan=schedule["reviewPlan"],
        totalCount=total,
    )
