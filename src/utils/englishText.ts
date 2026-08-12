/** 将英文正文拆成句子（保留句末标点） */
export function splitSentences(text: string): string[] {
  const raw = (text || '').replace(/\r\n/g, '\n').trim()
  if (!raw) return []
  const parts = raw.split(/(?<=[.!?…])\s+|\n+/).map((s) => s.trim()).filter(Boolean)
  return parts.length ? parts : [raw]
}

/** 将句子拆成可点击词元（单词 / 标点 / 空白） */
export function tokenizeSentence(sentence: string): { text: string; isWord: boolean }[] {
  const tokens: { text: string; isWord: boolean }[] = []
  const re = /([A-Za-z][A-Za-z'-]*|[^\sA-Za-z]+|\s+)/g
  let m: RegExpExecArray | null
  while ((m = re.exec(sentence)) !== null) {
    const text = m[0]
    tokens.push({ text, isWord: /^[A-Za-z]/.test(text) })
  }
  return tokens
}

export function normalizeWord(word: string): string {
  return word.replace(/^[^A-Za-z']+|[^A-Za-z']+$/g, '').toLowerCase()
}
