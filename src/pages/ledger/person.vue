<template>
  <view class="page-person">
    <view v-if="loading" class="empty">加载中...</view>
    <template v-else>
      <view class="summary">
        <text class="name">{{ name }}</text>
        <view class="sum-row">
          <view class="cell">
            <text class="v">¥{{ formatYuan(totalPrincipal) }}</text>
            <text class="k">累计出借</text>
          </view>
          <view class="cell">
            <text class="v">¥{{ formatYuan(totalRepaid) }}</text>
            <text class="k">累计已还</text>
          </view>
          <view class="cell">
            <text class="v warn">¥{{ formatYuan(totalRemaining) }}</text>
            <text class="k">合计待收</text>
          </view>
        </view>
        <text class="meta">共 {{ loans.length }} 笔 · 进行中 {{ openCount }} 笔</text>
      </view>

      <view class="actions">
        <nut-button type="primary" size="small" @click="goNewLoan">再借一笔</nut-button>
      </view>

      <text class="sec-title">明细流水</text>
      <view v-if="!loans.length" class="empty soft">暂无记录</view>
      <view v-else class="list">
        <view v-for="l in loans" :key="l.id" class="item" @tap="goDetail(l.id)">
          <view class="item-main">
            <view class="loan-head">
              <text class="item-title">¥{{ formatYuan(l.principal) }}</text>
              <text class="badge" :class="l.status">{{ l.status === 'settled' ? '已结清' : '待收回' }}</text>
            </view>
            <text class="item-sub">
              {{ l.lendDate }} · 已还 ¥{{ formatYuan(l.repaid) }}
              {{ l.note ? ' · ' + l.note : '' }}
            </text>
          </view>
          <text class="item-amt" :class="{ warn: l.remaining > 0 }">
            ¥{{ formatYuan(l.remaining) }}
          </text>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Taro, { useDidShow, useRouter } from '@tarojs/taro'
import { Button as NutButton } from '@nutui/nutui-taro'
import { api } from '@/api'
import { formatYuan } from '@/utils/ledger'
import type { LedgerLoan } from '@/types'

definePageConfig({ navigationBarTitleText: '对方汇总' })

const router = useRouter()
const name = ref(decodeURIComponent(router.params?.name || ''))
const loading = ref(false)
const loans = ref<LedgerLoan[]>([])

const totalPrincipal = computed(() => loans.value.reduce((s, l) => s + (l.principal || 0), 0))
const totalRepaid = computed(() => loans.value.reduce((s, l) => s + (l.repaid || 0), 0))
const totalRemaining = computed(() => loans.value.reduce((s, l) => s + (l.remaining || 0), 0))
const openCount = computed(() => loans.value.filter((l) => l.remaining > 0).length)

async function load() {
  if (!name.value) return
  loading.value = true
  try {
    const res = await api.listLedgerLoans(undefined, name.value)
    if (res.code === 0 && res.data) loans.value = res.data
  } finally {
    loading.value = false
  }
}

function goDetail(id: string) {
  Taro.navigateTo({ url: `/pages/ledger/loan-detail?id=${id}` })
}

function goNewLoan() {
  // 预填对方名：通过 query 传给编辑页
  Taro.navigateTo({
    url: `/pages/ledger/loan-edit?counterparty=${encodeURIComponent(name.value)}`,
  })
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';
.page-person { @include page-padding; padding-bottom: 40px; }
.summary {
  @include card; padding: 14px; margin-bottom: 12px;
  .name { display: block; font-size: 18px; font-weight: 700; margin-bottom: 12px; }
  .sum-row { display: flex; margin-bottom: 8px;
    .cell { flex: 1; text-align: center;
      .v { display: block; font-size: 16px; font-weight: 700;
        &.warn { color: $accent-amber; }
      }
      .k { font-size: 11px; color: $text-muted; }
    }
  }
  .meta { font-size: 12px; color: $text-muted; }
}
.actions { margin-bottom: 14px; }
.sec-title { display: block; font-size: 14px; font-weight: 700; margin-bottom: 8px; }
.empty { text-align: center; padding: 40px; color: $text-muted;
  &.soft { padding: 20px; font-size: 13px; }
}
.list { display: flex; flex-direction: column; gap: 8px; }
.item {
  @include card; padding: 12px; display: flex; align-items: center; gap: 10px;
  .item-main { flex: 1; min-width: 0; }
  .loan-head { display: flex; align-items: center; gap: 6px; }
  .item-title { font-size: 15px; font-weight: 600; }
  .item-sub { display: block; font-size: 12px; color: $text-muted; margin-top: 2px;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .item-amt { font-size: 15px; font-weight: 700; flex-shrink: 0;
    &.warn { color: $accent-amber; }
  }
  .badge {
    font-size: 10px; padding: 1px 6px; border-radius: 4px;
    background: rgba($accent-amber, 0.12); color: $accent-amber;
    &.settled { background: rgba($accent-green, 0.12); color: $success; }
  }
}
</style>
