<template>
  <view class="page-vocab">
    <view class="filter-bar">
      <text
        v-for="t in tabs"
        :key="t.value"
        class="tab"
        :class="{ active: activeTab === t.value }"
        @tap="activeTab = t.value; load()"
      >{{ t.label }}<text v-if="t.value === 'review' && reviewCount" class="badge">{{ reviewCount }}</text></text>
    </view>

    <view v-if="loading" class="state-box">
      <text class="state-title">加载中…</text>
    </view>
    <view v-else-if="loadError" class="state-box">
      <text class="state-title">加载失败</text>
      <text class="state-desc">{{ loadError }}</text>
      <view class="state-btn" @tap="load">点击重试</view>
    </view>
    <view v-else-if="!vocabs.length" class="state-box">
      <text class="state-title">{{ activeTab === 'review' ? '今日无待复习单词' : '暂无生词' }}</text>
      <text class="state-desc">阅读英文文章时长按单词可加入生词本</text>
    </view>

    <view v-else class="vocab-list">
      <view v-for="v in vocabs" :key="v.id" class="vocab-card" :class="{ mastered: v.mastered }">
        <view class="v-head">
          <text class="v-word" @tap="play(v.word)">{{ v.word }}</text>
          <text v-if="v.phonetic" class="v-phon">{{ v.phonetic }}</text>
          <text v-if="v.pos" class="v-pos">{{ v.pos }}</text>
          <text class="v-play" @tap="play(v.word)">🔊</text>
          <text class="v-fam" :class="`fam-${v.familiarity}`">★{{ v.familiarity }}</text>
        </view>
        <text v-if="v.meaning" class="v-meaning">{{ v.meaning }}</text>
        <text v-if="v.exampleSentence" class="v-example">{{ v.exampleSentence }}</text>
        <view class="v-actions">
          <text v-if="!v.mastered" class="act" @tap="onReview(v)">复习+1</text>
          <text class="act" @tap="onMaster(v)">{{ v.mastered ? '取消掌握' : '已掌握' }}</text>
          <text class="act danger" @tap="onDelete(v)">删除</text>
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
import type { UserVocab } from '@/types'

definePageConfig({ navigationBarTitleText: '生词本' })

const loading = ref(false)
const loadError = ref('')
const vocabs = ref<UserVocab[]>([])
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

const reviewCount = computed(() => vocabs.value.length)

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await api.listVocabs(activeTab.value as 'learning' | 'mastered' | 'review')
    if (res.code === 0 && res.data) vocabs.value = res.data
    else {
      vocabs.value = []
      loadError.value = res.message || '加载失败'
    }
  } catch {
    vocabs.value = []
    loadError.value = '网络异常，请稍后重试'
  } finally {
    loading.value = false
  }
}

function play(word: string) {
  playPronounce(word)
}

async function onReview(v: UserVocab) {
  const newFam = Math.min(5, v.familiarity + 1)
  const res = await api.updateVocab(v.id, { familiarity: newFam })
  if (res.code === 0 && res.data) {
    Object.assign(v, res.data)
    showToast(`熟悉度 → ${newFam}`, 'success')
    api.addEnglishLog({ logType: 'vocab', refId: v.id, wordsLearned: 1 }).catch(() => {})
  }
}

async function onMaster(v: UserVocab) {
  const res = await api.updateVocab(v.id, { mastered: !v.mastered, familiarity: v.mastered ? 1 : 5 })
  if (res.code === 0 && res.data) {
    Object.assign(v, res.data)
    showToast(v.mastered ? '已标记掌握' : '已取消', 'success')
    load()
  }
}

async function onDelete(v: UserVocab) {
  const ok = await showConfirm('删除生词', `确定删除「${v.word}」？`)
  if (!ok) return
  const res = await api.deleteVocab(v.id)
  if (res.code === 0) {
    vocabs.value = vocabs.value.filter((x) => x.id !== v.id)
    showToast('已删除', 'success')
  }
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-vocab {
  @include page-padding;
  padding-bottom: 40px;
}

.filter-bar {
  display: flex;
  gap: 6px;
  margin-bottom: 14px;
  .tab {
    @include filter-tab;
    font-size: 13px;
    background: $card-bg;
    color: $text-secondary;
    &.active {
      background: $primary-color;
      color: $on-primary;
      font-weight: 600;
      .badge { background: $on-primary; color: $primary-color; }
    }
    .badge {
      display: inline-block;
      margin-left: 4px;
      padding: 0 5px;
      min-width: 14px;
      height: 14px;
      line-height: 14px;
      text-align: center;
      background: $elevated;
      color: $primary-color;
      border-radius: 8px;
      font-size: 10px;
      font-weight: 700;
    }
  }
}

.state-box { @include page-state-box; }

.vocab-card {
  @include card;
  padding: 12px 14px;
  border-radius: $radius-md;
  margin-bottom: 10px;
  &.mastered { opacity: 0.6; .v-word { color: $text-muted; text-decoration: line-through; } }
}

.v-head {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 6px;
  flex-wrap: wrap;
  .v-word { font-size: 16px; font-weight: 600; color: $accent-blue; }
  .v-phon { font-size: 12px; color: $text-muted; font-style: italic; }
  .v-pos { font-size: 11px; color: $text-muted; }
  .v-play { font-size: 16px; }
  .v-fam { margin-left: auto; font-size: 11px; font-weight: 700; padding: 1px 6px; border-radius: 3px; &.fam-1 { color: $text-muted; background: $chip-bg; } &.fam-2 { color: $accent-amber; background: rgba($accent-amber, 0.12); } &.fam-3 { color: $accent-blue; background: rgba($accent-blue, 0.1); } &.fam-4 { color: $accent-green; background: rgba($accent-green, 0.1); } &.fam-5 { color: $on-primary; background: $success; } }
}

.v-meaning {
  display: block;
  font-size: 13px;
  color: $text-primary;
  margin-bottom: 4px;
}

.v-example {
  display: block;
  font-size: 12px;
  color: $text-secondary;
  line-height: 1.5;
  font-style: italic;
  padding: 6px 8px;
  background: $page-bg;
  border-radius: 4px;
  margin-bottom: 8px;
}

.v-actions {
  display: flex;
  gap: 4px;
  border-top: 1px solid $border-color;
  padding-top: 4px;
  flex-wrap: wrap;
  .act { @include list-act; }
}
</style>
