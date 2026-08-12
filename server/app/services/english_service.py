"""英语学习 service：文章、生词本、口语、语法、学习记录"""
from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import (
    AppUser,
    EnglishArticle,
    EnglishStudyLog,
    GrammarLesson,
    GrammarProgress,
    SpeakingAttempt,
    SpeakingLesson,
    UserSpeakingSentence,
    UserVocab,
    gen_id,
)
from app.schemas import (
    EnglishArticleCreate,
    EnglishArticleOut,
    EnglishArticleUpdate,
    EnglishStatsOut,
    EnglishStudyLogCreate,
    GrammarLessonCreate,
    GrammarLessonOut,
    GrammarProgressOut,
    GrammarProgressUpdate,
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
)
from app.timezone import now, today as today_str

# 间隔重复：熟悉度 -> 下次复习间隔天数
REVIEW_INTERVALS = {1: 1, 2: 2, 3: 4, 4: 7, 5: 15}


def _safe_json(s: str | None, default: Any) -> Any:
    if not s:
        return default
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return default


# ===== 文章 =====


def _article_to_out(a: EnglishArticle) -> EnglishArticleOut:
    return EnglishArticleOut(
        id=a.id,
        title=a.title,
        source=a.source or "",
        level=a.level or "B1",
        content=a.content,
        vocabHighlights=_safe_json(a.vocab_highlights, []),
        audioUrl=a.audio_url or "",
        tags=_safe_json(a.tags, []),
        difficulty=a.difficulty,
        isPublished=bool(a.is_published),
        readCount=a.read_count,
        createdAt=a.created_at,
    )


def list_articles(db: Session, level: str | None = None, is_published: bool = True) -> list[EnglishArticleOut]:
    q = db.query(EnglishArticle)
    if level:
        q = q.filter(EnglishArticle.level == level)
    if is_published is not None:
        q = q.filter(EnglishArticle.is_published.is_(is_published))
    rows = q.order_by(EnglishArticle.created_at.desc()).all()
    return [_article_to_out(a) for a in rows]


def get_article(db: Session, article_id: str) -> EnglishArticleOut | None:
    a = db.get(EnglishArticle, article_id)
    if not a:
        return None
    a.read_count += 1
    db.commit()
    db.refresh(a)
    return _article_to_out(a)


def create_article(db: Session, body: EnglishArticleCreate) -> EnglishArticleOut:
    a = EnglishArticle(
        id=gen_id("enart"),
        title=body.title,
        source=body.source,
        level=body.level,
        content=body.content,
        vocab_highlights=json.dumps(body.vocabHighlights, ensure_ascii=False),
        audio_url=body.audioUrl,
        tags=json.dumps(body.tags, ensure_ascii=False),
        difficulty=body.difficulty,
        is_published=body.isPublished,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return _article_to_out(a)


def update_article(db: Session, article_id: str, body: EnglishArticleUpdate) -> EnglishArticleOut | None:
    a = db.get(EnglishArticle, article_id)
    if not a:
        return None
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        key = {"vocabHighlights": "vocab_highlights", "audioUrl": "audio_url", "isPublished": "is_published"}.get(k, k)
        if key in ("vocab_highlights", "tags"):
            setattr(a, key, json.dumps(v, ensure_ascii=False))
        else:
            setattr(a, key, v)
    db.commit()
    db.refresh(a)
    return _article_to_out(a)


def delete_article(db: Session, article_id: str) -> bool:
    a = db.get(EnglishArticle, article_id)
    if not a:
        return False
    db.delete(a)
    db.commit()
    return True


# ===== 生词本 =====


def _vocab_to_out(v: UserVocab) -> UserVocabOut:
    return UserVocabOut(
        id=v.id,
        word=v.word,
        phonetic=v.phonetic or "",
        meaning=v.meaning or "",
        pos=v.pos or "",
        exampleSentence=v.example_sentence or "",
        articleId=v.article_id,
        familiarity=v.familiarity,
        reviewCount=v.review_count,
        nextReviewAt=v.next_review_at,
        mastered=bool(v.mastered),
        createdAt=v.created_at,
    )


def list_vocabs(db: Session, user: AppUser, status: str | None = None) -> list[UserVocabOut]:
    q = db.query(UserVocab).filter(UserVocab.user_id == user.id)
    if status == "learning":
        q = q.filter(UserVocab.mastered.is_(False))
    elif status == "mastered":
        q = q.filter(UserVocab.mastered.is_(True))
    elif status == "review":
        now_naive = now().replace(tzinfo=None)
        q = q.filter(
            UserVocab.mastered.is_(False),
            (UserVocab.next_review_at.is_(None)) | (UserVocab.next_review_at <= now_naive),
        )
    rows = q.order_by(UserVocab.mastered, UserVocab.next_review_at, UserVocab.created_at.desc()).all()
    return [_vocab_to_out(v) for v in rows]


def add_vocab(db: Session, user: AppUser, body: UserVocabAdd) -> UserVocabOut:
    # 同词合并
    existing = (
        db.query(UserVocab)
        .filter(UserVocab.user_id == user.id, UserVocab.word == body.word)
        .first()
    )
    if existing:
        # 更新释义（若新值更详细）
        if body.meaning and not existing.meaning:
            existing.meaning = body.meaning
        if body.phonetic and not existing.phonetic:
            existing.phonetic = body.phonetic
        if body.exampleSentence and not existing.example_sentence:
            existing.example_sentence = body.exampleSentence
        if body.pos and not existing.pos:
            existing.pos = body.pos
        db.commit()
        db.refresh(existing)
        return _vocab_to_out(existing)
    v = UserVocab(
        id=gen_id("uv"),
        user_id=user.id,
        word=body.word,
        phonetic=body.phonetic,
        meaning=body.meaning,
        pos=body.pos,
        example_sentence=body.exampleSentence,
        article_id=body.articleId,
        familiarity=1,
        next_review_at=now() + timedelta(days=REVIEW_INTERVALS[1]),
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return _vocab_to_out(v)


def update_vocab(db: Session, user: AppUser, vocab_id: str, body: UserVocabUpdate) -> UserVocabOut | None:
    v = db.get(UserVocab, vocab_id)
    if not v or v.user_id != user.id:
        return None
    data = body.model_dump(exclude_unset=True)
    for k, val in data.items():
        key = {"exampleSentence": "example_sentence", "nextReviewAt": "next_review_at"}.get(k, k)
        setattr(v, key, val)
    # 如果更新了 familiarity，重新计算下次复习时间
    if body.familiarity is not None and not body.mastered:
        v.review_count += 1
        interval = REVIEW_INTERVALS.get(v.familiarity, 15)
        v.next_review_at = now() + timedelta(days=interval)
        if v.familiarity >= 5:
            v.mastered = True
    db.commit()
    db.refresh(v)
    return _vocab_to_out(v)


def delete_vocab(db: Session, user: AppUser, vocab_id: str) -> bool:
    v = db.get(UserVocab, vocab_id)
    if not v or v.user_id != user.id:
        return False
    db.delete(v)
    db.commit()
    return True


# ===== 跟读本（用户收藏句子） =====


def _shadow_to_out(s: UserSpeakingSentence) -> UserSpeakingSentenceOut:
    return UserSpeakingSentenceOut(
        id=s.id,
        sentence=s.sentence or "",
        note=s.note or "",
        articleId=s.article_id,
        articleTitle=s.article_title or "",
        recordingUrl=s.recording_url or "",
        practiceCount=s.practice_count or 0,
        lastPracticeAt=s.last_practice_at,
        createdAt=s.created_at,
    )


def list_shadowing(db: Session, user: AppUser) -> list[UserSpeakingSentenceOut]:
    rows = (
        db.query(UserSpeakingSentence)
        .filter(UserSpeakingSentence.user_id == user.id)
        .order_by(UserSpeakingSentence.created_at.desc())
        .all()
    )
    return [_shadow_to_out(r) for r in rows]


def add_shadowing(db: Session, user: AppUser, body: UserSpeakingSentenceAdd) -> UserSpeakingSentenceOut:
    sentence = (body.sentence or "").strip()
    if not sentence:
        raise ValueError("句子不能为空")
    existing = (
        db.query(UserSpeakingSentence)
        .filter(
            UserSpeakingSentence.user_id == user.id,
            UserSpeakingSentence.sentence == sentence,
        )
        .first()
    )
    if existing:
        if body.note and not existing.note:
            existing.note = body.note
        if body.articleId and not existing.article_id:
            existing.article_id = body.articleId
            existing.article_title = body.articleTitle or existing.article_title
        db.commit()
        db.refresh(existing)
        return _shadow_to_out(existing)
    row = UserSpeakingSentence(
        id=gen_id("uss"),
        user_id=user.id,
        sentence=sentence,
        note=body.note or "",
        article_id=body.articleId,
        article_title=body.articleTitle or "",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _shadow_to_out(row)


def update_shadowing(
    db: Session, user: AppUser, sentence_id: str, body: UserSpeakingSentenceUpdate,
) -> UserSpeakingSentenceOut | None:
    row = db.get(UserSpeakingSentence, sentence_id)
    if not row or row.user_id != user.id:
        return None
    data = body.model_dump(exclude_unset=True)
    practiced = data.pop("practiced", None)
    for k, v in data.items():
        key = {"recordingUrl": "recording_url"}.get(k, k)
        setattr(row, key, v)
    if practiced:
        row.practice_count = (row.practice_count or 0) + 1
        row.last_practice_at = now().replace(tzinfo=None)
    db.commit()
    db.refresh(row)
    return _shadow_to_out(row)


def delete_shadowing(db: Session, user: AppUser, sentence_id: str) -> bool:
    row = db.get(UserSpeakingSentence, sentence_id)
    if not row or row.user_id != user.id:
        return False
    db.delete(row)
    db.commit()
    return True


# ===== 口语课程（可选精品课） =====


def _speaking_lesson_to_out(s: SpeakingLesson) -> SpeakingLessonOut:
    return SpeakingLessonOut(
        id=s.id,
        title=s.title,
        topic=s.topic or "daily",
        level=s.level or "B1",
        dialogue=_safe_json(s.dialogue, []),
        keySentences=_safe_json(s.key_sentences, []),
        tips=s.tips or "",
        isPublished=bool(s.is_published),
        createdAt=s.created_at,
    )


def list_speaking_lessons(db: Session, topic: str | None = None) -> list[SpeakingLessonOut]:
    q = db.query(SpeakingLesson).filter(SpeakingLesson.is_published.is_(True))
    if topic:
        q = q.filter(SpeakingLesson.topic == topic)
    rows = q.order_by(SpeakingLesson.created_at.desc()).all()
    return [_speaking_lesson_to_out(s) for s in rows]


def get_speaking_lesson(db: Session, lesson_id: str) -> SpeakingLessonOut | None:
    s = db.get(SpeakingLesson, lesson_id)
    return _speaking_lesson_to_out(s) if s else None


def create_speaking_lesson(db: Session, body: SpeakingLessonCreate) -> SpeakingLessonOut:
    s = SpeakingLesson(
        id=gen_id("spk"),
        title=body.title,
        topic=body.topic,
        level=body.level,
        dialogue=json.dumps(body.dialogue, ensure_ascii=False),
        key_sentences=json.dumps(body.keySentences, ensure_ascii=False),
        tips=body.tips,
        is_published=body.isPublished,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return _speaking_lesson_to_out(s)


def update_speaking_lesson(db: Session, lesson_id: str, body: dict) -> SpeakingLessonOut | None:
    s = db.get(SpeakingLesson, lesson_id)
    if not s:
        return None
    for k, v in body.items():
        key = {"keySentences": "key_sentences", "isPublished": "is_published"}.get(k, k)
        if key in ("dialogue", "key_sentences"):
            setattr(s, key, json.dumps(v, ensure_ascii=False))
        else:
            setattr(s, key, v)
    db.commit()
    db.refresh(s)
    return _speaking_lesson_to_out(s)


def delete_speaking_lesson(db: Session, lesson_id: str) -> bool:
    s = db.get(SpeakingLesson, lesson_id)
    if not s:
        return False
    db.delete(s)
    db.commit()
    return True


def _speaking_attempt_to_out(a: SpeakingAttempt) -> SpeakingAttemptOut:
    return SpeakingAttemptOut(
        id=a.id,
        lessonId=a.lesson_id,
        recordingUrl=a.recording_url or "",
        selfRating=a.self_rating,
        note=a.note or "",
        createdAt=a.created_at,
    )


def list_speaking_attempts(db: Session, user: AppUser, lesson_id: str | None = None) -> list[SpeakingAttemptOut]:
    q = db.query(SpeakingAttempt).filter(SpeakingAttempt.user_id == user.id)
    if lesson_id:
        q = q.filter(SpeakingAttempt.lesson_id == lesson_id)
    rows = q.order_by(SpeakingAttempt.created_at.desc()).all()
    return [_speaking_attempt_to_out(a) for a in rows]


def create_speaking_attempt(db: Session, user: AppUser, body: SpeakingAttemptCreate) -> SpeakingAttemptOut:
    a = SpeakingAttempt(
        id=gen_id("spa"),
        user_id=user.id,
        lesson_id=body.lessonId,
        recording_url=body.recordingUrl,
        self_rating=body.selfRating,
        note=body.note,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return _speaking_attempt_to_out(a)


# ===== 语法 =====


def _grammar_lesson_to_out(g: GrammarLesson) -> GrammarLessonOut:
    return GrammarLessonOut(
        id=g.id,
        title=g.title,
        category=g.category or "",
        level=g.level or "B1",
        explanation=g.explanation or "",
        examples=_safe_json(g.examples, []),
        commonMistakes=_safe_json(g.common_mistakes, []),
        sortOrder=g.sort_order,
        isPublished=bool(g.is_published),
        createdAt=g.created_at,
    )


def list_grammar_lessons(db: Session, category: str | None = None) -> list[GrammarLessonOut]:
    q = db.query(GrammarLesson).filter(GrammarLesson.is_published.is_(True))
    if category:
        q = q.filter(GrammarLesson.category == category)
    rows = q.order_by(GrammarLesson.sort_order, GrammarLesson.created_at).all()
    return [_grammar_lesson_to_out(g) for g in rows]


def get_grammar_lesson(db: Session, lesson_id: str) -> GrammarLessonOut | None:
    g = db.get(GrammarLesson, lesson_id)
    return _grammar_lesson_to_out(g) if g else None


def create_grammar_lesson(db: Session, body: GrammarLessonCreate) -> GrammarLessonOut:
    g = GrammarLesson(
        id=gen_id("gm"),
        title=body.title,
        category=body.category,
        level=body.level,
        explanation=body.explanation,
        examples=json.dumps(body.examples, ensure_ascii=False),
        common_mistakes=json.dumps(body.commonMistakes, ensure_ascii=False),
        sort_order=body.sortOrder,
        is_published=body.isPublished,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return _grammar_lesson_to_out(g)


def update_grammar_lesson(db: Session, lesson_id: str, body: dict) -> GrammarLessonOut | None:
    g = db.get(GrammarLesson, lesson_id)
    if not g:
        return None
    for k, v in body.items():
        key = {"commonMistakes": "common_mistakes", "isPublished": "is_published", "sortOrder": "sort_order"}.get(k, k)
        if key in ("examples", "common_mistakes"):
            setattr(g, key, json.dumps(v, ensure_ascii=False))
        else:
            setattr(g, key, v)
    db.commit()
    db.refresh(g)
    return _grammar_lesson_to_out(g)


def delete_grammar_lesson(db: Session, lesson_id: str) -> bool:
    g = db.get(GrammarLesson, lesson_id)
    if not g:
        return False
    db.delete(g)
    db.commit()
    return True


def get_grammar_progress(db: Session, user: AppUser) -> list[GrammarProgressOut]:
    rows = db.query(GrammarProgress).filter(GrammarProgress.user_id == user.id).all()
    return [
        GrammarProgressOut(
            lessonId=r.lesson_id,
            status=r.status,
            lastStudyAt=r.last_study_at,
        )
        for r in rows
    ]


def update_grammar_progress(db: Session, user: AppUser, lesson_id: str, body: GrammarProgressUpdate) -> GrammarProgressOut:
    r = (
        db.query(GrammarProgress)
        .filter(GrammarProgress.user_id == user.id, GrammarProgress.lesson_id == lesson_id)
        .first()
    )
    if r:
        r.status = body.status
        r.last_study_at = now()
    else:
        r = GrammarProgress(
            id=gen_id("gmp"),
            user_id=user.id,
            lesson_id=lesson_id,
            status=body.status,
            last_study_at=now(),
        )
        db.add(r)
    db.commit()
    db.refresh(r)
    return GrammarProgressOut(lessonId=r.lesson_id, status=r.status, lastStudyAt=r.last_study_at)


# ===== 学习记录 + 统计 =====


def add_study_log(db: Session, user: AppUser, body: EnglishStudyLogCreate) -> dict:
    log = EnglishStudyLog(
        id=gen_id("enlog"),
        user_id=user.id,
        log_type=body.logType,
        ref_id=body.refId,
        duration_sec=body.durationSec,
        words_learned=body.wordsLearned,
        sentences_practiced=body.sentencesPracticed,
        note=body.note,
        study_date=today_str(),
    )
    db.add(log)
    db.commit()
    return {"ok": True, "id": log.id}


def get_stats(db: Session, user: AppUser) -> EnglishStatsOut:
    today = today_str()
    week_ago = (now() - timedelta(days=7)).strftime("%Y-%m-%d")
    logs = db.query(EnglishStudyLog).filter(EnglishStudyLog.user_id == user.id).all()
    today_sec = sum(l.duration_sec for l in logs if l.study_date == today)
    week_sec = sum(l.duration_sec for l in logs if l.study_date >= week_ago)
    # 生词
    vocabs = db.query(UserVocab).filter(UserVocab.user_id == user.id).all()
    now_naive = now().replace(tzinfo=None)
    new_vocab = sum(1 for v in vocabs if v.created_at and v.created_at.strftime("%Y-%m-%d") == today)
    review_vocab = sum(
        1 for v in vocabs
        if not v.mastered and v.next_review_at and v.next_review_at.replace(tzinfo=None) <= now_naive
    )
    # 口语/跟读：优先统计跟读本练习
    week_start = now_naive - timedelta(days=7)
    shadow_practiced = (
        db.query(UserSpeakingSentence)
        .filter(
            UserSpeakingSentence.user_id == user.id,
            UserSpeakingSentence.last_practice_at.isnot(None),
            UserSpeakingSentence.last_practice_at >= week_start,
        )
        .count()
    )
    attempt_count = (
        db.query(SpeakingAttempt)
        .filter(SpeakingAttempt.user_id == user.id, SpeakingAttempt.created_at >= week_start)
        .count()
    )
    speaking_count = shadow_practiced or attempt_count
    # 语法
    progress = db.query(GrammarProgress).filter(GrammarProgress.user_id == user.id).all()
    grammar_mastered = sum(1 for p in progress if p.status == "mastered")
    grammar_learning = sum(1 for p in progress if p.status == "learning")
    # 文章阅读
    article_logs = [l for l in logs if l.log_type == "article" and l.study_date == today]
    article_read_count = len(article_logs)
    # 最近 7 条日志
    recent = (
        db.query(EnglishStudyLog)
        .filter(EnglishStudyLog.user_id == user.id)
        .order_by(EnglishStudyLog.created_at.desc())
        .limit(7)
        .all()
    )
    recent_list = [
        {
            "id": l.id,
            "logType": l.log_type,
            "durationSec": l.duration_sec,
            "wordsLearned": l.words_learned,
            "sentencesPracticed": l.sentences_practiced,
            "studyDate": l.study_date,
            "note": l.note or "",
        }
        for l in recent
    ]
    return EnglishStatsOut(
        todayMinutes=int(today_sec / 60),
        weekMinutes=int(week_sec / 60),
        newVocabCount=new_vocab,
        reviewVocabCount=review_vocab,
        speakingCount=speaking_count,
        grammarMasteredCount=grammar_mastered,
        grammarLearningCount=grammar_learning,
        articleReadCount=article_read_count,
        recentLogs=recent_list,
    )
