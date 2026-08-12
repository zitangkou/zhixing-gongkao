<template>
  <view class="page-detail">
    <view v-if="loading" class="empty">加载中...</view>
    <template v-else-if="loan">
      <view class="summary">
        <view class="sum-head">
          <text class="name">{{ loan.counterparty }}</text>
          <text class="badge" :class="loan.status">{{ loan.status === 'settled' ? '已结清' : '待收回' }}</text>
        </view>
        <view class="sum-row">
          <view class="cell">
            <text class="v">¥{{ formatYuan(loan.principal) }}</text>
            <text class="k">本金</text>
          </view>
          <view class="cell">
            <text class="v">¥{{ formatYuan(loan.repaid) }}</text>
            <text class="k">已还</text>
          </view>
          <view class="cell">
            <text class="v warn">¥{{ formatYuan(loan.remaining) }}</text>
            <text class="k">待收</text>
          </view>
        </view>
        <text class="meta">出借 {{ loan.lendDate }}{{ loan.dueDate ? ` · 约定 ${loan.dueDate}` : '' }}</text>
        <text v-if="loan.note" class="note">{{ loan.note }}</text>
        <view v-if="loan.images?.length" class="imgs">
          <image
            v-for="(url, i) in loan.images"
            :key="i"
            class="thumb"
            :src="media(url)"
            mode="aspectFill"
            @tap="preview(loan.images, i)"
          />
        </view>
      </view>

      <view class="actions">
        <nut-button v-if="loan.remaining > 0" type="primary" size="small" @click="goRepay">
          登记归还
        </nut-button>
        <nut-button plain type="primary" size="small" @click="goEdit">编辑</nut-button>
      </view>

      <text class="sec-title">归还流水</text>
      <view v-if="!(loan.repayments || []).length" class="empty soft">暂无归还记录</view>
      <view v-else class="list">
        <view v-for="r in loan.repayments" :key="r.id" class="item">
          <view class="item-main">
            <text class="item-title">+¥{{ formatYuan(r.amount) }}</text>
            <text class="item-sub">{{ r.repayDate }} · {{ r.method }}{{ r.note ? ' · ' + r.note : '' }}</text>
            <view v-if="r.images?.length" class="imgs sm">
              <image
                v-for="(url, i) in r.images"
                :key="i"
                class="thumb"
                :src="media(url)"
                mode="aspectFill"
                @tap="preview(r.images, i)"
              />
            </view>
          </view>
          <text class="act danger" @tap="onDeleteRepay(r.id)">删</text>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Taro, { useDidShow, useRouter } from '@tarojs/taro'
import { Button as NutButton } from '@nutui/nutui-taro'
import { api } from '@/api'
import { formatYuan } from '@/utils/ledger'
import { resolveMediaUrl } from '@/utils/media'
import { showConfirm, showToast } from '@/utils/platform'
import type { LedgerLoan } from '@/types'

definePageConfig({ navigationBarTitleText: '出借详情' })

const router = useRouter()
const id = ref(router.params?.id || '')
const loading = ref(false)
const loan = ref<LedgerLoan | null>(null)

function media(url: string) {
  return resolveMediaUrl(url)
}

function preview(urls: string[], i: number) {
  Taro.previewImage({ current: media(urls[i]), urls: urls.map(media) })
}

async function load() {
  if (!id.value) return
  loading.value = true
  try {
    const res = await api.getLedgerLoan(id.value)
    if (res.code === 0) loan.value = res.data
    else showToast(res.message || '加载失败', 'error')
  } finally {
    loading.value = false
  }
}

function goRepay() {
  Taro.navigateTo({
    url: `/pages/ledger/repay-edit?loanId=${id.value}&remaining=${loan.value?.remaining || 0}`,
  })
}
function goEdit() {
  Taro.navigateTo({ url: `/pages/ledger/loan-edit?id=${id.value}` })
}

async function onDeleteRepay(repayId: string) {
  const ok = await showConfirm('删除归还', '确定删除这条归还记录？')
  if (!ok) return
  const res = await api.deleteLedgerRepayment(repayId)
  if (res.code === 0) {
    showToast('已删除', 'success')
    load()
  } else {
    showToast(res.message || '删除失败', 'error')
  }
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';
.page-detail { @include page-padding; padding-bottom: 40px; }
.summary {
  @include card; padding: 14px; margin-bottom: 12px;
  .sum-head { display: flex; align-items: center; gap: 8px; margin-bottom: 12px;
    .name { font-size: 18px; font-weight: 700; }
  }
  .badge {
    font-size: 11px; padding: 2px 8px; border-radius: 4px;
    background: rgba($accent-amber, 0.12); color: $accent-amber;
    &.settled { background: rgba($accent-green, 0.12); color: $success; }
  }
  .sum-row { display: flex; margin-bottom: 8px;
    .cell { flex: 1; text-align: center;
      .v { display: block; font-size: 16px; font-weight: 700;
        &.warn { color: $accent-amber; }
      }
      .k { font-size: 11px; color: $text-muted; }
    }
  }
  .meta, .note { display: block; font-size: 12px; color: $text-muted; line-height: 1.45; }
  .note { margin-top: 4px; color: $text-secondary; }
}
.actions { display: flex; gap: 8px; margin-bottom: 14px; }
.sec-title { display: block; font-size: 14px; font-weight: 700; margin-bottom: 8px; }
.empty { text-align: center; padding: 40px; color: $text-muted;
  &.soft { padding: 20px; font-size: 13px; }
}
.list { display: flex; flex-direction: column; gap: 8px; }
.item {
  @include card; padding: 12px; display: flex; gap: 8px; align-items: flex-start;
  .item-main { flex: 1; min-width: 0; }
  .item-title { font-size: 15px; font-weight: 600; color: $success; }
  .item-sub { display: block; font-size: 12px; color: $text-muted; margin-top: 2px; }
  .act.danger { @include list-act; color: $danger; font-size: 13px; }
}
.imgs {
  display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;
  &.sm .thumb { width: 48px; height: 48px; }
  .thumb { width: 64px; height: 64px; border-radius: 6px; background: $page-bg; }
}
</style>
