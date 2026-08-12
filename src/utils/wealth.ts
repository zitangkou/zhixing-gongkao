export const WEALTH_EMOTION_LABEL: Record<string, string> = {
  calm: '冷静',
  happy: '开心',
  ok: '正常',
  anxious: '焦虑',
  angry: '生气',
}

export const WEALTH_LAYER_LABELS: Record<number, string> = {
  1: '硬规则（不能违反）',
  2: '股票原则',
  3: '买入条件',
  4: '卖出条件',
}

export const WEALTH_BUY_REASONS = ['行业趋势', '基本面', '资金流入', '估值合理', '技术形态', '长期持有']
export const WEALTH_SELL_REASONS = ['达到目标', '逻辑失效', '资金需求', '情绪化', '止损', '减仓']

export function formatYuan(n: number | undefined | null) {
  const v = Number(n || 0)
  return v.toLocaleString('zh-CN', { maximumFractionDigits: 0 })
}

export function emotionLabel(e: string) {
  return WEALTH_EMOTION_LABEL[e] || e
}
