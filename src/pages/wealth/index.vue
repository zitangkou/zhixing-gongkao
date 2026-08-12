<template>
  <view class="page-wealth">
    <view class="hero">
      <text class="hero-kicker">投资大脑</text>
      <text class="hero-title">财富</text>
      <text class="hero-desc">资产 · 原则 · 日志 · 复盘 · 记账</text>
    </view>

    <view v-if="hub?.latestSnapshot" class="total-card" @tap="go('/pages/wealth/overview')">
      <text class="total-label">总资产 · {{ hub.latestSnapshot.snapDate }}</text>
      <text class="total-num">¥{{ formatYuan(hub.latestSnapshot.total) }}</text>
      <view class="alloc-row">
        <text
          v-for="a in hub.latestSnapshot.allocations.filter((x) => x.amount > 0)"
          :key="a.key"
          class="alloc"
        >{{ a.label }} {{ a.percent }}%</text>
      </view>
    </view>
    <view v-else class="total-card empty" @tap="go('/pages/wealth/snapshot-edit')">
      <text class="total-label">尚未录入资产</text>
      <text class="total-cta">记录第一笔快照 ›</text>
    </view>

    <view class="week-row" v-if="hub">
      <view class="week-item">
        <text class="n">{{ hub.weekTradeCount }}</text>
        <text class="l">本周日志</text>
      </view>
      <view class="week-item">
        <text class="n win">{{ hub.weekWinCount }}</text>
        <text class="l">标记盈利</text>
      </view>
      <view class="week-item">
        <text class="n loss">{{ hub.weekLossCount }}</text>
        <text class="l">标记亏损</text>
      </view>
    </view>

    <view class="entries">
      <view class="entry" @tap="go('/pages/wealth/overview')">
        <text class="entry-name">财富总览</text>
        <text class="entry-desc">手动资产快照与配置占比</text>
      </view>
      <view class="entry" @tap="go('/pages/wealth/rules')">
        <text class="entry-name">投资方法论</text>
        <text class="entry-desc">{{ hub?.principleCount || 0 }} 条原则 · 分层规则</text>
      </view>
      <view class="entry" @tap="go('/pages/wealth/journal')">
        <text class="entry-name">投资日志</text>
        <text class="entry-desc">{{ hub?.journalCount || 0 }} 条 · 记录为什么买卖</text>
      </view>
      <view class="entry" @tap="go('/pages/wealth/review')">
        <text class="entry-name">复盘分析</text>
        <text class="entry-desc">本周盈亏与情绪统计</text>
      </view>
      <view class="entry" @tap="go('/pages/ledger/index')">
        <text class="entry-name">日常记账</text>
        <text class="entry-desc">支出 · 出借归还</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { api } from '@/api'
import { formatYuan } from '@/utils/wealth'
import type { WealthHub } from '@/types'

definePageConfig({ navigationBarTitleText: '财富' })

const hub = ref<WealthHub | null>(null)

function go(url: string) {
  Taro.navigateTo({ url })
}

async function load() {
  const res = await api.getWealthHub()
  if (res.code === 0) hub.value = res.data
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-wealth {
  padding: 20px 16px 48px;
}

.hero {
  margin-bottom: 20px;
  .hero-kicker {
    display: block;
    font-size: 12px;
    color: $text-muted;
    margin-bottom: 6px;
  }
  .hero-title {
    display: block;
    font-size: 26px;
    font-weight: 700;
    color: $text-primary;
  }
  .hero-desc {
    display: block;
    margin-top: 8px;
    font-size: 13px;
    color: $text-muted;
  }
}

.total-card {
  padding: 18px 16px;
  border-radius: 10px;
  background: $primary-color;
  color: $on-primary;
  margin-bottom: 16px;
  &.empty {
    background: $elevated;
    color: $text-primary;
  }
  .total-label { display: block; font-size: 12px; opacity: 0.85; }
  .total-num {
    display: block;
    margin-top: 8px;
    font-size: 28px;
    font-weight: 700;
    letter-spacing: 0.02em;
  }
  .total-cta {
    display: block;
    margin-top: 10px;
    font-size: 14px;
    color: $primary-color;
    font-weight: 600;
  }
  .alloc-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
    .alloc {
      font-size: 12px;
      opacity: 0.9;
    }
  }
}

.week-row {
  display: flex;
  margin-bottom: 20px;
  padding: 14px 0;
  border-top: 1px solid $border-color;
  border-bottom: 1px solid $border-color;
  .week-item {
    flex: 1;
    text-align: center;
    .n {
      display: block;
      font-size: 20px;
      font-weight: 700;
      color: $text-primary;
      &.win { color: $accent-green; }
      &.loss { color: $primary-color; }
    }
    .l {
      display: block;
      margin-top: 4px;
      font-size: 12px;
      color: $text-muted;
    }
  }
}

.entries {
  display: flex;
  flex-direction: column;
}
.entry {
  padding: 18px 0;
  border-bottom: 1px solid $border-color;
  &:last-child { border-bottom: none; }
  .entry-name {
    display: block;
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
  }
  .entry-desc {
    display: block;
    margin-top: 6px;
    font-size: 13px;
    color: $text-muted;
  }
}
</style>
