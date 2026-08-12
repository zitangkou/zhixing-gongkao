/**
 * DJ 音标 → TTS 可朗读的近似发音文本
 *
 * 有道 TTS 不能直接读音标符号（如 /iː/），
 * 需要用近似发音的字母组合让 TTS 发出接近的音。
 */
const PRONOUNCE_MAP: Record<string, string> = {
  // 单元音
  '/iː/': 'ee',
  '/ɪ/': 'ih',
  '/e/': 'eh',
  '/æ/': 'ah',
  '/ɜː/': 'er',
  '/ə/': 'uh',
  '/ʌ/': 'uh',
  '/uː/': 'oo',
  '/ʊ/': 'uh',
  '/ɔː/': 'aw',
  '/ɒ/': 'oh',
  '/ɑː/': 'ah',
  // 双元音
  '/eɪ/': 'ay',
  '/aɪ/': 'eye',
  '/ɔɪ/': 'boy',
  '/aʊ/': 'now',
  '/əʊ/': 'oh',
  '/ɪə/': 'ear',
  '/eə/': 'air',
  '/ʊə/': 'tour',
  // 辅音 — 用辅音+短元音的组合，TTS 能发出接近的辅音音色
  '/p/': 'pa',
  '/b/': 'ba',
  '/t/': 'ta',
  '/d/': 'da',
  '/k/': 'ka',
  '/ɡ/': 'ga',
  '/f/': 'fa',
  '/v/': 'va',
  '/θ/': 'thaw',
  '/ð/': 'they',
  '/s/': 'sa',
  '/z/': 'za',
  '/ʃ/': 'she',
  '/ʒ/': 'measure',
  '/h/': 'ha',
  '/tʃ/': 'cha',
  '/dʒ/': 'ja',
  '/m/': 'ma',
  '/n/': 'na',
  '/ŋ/': 'sing',
  '/l/': 'la',
  '/r/': 'ra',
  '/j/': 'ya',
  '/w/': 'wa',
  '/ts/': 'cats',
  '/dz/': 'beds',
  '/tr/': 'tra',
  '/dr/': 'dra',
}

/**
 * 根据音标符号返回 TTS 可朗读的近似发音文本
 */
export function phoneticPronounceText(symbol: string): string {
  return PRONOUNCE_MAP[symbol] || symbol.replace(/\//g, '')
}
