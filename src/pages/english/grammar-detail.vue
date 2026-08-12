<template>
  <view class="page-grammar-detail" v-if="lesson">
    <view class="head">
      <text class="title">{{ lesson.title }}</text>
      <view class="meta">
        <text class="chip chip-soft">{{ lesson.category }}</text>
        <text class="chip chip-blue">{{ lesson.level }}</text>
      </view>
    </view>

    <view v-if="lesson.explanation" class="section">
      <text class="block-title">讲解</text>
      <text class="explanation">{{ lesson.explanation }}</text>
    </view>

    <view v-if="lesson.examples.length" class="section">
      <text class="block-title">例句</text>
      <view v-for="(e, i) in lesson.examples" :key="i" class="example">
        <view class="e-head">
          <text class="e-en" @tap="play(e.en)">{{ e.en }}</text>
          <text class="e-play" @tap="play(e.en)">🔊</text>
        </view>
        <text class="e-zh">{{ e.zh }}</text>
      </view>
    </view>

    <view v-if="lesson.commonMistakes.length" class="section">
      <text class="block-title">常见错误</text>
      <view v-for="(m, i) in lesson.commonMistakes" :key="i" class="mistake">
        <text class="m-wrong">✗ {{ m.wrong }}</text>
        <text class="m-correct">✓ {{ m.correct }}</text>
        <text v-if="m.note" class="m-note">{{ m.note }}</text>
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
    <text class="state-title">{{ error || '内容不存在' }}</text>
    <view class="state-btn" @tap="load">点击重试</view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from '@tarojs/taro'
import { Button as NutButton } from '@nutui/nutui-taro'
import { api } from '@/api'
import { playPronounce } from '@/utils/pronounce'
import { showToast } from '@/utils/platform'
import type { GrammarLesson } from '@/types'

definePageConfig({ navigationBarTitleText: '语法详情' })

const router = useRouter()
const lessonId = ref(router.params?.id || '')
const lesson = ref<GrammarLesson | null>(null)
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.getGrammarLesson(lessonId.value)
    if (res.code === 0 && res.data) lesson.value = res.data
    else {
      lesson.value = null
      error.value = res.message || '加载失败'
    }
  } catch {
    lesson.value = null
    error.value = '网络异常，请稍后重试'
  } finally {
    loading.value = false
  }
}

function play(text: string) {
  playPronounce(text)
}

async function markProgress(status: 'learning' | 'mastered') {
  const res = await api.updateGrammarProgress(lessonId.value, status)
  if (res.code === 0) {
    showToast(status === 'mastered' ? '已标记掌握' : '已标记学习中', 'success')
  } else {
    showToast(res.message || '操作失败', 'error')
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-grammar-detail {
  @include page-padding;
  padding-bottom: 100px;
}

.state-box { @include page-state-box; }

.head {
  @include card;
  padding: 14px 16px;
  border-radius: $radius-lg;
  margin-bottom: 12px;
  .title { display: block; font-size: 18px; font-weight: 700; margin-bottom: 8px; }
  .meta { display: flex; gap: 6px; .chip { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; &.chip-blue { color: $accent-blue; background: rgba($accent-blue, 0.1); } &.chip-soft { color: $text-secondary; background: $chip-bg; } } }
}

.section {
  @include card;
  padding: 14px 16px;
  border-radius: $radius-lg;
  margin-bottom: 12px;
  .block-title { display: block; font-size: 14px; font-weight: 600; margin-bottom: 10px; }
}

.explanation {
  display: block;
  font-size: 14px;
  line-height: 1.7;
  color: $text-primary;
}

.example {
  padding: 8px 0;
  border-bottom: 1px solid $border-color;
  &:last-child { border-bottom: none; }
  .e-head { display: flex; align-items: center; gap: 8px; .e-en { flex: 1; font-size: 14px; color: $accent-blue; } .e-play { @include hit-target(44px); font-size: 16px; } }
  .e-zh { display: block; font-size: 12px; color: $text-secondary; margin-top: 4px; }
}

.mistake {
  padding: 10px;
  background: $page-bg;
  border-radius: 6px;
  margin-bottom: 8px;
  .m-wrong { display: block; font-size: 13px; color: $primary-color; margin-bottom: 4px; }
  .m-correct { display: block; font-size: 13px; color: $accent-green; margin-bottom: 4px; }
  .m-note { display: block; font-size: 12px; color: $text-muted; line-height: 1.5; }
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
