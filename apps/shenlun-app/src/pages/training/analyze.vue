<template>
  <view class="analyze-page">
    <template v-if="completed"><view class="complete-mark">✓</view><view class="page-title complete-title">今日训练完成</view><view class="complete-copy">你留下了一个结构判断、一段短作答和一个可迁移表达。</view><view class="card deposit-card"><view class="card-desc">今日表达</view><view class="card-title">{{ deposit }}</view></view><button class="auth-button" @tap="home">返回今日</button></template>
    <template v-else><view class="eyebrow">{{ articleTitle }}</view><view class="page-title">三刀拆开，再主动输出</view><view class="analyze-tip">内容自动保存在本机，提交后同步到开采本。</view>
      <view class="section-head"><view class="section-title">第一刀 · 立意</view><view class="section-meta">文章解决什么问题</view></view><textarea v-model="thesis" class="analyze-input" maxlength="300" placeholder="用自己的话写出核心问题与主张" />
      <view class="section-head"><view class="section-title">第二刀 · 结构</view><view class="section-meta">观点如何展开</view></view><textarea v-model="structure" class="analyze-input" maxlength="500" placeholder="梳理总论点、分论点和论证关系" />
      <view class="section-head"><view class="section-title">第三刀 · 表达</view><view class="section-meta">哪些写法可迁移</view></view><textarea v-model="expression" class="analyze-input" maxlength="300" placeholder="摘取并解释一个规范表达或句式" />
      <view class="section-head"><view class="section-title">120 字短作答</view><view class="section-meta">{{ answer.length }} / 120</view></view><textarea v-model="answer" class="analyze-input answer-input" maxlength="120" placeholder="概括文章关注的核心问题与主要解决思路" />
      <view class="section-head"><view class="section-title">表达沉淀</view><view class="section-meta">只留一个</view></view><input v-model="deposit" class="auth-input deposit-input" maxlength="40" placeholder="今天最值得带走的规范表达" />
      <button class="auth-button submit-training" :disabled="submitting" @tap="submit">{{ submitting ? '正在保存…' : '完成今日训练' }}</button>
    </template>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import Taro, { useRouter } from '@tarojs/taro'
import { api } from '@/api'
import { useDailyTaskStore } from '@/store/dailyTask'
import { showToast } from '@/utils/platform'

const router=useRouter(); const store=useDailyTaskStore(); const articleId=String(router.params?.articleId||''); const rawTitle=String(router.params?.title||'申论精读'); const articleTitle=decodeURIComponent(rawTitle); const taskId=String(router.params?.taskId||'');
const thesis=ref(''); const structure=ref(''); const expression=ref(''); const answer=ref(''); const deposit=ref(''); const submitting=ref(false); const completed=ref(false); const storageKey=`shenlun-analyze:${articleId}`
function snapshot(){return {thesis:thesis.value,structure:structure.value,expression:expression.value,answer:answer.value,deposit:deposit.value}}
watch([thesis,structure,expression,answer,deposit],()=>Taro.setStorageSync(storageKey,snapshot()))
onMounted(async()=>{const cached=Taro.getStorageSync(storageKey)||{};thesis.value=cached.thesis||'';structure.value=cached.structure||'';expression.value=cached.expression||'';answer.value=cached.answer||'';deposit.value=cached.deposit||'';if(taskId&&!store.task)await store.load()})
async function submit(){if(!thesis.value.trim()||!structure.value.trim()||!expression.value.trim())return showToast('请完成三刀拆解');if(answer.value.trim().length<30)return showToast('短作答至少写 30 字');if(!deposit.value.trim())return showToast('请留下一个规范表达');submitting.value=true;const draft=snapshot();const mine=await api.saveMine({articleId,articleTitle,sourceExcerpt:thesis.value,argumentChain:structure.value,templateSentence:expression.value,terms:[deposit.value.trim()]});if(mine.code!==0){submitting.value=false;return showToast(mine.message||'开采本保存失败')}if(taskId&&store.task?.id===taskId){let ok=true;const state=store.task.progress.state;if(state==='in_progress'){ok=await store.transition('save',draft,3)&&await store.transition('submit',draft,4)}if(ok&&store.task?.progress.state==='submitted')ok=await store.transition('review');if(ok&&store.task?.progress.state==='reviewed')ok=await store.transition('complete');if(!ok){submitting.value=false;return showToast(store.message||'任务进度同步失败')}}Taro.removeStorageSync(storageKey);submitting.value=false;completed.value=true}
function home(){Taro.switchTab({url:'/pages/today/index'})}
</script>
