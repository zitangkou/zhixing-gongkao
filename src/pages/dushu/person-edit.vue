<template>
  <view class="page-person">
    <view class="field" v-if="!cardId">
      <text class="label">所属书</text>
      <WheelPicker :range="bookNames" :value="bookIndex" @change="onBook">
        <view class="picker">{{ currentBook?.title || '选择书籍' }} ▾</view>
      </WheelPicker>
    </view>
    <view class="field">
      <text class="label">人物</text>
      <nut-input v-model="form.name" placeholder="如：孝文帝、缇萦" />
    </view>
    <view class="field">
      <text class="label">留下什么</text>
      <view class="voice-field">
        <view class="grow">
          <nut-textarea
            v-model="form.lesson"
            :rows="3"
            placeholder="印象 + 启发，一两句即可"
          />
        </view>
        <VoiceInputBtn v-model="form.lesson" />
      </view>
    </view>
    <text class="hint">读到谁印象深就记一张，不必填满。</text>

    <nut-button type="primary" block :loading="saving" class="mt" @click="onSave">保存</nut-button>
    <text v-if="cardId" class="danger" @tap="onDelete">删除</text>
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
import { showConfirm, showToast } from '@/utils/platform'
import type { DushuBook, DushuPersonCard } from '@/types'

definePageConfig({ navigationBarTitleText: '人物卡' })

const router = useRouter()
const cardId = ref('')
const bookId = ref('')
/** 避免页面缓存导致重复 load；id 变化时强制重载 */
const loadedForId = ref<string | null>(null)
const books = ref<DushuBook[]>([])
const saving = ref(false)

const form = reactive({
  name: '',
  lesson: '',
})

const bookNames = computed(() => books.value.map((b) => b.title))
const bookIndex = computed(() => Math.max(0, books.value.findIndex((b) => b.id === bookId.value)))
const currentBook = computed(() => books.value.find((b) => b.id === bookId.value) || books.value[0])

function onBook(e: any) {
  const b = books.value[Number(e.detail.value)]
  if (b) bookId.value = b.id
}

function personNote(card: DushuPersonCard): string {
  if (card.lesson?.trim()) return card.lesson.trim()
  return [card.trait, card.success, card.failure].filter((x) => x?.trim()).join(' · ')
}

async function load() {
  const currentId = (router.params?.id || '').trim()
  if (loadedForId.value === currentId) return
  cardId.value = currentId
  bookId.value = (router.params?.bookId || '').trim()

  const res = await api.listDushuBooks()
  if (res.code === 0 && res.data) books.value = res.data
  if (!bookId.value && books.value.length) bookId.value = books.value[0].id

  if (currentId) {
    const list = await api.listDushuPersons()
    const card = list.data?.find((p: DushuPersonCard) => p.id === currentId)
    if (card) {
      bookId.value = card.bookId
      form.name = card.name
      form.lesson = personNote(card)
    }
  }
  loadedForId.value = currentId
}

async function onSave() {
  await flushFormBeforeSave()

  if (!bookId.value) {
    showToast('请先选书')
    return
  }
  if (!form.name.trim()) {
    showToast('请填写人物名')
    return
  }
  saving.value = true
  try {
    const payload = {
      bookId: bookId.value,
      name: form.name.trim(),
      trait: '',
      success: '',
      failure: '',
      lesson: form.lesson.trim(),
      tags: '',
    }
    const res = cardId.value
      ? await api.updateDushuPerson(cardId.value, payload)
      : await api.createDushuPerson(payload)
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

async function onDelete() {
  if (!cardId.value) return
  const ok = await showConfirm('删除人物卡', '确定删除？')
  if (!ok) return
  const res = await api.deleteDushuPerson(cardId.value)
  if (res.code === 0) {
    showToast('已删除', 'success')
    Taro.navigateBack()
  }
}

useDidShow(() => {
  const currentId = (router.params?.id || '').trim()
  if (loadedForId.value !== currentId) {
    loadedForId.value = null
  }
  load()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-person { @include page-padding; padding-bottom: 40px; }
.field { margin-bottom: 12px;
  .label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
}
.picker { padding: 10px 12px; background: $card-bg; border-radius: 8px; font-size: 14px; }
.voice-field { display: flex; gap: 6px; align-items: flex-start;
  .grow { flex: 1; min-width: 0; }
}
.mt { margin-top: 12px; }
.hint { display: block; margin-top: 4px; font-size: 12px; color: $text-muted; line-height: 1.5; }
.danger { display: block; text-align: center; margin-top: 16px; color: $danger; font-size: 13px; }
</style>
