"""读书模块：书架 / 每日输出 / 人物卡 / 一书一页"""
from __future__ import annotations

import json
from datetime import timedelta

from sqlalchemy.orm import Session

from app.models import (
    AppUser,
    DushuBook,
    DushuBookSummary,
    DushuDailyLog,
    DushuPersonCard,
    gen_id,
)
from app.schemas import (
    DushuBookCreate,
    DushuBookOut,
    DushuBookSummaryOut,
    DushuBookSummaryUpsert,
    DushuBookUpdate,
    DushuDailyLogOut,
    DushuDailyLogUpsert,
    DushuPersonCardCreate,
    DushuPersonCardOut,
    DushuPersonCardUpdate,
    DushuStatsOut,
)
from app.timezone import now


def _today() -> str:
    return now().strftime("%Y-%m-%d")


def _loads(raw: str | None, default):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


def _book_out(b: DushuBook) -> DushuBookOut:
    return DushuBookOut(
        id=b.id,
        title=b.title,
        author=b.author or "",
        category=b.category or "历史",
        status=b.status or "reading",
        currentChapter=b.current_chapter or "",
        coverNote=b.cover_note or "",
        createdAt=b.created_at,
        updatedAt=b.updated_at,
    )


def _daily_out(d: DushuDailyLog, book: DushuBook | None = None) -> DushuDailyLogOut:
    return DushuDailyLogOut(
        id=d.id,
        bookId=d.book_id,
        bookTitle=book.title if book else "",
        bookCategory=book.category if book else "",
        logDate=d.log_date,
        chapter=d.chapter or "",
        goal=d.goal or "",
        output=_loads(d.output_json, {}),
        oralNote=d.oral_note or "",
        tags=d.tags or "",
        durationMin=d.duration_min or 60,
        createdAt=d.created_at,
        updatedAt=d.updated_at,
    )


def _person_out(p: DushuPersonCard, book: DushuBook | None = None) -> DushuPersonCardOut:
    return DushuPersonCardOut(
        id=p.id,
        bookId=p.book_id,
        bookTitle=book.title if book else "",
        name=p.name,
        trait=p.trait or "",
        success=p.success or "",
        failure=p.failure or "",
        lesson=p.lesson or "",
        tags=p.tags or "",
        createdAt=p.created_at,
        updatedAt=p.updated_at,
    )


def _summary_out(s: DushuBookSummary, book: DushuBook | None = None) -> DushuBookSummaryOut:
    insights = _loads(s.insights_json, [])
    if not isinstance(insights, list):
        insights = []
    return DushuBookSummaryOut(
        id=s.id,
        bookId=s.book_id,
        bookTitle=book.title if book else "",
        coreQuestion=s.core_question or "",
        skeleton=s.skeleton or "",
        insights=[str(x) for x in insights][:3],
        story=s.story or "",
        model=s.model or "",
        action=s.action or "",
        createdAt=s.created_at,
        updatedAt=s.updated_at,
    )


def _get_book(db: Session, user: AppUser, book_id: str) -> DushuBook | None:
    b = db.get(DushuBook, book_id)
    if not b or b.user_id != user.id:
        return None
    return b


# ---- books ----

def list_books(db: Session, user: AppUser, status: str | None = None) -> list[DushuBookOut]:
    q = db.query(DushuBook).filter(DushuBook.user_id == user.id)
    if status:
        q = q.filter(DushuBook.status == status)
    rows = q.order_by(DushuBook.updated_at.desc()).all()
    return [_book_out(b) for b in rows]


def get_book(db: Session, user: AppUser, book_id: str) -> DushuBookOut | None:
    b = _get_book(db, user, book_id)
    return _book_out(b) if b else None


def create_book(db: Session, user: AppUser, body: DushuBookCreate) -> DushuBookOut:
    title = (body.title or "").strip()
    if not title:
        raise ValueError("书名不能为空")
    b = DushuBook(
        id=gen_id("dbk"),
        user_id=user.id,
        title=title,
        author=(body.author or "").strip(),
        category=(body.category or "历史").strip() or "历史",
        status=(body.status or "reading").strip() or "reading",
        current_chapter=(body.currentChapter or "").strip(),
        cover_note=(body.coverNote or "").strip(),
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return _book_out(b)


def update_book(db: Session, user: AppUser, book_id: str, body: DushuBookUpdate) -> DushuBookOut | None:
    b = _get_book(db, user, book_id)
    if not b:
        return None
    data = body.model_dump(exclude_unset=True)
    mapping = {
        "title": "title",
        "author": "author",
        "category": "category",
        "status": "status",
        "currentChapter": "current_chapter",
        "coverNote": "cover_note",
    }
    for k, col in mapping.items():
        if k in data and data[k] is not None:
            setattr(b, col, str(data[k]).strip())
    if not b.title:
        raise ValueError("书名不能为空")
    db.commit()
    db.refresh(b)
    return _book_out(b)


def delete_book(db: Session, user: AppUser, book_id: str) -> bool:
    b = _get_book(db, user, book_id)
    if not b:
        return False
    db.query(DushuDailyLog).filter(DushuDailyLog.book_id == book_id).delete()
    db.query(DushuPersonCard).filter(DushuPersonCard.book_id == book_id).delete()
    db.query(DushuBookSummary).filter(DushuBookSummary.book_id == book_id).delete()
    db.delete(b)
    db.commit()
    return True


# ---- daily ----

def list_daily(db: Session, user: AppUser, book_id: str | None = None) -> list[DushuDailyLogOut]:
    q = db.query(DushuDailyLog).filter(DushuDailyLog.user_id == user.id)
    if book_id:
        q = q.filter(DushuDailyLog.book_id == book_id)
    rows = q.order_by(DushuDailyLog.log_date.desc(), DushuDailyLog.id.desc()).limit(100).all()
    books = {b.id: b for b in db.query(DushuBook).filter(DushuBook.user_id == user.id).all()}
    return [_daily_out(d, books.get(d.book_id)) for d in rows]


def get_daily_by_date(db: Session, user: AppUser, log_date: str, book_id: str | None = None) -> DushuDailyLogOut | None:
    q = db.query(DushuDailyLog).filter(DushuDailyLog.user_id == user.id, DushuDailyLog.log_date == log_date)
    if book_id:
        q = q.filter(DushuDailyLog.book_id == book_id)
    d = q.order_by(DushuDailyLog.updated_at.desc()).first()
    if not d:
        return None
    return _daily_out(d, _get_book(db, user, d.book_id))


def upsert_daily(db: Session, user: AppUser, body: DushuDailyLogUpsert) -> DushuDailyLogOut:
    book = _get_book(db, user, body.bookId)
    if not book:
        raise ValueError("书籍不存在")
    log_date = (body.logDate or _today()).strip()
    output = body.output if isinstance(body.output, dict) else {}
    # 至少有一点输出内容
    has_output = any(str(v).strip() for v in output.values()) or bool((body.oralNote or "").strip())
    if not has_output and not (body.goal or "").strip():
        raise ValueError("请至少填写今日目标或输出内容")

    d = (
        db.query(DushuDailyLog)
        .filter(
            DushuDailyLog.user_id == user.id,
            DushuDailyLog.book_id == body.bookId,
            DushuDailyLog.log_date == log_date,
        )
        .first()
    )
    payload = {
        "chapter": (body.chapter or "").strip(),
        "goal": (body.goal or "").strip(),
        "output_json": json.dumps(output, ensure_ascii=False),
        "oral_note": (body.oralNote or "").strip(),
        "tags": (body.tags or "").strip(),
        "duration_min": int(body.durationMin or 60),
    }
    if d:
        for k, v in payload.items():
            setattr(d, k, v)
    else:
        d = DushuDailyLog(
            id=gen_id("ddl"),
            user_id=user.id,
            book_id=body.bookId,
            log_date=log_date,
            **payload,
        )
        db.add(d)
    if payload["chapter"]:
        book.current_chapter = payload["chapter"]
    db.commit()
    db.refresh(d)
    return _daily_out(d, book)


def delete_daily(db: Session, user: AppUser, log_id: str) -> bool:
    d = db.get(DushuDailyLog, log_id)
    if not d or d.user_id != user.id:
        return False
    db.delete(d)
    db.commit()
    return True


# ---- person cards ----

def list_persons(db: Session, user: AppUser, book_id: str | None = None) -> list[DushuPersonCardOut]:
    q = db.query(DushuPersonCard).filter(DushuPersonCard.user_id == user.id)
    if book_id:
        q = q.filter(DushuPersonCard.book_id == book_id)
    rows = q.order_by(DushuPersonCard.updated_at.desc()).all()
    books = {b.id: b for b in db.query(DushuBook).filter(DushuBook.user_id == user.id).all()}
    return [_person_out(p, books.get(p.book_id)) for p in rows]


def create_person(db: Session, user: AppUser, body: DushuPersonCardCreate) -> DushuPersonCardOut:
    book = _get_book(db, user, body.bookId)
    if not book:
        raise ValueError("书籍不存在")
    name = (body.name or "").strip()
    if not name:
        raise ValueError("人物名不能为空")
    p = DushuPersonCard(
        id=gen_id("dpc"),
        user_id=user.id,
        book_id=body.bookId,
        name=name,
        trait=(body.trait or "").strip(),
        success=(body.success or "").strip(),
        failure=(body.failure or "").strip(),
        lesson=(body.lesson or "").strip(),
        tags=(body.tags or "").strip(),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _person_out(p, book)


def update_person(
    db: Session, user: AppUser, card_id: str, body: DushuPersonCardUpdate
) -> DushuPersonCardOut | None:
    p = db.get(DushuPersonCard, card_id)
    if not p or p.user_id != user.id:
        return None
    data = body.model_dump(exclude_unset=True)
    for k in ("name", "trait", "success", "failure", "lesson", "tags"):
        if k in data and data[k] is not None:
            setattr(p, k, str(data[k]).strip())
    if not p.name:
        raise ValueError("人物名不能为空")
    db.commit()
    db.refresh(p)
    return _person_out(p, _get_book(db, user, p.book_id))


def delete_person(db: Session, user: AppUser, card_id: str) -> bool:
    p = db.get(DushuPersonCard, card_id)
    if not p or p.user_id != user.id:
        return False
    db.delete(p)
    db.commit()
    return True


# ---- book summary ----

def get_summary(db: Session, user: AppUser, book_id: str) -> DushuBookSummaryOut | None:
    s = (
        db.query(DushuBookSummary)
        .filter(DushuBookSummary.user_id == user.id, DushuBookSummary.book_id == book_id)
        .first()
    )
    if not s:
        return None
    return _summary_out(s, _get_book(db, user, book_id))


def upsert_summary(db: Session, user: AppUser, body: DushuBookSummaryUpsert) -> DushuBookSummaryOut:
    book = _get_book(db, user, body.bookId)
    if not book:
        raise ValueError("书籍不存在")
    insights = [str(x).strip() for x in (body.insights or []) if str(x).strip()][:3]
    s = (
        db.query(DushuBookSummary)
        .filter(DushuBookSummary.user_id == user.id, DushuBookSummary.book_id == body.bookId)
        .first()
    )
    payload = {
        "core_question": (body.coreQuestion or "").strip(),
        "skeleton": (body.skeleton or "").strip(),
        "insights_json": json.dumps(insights, ensure_ascii=False),
        "story": (body.story or "").strip(),
        "model": (body.model or "").strip(),
        "action": (body.action or "").strip(),
    }
    if s:
        for k, v in payload.items():
            setattr(s, k, v)
    else:
        s = DushuBookSummary(id=gen_id("dbs"), user_id=user.id, book_id=body.bookId, **payload)
        db.add(s)
    db.commit()
    db.refresh(s)
    return _summary_out(s, book)


def list_summaries(db: Session, user: AppUser) -> list[DushuBookSummaryOut]:
    rows = (
        db.query(DushuBookSummary)
        .filter(DushuBookSummary.user_id == user.id)
        .order_by(DushuBookSummary.updated_at.desc())
        .all()
    )
    books = {b.id: b for b in db.query(DushuBook).filter(DushuBook.user_id == user.id).all()}
    return [_summary_out(s, books.get(s.book_id)) for s in rows]


# ---- stats ----

def get_stats(db: Session, user: AppUser) -> DushuStatsOut:
    d = now().date()
    monday = d - timedelta(days=d.weekday())
    week_start = monday.strftime("%Y-%m-%d")
    week_end = (monday + timedelta(days=6)).strftime("%Y-%m-%d")
    today = _today()

    week_rows = (
        db.query(DushuDailyLog.log_date)
        .filter(
            DushuDailyLog.user_id == user.id,
            DushuDailyLog.log_date >= week_start,
            DushuDailyLog.log_date <= week_end,
        )
        .distinct()
        .all()
    )
    week_output = (
        db.query(DushuDailyLog)
        .filter(
            DushuDailyLog.user_id == user.id,
            DushuDailyLog.log_date >= week_start,
            DushuDailyLog.log_date <= week_end,
        )
        .count()
    )
    today_done = (
        db.query(DushuDailyLog)
        .filter(DushuDailyLog.user_id == user.id, DushuDailyLog.log_date == today)
        .first()
        is not None
    )
    reading = (
        db.query(DushuBook)
        .filter(DushuBook.user_id == user.id, DushuBook.status == "reading")
        .order_by(DushuBook.updated_at.desc())
        .first()
    )
    book_count = db.query(DushuBook).filter(DushuBook.user_id == user.id).count()
    person_count = db.query(DushuPersonCard).filter(DushuPersonCard.user_id == user.id).count()
    return DushuStatsOut(
        weekReadDays=len(week_rows),
        weekReadTarget=7,
        weekOutputCount=week_output,
        todayDone=today_done,
        readingBookTitle=reading.title if reading else "",
        bookCount=book_count,
        personCardCount=person_count,
    )
