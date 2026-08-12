<template>
  <view class="page">
    <view class="toolbar">
      <text class="hint">手动录入，不接行情</text>
      <view class="btn" @tap="goEdit()">+ 新快照</view>
    </view>

    <view v-if="loading" class="empty">加载中...</view>
    <view v-else-if="!rows.length" class="empty">
      <text class="t">还没有资产快照</text>
      <view class="btn outline" @tap="goEdit()">记一笔</view>
    </view>
    <view v-else class="list">
      <view v-for="s in rows" :key="s.id" class="card" @tap="goEdit(s.id)">
        <view class="head">
          <text class="date">{{ s.snapDate }}</text>
          <text class="total">¥{{ formatYuan(s.total) }}</text>
        </view>
        <view class="bars">
          <view v-for="a in s.allocations" :key="a.key" class="bar-row">
            <text class="name">{{ a.label }}</text>
            <view class="track">
              <view class="fill" :style="{ width: Math.max(a.percent, a.amount > 0 ? 2 : 0) + '%' }" />
            </view>
            <text class="pct">{{ a.percent }}%</text>
            <text class="amt">¥{{ formatYuan(a.amount) }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { api } from '@/api'
import { formatYuan } from '@/utils/wealth'
import type { WealthSnapshot } from '@/types'

definePageConfig({ navigationBarTitleText: '财富总览' })

const loading = ref(false)
const rows = ref<WealthSnapshot[]>([])

function goEdit(id?: string) {
  Taro.navigateTo({
    url: id ? `/pages/wealth/snapshot-edit?id=${id}` : '/pages/wealth/snapshot-edit',
  })
}

async function load() {
  loading.value = true
  try {
    const res = await api.listWealthSnapshots()
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
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
  .hint { font-size: 13px; color: $text-muted; }
  .btn {
    padding: 8px 14px; border-radius: 8px; background: $primary-color; color: $on-primary;
    font-size: 13px; font-weight: 600;
  }
}
.btn.outline {
  display: inline-block; margin-top: 16px; padding: 10px 18px; border-radius: 8px;
  border: 1px solid $primary-color; color: $primary-color; font-weight: 600;
}
.empty { text-align: center; padding: 48px 16px; color: $text-muted;
  .t { display: block; font-size: 15px; color: $text-secondary; }
}
.card {
  padding: 16px 0; border-bottom: 1px solid $border-color;
  .head { display: flex; justify-content: space-between; margin-bottom: 14px;
    .date { font-size: 13px; color: $text-muted; }
    .total { font-size: 18px; font-weight: 700; color: $text-primary; }
  }
}
.bar-row {
  display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
  .name { width: 36px; font-size: 12px; color: $text-muted; flex-shrink: 0; }
  .track { flex: 1; height: 6px; background: $elevated; border-radius: 3px; overflow: hidden;
    .fill { height: 100%; background: $primary-color; border-radius: 3px; }
  }
  .pct { width: 40px; text-align: right; font-size: 12px; color: $text-secondary; }
  .amt { width: 72px; text-align: right; font-size: 12px; color: $text-muted; }
}
</style>
