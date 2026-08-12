<template>
  <view class="page-grammar">
    <view v-if="loading" class="empty">加载中...</view>
    <view v-else-if="!lessons.length" class="empty">
      <text class="empty-title">暂无语法课程</text>
    </view>
    <view v-else>
      <view v-for="cat in groupedByCategory" :key="cat.category" class="cat-group">
        <text class="cat-title" @tap="toggleCat(cat.category)">{{ cat.category || '未分类' }} ({{ cat.lessons.length }}) <text class="arrow">{{ expanded[cat.category] ? '▾' : '▸' }}</text></text>
        <view v-if="expanded[cat.category]" class="cat-body">
          <view v-for="g in cat.lessons" :key="g.id" class="g-row" @tap="goDetail(g.id)">
            <view class="g-main">
              <text class="g-title">{{ g.title }}</text>
              <text class="g-level">{{ g.level }}</text>
            </view>
            <text v-if="progressMap[g.id]" class="g-status" :class="progressMap[g.id]">{{ statusLabel(progressMap[g.id]) }}</text>
            <text class="g-arrow">›</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { api } from '@/api'
import type { GrammarLesson } from '@/types'

definePageConfig({ navigationBarTitleText: '语法句式' })

const loading = ref(false)
const lessons = ref<GrammarLesson[]>([])
const expanded = ref<Record<string, boolean>>({})
const progressMap = ref<Record<string, string>>({})

const groupedByCategory = computed(() => {
  const map: Record<string, GrammarLesson[]> = {}
  const order: string[] = []
  for (const g of lessons.value) {
    const c = g.category || '未分类'
    if (!map[c]) {
      map[c] = []
      order.push(c)
    }
    map[c].push(g)
  }
  return order.map((c) => ({ category: c, lessons: map[c] }))
})

function statusLabel(s: string) {
  return { learning: '学习中', mastered: '已掌握' }[s] || s
}

function toggleCat(c: string) {
  expanded.value = { ...expanded.value, [c]: !expanded.value[c] }
}

async function load() {
  loading.value = true
  try {
    const res = await api.listGrammarLessons()
    if (res.code === 0 && res.data) {
      lessons.value = res.data
      // 默认展开第一个分类
      if (groupedByCategory.value.length && expanded.value[groupedByCategory.value[0].category] === undefined) {
        expanded.value[groupedByCategory.value[0].category] = true
      }
    }
  } finally {
    loading.value = false
  }
}

function goDetail(id: string) {
  Taro.navigateTo({ url: `/pages/english/grammar-detail?id=${id}` })
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-grammar {
  @include page-padding;
  padding-bottom: 40px;
}

.empty {
  text-align: center;
  padding: 50px 20px;
  .empty-title { display: block; font-size: 15px; color: $text-secondary; }
}

.cat-group {
  @include card;
  padding: 12px 16px;
  border-radius: $radius-lg;
  margin-bottom: 10px;
  .cat-title { display: flex; justify-content: space-between; align-items: center; font-size: 14px; font-weight: 600; .arrow { color: $text-muted; } }
}

.cat-body {
  margin-top: 8px;
  border-top: 1px solid $border-color;
  padding-top: 8px;
}

.g-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid $border-color;
  &:last-child { border-bottom: none; }
  &:active { opacity: 0.7; }
  .g-main { flex: 1; .g-title { font-size: 14px; color: $text-primary; } .g-level { display: block; font-size: 11px; color: $text-muted; } }
  .g-status {
    font-size: 10px;
    padding: 1px 6px;
    border-radius: 3px;
    &.learning { color: $accent-amber; background: rgba($accent-amber, 0.12); }
    &.mastered { color: $on-primary; background: $success; }
  }
  .g-arrow { color: $text-muted; }
}
</style>
