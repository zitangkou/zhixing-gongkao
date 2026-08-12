<template>
  <view class="page-edit">
    <view class="hint" v-if="remaining > 0">当前待收 ¥{{ formatYuan(remaining) }}</view>
    <view class="field">
      <text class="label">归还金额（元）</text>
      <nut-input v-model="form.amount" type="digit" placeholder="0.00" />
    </view>
    <view class="field">
      <text class="label">日期</text>
      <nut-input v-model="form.repayDate" placeholder="YYYY-MM-DD" />
    </view>
    <view class="field">
      <text class="label">方式</text>
      <view class="chips">
        <text
          v-for="m in methods"
          :key="m"
          class="chip"
          :class="{ on: form.method === m }"
          @tap="form.method = m"
        >{{ m }}</text>
      </view>
    </view>
    <view class="field">
      <text class="label">备注</text>
      <nut-textarea v-model="form.note" :rows="2" placeholder="可选" />
    </view>
    <view class="field">
      <text class="label">还款凭据</text>
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
    </view>
    <nut-button type="primary" block :loading="saving" @click="onSave">保存归还</nut-button>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import Taro, { useDidShow, useRouter } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput, Textarea as NutTextarea } from '@nutui/nutui-taro'
import { api } from '@/api'
import { flushFormBeforeSave } from '@/utils/formFlush'
import { formatYuan, LEDGER_REPAY_METHODS_FALLBACK } from '@/utils/ledger'
import { resolveMediaUrl } from '@/utils/media'
import { showToast } from '@/utils/platform'

definePageConfig({ navigationBarTitleText: '登记归还' })

const router = useRouter()
const loanId = ref('')
const remaining = ref(0)
/** 避免页面缓存导致重复 load；loanId 变化时强制重载 */
const loadedForId = ref<string | null>(null)
const saving = ref(false)
const methods = ref([...LEDGER_REPAY_METHODS_FALLBACK])
const form = reactive({
  amount: '',
  repayDate: new Date().toISOString().slice(0, 10),
  method: '微信',
  note: '',
  images: [] as string[],
})

function media(url: string) {
  return resolveMediaUrl(url)
}

async function loadMeta() {
  const currentId = (router.params?.loanId || '').trim()
  if (loadedForId.value === currentId) return
  loanId.value = currentId
  remaining.value = Number(router.params?.remaining || 0)
  if (remaining.value > 0) form.amount = String(remaining.value)
  const res = await api.getLedgerOverview()
  if (res.code === 0 && res.data?.repayMethods?.length) {
    methods.value = res.data.repayMethods
  }
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

  if (!loanId.value) {
    showToast('缺少出借记录', 'error')
    return
  }
  const amount = Number(form.amount)
  if (!amount || amount <= 0) {
    showToast('请填写金额')
    return
  }
  saving.value = true
  try {
    const res = await api.createLedgerRepayment(loanId.value, {
      amount,
      repayDate: form.repayDate.trim(),
      method: form.method,
      note: form.note.trim(),
      images: form.images,
    })
    if (res.code === 0) {
      showToast('已登记', 'success')
      setTimeout(() => Taro.navigateBack(), 300)
    } else {
      showToast(res.message || '保存失败', 'error')
    }
  } finally {
    saving.value = false
  }
}

useDidShow(() => {
  const currentId = (router.params?.loanId || '').trim()
  if (loadedForId.value !== currentId) {
    loadedForId.value = null
  }
  loadMeta()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';
.page-edit { @include page-padding; padding-bottom: 40px; }
.hint {
  @include card; padding: 10px 12px; margin-bottom: 12px;
  font-size: 13px; color: $accent-amber; font-weight: 600;
}
.field { margin-bottom: 14px;
  .label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
}
.chips { display: flex; flex-wrap: wrap; gap: 6px;
  .chip {
    font-size: 12px; padding: 4px 10px; border-radius: 14px; background: $card-bg; color: $text-secondary;
    &.on { background: $primary-color; color: $on-primary; }
  }
}
.imgs { display: flex; flex-wrap: wrap; gap: 8px;
  .thumb, .add-img { width: 72px; height: 72px; border-radius: 8px; background: $page-bg; }
  .add-img {
    display: flex; align-items: center; justify-content: center;
    font-size: 28px; color: $text-muted; border: 1px dashed $border-color;
  }
}
:deep(.nut-input), :deep(.nut-textarea) {
  background: $input-bg; border-radius: 6px; padding: 8px 10px !important;
}
</style>
