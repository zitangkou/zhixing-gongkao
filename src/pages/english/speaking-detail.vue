<template>
  <view class="page-redirect">
    <text>正在打开跟读本…</text>
  </view>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import Taro from '@tarojs/taro'

definePageConfig({ navigationBarTitleText: '跟读本' })

onMounted(() => {
  Taro.redirectTo({ url: '/pages/english/speaking-list' }).catch(() => {
    Taro.navigateTo({ url: '/pages/english/speaking-list' })
  })
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-redirect {
  padding: 40px 16px;
  text-align: center;
  color: $text-muted;
  background: $page-bg;
  min-height: 100vh;
}
</style>
