"""英文 TTS：优先 Microsoft edge-tts（神经语音），失败再回退有道。"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from urllib.parse import quote

import httpx


def _looks_mp3(raw: bytes) -> bool:
    if len(raw) < 64:
        return False
    return raw[:3] == b"ID3" or (raw[0] == 0xFF and (raw[1] & 0xE0) == 0xE0)


async def _edge_tts_bytes(text: str, accent: str) -> bytes | None:
    try:
        import edge_tts
    except ImportError:
        return None
    voice = "en-US-JennyNeural" if accent == "us" else "en-GB-SoniaNeural"
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        path = f.name
    try:
        await edge_tts.Communicate(text, voice).save(path)
        raw = Path(path).read_bytes()
        return raw if _looks_mp3(raw) else None
    finally:
        try:
            Path(path).unlink(missing_ok=True)
        except Exception:
            pass


def _youdao_bytes(text: str, accent: str) -> bytes | None:
    type_code = 2 if accent == "us" else 1
    url = f"https://dict.youdao.com/dictvoice?audio={quote(text)}&type={type_code}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.youdao.com/",
        "Accept": "*/*",
    }
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True, headers=headers)
        if resp.status_code != 200:
            return None
        raw = resp.content or b""
        return raw if _looks_mp3(raw) else None
    except Exception:
        return None


def synthesize_english(text: str, accent: str = "us") -> bytes | None:
    """同步生成英文 mp3 字节。"""
    cleaned = (text or "").strip()[:300]
    if not cleaned:
        return None
    if accent not in ("us", "uk"):
        accent = "us"

    # 1) edge-tts（音质更好，云上通常比有道更稳）
    try:
        raw = asyncio.run(_edge_tts_bytes(cleaned, accent))
        if raw:
            return raw
    except RuntimeError:
        try:
            loop = asyncio.new_event_loop()
            try:
                raw = loop.run_until_complete(_edge_tts_bytes(cleaned, accent))
                if raw:
                    return raw
            finally:
                loop.close()
        except Exception:
            pass
    except Exception:
        pass

    # 2) 有道词典（短词尚可，长句音质一般）
    return _youdao_bytes(cleaned, accent)
