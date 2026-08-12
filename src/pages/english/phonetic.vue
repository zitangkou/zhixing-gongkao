<template>
  <view class="page-phonetic">
    <view class="filter-bar">
      <text
        v-for="t in tabs"
        :key="t.value"
        class="tab"
        :class="{ active: activeTab === t.value }"
        @tap="activeTab = t.value; load()"
      >{{ t.label }}<text class="count">{{ countByCat(t.value) }}</text></text>
    </view>

    <view v-if="loading" class="empty">加载中...</view>
    <view v-else>
      <view class="phonetic-grid">
        <view
          v-for="p in filtered"
          :key="p.id"
          class="ph-card"
          :class="{ mastered: isMastered(p.id) }"
          @tap="goDetail(p.id)"
        >
          <text class="ph-symbol" @tap.stop="playPhonetic(p)">{{ p.symbol }}</text>
          <text v-if="p.exampleWords.length" class="ph-word" @tap.stop="play(p.exampleWords[0].word)">{{ p.exampleWords[0].word }}</text>
          <text v-if="isMastered(p.id)" class="ph-badge">✓ 已掌握</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { api } from '@/api'
import { phoneticPronounceText } from '@/utils/phonetic'
import { playPronounce } from '@/utils/pronounce'
import type { PhoneticLesson, PhoneticProgressMap } from '@/types'

definePageConfig({ navigationBarTitleText: '音标学习' })

const loading = ref(false)
const phonetics = ref<PhoneticLesson[]>([])
const progress = ref<PhoneticProgressMap>({})
const activeTab = ref('')

const tabs = [
  { value: '', label: '全部' },
  { value: 'unit_vowel', label: '单元音' },
  { value: 'diphthong', label: '双元音' },
  { value: 'consonant', label: '辅音' },
]

const filtered = computed(() => {
  if (!activeTab.value) return phonetics.value
  return phonetics.value.filter((p) => p.category === activeTab.value)
})

function countByCat(cat: string) {
  if (!cat) return phonetics.value.length
  return phonetics.value.filter((p) => p.category === cat).length
}

function isMastered(id: string) {
  return progress.value[id]?.status === 'mastered'
}

function play(word: string) {
  playPronounce(word)
}

/** 播放音标本身的近似发音 */
function playPhonetic(p: PhoneticLesson) {
  play(phoneticPronounceText(p.symbol))
}

async function load() {
  loading.value = true
  try {
    const [r1, r2] = await Promise.all([
      api.listPhonetics(),
      api.getPhoneticProgress(),
    ])
    if (r1.code === 0 && r1.data) phonetics.value = r1.data
    if (r2.code === 0 && r2.data) progress.value = r2.data
  } finally {
    loading.value = false
  }
}

function goDetail(id: string) {
  Taro.navigateTo({ url: `/pages/english/phonetic-detail?id=${id}` })
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-phonetic {
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
    .count {
      display: inline-block;
      margin-left: 4px;
      font-size: 10px;
      opacity: 0.7;
    }
  }
}

.empty { text-align: center; padding: 40px 0; color: $text-muted; }

.phonetic-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.ph-card {
  background: $card-bg;
  border-radius: $radius-md;
  padding: 14px 8px 10px;
  text-align: center;
  box-shadow: $shadow-card;
  position: relative;
  &:active { opacity: 0.85; }
  &.mastered {
    border: 2px solid $accent-green;
  }
}

.ph-symbol {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: $primary-color;
  margin-bottom: 4px;
  &:active { opacity: 0.6; }
}

.ph-word {
  display: block;
  font-size: 12px;
  color: $accent-blue;
  &:active { opacity: 0.6; }
}

.ph-badge {
  display: block;
  font-size: 10px;
  color: $accent-green;
  font-weight: 600;
  margin-top: 2px;
}
</style>
