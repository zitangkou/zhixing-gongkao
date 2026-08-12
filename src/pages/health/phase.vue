<template>
  <view class="page-phase">
    <view class="intro">不是逼自己变外向，而是让大脑重新相信：社交是安全的，我可以慢慢来。</view>
    <view
      v-for="p in phases"
      :key="p.phase"
      class="card"
      :class="{ current: current === p.phase }"
    >
      <text class="tag">第 {{ p.weekStart }}–{{ p.weekEnd }} 周 · 阶段{{ p.phase }}</text>
      <text class="title">{{ p.title }}</text>
      <text class="goal">{{ p.goal }}</text>
      <text class="principle">{{ p.principle }}</text>
    </view>
    <nut-button block :loading="resetting" @click="onReset">从第 1 周重新开始</nut-button>
    <text class="disclaimer">本模块不能替代医疗或心理咨询。皮肤/消化持续加重，或情绪连续两周明显低落，请寻求专业帮助。</text>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Button as NutButton } from '@nutui/nutui-taro'
import { api } from '@/api'
import type { HealthPhase } from '@/types'
import { showConfirm, showToast } from '@/utils/platform'

definePageConfig({ navigationBarTitleText: '阶段说明' })

const phases = ref<HealthPhase[]>([])
const current = ref(1)
const resetting = ref(false)

async function load() {
  const [plist, ov] = await Promise.all([api.listHealthPhases(), api.getHealthOverview()])
  if (plist.code === 0 && plist.data) phases.value = plist.data
  if (ov.code === 0 && ov.data) current.value = ov.data.phase.phase
}

async function onReset() {
  const ok = await showConfirm('重新开始', '将把计划起点设为今天，确定吗？')
  if (!ok) return
  resetting.value = true
  try {
    const res = await api.resetHealthProgram()
    if (res.code === 0) {
      showToast('已重置', 'success')
      await load()
    } else showToast(res.message || '失败', 'error')
  } finally {
    resetting.value = false
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';
.page-phase { @include page-padding; }
.intro { font-size: 13px; color: $text-secondary; line-height: 1.5; margin-bottom: 14px; }
.card {
  @include card; padding: 14px; margin-bottom: 10px;
  &.current { border: 1px solid $primary-color; }
  .tag { font-size: 11px; color: $text-muted; }
  .title { display: block; font-size: 16px; font-weight: 700; margin: 4px 0; color: $primary-color; }
  .goal { display: block; font-size: 13px; margin-bottom: 4px; }
  .principle { display: block; font-size: 12px; color: $text-muted; line-height: 1.5; }
}
.disclaimer { display: block; margin-top: 16px; font-size: 11px; color: $text-muted; line-height: 1.5; }
</style>
