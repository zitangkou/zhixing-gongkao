<template>
  <view class="page-mind">
    <view v-if="ov" class="hero">
      <text class="tag">阶段{{ ov.phase.phase }} · {{ ov.phase.title }}</text>
      <text class="goal">{{ ov.phase.goal }}</text>
      <text class="principle">{{ ov.phase.principle }}</text>
    </view>

    <view class="section">
      <text class="section-title">今日训练</text>
      <view v-for="t in mindTasks" :key="t.id" class="task" @tap="toggle(t.id)">
        <text class="check">{{ done.has(t.id) ? '✓' : '○' }}</text>
        <view>
          <text class="skill">{{ t.skillLabel }}</text>
          <text class="title">{{ t.title }}</text>
          <text class="detail">{{ t.detail }}</text>
        </view>
      </view>
    </view>

    <view class="section">
      <text class="section-title">心理状态</text>
      <ScoreRow label="心理能量" v-model="energy" :max="10" polarity="higher-better" tip="想不想与外界打交道" low-label="很低" high-label="很足" />
      <ScoreRow label="焦虑" v-model="anxiety" :max="10" polarity="higher-worse" tip="紧张、担忧的程度" />
      <view class="num-row">
        <text class="label">主动交流</text>
        <nut-input v-model="socialStr" type="number" placeholder="次数" />
      </view>
    </view>

    <view class="section">
      <text class="section-title">反刍刹车</text>
      <view class="checks">
        <text class="chk" :class="{ on: rum.triggered }" @tap="rum.triggered = !rum.triggered">今日触发过反刍</text>
        <text class="chk" :class="{ on: rum.stoppedInTime }" @tap="rum.stoppedInTime = !rum.stoppedInTime">5 分钟内停下</text>
      </view>
      <nut-input v-model="rum.note" placeholder="备注（可选）" />
    </view>

    <view class="section">
      <view class="section-head" @tap="showCbt = !showCbt">
        <text class="section-title">焦虑五问（CBT）</text>
        <text class="arrow">{{ showCbt ? '▾' : '▸' }}</text>
      </view>
      <view v-if="showCbt" class="cbt">
        <nut-input v-model="cbt.anxious" placeholder="我焦虑了吗？" />
        <nut-input v-model="cbt.why" placeholder="为什么？" />
        <nut-input v-model="cbt.worst" placeholder="最坏会发生什么？" />
        <nut-input v-model="cbt.probability" placeholder="发生概率大概多少？" />
        <nut-input v-model="cbt.acceptable" placeholder="如果发生，我能接受吗？" />
        <nut-input v-model="cbt.nextStep" placeholder="我可以怎么做一小步？（可选）" />
      </view>
    </view>

    <view v-if="ov" class="section stats">
      <text class="section-title">本周小计</text>
      <text>暴露任务完成 {{ ov.weekMindStats.exposureTaskCompletions }} 次</text>
      <text>CBT 填写 {{ ov.weekMindStats.cbtDays }} 天</text>
      <text>主动交流合计 {{ ov.weekMindStats.socialCountSum }}</text>
      <text>平均能量 {{ ov.weekMindStats.avgEnergy || '—' }} · 平均焦虑 {{ ov.weekMindStats.avgAnxiety || '—' }}</text>
    </view>

    <view class="ladder">
      <text class="section-title">进阶阶梯（女生交流，可选）</text>
      <text class="ladder-line">眼神微笑 → 打招呼 → 一句工作/生活问询 → 一分钟聊天。不是搭讪，完成即可。</text>
    </view>

    <nut-button type="primary" block :loading="saving" @click="onSave">保存心理记录</nut-button>
    <text class="help">若连续两周几乎每天情绪低落、对学习娱乐人际失去兴趣，或出现消极想法，请寻求心理咨询或专科评估。</text>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useDidShow } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput } from '@nutui/nutui-taro'
import { api } from '@/api'
import type { HealthOverview } from '@/types'
import ScoreRow from './ScoreRow.vue'
import { flushFormBeforeSave } from '@/utils/formFlush'
import { showToast } from '@/utils/platform'

definePageConfig({ navigationBarTitleText: '心理训练' })

const ov = ref<HealthOverview | null>(null)
const saving = ref(false)
const showCbt = ref(false)
const energy = ref(0)
const anxiety = ref(0)
const socialStr = ref('')
const tasksDone = ref<string[]>([])
const rum = reactive({ triggered: false, stoppedInTime: false, note: '' })
const cbt = reactive({
  anxious: '', why: '', worst: '', probability: '', acceptable: '', nextStep: '',
})

const done = computed(() => new Set(tasksDone.value))
const mindTasks = computed(() => (ov.value?.todayTasks || []).filter((t) => t.domain === 'mind' || t.skill === 'energy' || t.skill === 'cbt' || t.skill === 'rumination' || t.skill.startsWith('exposure') || t.skill === 'social_warm'))

function toggle(id: string) {
  const i = tasksDone.value.indexOf(id)
  if (i >= 0) tasksDone.value.splice(i, 1)
  else tasksDone.value.push(id)
}

async function load() {
  const res = await api.getHealthOverview()
  if (res.code !== 0 || !res.data) return
  ov.value = res.data
  const log = res.data.todayLog
  if (log) {
    energy.value = log.energy
    anxiety.value = log.anxiety
    socialStr.value = log.socialCount ? String(log.socialCount) : ''
    tasksDone.value = [...log.tasksDone]
    Object.assign(rum, log.rumination)
    Object.assign(cbt, log.cbt)
  }
}

async function onSave() {
  await flushFormBeforeSave()

  saving.value = true
  try {
    const res = await api.upsertHealthDaily({
      energy: energy.value,
      anxiety: anxiety.value,
      socialCount: Number(socialStr.value) || 0,
      tasksDone: tasksDone.value,
      rumination: { ...rum },
      cbt: { ...cbt },
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
.page-mind { @include page-padding; padding-bottom: 40px; }
.hero { @include card; padding: 14px;
  .tag { font-size: 12px; color: $primary-color; font-weight: 700; }
  .goal { display: block; margin-top: 6px; font-size: 15px; font-weight: 700; }
  .principle { display: block; margin-top: 4px; font-size: 12px; color: $text-muted; line-height: 1.5; }
}
.section { @include card; padding: 14px; }
.section-title { display: block; font-size: 14px; font-weight: 700; margin-bottom: 8px; }
.section-head { display: flex; justify-content: space-between; align-items: center; }
.task { display: flex; gap: 8px; padding: 8px 0; border-bottom: 1px solid $border-color;
  .check { color: $primary-color; font-weight: 700; width: 20px; }
  .skill { display: block; font-size: 10px; color: $primary-color; }
  .title { display: block; font-size: 13px; font-weight: 600; }
  .detail { display: block; font-size: 11px; color: $text-muted; margin-top: 2px; }
}
.checks { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
.chk { font-size: 12px; padding: 4px 10px; border-radius: 8px; background: $chip-bg;
  &.on { background: $primary-color; color: $on-primary; }
}
.num-row { display: flex; align-items: center; gap: 8px; .label { width: 80px; font-size: 12px; color: $text-secondary; } }
.cbt { display: flex; flex-direction: column; gap: 8px; }
.stats text { display: block; font-size: 12px; color: $text-secondary; margin-top: 4px; }
.ladder { @include card; padding: 14px;
  .ladder-line { font-size: 12px; color: $text-muted; line-height: 1.5; }
}
.help { display: block; margin-top: 14px; font-size: 11px; color: $text-muted; line-height: 1.5; }
</style>
