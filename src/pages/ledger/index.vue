<template>
  <view class="page-ledger">
    <view class="stats-card">
      <view class="stat">
        <text class="num">¥{{ formatYuan(overview?.monthExpense) }}</text>
        <text class="label">本月支出</text>
      </view>
      <view class="stat">
        <text class="num">¥{{ formatYuan(overview?.todayExpense) }}</text>
        <text class="label">今日</text>
      </view>
      <view class="stat">
        <text class="num warn">¥{{ formatYuan(overview?.remaining) }}</text>
        <text class="label">待收回 · {{ overview?.openLoanCount || 0 }}笔</text>
      </view>
    </view>

    <view class="month-row">
      <text class="month-btn" @tap="shiftMonth(-1)">‹</text>
      <text class="month-label">{{ month }}</text>
      <text class="month-btn" @tap="shiftMonth(1)">›</text>
    </view>

    <view class="tabs">
      <text class="tab" :class="{ on: tab === 'expense' }" @tap="tab = 'expense'">支出</text>
      <text class="tab" :class="{ on: tab === 'loan' }" @tap="tab = 'loan'">出借</text>
    </view>

    <!-- 支出 -->
    <template v-if="tab === 'expense'">
      <view v-if="(overview?.categories || []).length" class="chart-card">
        <text class="chart-title">本月分类</text>
        <view v-for="c in overview?.categories || []" :key="c.category" class="cat-row">
          <text class="cat-name">{{ c.category }}</text>
          <view class="cat-bar-wrap">
            <view class="cat-bar" :style="{ width: Math.max(c.percent, 2) + '%' }" />
          </view>
          <text class="cat-amt">¥{{ formatYuan(c.amount) }}</text>
          <text class="cat-pct">{{ c.percent }}%</text>
        </view>
      </view>

      <view class="actions">
        <nut-button type="primary" size="small" @click="goExpense()">记一笔</nut-button>
      </view>

      <view v-if="loading" class="state-box">
        <text class="state-title">加载中…</text>
      </view>
      <view v-else-if="loadError" class="state-box">
        <text class="state-title">加载失败</text>
        <text class="state-desc">{{ loadError }}</text>
        <view class="state-btn" @tap="load">点击重试</view>
      </view>
      <view v-else-if="!expenses.length" class="state-box">
        <text class="state-title">本月暂无支出</text>
      </view>
      <view v-else class="list">
        <view v-for="e in expenses" :key="e.id" class="item" @tap="goExpense(e.id)">
          <view class="item-main">
            <text class="item-title">{{ e.category }}</text>
            <text class="item-sub">{{ e.occurDate }}{{ e.note ? ' · ' + e.note : '' }}</text>
          </view>
          <text class="item-amt">-¥{{ formatYuan(e.amount) }}</text>
        </view>
      </view>
    </template>

    <!-- 出借 -->
    <template v-else>
      <view class="actions loan-actions">
        <view class="sub-tabs">
          <text class="sub" :class="{ on: loanView === 'person' }" @tap="loanView = 'person'">按人</text>
          <text class="sub" :class="{ on: loanView === 'loan' }" @tap="loanView = 'loan'">按笔</text>
        </view>
        <nut-button type="primary" size="small" @click="goLoanEdit()">新建出借</nut-button>
      </view>

      <view v-if="loading" class="state-box">
        <text class="state-title">加载中…</text>
      </view>
      <view v-else-if="loadError" class="state-box">
        <text class="state-title">加载失败</text>
        <text class="state-desc">{{ loadError }}</text>
        <view class="state-btn" @tap="load">点击重试</view>
      </view>

      <template v-else-if="loanView === 'person'">
        <view v-if="!counterparties.length" class="state-box">
          <text class="state-title">暂无出借记录</text>
        </view>
        <view v-else class="list">
          <view
            v-for="p in counterparties"
            :key="p.name"
            class="item"
            @tap="goPerson(p.name)"
          >
            <view class="item-main">
              <view class="loan-head">
                <text class="item-title">{{ p.name }}</text>
                <text class="badge" :class="{ settled: p.remaining <= 0 }">
                  {{ p.remaining > 0 ? `${p.openCount}笔待收` : '已结清' }}
                </text>
              </view>
              <text class="item-sub">
                共 {{ p.loanCount }} 笔 · 出借 ¥{{ formatYuan(p.principal) }} · 已还 ¥{{ formatYuan(p.repaid) }}
              </text>
            </view>
            <view class="item-right">
              <text class="item-amt" :class="{ warn: p.remaining > 0 }">
                ¥{{ formatYuan(p.remaining) }}
              </text>
              <text class="item-hint">合计待收</text>
            </view>
          </view>
        </view>
      </template>

      <template v-else>
        <view v-if="!loans.length" class="state-box">
          <text class="state-title">暂无出借记录</text>
        </view>
        <view v-else class="list">
          <view v-for="l in loans" :key="l.id" class="item" @tap="goLoanDetail(l.id)">
            <view class="item-main">
              <view class="loan-head">
                <text class="item-title">{{ l.counterparty }}</text>
                <text class="badge" :class="l.status">{{ l.status === 'settled' ? '已结清' : '待收回' }}</text>
              </view>
              <text class="item-sub">
                出借 ¥{{ formatYuan(l.principal) }} · 已还 ¥{{ formatYuan(l.repaid) }} · {{ l.lendDate }}
              </text>
            </view>
            <text class="item-amt" :class="{ warn: l.remaining > 0 }">
              ¥{{ formatYuan(l.remaining) }}
            </text>
          </view>
        </view>
      </template>
    </template>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { Button as NutButton } from '@nutui/nutui-taro'
import { api } from '@/api'
import { formatYuan } from '@/utils/ledger'
import type { LedgerCounterparty, LedgerExpense, LedgerLoan, LedgerOverview } from '@/types'

definePageConfig({ navigationBarTitleText: '记账' })

const tab = ref<'expense' | 'loan'>('expense')
const loanView = ref<'person' | 'loan'>('person')
const month = ref(new Date().toISOString().slice(0, 7))
const loading = ref(false)
const loadError = ref('')
const overview = ref<LedgerOverview | null>(null)
const expenses = ref<LedgerExpense[]>([])
const loans = ref<LedgerLoan[]>([])
const counterparties = ref<LedgerCounterparty[]>([])

function shiftMonth(delta: number) {
  const [y, m] = month.value.split('-').map(Number)
  const d = new Date(y, m - 1 + delta, 1)
  month.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const [o, e, l, c] = await Promise.all([
      api.getLedgerOverview(month.value),
      api.listLedgerExpenses(month.value),
      api.listLedgerLoans(),
      api.listLedgerCounterparties(),
    ])
    if (o.code === 0) overview.value = o.data
    else loadError.value = o.message || '加载概览失败'
    if (e.code === 0 && e.data) expenses.value = e.data
    else if (!loadError.value) loadError.value = e.message || '加载支出失败'
    if (l.code === 0 && l.data) loans.value = l.data
    else if (!loadError.value) loadError.value = l.message || '加载出借失败'
    if (c.code === 0 && c.data) counterparties.value = c.data
    else if (!loadError.value) loadError.value = c.message || '加载对方汇总失败'
  } catch {
    loadError.value = '网络异常，请稍后重试'
  } finally {
    loading.value = false
  }
}

function goExpense(id?: string) {
  Taro.navigateTo({
    url: id ? `/pages/ledger/expense-edit?id=${id}` : '/pages/ledger/expense-edit',
  })
}
function goLoanEdit() {
  Taro.navigateTo({ url: '/pages/ledger/loan-edit' })
}
function goLoanDetail(id: string) {
  Taro.navigateTo({ url: `/pages/ledger/loan-detail?id=${id}` })
}
function goPerson(name: string) {
  Taro.navigateTo({ url: `/pages/ledger/person?name=${encodeURIComponent(name)}` })
}

watch(month, load)
onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-ledger { @include page-padding; padding-bottom: 40px; }

.stats-card {
  @include card; display: flex; padding: 14px; margin-bottom: 10px;
  .stat { flex: 1; text-align: center;
    .num { display: block; font-size: 16px; font-weight: 700; color: $primary-color;
      &.warn { color: $accent-amber; }
    }
    .label { font-size: 11px; color: $text-muted; margin-top: 2px; display: block; }
  }
}

.month-row {
  display: flex; align-items: center; justify-content: center; gap: 16px; margin-bottom: 10px;
  .month-btn { @include hit-target(44px); font-size: 20px; color: $primary-color; }
  .month-label { font-size: 15px; font-weight: 600; }
}

.tabs {
  display: flex; gap: 8px; margin-bottom: 12px;
  .tab {
    @include hit-target(44px);
    flex: 1; text-align: center; border-radius: 8px;
    background: $card-bg; font-size: 13px; color: $text-secondary;
    &.on { background: $primary-light; color: $primary-color; font-weight: 600; }
  }
}

.chart-card {
  @include card; padding: 12px; margin-bottom: 10px;
  .chart-title { display: block; font-size: 13px; font-weight: 600; margin-bottom: 8px; }
  .cat-row {
    display: flex; align-items: center; gap: 6px; margin-bottom: 6px;
    .cat-name { width: 36px; font-size: 12px; color: $text-secondary; flex-shrink: 0; }
    .cat-bar-wrap {
      flex: 1; height: 8px; background: $page-bg; border-radius: 4px; overflow: hidden;
      .cat-bar { height: 100%; background: $primary-color; border-radius: 4px; }
    }
    .cat-amt { width: 58px; text-align: right; font-size: 11px; color: $text-primary; flex-shrink: 0; }
    .cat-pct { width: 36px; text-align: right; font-size: 11px; color: $text-muted; flex-shrink: 0; }
  }
}

.actions { margin-bottom: 12px; }
.loan-actions {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
}
.sub-tabs {
  display: flex; gap: 4px; background: $page-bg; border-radius: 8px; padding: 2px;
  .sub {
    font-size: 12px; padding: 5px 12px; border-radius: 6px; color: $text-secondary;
    &.on { background: $card-bg; color: $primary-color; font-weight: 600; }
  }
}
.empty { @include page-state-box; }
.state-box { @include page-state-box; margin-bottom: 12px; }
.list { display: flex; flex-direction: column; gap: 8px; }
.item {
  @include card; padding: 12px; display: flex; align-items: center; gap: 10px;
  .item-main { flex: 1; min-width: 0; }
  .loan-head { display: flex; align-items: center; gap: 6px; margin-bottom: 2px; }
  .item-title { font-size: 15px; font-weight: 600; }
  .item-sub {
    display: block; font-size: 12px; color: $text-muted; margin-top: 2px;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .item-right { text-align: right; flex-shrink: 0; }
  .item-amt {
    font-size: 15px; font-weight: 700; color: $text-primary; flex-shrink: 0;
    &.warn { color: $accent-amber; }
  }
  .item-hint { display: block; font-size: 10px; color: $text-muted; margin-top: 2px; }
  .badge {
    font-size: 10px; padding: 1px 6px; border-radius: 4px;
    background: rgba($accent-amber, 0.12); color: $accent-amber;
    &.settled { background: rgba($accent-green, 0.12); color: $success; }
  }
}
</style>
