<template>
  <view class="page practice-page">
    <view class="eyebrow">证据刷题</view>
    <view class="page-title">每道题都回到原文</view>

    <view class="task-card">
      <view>
        <text class="task-title">今日练习</text>
        <text class="task-desc">已答 {{ questionStore.answeredToday }} 题 · 当前错题 {{ questionStore.wrongCount }} 道</text>
      </view>
      <text class="task-mark">题</text>
    </view>

    <view class="section-head">
      <view>
        <view class="section-title">练习方式</view>
        <view class="section-meta">保留原版随机练与按文章练</view>
      </view>
    </view>

    <view class="mode-grid">
      <view class="mode-card" @tap="startRandom">
        <text class="mode-icon">随</text>
        <text class="mode-title">随机刷题</text>
        <text class="mode-desc">从已审核题库抽取 10 题</text>
      </view>
      <view class="mode-card" @tap="pickArticle">
        <text class="mode-icon">文</text>
        <text class="mode-title">按文章练</text>
        <text class="mode-desc">选一篇理论原文集中训练</text>
      </view>
    </view>

    <view class="section-head">
      <view class="section-title">复习入口</view>
    </view>
    <view class="card row" @tap="openWrong">
      <view>
        <view class="card-title">文章错题本</view>
        <view class="card-desc">按间隔计划回收错误表述</view>
      </view>
      <view class="tag">进入 ›</view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import Taro, { useDidShow } from '@tarojs/taro'
import { useQuestionStore } from '@/store/question'

const questionStore = useQuestionStore()

function startRandom() {
  Taro.navigateTo({ url: '/pages/question/taking?mode=random' })
}

function pickArticle() {
  Taro.navigateTo({ url: '/pages/question/article-pick' })
}

function openWrong() {
  Taro.navigateTo({ url: '/pages/question/wrong' })
}

async function load() {
  await questionStore.loadWrongQuestions('all')
}

onMounted(load)
useDidShow(() => void load())
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.practice-page { padding-bottom: 32px; }
.task-card {
  @include card;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 18px;
  background: linear-gradient(135deg, $primary-light, $primary-faint);
  .task-title { display: block; font-size: 16px; font-weight: 700; }
  .task-desc { display: block; margin-top: 5px; font-size: 12px; color: $text-secondary; }
  .task-mark {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    background: $primary-color;
    color: $on-primary;
    text-align: center;
    line-height: 38px;
    font-weight: 700;
  }
}
.mode-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.mode-card {
  @include card;
  margin: 0;
  .mode-icon {
    display: block;
    width: 34px;
    height: 34px;
    line-height: 34px;
    text-align: center;
    border-radius: 10px;
    background: $primary-light;
    color: $primary-color;
    font-weight: 700;
    margin-bottom: 12px;
  }
  .mode-title { display: block; font-size: 15px; font-weight: 700; }
  .mode-desc { display: block; margin-top: 5px; color: $text-muted; font-size: 11px; line-height: 1.45; }
}
</style>
