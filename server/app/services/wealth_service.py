"""财富 / 投资大脑 · 资产快照 + 原则 + 日志 + 复盘"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import AppUser, WealthJournal, WealthPrinciple, WealthSnapshot, gen_id
from app.schemas import (
    WEALTH_ASSET_LABELS,
    WEALTH_BUY_REASON_PRESETS,
    WEALTH_EMOTIONS,
    WEALTH_LAYER_LABELS,
    WEALTH_SELL_REASON_PRESETS,
    WealthAllocationItem,
    WealthEmotionStat,
    WealthHubOut,
    WealthJournalCreate,
    WealthJournalOut,
    WealthJournalUpdate,
    WealthPrincipleCreate,
    WealthPrincipleOut,
    WealthPrincipleUpdate,
    WealthReasonStat,
    WealthReviewOut,
    WealthSnapshotCreate,
    WealthSnapshotOut,
    WealthSnapshotUpdate,
)
from app.timezone import today as today_str

DEFAULT_PRINCIPLES: list[tuple[int, str, str, int]] = [
    (1, "不融资", "不加杠杆、不用信用账户", 10),
    (1, "保留现金底仓", "永远保留 20% 以上现金", 20),
    (2, "不追涨停", "不碰 ST，不买连续暴涨与纯消息股", 10),
    (3, "买入四选三", "行业趋势 / 基本面 / 资金 / 技术，至少满足三项", 10),
    (4, "止损必卖", "跌破止损或逻辑失效必须卖；盈利 20% 可减仓", 10),
]


def _yuan_to_cents(amount: float | None, amount_cents: int | None) -> int:
    if amount_cents is not None:
        return max(0, int(amount_cents))
    if amount is not None:
        return max(0, int(round(float(amount) * 100)))
    return 0


def _cents_to_yuan(cents: int) -> float:
    return round(int(cents or 0) / 100, 2)


def _loads_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()][:20]
    except Exception:
        pass
    return []


def _dumps_list(items: list[str] | None) -> str:
    clean = [str(x).strip() for x in (items or []) if str(x).strip()]
    seen: set[str] = set()
    out: list[str] = []
    for t in clean:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return json.dumps(out[:20], ensure_ascii=False)


def _snapshot_out(s: WealthSnapshot) -> WealthSnapshotOut:
    parts = {
        "cash": int(s.cash_cents or 0),
        "deposit": int(s.deposit_cents or 0),
        "fund": int(s.fund_cents or 0),
        "stock": int(s.stock_cents or 0),
        "other": int(s.other_cents or 0),
    }
    total = sum(parts.values())
    allocations = []
    for key, cents in parts.items():
        pct = round(cents * 100 / total, 1) if total > 0 else 0.0
        allocations.append(
            WealthAllocationItem(
                key=key,
                label=WEALTH_ASSET_LABELS.get(key, key),
                amountCents=cents,
                amount=_cents_to_yuan(cents),
                percent=pct,
            )
        )
    return WealthSnapshotOut(
        id=s.id,
        snapDate=s.snap_date,
        cashCents=parts["cash"],
        depositCents=parts["deposit"],
        fundCents=parts["fund"],
        stockCents=parts["stock"],
        otherCents=parts["other"],
        cash=_cents_to_yuan(parts["cash"]),
        deposit=_cents_to_yuan(parts["deposit"]),
        fund=_cents_to_yuan(parts["fund"]),
        stock=_cents_to_yuan(parts["stock"]),
        other=_cents_to_yuan(parts["other"]),
        totalCents=total,
        total=_cents_to_yuan(total),
        allocations=allocations,
        note=s.note or "",
        createdAt=s.created_at,
        updatedAt=s.updated_at,
    )


def _principle_out(p: WealthPrinciple) -> WealthPrincipleOut:
    return WealthPrincipleOut(
        id=p.id,
        layer=int(p.layer or 1),
        layerLabel=WEALTH_LAYER_LABELS.get(int(p.layer or 1), ""),
        title=p.title or "",
        content=p.content or "",
        sortOrder=p.sort_order,
        isEnabled=bool(p.is_enabled),
        createdAt=p.created_at,
        updatedAt=p.updated_at,
    )


def _journal_out(j: WealthJournal) -> WealthJournalOut:
    return WealthJournalOut(
        id=j.id,
        side=j.side or "buy",
        symbol=j.symbol or "",
        name=j.name or "",
        tradeDate=j.trade_date,
        price=float(j.price or 0),
        positionPct=float(j.position_pct or 0),
        reasons=_loads_list(j.reasons_json),
        reasonNote=j.reason_note or "",
        riskNote=j.risk_note or "",
        stopLoss=float(j.stop_loss or 0),
        targetPrice=float(j.target_price or 0),
        emotion=j.emotion or "ok",
        confidence=int(j.confidence or 3),
        sleepHours=float(j.sleep_hours or 0),
        workStress=int(j.work_stress or 0),
        hadQuarrel=bool(j.had_quarrel),
        followedPlan=j.followed_plan,
        checklistOk=bool(j.checklist_ok),
        resultTag=j.result_tag or "",
        note=j.note or "",
        createdAt=j.created_at,
        updatedAt=j.updated_at,
    )


def ensure_default_principles(db: Session, user: AppUser) -> None:
    count = db.query(WealthPrinciple).filter(WealthPrinciple.user_id == user.id).count()
    if count > 0:
        return
    for layer, title, content, sort in DEFAULT_PRINCIPLES:
        db.add(
            WealthPrinciple(
                id=gen_id("wpr"),
                user_id=user.id,
                layer=layer,
                title=title,
                content=content,
                sort_order=sort,
                is_enabled=True,
            )
        )
    db.commit()


def get_hub(db: Session, user: AppUser) -> WealthHubOut:
    ensure_default_principles(db, user)
    latest = (
        db.query(WealthSnapshot)
        .filter(WealthSnapshot.user_id == user.id)
        .order_by(WealthSnapshot.snap_date.desc(), WealthSnapshot.updated_at.desc())
        .first()
    )
    principle_count = (
        db.query(WealthPrinciple)
        .filter(WealthPrinciple.user_id == user.id, WealthPrinciple.is_enabled.is_(True))
        .count()
    )
    journal_count = db.query(WealthJournal).filter(WealthJournal.user_id == user.id).count()
    today = today_str()
    # 本周一
    d = datetime.strptime(today, "%Y-%m-%d").date()
    week_start = (d - timedelta(days=d.weekday())).isoformat()
    week_rows = (
        db.query(WealthJournal)
        .filter(WealthJournal.user_id == user.id, WealthJournal.trade_date >= week_start)
        .all()
    )
    return WealthHubOut(
        latestSnapshot=_snapshot_out(latest) if latest else None,
        principleCount=principle_count,
        journalCount=journal_count,
        weekTradeCount=len(week_rows),
        weekWinCount=sum(1 for j in week_rows if j.result_tag == "win"),
        weekLossCount=sum(1 for j in week_rows if j.result_tag == "loss"),
    )


# ---- snapshots ----

def list_snapshots(db: Session, user: AppUser, limit: int = 30) -> list[WealthSnapshotOut]:
    rows = (
        db.query(WealthSnapshot)
        .filter(WealthSnapshot.user_id == user.id)
        .order_by(WealthSnapshot.snap_date.desc(), WealthSnapshot.updated_at.desc())
        .limit(max(1, min(limit, 100)))
        .all()
    )
    return [_snapshot_out(r) for r in rows]


def get_snapshot(db: Session, user: AppUser, snap_id: str) -> WealthSnapshotOut | None:
    s = db.get(WealthSnapshot, snap_id)
    if not s or s.user_id != user.id:
        return None
    return _snapshot_out(s)


def create_snapshot(db: Session, user: AppUser, body: WealthSnapshotCreate) -> WealthSnapshotOut:
    date = (body.snapDate or today_str()).strip()
    s = WealthSnapshot(
        id=gen_id("wsp"),
        user_id=user.id,
        snap_date=date,
        cash_cents=_yuan_to_cents(body.cash, body.cashCents),
        deposit_cents=_yuan_to_cents(body.deposit, body.depositCents),
        fund_cents=_yuan_to_cents(body.fund, body.fundCents),
        stock_cents=_yuan_to_cents(body.stock, body.stockCents),
        other_cents=_yuan_to_cents(body.other, body.otherCents),
        note=(body.note or "").strip(),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return _snapshot_out(s)


def update_snapshot(
    db: Session, user: AppUser, snap_id: str, body: WealthSnapshotUpdate
) -> WealthSnapshotOut | None:
    s = db.get(WealthSnapshot, snap_id)
    if not s or s.user_id != user.id:
        return None
    data = body.model_dump(exclude_unset=True)
    if "snapDate" in data and data["snapDate"]:
        s.snap_date = str(data["snapDate"]).strip()
    field_map = [
        ("cash", "cashCents", "cash_cents"),
        ("deposit", "depositCents", "deposit_cents"),
        ("fund", "fundCents", "fund_cents"),
        ("stock", "stockCents", "stock_cents"),
        ("other", "otherCents", "other_cents"),
    ]
    for yuan_k, cents_k, col in field_map:
        if yuan_k in data or cents_k in data:
            setattr(
                s,
                col,
                _yuan_to_cents(data.get(yuan_k), data.get(cents_k)),
            )
    if "note" in data and data["note"] is not None:
        s.note = str(data["note"]).strip()
    db.commit()
    db.refresh(s)
    return _snapshot_out(s)


def delete_snapshot(db: Session, user: AppUser, snap_id: str) -> bool:
    s = db.get(WealthSnapshot, snap_id)
    if not s or s.user_id != user.id:
        return False
    db.delete(s)
    db.commit()
    return True


# ---- principles ----

def list_principles(db: Session, user: AppUser, enabled_only: bool = False) -> list[WealthPrincipleOut]:
    ensure_default_principles(db, user)
    q = db.query(WealthPrinciple).filter(WealthPrinciple.user_id == user.id)
    if enabled_only:
        q = q.filter(WealthPrinciple.is_enabled.is_(True))
    rows = q.order_by(WealthPrinciple.layer, WealthPrinciple.sort_order, WealthPrinciple.created_at).all()
    return [_principle_out(r) for r in rows]


def create_principle(db: Session, user: AppUser, body: WealthPrincipleCreate) -> WealthPrincipleOut:
    title = (body.title or "").strip()
    if not title:
        raise ValueError("请填写原则标题")
    layer = int(body.layer or 1)
    if layer not in WEALTH_LAYER_LABELS:
        raise ValueError("层级须为 1～4")
    p = WealthPrinciple(
        id=gen_id("wpr"),
        user_id=user.id,
        layer=layer,
        title=title,
        content=(body.content or "").strip(),
        sort_order=body.sortOrder,
        is_enabled=body.isEnabled,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _principle_out(p)


def update_principle(
    db: Session, user: AppUser, principle_id: str, body: WealthPrincipleUpdate
) -> WealthPrincipleOut | None:
    p = db.get(WealthPrinciple, principle_id)
    if not p or p.user_id != user.id:
        return None
    data = body.model_dump(exclude_unset=True)
    if "layer" in data and data["layer"] is not None:
        layer = int(data["layer"])
        if layer not in WEALTH_LAYER_LABELS:
            raise ValueError("层级须为 1～4")
        p.layer = layer
    if "title" in data and data["title"] is not None:
        title = str(data["title"]).strip()
        if not title:
            raise ValueError("标题不能为空")
        p.title = title
    if "content" in data and data["content"] is not None:
        p.content = str(data["content"]).strip()
    if "sortOrder" in data and data["sortOrder"] is not None:
        p.sort_order = int(data["sortOrder"])
    if "isEnabled" in data and data["isEnabled"] is not None:
        p.is_enabled = bool(data["isEnabled"])
    db.commit()
    db.refresh(p)
    return _principle_out(p)


def delete_principle(db: Session, user: AppUser, principle_id: str) -> bool:
    p = db.get(WealthPrinciple, principle_id)
    if not p or p.user_id != user.id:
        return False
    db.delete(p)
    db.commit()
    return True


# ---- journals ----

def list_journals(
    db: Session, user: AppUser, side: str | None = None, limit: int = 50
) -> list[WealthJournalOut]:
    q = db.query(WealthJournal).filter(WealthJournal.user_id == user.id)
    if side in ("buy", "sell"):
        q = q.filter(WealthJournal.side == side)
    rows = q.order_by(WealthJournal.trade_date.desc(), WealthJournal.created_at.desc()).limit(
        max(1, min(limit, 200))
    ).all()
    return [_journal_out(r) for r in rows]


def get_journal(db: Session, user: AppUser, journal_id: str) -> WealthJournalOut | None:
    j = db.get(WealthJournal, journal_id)
    if not j or j.user_id != user.id:
        return None
    return _journal_out(j)


def create_journal(db: Session, user: AppUser, body: WealthJournalCreate) -> WealthJournalOut:
    side = (body.side or "buy").strip()
    if side not in ("buy", "sell"):
        raise ValueError("方向须为 buy 或 sell")
    name = (body.name or body.symbol or "").strip()
    if not name:
        raise ValueError("请填写标的名称")
    if side == "buy" and not body.checklistOk:
        raise ValueError("买入前请完成冷静期确认清单")
    emotion = (body.emotion or "ok").strip()
    if emotion not in WEALTH_EMOTIONS:
        emotion = "ok"
    conf = max(1, min(5, int(body.confidence or 3)))
    j = WealthJournal(
        id=gen_id("wjn"),
        user_id=user.id,
        side=side,
        symbol=(body.symbol or "").strip()[:32],
        name=name[:64],
        trade_date=(body.tradeDate or today_str()).strip(),
        price=float(body.price or 0),
        position_pct=float(body.positionPct or 0),
        reasons_json=_dumps_list(body.reasons),
        reason_note=(body.reasonNote or "").strip(),
        risk_note=(body.riskNote or "").strip(),
        stop_loss=float(body.stopLoss or 0),
        target_price=float(body.targetPrice or 0),
        emotion=emotion,
        confidence=conf,
        sleep_hours=float(body.sleepHours or 0),
        work_stress=max(0, min(5, int(body.workStress or 0))),
        had_quarrel=bool(body.hadQuarrel),
        followed_plan=body.followedPlan,
        checklist_ok=bool(body.checklistOk),
        result_tag=(body.resultTag or "").strip(),
        note=(body.note or "").strip(),
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return _journal_out(j)


def update_journal(
    db: Session, user: AppUser, journal_id: str, body: WealthJournalUpdate
) -> WealthJournalOut | None:
    j = db.get(WealthJournal, journal_id)
    if not j or j.user_id != user.id:
        return None
    data = body.model_dump(exclude_unset=True)
    if "side" in data and data["side"] is not None:
        side = str(data["side"]).strip()
        if side not in ("buy", "sell"):
            raise ValueError("方向须为 buy 或 sell")
        j.side = side
    if "symbol" in data and data["symbol"] is not None:
        j.symbol = str(data["symbol"]).strip()[:32]
    if "name" in data and data["name"] is not None:
        name = str(data["name"]).strip()
        if not name:
            raise ValueError("名称不能为空")
        j.name = name[:64]
    if "tradeDate" in data and data["tradeDate"]:
        j.trade_date = str(data["tradeDate"]).strip()
    for field, attr in [
        ("price", "price"),
        ("positionPct", "position_pct"),
        ("stopLoss", "stop_loss"),
        ("targetPrice", "target_price"),
        ("sleepHours", "sleep_hours"),
    ]:
        if field in data and data[field] is not None:
            setattr(j, attr, float(data[field]))
    if "reasons" in data and data["reasons"] is not None:
        j.reasons_json = _dumps_list(list(data["reasons"] or []))
    if "reasonNote" in data and data["reasonNote"] is not None:
        j.reason_note = str(data["reasonNote"]).strip()
    if "riskNote" in data and data["riskNote"] is not None:
        j.risk_note = str(data["riskNote"]).strip()
    if "emotion" in data and data["emotion"] is not None:
        emotion = str(data["emotion"]).strip()
        j.emotion = emotion if emotion in WEALTH_EMOTIONS else j.emotion
    if "confidence" in data and data["confidence"] is not None:
        j.confidence = max(1, min(5, int(data["confidence"])))
    if "workStress" in data and data["workStress"] is not None:
        j.work_stress = max(0, min(5, int(data["workStress"])))
    if "hadQuarrel" in data and data["hadQuarrel"] is not None:
        j.had_quarrel = bool(data["hadQuarrel"])
    if "followedPlan" in data:
        j.followed_plan = data["followedPlan"]
    if "checklistOk" in data and data["checklistOk"] is not None:
        j.checklist_ok = bool(data["checklistOk"])
    if "resultTag" in data and data["resultTag"] is not None:
        j.result_tag = str(data["resultTag"]).strip()
    if "note" in data and data["note"] is not None:
        j.note = str(data["note"]).strip()
    db.commit()
    db.refresh(j)
    return _journal_out(j)


def delete_journal(db: Session, user: AppUser, journal_id: str) -> bool:
    j = db.get(WealthJournal, journal_id)
    if not j or j.user_id != user.id:
        return False
    db.delete(j)
    db.commit()
    return True


# ---- review ----

def get_review(db: Session, user: AppUser, week_start: str | None = None) -> WealthReviewOut:
    today = today_str()
    if week_start:
        start = week_start.strip()
    else:
        d = datetime.strptime(today, "%Y-%m-%d").date()
        start = (d - timedelta(days=d.weekday())).isoformat()
    start_d = datetime.strptime(start, "%Y-%m-%d").date()
    end = (start_d + timedelta(days=6)).isoformat()
    rows = (
        db.query(WealthJournal)
        .filter(
            WealthJournal.user_id == user.id,
            WealthJournal.trade_date >= start,
            WealthJournal.trade_date <= end,
        )
        .all()
    )
    win_reasons: Counter[str] = Counter()
    loss_reasons: Counter[str] = Counter()
    emotion_all: Counter[str] = Counter()
    emotion_loss: Counter[str] = Counter()
    for j in rows:
        reasons = _loads_list(j.reasons_json)
        emotion_all[j.emotion or "ok"] += 1
        if j.result_tag == "win":
            for r in reasons:
                win_reasons[r] += 1
        elif j.result_tag == "loss":
            emotion_loss[j.emotion or "ok"] += 1
            for r in reasons:
                loss_reasons[r] += 1
    return WealthReviewOut(
        weekStart=start,
        weekEnd=end,
        tradeCount=len(rows),
        buyCount=sum(1 for j in rows if j.side == "buy"),
        sellCount=sum(1 for j in rows if j.side == "sell"),
        winCount=sum(1 for j in rows if j.result_tag == "win"),
        lossCount=sum(1 for j in rows if j.result_tag == "loss"),
        followedPlanCount=sum(1 for j in rows if j.followed_plan is True),
        brokePlanCount=sum(1 for j in rows if j.followed_plan is False),
        topWinReasons=[WealthReasonStat(reason=k, count=v) for k, v in win_reasons.most_common(8)],
        topLossReasons=[WealthReasonStat(reason=k, count=v) for k, v in loss_reasons.most_common(8)],
        emotionStats=[
            WealthEmotionStat(emotion=k, count=v, lossCount=emotion_loss.get(k, 0))
            for k, v in emotion_all.most_common()
        ],
        buyReasonPresets=list(WEALTH_BUY_REASON_PRESETS),
        sellReasonPresets=list(WEALTH_SELL_REASON_PRESETS),
        layerLabels={str(k): v for k, v in WEALTH_LAYER_LABELS.items()},
    )
