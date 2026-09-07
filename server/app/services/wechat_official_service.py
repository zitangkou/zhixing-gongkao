"""杜衡阁公众号基础回调：验签、明文消息解析和确定性回复。"""
from __future__ import annotations

import hashlib
import hmac
import re
import threading
import time
import xml.etree.ElementTree as ET
from collections import OrderedDict
from dataclasses import dataclass
from urllib.parse import urlsplit


MAX_XML_BYTES = 64 * 1024
DEDUP_TTL_SECONDS = 300
DEDUP_MAX_ITEMS = 2048


@dataclass(frozen=True)
class InboundMessage:
    to_user: str
    from_user: str
    create_time: str
    msg_type: str
    content: str = ""
    event: str = ""
    event_key: str = ""
    msg_id: str = ""


@dataclass(frozen=True)
class ReplyDecision:
    intent: str
    text: str | None


_dedup_lock = threading.Lock()
_dedup_cache: OrderedDict[str, tuple[float, ReplyDecision]] = OrderedDict()


def verify_signature(token: str, signature: str, timestamp: str, nonce: str) -> bool:
    if not token or not signature or not timestamp or not nonce:
        return False
    digest = hashlib.sha1("".join(sorted((token, timestamp, nonce))).encode("utf-8")).hexdigest()
    return hmac.compare_digest(digest, signature)


def parse_message(raw: bytes) -> InboundMessage:
    if not raw or len(raw) > MAX_XML_BYTES:
        raise ValueError("消息正文为空或超过限制")
    upper = raw[:1024].upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("消息正文包含不允许的 XML 声明")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError("消息 XML 无法解析") from exc

    def value(name: str) -> str:
        node = root.find(name)
        return (node.text or "").strip() if node is not None else ""

    message = InboundMessage(
        to_user=value("ToUserName"),
        from_user=value("FromUserName"),
        create_time=value("CreateTime"),
        msg_type=value("MsgType").lower(),
        content=value("Content"),
        event=value("Event").lower(),
        event_key=value("EventKey"),
        msg_id=value("MsgId"),
    )
    if not message.to_user or not message.from_user or not message.msg_type:
        raise ValueError("消息缺少必要字段")
    return message


def _normalise_text(text: str) -> str:
    text = text.strip().lower()
    return re.sub(r"[\s，。！？、,.!?：:；;‘’“”\"'（）()【】\[\]]+", "", text)


def _link(base_url: str, path: str) -> str:
    base = base_url.strip().rstrip("/")
    if not base:
        return ""
    parsed = urlsplit(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return f"{base}{path}"


def _with_link(title: str, description: str, url: str) -> str:
    if not url:
        return f"{title}\n{description}\n\n入口正在配置中，回复“菜单”可查看当前可用内容。"
    return f"{title}\n{description}\n\n开始学习：{url}"


def decide_reply(message: InboundMessage, public_base_url: str) -> ReplyDecision:
    theory_url = _link(public_base_url, "/theory/")
    shenlun_url = _link(public_base_url, "/shenlun/")

    if message.msg_type == "event":
        if message.event == "subscribe":
            return ReplyDecision(
                "subscribe",
                "欢迎来到杜衡阁。\n\n这里提供时政学习与申论学习内容，帮助你把重要文章读懂、练会、留下学习记录。\n\n回复“今日”，开始今天最值得完成的一次学习；回复“菜单”，查看全部入口。",
            )
        if message.event == "unsubscribe":
            return ReplyDecision("unsubscribe", None)
        return ReplyDecision("unsupported_event", "已收到。回复“菜单”查看当前学习入口。")

    if message.msg_type != "text":
        return ReplyDecision("unsupported_message", "暂时只能识别文字消息。回复“菜单”查看学习入口。")

    text = _normalise_text(message.content)
    aliases = {
        "today": {"今日", "今天", "今日学习", "今日一练"},
        "theory": {"时政", "日知", "时政学习"},
        "shenlun": {"申论", "策论", "申论学习", "三刀"},
        "menu": {"菜单", "帮助", "导航", "开始"},
    }
    if text in aliases["today"]:
        return ReplyDecision("today", _with_link("今日学习", "先完成一份短而完整的时政阅读与练习。", theory_url))
    if text in aliases["theory"]:
        return ReplyDecision("theory", _with_link("时政学习｜知行日知", "阅读重点文章，完成 5 题分辑或同文合集。", theory_url))
    if text in aliases["shenlun"]:
        return ReplyDecision("shenlun", _with_link("申论学习｜知行策论", "从原文阅读、三刀示范到一次短练习。", shenlun_url))
    if text in aliases["menu"]:
        return ReplyDecision(
            "menu",
            "杜衡阁学习菜单\n\n回复“今日”：开始今天的学习\n回复“时政”：进入知行日知\n回复“申论”：进入知行策论\n\n每次只选一个任务，完成后再继续。",
        )
    return ReplyDecision("fallback", "暂时没有识别这个问题。\n\n回复“今日”开始学习，或回复“菜单”查看全部入口。")


def message_key(message: InboundMessage) -> str:
    if message.msg_id:
        return f"msg:{message.msg_id}"
    material = "|".join(
        (message.from_user, message.create_time, message.msg_type, message.event, message.event_key, message.content)
    )
    return "event:" + hashlib.sha256(material.encode("utf-8")).hexdigest()


def decide_reply_once(message: InboundMessage, public_base_url: str) -> ReplyDecision:
    key = message_key(message)
    now = time.monotonic()
    with _dedup_lock:
        expired = [cached_key for cached_key, (deadline, _) in _dedup_cache.items() if deadline <= now]
        for cached_key in expired:
            _dedup_cache.pop(cached_key, None)
        cached = _dedup_cache.get(key)
        if cached:
            _dedup_cache.move_to_end(key)
            return cached[1]
        decision = decide_reply(message, public_base_url)
        _dedup_cache[key] = (now + DEDUP_TTL_SECONDS, decision)
        while len(_dedup_cache) > DEDUP_MAX_ITEMS:
            _dedup_cache.popitem(last=False)
        return decision


def build_text_reply(message: InboundMessage, text: str, timestamp: int | None = None) -> bytes:
    root = ET.Element("xml")
    ET.SubElement(root, "ToUserName").text = message.from_user
    ET.SubElement(root, "FromUserName").text = message.to_user
    ET.SubElement(root, "CreateTime").text = str(timestamp or int(time.time()))
    ET.SubElement(root, "MsgType").text = "text"
    ET.SubElement(root, "Content").text = text
    return ET.tostring(root, encoding="utf-8", xml_declaration=False)


def clear_dedup_cache() -> None:
    """仅用于测试隔离。"""
    with _dedup_lock:
        _dedup_cache.clear()
