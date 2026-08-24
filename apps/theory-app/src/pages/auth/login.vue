<template>
  <view class="auth-page">
    <view class="auth-mark">知行政治理论</view><view class="auth-title">理解原理，辨清表述</view><view class="auth-desc">登录后同步今日学习包、真题化练习和错题复习</view>
    <view class="auth-card">
      <view class="auth-field"><view class="auth-label">账号</view><input v-model="username" class="auth-input" placeholder-class="auth-placeholder" placeholder="请输入用户名" confirm-type="next" /></view>
      <view class="auth-field"><view class="auth-label">密码</view><input v-model="password" class="auth-input" placeholder-class="auth-placeholder" password placeholder="请输入密码" confirm-type="done" @confirm="submit" /></view>
      <button class="auth-button" :disabled="loading" @tap="submit">{{ loading ? '登录中…' : '登录' }}</button>
      <view class="auth-hint">使用统一知行公考账号登录</view><view class="auth-link" @tap="goRegister">没有账号？立即注册</view>
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
function goRegister() { Taro.navigateTo({ url: '/pages/auth/register' }) }
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
