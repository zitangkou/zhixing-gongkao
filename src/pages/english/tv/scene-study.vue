<template>
  <view class="page-study">
    <view v-if="loading" class="empty">加载中...</view>
    <template v-else-if="scene">
      <view class="head">
        <text class="title">{{ scene.title }}</text>
        <text class="meta">
          {{ scene.timeRange ? `${scene.timeRange} · ` : '' }}目标 {{ scene.targetCount }} 卡 · {{ session?.completedCount || 0 }}/5 步
        </text>
        <text v-if="scene.sceneSummary" class="summary">{{ scene.sceneSummary }}</text>
      </view>

      <view class="steps">
        <text
          v-for="(s, i) in stepDefs"
          :key="s.key"
          class="step-dot"
          :class="{ on: step === i, done: sessionDone(s.key), locked: !canGoStep(i) }"
          @tap="onStepTap(i)"
        >{{ i + 1 }}</text>
      </view>

      <!-- 1 盲看 -->
      <view v-if="step === 0" class="panel">
        <text class="panel-title">① 盲看</text>
        <text class="panel-desc">关掉字幕看一遍，写下你理解的情节（不求精确）。</text>
        <nut-textarea v-model="blindNote" :rows="4" placeholder="我的理解…" />
        <view class="btn-row">
          <nut-button type="primary" size="small" @click="saveBlind">完成盲看 →</nut-button>
        </view>
      </view>

      <!-- 2 精拆 -->
      <view v-if="step === 1" class="panel">
        <text class="panel-title">② 精拆对白</text>
        <text class="panel-desc">录入原句，从对白生成表达卡。</text>
        <view class="btn-row top">
          <nut-button size="small" @click="onAddLine">+ 加对白</nut-button>
          <nut-button size="small" type="primary" plain @click="saveLines">保存对白</nut-button>
        </view>

        <view v-for="(ln, idx) in editLines" :key="idx" class="line-card">
          <view class="line-head">
            <nut-input v-model="ln.speaker" placeholder="角色" class="speaker-input" />
            <text class="line-del" @tap="editLines.splice(idx, 1)">删</text>
          </view>
          <nut-textarea v-model="ln.en" :rows="2" placeholder="English" />
          <nut-input v-model="ln.zh" placeholder="中文" />
          <nut-input v-model="ln.phoneticNote" placeholder="连读/弱读备注（可选）" />
          <text v-if="ln.en.trim()" class="gen" @tap="openExprForm(ln)">→ 生成表达卡</text>
        </view>

        <view v-if="exprForm.open" class="expr-form">
          <text class="expr-form-title">新建表达卡</text>
          <text class="form-label">句型 *</text>
          <nut-input v-model="exprForm.phrase" placeholder="There's gotta be…" />
          <text class="form-label">含义</text>
          <nut-input v-model="exprForm.meaning" placeholder="中文意思" />
          <text class="form-label">使用场景</text>
          <nut-input v-model="exprForm.usageScene" placeholder="什么场合用" />
          <text class="form-label">我的造句（可选）</text>
          <nut-input v-model="exprForm.myExample" placeholder="换成自己的话" />
          <view class="btn-row top">
            <nut-button size="small" @click="exprForm.open = false">取消</nut-button>
            <nut-button type="primary" size="small" :loading="exprSaving" @click="submitExpr">加入表达库</nut-button>
          </view>
        </view>

        <view v-if="scene.expressions.length" class="expr-mini">
          <text class="sub">已有表达卡 {{ scene.expressions.length }}</text>
          <view v-for="e in scene.expressions" :key="e.id" class="expr-chip">
            <text class="chip-phrase">{{ e.phrase }}</text>
            <text v-if="e.meaning" class="chip-meaning">{{ e.meaning }}</text>
          </view>
        </view>
        <view class="btn-row">
          <nut-button type="primary" size="small" @click="finishParse">完成精拆 →</nut-button>
        </view>
      </view>

      <!-- 3 跟读 -->
      <view v-if="step === 2" class="panel">
        <text class="panel-title">③ 跟读</text>
        <text class="panel-desc">选句听原音、录音跟读（写入跟读本）。</text>
        <view v-if="!scene.lines.length" class="hint">请先在精拆步骤录入对白</view>
        <view v-for="ln in scene.lines" :key="ln.id" class="shadow-card">
          <text class="shadow-en" @tap="play(ln.en)">{{ ln.speaker ? `${ln.speaker}: ` : '' }}{{ ln.en }}</text>
          <text v-if="ln.zh" class="shadow-zh">{{ ln.zh }}</text>
          <view class="shadow-acts">
            <text class="act" @tap="play(ln.en)">🔊 听</text>
            <text class="act" @tap="addAndRecord(ln)">
              {{ recording && pendingShadowId ? '⏹ 停止录音' : '🎙 跟读录音' }}
            </text>
          </view>
        </view>
        <view class="btn-row">
          <nut-button type="primary" size="small" @click="finishShadow">完成跟读 →</nut-button>
        </view>
      </view>

      <!-- 4 置换 -->
      <view v-if="step === 3" class="panel">
        <text class="panel-title">④ 场景置换输出</text>
        <text class="panel-desc">用今天的句型，复述场景或换成你生活中的场景说一遍。</text>
        <nut-textarea v-model="retellText" :rows="5" placeholder="写下来，或先说再记要点…" />
        <view class="btn-row">
          <nut-button type="primary" size="small" @click="saveRetell">完成置换 →</nut-button>
        </view>
      </view>

      <!-- 5 复习标记 -->
      <view v-if="step === 4" class="panel">
        <text class="panel-title">⑤ 复习标记</text>
        <text class="panel-desc">今日新卡已进入 SRS。可快速过一遍，或勾选完成本场景。</text>
        <view v-if="!scene.expressions.length" class="hint">还没有表达卡，请回到精拆生成</view>
        <view v-for="e in scene.expressions" :key="e.id" class="review-card">
          <text class="r-phrase" @tap="play(e.phrase)">{{ e.phrase }}</text>
          <text v-if="e.meaning" class="r-meaning">{{ e.meaning }}</text>
          <view class="r-acts">
            <text class="act" @tap="reviewExpr(e.id, 'again')">再练</text>
            <text class="act good" @tap="reviewExpr(e.id, 'good')">记住了</text>
          </view>
        </view>
        <view class="btn-row">
          <nut-button type="primary" size="small" @click="finishReview">完成本场景 ✓</nut-button>
        </view>
      </view>
    </template>
    <view v-else class="empty">场景不存在或加载失败</view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import Taro, { useDidShow, useRouter } from '@tarojs/taro'
import { Button as NutButton, Input as NutInput, Textarea as NutTextarea } from '@nutui/nutui-taro'
import { api } from '@/api'
import { playPronounce } from '@/utils/pronounce'
import { showToast } from '@/utils/platform'
import type { TvDialogueLine, TvSceneDetail, TvStudySession } from '@/types'

definePageConfig({ navigationBarTitleText: '场景精学' })

const router = useRouter()
const sceneId = router.params?.id || ''
const loading = ref(false)
const scene = ref<TvSceneDetail | null>(null)
const session = ref<TvStudySession | null>(null)
const step = ref(0)
const blindNote = ref('')
const retellText = ref('')
const editLines = ref<{ speaker: string; en: string; zh: string; phoneticNote: string }[]>([])
const exprSaving = ref(false)
const exprForm = reactive({
  open: false,
  phrase: '',
  meaning: '',
  usageScene: '',
  myExample: '',
  sourceLine: '',
})

const stepDefs = [
  { key: 'blind' },
  { key: 'parse' },
  { key: 'shadow' },
  { key: 'retell' },
  { key: 'review' },
]

let recorderManager: ReturnType<typeof Taro.getRecorderManager> | null = null
const pendingShadowId = ref('')
const recording = ref(false)

function sessionDone(key: string) {
  const s = session.value
  if (!s) return false
  const map: Record<string, boolean> = {
    blind: s.stepBlind,
    parse: s.stepParse,
    shadow: s.stepShadow,
    retell: s.stepRetell,
    review: s.stepReview,
  }
  return !!map[key]
}

/** 已完成或当前步可进；禁止向前跳过未完成步骤 */
function canGoStep(i: number) {
  if (i <= step.value) return true
  if (sessionDone(stepDefs[i].key)) return true
  // 允许进入「下一未完成步」当且仅当前面步都已完成
  for (let j = 0; j < i; j++) {
    if (!sessionDone(stepDefs[j].key)) return false
  }
  return true
}

function onStepTap(i: number) {
  if (!canGoStep(i)) {
    showToast('请先完成前面的步骤', 'none')
    return
  }
  step.value = i
}

function play(text: string) {
  if (text) playPronounce(text)
}

function syncEditLines() {
  editLines.value = (scene.value?.lines || []).map((l) => ({
    speaker: l.speaker || '',
    en: l.en || '',
    zh: l.zh || '',
    phoneticNote: l.phoneticNote || '',
  }))
  if (!editLines.value.length) {
    editLines.value = [
      { speaker: '', en: '', zh: '', phoneticNote: '' },
      { speaker: '', en: '', zh: '', phoneticNote: '' },
      { speaker: '', en: '', zh: '', phoneticNote: '' },
      { speaker: '', en: '', zh: '', phoneticNote: '' },
    ]
  }
}

function onAddLine() {
  editLines.value.push({ speaker: '', en: '', zh: '', phoneticNote: '' })
}

function openExprForm(ln: { en: string; zh: string }) {
  exprForm.open = true
  exprForm.phrase = ln.en.trim().slice(0, 80)
  exprForm.meaning = ln.zh.trim()
  exprForm.usageScene = scene.value?.sceneSummary || ''
  exprForm.myExample = ''
  exprForm.sourceLine = ln.en.trim()
}

async function submitExpr() {
  const phrase = exprForm.phrase.trim()
  if (!phrase) {
    showToast('请填写句型', 'none')
    return
  }
  exprSaving.value = true
  try {
    const res = await api.createTvExpression({
      phrase,
      meaning: exprForm.meaning.trim(),
      usageScene: exprForm.usageScene.trim(),
      myExample: exprForm.myExample.trim(),
      sourceLine: exprForm.sourceLine,
      sceneId,
      episodeId: scene.value?.episodeId,
    })
    if (res.code === 0) {
      showToast('已加入表达卡', 'success')
      exprForm.open = false
      await reloadScene()
    } else {
      showToast(res.message || '创建失败', 'error')
    }
  } finally {
    exprSaving.value = false
  }
}

async function patchSession(data: Parameters<typeof api.updateTvSession>[1]) {
  const res = await api.updateTvSession(sceneId, data)
  if (res.code === 0 && res.data) session.value = res.data
  else if (res.code !== 0) showToast(res.message || '保存失败', 'error')
  return res
}

async function saveBlind() {
  await patchSession({ blindNote: blindNote.value, stepBlind: true })
  showToast('盲看完成', 'success')
  step.value = 1
}

async function saveLines(): Promise<boolean> {
  const lines = editLines.value
    .filter((l) => l.en.trim() || l.zh.trim())
    .map((l, i) => ({ ...l, sortOrder: i }))
  if (!lines.length) {
    showToast('请至少录入一句对白', 'none')
    return false
  }
  const res = await api.updateTvScene(sceneId, { lines })
  if (res.code === 0 && res.data) {
    scene.value = res.data
    syncEditLines()
    showToast('对白已保存', 'success')
    return true
  }
  showToast(res.message || '保存失败', 'error')
  return false
}

async function finishParse() {
  const ok = await saveLines()
  if (!ok) return
  await patchSession({ stepParse: true })
  step.value = 2
}

function ensureRecorder() {
  if (recorderManager) return recorderManager
  try {
    recorderManager = Taro.getRecorderManager()
    recorderManager.onStop(async (res) => {
      recording.value = false
      const id = pendingShadowId.value
      pendingShadowId.value = ''
      if (!id) return
      const up = await api.uploadSpeakingRecording(res.tempFilePath)
      if (up.code === 0 && up.data?.url) {
        await api.updateShadowing(id, { recordingUrl: up.data.url, practiced: true })
        showToast('录音已保存', 'success')
      } else {
        showToast(up.message || '上传失败', 'error')
      }
    })
  } catch {
    recorderManager = null
  }
  return recorderManager
}

async function addAndRecord(ln: TvDialogueLine) {
  if (!ln.en.trim()) return
  const rm = ensureRecorder()
  if (recording.value && pendingShadowId.value) {
    try { rm?.stop() } catch { /* ignore */ }
    return
  }

  const title = `${scene.value?.title || 'Scene'} · TV`
  const add = await api.addShadowing({
    sentence: ln.en,
    articleTitle: title,
    note: `tvsc:${sceneId}`,
  })
  if (add.code !== 0 || !add.data) {
    showToast(add.message || '加入跟读本失败', 'error')
    return
  }
  if (!rm) {
    showToast('已加入跟读本（当前环境不支持录音）', 'none')
    return
  }
  pendingShadowId.value = add.data.id
  recording.value = true
  showToast('录音中，再点一次结束', 'none')
  try {
    rm.start({ format: 'mp3', duration: 60000 })
  } catch {
    recording.value = false
    pendingShadowId.value = ''
    showToast('无法开始录音', 'error')
  }
}

async function finishShadow() {
  await patchSession({ stepShadow: true })
  step.value = 3
}

async function saveRetell() {
  await patchSession({
    retellText: retellText.value,
    stepRetell: true,
  })
  showToast('置换完成', 'success')
  step.value = 4
}

async function reviewExpr(id: string, result: 'again' | 'good') {
  const res = await api.reviewTvExpression(id, result)
  if (res.code === 0) showToast(result === 'good' ? '已排期' : '明天再练', 'success')
  else showToast(res.message || '操作失败', 'error')
}

async function finishReview() {
  await patchSession({ stepReview: true })
  showToast('本场景今日完成', 'success')
  api.addEnglishLog({
    logType: 'speaking',
    refId: sceneId,
    durationSec: 300,
    sentencesPracticed: scene.value?.lines.length || 0,
    note: 'tv-scene',
  }).catch(() => {})
}

async function reloadScene() {
  const res = await api.getTvScene(sceneId)
  if (res.code === 0 && res.data) {
    scene.value = res.data
    syncEditLines()
  }
}

async function load() {
  if (!sceneId) {
    showToast('缺少场景 id', 'error')
    return
  }
  loading.value = true
  try {
    const [sc, sess] = await Promise.all([
      api.getTvScene(sceneId),
      api.getTvSession(sceneId),
    ])
    if (sc.code === 0 && sc.data) {
      scene.value = sc.data
      Taro.setNavigationBarTitle({ title: sc.data.title || '场景精学' })
      syncEditLines()
    } else {
      showToast(sc.message || '加载失败', 'error')
    }
    if (sess.code === 0 && sess.data) {
      session.value = sess.data
      blindNote.value = sess.data.blindNote || ''
      retellText.value = sess.data.retellText || ''
      const flags = [
        sess.data.stepBlind,
        sess.data.stepParse,
        sess.data.stepShadow,
        sess.data.stepRetell,
        sess.data.stepReview,
      ]
      const first = flags.findIndex((f) => !f)
      step.value = first >= 0 ? first : 4
    }
  } finally {
    loading.value = false
  }
}

onMounted(load)
useDidShow(load)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-study {
  @include page-padding;
  padding-bottom: 48px;
}

.head {
  margin-bottom: 12px;
  .title { display: block; font-size: 18px; font-weight: 700; color: $text-primary; }
  .meta { display: block; font-size: 12px; color: $text-muted; margin-top: 4px; }
  .summary { display: block; font-size: 13px; color: $text-secondary; margin-top: 6px; line-height: 1.45; }
}

.steps {
  display: flex;
  gap: 6px;
  margin-bottom: 14px;
  .step-dot {
    @include hit-target(44px);
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: $page-bg;
    color: $text-muted;
    font-size: 14px;
    font-weight: 600;
    &.on { background: $primary-color; color: $on-primary; }
    &.done { background: rgba(61, 186, 128, 0.18); color: var(--zk-success); }
    &.on.done { background: $primary-color; color: $on-primary; }
    &.locked { opacity: 0.45; }
  }
}

.panel {
  @include card;
  padding: 14px;
  border-radius: $radius-lg;
}
.panel-title { display: block; font-size: 16px; font-weight: 700; color: $text-primary; }
.panel-desc { display: block; font-size: 12px; color: $text-muted; margin: 6px 0 12px; line-height: 1.5; }

.btn-row {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 14px;
  &.top { justify-content: flex-start; margin-top: 0; margin-bottom: 10px; }
}

.line-card {
  border: 1px solid $border-color;
  border-radius: $radius-md;
  padding: 10px;
  margin-bottom: 10px;
  .line-head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }
  .speaker-input { flex: 1; }
  .line-del { @include hit-target(44px); font-size: 13px; color: $text-muted; flex-shrink: 0; }
  .gen { display: block; font-size: 13px; color: $primary-color; margin-top: 8px; }
}

.expr-form {
  border: 1px solid $primary-color;
  border-radius: $radius-md;
  padding: 12px;
  margin-bottom: 12px;
  background: $primary-light;
  .expr-form-title {
    display: block;
    font-size: 14px;
    font-weight: 600;
    color: $primary-color;
    margin-bottom: 4px;
  }
  .form-label {
    display: block;
    font-size: 12px;
    color: $text-muted;
    margin: 8px 0 4px;
  }
}

.expr-mini {
  margin-top: 8px;
  .sub { display: block; font-size: 12px; color: $text-muted; margin-bottom: 6px; }
  .expr-chip {
    padding: 8px 0;
    border-bottom: 1px solid $border-color;
  }
  .chip-phrase { display: block; font-size: 13px; color: $text-primary; font-weight: 600; }
  .chip-meaning { display: block; font-size: 12px; color: $text-muted; margin-top: 2px; }
}

.shadow-card {
  border-bottom: 1px solid $border-color;
  padding: 10px 0;
  .shadow-en { display: block; font-size: 14px; color: $text-primary; line-height: 1.45; }
  .shadow-zh { display: block; font-size: 12px; color: $text-muted; margin-top: 4px; }
  .shadow-acts { display: flex; gap: 4px; margin-top: 4px; flex-wrap: wrap; }
  .act { @include list-act; }
}

.review-card {
  border-bottom: 1px solid $border-color;
  padding: 10px 0;
  .r-phrase { display: block; font-size: 15px; font-weight: 600; color: $text-primary; }
  .r-meaning { display: block; font-size: 12px; color: $text-muted; margin-top: 4px; }
  .r-acts { display: flex; gap: 4px; margin-top: 4px; flex-wrap: wrap; }
  .act { @include list-act; color: $text-muted; &.good { color: $primary-color; } }
}

.hint { font-size: 13px; color: $text-muted; padding: 12px 0; }
.empty { text-align: center; padding: 40px; color: $text-muted; }
</style>
