<template>
  <view class="page">
    <text class="tip">情绪来了就翻这里。分层原则：硬规则不可破。</text>

    <view v-for="layer in layers" :key="layer" class="layer">
      <view class="layer-head">
        <text class="layer-title">{{ layerLabel(layer) }}</text>
        <text class="add" @tap="openAdd(layer)">+ 添加</text>
      </view>
      <view v-for="p in byLayer(layer)" :key="p.id" class="item">
        <view class="item-main" @tap="openEdit(p)">
          <text class="item-title" :class="{ off: !p.isEnabled }">{{ p.title }}</text>
          <text v-if="p.content" class="item-content">{{ p.content }}</text>
        </view>
        <text class="x" @tap="onDelete(p)">×</text>
      </view>
      <view v-if="!byLayer(layer).length" class="empty-hint">暂无，点右上添加</view>
    </view>

    <view v-if="dialog" class="mask" @tap="dialog = false">
      <view class="dialog" @tap.stop>
        <text class="dlg-title">{{ editId ? '编辑原则' : '新原则' }}</text>
        <nut-input v-model="form.title" placeholder="标题，如：不融资" />
        <nut-textarea v-model="form.content" :rows="3" placeholder="说明（可选）" class="mt" />
        <view class="dlg-actions">
          <text class="cancel" @tap="dialog = false">取消</text>
          <text class="ok" @tap="onSave">保存</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useDidShow } from '@tarojs/taro'
import { flushFormBeforeSave } from '@/utils/formFlush'
import { Input as NutInput, Textarea as NutTextarea } from '@nutui/nutui-taro'
import { api } from '@/api'
import { WEALTH_LAYER_LABELS } from '@/utils/wealth'
import { showConfirm, showToast } from '@/utils/platform'
import type { WealthPrinciple } from '@/types'

definePageConfig({ navigationBarTitleText: '投资方法论' })

const layers = [1, 2, 3, 4]
const rows = ref<WealthPrinciple[]>([])
const dialog = ref(false)
const editId = ref('')
const form = reactive({ layer: 1, title: '', content: '' })

function layerLabel(n: number) {
  return WEALTH_LAYER_LABELS[n] || `第${n}层`
}

function byLayer(layer: number) {
  return rows.value.filter((p) => p.layer === layer)
}

function openAdd(layer: number) {
  editId.value = ''
  form.layer = layer
  form.title = ''
  form.content = ''
  dialog.value = true
}

function openEdit(p: WealthPrinciple) {
  editId.value = p.id
  form.layer = p.layer
  form.title = p.title
  form.content = p.content || ''
  dialog.value = true
}

async function load() {
  const res = await api.listWealthPrinciples()
  if (res.code === 0) rows.value = res.data || []
}

async function onSave() {
  await flushFormBeforeSave()
  if (!form.title.trim()) {
    showToast('请填写标题')
    return
  }
  const payload = {
    layer: form.layer,
    title: form.title.trim(),
    content: form.content.trim(),
  }
  const res = editId.value
    ? await api.updateWealthPrinciple(editId.value, payload)
    : await api.createWealthPrinciple(payload)
  if (res.code !== 0) {
    showToast(res.message || '保存失败')
    return
  }
  dialog.value = false
  showToast('已保存')
  await load()
}

async function onDelete(p: WealthPrinciple) {
  const ok = await showConfirm('删除原则', `删除「${p.title}」？`)
  if (!ok) return
  await api.deleteWealthPrinciple(p.id)
  await load()
}

useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';
.page { padding: 16px 16px 40px; }
.tip { display: block; font-size: 13px; color: $text-muted; line-height: 1.5; margin-bottom: 20px; }
.layer { margin-bottom: 28px; }
.layer-head {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;
  .layer-title { font-size: 15px; font-weight: 700; color: $text-primary; }
  .add { font-size: 13px; color: $primary-color; font-weight: 600; }
}
.item {
  display: flex; gap: 10px; padding: 14px 0; border-bottom: 1px solid $border-color;
  .item-main { flex: 1; min-width: 0; }
  .item-title { display: block; font-size: 15px; font-weight: 600; color: $text-primary;
    &.off { opacity: 0.45; text-decoration: line-through; }
  }
  .item-content { display: block; margin-top: 6px; font-size: 13px; color: $text-secondary; line-height: 1.45; }
  .x { color: $text-muted; font-size: 18px; padding: 0 4px; }
}
.empty-hint { font-size: 13px; color: $text-muted; padding: 8px 0; }
.mask {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: flex-end; z-index: 20;
}
.dialog {
  width: 100%; background: $card-bg; border-radius: 12px 12px 0 0; padding: 20px 16px calc(20px + env(safe-area-inset-bottom));
  .dlg-title { display: block; font-size: 16px; font-weight: 700; margin-bottom: 14px; }
  .mt { margin-top: 12px; }
  .dlg-actions {
    display: flex; justify-content: flex-end; gap: 24px; margin-top: 16px;
    .cancel { color: $text-muted; }
    .ok { color: $primary-color; font-weight: 700; }
  }
}
</style>
