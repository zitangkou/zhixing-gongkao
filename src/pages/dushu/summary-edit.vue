<template>
  <view class="page-summary">
    <text class="tip">读完整本后，用两三句话收个尾即可。在读也可先草稿。</text>
    <view class="field">
      <text class="label">书名</text>
      <WheelPicker v-if="!fixedBook" :range="bookNames" :value="bookIndex" @change="onBook">
        <view class="picker">{{ currentBook?.title || '选择书籍' }} ▾</view>
      </WheelPicker>
      <text v-else class="picker">{{ currentBook?.title }}</text>
    </view>
    <view class="field">
      <text class="label">这本书带走什么</text>
      <view class="voice-field">
        <view class="grow">
          <nut-textarea
            v-model="form.coreQuestion"
            :rows="3"
            placeholder="核心问题 / 最大启发，一两段即可"
          />
        </view>
        <VoiceInputBtn v-model="form.coreQuestion" />
      </view>
    </view>
    <view class="field">
      <text class="label">接下来能做什么（可选）</text>
      <view class="voice-field">
        <view class="grow"><nut-input v-model="form.action" placeholder="一个小行动" /></view>
        <VoiceInputBtn v-model="form.action" />
      </view>
    </view>

    <nut-button type="primary" block :loading="saving" @click="onSave">保存</nut-button>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import Taro, { useDidShow, useRouter } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput, Textarea as NutTextarea } from '@nutui/nutui-taro'
import VoiceInputBtn from '@/components/VoiceInputBtn.vue'
import WheelPicker from '@/components/WheelPicker.vue'
import { api } from '@/api'
import { flushFormBeforeSave } from '@/utils/formFlush'
import { showToast } from '@/utils/platform'
import type { DushuBook } from '@/types'

definePageConfig({ navigationBarTitleText: '一书一页' })

const router = useRouter()
const bookId = ref('')
const fixedBook = ref(false)
/** 避免页面缓存导致重复 load；bookId 变化时强制重载 */
const loadedForId = ref<string | null>(null)
const books = ref<DushuBook[]>([])
const saving = ref(false)

const form = reactive({
  coreQuestion: '',
  action: '',
})

const bookNames = computed(() => books.value.map((b) => b.title))
const bookIndex = computed(() => Math.max(0, books.value.findIndex((b) => b.id === bookId.value)))
const currentBook = computed(() => books.value.find((b) => b.id === bookId.value) || books.value[0])

function onBook(e: any) {
  const b = books.value[Number(e.detail.value)]
  if (b) {
    bookId.value = b.id
    loadSummary()
  }
}

async function loadSummary() {
  if (!bookId.value) return
  const res = await api.getDushuSummary(bookId.value)
  if (res.code === 0 && res.data) {
    const s = res.data
    const legacy = [s.skeleton, ...(s.insights || []), s.story, s.model].filter((x) => x?.trim()).join('\n')
    form.coreQuestion = s.coreQuestion?.trim() || legacy
    form.action = s.action || ''
  }
}

async function load() {
  const currentId = (router.params?.bookId || '').trim()
  if (loadedForId.value === currentId) return
  bookId.value = currentId
  fixedBook.value = !!currentId

  const res = await api.listDushuBooks()
  if (res.code === 0 && res.data) books.value = res.data
  if (!bookId.value && books.value.length) bookId.value = books.value[0].id
  await loadSummary()
  loadedForId.value = currentId
}

async function onSave() {
  await flushFormBeforeSave()

  if (!bookId.value) {
    showToast('请先选书')
    return
  }
  if (!form.coreQuestion.trim() && !form.action.trim()) {
    showToast('写一句带走的就好')
    return
  }
  saving.value = true
  try {
    const res = await api.upsertDushuSummary({
      bookId: bookId.value,
      coreQuestion: form.coreQuestion.trim(),
      skeleton: '',
      insights: [],
      story: '',
      model: '',
      action: form.action.trim(),
    })
    if (res.code === 0) {
      showToast('已保存', 'success')
      Taro.navigateBack()
    } else {
      showToast(res.message || '保存失败', 'error')
    }
  } finally {
    saving.value = false
  }
}

useDidShow(() => {
  const currentId = (router.params?.bookId || '').trim()
  if (loadedForId.value !== currentId) {
    loadedForId.value = null
  }
  load()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-summary { @include page-padding; padding-bottom: 40px; }
.tip { display: block; font-size: 12px; color: $text-muted; margin-bottom: 12px; line-height: 1.45; }
.field { margin-bottom: 12px;
  .label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
}
.picker { padding: 10px 12px; background: $card-bg; border-radius: 8px; font-size: 14px; }
.voice-field { display: flex; gap: 6px; align-items: flex-start;
  .grow { flex: 1; min-width: 0; }
}
</style>
