<template>
  <view class="page-shadow">
    <view class="tip-card">
      <text class="tip-title">我的跟读本</text>
      <text class="tip-desc">在英文文章里点句子「＋ 跟读」即可收藏，在这里听原音、录音跟读。</text>
    </view>

    <view v-if="loading" class="empty">加载中...</view>
    <view v-else-if="!list.length" class="empty">
      <text class="empty-title">还没有跟读句子</text>
      <text class="empty-desc">去读一篇英文文章，点句子旁的「＋ 跟读」</text>
      <nut-button type="primary" size="small" class="go-btn" @click="goArticles">去读文章</nut-button>
    </view>

    <view v-else class="list">
      <view v-for="item in list" :key="item.id" class="card">
        <text class="sentence" @tap="play(item.sentence)">{{ item.sentence }}</text>
        <text v-if="item.articleTitle" class="source">来自 · {{ item.articleTitle }}</text>
        <view class="meta">
          <text>练过 {{ item.practiceCount }} 次</text>
          <text v-if="item.lastPracticeAt" class="muted">最近 {{ formatDate(item.lastPracticeAt) }}</text>
        </view>
        <view class="actions">
          <text class="act" @tap="play(item.sentence)">🔊 听原句</text>
          <text class="act" @tap="onRecord(item)">{{ recording && pendingId === item.id ? '⏹ 停止' : '🎙 录音' }}</text>
          <text v-if="item.recordingUrl" class="act" @tap="playRecording(item)">▶ 我的录音</text>
          <text class="act danger" @tap="onDelete(item)">删除</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { Button as NutButton } from '@nutui/nutui-taro'
import { api } from '@/api'
import { resolveMediaUrl } from '@/utils/media'
import { playPronounce } from '@/utils/pronounce'
import { showConfirm, showToast } from '@/utils/platform'
import type { UserSpeakingSentence } from '@/types'

definePageConfig({ navigationBarTitleText: '跟读本' })

const loading = ref(false)
const list = ref<UserSpeakingSentence[]>([])
const pendingId = ref('')
const recording = ref(false)
const canRecord = ref(false)
let audioCtx: ReturnType<typeof Taro.createInnerAudioContext> | null = null
let recorderManager: ReturnType<typeof Taro.getRecorderManager> | null = null

function ensureRecorder() {
  if (recorderManager) return recorderManager
  try {
    recorderManager = Taro.getRecorderManager()
    recorderManager.onStop(async (res) => {
      recording.value = false
      const id = pendingId.value
      if (!id) return
      const up = await api.uploadSpeakingRecording(res.tempFilePath)
      if (up.code === 0 && up.data?.url) {
        const upd = await api.updateShadowing(id, { recordingUrl: up.data.url, practiced: true })
        if (upd.code === 0 && upd.data) {
          const idx = list.value.findIndex((x) => x.id === id)
          if (idx >= 0) list.value[idx] = upd.data
          showToast('录音已保存', 'success')
        }
      } else {
        showToast(up.message || '录音上传失败', 'error')
      }
    })
    canRecord.value = true
  } catch {
    canRecord.value = false
    recorderManager = null
  }
  return recorderManager
}

function formatDate(iso: string) {
  return iso.slice(0, 10)
}

function play(text: string) {
  playPronounce(text)
}

function playRecording(item: UserSpeakingSentence) {
  if (!item.recordingUrl) return
  if (audioCtx) audioCtx.destroy()
  audioCtx = Taro.createInnerAudioContext()
  audioCtx.src = resolveMediaUrl(item.recordingUrl)
  audioCtx.play()
}

function onRecord(item: UserSpeakingSentence) {
  const rm = ensureRecorder()
  if (!rm) {
    showToast('当前环境不支持录音（可用浏览器原生麦克风权限时再试）', 'none')
    return
  }
  if (recording.value && pendingId.value === item.id) {
    try { rm.stop() } catch { /* ignore */ }
    return
  }
  pendingId.value = item.id
  recording.value = true
  showToast('录音中，再点一次结束', 'none')
  try {
    rm.start({ format: 'mp3', duration: 60000 })
  } catch {
    recording.value = false
    showToast('无法开始录音', 'error')
  }
}

async function onDelete(item: UserSpeakingSentence) {
  const ok = await showConfirm('删除句子', '确定从跟读本移除？')
  if (!ok) return
  const res = await api.deleteShadowing(item.id)
  if (res.code === 0) {
    list.value = list.value.filter((x) => x.id !== item.id)
    showToast('已删除', 'success')
  }
}

function goArticles() {
  Taro.navigateTo({ url: '/pages/english/article-list' })
}

async function load() {
  loading.value = true
  try {
    const res = await api.listShadowing()
    if (res.code === 0 && res.data) list.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-shadow {
  @include page-padding;
  padding-bottom: 40px;
}

.tip-card {
  @include card;
  padding: 14px 16px;
  border-radius: $radius-lg;
  margin-bottom: 12px;
  background: linear-gradient(135deg, $primary-faint, $card-bg);
  .tip-title { display: block; font-size: 15px; font-weight: 700; margin-bottom: 4px; }
  .tip-desc { display: block; font-size: 12px; color: $text-secondary; line-height: 1.5; }
}

.empty {
  text-align: center;
  padding: 48px 16px;
  color: $text-muted;
  .empty-title { display: block; font-size: 15px; font-weight: 600; color: $text-secondary; margin-bottom: 6px; }
  .empty-desc { display: block; font-size: 12px; margin-bottom: 16px; }
  .go-btn { min-width: 120px; }
}

.card {
  @include card;
  padding: 14px 16px;
  border-radius: $radius-lg;
  margin-bottom: 10px;
  .sentence { display: block; font-size: 15px; line-height: 1.7; font-weight: 600; color: $text-primary; }
  .source { display: block; font-size: 11px; color: $text-muted; margin-top: 6px; }
  .meta {
    display: flex;
    gap: 10px;
    margin-top: 8px;
    font-size: 11px;
    color: $text-secondary;
    .muted { color: $text-muted; }
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 10px;
    .act {
      @include list-act;
      &.danger { color: $text-muted; }
    }
  }
}
</style>
