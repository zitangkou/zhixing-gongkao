<template>
  <view class="page-dushu">
    <view class="hero-card" v-if="stats">
      <view class="hero-item">
        <text class="hero-num">{{ stats.weekReadDays }}/{{ stats.weekReadTarget }}</text>
        <text class="hero-label">本周阅读</text>
      </view>
      <view class="hero-item">
        <text class="hero-num">{{ stats.weekOutputCount }}</text>
        <text class="hero-label">本周记录</text>
      </view>
      <view class="hero-item">
        <text class="hero-num">{{ stats.todayDone ? '✓' : '—' }}</text>
        <text class="hero-label">今日</text>
      </view>
    </view>

    <view class="method-tip">
      读完留一句自己的话就好，不必写长。
      <text v-if="stats?.readingBookTitle"> 当前在读：《{{ stats.readingBookTitle }}》</text>
    </view>

    <nut-button type="primary" block class="main-btn" @click="goToday">今日阅读</nut-button>

    <view class="entry-grid">
      <view class="entry-item" @tap="go('/pages/dushu/shelf')">
        <text class="entry-name">我的书架</text>
        <text class="entry-desc">{{ stats?.bookCount || 0 }} 本</text>
      </view>
      <view class="entry-item" @tap="go('/pages/dushu/assets')">
        <text class="entry-name">知识资产</text>
        <text class="entry-desc">人物卡 {{ stats?.personCardCount || 0 }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { Button as NutButton } from '@nutui/nutui-taro'
import { api } from '@/api'
import type { DushuStats } from '@/types'

definePageConfig({ navigationBarTitleText: '读书' })

const stats = ref<DushuStats | null>(null)

function go(url: string) {
  Taro.navigateTo({ url })
}

function goToday() {
  Taro.navigateTo({ url: '/pages/dushu/today' })
}

async function load() {
  const res = await api.getDushuStats()
  if (res.code === 0 && res.data) stats.value = res.data
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-dushu { @include page-padding; }
.hero-card {
  @include card; display: flex; padding: 16px;
  .hero-item { flex: 1; text-align: center;
    .hero-num { display: block; font-size: 20px; font-weight: 700; color: $primary-color; }
    .hero-label { font-size: 12px; color: $text-muted; }
  }
}
.method-tip { font-size: 12px; color: $text-muted; line-height: 1.5; margin: 10px 0 14px; }
.main-btn { margin-bottom: 14px; }
.entry-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.entry-item {
  @include card; padding: 16px; margin-bottom: 0;
  .entry-name { display: block; font-size: 15px; font-weight: 700; margin-bottom: 4px; }
  .entry-desc { font-size: 12px; color: $text-muted; }
}
</style>
