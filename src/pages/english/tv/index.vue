<template>
  <view class="page-tv">
    <view class="hero">
      <view class="hero-text">
        <text class="hero-title">美剧口语</text>
        <text class="hero-desc">精拆场景 · 句型卡 · 跟读置换</text>
      </view>
      <view class="hero-btn" @tap="showForm = !showForm">{{ showForm ? '收起' : '+ 加剧' }}</view>
    </view>

    <view v-if="showForm" class="form-card">
      <text class="form-label">剧名 *</text>
      <nut-input v-model="form.title" placeholder="剧名，如老友记" />
      <text class="form-label">难度</text>
      <view class="stage-row">
        <text
          v-for="s in stages"
          :key="s.value"
          class="stage"
          :class="{ on: form.stage === s.value }"
          @tap="form.stage = s.value"
        >{{ s.label }}</text>
      </view>
      <text class="form-label">为何选这部（可选）</text>
      <nut-input v-model="form.reason" placeholder="日常口语 / 语速适中…" />
      <nut-button type="primary" size="small" block :loading="saving" class="save-btn" @click="onCreateShow">
        保存剧目
      </nut-button>
    </view>

    <view class="stats-row" v-if="hub">
      <view class="stat" @tap="goBank('review')">
        <text class="num" :class="{ warn: hub.expressionDueCount > 0 }">{{ hub.expressionDueCount }}</text>
        <text class="label">待复习</text>
      </view>
      <view class="stat-divider" />
      <view class="stat" @tap="goBank('learning')">
        <text class="num">{{ hub.expressionTotal }}</text>
        <text class="label">表达卡</text>
      </view>
      <view class="stat-divider" />
      <view class="stat" @tap="goBank('mastered')">
        <text class="num">{{ hub.expressionMastered }}</text>
        <text class="label">已掌握</text>
      </view>
      <view class="stat-divider" />
      <view class="stat" @tap="goWeekly">
        <text class="num">{{ hub.showCount }}</text>
        <text class="label">剧目</text>
      </view>
    </view>

    <view class="quick-row">
      <text class="quick" @tap="goBank('review')">表达库 ›</text>
      <text class="quick" @tap="goWeekly">周复盘 ›</text>
    </view>

    <view v-if="hub?.activeScenes?.length" class="block">
      <text class="block-title">今日进行中</text>
      <view
        v-for="s in hub.activeScenes"
        :key="s.id"
        class="scene-row"
        @tap="goStudy(s.id)"
      >
        <view class="scene-main">
          <text class="scene-title">{{ s.title }}</text>
          <text class="scene-meta">
            {{ s.todaySession?.completedCount || 0 }}/5 步{{ s.timeRange ? ` · ${s.timeRange}` : '' }}
          </text>
        </view>
        <text class="arrow">›</text>
      </view>
    </view>

    <view class="block">
      <text class="block-title">我的剧目</text>
      <view v-if="loading" class="empty">加载中...</view>
      <view v-else-if="!shows.length" class="empty">
        <text class="empty-title">还没有剧目</text>
        <text class="empty-desc">添加一部剧后，再建集与精学场景</text>
        <view class="empty-btn" @tap="showForm = true">添加第一部</view>
      </view>
      <view
        v-for="show in shows"
        :key="show.id"
        class="show-card"
        @tap="goShow(show.id)"
      >
        <view class="show-main">
          <text class="show-title">{{ show.title }}</text>
          <text class="show-meta">
            {{ stageLabel(show.stage) }} · {{ show.episodeCount }} 集 · {{ show.expressionCount }} 卡
          </text>
          <text v-if="show.reason" class="show-reason">{{ show.reason }}</text>
        </view>
        <text class="arrow">›</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput } from '@nutui/nutui-taro'
import { api } from '@/api'
import { showToast } from '@/utils/platform'
import type { TvHub, TvShow } from '@/types'

definePageConfig({ navigationBarTitleText: '美剧口语' })

const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const hub = ref<TvHub | null>(null)
const shows = ref<TvShow[]>([])
const stages = [
  { value: 'beginner', label: '入门' },
  { value: 'intermediate', label: '进阶' },
  { value: 'advanced', label: '高阶' },
]
const form = reactive({
  title: '',
  stage: 'beginner',
  reason: '',
})

function stageLabel(s: string) {
  return { beginner: '入门', intermediate: '进阶', advanced: '高阶' }[s] || s
}

function go(url: string) {
  Taro.navigateTo({ url })
}

function goShow(id: string) {
  go(`/pages/english/tv/show?id=${id}`)
}

function goStudy(id: string) {
  go(`/pages/english/tv/scene-study?id=${id}`)
}

function goBank(tab: string) {
  go(`/pages/english/tv/expression-bank?tab=${tab}`)
}

function goWeekly() {
  go('/pages/english/tv/weekly')
}

async function onCreateShow() {
  const title = form.title.trim()
  if (!title) {
    showToast('请填写剧名', 'none')
    return
  }
  saving.value = true
  try {
    const created = await api.createTvShow({
      title,
      stage: form.stage,
      reason: form.reason.trim(),
    })
    if (created.code === 0 && created.data) {
      showToast('已添加', 'success')
      form.title = ''
      form.reason = ''
      form.stage = 'beginner'
      showForm.value = false
      await load()
      goShow(created.data.id)
    } else {
      showToast(created.message || '添加失败', 'error')
    }
  } finally {
    saving.value = false
  }
}

async function load() {
  loading.value = true
  try {
    const [h, s] = await Promise.all([api.getTvHub(), api.listTvShows()])
    if (h.code === 0 && h.data) hub.value = h.data
    else if (h.code !== 0) showToast(h.message || '加载失败', 'error')
    if (s.code === 0 && s.data) shows.value = s.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-tv {
  @include page-padding;
  padding-bottom: 40px;
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  .hero-title { display: block; font-size: 22px; font-weight: 700; color: $text-primary; }
  .hero-desc { display: block; font-size: 12px; color: $text-muted; margin-top: 4px; }
  .hero-btn {
    background: $primary-color;
    color: #fff;
    font-size: 13px;
    padding: 8px 14px;
    border-radius: $radius-md;
  }
}

.form-card {
  @include card;
  padding: 14px;
  margin-bottom: 14px;
  border-radius: $radius-lg;
  .form-label {
    display: block;
    font-size: 12px;
    color: $text-muted;
    margin: 10px 0 6px;
    &:first-child { margin-top: 0; }
  }
  .stage-row { display: flex; gap: 8px; flex-wrap: wrap; }
  .stage {
    font-size: 12px;
    padding: 5px 10px;
    border-radius: 999px;
    background: $page-bg;
    color: $text-secondary;
    border: 1px solid $border-color;
    &.on {
      background: $primary-light;
      color: $primary-color;
      border-color: transparent;
      font-weight: 600;
    }
  }
  .save-btn { margin-top: 14px; }
}

.stats-row {
  @include card;
  display: flex;
  align-items: center;
  padding: 12px 8px;
  margin-bottom: 10px;
  border-radius: $radius-lg;
  .stat { flex: 1; text-align: center;
    .num { display: block; font-size: 20px; font-weight: 700; color: $text-primary; &.warn { color: $primary-color; } }
    .label { display: block; font-size: 11px; color: $text-muted; margin-top: 2px; }
  }
  .stat-divider { width: 1px; height: 28px; background: $border-color; }
}

.quick-row {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
  .quick { font-size: 13px; color: $primary-color; }
}

.block { margin-bottom: 16px; }
.block-title {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: $text-muted;
  margin-bottom: 8px;
}

.scene-row, .show-card {
  @include card;
  display: flex;
  align-items: center;
  padding: 12px 14px;
  margin-bottom: 8px;
  border-radius: $radius-lg;
}
.scene-title, .show-title {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: $text-primary;
}
.scene-meta, .show-meta {
  display: block;
  font-size: 12px;
  color: $text-muted;
  margin-top: 4px;
}
.show-reason {
  display: block;
  font-size: 12px;
  color: $text-secondary;
  margin-top: 4px;
}
.scene-main, .show-main { flex: 1; min-width: 0; }
.arrow { color: $text-muted; font-size: 18px; }

.empty {
  text-align: center;
  padding: 28px 16px;
  .empty-title { display: block; font-size: 15px; font-weight: 600; color: $text-primary; }
  .empty-desc { display: block; font-size: 12px; color: $text-muted; margin-top: 6px; line-height: 1.5; }
  .empty-btn {
    display: inline-block;
    margin-top: 14px;
    background: $primary-color;
    color: #fff;
    font-size: 13px;
    padding: 8px 16px;
    border-radius: $radius-md;
  }
}
</style>
