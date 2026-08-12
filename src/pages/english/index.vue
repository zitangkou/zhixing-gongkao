<template>
  <view class="page-english">
    <view class="hero-card">
      <view class="hero-row">
        <view class="hero-item">
          <text class="hero-num">{{ statsReady ? stats.todayMinutes : '—' }}</text>
          <text class="hero-label">今日(min)</text>
        </view>
        <view class="hero-item">
          <text class="hero-num">{{ statsReady ? stats.weekMinutes : '—' }}</text>
          <text class="hero-label">本周(min)</text>
        </view>
        <view class="hero-item">
          <text class="hero-num">{{ statsReady ? stats.reviewVocabCount : '—' }}</text>
          <text class="hero-label">待复习</text>
        </view>
      </view>
    </view>
    <view v-if="loadError" class="state-box">
      <text class="state-title">加载失败</text>
      <text class="state-desc">{{ loadError }}</text>
      <view class="state-btn" @tap="load">点击重试</view>
    </view>

    <view class="entry-grid">
      <view class="entry-item" @tap="go('/pages/english/article-list')">
        <view class="entry-icon-wrap"><IconImage :color="brandIcon" size="22" /></view>
        <text class="entry-name">英文文章</text>
        <text class="entry-desc">阅读 + 生词</text>
      </view>
      <view class="entry-item" @tap="go('/pages/english/vocab')">
        <view class="entry-icon-wrap"><Star :color="brandIcon" size="22" /></view>
        <text class="entry-name">生词本</text>
        <text class="entry-desc">{{ statsReady ? `${stats.reviewVocabCount} 待复习` : '生词复习' }}</text>
      </view>
      <view class="entry-item" @tap="go('/pages/english/speaking-list')">
        <view class="entry-icon-wrap"><Voice :color="brandIcon" size="22" /></view>
        <text class="entry-name">跟读本</text>
        <text class="entry-desc">文章收藏句子</text>
      </view>
      <view class="entry-item" @tap="go('/pages/english/phonetic')">
        <view class="entry-icon-wrap"><Voice :color="brandIcon" size="22" /></view>
        <text class="entry-name">音标学习</text>
        <text class="entry-desc">DJ 48 音标</text>
      </view>
      <view class="entry-item" @tap="go('/pages/english/tv/index')">
        <view class="entry-icon-wrap"><Voice :color="brandIcon" size="22" /></view>
        <text class="entry-name">美剧口语</text>
        <text class="entry-desc">
          {{ tvDue > 0 ? `${tvDue} 句待复习` : '场景精学 + 句型卡' }}
        </text>
      </view>
    </view>

    <view v-if="stats.recentLogs.length" class="recent">
      <text class="block-title">最近学习</text>
      <view v-for="log in stats.recentLogs.slice(0, 5)" :key="log.id" class="log-row">
        <text class="log-type" :class="`type-${log.logType}`">{{ logTypeLabel(log.logType) }}</text>
        <text class="log-meta">{{ log.studyDate }}</text>
        <text v-if="log.durationSec" class="log-dur">{{ Math.round(log.durationSec / 60) }}min</text>
        <text v-if="log.wordsLearned" class="log-extra">+{{ log.wordsLearned }}词</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { Image as IconImage, Star, Voice } from '@nutui/icons-vue-taro'
import { api } from '@/api'
import type { EnglishStats } from '@/types'
import { useBrandColor } from '@/utils/brandColor'

definePageConfig({ navigationBarTitleText: '英语学习' })

const { brandColor: brandIcon } = useBrandColor()

const stats = ref<EnglishStats>({
  todayMinutes: 0, weekMinutes: 0, newVocabCount: 0, reviewVocabCount: 0,
  speakingCount: 0, grammarMasteredCount: 0, grammarLearningCount: 0, articleReadCount: 0,
  recentLogs: [],
})
const statsReady = ref(false)
const loadError = ref('')
const tvDue = ref(0)

function logTypeLabel(t: string) {
  return { article: '文章', speaking: '口语', grammar: '语法', vocab: '生词' }[t] || t
}

function go(url: string) {
  Taro.navigateTo({ url })
}

async function load() {
  loadError.value = ''
  try {
    const res = await api.getEnglishStats()
    if (res.code === 0 && res.data) {
      stats.value = res.data
      statsReady.value = true
    } else {
      loadError.value = res.message || '加载学习数据失败'
    }
  } catch {
    loadError.value = '网络异常，请稍后重试'
  }
  try {
    const hub = await api.getTvHub()
    if (hub.code === 0 && hub.data) tvDue.value = hub.data.expressionDueCount || 0
  } catch {
    /* mock / 未登录时忽略 */
  }
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-english {
  @include page-padding;
  padding-bottom: 40px;
}

.state-box {
  @include page-state-box;
  margin-bottom: 14px;
}

.hero-card {
  @include card;
  padding: 16px 14px;
  border-radius: $radius-lg;
  margin-bottom: 14px;
  background: linear-gradient(168deg, $primary-light 0%, $card-bg 70%);
  .hero-row { display: flex; .hero-item { flex: 1; text-align: center; .hero-num { display: block; font-size: 22px; font-weight: 700; color: $primary-color; } .hero-label { display: block; font-size: 12px; color: $text-muted; margin-top: 2px; } } }
}

.entry-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 14px;
}

.entry-item {
  @include card;
  padding: 14px 12px;
  border-radius: $radius-lg;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  &:active { opacity: 0.85; }
  .entry-icon-wrap {
    @include icon-tile;
    margin-bottom: 2px;
  }
  .entry-name { font-size: 14px; font-weight: 600; color: $text-primary; }
  .entry-desc { font-size: 12px; color: $text-muted; }
}

.recent {
  @include card;
  padding: 12px 14px;
  border-radius: $radius-lg;
  .block-title {
    display: block;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
    padding-bottom: 8px;
    border-bottom: 1px solid $border-color;
  }
}

.log-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  font-size: 12px;
  border-bottom: 1px solid $border-color;
  &:last-child { border-bottom: none; }
  .log-type {
    font-weight: 600;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 11px;
    &.type-article { color: $primary-color; background: $primary-light; }
    &.type-speaking { color: $accent-blue; background: rgba($accent-blue, 0.1); }
    &.type-grammar { color: $accent-green; background: rgba($accent-green, 0.1); }
    &.type-vocab { color: $accent-amber; background: rgba($accent-amber, 0.12); }
  }
  .log-meta { color: $text-muted; }
  .log-dur { margin-left: auto; color: $text-secondary; }
  .log-extra { color: $primary-color; }
}
</style>
