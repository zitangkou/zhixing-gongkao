export const DUSHU_CATEGORIES = ['历史', '社会', '心理', '统计', '文学', '哲学', '其他'] as const

export const DUSHU_STATUS = [
  { value: 'reading', label: '在读' },
  { value: 'wishlist', label: '想读' },
  { value: 'done', label: '已读' },
] as const

export type DushuOutputField = { key: string; label: string; placeholder: string }

export type DushuModeMeta = {
  modeName: string
  chapterPlaceholder: string
  /** 轻提示：今天怎么记 */
  tip: string
  /** 唯一主字段的占位提示（按类型略有不同） */
  notePlaceholder: string
  fields: DushuOutputField[]
}

/** 统一极简：只记「今日留下」；类型只影响提示文案 */
export function modeForCategory(category: string): DushuModeMeta {
  const noteField = (placeholder: string): DushuOutputField[] => [
    { key: 'note', label: '今日留下', placeholder },
  ]

  switch (category) {
    case '历史':
      return {
        modeName: '历史',
        chapterPlaceholder: '章节/篇名，如：孝文本纪',
        tip: '人物、事件、一句启发，随意写几句即可。',
        notePlaceholder: '如：缇萦上书，文帝废肉刑——仁政可感化',
        fields: noteField('如：缇萦上书，文帝废肉刑——仁政可感化'),
      }
    case '社会':
      return {
        modeName: '社会',
        chapterPlaceholder: '章节/篇名',
        tip: '问题、规范词或一句可写进申论的话，任选留下。',
        notePlaceholder: '如：路径依赖——制度成本高时改革难推进',
        fields: noteField('如：路径依赖——制度成本高时改革难推进'),
      }
    case '心理':
      return {
        modeName: '心理',
        chapterPlaceholder: '概念/章节，如：锚定效应',
        tip: '概念用自己的话 + 一个例子就够。',
        notePlaceholder: '如：锚定效应——第一印象会拽住判断',
        fields: noteField('如：锚定效应——第一印象会拽住判断'),
      }
    case '统计':
      return {
        modeName: '统计',
        chapterPlaceholder: '概念/习题，如：标准差',
        tip: '概念干什么用、易错点，记一句即可。',
        notePlaceholder: '如：标准差——看数据有多散',
        fields: noteField('如：标准差——看数据有多散'),
      }
    case '文学':
      return {
        modeName: '文学',
        chapterPlaceholder: '章节/篇名',
        tip: '金句或感受，不用拆解。',
        notePlaceholder: '最触动的一句，或合上书后还记得的画面',
        fields: noteField('最触动的一句，或合上书后还记得的画面'),
      }
    case '哲学':
      return {
        modeName: '哲学',
        chapterPlaceholder: '章节，如：洞穴喻',
        tip: '作者主张什么、对你意味着什么，写一句。',
        notePlaceholder: '如：洞穴喻——走出习以为常的「真实」',
        fields: noteField('如：洞穴喻——走出习以为常的「真实」'),
      }
    default:
      return {
        modeName: '阅读',
        chapterPlaceholder: '章节（可选）',
        tip: '读完留下一句自己的话就好。',
        notePlaceholder: '今天留下什么？',
        fields: noteField('今天留下什么？'),
      }
  }
}

/** @deprecated 使用 modeForCategory */
export function outputFieldsForCategory(category: string): DushuOutputField[] {
  return modeForCategory(category).fields
}

export function categoryTip(category: string): string {
  return modeForCategory(category).tip
}

export function statusLabel(status: string): string {
  return DUSHU_STATUS.find((s) => s.value === status)?.label || status
}

/** 把新旧 output 合成一条可读正文（兼容旧多字段卡） */
export function flattenOutput(output?: Record<string, string> | null): string {
  if (!output) return ''
  if (output.note?.trim()) return output.note.trim()
  const preferred = [
    'takeaway', 'insight', 'viewpoint', 'quote', 'thesis', 'define', 'plain',
    'scene', 'point', 'why', 'problem', 'concept', 'moved', 'feeling',
  ]
  const parts: string[] = []
  const seen = new Set<string>()
  for (const k of preferred) {
    const v = (output[k] || '').trim()
    if (v && !seen.has(v)) {
      parts.push(v)
      seen.add(v)
    }
  }
  for (const [k, v] of Object.entries(output)) {
    const t = (v || '').trim()
    if (!t || k === 'note' || seen.has(t)) continue
    parts.push(t)
    seen.add(t)
  }
  return parts.join(' · ')
}

/** 每日卡展示：旧字段仍可读 */
export const OUTPUT_LABELS: Record<string, string> = {
  note: '今日留下',
  scene: '读了什么',
  point: '关键情节',
  why: '为何重要',
  takeaway: '带走一句',
  whoWhat: '谁/什么事',
  decision: '关键决定',
  reasonWord: '成败一词',
  reality: '现实联想',
  problem: '问题',
  skeleton: '论证骨架',
  terms: '规范词',
  insight: '启发',
  concept: '概念',
  define: '定义',
  lifeCase: '生活案例',
  policy: '政策联想',
  plain: '通俗解释',
  useCase: '用途/例题',
  pitfall: '易错点',
  quote: '金句',
  moved: '感动点',
  image: '挥之不去',
  feeling: '感受',
  thesis: '核心命题',
  concepts: '关键概念',
  argument: '论证路径',
  imply: '若成立则…',
  viewpoint: '观点',
}

export function outputLabel(key: string): string {
  return OUTPUT_LABELS[key] || key
}
