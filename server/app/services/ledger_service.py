"""记账模块 · 日常支出 + 出借归还"""
from __future__ import annotations

import json
from calendar import monthrange

from sqlalchemy.orm import Session

from app.models import AppUser, LedgerExpense, LedgerLoan, LedgerRepayment, gen_id
from app.schemas import (
    LEDGER_EXPENSE_CATEGORIES,
    LEDGER_REPAY_METHODS,
    LedgerCategoryStat,
    LedgerCounterpartyOut,
    LedgerExpenseCreate,
    LedgerExpenseOut,
    LedgerExpenseUpdate,
    LedgerLoanCreate,
    LedgerLoanOut,
    LedgerLoanUpdate,
    LedgerOverviewOut,
    LedgerRepaymentCreate,
    LedgerRepaymentOut,
    LedgerRepaymentUpdate,
)
from app.timezone import today as today_str


def _loads_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x) for x in data if str(x).strip()]
    except Exception:
        pass
    return []


def _dumps_list(items: list[str] | None) -> str:
    clean = [str(x).strip() for x in (items or []) if str(x).strip()]
    return json.dumps(clean[:12], ensure_ascii=False)


def _yuan_to_cents(amount: float | None, amount_cents: int | None) -> int:
    if amount_cents is not None:
        return max(0, int(amount_cents))
    if amount is not None:
        return max(0, int(round(float(amount) * 100)))
    return 0


def _cents_to_yuan(cents: int) -> float:
    return round(int(cents or 0) / 100, 2)


def _expense_out(e: LedgerExpense) -> LedgerExpenseOut:
    return LedgerExpenseOut(
        id=e.id,
        amountCents=e.amount_cents,
        amount=_cents_to_yuan(e.amount_cents),
        occurDate=e.occur_date,
        category=e.category or "其他",
        note=e.note or "",
        images=_loads_list(e.images_json),
        createdAt=e.created_at,
        updatedAt=e.updated_at,
    )


def _repay_out(r: LedgerRepayment) -> LedgerRepaymentOut:
    return LedgerRepaymentOut(
        id=r.id,
        loanId=r.loan_id,
        amountCents=r.amount_cents,
        amount=_cents_to_yuan(r.amount_cents),
        repayDate=r.repay_date,
        method=r.method or "微信",
        note=r.note or "",
        images=_loads_list(r.voucher_images_json),
        createdAt=r.created_at,
        updatedAt=r.updated_at,
    )


def _loan_repaid_cents(db: Session, loan_id: str) -> int:
    rows = db.query(LedgerRepayment).filter(LedgerRepayment.loan_id == loan_id).all()
    return sum(int(r.amount_cents or 0) for r in rows)


def _sync_loan_status(db: Session, loan: LedgerLoan) -> int:
    repaid = _loan_repaid_cents(db, loan.id)
    remaining = max(0, int(loan.principal_cents or 0) - repaid)
    loan.status = "settled" if remaining <= 0 and int(loan.principal_cents or 0) > 0 else "open"
    return repaid


def _loan_out(db: Session, loan: LedgerLoan, with_repayments: bool = False) -> LedgerLoanOut:
    repaid = _sync_loan_status(db, loan)
    remaining = max(0, int(loan.principal_cents or 0) - repaid)
    reps: list[LedgerRepaymentOut] = []
    if with_repayments:
        rows = (
            db.query(LedgerRepayment)
            .filter(LedgerRepayment.loan_id == loan.id)
            .order_by(LedgerRepayment.repay_date.desc(), LedgerRepayment.created_at.desc())
            .all()
        )
        reps = [_repay_out(r) for r in rows]
    return LedgerLoanOut(
        id=loan.id,
        counterparty=loan.counterparty or "",
        principalCents=loan.principal_cents,
        principal=_cents_to_yuan(loan.principal_cents),
        repaidCents=repaid,
        repaid=_cents_to_yuan(repaid),
        remainingCents=remaining,
        remaining=_cents_to_yuan(remaining),
        lendDate=loan.lend_date,
        dueDate=loan.due_date or "",
        status=loan.status or "open",
        note=loan.note or "",
        images=_loads_list(loan.voucher_images_json),
        repayments=reps,
        createdAt=loan.created_at,
        updatedAt=loan.updated_at,
    )


def get_overview(db: Session, user: AppUser, month: str | None = None) -> LedgerOverviewOut:
    today = today_str()
    month = (month or today[:7]).strip()
    if len(month) != 7:
        month = today[:7]
    year, mon = int(month[:4]), int(month[5:7])
    last_day = monthrange(year, mon)[1]
    start, end = f"{month}-01", f"{month}-{last_day:02d}"

    expenses = (
        db.query(LedgerExpense)
        .filter(
            LedgerExpense.user_id == user.id,
            LedgerExpense.occur_date >= start,
            LedgerExpense.occur_date <= end,
        )
        .all()
    )
    month_cents = sum(int(e.amount_cents or 0) for e in expenses)
    today_cents = sum(int(e.amount_cents or 0) for e in expenses if e.occur_date == today)

    cat_map: dict[str, list[int]] = {}
    for e in expenses:
        cat = e.category or "其他"
        bucket = cat_map.setdefault(cat, [0, 0])
        bucket[0] += int(e.amount_cents or 0)
        bucket[1] += 1
    categories: list[LedgerCategoryStat] = []
    for cat, (cents, count) in sorted(cat_map.items(), key=lambda x: -x[1][0]):
        categories.append(
            LedgerCategoryStat(
                category=cat,
                amountCents=cents,
                amount=_cents_to_yuan(cents),
                percent=round(cents * 100 / month_cents, 1) if month_cents else 0,
                count=count,
            )
        )

    loans = db.query(LedgerLoan).filter(LedgerLoan.user_id == user.id).all()
    remaining = 0
    open_count = 0
    for loan in loans:
        repaid = _sync_loan_status(db, loan)
        rem = max(0, int(loan.principal_cents or 0) - repaid)
        if rem > 0:
            remaining += rem
            open_count += 1
    db.commit()

    return LedgerOverviewOut(
        month=month,
        monthExpenseCents=month_cents,
        monthExpense=_cents_to_yuan(month_cents),
        todayExpenseCents=today_cents,
        todayExpense=_cents_to_yuan(today_cents),
        openLoanCount=open_count,
        remainingCents=remaining,
        remaining=_cents_to_yuan(remaining),
        categories=categories,
        expenseCategories=list(LEDGER_EXPENSE_CATEGORIES),
        repayMethods=list(LEDGER_REPAY_METHODS),
    )


def list_expenses(db: Session, user: AppUser, month: str | None = None) -> list[LedgerExpenseOut]:
    today = today_str()
    month = (month or today[:7]).strip()
    year, mon = int(month[:4]), int(month[5:7])
    last_day = monthrange(year, mon)[1]
    start, end = f"{month}-01", f"{month}-{last_day:02d}"
    rows = (
        db.query(LedgerExpense)
        .filter(
            LedgerExpense.user_id == user.id,
            LedgerExpense.occur_date >= start,
            LedgerExpense.occur_date <= end,
        )
        .order_by(LedgerExpense.occur_date.desc(), LedgerExpense.created_at.desc())
        .all()
    )
    return [_expense_out(r) for r in rows]


def get_expense(db: Session, user: AppUser, expense_id: str) -> LedgerExpenseOut | None:
    e = db.get(LedgerExpense, expense_id)
    if not e or e.user_id != user.id:
        return None
    return _expense_out(e)


def create_expense(db: Session, user: AppUser, body: LedgerExpenseCreate) -> LedgerExpenseOut:
    cents = _yuan_to_cents(body.amount, body.amountCents)
    if cents <= 0:
        raise ValueError("金额须大于 0")
    cat = (body.category or "其他").strip() or "其他"
    if cat not in LEDGER_EXPENSE_CATEGORIES:
        cat = "其他"
    e = LedgerExpense(
        id=gen_id("lex"),
        user_id=user.id,
        amount_cents=cents,
        occur_date=(body.occurDate or today_str()).strip(),
        category=cat,
        note=(body.note or "").strip(),
        images_json=_dumps_list(body.images),
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return _expense_out(e)


def update_expense(
    db: Session, user: AppUser, expense_id: str, body: LedgerExpenseUpdate
) -> LedgerExpenseOut | None:
    e = db.get(LedgerExpense, expense_id)
    if not e or e.user_id != user.id:
        return None
    data = body.model_dump(exclude_unset=True)
    if "amount" in data or "amountCents" in data:
        e.amount_cents = _yuan_to_cents(data.get("amount"), data.get("amountCents"))
        if e.amount_cents <= 0:
            raise ValueError("金额须大于 0")
    if "occurDate" in data and data["occurDate"]:
        e.occur_date = str(data["occurDate"]).strip()
    if "category" in data and data["category"] is not None:
        cat = str(data["category"]).strip() or "其他"
        e.category = cat if cat in LEDGER_EXPENSE_CATEGORIES else "其他"
    if "note" in data and data["note"] is not None:
        e.note = str(data["note"]).strip()
    if "images" in data and data["images"] is not None:
        e.images_json = _dumps_list(data["images"])
    db.commit()
    db.refresh(e)
    return _expense_out(e)


def delete_expense(db: Session, user: AppUser, expense_id: str) -> bool:
    e = db.get(LedgerExpense, expense_id)
    if not e or e.user_id != user.id:
        return False
    db.delete(e)
    db.commit()
    return True


def list_loans(
    db: Session,
    user: AppUser,
    status: str | None = None,
    counterparty: str | None = None,
) -> list[LedgerLoanOut]:
    rows = db.query(LedgerLoan).filter(LedgerLoan.user_id == user.id).all()
    name_filter = (counterparty or "").strip()
    out: list[LedgerLoanOut] = []
    for loan in rows:
        if name_filter and (loan.counterparty or "").strip() != name_filter:
            continue
        item = _loan_out(db, loan, with_repayments=False)
        if status and status != "all" and item.status != status:
            continue
        out.append(item)
    db.commit()
    opens = [x for x in out if x.status == "open"]
    settled = [x for x in out if x.status != "open"]
    opens.sort(key=lambda x: x.lendDate, reverse=True)
    settled.sort(key=lambda x: x.lendDate, reverse=True)
    return opens + settled


def list_counterparties(db: Session, user: AppUser) -> list[LedgerCounterpartyOut]:
    """按对方姓名聚合：一共欠多少、几笔进行中等。"""
    rows = db.query(LedgerLoan).filter(LedgerLoan.user_id == user.id).all()
    buckets: dict[str, dict] = {}
    for loan in rows:
        name = (loan.counterparty or "").strip() or "（未填姓名）"
        repaid = _sync_loan_status(db, loan)
        principal = int(loan.principal_cents or 0)
        remaining = max(0, principal - repaid)
        b = buckets.setdefault(
            name,
            {
                "loanCount": 0,
                "openCount": 0,
                "principalCents": 0,
                "repaidCents": 0,
                "remainingCents": 0,
                "lastLendDate": "",
            },
        )
        b["loanCount"] += 1
        b["principalCents"] += principal
        b["repaidCents"] += repaid
        b["remainingCents"] += remaining
        if remaining > 0:
            b["openCount"] += 1
        if loan.lend_date and loan.lend_date > b["lastLendDate"]:
            b["lastLendDate"] = loan.lend_date
    db.commit()

    out: list[LedgerCounterpartyOut] = []
    for name, b in buckets.items():
        out.append(
            LedgerCounterpartyOut(
                name=name,
                loanCount=b["loanCount"],
                openCount=b["openCount"],
                principalCents=b["principalCents"],
                principal=_cents_to_yuan(b["principalCents"]),
                repaidCents=b["repaidCents"],
                repaid=_cents_to_yuan(b["repaidCents"]),
                remainingCents=b["remainingCents"],
                remaining=_cents_to_yuan(b["remainingCents"]),
                lastLendDate=b["lastLendDate"],
            )
        )
    with_debt = [x for x in out if x.remainingCents > 0]
    cleared = [x for x in out if x.remainingCents <= 0]
    with_debt.sort(key=lambda x: (x.remainingCents, x.lastLendDate), reverse=True)
    cleared.sort(key=lambda x: x.lastLendDate, reverse=True)
    return with_debt + cleared


def get_loan(db: Session, user: AppUser, loan_id: str) -> LedgerLoanOut | None:
    loan = db.get(LedgerLoan, loan_id)
    if not loan or loan.user_id != user.id:
        return None
    out = _loan_out(db, loan, with_repayments=True)
    db.commit()
    return out


def create_loan(db: Session, user: AppUser, body: LedgerLoanCreate) -> LedgerLoanOut:
    name = (body.counterparty or "").strip()
    if not name:
        raise ValueError("请填写对方姓名")
    cents = _yuan_to_cents(body.amount, body.amountCents)
    if cents <= 0:
        raise ValueError("出借金额须大于 0")
    loan = LedgerLoan(
        id=gen_id("lln"),
        user_id=user.id,
        counterparty=name,
        principal_cents=cents,
        lend_date=(body.lendDate or today_str()).strip(),
        due_date=(body.dueDate or "").strip(),
        status="open",
        note=(body.note or "").strip(),
        voucher_images_json=_dumps_list(body.images),
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return _loan_out(db, loan, with_repayments=True)


def update_loan(
    db: Session, user: AppUser, loan_id: str, body: LedgerLoanUpdate
) -> LedgerLoanOut | None:
    loan = db.get(LedgerLoan, loan_id)
    if not loan or loan.user_id != user.id:
        return None
    data = body.model_dump(exclude_unset=True)
    if "counterparty" in data and data["counterparty"] is not None:
        name = str(data["counterparty"]).strip()
        if not name:
            raise ValueError("请填写对方姓名")
        loan.counterparty = name
    if "amount" in data or "amountCents" in data:
        cents = _yuan_to_cents(data.get("amount"), data.get("amountCents"))
        if cents <= 0:
            raise ValueError("出借金额须大于 0")
        loan.principal_cents = cents
    if "lendDate" in data and data["lendDate"]:
        loan.lend_date = str(data["lendDate"]).strip()
    if "dueDate" in data and data["dueDate"] is not None:
        loan.due_date = str(data["dueDate"]).strip()
    if "note" in data and data["note"] is not None:
        loan.note = str(data["note"]).strip()
    if "images" in data and data["images"] is not None:
        loan.voucher_images_json = _dumps_list(data["images"])
    _sync_loan_status(db, loan)
    db.commit()
    db.refresh(loan)
    return _loan_out(db, loan, with_repayments=True)


def delete_loan(db: Session, user: AppUser, loan_id: str) -> bool:
    loan = db.get(LedgerLoan, loan_id)
    if not loan or loan.user_id != user.id:
        return False
    db.query(LedgerRepayment).filter(LedgerRepayment.loan_id == loan_id).delete()
    db.delete(loan)
    db.commit()
    return True


def create_repayment(
    db: Session, user: AppUser, loan_id: str, body: LedgerRepaymentCreate
) -> LedgerRepaymentOut:
    loan = db.get(LedgerLoan, loan_id)
    if not loan or loan.user_id != user.id:
        raise ValueError("出借记录不存在")
    cents = _yuan_to_cents(body.amount, body.amountCents)
    if cents <= 0:
        raise ValueError("归还金额须大于 0")
    method = (body.method or "微信").strip() or "微信"
    if method not in LEDGER_REPAY_METHODS:
        method = "其他"
    r = LedgerRepayment(
        id=gen_id("lrp"),
        user_id=user.id,
        loan_id=loan_id,
        amount_cents=cents,
        repay_date=(body.repayDate or today_str()).strip(),
        method=method,
        note=(body.note or "").strip(),
        voucher_images_json=_dumps_list(body.images),
    )
    db.add(r)
    _sync_loan_status(db, loan)
    db.commit()
    db.refresh(r)
    return _repay_out(r)


def update_repayment(
    db: Session, user: AppUser, repay_id: str, body: LedgerRepaymentUpdate
) -> LedgerRepaymentOut | None:
    r = db.get(LedgerRepayment, repay_id)
    if not r or r.user_id != user.id:
        return None
    data = body.model_dump(exclude_unset=True)
    if "amount" in data or "amountCents" in data:
        cents = _yuan_to_cents(data.get("amount"), data.get("amountCents"))
        if cents <= 0:
            raise ValueError("归还金额须大于 0")
        r.amount_cents = cents
    if "repayDate" in data and data["repayDate"]:
        r.repay_date = str(data["repayDate"]).strip()
    if "method" in data and data["method"] is not None:
        method = str(data["method"]).strip() or "微信"
        r.method = method if method in LEDGER_REPAY_METHODS else "其他"
    if "note" in data and data["note"] is not None:
        r.note = str(data["note"]).strip()
    if "images" in data and data["images"] is not None:
        r.voucher_images_json = _dumps_list(data["images"])
    loan = db.get(LedgerLoan, r.loan_id)
    if loan:
        _sync_loan_status(db, loan)
    db.commit()
    db.refresh(r)
    return _repay_out(r)


def delete_repayment(db: Session, user: AppUser, repay_id: str) -> bool:
    r = db.get(LedgerRepayment, repay_id)
    if not r or r.user_id != user.id:
        return False
    loan_id = r.loan_id
    db.delete(r)
    loan = db.get(LedgerLoan, loan_id)
    if loan:
        _sync_loan_status(db, loan)
    db.commit()
    return True
