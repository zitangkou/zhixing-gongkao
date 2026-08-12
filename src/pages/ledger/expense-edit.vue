<template>
  <view class="page-edit">
    <view class="field">
      <text class="label">金额（元）</text>
      <nut-input v-model="form.amount" type="digit" placeholder="0.00" />
    </view>
    <view class="field">
      <text class="label">日期</text>
      <nut-input v-model="form.occurDate" placeholder="YYYY-MM-DD" />
    </view>
    <view class="field">
      <text class="label">分类</text>
      <view class="chips">
        <text
          v-for="c in categories"
          :key="c"
          class="chip"
          :class="{ on: form.category === c }"
          @tap="form.category = c"
        >{{ c }}</text>
      </view>
    </view>
    <view class="field">
      <text class="label">备注</text>
      <nut-textarea v-model="form.note" :rows="2" placeholder="可选" />
    </view>
    <view class="field">
      <text class="label">小票/凭据</text>
      <view class="imgs">
        <image
          v-for="(url, i) in form.images"
          :key="i"
          class="thumb"
          :src="media(url)"
          mode="aspectFill"
          @tap="preview(i)"
          @longpress="removeImg(i)"
        />
        <view v-if="form.images.length < 6" class="add-img" @tap="pickImage">+</view>
      </view>
      <text class="tip">长按可删除</text>
    </view>

    <nut-button type="primary" block :loading="saving" @click="onSave">保存</nut-button>
    <text v-if="id" class="del-link" @tap="onDelete">删除</text>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import Taro, { useDidShow, useRouter } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput, Textarea as NutTextarea } from '@nutui/nutui-taro'
import { api } from '@/api'
import { flushFormBeforeSave } from '@/utils/formFlush'
import { LEDGER_EXPENSE_CATEGORIES_FALLBACK } from '@/utils/ledger'
import { resolveMediaUrl } from '@/utils/media'
import { showConfirm, showToast } from '@/utils/platform'

definePageConfig({ navigationBarTitleText: '记支出' })

const router = useRouter()
const id = ref('')
/** 避免页面缓存导致重复 load；id 变化时强制重载 */
const loadedForId = ref<string | null>(null)
const saving = ref(false)
const categories = ref([...LEDGER_EXPENSE_CATEGORIES_FALLBACK])
const form = reactive({
  amount: '',
  occurDate: new Date().toISOString().slice(0, 10),
  category: '餐饮',
  note: '',
  images: [] as string[],
})

function media(url: string) {
  return resolveMediaUrl(url)
}

async function loadMeta() {
  const res = await api.getLedgerOverview()
  if (res.code === 0 && res.data?.expenseCategories?.length) {
    categories.value = res.data.expenseCategories
  }
}

async function load() {
  const currentId = (router.params?.id || '').trim()
  if (loadedForId.value === currentId) return
  id.value = currentId
  await loadMeta()
  if (!currentId) {
    loadedForId.value = ''
    return
  }
  const res = await api.getLedgerExpense(currentId)
  if (res.code !== 0 || !res.data) {
    showToast(res.message || '加载失败', 'error')
    return
  }
  form.amount = String(res.data.amount)
  form.occurDate = res.data.occurDate
  form.category = res.data.category
  form.note = res.data.note || ''
  form.images = [...(res.data.images || [])]
  loadedForId.value = currentId
}

async function pickImage() {
  try {
    const res = await Taro.chooseImage({
      count: Math.max(1, 6 - form.images.length),
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
    })
    const paths = res.tempFilePaths || []
    const files = (res as any).tempFiles || []
    for (let i = 0; i < paths.length; i++) {
      const file = files[i]?.originalFileObj as File | undefined
      const up = await api.uploadLedgerImage(paths[i], file)
      if (up.code === 0 && up.data?.url) form.images.push(up.data.url)
      else showToast(up.message || '上传失败', 'error')
    }
  } catch {
    /* cancel */
  }
}

function preview(i: number) {
  Taro.previewImage({
    current: media(form.images[i]),
    urls: form.images.map(media),
  })
}

function removeImg(i: number) {
  form.images.splice(i, 1)
}

async function onSave() {
  await flushFormBeforeSave()

  const amount = Number(form.amount)
  if (!amount || amount <= 0) {
    showToast('请填写金额')
    return
  }
  saving.value = true
  try {
    const payload = {
      amount,
      occurDate: form.occurDate.trim(),
      category: form.category,
      note: form.note.trim(),
      images: form.images,
    }
    const res = id.value
      ? await api.updateLedgerExpense(id.value, payload)
      : await api.createLedgerExpense(payload)
    if (res.code === 0) {
      showToast('已保存', 'success')
      setTimeout(() => Taro.navigateBack(), 300)
    } else {
      showToast(res.message || '保存失败', 'error')
    }
  } finally {
    saving.value = false
  }
}

async function onDelete() {
  if (!id.value) return
  const ok = await showConfirm('删除支出', '确定删除这条支出？')
  if (!ok) return
  const res = await api.deleteLedgerExpense(id.value)
  if (res.code === 0) {
    showToast('已删除', 'success')
    Taro.navigateBack()
  } else {
    showToast(res.message || '删除失败', 'error')
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
.page-edit { @include page-padding; padding-bottom: 40px; }
.field { margin-bottom: 14px;
  .label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; color: $text-primary; }
  .tip { display: block; font-size: 11px; color: $text-muted; margin-top: 4px; }
}
.chips { display: flex; flex-wrap: wrap; gap: 6px;
  .chip {
    font-size: 12px; padding: 4px 10px; border-radius: 14px; background: $card-bg; color: $text-secondary;
    &.on { background: $primary-color; color: $on-primary; }
  }
}
.imgs { display: flex; flex-wrap: wrap; gap: 8px;
  .thumb, .add-img {
    width: 72px; height: 72px; border-radius: 8px; background: $page-bg;
  }
  .add-img {
    display: flex; align-items: center; justify-content: center;
    font-size: 28px; color: $text-muted; border: 1px dashed $border-color;
  }
}
.del-link {
  display: block; text-align: center; margin-top: 16px; color: $danger; font-size: 13px;
}
:deep(.nut-input), :deep(.nut-textarea) {
  background: $input-bg; border-radius: 6px; padding: 8px 10px !important;
}
</style>
