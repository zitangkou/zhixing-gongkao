<template>
  <view class="page-health">
    <view v-if="loading && !ov" class="state-box">
      <text class="state-title">加载中…</text>
      <text class="state-desc">正在同步健康数据</text>
    </view>
    <view v-else-if="loadError && !ov" class="state-box">
      <text class="state-title">加载失败</text>
      <text class="state-desc">{{ loadError }}</text>
      <view class="state-btn" @tap="load">点击重试</view>
    </view>
    <template v-else-if="ov">
      <view class="hero">
        <text class="phase-tag">第 {{ ov.weekIndex }} 周 · 阶段{{ ov.phase.phase }}</text>
        <text class="phase-title">{{ ov.phase.title }}</text>
        <text class="phase-goal">{{ ov.phase.goal }}</text>
        <view class="hero-meta">
          <text>连续打卡 {{ ov.streakDays }} 天</text>
          <text>{{ ov.todayCheckedIn ? '今日已记录' : '今日未打卡' }}</text>
        </view>
      </view>

      <nut-button type="primary" block class="main-btn" @click="go('/pages/health/today')">
        {{ ov.todayCheckedIn ? '继续今日打卡' : '开始今日打卡' }}
      </nut-button>

      <view class="entry-grid">
        <view class="entry-item" @tap="go('/pages/health/mind')">
          <text class="entry-name">心理训练</text>
          <text class="entry-desc">能量 {{ avg(ov.weekEnergy) }} · 焦虑 {{ ov.weekMindStats.avgAnxiety || '—' }}</text>
        </view>
        <view class="entry-item" @tap="go('/pages/health/body')">
          <text class="entry-name">身体</text>
          <text class="entry-desc">胃 {{ avg(ov.weekStomach) }} · 皮肤 {{ avg(ov.weekSkin) }}</text>
        </view>
        <view class="entry-item" @tap="go('/pages/health/habits')">
          <text class="entry-name">习惯 · 饮食</text>
          <text class="entry-desc">三餐/排便清单 · 复盘评估</text>
        </view>
        <view class="entry-item" @tap="go('/pages/health/phase')">
          <text class="entry-name">阶段说明</text>
          <text class="entry-desc">8 周计划</text>
        </view>
      </view>

      <view class="section">
        <text class="section-title">本周心情</text>
        <view class="dots">
          <view v-for="p in ov.weekMood" :key="p.date" class="dot-col" :class="{ today: p.isToday }">
            <view class="dot" :style="{ opacity: p.value ? 0.3 + p.value * 0.07 : 0.15, height: (8 + p.value * 4) + 'px' }" />
            <text class="dot-label">{{ p.label }}</text>
          </view>
        </view>
      </view>

      <view v-if="ov.lowEnergyHint" class="tip warn">本周心理能量偏低，可先回到散步与作息，不必强求社交表现。</view>
      <view v-for="(t, i) in ov.softTips" :key="i" class="tip">{{ t }}</view>

      <nut-button size="small" class="link-btn" @click="go('/pages/health/review')">晚间复盘</nut-button>

      <text class="disclaimer">{{ ov.disclaimer }}</text>
    </template>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { Button as NutButton } from '@nutui/nutui-taro'
import { api } from '@/api'
import type { HealthOverview, HealthWeekPoint } from '@/types'

definePageConfig({ navigationBarTitleText: '健康' })

const ov = ref<HealthOverview | null>(null)
const loading = ref(false)
const loadError = ref('')

function avg(pts: HealthWeekPoint[]) {
  const nums = pts.map((p) => p.value).filter((v) => v > 0)
  if (!nums.length) return '—'
  return (nums.reduce((a, b) => a + b, 0) / nums.length).toFixed(1)
}

function go(url: string) {
  Taro.navigateTo({ url })
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await api.getHealthOverview()
    if (res.code === 0 && res.data) {
      ov.value = res.data
    } else {
      loadError.value = res.message || '加载健康数据失败'
    }
  } catch {
    loadError.value = '网络异常，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-health { @include page-padding; padding-bottom: 40px; }
.hero {
  @include card; padding: 16px;
  .phase-tag { font-size: 12px; color: $text-muted; }
  .phase-title { display: block; font-size: 20px; font-weight: 700; margin: 6px 0 4px; color: $primary-color; }
  .phase-goal { display: block; font-size: 13px; color: $text-secondary; line-height: 1.5; }
  .hero-meta { display: flex; justify-content: space-between; margin-top: 12px; font-size: 12px; color: $text-muted; }
}
.main-btn { margin: 12px 0; }
.entry-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
.entry-item {
  @include card; padding: 14px; margin-bottom: 0;
  .entry-name { display: block; font-size: 15px; font-weight: 700; margin-bottom: 4px; }
  .entry-desc { font-size: 11px; color: $text-muted; }
}
.section { @include card; padding: 14px; }
.section-title { display: block; font-size: 14px; font-weight: 700; margin-bottom: 10px; }
.dots { display: flex; align-items: flex-end; justify-content: space-between; height: 48px; }
.dot-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px;
  &.today .dot-label { color: $primary-color; font-weight: 700; }
}
.dot { width: 10px; border-radius: 4px; background: $primary-color; min-height: 8px; }
.dot-label { font-size: 10px; color: $text-muted; }
.tip { @include card; font-size: 12px; color: $text-secondary; line-height: 1.5; padding: 10px 12px;
  &.warn { color: $danger; }
}
.link-btn { margin: 8px 0 16px; }
.disclaimer { display: block; font-size: 11px; color: $text-muted; line-height: 1.5; }
.state-box { @include page-state-box; }
</style>
