<template>
  <view class="page-tv-show">
    <view class="head">
      <text class="title">{{ showTitle || '剧集列表' }}</text>
      <view class="actions">
        <text class="act" @tap="showForm = !showForm">{{ showForm ? '收起' : '+ 加集' }}</text>
        <text class="act danger" @tap="onDeleteShow">删除剧</text>
      </view>
    </view>

    <view v-if="showForm" class="form-card">
      <view class="row-2">
        <view class="half">
          <text class="form-label">季</text>
          <nut-input v-model="form.season" type="number" placeholder="1" />
        </view>
        <view class="half">
          <text class="form-label">集</text>
          <nut-input v-model="form.episode" type="number" placeholder="1" />
        </view>
      </view>
      <text class="form-label">标题（可选）</text>
      <nut-input v-model="form.title" placeholder="如 The One Where…" />
      <text class="form-label">剧情摘要（可选）</text>
      <nut-input v-model="form.summary" placeholder="一句话剧情" />
      <nut-button type="primary" size="small" block :loading="saving" class="save-btn" @click="onAddEpisode">
        保存剧集
      </nut-button>
    </view>

    <view v-if="loading" class="empty">加载中...</view>
    <view v-else-if="!episodes.length" class="empty">
      <text class="empty-title">还没有剧集</text>
      <text class="empty-desc">添加一集后，再拆几个 3–5 分钟精学场景</text>
      <view class="empty-btn" @tap="showForm = true">添加第一集</view>
    </view>

    <view v-else class="list">
      <view
        v-for="ep in episodes"
        :key="ep.id"
        class="ep-card"
        @tap="goEpisode(ep.id)"
      >
        <view class="ep-main">
          <view class="ep-top">
            <text class="ep-label">{{ ep.label }}</text>
            <text class="ep-status" :class="ep.status">{{ statusLabel(ep.status) }}</text>
          </view>
          <text v-if="ep.summary" class="ep-summary">{{ ep.summary }}</text>
          <text class="ep-meta">{{ ep.sceneCount }} 场景 · {{ ep.expressionCount }} 表达卡</text>
        </view>
        <text class="arrow">›</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import Taro, { useDidShow, useRouter } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput } from '@nutui/nutui-taro'
import { api } from '@/api'
import { showConfirm, showToast } from '@/utils/platform'
import type { TvEpisode } from '@/types'

definePageConfig({ navigationBarTitleText: '剧集列表' })

const router = useRouter()
const showId = router.params?.id || ''
const showTitle = ref('')
const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const episodes = ref<TvEpisode[]>([])
const form = reactive({
  season: '1',
  episode: '1',
  title: '',
  summary: '',
})

function statusLabel(s: string) {
  return { todo: '未学', learning: '学习中', done: '已完成' }[s] || s
}

function goEpisode(id: string) {
  Taro.navigateTo({ url: `/pages/english/tv/episode?id=${id}&showId=${showId}` })
}

async function onAddEpisode() {
  const season = Math.max(1, parseInt(form.season || '1', 10) || 1)
  const episode = Math.max(1, parseInt(form.episode || '1', 10) || 1)
  saving.value = true
  try {
    const res = await api.createTvEpisode({
      showId,
      season,
      episode,
      title: form.title.trim(),
      summary: form.summary.trim(),
    })
    if (res.code === 0 && res.data) {
      showToast('已添加', 'success')
      showForm.value = false
      form.title = ''
      form.summary = ''
      form.episode = String(episode + 1)
      await load()
      goEpisode(res.data.id)
    } else {
      showToast(res.message || '添加失败', 'error')
    }
  } finally {
    saving.value = false
  }
}

async function onDeleteShow() {
  const ok = await showConfirm('删除剧目', '将删除所有集、场景与表达卡，确定？')
  if (!ok) return
  const res = await api.deleteTvShow(showId)
  if (res.code === 0) {
    showToast('已删除', 'success')
    Taro.navigateBack()
  } else {
    showToast(res.message || '删除失败', 'error')
  }
}

async function load() {
  if (!showId) {
    showToast('缺少剧目 id', 'error')
    return
  }
  loading.value = true
  try {
    const [showsRes, epRes] = await Promise.all([
      api.listTvShows(),
      api.listTvEpisodes(showId),
    ])
    if (showsRes.code === 0 && showsRes.data) {
      showTitle.value = showsRes.data.find((s) => s.id === showId)?.title || ''
      if (showTitle.value) Taro.setNavigationBarTitle({ title: showTitle.value })
    }
    if (epRes.code === 0 && epRes.data) {
      episodes.value = epRes.data
      const last = epRes.data[epRes.data.length - 1]
      if (last) {
        form.season = String(last.season)
        form.episode = String(last.episode + 1)
      }
    } else if (epRes.code !== 0) {
      showToast(epRes.message || '加载失败', 'error')
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

.page-tv-show {
  @include page-padding;
  padding-bottom: 40px;
}

.head {
  margin-bottom: 14px;
  .title { display: block; font-size: 20px; font-weight: 700; color: $text-primary; }
  .actions { display: flex; gap: 4px; margin-top: 4px; flex-wrap: wrap; }
  .act {
    @include list-act;
    &.danger { color: $text-muted; }
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
  }
  .row-2 { display: flex; gap: 10px; }
  .half { flex: 1; .form-label { margin-top: 0; } }
  .save-btn { margin-top: 14px; }
}

.ep-card {
  @include card;
  display: flex;
  align-items: center;
  padding: 12px 14px;
  margin-bottom: 8px;
  border-radius: $radius-lg;
}
.ep-main { flex: 1; min-width: 0; }
.ep-top { display: flex; align-items: center; gap: 8px; }
.ep-label { font-size: 15px; font-weight: 600; color: $text-primary; }
.ep-status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: $page-bg;
  color: $text-muted;
  &.learning { background: $primary-light; color: $primary-color; }
  &.done { background: rgba(61, 186, 128, 0.18); color: var(--zk-success); }
}
.ep-summary {
  display: block;
  font-size: 12px;
  color: $text-secondary;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ep-meta { display: block; font-size: 12px; color: $text-muted; margin-top: 4px; }
.arrow { color: $text-muted; font-size: 18px; }

.empty {
  text-align: center;
  padding: 36px 16px;
  .empty-title { display: block; font-size: 15px; font-weight: 600; color: $text-primary; }
  .empty-desc { display: block; font-size: 12px; color: $text-muted; margin-top: 6px; }
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
