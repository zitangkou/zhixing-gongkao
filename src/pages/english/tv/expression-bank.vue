<template>
  <view class="page-bank">
    <view class="filter-bar">
      <text
        v-for="t in tabs"
        :key="t.value"
        class="tab"
        :class="{ active: activeTab === t.value }"
        @tap="activeTab = t.value; load()"
      >
        {{ t.label }}{{ t.value === 'review' && dueHint ? ` ${dueHint}` : '' }}
      </text>
    </view>

    <view v-if="loading" class="empty">加载中...</view>
    <view v-else-if="!list.length" class="empty">
      <text class="empty-title">{{ emptyTitle }}</text>
      <text class="empty-desc">在场景精学的「精拆」步骤从对白生成表达卡</text>
    </view>

    <view v-else class="list">
      <view v-for="e in list" :key="e.id" class="card" :class="{ mastered: e.mastered }">
        <text class="phrase" @tap="play(e.phrase)">{{ e.phrase }}</text>
        <text v-if="e.meaning" class="meaning">{{ e.meaning }}</text>
        <text v-if="e.usageScene" class="meta">场景 · {{ e.usageScene }}</text>
        <text v-if="e.myExample" class="meta">造句 · {{ e.myExample }}</text>
        <text v-if="e.sourceLine" class="source">原句 · {{ e.sourceLine }}</text>
        <view class="actions">
          <text class="act" @tap="play(e.phrase)">🔊</text>
          <template v-if="!e.mastered">
            <text class="act" @tap="onReview(e.id, 'again')">再练</text>
            <text class="act good" @tap="onReview(e.id, 'good')">记住了</text>
          </template>
          <text class="act danger" @tap="onDelete(e)">删除</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useDidShow, useRouter } from '@tarojs/taro'
import { api } from '@/api'
import { playPronounce } from '@/utils/pronounce'
import { showConfirm, showToast } from '@/utils/platform'
import type { TvExpression } from '@/types'

definePageConfig({ navigationBarTitleText: '表达库' })

const tabs = [
  { value: 'learning', label: '学习中' },
  { value: 'review', label: '待复习' },
  { value: 'mastered', label: '已掌握' },
]
const router = useRouter()
const tabFromQuery = router.params?.tab
const activeTab = ref(
  tabFromQuery && tabs.some((t) => t.value === tabFromQuery) ? tabFromQuery : 'learning',
)
const loading = ref(false)
const list = ref<TvExpression[]>([])
const dueHint = ref(0)

const emptyTitle = computed(() => {
  if (activeTab.value === 'review') return '今日无待复习句型'
  if (activeTab.value === 'mastered') return '还没有已掌握句型'
  return '暂无表达卡'
})

function play(text: string) {
  playPronounce(text)
}

async function onReview(id: string, result: 'again' | 'good') {
  const res = await api.reviewTvExpression(id, result)
  if (res.code === 0) {
    showToast(result === 'good' ? '已排期下一档' : '明天再练', 'success')
    load()
  }
}

async function onDelete(e: TvExpression) {
  const ok = await showConfirm('删除表达卡', `确定删除「${e.phrase}」？`)
  if (!ok) return
  const res = await api.deleteTvExpression(e.id)
  if (res.code === 0) {
    list.value = list.value.filter((x) => x.id !== e.id)
    showToast('已删除', 'success')
  }
}

async function load() {
  loading.value = true
  try {
    const res = await api.listTvExpressions(activeTab.value as 'learning' | 'review' | 'mastered')
    if (res.code === 0 && res.data) list.value = res.data
    if (activeTab.value === 'review') dueHint.value = list.value.length
    else {
      const due = await api.listTvExpressionsDue()
      if (due.code === 0 && due.data) dueHint.value = due.data.length
    }
  } finally {
    loading.value = false
  }
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-bank {
  @include page-padding;
  padding-bottom: 40px;
}

.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  .tab {
    font-size: 13px;
    padding: 6px 12px;
    border-radius: 999px;
    background: $card-bg;
    color: $text-muted;
    border: 1px solid $border-color;
    &.active {
      background: $primary-light;
      color: $primary-color;
      border-color: transparent;
      font-weight: 600;
    }
    .badge {
      margin-left: 4px;
      font-size: 11px;
    }
  }
}

.card {
  @include card;
  padding: 12px 14px;
  margin-bottom: 8px;
  border-radius: $radius-lg;
  &.mastered { opacity: 0.75; }
  .phrase { display: block; font-size: 16px; font-weight: 700; color: $text-primary; }
  .meaning { display: block; font-size: 13px; color: $text-secondary; margin-top: 6px; }
  .meta { display: block; font-size: 12px; color: $text-muted; margin-top: 4px; }
  .source { display: block; font-size: 12px; color: $text-muted; margin-top: 4px; font-style: italic; }
  .actions { display: flex; gap: 4px; margin-top: 6px; flex-wrap: wrap; }
  .act {
    @include list-act;
    &.danger { color: $text-muted; }
    &.good { color: $primary-color; }
  }
}

.empty {
  text-align: center;
  padding: 40px 16px;
  .empty-title { display: block; font-size: 15px; font-weight: 600; }
  .empty-desc { display: block; font-size: 12px; color: $text-muted; margin-top: 6px; }
}
</style>
