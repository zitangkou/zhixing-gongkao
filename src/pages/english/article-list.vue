<template>
  <view class="page-en-articles">
    <view class="filter-bar">
      <text
        v-for="t in levels"
        :key="t.value"
        class="tab"
        :class="{ active: activeLevel === t.value }"
        @tap="activeLevel = t.value; load()"
      >{{ t.label }}</text>
    </view>

    <view v-if="loading" class="state-box">
      <text class="state-title">加载中…</text>
    </view>
    <view v-else-if="loadError" class="state-box">
      <text class="state-title">加载失败</text>
      <text class="state-desc">{{ loadError }}</text>
      <view class="state-btn" @tap="load">点击重试</view>
    </view>
    <view v-else-if="!articles.length" class="state-box">
      <text class="state-title">暂无英文文章</text>
      <text class="state-desc">暂无内容，稍后再来</text>
    </view>

    <view v-else class="article-list">
      <view v-for="a in articles" :key="a.id" class="art-card" @tap="goDetail(a.id)">
        <view class="art-meta">
          <text v-if="a.source" class="chip chip-soft">{{ a.source }}</text>
          <text class="chip" :class="levelClass(a.level)">{{ a.level }}</text>
          <text class="art-count">{{ a.readCount }} 次阅读</text>
        </view>
        <text class="art-title">{{ a.title }}</text>
        <text class="art-excerpt">{{ excerpt(a.content) }}</text>
        <view v-if="a.vocabHighlights.length" class="art-vocab">
          <text v-for="v in a.vocabHighlights.slice(0, 3)" :key="v.word" class="vocab-tag">{{ v.word }}</text>
          <text v-if="a.vocabHighlights.length > 3" class="vocab-more">+{{ a.vocabHighlights.length - 3 }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { api } from '@/api'
import type { EnglishArticle } from '@/types'

definePageConfig({ navigationBarTitleText: '英文文章' })

const loading = ref(false)
const loadError = ref('')
const articles = ref<EnglishArticle[]>([])
const activeLevel = ref('')

const levels = [
  { value: '', label: '全部' },
  { value: 'A2', label: 'A2' },
  { value: 'B1', label: 'B1' },
  { value: 'B2', label: 'B2' },
  { value: 'C1', label: 'C1' },
]

function levelClass(l: string) {
  return { A2: 'chip-green', B1: 'chip-blue', B2: 'chip-amber', C1: 'chip-red' }[l] || 'chip-soft'
}

function excerpt(c: string) {
  const plain = c.replace(/\s+/g, ' ').trim()
  return plain.length > 80 ? plain.slice(0, 80) + '...' : plain
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await api.listEnglishArticles(activeLevel.value || undefined)
    if (res.code === 0 && res.data) articles.value = res.data
    else {
      articles.value = []
      loadError.value = res.message || '加载失败'
    }
  } catch {
    articles.value = []
    loadError.value = '网络异常，请稍后重试'
  } finally {
    loading.value = false
  }
}

function goDetail(id: string) {
  Taro.navigateTo({ url: `/pages/english/article-detail?id=${id}` })
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-en-articles {
  @include page-padding;
  padding-bottom: 40px;
}

.filter-bar {
  display: flex;
  gap: 6px;
  margin-bottom: 14px;
  flex-wrap: wrap;
  .tab {
    @include filter-tab;
    font-size: 13px;
    background: $card-bg;
    color: $text-secondary;
    &.active { background: $primary-color; color: $on-primary; font-weight: 600; }
  }
}

.state-box { @include page-state-box; }

.art-card {
  @include card;
  padding: 14px 16px;
  border-radius: $radius-lg;
  margin-bottom: 12px;
  &:active { opacity: 0.85; }
}

.art-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  flex-wrap: wrap;
  .chip {
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
  }
  .chip-red { color: $primary-color; background: $primary-light; }
  .chip-blue { color: $accent-blue; background: rgba($accent-blue, 0.1); }
  .chip-green { color: $accent-green; background: rgba($accent-green, 0.1); }
  .chip-amber { color: $accent-amber; background: rgba($accent-amber, 0.12); }
  .chip-soft { color: $text-secondary; background: $chip-bg; }
  .art-count { margin-left: auto; font-size: 11px; color: $text-muted; }
}

.art-title {
  display: block;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.5;
  margin-bottom: 6px;
}

.art-excerpt {
  display: block;
  font-size: 13px;
  color: $text-secondary;
  line-height: 1.5;
  margin-bottom: 8px;
}

.art-vocab {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  align-items: center;
  .vocab-tag {
    font-size: 11px;
    padding: 1px 8px;
    border-radius: 3px;
    background: rgba($accent-blue, 0.1);
    color: $accent-blue;
  }
  .vocab-more { font-size: 11px; color: $text-muted; }
}
</style>
