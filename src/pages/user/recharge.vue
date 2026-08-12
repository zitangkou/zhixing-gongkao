<template>
  <view class="page-recharge">
    <view class="balance">
      <text>当前积分</text>
      <text class="num">{{ userStore.points }}</text>
    </view>

    <view class="packages">
      <view
        v-for="pkg in packages"
        :key="pkg.id"
        class="pkg-card"
        :class="{ selected: selectedId === pkg.id }"
        @tap="selectedId = pkg.id"
      >
        <text class="pkg-label">{{ pkg.label }}</text>
        <text class="pkg-points">{{ pkg.points }} 积分</text>
        <text class="pkg-price">¥{{ pkg.price }}</text>
      </view>
    </view>

    <view class="pay-methods">
      <nut-radio-group v-model="payMethod" direction="horizontal">
        <nut-radio label="wechat">微信支付</nut-radio>
        <nut-radio label="alipay">支付宝</nut-radio>
      </nut-radio-group>
    </view>

    <nut-button type="primary" block class="primary-btn" :loading="paying" @click="handlePay">
      立即充值
    </nut-button>
    <view class="mock-tip">* 开发阶段为模拟支付，不会真实扣款</view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Button as NutButton, Radio as NutRadio, RadioGroup as NutRadioGroup } from '@nutui/nutui-taro'
import { api } from '@/api'
import { useUserStore } from '@/store/user'
import type { RechargePackage } from '@/types'
import { getPlatform, showToast } from '@/utils/platform'

definePageConfig({ navigationBarTitleText: '积分充值' })

const userStore = useUserStore()
const packages = ref<RechargePackage[]>([])
const selectedId = ref('')
const payMethod = ref('wechat')
const paying = ref(false)

onMounted(async () => {
  const res = await api.getRechargePackages()
  if (res.code === 0) {
    packages.value = res.data
    selectedId.value = res.data[0]?.id || ''
  }
})

async function handlePay() {
  if (!selectedId.value) return
  paying.value = true
  try {
    const res = await api.createPayOrder(selectedId.value)
    if (res.code === 0) {
      const platform = getPlatform()
      if (platform === 'weapp') {
        // 微信小程序支付需条件编译，此处 mock
        showToast('已调起微信支付(Mock)', 'success')
      } else {
        showToast(`模拟跳转：${payMethod.value} 支付 ¥${res.data.amount}`, 'success')
      }
    }
  } finally {
    paying.value = false
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-recharge {
  @include page-padding;
  .balance {
    text-align: center;
    padding: 20px;
    margin-bottom: 16px;
    background: $primary-light;
    border-radius: 12px;
    font-size: 14px;
    color: $text-secondary;
    .num { display: block; font-size: 32px; font-weight: 700; color: $primary-color; margin-top: 8px; }
  }
  .packages {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 20px;
    .pkg-card {
      @include card;
      text-align: center;
      padding: 16px;
      border: 2px solid transparent;
      &.selected { border-color: $primary-color; background: $primary-light; }
      .pkg-label { display: block; font-size: 13px; color: $text-muted; }
      .pkg-points { display: block; font-size: 18px; font-weight: 700; margin: 8px 0; }
      .pkg-price { display: block; font-size: 16px; color: $primary-color; }
    }
  }
  .pay-methods { margin-bottom: 20px; }
  .mock-tip { text-align: center; font-size: 11px; color: $text-muted; margin-top: 12px; }
}
</style>
