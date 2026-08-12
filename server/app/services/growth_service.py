"""知行足迹：聚合各模块学习数据，供成长总览页展示"""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.models import (
    AppUser,
    DushuDailyLog,
    ExamAttempt,
    ManualWrong,
    PlanTask,
    QuizAttempt,
    SignRecord,
    StudyRecord,
    WrongAnswer,
)
from app.schemas import GrowthDayBar, GrowthDomainProgress, GrowthOverviewOut
from app.services.dushu_service import get_stats as get_dushu_stats
from app.services.english_service import get_stats as get_english_stats
from app.services.shenlun_service import get_stats as get_shenlun_stats
from app.services.user_service import calc_sign_streak
from app.timezone import now, today as today_str

_WEEKDAY_LABELS = ["一", "二", "三", "四", "五", "六", "日"]


def _week_range():
    d = now().date()
    monday = d - timedelta(days=d.weekday())
    days = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    return monday.strftime("%Y-%m-%d"), (monday + timedelta(days=6)).strftime("%Y-%m-%d"), days


def _pct(num: float, den: float) -> int:
    if den <= 0:
        return 0
    return max(0, min(100, int(round(num / den * 100))))


def get_growth_overview(db: Session, user: AppUser) -> GrowthOverviewOut:
    today = today_str()
    week_start, week_end, week_dates = _week_range()
    streak = calc_sign_streak(db, user.id, today)

    # —— 本周计划分钟 / 完成 ——
    plan_rows = (
        db.query(PlanTask)
        .filter(
            PlanTask.user_id == user.id,
            PlanTask.plan_date >= week_start,
            PlanTask.plan_date <= week_end,
        )
        .all()
    )
    plan_total = len(plan_rows)
    plan_done = sum(1 for t in plan_rows if t.status == "done")
    plan_minutes_by_day: dict[str, int] = {d: 0 for d in week_dates}
    for t in plan_rows:
        plan_minutes_by_day[t.plan_date] = plan_minutes_by_day.get(t.plan_date, 0) + int(
            t.actual_minutes or 0
        )

    # —— 读书分钟 ——
    dushu_rows = (
        db.query(DushuDailyLog)
        .filter(
            DushuDailyLog.user_id == user.id,
            DushuDailyLog.log_date >= week_start,
            DushuDailyLog.log_date <= week_end,
        )
        .all()
    )
    dushu_minutes_by_day: dict[str, int] = {d: 0 for d in week_dates}
    for r in dushu_rows:
        dushu_minutes_by_day[r.log_date] = dushu_minutes_by_day.get(r.log_date, 0) + int(
            r.duration_min or 0
        )

    # —— 英语分钟（EnglishStudyLog）——
    from app.models import EnglishStudyLog

    eng_logs = (
        db.query(EnglishStudyLog)
        .filter(
            EnglishStudyLog.user_id == user.id,
            EnglishStudyLog.study_date >= week_start,
            EnglishStudyLog.study_date <= week_end,
        )
        .all()
    )
    eng_minutes_by_day: dict[str, int] = {d: 0 for d in week_dates}
    for l in eng_logs:
        eng_minutes_by_day[l.study_date] = eng_minutes_by_day.get(l.study_date, 0) + int(
            (l.duration_sec or 0) / 60
        )

    week_minutes = 0
    week_bars: list[GrowthDayBar] = []
    for i, date in enumerate(week_dates):
        mins = (
            plan_minutes_by_day.get(date, 0)
            + dushu_minutes_by_day.get(date, 0)
            + eng_minutes_by_day.get(date, 0)
        )
        # 无实际分钟时，用计划完成数估一个活跃度（每完成 1 任务计 15）
        if mins <= 0:
            day_tasks = [t for t in plan_rows if t.plan_date == date and t.status == "done"]
            mins = len(day_tasks) * 15
        week_minutes += mins
        week_bars.append(
            GrowthDayBar(
                date=date,
                label=_WEEKDAY_LABELS[i],
                minutes=mins,
                isToday=date == today,
            )
        )

    # —— 本周刷题 ——
    week_start_dt = now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
        days=now().weekday()
    )
    if week_start_dt.tzinfo is not None:
        week_start_dt = week_start_dt.replace(tzinfo=None)
    quiz_week = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user.id, QuizAttempt.created_at >= week_start_dt)
        .all()
    )
    week_quiz_total = sum(q.total_count for q in quiz_week)
    week_quiz_correct = sum(q.correct_count for q in quiz_week)

    # —— 累计 ——
    article_read = db.query(StudyRecord).filter(StudyRecord.user_id == user.id).count()
    article_wrong = db.query(WrongAnswer).filter(WrongAnswer.user_id == user.id).count()
    manual_all = db.query(ManualWrong).filter(ManualWrong.user_id == user.id).count()
    manual_mastered = (
        db.query(ManualWrong)
        .filter(ManualWrong.user_id == user.id, ManualWrong.mastered.is_(True))
        .count()
    )
    exam_finished = (
        db.query(ExamAttempt)
        .filter(ExamAttempt.user_id == user.id, ExamAttempt.is_finished.is_(True))
        .count()
    )
    sign_days = db.query(SignRecord).filter(SignRecord.user_id == user.id).count()

    shenlun = get_shenlun_stats(db, user)
    english = get_english_stats(db, user)
    dushu = get_dushu_stats(db, user)

    domains = [
        GrowthDomainProgress(
            key="plan",
            name="计划执行",
            percent=_pct(plan_done, plan_total) if plan_total else 0,
            detail=f"本周 {plan_done}/{plan_total} 项",
        ),
        GrowthDomainProgress(
            key="shenlun",
            name="申论·人民日报",
            percent=_pct(shenlun.weekMineDays, shenlun.weekMineTarget or 7),
            detail=f"本周开采 {shenlun.weekMineDays} 天 · 词库 {shenlun.termCount}",
        ),
        GrowthDomainProgress(
            key="english",
            name="英语",
            percent=_pct(english.weekMinutes, 210),  # 目标约每天 30 分钟
            detail=f"本周 {english.weekMinutes} 分钟 · 语法掌握 {english.grammarMasteredCount}",
        ),
        GrowthDomainProgress(
            key="dushu",
            name="读书",
            percent=_pct(dushu.weekReadDays, dushu.weekReadTarget or 7),
            detail=f"本周阅读 {dushu.weekReadDays} 天 · 输出 {dushu.weekOutputCount} 次",
        ),
        GrowthDomainProgress(
            key="wrong",
            name="错题消化",
            percent=_pct(manual_mastered, manual_all) if manual_all else (100 if article_wrong == 0 else 0),
            detail=f"行测掌握 {manual_mastered}/{manual_all} · 文章错题 {article_wrong}",
        ),
    ]

    return GrowthOverviewOut(
        signStreak=streak,
        signDays=sign_days,
        points=user.points,
        weekMinutes=week_minutes,
        weekQuizTotal=week_quiz_total,
        weekQuizCorrect=week_quiz_correct,
        articleReadCount=article_read,
        examFinishedCount=exam_finished,
        weekBars=week_bars,
        domains=domains,
    )
