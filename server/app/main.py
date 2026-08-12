from contextlib import asynccontextmanager
from pathlib import Path

# from apscheduler.schedulers.background import BackgroundScheduler  # 爬虫定时任务已关闭
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.admin.routes import router as admin_router
from app.api.public.routes import router as public_router
from app.config import get_settings
from app.database import SessionLocal, engine
from app.models import Base
# from app.services.crawler import run_daily_crawl  # 爬虫已关闭

settings = get_settings()
# scheduler = BackgroundScheduler()  # 爬虫定时任务已关闭


def _ensure_article_columns():
    """SQLite 旧库补列"""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if not insp.has_table("articles"):
        return
    cols = [c["name"] for c in insp.get_columns("articles")]
    alters: list[str] = []
    if "sections" not in cols:
        alters.append("ALTER TABLE articles ADD COLUMN sections TEXT DEFAULT '[]'")
    if "is_featured" not in cols:
        alters.append("ALTER TABLE articles ADD COLUMN is_featured BOOLEAN DEFAULT 0")
    if "category_id" not in cols:
        alters.append("ALTER TABLE articles ADD COLUMN category_id VARCHAR(32)")
    if "category_path" not in cols:
        alters.append("ALTER TABLE articles ADD COLUMN category_path TEXT DEFAULT '[]'")
    if "importance" not in cols:
        alters.append("ALTER TABLE articles ADD COLUMN importance INTEGER DEFAULT 3")
    if "status" not in cols:
        alters.append("ALTER TABLE articles ADD COLUMN status VARCHAR(16) DEFAULT 'published'")
    if "allow_quiz" not in cols:
        alters.append("ALTER TABLE articles ADD COLUMN allow_quiz BOOLEAN DEFAULT 1")
    if not alters:
        return
    with engine.begin() as conn:
        for sql in alters:
            conn.execute(text(sql))


def _ensure_app_user_columns():
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if not insp.has_table("app_users"):
        return
    cols = [c["name"] for c in insp.get_columns("app_users")]
    alters: list[str] = []
    if "username" not in cols:
        alters.append("ALTER TABLE app_users ADD COLUMN username VARCHAR(64)")
    if "password_hash" not in cols:
        alters.append("ALTER TABLE app_users ADD COLUMN password_hash VARCHAR(255)")
    if "email" not in cols:
        alters.append("ALTER TABLE app_users ADD COLUMN email VARCHAR(128) DEFAULT ''")
    if "phone" not in cols:
        alters.append("ALTER TABLE app_users ADD COLUMN phone VARCHAR(20) DEFAULT ''")
    if not alters:
        return
    with engine.begin() as conn:
        for sql in alters:
            conn.execute(text(sql))


def _ensure_manual_wrong_images_column():
    """兼容旧 manual_wrongs 表"""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if not insp.has_table("manual_wrongs"):
        return
    cols = [c["name"] for c in insp.get_columns("manual_wrongs")]
    # SQLAlchemy 会自动 create_all 新表，这里只处理已存在旧表
    needed = {
        "images": "ALTER TABLE manual_wrongs ADD COLUMN images TEXT DEFAULT '[]'",
        "source": "ALTER TABLE manual_wrongs ADD COLUMN source VARCHAR(32) DEFAULT 'manual'",
        "review_count": "ALTER TABLE manual_wrongs ADD COLUMN review_count INTEGER DEFAULT 0",
        "review_stage": "ALTER TABLE manual_wrongs ADD COLUMN review_stage INTEGER DEFAULT 0",
        "next_review_at": "ALTER TABLE manual_wrongs ADD COLUMN next_review_at DATETIME",
        "mastered": "ALTER TABLE manual_wrongs ADD COLUMN mastered BOOLEAN DEFAULT 0",
        "wrong_reason": "ALTER TABLE manual_wrongs ADD COLUMN wrong_reason VARCHAR(64) DEFAULT ''",
        "question_type": "ALTER TABLE manual_wrongs ADD COLUMN question_type VARCHAR(64) DEFAULT ''",
        "note": "ALTER TABLE manual_wrongs ADD COLUMN note TEXT DEFAULT ''",
        "knowledge_node_id": "ALTER TABLE manual_wrongs ADD COLUMN knowledge_node_id VARCHAR(32)",
        "knowledge_tree_key": "ALTER TABLE manual_wrongs ADD COLUMN knowledge_tree_key VARCHAR(32) DEFAULT ''",
        "knowledge_path": "ALTER TABLE manual_wrongs ADD COLUMN knowledge_path TEXT DEFAULT ''",
    }
    alters = [sql for col, sql in needed.items() if col not in cols]
    with engine.begin() as conn:
        for sql in alters:
            conn.execute(text(sql))
        if "next_review_at" in cols or "next_review_at" in needed:
            conn.execute(
                text(
                    "UPDATE manual_wrongs SET next_review_at = CURRENT_TIMESTAMP "
                    "WHERE next_review_at IS NULL AND (mastered = 0 OR mastered IS NULL)"
                )
            )


def _ensure_knowledge_node_columns():
    """兼容旧 knowledge_nodes 表：补 my_note / is_starred / 掌握度字段"""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if not insp.has_table("knowledge_nodes"):
        return
    cols = [c["name"] for c in insp.get_columns("knowledge_nodes")]
    alters: list[str] = []
    if "my_note" not in cols:
        alters.append("ALTER TABLE knowledge_nodes ADD COLUMN my_note TEXT DEFAULT ''")
    if "is_starred" not in cols:
        alters.append("ALTER TABLE knowledge_nodes ADD COLUMN is_starred BOOLEAN DEFAULT 0")
    if "mastery_level" not in cols:
        alters.append("ALTER TABLE knowledge_nodes ADD COLUMN mastery_level VARCHAR(16) DEFAULT 'new'")
    if "next_review_at" not in cols:
        alters.append("ALTER TABLE knowledge_nodes ADD COLUMN next_review_at DATETIME")
    if "review_count" not in cols:
        alters.append("ALTER TABLE knowledge_nodes ADD COLUMN review_count INTEGER DEFAULT 0")
    if "last_reviewed_at" not in cols:
        alters.append("ALTER TABLE knowledge_nodes ADD COLUMN last_reviewed_at DATETIME")
    if not alters:
        return
    with engine.begin() as conn:
        for sql in alters:
            conn.execute(text(sql))


def _ensure_exam_question_knowledge_columns():
    """真题题目关联知识框架字段"""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if not insp.has_table("exam_questions"):
        return
    cols = [c["name"] for c in insp.get_columns("exam_questions")]
    needed = {
        "knowledge_node_id": "ALTER TABLE exam_questions ADD COLUMN knowledge_node_id VARCHAR(32)",
        "knowledge_tree_key": "ALTER TABLE exam_questions ADD COLUMN knowledge_tree_key VARCHAR(32) DEFAULT ''",
        "knowledge_path": "ALTER TABLE exam_questions ADD COLUMN knowledge_path TEXT DEFAULT ''",
    }
    alters = [sql for col, sql in needed.items() if col not in cols]
    if not alters:
        return
    with engine.begin() as conn:
        for sql in alters:
            conn.execute(text(sql))


def _ensure_corpus_knowledge_columns():
    """语料本挂知识框架字段"""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if not insp.has_table("corpus_items"):
        return
    cols = [c["name"] for c in insp.get_columns("corpus_items")]
    needed = {
        "knowledge_node_id": "ALTER TABLE corpus_items ADD COLUMN knowledge_node_id VARCHAR(32)",
        "knowledge_tree_key": "ALTER TABLE corpus_items ADD COLUMN knowledge_tree_key VARCHAR(64) DEFAULT ''",
        "knowledge_path": "ALTER TABLE corpus_items ADD COLUMN knowledge_path TEXT DEFAULT ''",
    }
    alters = [sql for col, sql in needed.items() if col not in cols]
    if not alters:
        return
    with engine.begin() as conn:
        for sql in alters:
            conn.execute(text(sql))


def _ensure_plan_task_priority_column():
    """兼容旧 plan_tasks 表：补 priority"""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if not insp.has_table("plan_tasks"):
        return
    cols = [c["name"] for c in insp.get_columns("plan_tasks")]
    if "priority" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE plan_tasks ADD COLUMN priority INTEGER DEFAULT 3"))


def _ensure_shenlun_columns():
    """开采本结构化字段 + 规范词分类（兼容已有表）"""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if insp.has_table("shenlun_mine_logs"):
        cols = {c["name"] for c in insp.get_columns("shenlun_mine_logs")}
        alters = []
        if "argument_json" not in cols:
            alters.append("ALTER TABLE shenlun_mine_logs ADD COLUMN argument_json TEXT DEFAULT '{}'")
        if "templates_json" not in cols:
            alters.append("ALTER TABLE shenlun_mine_logs ADD COLUMN templates_json TEXT DEFAULT '[]'")
        if "quotes_json" not in cols:
            alters.append("ALTER TABLE shenlun_mine_logs ADD COLUMN quotes_json TEXT DEFAULT '[]'")
        if "verbs_json" not in cols:
            alters.append("ALTER TABLE shenlun_mine_logs ADD COLUMN verbs_json TEXT DEFAULT '[]'")
        if alters:
            with engine.begin() as conn:
                for sql in alters:
                    conn.execute(text(sql))
    if insp.has_table("shenlun_norm_terms"):
        cols = {c["name"] for c in insp.get_columns("shenlun_norm_terms")}
        if "category" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE shenlun_norm_terms ADD COLUMN category VARCHAR(32) DEFAULT '其他'"))
    if insp.has_table("shenlun_term_categories"):
        cols = {c["name"] for c in insp.get_columns("shenlun_term_categories")}
        if "kind" not in cols:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE shenlun_term_categories ADD COLUMN kind VARCHAR(16) DEFAULT 'term'")
                )


def _ensure_wrong_answer_columns():
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if not insp.has_table("wrong_answers"):
        return
    cols = [c["name"] for c in insp.get_columns("wrong_answers")]
    alters: list[str] = []
    if "user_answer" not in cols:
        alters.append("ALTER TABLE wrong_answers ADD COLUMN user_answer TEXT DEFAULT ''")
    if "review_stage" not in cols:
        alters.append("ALTER TABLE wrong_answers ADD COLUMN review_stage INTEGER DEFAULT 0")
    if "next_review_at" not in cols:
        alters.append("ALTER TABLE wrong_answers ADD COLUMN next_review_at DATETIME")
    with engine.begin() as conn:
        for sql in alters:
            conn.execute(text(sql))
        # 旧错题先全部标为今日到期，进入记忆曲线
        conn.execute(
            text(
                "UPDATE wrong_answers SET next_review_at = CURRENT_TIMESTAMP "
                "WHERE next_review_at IS NULL"
            )
        )


def _ensure_question_columns():
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if not insp.has_table("questions"):
        return
    cols = [c["name"] for c in insp.get_columns("questions")]
    alters: list[str] = []
    if "status" not in cols:
        alters.append("ALTER TABLE questions ADD COLUMN status VARCHAR(16) DEFAULT 'approved'")
    if "origin" not in cols:
        alters.append("ALTER TABLE questions ADD COLUMN origin VARCHAR(16) DEFAULT 'manual'")
    if not alters:
        return
    with engine.begin() as conn:
        for sql in alters:
            conn.execute(text(sql))


def _ensure_health_daily_columns():
    """兼容旧 health_daily_logs：补 meals_json / stool_json"""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if not insp.has_table("health_daily_logs"):
        return
    cols = {c["name"] for c in insp.get_columns("health_daily_logs")}
    alters: list[str] = []
    if "meals_json" not in cols:
        alters.append("ALTER TABLE health_daily_logs ADD COLUMN meals_json TEXT DEFAULT '{}'")
    if "stool_json" not in cols:
        alters.append("ALTER TABLE health_daily_logs ADD COLUMN stool_json TEXT DEFAULT '{}'")
    if not alters:
        return
    with engine.begin() as conn:
        for sql in alters:
            conn.execute(text(sql))


def _ensure_rmrb_article_columns():
    """兼容旧 rmrb_articles：补主题标签 tags"""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if not insp.has_table("rmrb_articles"):
        return
    cols = {c["name"] for c in insp.get_columns("rmrb_articles")}
    if "tags" in cols:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE rmrb_articles ADD COLUMN tags TEXT DEFAULT '[]'"))


def _ensure_ziliao_formula_plain_column():
    """资料分析公式：补 formula_plain（中文可读式，配合 latex 渲染）"""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if not insp.has_table("ziliao_formulas"):
        return
    cols = [c["name"] for c in insp.get_columns("ziliao_formulas")]
    if "formula_plain" in cols:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE ziliao_formulas ADD COLUMN formula_plain TEXT DEFAULT ''"))


# def _scheduled_crawl():
#     db = SessionLocal()
#     try:
#         run_daily_crawl(db)
#     finally:
#         db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _ensure_article_columns()
    _ensure_app_user_columns()
    _ensure_question_columns()
    _ensure_wrong_answer_columns()
    _ensure_manual_wrong_images_column()
    _ensure_knowledge_node_columns()
    _ensure_exam_question_knowledge_columns()
    _ensure_corpus_knowledge_columns()
    _ensure_plan_task_priority_column()
    _ensure_shenlun_columns()
    _ensure_health_daily_columns()
    _ensure_rmrb_article_columns()
    _ensure_ziliao_formula_plain_column()
    from app.seed import seed_if_empty

    db = SessionLocal()
    try:
        seed_if_empty(db)
        # 启动时尝试同步 Obsidian 知识库（目录不存在则跳过）
        try:
            from app.services.knowledge_service import sync_knowledge

            sync_knowledge(db)
        except Exception as e:
            print(f"[knowledge] 启动同步失败: {e}")
        # 启动时确保 plan 模板有默认数据
        try:
            from app.services.plan_service import seed_default_templates

            seed_default_templates(db)
        except Exception as e:
            print(f"[plan] 模板初始化失败: {e}")
        # 启动时 seed 48 个 DJ 音标
        try:
            from app.services.phonetic_service import seed_default_phonetics

            seed_default_phonetics(db)
        except Exception as e:
            print(f"[phonetic] 音标初始化失败: {e}")
        # 资料分析资源库 + 样例材料组（force 刷新 latex 种子时可在 Admin 点覆盖）
        try:
            from app.services.ziliao_service import seed_sample_drill_paper, seed_ziliao_resources

            seed_ziliao_resources(db)
            seed_sample_drill_paper(db)
        except Exception as e:
            print(f"[ziliao] 资料分析初始化失败: {e}")
    finally:
        db.close()

    # 爬虫定时任务已关闭（如需恢复：取消注释 scheduler / _scheduled_crawl，并设置 CRAWL_ENABLED=true）
    # if settings.crawl_enabled:
    #     scheduler.add_job(
    #         _scheduled_crawl,
    #         "cron",
    #         hour=settings.crawl_cron_hour,
    #         minute=settings.crawl_cron_minute,
    #         id="daily_crawl",
    #         replace_existing=True,
    #     )
    #     scheduler.start()
    yield
    # if scheduler.running:
    #     scheduler.shutdown()


app = FastAPI(
    title="政考通 API",
    description="轻量级政治理论学习后端 — 文章爬取、试题管理、RBAC 权限",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public_router)
app.include_router(admin_router)

_admin_dist = Path(__file__).resolve().parents[1] / "admin-dist"


@app.get("/manage")
def manage_redirect():
    return RedirectResponse(url="/manage/")


@app.get("/health")
def health():
    return {"status": "ok", "service": "zhengkao-tong-server"}


from app.upload_paths import UPLOADS_DIR

_uploads_dir = UPLOADS_DIR
_uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")

if _admin_dist.is_dir():
    app.mount("/manage", StaticFiles(directory=_admin_dist, html=True), name="admin-web")
