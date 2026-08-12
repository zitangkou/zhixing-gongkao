/** 金额展示：元，保留最多两位 */
export function formatYuan(n: number | undefined | null): string {
  const v = Number(n || 0)
  return v.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

export const LEDGER_EXPENSE_CATEGORIES_FALLBACK = [
  '餐饮',
  '交通',
  '日用',
  '住房',
  '学习',
  '医疗',
  '娱乐',
  '人情',
  '其他',
]

export const LEDGER_REPAY_METHODS_FALLBACK = ['微信', '支付宝', '现金', '银行转账', '其他']
