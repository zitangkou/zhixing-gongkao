import Taro from '@tarojs/taro'
import { api } from '@/api'
import { getPlatform, showToast } from '@/utils/platform'

let audioCtx: ReturnType<typeof Taro.createInnerAudioContext> | null = null
let htmlAudio: HTMLAudioElement | null = null
let blobUrl: string | null = null

function cleanupBlob() {
  if (blobUrl) {
    try { URL.revokeObjectURL(blobUrl) } catch { /* ignore */ }
    blobUrl = null
  }
}

function pickEnglishVoice(): SpeechSynthesisVoice | null {
  if (typeof window === 'undefined' || !window.speechSynthesis) return null
  const voices = window.speechSynthesis.getVoices() || []
  const prefer = [
    (v: SpeechSynthesisVoice) => /en-US/i.test(v.lang) && /Google|Microsoft|Samantha|Jenny|Neural/i.test(v.name),
    (v: SpeechSynthesisVoice) => /en-US/i.test(v.lang),
    (v: SpeechSynthesisVoice) => /^en/i.test(v.lang),
  ]
  for (const fn of prefer) {
    const hit = voices.find(fn)
    if (hit) return hit
  }
  return voices[0] || null
}

function speakWithWebSpeech(text: string): boolean {
  if (typeof window === 'undefined') return false
  const synth = window.speechSynthesis
  if (!synth) return false
  try {
    synth.cancel()
    const u = new SpeechSynthesisUtterance(text)
    u.lang = 'en-US'
    u.rate = 0.92
    const voice = pickEnglishVoice()
    if (voice) u.voice = voice
    synth.speak(u)
    return true
  } catch {
    return false
  }
}

function stopAll() {
  if (audioCtx) {
    try { audioCtx.stop() } catch { /* ignore */ }
    try { audioCtx.destroy() } catch { /* ignore */ }
    audioCtx = null
  }
  if (htmlAudio) {
    try { htmlAudio.pause() } catch { /* ignore */ }
    htmlAudio = null
  }
  cleanupBlob()
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    try { window.speechSynthesis.cancel() } catch { /* ignore */ }
  }
}

async function playViaFetch(src: string): Promise<boolean> {
  try {
    const res = await fetch(src)
    const ctype = (res.headers.get('content-type') || '').toLowerCase()
    if (!res.ok || !ctype.includes('audio')) return false
    const buf = await res.arrayBuffer()
    if (buf.byteLength < 64) return false
    cleanupBlob()
    blobUrl = URL.createObjectURL(new Blob([buf], { type: 'audio/mpeg' }))
    htmlAudio = new Audio(blobUrl)
    await htmlAudio.play()
    return true
  } catch {
    return false
  }
}

function playViaInnerAudio(src: string): Promise<boolean> {
  return new Promise((resolve) => {
    audioCtx = Taro.createInnerAudioContext()
    audioCtx.src = src
    let settled = false
    const done = (ok: boolean) => {
      if (settled) return
      settled = true
      resolve(ok)
    }
    audioCtx.onCanplay(() => {
      try { audioCtx?.play() } catch { done(false) }
    })
    audioCtx.onPlay(() => done(true))
    audioCtx.onError(() => done(false))
    // 部分端 onCanplay 不触发，直接 play
    try { audioCtx.play() } catch { done(false) }
    setTimeout(() => done(false), 4000)
  })
}

/** 播放英文发音：服务端 TTS（edge-tts/有道）→ H5 Web Speech 兜底 */
export async function playPronounce(text: string, accent: 'us' | 'uk' = 'us') {
  const t = (text || '').trim()
  if (!t) return

  stopAll()
  const src = api.pronounceUrl(t.slice(0, 300), accent)
  const isH5 = getPlatform() === 'h5'

  if (isH5 && typeof fetch !== 'undefined' && typeof Audio !== 'undefined') {
    const ok = await playViaFetch(src)
    if (ok) return
    if (speakWithWebSpeech(t)) return
    showToast('发音暂不可用', 'error')
    return
  }

  const ok = await playViaInnerAudio(src)
  if (!ok && isH5 && speakWithWebSpeech(t)) return
  if (!ok) showToast('发音暂不可用', 'error')
}
