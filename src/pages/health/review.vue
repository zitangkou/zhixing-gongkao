<template>
  <view class="page-review">
    <view v-if="assessment" class="section assess">
      <text class="section-title">今日身体评估</text>
      <text class="assess-body">{{ assessment }}</text>
      <text class="sub">依据饮食清单、大小便与胃/湿/皮肤主观分生成，仅供节律参考，非医疗诊断。</text>
    </view>

    <view class="section">
      <text class="section-title">晚间复盘</text>
      <nut-input v-model="bestThing" placeholder="今天完成最好的事情" />
      <nut-input v-model="tomorrowGoal" placeholder="明天一个小目标" class="mt" />
    </view>

    <view class="section">
      <view class="section-head" @tap="showCbt = !showCbt">
        <text class="section-title">焦虑五问（可选）</text>
        <text>{{ showCbt ? '▾' : '▸' }}</text>
      </view>
      <view v-if="showCbt" class="cbt">
        <nut-input v-model="cbt.anxious" placeholder="我焦虑了吗？" />
        <nut-input v-model="cbt.why" placeholder="为什么？" />
        <nut-input v-model="cbt.worst" placeholder="最坏会发生什么？" />
        <nut-input v-model="cbt.probability" placeholder="发生概率？" />
        <nut-input v-model="cbt.acceptable" placeholder="我能接受吗？" />
        <nut-input v-model="cbt.nextStep" placeholder="一小步行动（可选）" />
      </view>
    </view>

    <view class="section">
      <text class="section-title">反刍刹车</text>
      <view class="checks">
        <text class="chk" :class="{ on: rum.triggered }" @tap="rum.triggered = !rum.triggered">今日触发过</text>
        <text class="chk" :class="{ on: rum.stoppedInTime }" @tap="rum.stoppedInTime = !rum.stoppedInTime">5 分钟内停下</text>
      </view>
    </view>

    <nut-button type="primary" block :loading="saving" @click="onSave">保存复盘</nut-button>
    <text class="link" @tap="goHabits">去完善饮食 / 大小便清单 →</text>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput } from '@nutui/nutui-taro'
import { api } from '@/api'
import { flushFormBeforeSave } from '@/utils/formFlush'
import { showToast } from '@/utils/platform'

definePageConfig({ navigationBarTitleText: '晚间复盘' })

const bestThing = ref('')
const tomorrowGoal = ref('')
const assessment = ref('')
const showCbt = ref(true)
const saving = ref(false)
const rum = reactive({ triggered: false, stoppedInTime: false, note: '' })
const cbt = reactive({
  anxious: '', why: '', worst: '', probability: '', acceptable: '', nextStep: '',
})

function goHabits() {
  Taro.navigateTo({ url: '/pages/health/habits' })
}

async function load() {
  const res = await api.getHealthDaily()
  if (res.code === 0 && res.data) {
    bestThing.value = res.data.review?.bestThing || ''
    tomorrowGoal.value = res.data.review?.tomorrowGoal || ''
    assessment.value = res.data.bodyAssessment || res.data.review?.bodyAssessment || ''
    Object.assign(cbt, res.data.cbt)
    Object.assign(rum, res.data.rumination)
  }
}

async function onSave() {
  await flushFormBeforeSave()

  saving.value = true
  try {
    const res = await api.upsertHealthDaily({
      review: { bestThing: bestThing.value, tomorrowGoal: tomorrowGoal.value },
      cbt: { ...cbt },
      rumination: { ...rum },
    })
    if (res.code === 0 && res.data) {
      assessment.value = res.data.bodyAssessment || res.data.review?.bodyAssessment || ''
      showToast('已保存', 'success')
    } else showToast(res.message || '失败', 'error')
  } finally {
    saving.value = false
  }
}

useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';
.page-review { @include page-padding; padding-bottom: 40px; }
.section { @include card; padding: 14px; margin-bottom: 12px; }
.section-title { display: block; font-size: 14px; font-weight: 700; margin-bottom: 10px; }
.section-head { display: flex; justify-content: space-between; }
.mt { margin-top: 8px; }
.cbt { display: flex; flex-direction: column; gap: 8px; }
.checks { display: flex; gap: 8px; flex-wrap: wrap; }
.chk { font-size: 12px; padding: 4px 10px; border-radius: 8px; background: $chip-bg;
  &.on { background: $primary-color; color: $on-primary; }
}
.assess { background: $primary-faint;
  .assess-body { display: block; font-size: 13px; line-height: 1.55; color: $text-secondary; margin-bottom: 6px; }
  .sub { display: block; font-size: 11px; color: $text-muted; line-height: 1.4; }
}
.link { display: block; text-align: center; margin-top: 14px; font-size: 13px; color: $primary-color; }
</style>
