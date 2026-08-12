<template>
  <view class="page-habits">
    <view class="section">
      <text class="section-title">今日习惯</text>
      <ScoreRow label="心情" v-model="mood" :max="10" polarity="higher-better" tip="今天整体情绪" />
      <ScoreRow label="睡眠质量" v-model="sleepQuality" :max="5" polarity="higher-better" tip="昨晚睡得怎样" />
      <view class="checks">
        <text class="chk" :class="{ on: sleepBefore23 }" @tap="sleepBefore23 = !sleepBefore23">23点前睡</text>
        <text class="chk" :class="{ on: weekendLieFlat }" @tap="weekendLieFlat = !weekendLieFlat">周末久躺</text>
      </view>
      <nut-input v-model="habitNote" placeholder="作息备注（可选）" />
    </view>

    <view class="section">
      <text class="section-title">饮食清单</text>
      <text class="sub">早/午/晚勾选后可记餐后自评与感受，便于复盘</text>
      <view v-for="slot in mealSlots" :key="slot.key" class="meal">
        <view class="meal-head">
          <text class="chk" :class="{ on: meals[slot.key].eaten }" @tap="toggleMeal(slot.key)">{{ slot.label }}</text>
          <text
            class="chk sm"
            :class="{ on: meals[slot.key].light }"
            @tap="meals[slot.key].light = !meals[slot.key].light"
          >清淡</text>
        </view>
        <template v-if="meals[slot.key].eaten || slot.key === 'snack'">
          <nut-input v-model="meals[slot.key].items" :placeholder="slot.ph" />
          <view v-if="slot.key !== 'snack' || meals[slot.key].eaten" class="after-meal">
            <text class="label mt">餐后自评</text>
            <view class="checks">
              <text
                v-for="s in scoreOpts"
                :key="s.v"
                class="chk sm"
                :class="{ on: meals[slot.key].score === s.v }"
                @tap="meals[slot.key].score = meals[slot.key].score === s.v ? 0 : s.v"
              >{{ s.l }}</text>
            </view>
            <nut-input
              v-model="meals[slot.key].feel"
              placeholder="感受：饱胀、困倦、清爽、反酸…"
            />
          </view>
        </template>
      </view>
      <view class="water">
        <text class="label">饮水（杯）</text>
        <view class="water-row">
          <text class="chk sm" @tap="meals.waterCups = Math.max(0, meals.waterCups - 1)">−</text>
          <text class="num">{{ meals.waterCups }}</text>
          <text class="chk sm" @tap="meals.waterCups += 1">+</text>
        </view>
      </view>
      <nut-input v-model="meals.note" placeholder="饮食备注，如：加班外卖、宵夜" />
    </view>

    <view class="section">
      <text class="section-title">大小便</text>
      <view class="water">
        <text class="label">排便次数</text>
        <view class="water-row">
          <text class="chk sm" @tap="stool.times = Math.max(0, stool.times - 1)">−</text>
          <text class="num">{{ stool.times }}</text>
          <text class="chk sm" @tap="stool.times += 1">+</text>
        </view>
      </view>
      <text class="label mt">性状</text>
      <view class="checks">
        <text
          v-for="f in formOpts"
          :key="f.v"
          class="chk"
          :class="{ on: stool.form === f.v }"
          @tap="stool.form = f.v"
        >{{ f.l }}</text>
      </view>
      <text class="label mt">顺畅度</text>
      <view class="checks">
        <text
          v-for="e in easeOpts"
          :key="e.v"
          class="chk"
          :class="{ on: stool.ease === e.v }"
          @tap="stool.ease = e.v"
        >{{ e.l }}</text>
      </view>
      <view class="checks mt">
        <text class="chk" :class="{ on: stool.urineOk }" @tap="stool.urineOk = !stool.urineOk">
          {{ stool.urineOk ? '小便正常' : '小便不适' }}
        </text>
      </view>
      <nut-input v-model="stool.note" placeholder="备注（可选）" />
    </view>

    <nut-button type="primary" block :loading="saving" @click="onSave">保存</nut-button>

    <view v-if="assessment" class="section assess">
      <text class="section-title">即时评估</text>
      <text class="assess-body">{{ assessment }}</text>
    </view>

    <view class="section">
      <text class="section-title">本周心情</text>
      <WeekDots label="" :points="weekMood" />
    </view>

    <view class="section">
      <text class="section-title">本周记录</text>
      <view v-if="!logs.length" class="empty">暂无记录</view>
      <view v-for="log in logs" :key="log.id" class="log">
        <text class="date">{{ log.logDate }}</text>
        <text class="meta">心情 {{ log.mood || '—' }} · 睡眠 {{ log.sleepQuality || '—' }}</text>
        <text class="flags">{{ mealSummary(log) }}</text>
        <text v-if="log.habitNote" class="note">{{ log.habitNote }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useDidShow } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput } from '@nutui/nutui-taro'
import { api } from '@/api'
import type { HealthDailyLog, HealthMealSlot, HealthMeals, HealthStool, HealthWeekPoint } from '@/types'
import ScoreRow from './ScoreRow.vue'
import WeekDots from './WeekDots.vue'
import { flushFormBeforeSave } from '@/utils/formFlush'
import { showToast } from '@/utils/platform'

definePageConfig({ navigationBarTitleText: '习惯 · 饮食排便' })

type MealKey = 'breakfast' | 'lunch' | 'dinner' | 'snack'

function emptySlot(): HealthMealSlot {
  return { eaten: false, items: '', light: false, time: '', score: 0, feel: '' }
}

const mood = ref(0)
const sleepQuality = ref(0)
const sleepBefore23 = ref(false)
const weekendLieFlat = ref(false)
const habitNote = ref('')
const saving = ref(false)
const assessment = ref('')
const weekMood = ref<HealthWeekPoint[]>([])
const logs = ref<HealthDailyLog[]>([])

const meals = reactive<HealthMeals>({
  breakfast: emptySlot(),
  lunch: emptySlot(),
  dinner: emptySlot(),
  snack: emptySlot(),
  waterCups: 0,
  note: '',
})

const stool = reactive<HealthStool>({
  times: 0,
  form: '',
  ease: '',
  urineOk: true,
  note: '',
})

const mealSlots: { key: MealKey; label: string; ph: string }[] = [
  { key: 'breakfast', label: '早餐', ph: '吃了什么' },
  { key: 'lunch', label: '午餐', ph: '吃了什么' },
  { key: 'dinner', label: '晚餐', ph: '吃了什么' },
  { key: 'snack', label: '加餐/宵夜', ph: '有则填写' },
]

const formOpts = [
  { v: 'hard', l: '干硬' },
  { v: 'normal', l: '成形' },
  { v: 'soft', l: '偏软' },
  { v: 'loose', l: '稀溏' },
]

const easeOpts = [
  { v: 'hard', l: '费力' },
  { v: 'smooth', l: '顺畅' },
  { v: 'urgent', l: '急迫' },
]

const scoreOpts = [
  { v: 1, l: '很差' },
  { v: 2, l: '偏差' },
  { v: 3, l: '一般' },
  { v: 4, l: '较好' },
  { v: 5, l: '很好' },
]

function toggleMeal(key: MealKey) {
  meals[key].eaten = !meals[key].eaten
  if (!meals[key].eaten) {
    meals[key].score = 0
    meals[key].feel = ''
  }
}

function applyMeals(m?: HealthMeals | null) {
  if (!m) return
  ;(['breakfast', 'lunch', 'dinner', 'snack'] as MealKey[]).forEach((k) => {
    Object.assign(meals[k], emptySlot(), m[k] || {})
  })
  meals.waterCups = m.waterCups || 0
  meals.note = m.note || ''
}

function applyStool(s?: HealthStool | null) {
  if (!s) return
  Object.assign(stool, {
    times: s.times || 0,
    form: s.form || '',
    ease: s.ease || '',
    urineOk: s.urineOk !== false,
    note: s.note || '',
  })
}

function mealSummary(log: HealthDailyLog) {
  const m = log.meals
  if (!m) {
    return `${log.mealsRegular ? '规律餐 ' : ''}${log.mealsLight ? '清淡 ' : ''}${log.weekendLieFlat ? '久躺' : ''}`
  }
  const n = [m.breakfast, m.lunch, m.dinner].filter((x) => x?.eaten).length
  const felt = [m.breakfast, m.lunch, m.dinner].filter((x) => x?.eaten && (x.score || x.feel)).length
  const st = log.stool?.times != null ? `便${log.stool.times}次` : ''
  return `正餐${n}/3${felt ? ` · 自评${felt}` : ''} · 水${m.waterCups || 0}杯${st ? ` · ${st}` : ''}`
}

async function load() {
  const [ov, week] = await Promise.all([api.getHealthOverview(), api.listHealthDailyWeek()])
  if (ov.code === 0 && ov.data) {
    weekMood.value = ov.data.weekMood
    const log = ov.data.todayLog
    if (log) {
      mood.value = log.mood
      sleepQuality.value = log.sleepQuality
      sleepBefore23.value = log.sleepBefore23
      weekendLieFlat.value = log.weekendLieFlat
      habitNote.value = log.habitNote
      applyMeals(log.meals)
      applyStool(log.stool)
      assessment.value = log.bodyAssessment || log.review?.bodyAssessment || ''
    }
  }
  if (week.code === 0 && week.data) logs.value = [...week.data].reverse()
}

async function onSave() {
  await flushFormBeforeSave()

  saving.value = true
  try {
    const payload = {
      mood: mood.value,
      sleepQuality: sleepQuality.value,
      sleepBefore23: sleepBefore23.value,
      weekendLieFlat: weekendLieFlat.value,
      habitNote: habitNote.value,
      meals: {
        breakfast: { ...meals.breakfast },
        lunch: { ...meals.lunch },
        dinner: { ...meals.dinner },
        snack: { ...meals.snack },
        waterCups: meals.waterCups,
        note: meals.note,
      },
      stool: { ...stool },
    }
    const res = await api.upsertHealthDaily(payload)
    if (res.code === 0 && res.data) {
      assessment.value = res.data.bodyAssessment || ''
      showToast('已保存', 'success')
      await load()
    } else showToast(res.message || '失败', 'error')
  } finally {
    saving.value = false
  }
}

useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';
.page-habits { @include page-padding; padding-bottom: 40px; }
.section { @include card; padding: 14px; margin-bottom: 12px; }
.section-title { display: block; font-size: 14px; font-weight: 700; margin-bottom: 6px; }
.sub { display: block; font-size: 11px; color: $text-muted; margin-bottom: 10px; }
.checks { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; }
.chk {
  @include hit-target(44px);
  font-size: 12px;
  padding: 0 12px;
  border-radius: 8px;
  background: $chip-bg;
  &.on { background: $primary-color; color: $on-primary; }
  &.sm { padding: 0 10px; font-size: 11px; }
}
.meal { margin-bottom: 10px;
  .meal-head { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
}
.after-meal { margin-top: 4px; padding: 8px 0 2px; border-top: 1px dashed $border-color; }
.water { display: flex; justify-content: space-between; align-items: center; margin: 8px 0;
  .label { font-size: 13px; }
  .water-row { display: flex; align-items: center; gap: 10px; }
  .num { font-size: 16px; font-weight: 700; min-width: 24px; text-align: center; }
}
.label { display: block; font-size: 12px; color: $text-secondary; }
.mt { margin-top: 8px; }
.assess { background: $primary-faint;
  .assess-body { display: block; font-size: 13px; line-height: 1.55; color: $text-secondary; }
}
.empty { font-size: 12px; color: $text-muted; }
.log { padding: 10px 0; border-bottom: 1px solid $border-color;
  .date { display: block; font-size: 13px; font-weight: 600; }
  .meta, .flags, .note { display: block; font-size: 11px; color: $text-muted; margin-top: 2px; }
  .note { color: $text-secondary; }
}
</style>
