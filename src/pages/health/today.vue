<template>
  <view class="page-today">
    <view class="section">
      <text class="section-title">今日任务（阶段{{ phase }}）</text>
      <view v-for="t in tasks" :key="t.id" class="task" @tap="toggleTask(t.id)">
        <text class="check">{{ doneSet.has(t.id) ? '✓' : '○' }}</text>
        <view class="task-body">
          <text class="task-title">{{ t.title }}{{ t.optional ? '（可选）' : '' }}</text>
          <text class="task-detail">{{ t.detail }}</text>
        </view>
      </view>
    </view>

    <view class="section">
      <text class="section-title">习惯</text>
      <ScoreRow label="心情" v-model="form.mood" :max="10" polarity="higher-better" tip="今天整体情绪" />
      <ScoreRow label="睡眠质量" v-model="form.sleepQuality" :max="5" polarity="higher-better" tip="昨晚睡得怎样" />
      <view class="checks">
        <text class="chk" :class="{ on: form.sleepBefore23 }" @tap="form.sleepBefore23 = !form.sleepBefore23">23点前睡</text>
        <text class="chk" :class="{ on: form.mealsRegular }" @tap="form.mealsRegular = !form.mealsRegular">三餐规律</text>
        <text class="chk" :class="{ on: form.mealsLight }" @tap="form.mealsLight = !form.mealsLight">七分饱少油少甜</text>
        <text class="chk" :class="{ on: form.weekendLieFlat }" @tap="form.weekendLieFlat = !form.weekendLieFlat">周末久躺</text>
      </view>
      <nut-input v-model="form.habitNote" placeholder="饮食/作息备注（可选）" />
    </view>

    <view class="section">
      <text class="section-title">身体</text>
      <ScoreRow label="胃舒适" v-model="form.stomach" :max="10" polarity="higher-better" tip="越高越舒服" low-label="很难受" high-label="很舒服" />
      <ScoreRow label="湿气感" v-model="form.dampness" :max="10" polarity="higher-worse" tip="困重、黏滞等主观感" />
      <ScoreRow label="皮肤/湿疹" v-model="form.skin" :max="10" polarity="higher-worse" tip="越高越严重" />
      <view class="checks">
        <text class="chk" :class="{ on: form.skinItch }" @tap="form.skinItch = !form.skinItch">明显瘙痒</text>
        <text class="chk" :class="{ on: form.skinFlare }" @tap="form.skinFlare = !form.skinFlare">今日加重</text>
      </view>
      <view class="num-row">
        <text class="label">散步分钟</text>
        <nut-input v-model="walkStr" type="number" placeholder="0" />
      </view>
      <nut-input v-model="form.bodyNote" placeholder="关联备注，如睡眠差后皮肤痒" />
    </view>

    <view class="section">
      <text class="section-title">心理</text>
      <ScoreRow label="心理能量" v-model="form.energy" :max="10" polarity="higher-better" tip="想不想与外界打交道" low-label="很低" high-label="很足" />
      <ScoreRow label="焦虑" v-model="form.anxiety" :max="10" polarity="higher-worse" tip="紧张、担忧的程度" />
      <view class="num-row">
        <text class="label">主动交流次数</text>
        <nut-input v-model="socialStr" type="number" placeholder="0" />
      </view>
      <view class="num-row">
        <text class="label">学习分钟</text>
        <nut-input v-model="studyStr" type="number" placeholder="0" />
      </view>
    </view>

    <nut-button type="primary" block :loading="saving" @click="onSave">保存今日</nut-button>
    <nut-button block class="ghost" @click="goReview">去晚间复盘 / CBT</nut-button>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput } from '@nutui/nutui-taro'
import { api } from '@/api'
import type { HealthTask } from '@/types'
import ScoreRow from './ScoreRow.vue'
import { flushFormBeforeSave } from '@/utils/formFlush'
import { showToast } from '@/utils/platform'

definePageConfig({ navigationBarTitleText: '今日打卡' })

const tasks = ref<HealthTask[]>([])
const phase = ref(1)
const saving = ref(false)
const form = reactive({
  mood: 0,
  sleepQuality: 0,
  sleepBefore23: false,
  mealsRegular: false,
  mealsLight: false,
  weekendLieFlat: false,
  habitNote: '',
  stomach: 0,
  dampness: 0,
  skin: 0,
  skinItch: false,
  skinFlare: false,
  bodyNote: '',
  energy: 0,
  anxiety: 0,
  tasksDone: [] as string[],
})
const walkStr = ref('')
const socialStr = ref('')
const studyStr = ref('')

const doneSet = computed(() => new Set(form.tasksDone))

function toggleTask(id: string) {
  const i = form.tasksDone.indexOf(id)
  if (i >= 0) form.tasksDone.splice(i, 1)
  else form.tasksDone.push(id)
}

function goReview() {
  Taro.navigateTo({ url: '/pages/health/review' })
}

async function load() {
  const ov = await api.getHealthOverview()
  if (ov.code === 0 && ov.data) {
    phase.value = ov.data.phase.phase
    tasks.value = ov.data.todayTasks || []
    const log = ov.data.todayLog
    if (log) {
      form.mood = log.mood
      form.sleepQuality = log.sleepQuality
      form.sleepBefore23 = log.sleepBefore23
      form.mealsRegular = log.mealsRegular
      form.mealsLight = log.mealsLight
      form.weekendLieFlat = log.weekendLieFlat
      form.habitNote = log.habitNote
      form.stomach = log.stomach
      form.dampness = log.dampness
      form.skin = log.skin
      form.skinItch = log.skinItch
      form.skinFlare = log.skinFlare
      form.bodyNote = log.bodyNote
      form.energy = log.energy
      form.anxiety = log.anxiety
      form.tasksDone = [...(log.tasksDone || [])]
      walkStr.value = log.walkMin ? String(log.walkMin) : ''
      socialStr.value = log.socialCount ? String(log.socialCount) : ''
      studyStr.value = log.studyMin ? String(log.studyMin) : ''
    }
  }
}

async function onSave() {
  await flushFormBeforeSave()

  saving.value = true
  try {
    const res = await api.upsertHealthDaily({
      ...form,
      walkMin: Number(walkStr.value) || 0,
      socialCount: Number(socialStr.value) || 0,
      studyMin: Number(studyStr.value) || 0,
      tasksDone: form.tasksDone,
    })
    if (res.code === 0) showToast('已保存', 'success')
    else showToast(res.message || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';
.page-today { @include page-padding; padding-bottom: 40px; }
.section { @include card; padding: 14px; margin-bottom: 12px; }
.section-title { display: block; font-size: 15px; font-weight: 700; margin-bottom: 10px; }
.task { display: flex; gap: 8px; padding: 8px 0; border-bottom: 1px solid $border-color;
  &:last-child { border-bottom: none; }
  .check { width: 22px; color: $primary-color; font-weight: 700; }
  .task-title { display: block; font-size: 13px; font-weight: 600; }
  .task-detail { display: block; font-size: 11px; color: $text-muted; margin-top: 2px; line-height: 1.4; }
}
.checks { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; }
.chk {
  font-size: 12px; padding: 4px 10px; border-radius: 8px; background: $chip-bg; color: $text-secondary;
  &.on { background: $primary-color; color: $on-primary; }
}
.num-row { display: flex; align-items: center; gap: 8px; margin: 8px 0;
  .label { font-size: 12px; color: $text-secondary; width: 90px; flex-shrink: 0; }
}
.ghost { margin-top: 10px; }
</style>
