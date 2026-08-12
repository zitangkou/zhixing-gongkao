import json

from sqlalchemy.orm import Session

# 爬虫模块已关闭 — 入口见 main.py / admin/routes.py

from app.models import Article, CrawlLog, gen_id
from app.services.crawl_filter import should_keep_article
from app.services.question_factory import add_generated_questions
from app.timezone import now
from app.services.rss_crawler import fetch_people_daily_articles
from app.services.section_parser import build_sections_from_content, sections_to_content
from app.services.serializers import build_mind_map

# 本地兜底数据源（RSS 不可用时）
FALLBACK_SOURCES = [
    {
        "source": "求是网",
        "source_url": "https://www.qstheory.cn/",
        "items": [
            {
                "title": "深刻把握中华文明的突出特性",
                "summary": "中华文明连续性、创新性、统一性、包容性、和平性。",
                "content": """中华文明具有突出的连续性，从根本上决定了中华民族必然走自己的路。中华文明具有突出的创新性，从根本上决定了中华民族守正不守旧、尊古不复古的进取精神。

中华文明具有突出的统一性，从根本上决定了各民族融入中华民族大家庭，决定了国土不可分、国家不可乱、民族不可散、文明不可断的共同信念。

中华文明具有突出的包容性，从根本上决定了中华民族交往交流交融的历史取向。中华文明具有突出的和平性，从根本上决定了中国始终是世界和平的建设者。""",
                "tags": ["中华文明", "文化思想"],
            },
        ],
    },
]


def _today() -> str:
    return now().strftime("%Y-%m-%d")


def _save_article(db: Session, item: dict, source: str, source_url: str) -> Article | None:
    link = item.get("source_url") or source_url
    exists = (
        db.query(Article)
        .filter((Article.title == item["title"]) | (Article.source_url == link))
        .first()
    )
    if exists:
        return None

    content = item.get("content") or item.get("summary") or ""
    keep, reason = should_keep_article(item["title"], content)
    if not keep:
        return None

    sections = item.get("sections") or build_sections_from_content(item["title"], content)
    if not content:
        content = sections_to_content(sections)

    mind_map = build_mind_map(item["title"], content)
    article = Article(
        id=gen_id("art"),
        title=item["title"],
        source=source,
        source_url=link,
        publish_date=item.get("publish_date") or _today(),
        summary=item.get("summary") or item["title"][:120],
        content=content,
        sections=json.dumps(sections, ensure_ascii=False),
        tags=json.dumps(item.get("tags") or ["政治理论"], ensure_ascii=False),
        mind_map=json.dumps(mind_map, ensure_ascii=False),
        status="pending",
        is_published=False,
        is_daily=False,
        allow_quiz=True,
        crawled_at=now(),
    )
    db.add(article)
    db.flush()
    add_generated_questions(db, article, pending=True, origin="crawl_auto")
    return article


def _refresh_daily_recommendations(db: Session) -> None:
    db.query(Article).filter(Article.is_featured.is_(False)).update({"is_daily": False})
    latest = (
        db.query(Article)
        .filter(
            Article.is_published.is_(True),
            Article.status == "published",
            Article.is_featured.is_(False),
        )
        .order_by(Article.created_at.desc())
        .limit(3)
        .all()
    )
    for a in latest:
        a.is_daily = True


def run_daily_crawl(db: Session) -> CrawlLog:
    log = CrawlLog(source="all", status="running", started_at=now())
    db.add(log)
    db.flush()

    fetched = 0
    new_count = 0
    filtered_count = 0
    messages: list[str] = []

    try:
        rss_items = fetch_people_daily_articles(limit_per_feed=5)
        fetched += len(rss_items)

        for rss in rss_items:
            item = {
                "title": rss.title,
                "summary": rss.summary,
                "content": rss.content,
                "tags": rss.tags,
                "publish_date": rss.publish_date,
                "source_url": rss.link,
            }
            keep, reason = should_keep_article(item["title"], item["content"] or item["summary"])
            if not keep:
                filtered_count += 1
                messages.append(f"[过滤] {rss.title[:20]}… ({reason})")
                continue
            article = _save_article(db, item, rss.source, rss.source_url)
            if article:
                new_count += 1
                messages.append(f"[待审] {rss.title[:28]}")

        if new_count == 0:
            for src in FALLBACK_SOURCES:
                for raw in src["items"]:
                    fetched += 1
                    keep, reason = should_keep_article(raw["title"], raw.get("content") or raw.get("summary", ""))
                    if not keep:
                        filtered_count += 1
                        continue
                    article = _save_article(db, raw, src["source"], src["source_url"])
                    if article:
                        new_count += 1
                        messages.append(f"[待审/兜底] {raw['title'][:28]}")

        _refresh_daily_recommendations(db)

        log.status = "success"
        log.fetched_count = fetched
        log.new_count = new_count
        summary = f"抓取 {fetched}，过滤 {filtered_count}，待审新增 {new_count}"
        detail = "; ".join(messages[:20]) if messages else "无新文章"
        log.message = f"{summary} | {detail}"
    except Exception as e:
        log.status = "failed"
        log.message = str(e)
    finally:
        log.finished_at = now()
        db.commit()
        db.refresh(log)

    return log
