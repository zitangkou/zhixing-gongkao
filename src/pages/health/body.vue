<template>
  <view class="page-body">
    <view class="tip">记录胃、湿气感、皮肤状态，便于和饮食睡眠对照。非诊断，持续加重请就医。</view>

    <view class="section">
      <ScoreRow label="胃舒适" v-model="stomach" :max="10" polarity="higher-better" tip="越高越舒服" low-label="很难受" high-label="很舒服" />
      <ScoreRow label="湿气感" v-model="dampness" :max="10" polarity="higher-worse" tip="困重、黏滞等主观感" />
      <ScoreRow label="湿疹/皮炎" v-model="skin" :max="10" polarity="higher-worse" tip="越高越严重" />
      <view class="checks">
        <text class="chk" :class="{ on: skinItch }" @tap="skinItch = !skinItch">明显瘙痒</text>
        <text class="chk" :class="{ on: skinFlare }" @tap="skinFlare = !skinFlare">今日加重</text>
      </view>
      <view class="num-row">
        <text class="label">散步分钟</text>
        <nut-input v-model="walkStr" type="number" placeholder="0" />
      </view>
      <nut-input v-model="bodyNote" placeholder="关联备注" />
      <nut-button type="primary" block :loading="saving" @click="onSave">保存</nut-button>
    </view>

    <view class="section">
      <text class="section-title">本周对照</text>
      <WeekDots label="胃" :points="weekStomach" />
      <WeekDots label="湿气" :points="weekDampness" />
      <WeekDots label="皮肤" :points="weekSkin" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useDidShow } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput } from '@nutui/nutui-taro'
import { api } from '@/api'
import type { HealthWeekPoint } from '@/types'
import ScoreRow from './ScoreRow.vue'
import WeekDots from './WeekDots.vue'
import { flushFormBeforeSave } from '@/utils/formFlush'
import { showToast } from '@/utils/platform'

definePageConfig({ navigationBarTitleText: '身体' })

const stomach = ref(0)
const dampness = ref(0)
const skin = ref(0)
const skinItch = ref(false)
const skinFlare = ref(false)
const walkStr = ref('')
const bodyNote = ref('')
const saving = ref(false)
const weekStomach = ref<HealthWeekPoint[]>([])
const weekDampness = ref<HealthWeekPoint[]>([])
const weekSkin = ref<HealthWeekPoint[]>([])

async function load() {
  const res = await api.getHealthOverview()
  if (res.code !== 0 || !res.data) return
  weekStomach.value = res.data.weekStomach
  weekDampness.value = res.data.weekDampness
  weekSkin.value = res.data.weekSkin
  const log = res.data.todayLog
  if (log) {
    stomach.value = log.stomach
    dampness.value = log.dampness
    skin.value = log.skin
    skinItch.value = log.skinItch
    skinFlare.value = log.skinFlare
    walkStr.value = log.walkMin ? String(log.walkMin) : ''
    bodyNote.value = log.bodyNote
  }
}

async function onSave() {
  await flushFormBeforeSave()

  saving.value = true
  try {
    const res = await api.upsertHealthDaily({
      stomach: stomach.value,
      dampness: dampness.value,
      skin: skin.value,
      skinItch: skinItch.value,
      skinFlare: skinFlare.value,
      walkMin: Number(walkStr.value) || 0,
      bodyNote: bodyNote.value,
    })
    if (res.code === 0) {
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
.page-body { @include page-padding; }
.tip { font-size: 12px; color: $text-muted; line-height: 1.5; margin-bottom: 12px; }
.section { @include card; padding: 14px; }
.section-title { display: block; font-size: 14px; font-weight: 700; margin-bottom: 10px; }
.checks { display: flex; gap: 8px; margin: 8px 0; flex-wrap: wrap; }
.chk { font-size: 12px; padding: 4px 10px; border-radius: 8px; background: $chip-bg;
  &.on { background: $primary-color; color: $on-primary; }
}
.num-row { display: flex; align-items: center; gap: 8px; margin: 8px 0;
  .label { width: 80px; font-size: 12px; color: $text-secondary; }
}
</style>
