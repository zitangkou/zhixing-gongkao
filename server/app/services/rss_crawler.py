"""人民日报 RSS 爬取与正文解析"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

PEOPLE_RSS_FEEDS = [
    {
        "source": "人民日报",
        "url": "http://www.people.com.cn/rss/politics.xml",
        "tags": ["时政", "政治理论"],
    },
    {
        "source": "人民日报",
        "url": "http://www.people.com.cn/rss/legal.xml",
        "tags": ["法治", "政治理论"],
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ZhixingGongkaoBot/1.0; +https://github.com/zitangkou/zhixing-gongkao)",
}


@dataclass
class RssArticleItem:
    title: str
    link: str
    summary: str
    content: str
    source: str
    source_url: str
    tags: list[str]
    publish_date: str


def _clean_html_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _fetch_article_content(client: httpx.Client, url: str) -> str:
    try:
        resp = client.get(url, headers=HEADERS, timeout=20, follow_redirects=True)
        resp.raise_for_status()
    except Exception:
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")

    selectors = [
        "#rwb_zw",
        ".box_con",
        ".article",
        ".content",
        "article",
    ]
    for sel in selectors:
        node = soup.select_one(sel)
        if node:
            text = _clean_html_text(str(node))
            if len(text) > 80:
                return text

    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20]
    if paragraphs:
        return "\n\n".join(paragraphs[:20])

    return _clean_html_text(resp.text)[:3000]


def _parse_rss_items(xml_text: str, source: str, source_url: str, tags: list[str], limit: int = 5) -> list[RssArticleItem]:
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []

    items: list[RssArticleItem] = []
    for item in channel.findall("item")[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()

        if not title or not link:
            continue

        from app.timezone import today as today_str

        publish_date = today_str()
        if pub:
            try:
                publish_date = datetime.strptime(pub[:16], "%a, %d %b %Y").strftime("%Y-%m-%d")
            except ValueError:
                pass

        summary = _clean_html_text(description)[:200] if description else title[:120]
        items.append(
            RssArticleItem(
                title=title,
                link=link,
                summary=summary,
                content="",
                source=source,
                source_url=source_url,
                tags=tags,
                publish_date=publish_date,
            )
        )
    return items


def fetch_people_daily_articles(limit_per_feed: int = 5) -> list[RssArticleItem]:
    results: list[RssArticleItem] = []

    with httpx.Client(headers=HEADERS, timeout=25) as client:
        for feed in PEOPLE_RSS_FEEDS:
            try:
                resp = client.get(feed["url"], follow_redirects=True)
                resp.raise_for_status()
                items = _parse_rss_items(
                    resp.text,
                    feed["source"],
                    feed["url"],
                    feed["tags"],
                    limit=limit_per_feed,
                )
            except Exception:
                continue

            for item in items:
                content = _fetch_article_content(client, item.link)
                if not content:
                    content = item.summary
                item.content = content
                results.append(item)

    return results
