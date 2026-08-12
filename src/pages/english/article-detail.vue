<template>
  <view class="page-en-detail" v-if="article">
    <view class="article-head">
      <text class="title">{{ article.title }}</text>
      <view class="meta-row">
        <text v-if="article.source" class="chip chip-soft">{{ article.source }}</text>
        <text class="chip" :class="levelClass(article.level)">{{ article.level }}</text>
      </view>
      <text class="hint">点单词：发音 / 加生词 · 点句末按钮：发音 / 加跟读</text>
    </view>

    <view v-if="article.vocabHighlights.length" class="vocab-section">
      <text class="block-title">本文生词 ({{ article.vocabHighlights.length }})</text>
      <view v-for="v in article.vocabHighlights" :key="v.word" class="vocab-row">
        <view class="vocab-main">
          <text class="v-word" @tap="playText(v.word)">{{ v.word }}</text>
          <text v-if="v.pos" class="v-pos">{{ v.pos }}</text>
          <text class="v-meaning">{{ v.meaning }}</text>
        </view>
        <view class="v-actions">
          <text class="v-add" @tap="onAddVocab(v.word, v.meaning, v.pos, v.sentence)">+ 生词本</text>
        </view>
      </view>
    </view>

    <view class="content-section">
      <text class="block-title">正文</text>
      <view
        v-for="(sent, si) in sentences"
        :key="si"
        class="sentence-block"
        :class="{ active: activeSentence === si }"
      >
        <view class="sentence-text">
          <text
            v-for="(tok, ti) in tokenize(sent)"
            :key="`${si}-${ti}`"
            class="tok"
            :class="{ word: tok.isWord }"
            @tap.stop="tok.isWord ? onWordTap(tok.text, sent) : undefined"
          >{{ tok.text }}</text>
        </view>
        <view class="sentence-actions">
          <text class="sa" @tap="playText(sent)">🔊 读</text>
          <text class="sa" @tap="onAddShadow(sent)">＋ 跟读</text>
        </view>
      </view>
    </view>

    <!-- 点词操作条 -->
    <view v-if="wordSheet" class="action-sheet" @tap="wordSheet = null">
      <view class="sheet-card" @tap.stop>
        <text class="sheet-word">{{ wordSheet.word }}</text>
        <text class="sheet-ctx">{{ wordSheet.sentence }}</text>
        <view class="sheet-btns">
          <nut-button type="primary" @click="playText(wordSheet.word)">发音</nut-button>
          <nut-button plain type="primary" @click="onAddVocab(wordSheet.word, '', '', wordSheet.sentence); wordSheet = null">
            加入生词本
          </nut-button>
        </view>
        <text class="sheet-cancel" @tap="wordSheet = null">取消</text>
      </view>
    </view>
  </view>
  <view v-else-if="loading" class="state-box">
    <text class="state-title">加载中…</text>
  </view>
  <view v-else class="state-box">
    <text class="state-title">{{ error || '文章不存在' }}</text>
    <text class="state-desc">可以返回列表再试一次</text>
    <view class="state-btn" @tap="load">点击重试</view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from '@tarojs/taro'
import { Button as NutButton } from '@nutui/nutui-taro'
import { api } from '@/api'
import { normalizeWord, splitSentences, tokenizeSentence } from '@/utils/englishText'
import { playPronounce } from '@/utils/pronounce'
import { showToast } from '@/utils/platform'
import type { EnglishArticle } from '@/types'

definePageConfig({ navigationBarTitleText: '文章详情' })

const router = useRouter()
const articleId = ref(router.params?.id || '')
const article = ref<EnglishArticle | null>(null)
const loading = ref(false)
const error = ref('')
const activeSentence = ref(-1)
const wordSheet = ref<{ word: string; sentence: string } | null>(null)

const sentences = computed(() => splitSentences(article.value?.content || ''))

function tokenize(sent: string) {
  return tokenizeSentence(sent)
}

function levelClass(l: string) {
  return { A2: 'chip-green', B1: 'chip-blue', B2: 'chip-amber', C1: 'chip-red' }[l] || 'chip-soft'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.getEnglishArticle(articleId.value)
    if (res.code === 0 && res.data) article.value = res.data
    else {
      article.value = null
      error.value = res.message || '加载失败'
    }
  } catch {
    article.value = null
    error.value = '网络异常，请稍后重试'
  } finally {
    loading.value = false
  }
}

function playText(text: string) {
  playPronounce(text)
}

function onWordTap(raw: string, sentence: string) {
  const word = normalizeWord(raw)
  if (!word) return
  wordSheet.value = { word, sentence }
}

async function onAddVocab(word: string, meaning = '', pos = '', sentence = '') {
  const w = normalizeWord(word)
  if (!w) return
  const res = await api.addVocab({
    word: w,
    meaning,
    pos,
    exampleSentence: sentence,
    articleId: articleId.value,
  })
  if (res.code === 0) {
    showToast('已加入生词本', 'success')
    api.addEnglishLog({ logType: 'vocab', refId: w, wordsLearned: 1 }).catch(() => {})
  } else {
    showToast(res.message || '添加失败', 'error')
  }
}

async function onAddShadow(sentence: string) {
  const s = sentence.trim()
  if (!s) return
  activeSentence.value = sentences.value.indexOf(sentence)
  const res = await api.addShadowing({
    sentence: s,
    articleId: articleId.value,
    articleTitle: article.value?.title || '',
  })
  if (res.code === 0) {
    showToast('已加入跟读本', 'success')
  } else {
    showToast(res.message || '添加失败', 'error')
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-en-detail {
  @include page-padding;
  padding-bottom: 40px;
}

.state-box { @include page-state-box; }

.article-head {
  margin-bottom: 14px;
  .title { display: block; font-size: 20px; font-weight: 700; line-height: 1.4; margin-bottom: 8px; }
  .meta-row { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
  .chip { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; }
  .chip-soft { color: $text-secondary; background: $page-bg; }
  .chip-green { color: $accent-green; background: rgba($accent-green, 0.1); }
  .chip-blue { color: $accent-blue; background: rgba($accent-blue, 0.1); }
  .chip-amber { color: $accent-amber; background: rgba($accent-amber, 0.12); }
  .chip-red { color: $primary-color; background: $primary-light; }
  .hint { display: block; font-size: 12px; color: $text-muted; line-height: 1.5; }
}

.vocab-section, .content-section {
  @include card;
  padding: 14px 16px;
  border-radius: $radius-lg;
  margin-bottom: 12px;
  .block-title { display: block; font-size: 14px; font-weight: 600; margin-bottom: 10px; }
}

.vocab-row {
  padding: 8px 0;
  border-bottom: 1px solid $border-color;
  &:last-child { border-bottom: none; }
  .vocab-main { display: flex; align-items: baseline; gap: 6px; flex-wrap: wrap; }
  .v-word { font-size: 15px; font-weight: 700; color: $primary-color; }
  .v-pos { font-size: 11px; color: $text-muted; }
  .v-meaning { font-size: 13px; color: $text-secondary; }
  .v-actions { margin-top: 4px; }
  .v-add { @include list-act; color: $accent-blue; }
}

.sentence-block {
  padding: 10px 0;
  border-bottom: 1px solid $border-color;
  &:last-child { border-bottom: none; }
  &.active { background: $primary-faint; margin: 0 -8px; padding: 10px 8px; border-radius: 8px; }
}

.sentence-text {
  font-size: 16px;
  line-height: 1.85;
  color: $text-primary;
  .tok.word {
    color: $text-primary;
    border-bottom: 1px dashed $primary-soft;
    &:active { color: $primary-color; background: $primary-light; }
  }
}

.sentence-actions {
  display: flex;
  gap: 14px;
  margin-top: 6px;
  .sa {
    @include list-act;
    color: $accent-blue;
    &:active { opacity: 0.6; }
  }
}

.action-sheet {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 2000;
  display: flex;
  align-items: flex-end;
  .sheet-card {
    width: 100%;
    background: $card-bg;
    border-radius: 16px 16px 0 0;
    padding: 20px 16px calc(20px + env(safe-area-inset-bottom));
    .sheet-word { display: block; font-size: 22px; font-weight: 700; color: $primary-color; margin-bottom: 8px; }
    .sheet-ctx { display: block; font-size: 13px; color: $text-secondary; line-height: 1.5; margin-bottom: 16px; }
    .sheet-btns { display: flex; gap: 10px; .nut-button { flex: 1; } }
    .sheet-cancel { display: block; text-align: center; margin-top: 14px; font-size: 14px; color: $text-muted; }
  }
}
</style>
