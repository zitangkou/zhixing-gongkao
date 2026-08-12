<template>
  <view class="page-tv-ep">
    <view class="head">
      <text class="title">{{ epLabel || '场景列表' }}</text>
      <view class="actions">
        <text class="act" @tap="showForm = !showForm">{{ showForm ? '收起' : '+ 加场景' }}</text>
        <text class="act danger" @tap="onDeleteEpisode">删除集</text>
      </view>
    </view>

    <view v-if="showForm" class="form-card">
      <text class="form-label">场景标题 *</text>
      <nut-input v-model="form.title" placeholder="如 coffee shop intro" />
      <text class="form-label">时间段（可选）</text>
      <nut-input v-model="form.timeRange" placeholder="如 02:10-05:00" />
      <text class="form-label">场景一句话（可选）</text>
      <nut-input v-model="form.sceneSummary" placeholder="谁在什么场合说了什么" />
      <text class="form-label">目标句型数</text>
      <nut-input v-model="form.targetCount" type="number" placeholder="3" />
      <nut-button type="primary" size="small" block :loading="saving" class="save-btn" @click="onAddScene">
        创建并开始精学
      </nut-button>
    </view>

    <view v-if="loading" class="empty">加载中...</view>
    <view v-else-if="!scenes.length" class="empty">
      <text class="empty-title">还没有精学场景</text>
      <text class="empty-desc">选 3–5 分钟片段，录入对白后开始精学</text>
      <view class="empty-btn" @tap="showForm = true">添加场景</view>
    </view>

    <view v-else class="list">
      <view
        v-for="sc in scenes"
        :key="sc.id"
        class="sc-card"
        @tap="goStudy(sc.id)"
      >
        <view class="sc-main">
          <text class="sc-title">{{ sc.title }}</text>
          <text v-if="sc.sceneSummary" class="sc-summary">{{ sc.sceneSummary }}</text>
          <text class="sc-meta">
            {{ sc.timeRange ? `${sc.timeRange} · ` : '' }}{{ sc.lineCount }} 句 · {{ sc.expressionCount }} 卡{{ sc.todaySession ? ` · 今日 ${sc.todaySession.completedCount}/5` : '' }}
          </text>
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
import type { TvScene } from '@/types'

definePageConfig({ navigationBarTitleText: '场景列表' })

const router = useRouter()
const episodeId = router.params?.id || ''
const showId = router.params?.showId || ''
const epLabel = ref('')
const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const scenes = ref<TvScene[]>([])
const form = reactive({
  title: '',
  timeRange: '',
  sceneSummary: '',
  targetCount: '3',
})

function goStudy(id: string) {
  Taro.navigateTo({ url: `/pages/english/tv/scene-study?id=${id}` })
}

async function onAddScene() {
  const title = form.title.trim()
  if (!title) {
    showToast('请填写场景标题', 'none')
    return
  }
  saving.value = true
  try {
    const res = await api.createTvScene({
      episodeId,
      title,
      timeRange: form.timeRange.trim(),
      sceneSummary: form.sceneSummary.trim(),
      targetCount: Math.max(1, parseInt(form.targetCount || '3', 10) || 3),
      lines: [],
    })
    if (res.code === 0 && res.data) {
      showToast('已创建', 'success')
      showForm.value = false
      form.title = ''
      form.timeRange = ''
      form.sceneSummary = ''
      goStudy(res.data.id)
    } else {
      showToast(res.message || '创建失败', 'error')
    }
  } finally {
    saving.value = false
  }
}

async function onDeleteEpisode() {
  const ok = await showConfirm('删除剧集', '将删除本集场景与表达卡，确定？')
  if (!ok) return
  const res = await api.deleteTvEpisode(episodeId)
  if (res.code === 0) {
    showToast('已删除', 'success')
    Taro.navigateBack()
  } else {
    showToast(res.message || '删除失败', 'error')
  }
}

async function load() {
  if (!episodeId) {
    showToast('缺少剧集 id', 'error')
    return
  }
  loading.value = true
  try {
    if (showId) {
      const epRes = await api.listTvEpisodes(showId)
      if (epRes.code === 0 && epRes.data) {
        const ep = epRes.data.find((e) => e.id === episodeId)
        if (ep) {
          epLabel.value = ep.label
          Taro.setNavigationBarTitle({ title: ep.label })
        }
      }
    }
    const res = await api.listTvScenes(episodeId)
    if (res.code === 0 && res.data) scenes.value = res.data
    else if (res.code !== 0) showToast(res.message || '加载失败', 'error')
  } finally {
    loading.value = false
  }
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-tv-ep {
  @include page-padding;
  padding-bottom: 40px;
}

.head {
  margin-bottom: 14px;
  .title { display: block; font-size: 18px; font-weight: 700; color: $text-primary; }
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
    &:first-child { margin-top: 0; }
  }
  .save-btn { margin-top: 14px; }
}

.sc-card {
  @include card;
  display: flex;
  align-items: center;
  padding: 12px 14px;
  margin-bottom: 8px;
  border-radius: $radius-lg;
}
.sc-main { flex: 1; min-width: 0; }
.sc-title { display: block; font-size: 15px; font-weight: 600; color: $text-primary; }
.sc-summary {
  display: block;
  font-size: 12px;
  color: $text-secondary;
  margin-top: 4px;
}
.sc-meta { display: block; font-size: 12px; color: $text-muted; margin-top: 4px; }
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
