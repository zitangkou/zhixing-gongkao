<template>
  <view class="page">
    <view class="toolbar">
      <view class="filters">
        <text class="f" :class="{ on: side === '' }" @tap="setSide('')">全部</text>
        <text class="f" :class="{ on: side === 'buy' }" @tap="setSide('buy')">买入</text>
        <text class="f" :class="{ on: side === 'sell' }" @tap="setSide('sell')">卖出</text>
      </view>
      <view class="btn" @tap="goEdit()">+ 写日志</view>
    </view>

    <view v-if="loading" class="empty">加载中...</view>
    <view v-else-if="!rows.length" class="empty">
      <text class="t">还没有投资日志</text>
      <text class="d">记录「为什么买」，而不是成交流水</text>
    </view>
    <view v-else class="list">
      <view v-for="j in rows" :key="j.id" class="item" @tap="goEdit(j.id)">
        <view class="top">
          <text class="side" :class="j.side">{{ j.side === 'sell' ? '卖' : '买' }}</text>
          <text class="name">{{ j.name }}</text>
          <text class="date">{{ j.tradeDate }}</text>
        </view>
        <text class="meta">
          {{ j.price ? `¥${j.price}` : '' }}
          {{ j.positionPct ? ` · 仓位 ${j.positionPct}%` : '' }}
          · {{ emotionLabel(j.emotion) }}
          {{ j.resultTag === 'win' ? ' · 盈' : j.resultTag === 'loss' ? ' · 亏' : '' }}
        </text>
        <text v-if="j.reasonNote || j.reasons.length" class="note">
          {{ j.reasons.join(' · ') }}{{ j.reasonNote ? (j.reasons.length ? ' · ' : '') + j.reasonNote : '' }}
        </text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { api } from '@/api'
import { emotionLabel } from '@/utils/wealth'
import type { WealthJournal } from '@/types'

definePageConfig({ navigationBarTitleText: '投资日志' })

const side = ref('')
const loading = ref(false)
const rows = ref<WealthJournal[]>([])

function setSide(v: string) {
  side.value = v
  load()
}

function goEdit(id?: string) {
  Taro.navigateTo({
    url: id ? `/pages/wealth/journal-edit?id=${id}` : '/pages/wealth/journal-edit',
  })
}

async function load() {
  loading.value = true
  try {
    const res = await api.listWealthJournals(side.value || undefined)
    if (res.code === 0) rows.value = res.data || []
  } finally {
    loading.value = false
  }
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';
.page { padding: 16px 16px 40px; }
.toolbar {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; gap: 12px;
  .filters { display: flex; gap: 4px;
    .f { font-size: 14px; padding: 6px 12px; color: $text-muted;
      &.on { color: $text-primary; font-weight: 600; }
    }
  }
  .btn {
    flex-shrink: 0; padding: 8px 14px; border-radius: 8px; background: $primary-color;
    color: $on-primary; font-size: 13px; font-weight: 600;
  }
}
.empty { text-align: center; padding: 48px 16px; color: $text-muted;
  .t { display: block; font-size: 15px; color: $text-secondary; margin-bottom: 8px; }
  .d { font-size: 13px; }
}
.item {
  padding: 16px 0; border-bottom: 1px solid $border-color;
  .top { display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
    .side {
      font-size: 12px; font-weight: 700; padding: 2px 6px; border-radius: 4px;
      &.buy { background: rgba($accent-green, 0.12); color: $accent-green; }
      &.sell { background: $primary-light; color: $primary-color; }
    }
    .name { flex: 1; font-size: 16px; font-weight: 600; color: $text-primary; }
    .date { font-size: 12px; color: $text-muted; }
  }
  .meta { display: block; font-size: 12px; color: $text-muted; margin-bottom: 6px; }
  .note { display: block; font-size: 13px; color: $text-secondary; line-height: 1.45; }
}
</style>
