<template>
  <view class="page-book" v-if="book">
    <view class="hero">
      <text class="title">{{ book.title }}</text>
      <text class="meta">{{ book.category }} · {{ book.author || '作者未填' }} · {{ statusLabel(book.status) }}</text>
      <text v-if="book.currentChapter" class="chap">读到：{{ book.currentChapter }}</text>
    </view>

    <nut-button type="primary" block @click="goToday">继续今日阅读</nut-button>

    <view class="actions">
      <nut-button plain type="primary" size="small" @click="goPersons">人物卡</nut-button>
      <nut-button plain type="primary" size="small" @click="goSummary">一书一页</nut-button>
      <nut-button plain type="primary" size="small" @click="goAssets">历史输出</nut-button>
    </view>

    <view class="block" v-if="recent.length">
      <text class="block-title">最近输出</text>
      <view v-for="d in recent" :key="d.id" class="log">
        <text class="date">{{ d.logDate }} · {{ d.chapter || '未填章节' }}</text>
        <text class="goal">{{ d.goal || previewOutput(d.output) }}</text>
      </view>
    </view>

    <text class="danger" @tap="onDelete">删除本书及全部记录</text>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Taro, { useRouter, useDidShow } from '@tarojs/taro'
import { Button as NutButton } from '@nutui/nutui-taro'
import { api } from '@/api'
import { showConfirm, showToast } from '@/utils/platform'
import { statusLabel } from '@/utils/dushu'
import type { DushuBook, DushuDailyLog } from '@/types'

definePageConfig({ navigationBarTitleText: '书详情' })

const router = useRouter()
const bookId = router.params?.id || ''
const book = ref<DushuBook | null>(null)
const recent = ref<DushuDailyLog[]>([])

function previewOutput(output: Record<string, string>) {
  const vals = Object.values(output || {}).filter(Boolean)
  return vals[0]?.slice(0, 40) || '（无摘要）'
}

async function load() {
  const [b, d] = await Promise.all([
    api.getDushuBook(bookId),
    api.listDushuDaily(bookId),
  ])
  if (b.code === 0 && b.data) book.value = b.data
  if (d.code === 0 && d.data) recent.value = d.data.slice(0, 5)
}

function goToday() {
  Taro.navigateTo({ url: `/pages/dushu/today?bookId=${bookId}` })
}
function goPersons() {
  Taro.navigateTo({ url: `/pages/dushu/person-edit?bookId=${bookId}` })
}
function goSummary() {
  Taro.navigateTo({ url: `/pages/dushu/summary-edit?bookId=${bookId}` })
}
function goAssets() {
  Taro.navigateTo({ url: `/pages/dushu/assets?tab=daily&bookId=${bookId}` })
}

async function onDelete() {
  const ok = await showConfirm('删除书籍', '将同时删除每日卡、人物卡、一书一页，确定？')
  if (!ok) return
  const res = await api.deleteDushuBook(bookId)
  if (res.code === 0) {
    showToast('已删除', 'success')
    Taro.navigateBack()
  } else {
    showToast(res.message || '删除失败', 'error')
  }
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-book { @include page-padding; padding-bottom: 40px; }
.hero {
  @include card; padding: 16px; margin-bottom: 12px;
  .title { display: block; font-size: 20px; font-weight: 700; margin-bottom: 6px; }
  .meta { font-size: 12px; color: $text-muted; }
  .chap { display: block; margin-top: 6px; font-size: 13px; color: $text-secondary; }
}
.actions { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0 16px; }
.block {
  margin-top: 8px;
  .block-title { display: block; font-size: 14px; font-weight: 700; margin-bottom: 8px; }
}
.log {
  @include card; padding: 10px 12px; margin-bottom: 8px;
  .date { display: block; font-size: 12px; color: $primary-color; margin-bottom: 4px; }
  .goal { font-size: 13px; line-height: 1.45; color: $text-primary; }
}
.danger { display: block; text-align: center; margin-top: 24px; font-size: 13px; color: #c0392b; }
</style>
