<template>
  <view class="page-assets">
    <view class="tabs">
      <text
        v-for="t in tabs"
        :key="t.value"
        class="tab"
        :class="{ on: tab === t.value }"
        @tap="tab = t.value; load()"
      >{{ t.label }}</text>
    </view>

    <view v-if="loading" class="empty">加载中...</view>

    <template v-else-if="tab === 'daily'">
      <view v-if="!dailies.length" class="empty">暂无每日记录</view>
      <view v-else class="list">
        <view v-for="d in dailies" :key="d.id" class="card">
          <text class="head">{{ d.logDate }} · 《{{ d.bookTitle }}》</text>
          <text v-if="d.chapter" class="sub">{{ d.chapter }}</text>
          <text class="body">{{ dailyText(d) }}</text>
        </view>
      </view>
    </template>

    <template v-else-if="tab === 'persons'">
      <nut-button size="small" type="primary" class="add" @click="goPerson()">+ 人物卡</nut-button>
      <view v-if="!persons.length" class="empty">
        <text>暂无人物卡</text>
        <text class="hint">读到印象深的人物时记一张即可</text>
      </view>
      <view v-else class="list">
        <view v-for="p in persons" :key="p.id" class="card" @tap="goPerson(p.id)">
          <text class="head">{{ p.name }} · 《{{ p.bookTitle }}》</text>
          <text class="body">{{ personText(p) }}</text>
        </view>
      </view>
    </template>

    <template v-else>
      <view v-if="!summaries.length" class="empty">
        <text>还没有「一书一页」</text>
        <text class="hint">全书读完后写一两句带走什么即可。</text>
      </view>
      <view v-else class="list">
        <view v-for="s in summaries" :key="s.id" class="card" @tap="goSummary(s.bookId)">
          <text class="head">《{{ s.bookTitle }}》</text>
          <text class="body">{{ s.coreQuestion || s.insights?.[0] || '（草稿）' }}</text>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Taro, { useRouter, useDidShow } from '@tarojs/taro'
import { Button as NutButton } from '@nutui/nutui-taro'
import { api } from '@/api'
import type { DushuBookSummary, DushuDailyLog, DushuPersonCard } from '@/types'
import { flattenOutput } from '@/utils/dushu'

definePageConfig({ navigationBarTitleText: '知识资产' })

const router = useRouter()
const tab = ref<'daily' | 'persons' | 'summaries'>((router.params?.tab as any) || 'daily')
const bookId = router.params?.bookId || ''
const loading = ref(false)
const dailies = ref<DushuDailyLog[]>([])
const persons = ref<DushuPersonCard[]>([])
const summaries = ref<DushuBookSummary[]>([])

const tabs = [
  { value: 'daily' as const, label: '每日卡' },
  { value: 'persons' as const, label: '人物卡' },
  { value: 'summaries' as const, label: '一书一页' },
]

function dailyText(d: DushuDailyLog) {
  return flattenOutput(d.output) || d.oralNote || d.goal || '（空）'
}

function personText(p: DushuPersonCard) {
  if (p.lesson?.trim()) return p.lesson
  return [p.trait, p.success, p.failure].filter((x) => x?.trim()).join(' · ') || '（空）'
}

async function load() {
  loading.value = true
  try {
    if (tab.value === 'daily') {
      const res = await api.listDushuDaily(bookId || undefined)
      if (res.code === 0 && res.data) dailies.value = res.data
    } else if (tab.value === 'persons') {
      const res = await api.listDushuPersons(bookId || undefined)
      if (res.code === 0 && res.data) persons.value = res.data
    } else {
      const res = await api.listDushuSummaries()
      if (res.code === 0 && res.data) summaries.value = res.data
    }
  } finally {
    loading.value = false
  }
}

function goPerson(id?: string) {
  const q = id ? `id=${id}` : `bookId=${bookId || ''}`
  Taro.navigateTo({ url: `/pages/dushu/person-edit?${q}` })
}
function goSummary(bid: string) {
  Taro.navigateTo({ url: `/pages/dushu/summary-edit?bookId=${bid}` })
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-assets { @include page-padding; padding-bottom: 40px; }
.tabs { display: flex; gap: 8px; margin-bottom: 12px;
  .tab {
    flex: 1; text-align: center; padding: 8px; border-radius: 8px; background: $card-bg; font-size: 13px;
    &.on { background: $primary-light; color: $primary-color; font-weight: 700; }
  }
}
.add { margin-bottom: 10px; }
.empty { text-align: center; padding: 40px 16px; color: $text-muted;
  .hint { display: block; margin-top: 6px; font-size: 12px; }
}
.list { display: flex; flex-direction: column; gap: 8px; }
.card {
  @include card; padding: 12px;
  .head { display: block; font-size: 13px; font-weight: 700; margin-bottom: 4px; }
  .sub { display: block; font-size: 12px; color: $text-muted; margin-bottom: 4px; }
  .body { display: block; font-size: 13px; line-height: 1.45; margin-top: 2px;
    &.oral { color: $primary-color; margin-top: 6px; }
  }
  .tags { display: block; margin-top: 6px; font-size: 11px; color: $primary-color; }
}
</style>
