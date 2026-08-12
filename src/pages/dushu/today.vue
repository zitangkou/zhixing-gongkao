<template>
  <view class="page-today">
    <view v-if="!books.length" class="empty">
      <text class="empty-title">还没有在读书籍</text>
      <nut-button type="primary" size="small" @click="goShelf">去书架添加</nut-button>
    </view>

    <template v-else>
      <view class="field">
        <text class="label">读哪本</text>
        <WheelPicker :range="bookNames" :value="bookIndex" @change="onBookPick">
          <view class="picker">{{ currentBook?.title || '选择书籍' }} ▾</view>
        </WheelPicker>
        <text class="mode-hint">{{ mode.modeName }} · {{ mode.tip }}</text>
      </view>

      <view class="card">
        <nut-input v-model="form.chapter" :placeholder="mode.chapterPlaceholder" />
        <view class="voice-field">
          <view class="grow">
            <text class="mini-label">今日留下</text>
            <nut-textarea v-model="form.note" :rows="3" :placeholder="mode.notePlaceholder" />
          </view>
          <VoiceInputBtn v-model="form.note" />
        </view>
      </view>

      <nut-button type="primary" block :loading="saving" @click="onSave">保存</nut-button>
    </template>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import Taro, { useDidShow, useRouter } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput, Textarea as NutTextarea } from '@nutui/nutui-taro'
import VoiceInputBtn from '@/components/VoiceInputBtn.vue'
import WheelPicker from '@/components/WheelPicker.vue'
import { api } from '@/api'
import { flattenOutput, modeForCategory } from '@/utils/dushu'
import { flushFormBeforeSave } from '@/utils/formFlush'
import { showToast } from '@/utils/platform'
import type { DushuBook } from '@/types'

definePageConfig({ navigationBarTitleText: '今日阅读' })

const router = useRouter()
const books = ref<DushuBook[]>([])
const bookId = ref('')
/** 避免页面缓存导致重复 load；bookId 变化时强制重载 */
const loadedForId = ref<string | null>(null)
const saving = ref(false)

const form = reactive({
  chapter: '',
  note: '',
})

const bookNames = computed(() => books.value.map((b) => `${b.title}（${b.category}）`))
const bookIndex = computed(() => {
  const i = books.value.findIndex((b) => b.id === bookId.value)
  return i >= 0 ? i : 0
})
const currentBook = computed(() => books.value.find((b) => b.id === bookId.value) || books.value[0] || null)
const mode = computed(() => modeForCategory(currentBook.value?.category || '其他'))

function onBookPick(e: any) {
  const b = books.value[Number(e.detail.value)]
  if (b) {
    bookId.value = b.id
    form.chapter = b.currentChapter || ''
    form.note = ''
    void loadDailyForBook(b.id)
  }
}

function goShelf() {
  Taro.navigateTo({ url: '/pages/dushu/shelf' })
}

async function loadDailyForBook(id: string) {
  const today = new Date().toISOString().slice(0, 10)
  const d = await api.getDushuDailyByDate(today, id)
  if (d.code === 0 && d.data) {
    form.chapter = d.data.chapter || form.chapter
    form.note = flattenOutput(d.data.output) || d.data.oralNote || d.data.goal || ''
  } else {
    form.note = ''
  }
}

async function load() {
  const currentId = (router.params?.bookId || '').trim()
  if (loadedForId.value === currentId) return
  bookId.value = currentId

  const res = await api.listDushuBooks('reading')
  const all = res.code === 0 && res.data ? res.data : []
  if (!all.length) {
    const allRes = await api.listDushuBooks()
    books.value = allRes.code === 0 && allRes.data ? allRes.data : []
  } else {
    books.value = all
  }
  if (!bookId.value && books.value.length) bookId.value = books.value[0].id
  const book = currentBook.value
  if (book) {
    form.chapter = book.currentChapter || ''
    await loadDailyForBook(book.id)
  }
  loadedForId.value = currentId
}

async function onSave() {
  await flushFormBeforeSave()

  if (!currentBook.value) return
  const note = form.note.trim()
  if (!note) {
    showToast('写一句今天留下的就好')
    return
  }
  saving.value = true
  try {
    const res = await api.upsertDushuDaily({
      bookId: currentBook.value.id,
      chapter: form.chapter.trim(),
      goal: '',
      output: { note },
      tags: '',
      oralNote: '',
      durationMin: 60,
    })
    if (res.code === 0) {
      showToast('已保存', 'success')
      setTimeout(() => Taro.navigateBack(), 400)
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

.page-today { @include page-padding; padding-bottom: 40px; }
.empty { text-align: center; padding: 48px 20px; color: $text-muted;
  .empty-title { display: block; margin-bottom: 12px; color: $text-primary; }
}
.field { margin-bottom: 12px;
  .label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
}
.picker { padding: 10px 12px; background: $card-bg; border-radius: 8px; font-size: 14px; font-weight: 600; }
.mode-hint { display: block; margin-top: 8px; font-size: 12px; color: $text-muted; line-height: 1.45; }
.card { @include card; padding: 12px; margin-bottom: 14px; }
.mini-label { display: block; font-size: 12px; font-weight: 600; color: $primary-color; margin: 10px 0 6px; }
.voice-field {
  display: flex; align-items: flex-start; gap: 6px;
  .grow { flex: 1; min-width: 0; }
}
</style>
