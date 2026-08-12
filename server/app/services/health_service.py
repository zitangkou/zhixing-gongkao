"""健康模块：8 周身心恢复计划 · 每日打卡 / 阶段任务 / 心理训练"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import AppUser, HealthDailyLog, HealthUserState, gen_id
from app.schemas import (
    HealthCbtOut,
    HealthDailyLogOut,
    HealthDailyLogUpsert,
    HealthMealSlotOut,
    HealthMealsOut,
    HealthOverviewOut,
    HealthPhaseOut,
    HealthRuminationOut,
    HealthReviewOut,
    HealthStoolOut,
    HealthTaskOut,
    HealthWeekPoint,
)
from app.timezone import now, today as today_str

# skill → 通俗名
SKILL_LABELS = {
    "energy": "能量恢复",
    "cbt": "想法练习",
    "rumination": "反刍刹车",
    "exposure_micro": "小暴露",
    "exposure_pace": "节奏与卡壳",
    "exposure_talk": "开口聊天",
    "social_warm": "温暖表达",
    "exposure_stretch": "舒适区外",
    "weekend": "周末防崩",
}

PHASES: list[dict] = [
    {
        "phase": 1,
        "weekStart": 1,
        "weekEnd": 2,
        "title": "恢复心理能量",
        "goal": "不解决社交，只恢复身体和精神。",
        "principle": "心理电量不足时，先充电。散步、作息、饮食规律优先。",
        "focusSkills": ["energy", "cbt", "exposure_micro", "weekend"],
    },
    {
        "phase": 2,
        "weekStart": 3,
        "weekEnd": 4,
        "title": "降低社交焦虑",
        "goal": "用小暴露重建「社交是安全的」。",
        "principle": "打招呼即可离开；允许卡壳；刻意放慢语速。",
        "focusSkills": ["exposure_micro", "exposure_pace", "exposure_talk", "rumination", "cbt"],
    },
    {
        "phase": 3,
        "weekStart": 5,
        "weekEnd": 6,
        "title": "真正开始聊天",
        "goal": "用好奇了解别人，而不是表现自己。",
        "principle": "一个开放式问题 + 认真听；具体赞美；认真谢谢。",
        "focusSkills": ["exposure_talk", "social_warm", "rumination", "cbt"],
    },
    {
        "phase": 4,
        "weekStart": 7,
        "weekEnd": 8,
        "title": "突破舒适区",
        "goal": "完成比完美重要；允许冷场。",
        "principle": "工作场景短句即可；熟人聊两分钟；反刍严格限时。",
        "focusSkills": ["exposure_stretch", "rumination", "cbt", "weekend"],
    },
]

# 全量任务池：按 phase + skill
TASKS: list[dict] = [
    # —— 阶段1 ——
    {"id": "p1-walk", "phase": 1, "domain": "body", "skill": "energy", "title": "散步 20～30 分钟", "detail": "尽量晒太阳，不戴耳机，把注意力放在周围，而不是自己身上。", "optional": False},
    {"id": "p1-cbt", "phase": 1, "domain": "mind", "skill": "cbt", "title": "焦虑五问写 5 分钟", "detail": "写下：焦虑了吗？为什么？最坏是什么？概率？能否接受？", "optional": False},
    {"id": "p1-three", "phase": 1, "domain": "mind", "skill": "exposure_micro", "title": "主动说三句短话", "detail": "例如食堂「谢谢」、便利店「微信支付」。不用聊天。", "optional": False},
    {"id": "p1-sleep", "phase": 1, "domain": "habit", "skill": "energy", "title": "23:00 左右睡、周末不补大觉", "detail": "起床尽量不要比工作日晚超过 1 小时。", "optional": False},
    {"id": "p1-meal", "phase": 1, "domain": "habit", "skill": "energy", "title": "三餐规律、七分饱、少油少甜", "detail": "胃恢复期：周末尽量复制工作日饮食。", "optional": False},
    {"id": "p1-weekend", "phase": 1, "domain": "habit", "skill": "weekend", "title": "周末防崩：上午散步+学习 40 分钟", "detail": "不要睡一天；下午可买菜做饭；少长时间躺刷。", "optional": True},
    # —— 阶段2 ——
    {"id": "p2-hi", "phase": 2, "domain": "mind", "skill": "exposure_micro", "title": "认识的人打招呼 ≥3", "detail": "「早」或「下午好」，打完继续走，不用停下来聊。", "optional": False},
    {"id": "p2-pace", "phase": 2, "domain": "mind", "skill": "exposure_pace", "title": "刻意放慢语速", "detail": "一句话说完，故意停一秒再继续。", "optional": False},
    {"id": "p2-pause", "phase": 2, "domain": "mind", "skill": "exposure_pace", "title": "允许卡壳两秒", "detail": "紧张时停两秒再继续，不必拼命补救。", "optional": False},
    {"id": "p2-10", "phase": 2, "domain": "mind", "skill": "exposure_talk", "title": "对一人说超过十字的话", "detail": "如「今天温度挺高」「最近工作挺忙吧」，说完可离开。", "optional": False},
    {"id": "p2-rum", "phase": 2, "domain": "mind", "skill": "rumination", "title": "反刍限时 5 分钟", "detail": "聊天结束后只允许回想 5 分钟，到点去做别的事。", "optional": False},
    {"id": "p2-cbt", "phase": 2, "domain": "mind", "skill": "cbt", "title": "焦虑五问", "detail": "继续每晚或焦虑时写五问。", "optional": False},
    {"id": "p2-walk", "phase": 2, "domain": "body", "skill": "energy", "title": "保持散步", "detail": "维持阶段1 的散步习惯。", "optional": False},
    # —— 阶段3 ——
    {"id": "p3-q", "phase": 3, "domain": "mind", "skill": "exposure_talk", "title": "一个开放式问题", "detail": "如「最近忙吗」「周末去哪」。问完认真听，不要连续追问轰炸。", "optional": False},
    {"id": "p3-follow", "phase": 3, "domain": "mind", "skill": "exposure_talk", "title": "好奇地追问一句", "detail": "对方说累 →「最近一直加班？」；说跑步 →「跑了多久？」", "optional": False},
    {"id": "p3-praise", "phase": 3, "domain": "mind", "skill": "social_warm", "title": "具体赞美一次", "detail": "夸衣服、字、PPT 等具体点，不必夸漂亮/优秀。", "optional": False},
    {"id": "p3-thanks", "phase": 3, "domain": "mind", "skill": "social_warm", "title": "认真说一次谢谢/辛苦了", "detail": "把「不好意思」换成清晰的感谢。", "optional": False},
    {"id": "p3-rum", "phase": 3, "domain": "mind", "skill": "rumination", "title": "反刍限时", "detail": "继续 5 分钟规则。", "optional": False},
    {"id": "p3-cbt", "phase": 3, "domain": "mind", "skill": "cbt", "title": "焦虑五问", "detail": "焦虑明显时写一遍。", "optional": False},
    # —— 阶段4 ——
    {"id": "p4-cold", "phase": 4, "domain": "mind", "skill": "exposure_stretch", "title": "故意允许一次冷场", "detail": "说完没话就没话，不拼命救场。", "optional": False},
    {"id": "p4-2min", "phase": 4, "domain": "mind", "skill": "exposure_stretch", "title": "与熟人聊两分钟", "detail": "到点可以自然结束，不追求聊很久。", "optional": False},
    {"id": "p4-work", "phase": 4, "domain": "mind", "skill": "exposure_stretch", "title": "工作/生活场景对女生说一句话", "detail": "如「这个文件放哪」「这里有人吗」。不是搭讪，完成即可。", "optional": True},
    {"id": "p4-rum", "phase": 4, "domain": "mind", "skill": "rumination", "title": "反刍限时", "detail": "严格执行 5 分钟刹车。", "optional": False},
    {"id": "p4-cbt", "phase": 4, "domain": "mind", "skill": "cbt", "title": "焦虑五问", "detail": "挑战日后若焦虑升高，写五问。", "optional": False},
    {"id": "p4-weekend", "phase": 4, "domain": "habit", "skill": "weekend", "title": "周末保持节奏", "detail": "散步 + 短学习 + 规律饮食，避免整日躺刷。", "optional": True},
]


def _loads(raw: str | None, default):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


def _clamp(n: int | None, lo: int, hi: int, default: int = 0) -> int:
    if n is None:
        return default
    try:
        v = int(n)
    except (TypeError, ValueError):
        return default
    if v == 0:
        return 0
    return max(lo, min(hi, v))


def _parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def ensure_user_state(db: Session, user: AppUser) -> HealthUserState:
    st = db.get(HealthUserState, user.id)
    if st:
        return st
    st = HealthUserState(user_id=user.id, program_start_date=today_str())
    db.add(st)
    db.commit()
    db.refresh(st)
    return st


def reset_program(db: Session, user: AppUser) -> HealthUserState:
    st = ensure_user_state(db, user)
    st.program_start_date = today_str()
    st.updated_at = now()
    db.commit()
    db.refresh(st)
    return st


def _week_index(start: str, on_date: str) -> int:
    """1-based week index since program start; min 1."""
    try:
        d0 = _parse_date(start).date()
        d1 = _parse_date(on_date).date()
    except ValueError:
        return 1
    days = max(0, (d1 - d0).days)
    return days // 7 + 1


def _phase_for_week(week: int) -> dict:
    for p in PHASES:
        if p["weekStart"] <= week <= p["weekEnd"]:
            return p
    if week < 1:
        return PHASES[0]
    return PHASES[-1]  # 超过 8 周停留在阶段4


def list_phases() -> list[HealthPhaseOut]:
    return [HealthPhaseOut(**p) for p in PHASES]


def tasks_for_phase(phase: int) -> list[HealthTaskOut]:
    rows = [t for t in TASKS if t["phase"] == phase]
    return [
        HealthTaskOut(
            id=t["id"],
            phase=t["phase"],
            domain=t["domain"],
            skill=t["skill"],
            skillLabel=SKILL_LABELS.get(t["skill"], t["skill"]),
            title=t["title"],
            detail=t["detail"],
            optional=bool(t.get("optional")),
        )
        for t in rows
    ]


def _meal_slot(raw: dict | None) -> HealthMealSlotOut:
    d = raw if isinstance(raw, dict) else {}
    score = int(d.get("score") or 0)
    if score < 0:
        score = 0
    if score > 5:
        score = 5
    return HealthMealSlotOut(
        eaten=bool(d.get("eaten")),
        items=str(d.get("items") or ""),
        light=bool(d.get("light")),
        time=str(d.get("time") or ""),
        score=score,
        feel=str(d.get("feel") or "").strip()[:500],
    )


def _parse_meals(raw) -> HealthMealsOut:
    d = raw if isinstance(raw, dict) else {}
    return HealthMealsOut(
        breakfast=_meal_slot(d.get("breakfast")),
        lunch=_meal_slot(d.get("lunch")),
        dinner=_meal_slot(d.get("dinner")),
        snack=_meal_slot(d.get("snack")),
        waterCups=max(0, int(d.get("waterCups") or 0)),
        note=str(d.get("note") or ""),
    )


def _parse_stool(raw) -> HealthStoolOut:
    d = raw if isinstance(raw, dict) else {}
    return HealthStoolOut(
        times=max(0, int(d.get("times") or 0)),
        form=str(d.get("form") or ""),
        ease=str(d.get("ease") or ""),
        urineOk=bool(d.get("urineOk", True)),
        note=str(d.get("note") or ""),
    )


def assess_body_day(
    *,
    meals: HealthMealsOut,
    stool: HealthStoolOut,
    stomach: int = 0,
    dampness: int = 0,
    skin: int = 0,
    meals_regular: bool = False,
    meals_light: bool = False,
) -> str:
    """根据饮食/排便/主观身体分给出一句非医疗建议式复盘（非诊断）。"""
    tips: list[str] = []
    main_meals = [meals.breakfast, meals.lunch, meals.dinner]
    eaten_n = sum(1 for m in main_meals if m.eaten)
    light_n = sum(1 for m in main_meals if m.eaten and m.light)

    if eaten_n == 0 and stool.times == 0 and not (stomach or dampness or skin):
        return "今日饮食与排便尚未记录。晚间复盘前可先勾选三餐与大便情况，便于评估节律。"

    if eaten_n < 3:
        tips.append(f"正餐记录 {eaten_n}/3，节律偏碎，尽量固定三餐时间。")
    elif meals_regular or eaten_n == 3:
        tips.append("三餐有记录，节律尚可。")

    if eaten_n and light_n < max(1, eaten_n - 1) and not meals_light:
        tips.append("油腻/过饱迹象偏多时，胃与皮肤更容易闹脾气。")
    elif light_n >= 2 or meals_light:
        tips.append("清淡选择不错，有利于胃与湿气感。")

    scored = [m for m in main_meals if m.eaten and m.score > 0]
    if scored:
        low = [m for m in scored if m.score <= 2]
        avg = sum(m.score for m in scored) / len(scored)
        if low:
            tips.append(f"有 {len(low)} 餐餐后自评偏低，留意饱胀、困倦或油腻诱因。")
        elif avg >= 4:
            tips.append("餐后自评整体不错，可保持当前节奏。")
        else:
            tips.append("餐后感受中等，可对照清淡与饮水再微调。")

    if meals.waterCups and meals.waterCups < 4:
        tips.append("饮水偏少，可慢慢加到 6～8 杯。")
    elif meals.waterCups >= 6:
        tips.append("饮水够量。")

    if stool.times == 0 and (eaten_n >= 2 or stool.form or stool.ease):
        tips.append("今日未排便或未记次数，留意是否腹胀、胃口差。")
    elif stool.times >= 3 or (stool.form in ("loose", "soft") and stool.ease == "urgent"):
        tips.append("排便偏稀/偏频，少油少刺激，观察一天。")
    elif stool.form == "hard" or stool.ease == "hard":
        tips.append("便干或费力，可加膳食纤维与走动，忌硬扛。")
    elif stool.times in (1, 2) and (stool.form in ("", "normal") or stool.ease in ("", "smooth")):
        tips.append("排便大体正常。")

    if stomach and stomach <= 4:
        tips.append("胃部不适偏明显，今晚宜温软、早停食。")
    elif stomach >= 7:
        tips.append("胃部主观感较好。")

    if dampness and dampness >= 7:
        tips.append("湿气感偏高，少甜少冰，保持散步。")
    if skin and skin >= 7:
        tips.append("皮肤不适偏重，记录诱因（熬夜/辛辣）比急着用药更重要。")

    if not tips:
        return "记录已保存。身体主观分与饮食排便暂无明显冲突信号。"
    return "；".join(tips)


def _daily_out(row: HealthDailyLog) -> HealthDailyLogOut:
    cbt_raw = _loads(row.cbt_json, {}) or {}
    rum_raw = _loads(row.rumination_json, {}) or {}
    rev_raw = _loads(row.review_json, {}) or {}
    tasks = _loads(row.tasks_done_json, [])
    if not isinstance(tasks, list):
        tasks = []
    meals = _parse_meals(_loads(getattr(row, "meals_json", None) or "{}", {}))
    stool = _parse_stool(_loads(getattr(row, "stool_json", None) or "{}", {}))
    assessment = assess_body_day(
        meals=meals,
        stool=stool,
        stomach=row.stomach or 0,
        dampness=row.dampness or 0,
        skin=row.skin or 0,
        meals_regular=bool(row.meals_regular),
        meals_light=bool(row.meals_light),
    )
    stored_assess = str(rev_raw.get("bodyAssessment") or "")
    return HealthDailyLogOut(
        id=row.id,
        logDate=row.log_date,
        mood=row.mood or 0,
        sleepQuality=row.sleep_quality or 0,
        sleepBefore23=bool(row.sleep_before_23),
        mealsRegular=bool(row.meals_regular),
        mealsLight=bool(row.meals_light),
        weekendLieFlat=bool(row.weekend_lie_flat),
        habitNote=row.habit_note or "",
        meals=meals,
        stool=stool,
        stomach=row.stomach or 0,
        dampness=row.dampness or 0,
        skin=row.skin or 0,
        skinItch=bool(row.skin_itch),
        skinFlare=bool(row.skin_flare),
        walkMin=row.walk_min or 0,
        bodyNote=row.body_note or "",
        anxiety=row.anxiety or 0,
        energy=row.energy or 0,
        socialCount=row.social_count or 0,
        studyMin=row.study_min or 0,
        tasksDone=[str(x) for x in tasks],
        cbt=HealthCbtOut(
            anxious=str(cbt_raw.get("anxious") or ""),
            why=str(cbt_raw.get("why") or ""),
            worst=str(cbt_raw.get("worst") or ""),
            probability=str(cbt_raw.get("probability") or ""),
            acceptable=str(cbt_raw.get("acceptable") or ""),
            nextStep=str(cbt_raw.get("nextStep") or ""),
        ),
        rumination=HealthRuminationOut(
            triggered=bool(rum_raw.get("triggered")),
            stoppedInTime=bool(rum_raw.get("stoppedInTime")),
            note=str(rum_raw.get("note") or ""),
        ),
        review=HealthReviewOut(
            bestThing=str(rev_raw.get("bestThing") or ""),
            tomorrowGoal=str(rev_raw.get("tomorrowGoal") or ""),
            bodyAssessment=stored_assess or assessment,
        ),
        bodyAssessment=assessment,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )


def get_daily(db: Session, user: AppUser, date: str | None = None) -> HealthDailyLogOut | None:
    d = date or today_str()
    row = (
        db.query(HealthDailyLog)
        .filter(HealthDailyLog.user_id == user.id, HealthDailyLog.log_date == d)
        .first()
    )
    return _daily_out(row) if row else None


def list_daily_range(db: Session, user: AppUser, start: str, end: str) -> list[HealthDailyLogOut]:
    rows = (
        db.query(HealthDailyLog)
        .filter(
            HealthDailyLog.user_id == user.id,
            HealthDailyLog.log_date >= start,
            HealthDailyLog.log_date <= end,
        )
        .order_by(HealthDailyLog.log_date.asc())
        .all()
    )
    return [_daily_out(r) for r in rows]


def upsert_daily(db: Session, user: AppUser, body: HealthDailyLogUpsert) -> HealthDailyLogOut:
    ensure_user_state(db, user)
    d = body.logDate or today_str()
    row = (
        db.query(HealthDailyLog)
        .filter(HealthDailyLog.user_id == user.id, HealthDailyLog.log_date == d)
        .first()
    )
    if not row:
        row = HealthDailyLog(id=gen_id("hdl"), user_id=user.id, log_date=d)
        db.add(row)

    data = body.model_dump(exclude_unset=True)
    if "mood" in data:
        row.mood = _clamp(data["mood"], 1, 10)
    if "sleepQuality" in data:
        row.sleep_quality = _clamp(data["sleepQuality"], 1, 5)
    if "sleepBefore23" in data:
        row.sleep_before_23 = bool(data["sleepBefore23"])
    if "mealsRegular" in data:
        row.meals_regular = bool(data["mealsRegular"])
    if "mealsLight" in data:
        row.meals_light = bool(data["mealsLight"])
    if "weekendLieFlat" in data:
        row.weekend_lie_flat = bool(data["weekendLieFlat"])
    if "habitNote" in data:
        row.habit_note = str(data["habitNote"] or "")
    if "meals" in data and data["meals"] is not None:
        m = data["meals"] if isinstance(data["meals"], dict) else data["meals"].model_dump()
        row.meals_json = json.dumps(m, ensure_ascii=False)
        # 由详细清单推导简易勾选，便于旧视图兼容
        slots = [m.get("breakfast") or {}, m.get("lunch") or {}, m.get("dinner") or {}]
        eaten = [s for s in slots if isinstance(s, dict) and s.get("eaten")]
        if len(eaten) >= 3:
            row.meals_regular = True
        if sum(1 for s in eaten if s.get("light")) >= 2:
            row.meals_light = True
    if "stool" in data and data["stool"] is not None:
        s = data["stool"] if isinstance(data["stool"], dict) else data["stool"].model_dump()
        row.stool_json = json.dumps(s, ensure_ascii=False)
    if "stomach" in data:
        row.stomach = _clamp(data["stomach"], 1, 10)
    if "dampness" in data:
        row.dampness = _clamp(data["dampness"], 1, 10)
    if "skin" in data:
        row.skin = _clamp(data["skin"], 1, 10)
    if "skinItch" in data:
        row.skin_itch = bool(data["skinItch"])
    if "skinFlare" in data:
        row.skin_flare = bool(data["skinFlare"])
    if "walkMin" in data:
        row.walk_min = max(0, int(data["walkMin"] or 0))
    if "bodyNote" in data:
        row.body_note = str(data["bodyNote"] or "")
    if "anxiety" in data:
        row.anxiety = _clamp(data["anxiety"], 1, 10)
    if "energy" in data:
        row.energy = _clamp(data["energy"], 1, 10)
    if "socialCount" in data:
        row.social_count = max(0, int(data["socialCount"] or 0))
    if "studyMin" in data:
        row.study_min = max(0, int(data["studyMin"] or 0))
    if "tasksDone" in data and data["tasksDone"] is not None:
        row.tasks_done_json = json.dumps(list(data["tasksDone"]), ensure_ascii=False)
    if "cbt" in data and data["cbt"] is not None:
        c = data["cbt"] if isinstance(data["cbt"], dict) else data["cbt"].model_dump()
        row.cbt_json = json.dumps(c, ensure_ascii=False)
    if "rumination" in data and data["rumination"] is not None:
        r = data["rumination"] if isinstance(data["rumination"], dict) else data["rumination"].model_dump()
        row.rumination_json = json.dumps(r, ensure_ascii=False)
    if "review" in data and data["review"] is not None:
        v = data["review"] if isinstance(data["review"], dict) else data["review"].model_dump()
        # 保存复盘时写入最新身体评估
        meals = _parse_meals(_loads(getattr(row, "meals_json", None) or "{}", {}))
        stool = _parse_stool(_loads(getattr(row, "stool_json", None) or "{}", {}))
        v["bodyAssessment"] = assess_body_day(
            meals=meals,
            stool=stool,
            stomach=row.stomach or 0,
            dampness=row.dampness or 0,
            skin=row.skin or 0,
            meals_regular=bool(row.meals_regular),
            meals_light=bool(row.meals_light),
        )
        row.review_json = json.dumps(v, ensure_ascii=False)

    row.updated_at = now()
    db.commit()
    db.refresh(row)
    return _daily_out(row)


def _avg(vals: list[int]) -> float:
    nums = [v for v in vals if v and v > 0]
    if not nums:
        return 0.0
    return round(sum(nums) / len(nums), 1)


def get_overview(db: Session, user: AppUser) -> HealthOverviewOut:
    st = ensure_user_state(db, user)
    today = today_str()
    week = _week_index(st.program_start_date or today, today)
    phase = _phase_for_week(week)
    tasks = tasks_for_phase(phase["phase"])

    # 本周日期
    d = now().date()
    monday = d - timedelta(days=d.weekday())
    week_dates = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    logs = list_daily_range(db, user, week_dates[0], week_dates[-1])
    by_date = {x.logDate: x for x in logs}

    def pts(getter) -> list[HealthWeekPoint]:
        labels = ["一", "二", "三", "四", "五", "六", "日"]
        out: list[HealthWeekPoint] = []
        for i, date in enumerate(week_dates):
            log = by_date.get(date)
            out.append(
                HealthWeekPoint(
                    date=date,
                    label=labels[i],
                    value=int(getter(log) or 0) if log else 0,
                    isToday=date == today,
                )
            )
        return out

    today_log = by_date.get(today)
    checked = today_log is not None and (
        today_log.mood > 0 or today_log.energy > 0 or today_log.stomach > 0 or bool(today_log.tasksDone)
    )

    # 连续打卡：从今天往前
    streak = 0
    cur = d
    while True:
        key = cur.strftime("%Y-%m-%d")
        row = (
            db.query(HealthDailyLog)
            .filter(HealthDailyLog.user_id == user.id, HealthDailyLog.log_date == key)
            .first()
        )
        if not row:
            break
        if not (row.mood or row.energy or row.stomach or _loads(row.tasks_done_json, [])):
            break
        streak += 1
        cur -= timedelta(days=1)
        if streak > 60:
            break

    week_logs = list(by_date.values())
    exposure_done = 0
    cbt_days = 0
    for lg in week_logs:
        for tid in lg.tasksDone:
            t = next((x for x in TASKS if x["id"] == tid), None)
            if t and str(t["skill"]).startswith("exposure"):
                exposure_done += 1
        if any(
            [
                lg.cbt.anxious,
                lg.cbt.why,
                lg.cbt.worst,
                lg.cbt.probability,
                lg.cbt.acceptable,
            ]
        ):
            cbt_days += 1

    low_energy_hint = False
    energies = [lg.energy for lg in week_logs if lg.energy > 0]
    if len(energies) >= 3 and _avg(energies) <= 3:
        low_energy_hint = True

    tips: list[str] = []
    if today_log and (not today_log.mealsRegular) and (today_log.skin >= 6 or today_log.dampness >= 6):
        tips.append("今日饮食不够规律，同时湿气/皮肤评分偏高，可回顾三餐与睡眠。")
    if today_log and today_log.skinFlare and today_log.anxiety >= 7:
        tips.append("焦虑较高且皮肤有加重，可先做反刍刹车与规律作息，症状持续请就医。")

    return HealthOverviewOut(
        programStartDate=st.program_start_date or today,
        weekIndex=min(week, 8) if week <= 12 else week,
        phase=HealthPhaseOut(**phase),
        todayCheckedIn=checked,
        streakDays=streak,
        todayTasks=tasks,
        todayLog=today_log,
        weekMood=pts(lambda x: x.mood),
        weekEnergy=pts(lambda x: x.energy),
        weekStomach=pts(lambda x: x.stomach),
        weekSkin=pts(lambda x: x.skin),
        weekDampness=pts(lambda x: x.dampness),
        weekMindStats={
            "exposureTaskCompletions": exposure_done,
            "cbtDays": cbt_days,
            "avgAnxiety": _avg([lg.anxiety for lg in week_logs]),
            "avgEnergy": _avg([lg.energy for lg in week_logs]),
            "socialCountSum": sum(lg.socialCount for lg in week_logs),
        },
        lowEnergyHint=low_energy_hint,
        softTips=tips,
        privateFocus=st.private_focus or "",
        disclaimer="本模块仅供自我观察与习惯管理，不能替代医疗或心理咨询。湿气/皮肤等记录为个人感受，非诊断。若持续两周情绪低落、兴趣丧失，或皮肤/消化明显加重，请及时就医或寻求专业帮助。",
    )


def update_private_focus(db: Session, user: AppUser, text: str) -> str:
    st = ensure_user_state(db, user)
    st.private_focus = (text or "")[:2000]
    st.updated_at = now()
    db.commit()
    return st.private_focus
