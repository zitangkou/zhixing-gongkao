<template>
  <view class="auth-page">
    <view class="auth-mark">知行申论</view><view class="auth-title">读得深，写得出</view><view class="auth-desc">登录后同步今日精读、三刀拆解和训练沉淀</view>
    <view class="auth-card">
      <input v-model="username" class="auth-input" placeholder="用户名" />
      <input v-model="password" class="auth-input" password placeholder="密码" />
      <button class="auth-button" :disabled="loading" @tap="submit">{{ loading ? '登录中…' : '登录' }}</button>
      <view class="auth-hint">使用统一知行公考账号登录</view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Taro from '@tarojs/taro'
import { api } from '@/api'
import { setToken } from '@/utils/auth'
import { showToast } from '@/utils/platform'

const username = ref('')
const password = ref('')
const loading = ref(false)
async function submit() {
  if (!username.value.trim() || !password.value) return showToast('请输入用户名和密码')
  loading.value = true
  const response = await api.login(username.value.trim(), password.value)
  loading.value = false
  if (response.code !== 0 || !response.data?.access_token) return showToast(response.message || '登录失败')
  setToken(response.data.access_token)
  Taro.switchTab({ url: '/pages/today/index' })
}
</script>
