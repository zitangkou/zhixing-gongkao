"""语音转文字（ASR）：默认关闭云识别，配置后可切换阿里云/腾讯云。

环境变量：
  ASR_PROVIDER=none|aliyun|tencent   # 默认 none（前端走免费 Web Speech）
  ASR_PREFER_CLOUD=true              # 云可用时是否优先云（默认 false，仍以免费为主）
  # 阿里云一句话识别（可选）
  ALIYUN_ASR_APPKEY=
  ALIYUN_ASR_TOKEN=                  # 或用 AK 自行换 token，这里直接填临时/长期 token
  # 腾讯云（可选，预留）
  TENCENT_ASR_SECRET_ID=
  TENCENT_ASR_SECRET_KEY=
  TENCENT_ASR_APP_ID=
"""
from __future__ import annotations

import base64
import json
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def asr_status() -> dict[str, Any]:
    s = get_settings()
    provider = (s.asr_provider or "none").strip().lower()
    cloud = provider in ("aliyun", "tencent") and _cloud_ready(provider)
    prefer = bool(s.asr_prefer_cloud) and cloud
    if prefer:
        hint = f"云识别优先（{provider}）"
    elif cloud:
        hint = f"已配置云 ASR（{provider}），当前仍优先免费浏览器识别；设 ASR_PREFER_CLOUD=true 可切换"
    else:
        hint = "浏览器语音识别（免费）；配置 ASR_PROVIDER=aliyun|tencent 可启用云识别"
    return {
        "provider": provider if cloud else "webspeech",
        "cloudAvailable": cloud,
        "preferCloud": prefer,
        "hint": hint,
    }


def _cloud_ready(provider: str) -> bool:
    s = get_settings()
    if provider == "aliyun":
        return bool(s.aliyun_asr_appkey and s.aliyun_asr_token)
    if provider == "tencent":
        return bool(s.tencent_asr_secret_id and s.tencent_asr_secret_key and s.tencent_asr_app_id)
    return False


def transcribe_audio(data: bytes, content_type: str = "audio/webm", filename: str = "speech.webm") -> str:
    s = get_settings()
    provider = (s.asr_provider or "none").strip().lower()
    if provider == "aliyun":
        return _transcribe_aliyun(data, content_type, filename)
    if provider == "tencent":
        return _transcribe_tencent(data, content_type, filename)
    raise ValueError("未配置云 ASR。请设置 ASR_PROVIDER=aliyun|tencent 及相关密钥；或继续使用前端免费语音识别。")


def _transcribe_aliyun(data: bytes, content_type: str, filename: str) -> str:
    """阿里云智能语音一句话识别（REST）。

    文档：https://help.aliyun.com/document_detail/92131.html
    需要 APPKEY + Token；音频建议 16k 单声道，webm/opus 部分账号需转码。
    """
    s = get_settings()
    appkey = s.aliyun_asr_appkey
    token = s.aliyun_asr_token
    # 优先尝试 flash 识别接口；失败给出明确提示
    # 这里使用通用 HTTP 一句话接口（PCM/WAV 最稳）；webm 可能不被接受
    url = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr"
    params = {
        "appkey": appkey,
        "format": "wav" if "wav" in (content_type or "") or filename.endswith(".wav") else "pcm",
        "sample_rate": 16000,
        "enable_punctuation_prediction": "true",
        "enable_inverse_text_normalization": "true",
    }
    # webm 时改走文件识别较复杂；先尝试以 binary 提交，失败则提示转码
    headers = {
        "X-NLS-Token": token,
        "Content-Type": "application/octet-stream",
    }
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(url, params=params, headers=headers, content=data)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if r.status_code != 200:
            raise ValueError(body.get("message") or f"阿里云 ASR HTTP {r.status_code}")
        status = body.get("status")
        if status not in (0, 20000000, None) and body.get("result") is None:
            # 部分返回 status=20000000 成功
            if not body.get("result"):
                raise ValueError(body.get("message") or json.dumps(body, ensure_ascii=False)[:200])
        text = (body.get("result") or body.get("text") or "").strip()
        if not text:
            raise ValueError(
                "阿里云未识别出文字。若上传的是 webm，请改用 16k WAV/PCM，或暂时使用浏览器免费识别。"
            )
        return text
    except ValueError:
        raise
    except Exception as e:
        logger.exception("aliyun asr failed")
        raise ValueError(f"阿里云识别失败：{e}") from e


def _transcribe_tencent(data: bytes, content_type: str, filename: str) -> str:
    """腾讯云一句话识别（预留骨架）。

    完整签名较繁琐，这里提供可运行的最小实现：若未装 tencentcloud-sdk，返回配置提示。
    """
    s = get_settings()
    try:
        from tencentcloud.common import credential
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
        from tencentcloud.asr.v20190614 import asr_client, models
    except ImportError as e:
        raise ValueError(
            "未安装 tencentcloud-sdk-python。可 pip install tencentcloud-sdk-python，"
            "或暂用浏览器免费识别 / 改用阿里云。"
        ) from e

    cred = credential.Credential(s.tencent_asr_secret_id, s.tencent_asr_secret_key)
    http_profile = HttpProfile(endpoint="asr.tencentcloudapi.com")
    client_profile = ClientProfile(httpProfile=http_profile)
    client = asr_client.AsrClient(cred, "ap-guangzhou", client_profile)
    req = models.SentenceRecognitionRequest()
    # VoiceFormat: 0 wav/pcm；webm 可能需 16 等，不稳定时前端走 webspeech
    voice_format = 0 if ("wav" in content_type or filename.endswith(".wav")) else 16
    params = {
        "ProjectId": 0,
        "SubServiceType": 2,
        "EngSerViceType": "16k_zh",
        "SourceType": 1,
        "VoiceFormat": voice_format,
        "UsrAudioKey": filename,
        "Data": base64.b64encode(data).decode("ascii"),
        "DataLen": len(data),
    }
    req.from_json_string(json.dumps(params))
    try:
        resp = client.SentenceRecognition(req)
        text = (getattr(resp, "Result", None) or "").strip()
        if not text:
            raise ValueError("腾讯云未识别出文字")
        return text
    except ValueError:
        raise
    except Exception as e:
        logger.exception("tencent asr failed")
        raise ValueError(f"腾讯云识别失败：{e}") from e
