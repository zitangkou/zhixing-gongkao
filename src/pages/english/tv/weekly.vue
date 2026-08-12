<template>
  <view class="page-weekly">
    <view class="hero">
      <text class="hero-title">周复盘</text>
      <text class="hero-desc" v-if="data">{{ data.weekStart }} ~ {{ data.weekEnd }}</text>
    </view>

    <view v-if="loading" class="empty">加载中...</view>
    <view v-else-if="data" class="grid">
      <view class="cell">
        <text class="num">{{ data.episodesTouched }}</text>
        <text class="label">触及集数</text>
      </view>
      <view class="cell">
        <text class="num">{{ data.completedSessionCount }}</text>
        <text class="label">完成场景</text>
      </view>
      <view class="cell">
        <text class="num">{{ data.newExpressionCount }}</text>
        <text class="label">新增表达</text>
      </view>
      <view class="cell">
        <text class="num">{{ data.masteredCount }}</text>
        <text class="label">新掌握</text>
      </view>
      <view class="cell">
        <text class="num">{{ data.shadowCount }}</text>
        <text class="label">跟读次数</text>
      </view>
      <view class="cell">
        <text class="num">{{ Math.round(data.durationSec / 60) }}</text>
        <text class="label">学习分钟</text>
      </view>
    </view>

    <view class="tips">
      <text class="tips-title">本周自问</text>
      <text class="tips-item">· 哪些句型已经能脱口而出？</text>
      <text class="tips-item">· 哪一集场景最值得重看精拆？</text>
      <text class="tips-item">· 下周只盯 1 部剧、每天 1 个场景是否更稳？</text>
    </view>

    <view class="link" @tap="goBank">去表达库复习 ›</view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { api } from '@/api'
import type { TvWeeklyReview } from '@/types'

definePageConfig({ navigationBarTitleText: '周复盘' })

const loading = ref(false)
const data = ref<TvWeeklyReview | null>(null)

function goBank() {
  Taro.navigateTo({ url: '/pages/english/tv/expression-bank?tab=review' })
}

async function load() {
  loading.value = true
  try {
    const res = await api.getTvWeekly()
    if (res.code === 0 && res.data) data.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-weekly {
  @include page-padding;
  padding-bottom: 40px;
}

.hero {
  margin-bottom: 16px;
  .hero-title { display: block; font-size: 22px; font-weight: 700; color: $text-primary; }
  .hero-desc { display: block; font-size: 12px; color: $text-muted; margin-top: 4px; }
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 18px;
  .cell {
    @include card;
    padding: 14px 8px;
    border-radius: $radius-lg;
    text-align: center;
    .num { display: block; font-size: 22px; font-weight: 700; color: $primary-color; }
    .label { display: block; font-size: 11px; color: $text-muted; margin-top: 4px; }
  }
}

.tips {
  @include card;
  padding: 14px;
  border-radius: $radius-lg;
  margin-bottom: 16px;
  .tips-title { display: block; font-size: 14px; font-weight: 600; margin-bottom: 8px; }
  .tips-item { display: block; font-size: 13px; color: $text-secondary; line-height: 1.7; }
}

.link { font-size: 14px; color: $primary-color; }
.empty { text-align: center; padding: 40px; color: $text-muted; }
</style>
