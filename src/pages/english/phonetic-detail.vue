<template>
  <view class="page-ph-detail" v-if="ph">
    <view class="symbol-card">
      <text class="big-symbol" @tap="playPhonetic">{{ ph.symbol }}</text>
      <text class="tap-hint">点击音标听发音</text>
      <view class="cat-row">
        <text class="chip" :class="catClass(ph.category)">{{ catLabel(ph.category) }}</text>
        <text v-if="isMastered" class="chip chip-green">已掌握 ✓</text>
      </view>
    </view>

    <view v-if="ph.description" class="section">
      <text class="block-title">发音说明</text>
      <text class="text-body">{{ ph.description }}</text>
    </view>

    <view v-if="ph.mouthShape" class="section">
      <text class="block-title">口型舌位</text>
      <text class="text-body">{{ ph.mouthShape }}</text>
    </view>

    <view v-if="ph.tips" class="section">
      <text class="block-title">发音技巧</text>
      <text class="text-body">{{ ph.tips }}</text>
    </view>

    <view v-if="ph.exampleWords.length" class="section">
      <text class="block-title">示例单词 ({{ ph.exampleWords.length }})</text>
      <text class="word-hint">点击单词听发音</text>
      <view v-for="(w, i) in ph.exampleWords" :key="i" class="word-row">
        <text class="w-en" @tap="play(w.word)">{{ w.word }}</text>
        <text class="w-zh">{{ w.meaning }}</text>
      </view>
    </view>

    <view v-if="ph.commonSpellings.length" class="section">
      <text class="block-title">常见拼写</text>
      <view class="spelling-row">
        <text v-for="s in ph.commonSpellings" :key="s" class="spell-tag">{{ s }}</text>
      </view>
    </view>

    <view class="action-bar">
      <nut-button plain type="primary" @click="markProgress('learning')">标记学习中</nut-button>
      <nut-button type="primary" @click="markProgress('mastered')">已掌握</nut-button>
    </view>
  </view>
  <view v-else-if="loading" class="state-box">
    <text class="state-title">加载中…</text>
  </view>
  <view v-else class="state-box">
    <text class="state-title">{{ error || '音标不存在' }}</text>
    <view class="state-btn" @tap="load">点击重试</view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from '@tarojs/taro'
import { Button as NutButton } from '@nutui/nutui-taro'
import { api } from '@/api'
import { phoneticPronounceText } from '@/utils/phonetic'
import { playPronounce } from '@/utils/pronounce'
import { showToast } from '@/utils/platform'
import type { PhoneticLesson, PhoneticProgressMap } from '@/types'

definePageConfig({ navigationBarTitleText: '音标详情' })

const router = useRouter()
const lessonId = ref(router.params?.id || '')
const ph = ref<PhoneticLesson | null>(null)
const progress = ref<PhoneticProgressMap>({})
const loading = ref(false)
const error = ref('')

const isMastered = computed(() => progress.value[lessonId.value]?.status === 'mastered')

function catLabel(c: string) {
  return { unit_vowel: '单元音', diphthong: '双元音', consonant: '辅音' }[c] || c
}

function catClass(c: string) {
  return { unit_vowel: 'chip-red', diphthong: 'chip-amber', consonant: 'chip-blue' }[c] || 'chip-soft'
}

function play(word: string) {
  playPronounce(word)
}

/** 播放音标本身的近似发音 */
function playPhonetic() {
  if (!ph.value) return
  play(phoneticPronounceText(ph.value.symbol))
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [r1, r2] = await Promise.all([
      api.listPhonetics(),
      api.getPhoneticProgress(),
    ])
    if (r1.code === 0 && r1.data) {
      ph.value = r1.data.find((p) => p.id === lessonId.value) || null
      if (!ph.value) error.value = '未找到该音标'
    } else {
      error.value = r1.message || '加载失败'
    }
    if (r2.code === 0 && r2.data) progress.value = r2.data
  } catch {
    error.value = '网络异常，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function markProgress(status: 'learning' | 'mastered') {
  const res = await api.updatePhoneticProgress(lessonId.value, status)
  if (res.code === 0) {
    showToast(status === 'mastered' ? '已标记掌握' : '已标记学习中', 'success')
    progress.value = { ...progress.value, [lessonId.value]: { status, practicedCount: res.data.practicedCount, lastPracticeAt: new Date().toISOString() } }
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-ph-detail {
  @include page-padding;
  padding-bottom: 100px;
}

.state-box { @include page-state-box; }

.symbol-card {
  background: linear-gradient(135deg, $primary-light, $card-bg);
  border-radius: $radius-lg;
  padding: 28px 16px;
  text-align: center;
  margin-bottom: 12px;
  .big-symbol {
    display: block;
    font-size: 48px;
    font-weight: 700;
    color: $primary-color;
    margin-bottom: 6px;
    &:active { opacity: 0.6; }
  }
  .tap-hint {
    display: block;
    font-size: 12px;
    color: $text-muted;
    margin-bottom: 12px;
  }
  .cat-row { display: flex; justify-content: center; gap: 6px; .chip { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; } .chip-red { color: $primary-color; background: $primary-light; } .chip-amber { color: $accent-amber; background: rgba($accent-amber, 0.12); } .chip-blue { color: $accent-blue; background: rgba($accent-blue, 0.1); } .chip-green { color: $on-primary; background: $success; } }
}

.section {
  @include card;
  padding: 14px 16px;
  border-radius: $radius-lg;
  margin-bottom: 12px;
  .block-title { display: block; font-size: 14px; font-weight: 600; margin-bottom: 8px; }
  .text-body { display: block; font-size: 14px; line-height: 1.7; color: $text-primary; }
}

.word-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid $border-color;
  &:last-child { border-bottom: none; }
  .w-en {
    font-size: 15px;
    font-weight: 600;
    color: $accent-blue;
    &:active { opacity: 0.6; }
  }
  .w-zh { flex: 1; font-size: 13px; color: $text-secondary; text-align: right; }
}

.word-hint {
  display: block;
  font-size: 12px;
  color: $text-muted;
  margin: -4px 0 8px;
}

.spelling-row {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  .spell-tag {
    font-size: 13px;
    padding: 4px 12px;
    border-radius: 6px;
    background: $page-bg;
    color: $text-secondary;
    font-weight: 600;
  }
}

.action-bar {
  display: flex;
  gap: 12px;
  position: fixed;
  left: 16px;
  right: 16px;
  bottom: 16px;
  .nut-button { flex: 1; }
}
</style>
