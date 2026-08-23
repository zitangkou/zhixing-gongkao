"""核心业务闭环测试：答题→错题→SRS 复习、套卷交卷、签到积分、管理端 RBAC、资料练习。

使用独立临时库，避免污染开发库。须在导入 app 之前设置 DATABASE_URL。
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import timedelta
from pathlib import Path

_DB = Path(__file__).resolve().parent / "_core_loops.db"
if _DB.exists():
    _DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{_DB}"
os.environ["ALLOW_REGISTER"] = "true"
os.environ["SECRET_KEY"] = "core-loops-test-secret"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "admin123"

from app.config import get_settings  # noqa: E402

get_settings.cache_clear()

from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    AdminUser,
    AppUser,
    Article,
    Base,
    DailyLearningTask,
    ExamPaper,
    ExamQuestion,
    Question,
    RmrbArticle,
    Role,
    UserDailyTaskProgress,
    WrongAnswer,
)
from app.timezone import now, today  # noqa: E402

# 本文件会在进入 TestClient 生命周期前直接写入测试数据，先显式建表，
# 保证单独运行该测试文件时不依赖其他测试留下的数据库结构。
Base.metadata.create_all(bind=engine)


def _ok(res):
    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("code") == 0, body
    return body.get("data")


def _register(client: TestClient) -> dict:
    username = f"u_{uuid.uuid4().hex[:8]}"
    password = "Passw0rd!"
    auth = _ok(
        client.post(
            "/api/auth/register",
            json={"username": username, "password": password, "passwordConfirm": password},
        )
    )
    return {
        "username": username,
        "headers": {"Authorization": f"Bearer {auth['access_token']}"},
    }


def _user_id(username: str) -> str:
    with SessionLocal() as db:
        user = db.query(AppUser).filter(AppUser.username == username).first()
        assert user is not None
        return user.id


def _insert_article_with_question(article_id: str, question_id: str) -> None:
    with SessionLocal() as db:
        db.add(
            Article(
                id=article_id,
                title="测试文章",
                source="测试",
                publish_date="2026-08-14",
                summary="摘要",
                content="内容",
                sections="[]",
                tags="[]",
                status="published",
                allow_quiz=True,
                is_published=True,
            )
        )
        db.add(
            Question(
                id=question_id,
                article_id=article_id,
                type="single",
                stem="1+1=?",
                options=json.dumps(["1", "2", "3", "4"]),
                correct_answer="2",
                analysis="解析",
                status="approved",
                origin="manual",
                is_active=True,
            )
        )
        db.commit()


def _force_due(user_id: str, question_id: str) -> None:
    with SessionLocal() as db:
        row = (
            db.query(WrongAnswer)
            .filter(WrongAnswer.user_id == user_id, WrongAnswer.question_id == question_id)
            .first()
        )
        assert row is not None, "错题记录不存在，无法推进复习"
        row.next_review_at = now() - timedelta(days=1)
        db.commit()


def test_quiz_wrong_review_srs_loop():
    """答题 → 错题 → 艾宾浩斯复习推进 → 掌握移除。"""
    _insert_article_with_question("art-loop-1", "q-loop-1")
    with TestClient(app) as client:
        user = _register(client)
        headers = user["headers"]

        questions = _ok(
            client.get("/api/questions", params={"articleId": "art-loop-1"}, headers=headers)
        )
        assert len(questions) == 1
        qid = questions[0]["id"]

        # 答错：进错题本，第 0 档
        wrong = _ok(client.post("/api/answer", json={"questionId": qid, "answer": "1"}, headers=headers))
        assert wrong["correct"] is False and wrong["pointsEarned"] == 0
        wrongs = _ok(client.get("/api/wrong", params={"status": "all"}, headers=headers))
        row = next(w for w in wrongs if w["question"]["id"] == qid)
        assert row["reviewStage"] == 0 and row["wrongCount"] == 1

        # 首次答对：推进一档 + 复习积分
        redo = _ok(client.post("/api/wrong/redo", json={"questionId": qid, "answer": "2"}, headers=headers))
        assert redo["correct"] is True and redo["pointsEarned"] == 3
        wrongs = _ok(client.get("/api/wrong", params={"status": "all"}, headers=headers))
        assert next(w for w in wrongs if w["question"]["id"] == qid)["reviewStage"] == 1

        # 逐档答对直至掌握（第 6 档移除）
        uid = _user_id(user["username"])
        for _ in range(8):
            with SessionLocal() as db:
                exists = (
                    db.query(WrongAnswer)
                    .filter(WrongAnswer.user_id == uid, WrongAnswer.question_id == qid)
                    .first()
                )
                if exists is None:
                    break
                exists.next_review_at = now() - timedelta(days=1)
                db.commit()
            redo = _ok(client.post("/api/wrong/redo", json={"questionId": qid, "answer": "2"}, headers=headers))
            assert redo["correct"] is True

        wrongs = _ok(client.get("/api/wrong", params={"status": "all"}, headers=headers))
        assert all(w["question"]["id"] != qid for w in wrongs), "掌握后错题应被移除"

        # 积分流水含复习记录
        log = _ok(client.get("/api/points/log", headers=headers))
        assert any(item["source"] == "复习" for item in log)


def test_exam_paper_loop():
    """套卷：开考 → 逐题作答 → 交卷判分 → 历史记录。"""
    with SessionLocal() as db:
        db.add(
            ExamPaper(
                id="paper-loop-1",
                title="测试套卷",
                exam_type="mock",
                subject="行测",
                total_count=2,
                is_published=True,
            )
        )
        db.add(
            ExamQuestion(
                id="eq-loop-1",
                paper_id="paper-loop-1",
                section="常识判断",
                sort_order=1,
                stem="题1：下列哪个是 1？",
                options=json.dumps(["A", "B", "C"]),
                correct_answer="A",
                analysis="A 正确",
                is_active=True,
            )
        )
        db.add(
            ExamQuestion(
                id="eq-loop-2",
                paper_id="paper-loop-1",
                section="常识判断",
                sort_order=2,
                stem="题2：下列哪个是 3？",
                options=json.dumps(["A", "B", "C"]),
                correct_answer="C",
                analysis="C 正确",
                is_active=True,
            )
        )
        db.commit()

    with TestClient(app) as client:
        user = _register(client)
        headers = user["headers"]

        papers = _ok(client.get("/api/exam/papers", headers=headers))
        assert any(p["id"] == "paper-loop-1" for p in papers)
        detail = _ok(client.get("/api/exam/paper/paper-loop-1", headers=headers))
        assert detail["totalCount"] == 2

        started = _ok(client.post("/api/exam/start/paper-loop-1", headers=headers))
        attempt_id = started["attemptId"]
        assert len(started["questions"]) == 2

        _ok(
            client.post(
                "/api/exam/answer",
                params={"attempt_id": attempt_id},
                json={"questionId": "eq-loop-1", "answer": "A", "timeUsedSec": 10},
                headers=headers,
            )
        )
        _ok(
            client.post(
                "/api/exam/answer",
                params={"attempt_id": attempt_id},
                json={"questionId": "eq-loop-2", "answer": "B", "timeUsedSec": 15},
                headers=headers,
            )
        )

        result = _ok(client.post("/api/exam/submit", params={"attempt_id": attempt_id}, headers=headers))
        assert result["isFinished"] is True
        assert result["totalCount"] == 2
        assert result["answeredCount"] == 2
        assert result["correctCount"] == 1
        assert result["score"] == 1

        attempts = _ok(client.get("/api/exam/attempts", headers=headers))
        assert any(a["id"] == attempt_id for a in attempts)
        attempt = _ok(client.get(f"/api/exam/attempt/{attempt_id}", headers=headers))
        assert attempt["correctCount"] == 1


def test_signin_points_flow():
    """签到 → 积分入账 → 重复签到被拦截。"""
    with TestClient(app) as client:
        user = _register(client)
        headers = user["headers"]

        sign = _ok(client.post("/api/signin", headers=headers))
        assert sign["streak"] == 1 and sign["points"] == 5

        again = client.post("/api/signin", headers=headers)
        assert again.status_code == 200
        assert again.json()["code"] == 400

        assert _ok(client.get("/api/points", headers=headers)) == 5
        log = _ok(client.get("/api/points/log", headers=headers))
        assert any(item["source"] == "签到" and item["amount"] == 5 for item in log)


def test_admin_rbac():
    """管理端 RBAC：超管可读写，只读角色读可、写被 403。"""
    with TestClient(app) as client:
        login = _ok(
            client.post(
                "/admin/auth/login",
                json={"username": "admin", "password": "admin123"},
            )
        )
        assert login["role"] == "super_admin"
        assert "article:write" in login["permissions"]
        admin_headers = {"Authorization": f"Bearer {login['access_token']}"}
        articles = _ok(client.get("/admin/articles", headers=admin_headers))
        assert isinstance(articles, dict) and "items" in articles

        # 新建只读管理员
        with SessionLocal() as db:
            role = db.query(Role).filter(Role.code == "viewer").first()
            assert role is not None
            viewer_name = f"viewer_{uuid.uuid4().hex[:6]}"
            db.add(
                AdminUser(
                    username=viewer_name,
                    password_hash=hash_password("Viewer123!"),
                    nickname="只读",
                    role_id=role.id,
                )
            )
            db.commit()

        v_login = _ok(
            client.post(
                "/admin/auth/login",
                json={"username": viewer_name, "password": "Viewer123!"},
            )
        )
        v_headers = {"Authorization": f"Bearer {v_login['access_token']}"}
        assert v_login["role"] == "viewer"
        assert "article:write" not in v_login["permissions"]

        # 读接口可访问
        _ok(client.get("/admin/articles", headers=v_headers))

        # 写接口被 403 拦截
        denied = client.post(
            "/admin/articles",
            headers=v_headers,
            json={"title": "越权", "source": "x", "publish_date": "2026-08-14", "summary": "x"},
        )
        assert denied.status_code == 403, denied.text


def test_ziliao_drill_submit_and_stats():
    """资料分析：样例练习组 → 提交判分 → 今日统计。"""
    with TestClient(app) as client:
        user = _register(client)
        headers = user["headers"]

        sets = _ok(
            client.get(
                "/api/ziliao/drill/sets",
                params={"includeSample": "true"},
                headers=headers,
            )
        )
        assert sets, "样例练习组未初始化"
        sample = next(s for s in sets if s["isSample"])
        detail = _ok(client.get(f"/api/ziliao/drill/set/{sample['setId']}", headers=headers))
        questions = detail["questions"]
        assert questions

        with SessionLocal() as db:
            rows = (
                db.query(ExamQuestion)
                .filter(ExamQuestion.id.in_([q["id"] for q in questions]))
                .all()
            )
            correct_map = {r.id: r.correct_answer for r in rows}

        total = len(questions)
        answers = [
            {"questionId": q["id"], "userAnswer": correct_map[q["id"]]}
            for q in questions
        ]
        # 第一题故意答错（换一个选项）
        first = questions[0]
        wrong_option = next(
            opt for opt in first["options"] if opt != correct_map[first["id"]]
        )
        answers[0]["userAnswer"] = wrong_option

        result = _ok(
            client.post(
                "/api/ziliao/drill/submit",
                json={"setId": sample["setId"], "answers": answers, "timeUsedSec": 42},
                headers=headers,
            )
        )
        assert result["totalCount"] == total
        assert result["correctCount"] == total - 1
        assert len(result["wrongs"]) == 1

        overview = _ok(client.get("/api/ziliao/overview", headers=headers))
        assert overview["todaySets"] >= 1
        assert overview["todayTotal"] >= total
        assert overview["todayCorrect"] >= total - 1


def test_daily_task_state_machine_and_product_isolation():
    """今日任务：按产品隔离，草稿可恢复，状态只能顺序推进。"""
    task_date = "2026-08-23"
    with TestClient(app) as client:
        user = _register(client)
        shenlun_headers = {**user["headers"], "X-Product-Key": "shenlun"}
        theory_headers = {**user["headers"], "X-Product-Key": "theory"}

        with SessionLocal() as db:
            db.add_all(
                [
                    DailyLearningTask(
                        id="dlt-shenlun-loop",
                        product_key="shenlun",
                        task_date=task_date,
                        task_type="daily_training",
                        title="今日三刀训练",
                        description="精读并完成概括",
                        content_type="rmrb_article",
                        content_id="rmrb-test",
                        estimated_minutes=15,
                        total_steps=5,
                        status="published",
                    ),
                    DailyLearningTask(
                        id="dlt-theory-loop",
                        product_key="theory",
                        task_date=task_date,
                        task_type="daily_pack",
                        title="今日政治理论",
                        estimated_minutes=12,
                        total_steps=4,
                        status="published",
                    ),
                ]
            )
            db.commit()

        shenlun = _ok(
            client.get(
                "/api/product/daily-tasks",
                params={"date": task_date},
                headers=shenlun_headers,
            )
        )
        assert shenlun["productKey"] == "shenlun"
        assert [task["id"] for task in shenlun["tasks"]] == ["dlt-shenlun-loop"]
        assert shenlun["tasks"][0]["progress"]["state"] == "not_started"

        theory = _ok(
            client.get(
                "/api/product/daily-tasks",
                params={"date": task_date},
                headers=theory_headers,
            )
        )
        assert [task["id"] for task in theory["tasks"]] == ["dlt-theory-loop"]

        started = _ok(
            client.post(
                "/api/product/daily-tasks/dlt-shenlun-loop/progress",
                headers=shenlun_headers,
                json={"event": "start"},
            )
        )
        assert started["progress"]["state"] == "in_progress"

        saved = _ok(
            client.post(
                "/api/product/daily-tasks/dlt-shenlun-loop/progress",
                headers=shenlun_headers,
                json={
                    "event": "save",
                    "currentStep": 2,
                    "draft": {"answer": "基层协同机制仍需完善"},
                },
            )
        )
        assert saved["progress"]["currentStep"] == 2

        restored = _ok(
            client.get(
                "/api/product/daily-tasks",
                params={"date": task_date},
                headers=shenlun_headers,
            )
        )
        progress = restored["tasks"][0]["progress"]
        assert progress["state"] == "in_progress"
        assert progress["draft"]["answer"] == "基层协同机制仍需完善"

        invalid = client.post(
            "/api/product/daily-tasks/dlt-shenlun-loop/progress",
            headers=shenlun_headers,
            json={"event": "complete"},
        )
        assert invalid.status_code == 200
        assert invalid.json()["code"] == 400

        for event, expected in (
            ("submit", "submitted"),
            ("review", "reviewed"),
            ("complete", "completed"),
        ):
            updated = _ok(
                client.post(
                    "/api/product/daily-tasks/dlt-shenlun-loop/progress",
                    headers=shenlun_headers,
                    json={"event": event},
                )
            )
            assert updated["progress"]["state"] == expected

        completed = _ok(
            client.get(
                "/api/product/daily-tasks",
                params={"date": task_date},
                headers=shenlun_headers,
            )
        )
        assert completed["completion"] == 100
        assert completed["completedCount"] == 1

        cross_product = client.post(
            "/api/product/daily-tasks/dlt-shenlun-loop/progress",
            headers=theory_headers,
            json={"event": "start"},
        )
        assert cross_product.status_code == 200
        assert cross_product.json()["code"] == 400


def test_shenlun_home_provisions_one_daily_article_task():
    """申论首页为今日选择一篇已审核文章，重复加载不重复编排。"""
    task_date = today()
    with TestClient(app) as client:
        user = _register(client)
        headers = {**user["headers"], "X-Product-Key": "shenlun"}
        with SessionLocal() as db:
            existing_ids = [
                row[0]
                for row in db.query(DailyLearningTask.id).filter(
                    DailyLearningTask.product_key == "shenlun",
                    DailyLearningTask.task_date == task_date,
                )
            ]
            if existing_ids:
                db.query(UserDailyTaskProgress).filter(
                    UserDailyTaskProgress.task_id.in_(existing_ids)
                ).delete(synchronize_session=False)
            db.query(DailyLearningTask).filter(
                DailyLearningTask.product_key == "shenlun",
                DailyLearningTask.task_date == task_date,
            ).delete(synchronize_session=False)
            db.add(
                RmrbArticle(
                    id="rmrb-daily-home",
                    title="以务实行动答好民生考题",
                    source="人民时评",
                    publish_date=task_date,
                    summary="从群众关切出发，把好事实事办到心坎上。",
                    content="测试文章正文",
                    tags='["民生", "基层治理"]',
                    is_published=True,
                    sort_order=999,
                )
            )
            db.commit()

        first = _ok(client.get("/api/product/daily-tasks", headers=headers))
        second = _ok(client.get("/api/product/daily-tasks", headers=headers))

        assert first["date"] == task_date
        assert first["totalCount"] == 1
        assert second["totalCount"] == 1
        task = first["tasks"][0]
        assert task["taskType"] == "shenlun_article_training"
        assert task["contentId"] == "rmrb-daily-home"
        assert task["totalSteps"] == 4
        assert task["metadata"]["tags"] == ["民生", "基层治理"]


def teardown_module(_mod=None):
    engine.dispose()
    for path in (_DB, Path(f"{_DB}-shm"), Path(f"{_DB}-wal")):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
