<template>
  <view class="page-shelf">
    <view class="toolbar">
      <nut-button type="primary" size="small" @click="openAdd">+ 添加书</nut-button>
      <scroll-view scroll-x class="status-scroll">
        <view class="status-row">
          <text
            v-for="s in statusTabs"
            :key="s.value"
            class="st"
            :class="{ on: filter === s.value }"
            @tap="filter = s.value; load()"
          >{{ s.label }}</text>
        </view>
      </scroll-view>
    </view>

    <view v-if="loading" class="empty">加载中...</view>
    <view v-else-if="!books.length" class="empty">
      <text class="empty-title">书架还空着</text>
      <text class="empty-desc">先加一本在读的书，比如《史记》</text>
      <nut-button type="primary" size="small" class="mt" @click="quickShiji">一键添加《史记》</nut-button>
    </view>

    <view v-else class="list">
      <view v-for="b in books" :key="b.id" class="card" @tap="goBook(b.id)">
        <view class="head">
          <text class="title">{{ b.title }}</text>
          <text class="badge">{{ statusLabel(b.status) }}</text>
        </view>
        <text class="meta">{{ b.category }} · {{ b.author || '作者未填' }}</text>
        <text v-if="b.currentChapter" class="chap">读到：{{ b.currentChapter }}</text>
      </view>
    </view>

    <nut-popup v-model:visible="showForm" position="bottom" round>
      <view class="form">
        <text class="form-title">{{ editId ? '编辑书籍' : '添加书籍' }}</text>
        <nut-input v-model="form.title" placeholder="书名 *" />
        <nut-input v-model="form.author" placeholder="作者" />
        <WheelPicker :range="categories" :value="catIndex" @change="onCat">
          <view class="picker">类型：{{ form.category }} ▾</view>
        </WheelPicker>
        <WheelPicker :range="statusLabels" :value="statusIndex" @change="onStatus">
          <view class="picker">状态：{{ statusLabel(form.status) }} ▾</view>
        </WheelPicker>
        <nut-input v-model="form.currentChapter" placeholder="当前章节，如：项羽本纪" />
        <nut-button type="primary" block :loading="saving" @click="save">保存</nut-button>
      </view>
    </nut-popup>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput, Popup as NutPopup } from '@nutui/nutui-taro'
import WheelPicker from '@/components/WheelPicker.vue'
import { api } from '@/api'
import { showToast } from '@/utils/platform'
import { DUSHU_CATEGORIES, DUSHU_STATUS, statusLabel } from '@/utils/dushu'
import type { DushuBook } from '@/types'

definePageConfig({ navigationBarTitleText: '我的书架' })

const loading = ref(false)
const saving = ref(false)
const books = ref<DushuBook[]>([])
const filter = ref('')
const showForm = ref(false)
const editId = ref('')
const categories = [...DUSHU_CATEGORIES]
const statusTabs = [{ value: '', label: '全部' }, ...DUSHU_STATUS]
const statusLabels = DUSHU_STATUS.map((s) => s.label)

const form = reactive({
  title: '',
  author: '',
  category: '历史',
  status: 'reading',
  currentChapter: '',
})

const catIndex = computed(() => Math.max(0, categories.indexOf(form.category as any)))
const statusIndex = computed(() => Math.max(0, DUSHU_STATUS.findIndex((s) => s.value === form.status)))

async function load() {
  loading.value = true
  try {
    const res = await api.listDushuBooks(filter.value || undefined)
    if (res.code === 0 && res.data) books.value = res.data
  } finally {
    loading.value = false
  }
}

function openAdd() {
  editId.value = ''
  Object.assign(form, { title: '', author: '', category: '历史', status: 'reading', currentChapter: '' })
  showForm.value = true
}

function onCat(e: any) {
  form.category = categories[Number(e.detail.value)] || '历史'
}
function onStatus(e: any) {
  form.status = DUSHU_STATUS[Number(e.detail.value)]?.value || 'reading'
}

async function save() {
  if (!form.title.trim()) {
    showToast('请填写书名')
    return
  }
  saving.value = true
  try {
    const payload = {
      title: form.title.trim(),
      author: form.author.trim(),
      category: form.category,
      status: form.status,
      currentChapter: form.currentChapter.trim(),
    }
    const res = editId.value
      ? await api.updateDushuBook(editId.value, payload)
      : await api.createDushuBook(payload)
    if (res.code === 0) {
      showToast('已保存', 'success')
      showForm.value = false
      load()
    } else {
      showToast(res.message || '保存失败', 'error')
    }
  } finally {
    saving.value = false
  }
}

async function quickShiji() {
  const res = await api.createDushuBook({
    title: '史记',
    author: '司马迁',
    category: '历史',
    status: 'reading',
    currentChapter: '',
  })
  if (res.code === 0) {
    showToast('已添加《史记》', 'success')
    load()
  } else {
    showToast(res.message || '添加失败', 'error')
  }
}

function goBook(id: string) {
  Taro.navigateTo({ url: `/pages/dushu/book-detail?id=${id}` })
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-shelf { @include page-padding; padding-bottom: 40px; }
.toolbar { margin-bottom: 12px; }
.status-scroll { margin-top: 10px; white-space: nowrap; }
.status-row { display: inline-flex; gap: 8px; }
.st {
  padding: 4px 10px; font-size: 12px; border-radius: 4px; background: $card-bg; color: $text-secondary;
  &.on { background: $primary-light; color: $primary-color; font-weight: 600; }
}
.empty { text-align: center; padding: 48px 20px; color: $text-muted;
  .empty-title { display: block; font-size: 15px; color: $text-primary; margin-bottom: 6px; }
  .mt { margin-top: 14px; }
}
.list { display: flex; flex-direction: column; gap: 10px; }
.card {
  @include card; padding: 14px;
  .head { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 4px; }
  .title { font-size: 16px; font-weight: 700; }
  .badge { font-size: 11px; color: $primary-color; }
  .meta { font-size: 12px; color: $text-muted; }
  .chap { display: block; margin-top: 4px; font-size: 12px; color: $text-secondary; }
}
.form {
  padding: 16px; display: flex; flex-direction: column; gap: 10px;
  .form-title { font-size: 16px; font-weight: 700; }
  .picker { padding: 10px 12px; background: $page-bg; border-radius: 8px; font-size: 13px; }
}
</style>
