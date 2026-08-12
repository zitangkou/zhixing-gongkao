<template>
  <view class="page">
    <view class="field">
      <text class="label">日期</text>
      <nut-input v-model="form.snapDate" placeholder="YYYY-MM-DD" />
    </view>
    <view v-for="f in fields" :key="f.key" class="field">
      <text class="label">{{ f.label }}（元）</text>
      <nut-input v-model="form[f.key]" type="digit" placeholder="0" />
    </view>
    <view class="field">
      <text class="label">备注</text>
      <nut-textarea v-model="form.note" :rows="2" placeholder="可选" />
    </view>
    <view class="sum">合计约 ¥{{ sumPreview }}</view>
    <nut-button type="primary" block :loading="saving" @click="onSave">保存快照</nut-button>
    <text v-if="id" class="del" @tap="onDelete">删除</text>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import Taro, { useDidShow, useRouter } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput, Textarea as NutTextarea } from '@nutui/nutui-taro'
import { api } from '@/api'
import { flushFormBeforeSave } from '@/utils/formFlush'
import { formatYuan } from '@/utils/wealth'
import { showConfirm, showToast } from '@/utils/platform'

definePageConfig({ navigationBarTitleText: '资产快照' })

const fields = [
  { key: 'cash', label: '现金' },
  { key: 'deposit', label: '存款' },
  { key: 'fund', label: '基金' },
  { key: 'stock', label: '股票' },
  { key: 'other', label: '其它' },
] as const

const router = useRouter()
const id = ref('')
/** 避免页面缓存导致重复 load；id 变化时强制重载 */
const loadedForId = ref<string | null>(null)
const saving = ref(false)
const form = reactive({
  snapDate: new Date().toISOString().slice(0, 10),
  cash: '',
  deposit: '',
  fund: '',
  stock: '',
  other: '',
  note: '',
})

const sumPreview = computed(() => {
  const n = fields.reduce((s, f) => s + (Number(form[f.key]) || 0), 0)
  return formatYuan(n)
})

async function load() {
  const currentId = (router.params?.id || '').trim()
  if (loadedForId.value === currentId) return
  id.value = currentId
  if (!currentId) {
    loadedForId.value = ''
    return
  }
  const res = await api.getWealthSnapshot(currentId)
  if (res.code !== 0 || !res.data) return
  const d = res.data
  form.snapDate = d.snapDate
  form.cash = String(d.cash || '')
  form.deposit = String(d.deposit || '')
  form.fund = String(d.fund || '')
  form.stock = String(d.stock || '')
  form.other = String(d.other || '')
  form.note = d.note || ''
  loadedForId.value = currentId
}

async function onSave() {
  await flushFormBeforeSave()

  saving.value = true
  try {
    const payload = {
      snapDate: form.snapDate,
      cash: Number(form.cash) || 0,
      deposit: Number(form.deposit) || 0,
      fund: Number(form.fund) || 0,
      stock: Number(form.stock) || 0,
      other: Number(form.other) || 0,
      note: form.note.trim(),
    }
    const res = id.value
      ? await api.updateWealthSnapshot(id.value, payload)
      : await api.createWealthSnapshot(payload)
    if (res.code !== 0) {
      showToast(res.message || '保存失败')
      return
    }
    showToast('已保存')
    setTimeout(() => Taro.navigateBack(), 400)
  } finally {
    saving.value = false
  }
}

async function onDelete() {
  if (!id.value) return
  const ok = await showConfirm('删除快照', '确定删除？')
  if (!ok) return
  await api.deleteWealthSnapshot(id.value)
  showToast('已删除')
  Taro.navigateBack()
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
.page { padding: 16px 16px 48px; }
.field { margin-bottom: 18px;
  .label { display: block; font-size: 13px; font-weight: 600; color: $text-secondary; margin-bottom: 8px; }
}
.sum { margin-bottom: 16px; font-size: 15px; font-weight: 600; color: $text-primary; }
.del { display: block; text-align: center; padding: 16px; color: $danger; }
</style>
