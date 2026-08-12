<template>
  <view class="page">
    <view class="week-bar">
      <text class="nav" @tap="shiftWeek(-1)">‹ 上周</text>
      <text class="range">{{ review?.weekStart }} ～ {{ review?.weekEnd }}</text>
      <text class="nav" @tap="shiftWeek(1)">下周 ›</text>
    </view>

    <view v-if="loading" class="empty">加载中...</view>
    <template v-else-if="review">
      <view class="stats">
        <view class="stat"><text class="n">{{ review.tradeCount }}</text><text class="l">交易日志</text></view>
        <view class="stat"><text class="n">{{ review.buyCount }}</text><text class="l">买入</text></view>
        <view class="stat"><text class="n">{{ review.sellCount }}</text><text class="l">卖出</text></view>
      </view>
      <view class="stats">
        <view class="stat"><text class="n win">{{ review.winCount }}</text><text class="l">标记盈利</text></view>
        <view class="stat"><text class="n loss">{{ review.lossCount }}</text><text class="l">标记亏损</text></view>
        <view class="stat"><text class="n">{{ review.brokePlanCount }}</text><text class="l">未按计划</text></view>
      </view>

      <view class="block">
        <text class="block-title">赚钱原因</text>
        <view v-if="!review.topWinReasons.length" class="muted">本周暂无标记盈利的原因标签</view>
        <view v-for="r in review.topWinReasons" :key="'w'+r.reason" class="row">
          <text class="k">{{ r.reason }}</text>
          <text class="v">{{ r.count }} 次</text>
        </view>
      </view>

      <view class="block">
        <text class="block-title">亏钱原因</text>
        <view v-if="!review.topLossReasons.length" class="muted">本周暂无标记亏损的原因标签</view>
        <view v-for="r in review.topLossReasons" :key="'l'+r.reason" class="row">
          <text class="k">{{ r.reason }}</text>
          <text class="v loss">{{ r.count }} 次</text>
        </view>
      </view>

      <view class="block">
        <text class="block-title">情绪分布</text>
        <view v-if="!review.emotionStats.length" class="muted">本周无日志</view>
        <view v-for="e in review.emotionStats" :key="e.emotion" class="row">
          <text class="k">{{ emotionLabel(e.emotion) }}</text>
          <text class="v">{{ e.count }} 次{{ e.lossCount ? ` · 亏 ${e.lossCount}` : '' }}</text>
        </view>
      </view>

      <text class="foot-tip">在日志里标记「盈利/亏损」并打原因标签后，复盘会更准。</text>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useDidShow } from '@tarojs/taro'
import { api } from '@/api'
import { emotionLabel } from '@/utils/wealth'
import type { WealthReview } from '@/types'

definePageConfig({ navigationBarTitleText: '复盘分析' })

const loading = ref(false)
const review = ref<WealthReview | null>(null)
const weekStart = ref('')

function mondayOf(d: Date) {
  const x = new Date(d)
  const day = (x.getDay() + 6) % 7
  x.setDate(x.getDate() - day)
  return x.toISOString().slice(0, 10)
}

function shiftWeek(delta: number) {
  const base = weekStart.value || mondayOf(new Date())
  const d = new Date(base + 'T12:00:00')
  d.setDate(d.getDate() + delta * 7)
  weekStart.value = mondayOf(d)
  load()
}

async function load() {
  loading.value = true
  try {
    const res = await api.getWealthReview(weekStart.value || undefined)
    if (res.code === 0 && res.data) {
      review.value = res.data
      weekStart.value = res.data.weekStart
    }
  } finally {
    loading.value = false
  }
}

useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';
.page { padding: 16px 16px 40px; }
.week-bar {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;
  .nav { font-size: 13px; color: $primary-color; font-weight: 600; padding: 6px; }
  .range { font-size: 13px; color: $text-secondary; }
}
.stats {
  display: flex; margin-bottom: 12px; padding: 12px 0; border-bottom: 1px solid $border-color;
  .stat { flex: 1; text-align: center;
    .n { display: block; font-size: 20px; font-weight: 700; color: $text-primary;
      &.win { color: $accent-green; }
      &.loss { color: $primary-color; }
    }
    .l { display: block; margin-top: 4px; font-size: 12px; color: $text-muted; }
  }
}
.block { margin-top: 24px;
  .block-title { display: block; font-size: 15px; font-weight: 700; margin-bottom: 12px; }
  .muted { font-size: 13px; color: $text-muted; }
  .row {
    display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid $border-color;
    .k { font-size: 14px; color: $text-primary; }
    .v { font-size: 13px; color: $text-secondary; &.loss { color: $primary-color; } }
  }
}
.foot-tip { display: block; margin-top: 24px; font-size: 12px; color: $text-muted; line-height: 1.5; }
.empty { text-align: center; padding: 40px; color: $text-muted; }
</style>
