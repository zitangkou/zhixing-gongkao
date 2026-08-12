<template>
  <view class="page">
    <view class="field">
      <text class="label">方向</text>
      <view class="chips">
        <text class="chip" :class="{ on: form.side === 'buy' }" @tap="form.side = 'buy'">买入</text>
        <text class="chip" :class="{ on: form.side === 'sell' }" @tap="form.side = 'sell'">卖出</text>
      </view>
    </view>

    <view class="field">
      <text class="label">标的名称 *</text>
      <nut-input v-model="form.name" placeholder="如：贵州茅台" />
    </view>
    <view class="field">
      <text class="label">代码（可选）</text>
      <nut-input v-model="form.symbol" placeholder="如：600519" />
    </view>
    <view class="row2">
      <view class="field half">
        <text class="label">日期</text>
        <nut-input v-model="form.tradeDate" placeholder="YYYY-MM-DD" />
      </view>
      <view class="field half">
        <text class="label">价格</text>
        <nut-input v-model="form.price" type="digit" placeholder="0" />
      </view>
    </view>
    <view class="field">
      <text class="label">仓位 %</text>
      <nut-input v-model="form.positionPct" type="digit" placeholder="如 15" />
    </view>

    <view class="field">
      <text class="label">原因标签</text>
      <view class="chips">
        <text
          v-for="r in reasonPresets"
          :key="r"
          class="chip"
          :class="{ on: form.reasons.includes(r) }"
          @tap="toggleReason(r)"
        >{{ r }}</text>
      </view>
    </view>
    <view class="field">
      <text class="label">原因说明</text>
      <nut-textarea v-model="form.reasonNote" :rows="3" placeholder="为什么买 / 为什么卖" />
    </view>
    <view class="field">
      <text class="label">风险</text>
      <nut-input v-model="form.riskNote" placeholder="主要风险点" />
    </view>
    <view class="row2">
      <view class="field half">
        <text class="label">止损</text>
        <nut-input v-model="form.stopLoss" type="digit" placeholder="0" />
      </view>
      <view class="field half">
        <text class="label">目标</text>
        <nut-input v-model="form.targetPrice" type="digit" placeholder="0" />
      </view>
    </view>

    <view class="divider">情绪与状态</view>
    <view class="field">
      <text class="label">今天状态</text>
      <view class="chips">
        <text
          v-for="e in emotions"
          :key="e.key"
          class="chip"
          :class="{ on: form.emotion === e.key }"
          @tap="form.emotion = e.key"
        >{{ e.label }}</text>
      </view>
    </view>
    <view class="field">
      <text class="label">信心 1～5</text>
      <view class="chips">
        <text
          v-for="n in 5"
          :key="n"
          class="chip"
          :class="{ on: form.confidence === n }"
          @tap="form.confidence = n"
        >{{ n }}</text>
      </view>
    </view>
    <view class="row2">
      <view class="field half">
        <text class="label">睡眠（小时）</text>
        <nut-input v-model="form.sleepHours" type="digit" placeholder="7" />
      </view>
      <view class="field half">
        <text class="label">工作压力 0～5</text>
        <nut-input v-model="form.workStress" type="digit" placeholder="0" />
      </view>
    </view>
    <view class="field">
      <text class="label">是否争吵 / 情绪冲突</text>
      <view class="chips">
        <text class="chip" :class="{ on: form.hadQuarrel === false }" @tap="form.hadQuarrel = false">否</text>
        <text class="chip" :class="{ on: form.hadQuarrel === true }" @tap="form.hadQuarrel = true">是</text>
      </view>
    </view>

    <view v-if="form.side === 'buy'" class="cooldown">
      <text class="cd-title">冷静期确认（买入必填）</text>
      <text class="cd-tip">冲动交易往往在确认前冷却。请逐项勾选：</text>
      <view
        v-for="(c, i) in checklist"
        :key="i"
        class="cd-item"
        :class="{ on: checks[i] }"
        @tap="checks[i] = !checks[i]"
      >{{ c }}</view>
    </view>

    <view class="field">
      <text class="label">是否按计划执行</text>
      <view class="chips">
        <text class="chip" :class="{ on: form.followedPlan === true }" @tap="form.followedPlan = true">是</text>
        <text class="chip" :class="{ on: form.followedPlan === false }" @tap="form.followedPlan = false">否</text>
        <text class="chip" :class="{ on: form.followedPlan === null }" @tap="form.followedPlan = null">未定</text>
      </view>
    </view>
    <view class="field">
      <text class="label">结果标记</text>
      <view class="chips">
        <text class="chip" :class="{ on: form.resultTag === '' }" @tap="form.resultTag = ''">待定</text>
        <text class="chip" :class="{ on: form.resultTag === 'win' }" @tap="form.resultTag = 'win'">盈利</text>
        <text class="chip" :class="{ on: form.resultTag === 'loss' }" @tap="form.resultTag = 'loss'">亏损</text>
      </view>
    </view>
    <view class="field">
      <text class="label">备注</text>
      <nut-textarea v-model="form.note" :rows="2" placeholder="可选" />
    </view>

    <nut-button type="primary" block :loading="saving" @click="onSave">保存日志</nut-button>
    <text v-if="id" class="del" @tap="onDelete">删除</text>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import Taro, { useDidShow, useRouter } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput, Textarea as NutTextarea } from '@nutui/nutui-taro'
import { api } from '@/api'
import { flushFormBeforeSave } from '@/utils/formFlush'
import { WEALTH_BUY_REASONS, WEALTH_SELL_REASONS } from '@/utils/wealth'
import { showConfirm, showToast } from '@/utils/platform'

definePageConfig({ navigationBarTitleText: '写投资日志' })

const emotions = [
  { key: 'calm', label: '冷静' },
  { key: 'happy', label: '开心' },
  { key: 'ok', label: '正常' },
  { key: 'anxious', label: '焦虑' },
  { key: 'angry', label: '生气' },
]

const checklist = [
  '写清了为什么买',
  '符合我的投资原则',
  '已有止损与目标',
  '若一周不能交易，我仍会买',
]

const router = useRouter()
const id = ref('')
/** 避免页面缓存导致重复 load；id 变化时强制重载 */
const loadedForId = ref<string | null>(null)
const saving = ref(false)
const checks = reactive([false, false, false, false])

const form = reactive({
  side: 'buy',
  name: '',
  symbol: '',
  tradeDate: new Date().toISOString().slice(0, 10),
  price: '',
  positionPct: '',
  reasons: [] as string[],
  reasonNote: '',
  riskNote: '',
  stopLoss: '',
  targetPrice: '',
  emotion: 'ok',
  confidence: 3,
  sleepHours: '',
  workStress: '',
  hadQuarrel: false,
  followedPlan: null as boolean | null,
  resultTag: '',
  note: '',
})

const reasonPresets = computed(() =>
  form.side === 'sell' ? WEALTH_SELL_REASONS : WEALTH_BUY_REASONS,
)

function toggleReason(r: string) {
  const i = form.reasons.indexOf(r)
  if (i >= 0) form.reasons.splice(i, 1)
  else form.reasons.push(r)
}

async function load() {
  const currentId = (router.params?.id || '').trim()
  if (loadedForId.value === currentId) return
  id.value = currentId
  if (!currentId) {
    loadedForId.value = ''
    return
  }
  const res = await api.getWealthJournal(currentId)
  if (res.code !== 0 || !res.data) return
  const d = res.data
  form.side = d.side
  form.name = d.name
  form.symbol = d.symbol || ''
  form.tradeDate = d.tradeDate
  form.price = d.price ? String(d.price) : ''
  form.positionPct = d.positionPct ? String(d.positionPct) : ''
  form.reasons = [...(d.reasons || [])]
  form.reasonNote = d.reasonNote || ''
  form.riskNote = d.riskNote || ''
  form.stopLoss = d.stopLoss ? String(d.stopLoss) : ''
  form.targetPrice = d.targetPrice ? String(d.targetPrice) : ''
  form.emotion = d.emotion || 'ok'
  form.confidence = d.confidence || 3
  form.sleepHours = d.sleepHours ? String(d.sleepHours) : ''
  form.workStress = d.workStress ? String(d.workStress) : ''
  form.hadQuarrel = !!d.hadQuarrel
  form.followedPlan = d.followedPlan
  form.resultTag = d.resultTag || ''
  form.note = d.note || ''
  if (d.checklistOk) checks.fill(true)
  loadedForId.value = currentId
}

async function onSave() {
  await flushFormBeforeSave()

  if (!form.name.trim()) {
    showToast('请填写标的名称')
    return
  }
  const checklistOk = form.side !== 'buy' || checks.every(Boolean)
  if (form.side === 'buy' && !checklistOk) {
    showToast('请完成冷静期确认清单')
    return
  }
  saving.value = true
  try {
    const payload = {
      side: form.side,
      name: form.name.trim(),
      symbol: form.symbol.trim(),
      tradeDate: form.tradeDate,
      price: Number(form.price) || 0,
      positionPct: Number(form.positionPct) || 0,
      reasons: [...form.reasons],
      reasonNote: form.reasonNote.trim(),
      riskNote: form.riskNote.trim(),
      stopLoss: Number(form.stopLoss) || 0,
      targetPrice: Number(form.targetPrice) || 0,
      emotion: form.emotion,
      confidence: form.confidence,
      sleepHours: Number(form.sleepHours) || 0,
      workStress: Number(form.workStress) || 0,
      hadQuarrel: form.hadQuarrel,
      followedPlan: form.followedPlan,
      checklistOk,
      resultTag: form.resultTag,
      note: form.note.trim(),
    }
    const res = id.value
      ? await api.updateWealthJournal(id.value, payload)
      : await api.createWealthJournal(payload)
    if (res.code !== 0) {
      showToast(res.message || '保存失败')
      return
    }
    showToast('已保存')
    setTimeout(() => Taro.navigateBack(), 400)
  } finally {
    saving.value = false
  }
}

async function onDelete() {
  if (!id.value) return
  const ok = await showConfirm('删除日志', '确定删除？')
  if (!ok) return
  await api.deleteWealthJournal(id.value)
  showToast('已删除')
  Taro.navigateBack()
}

useDidShow(() => {
  const currentId = (router.params?.id || '').trim()
  if (loadedForId.value !== currentId) {
    loadedForId.value = null
  }
  load()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';
.page { padding: 16px 16px 48px; }
.field { margin-bottom: 18px;
  .label { display: block; font-size: 13px; font-weight: 600; color: $text-secondary; margin-bottom: 8px; }
}
.row2 { display: flex; gap: 12px; .half { flex: 1; } }
.chips { display: flex; flex-wrap: wrap; gap: 8px;
  .chip {
    font-size: 13px; padding: 8px 12px; border-radius: 8px; background: $elevated; color: $text-secondary;
    &.on { background: $primary-light; color: $primary-color; font-weight: 600; }
  }
}
.divider {
  font-size: 14px; font-weight: 700; color: $text-primary; margin: 8px 0 16px;
  padding-top: 12px; border-top: 1px solid $border-color;
}
.cooldown {
  margin-bottom: 20px; padding: 14px; background: $elevated; border-radius: 8px;
  .cd-title { display: block; font-size: 14px; font-weight: 700; margin-bottom: 6px; }
  .cd-tip { display: block; font-size: 12px; color: $text-muted; margin-bottom: 12px; line-height: 1.4; }
  .cd-item {
    font-size: 13px; padding: 10px 12px; margin-bottom: 8px; border-radius: 8px;
    background: $card-bg; color: $text-secondary; border: 1px solid $border-color;
    &.on { border-color: $primary-color; color: $primary-color; font-weight: 600; }
  }
}
.del { display: block; text-align: center; padding: 16px; color: $danger; }
</style>
