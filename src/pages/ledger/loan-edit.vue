<template>
  <view class="page-edit">
    <view class="field">
      <text class="label">对方</text>
      <nut-input v-model="form.counterparty" placeholder="姓名/称呼" />
    </view>
    <view class="field">
      <text class="label">出借金额（元）</text>
      <nut-input v-model="form.amount" type="digit" placeholder="0.00" />
    </view>
    <view class="field">
      <text class="label">出借日期</text>
      <nut-input v-model="form.lendDate" placeholder="YYYY-MM-DD" />
    </view>
    <view class="field">
      <text class="label">约定归还日（可选）</text>
      <nut-input v-model="form.dueDate" placeholder="YYYY-MM-DD" />
    </view>
    <view class="field">
      <text class="label">事由备注</text>
      <nut-textarea v-model="form.note" :rows="2" placeholder="可选" />
    </view>
    <view class="field">
      <text class="label">凭据（借条/转账截图）</text>
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
    <text v-if="id" class="del-link" @tap="onDelete">删除整笔出借</text>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import Taro, { useDidShow, useRouter } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput, Textarea as NutTextarea } from '@nutui/nutui-taro'
import { api } from '@/api'
import { flushFormBeforeSave } from '@/utils/formFlush'
import { resolveMediaUrl } from '@/utils/media'
import { showConfirm, showToast } from '@/utils/platform'

definePageConfig({ navigationBarTitleText: '出借登记' })

const router = useRouter()
const id = ref('')
/** 避免页面缓存导致重复 load；id 变化时强制重载 */
const loadedForId = ref<string | null>(null)
const saving = ref(false)
const form = reactive({
  counterparty: '',
  amount: '',
  lendDate: new Date().toISOString().slice(0, 10),
  dueDate: '',
  note: '',
  images: [] as string[],
})

function media(url: string) {
  return resolveMediaUrl(url)
}

async function load() {
  const currentId = (router.params?.id || '').trim()
  if (loadedForId.value === currentId) return
  id.value = currentId
  if (!currentId) {
    loadedForId.value = ''
    form.counterparty = decodeURIComponent(router.params?.counterparty || '')
    return
  }
  const res = await api.getLedgerLoan(currentId)
  if (res.code !== 0 || !res.data) {
    showToast(res.message || '加载失败', 'error')
    return
  }
  form.counterparty = res.data.counterparty
  form.amount = String(res.data.principal)
  form.lendDate = res.data.lendDate
  form.dueDate = res.data.dueDate || ''
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
  Taro.previewImage({ current: media(form.images[i]), urls: form.images.map(media) })
}
function removeImg(i: number) {
  form.images.splice(i, 1)
}

async function onSave() {
  await flushFormBeforeSave()

  if (!form.counterparty.trim()) {
    showToast('请填写对方')
    return
  }
  const amount = Number(form.amount)
  if (!amount || amount <= 0) {
    showToast('请填写金额')
    return
  }
  saving.value = true
  try {
    const payload = {
      counterparty: form.counterparty.trim(),
      amount,
      lendDate: form.lendDate.trim(),
      dueDate: form.dueDate.trim(),
      note: form.note.trim(),
      images: form.images,
    }
    const res = id.value
      ? await api.updateLedgerLoan(id.value, payload)
      : await api.createLedgerLoan(payload)
    if (res.code === 0) {
      showToast('已保存', 'success')
      if (!id.value && res.data?.id) {
        setTimeout(() => {
          Taro.redirectTo({ url: `/pages/ledger/loan-detail?id=${res.data!.id}` })
        }, 300)
      } else {
        setTimeout(() => Taro.navigateBack(), 300)
      }
    } else {
      showToast(res.message || '保存失败', 'error')
    }
  } finally {
    saving.value = false
  }
}

async function onDelete() {
  if (!id.value) return
  const ok = await showConfirm('删除出借', '将同时删除全部归还记录，确定？')
  if (!ok) return
  const res = await api.deleteLedgerLoan(id.value)
  if (res.code === 0) {
    showToast('已删除', 'success')
    Taro.navigateBack({ delta: 2 })
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
  .label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
  .tip { display: block; font-size: 11px; color: $text-muted; margin-top: 4px; }
}
.imgs { display: flex; flex-wrap: wrap; gap: 8px;
  .thumb, .add-img { width: 72px; height: 72px; border-radius: 8px; background: $page-bg; }
  .add-img {
    display: flex; align-items: center; justify-content: center;
    font-size: 28px; color: $text-muted; border: 1px dashed $border-color;
  }
}
.del-link { display: block; text-align: center; margin-top: 16px; color: $danger; font-size: 13px; }
:deep(.nut-input), :deep(.nut-textarea) {
  background: $input-bg; border-radius: 6px; padding: 8px 10px !important;
}
</style>
