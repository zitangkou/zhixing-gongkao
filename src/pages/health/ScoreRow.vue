<template>
  <view class="score-row">
    <view class="head">
      <text class="label">{{ label }}</text>
      <text v-if="tip" class="tip">{{ tip }}</text>
      <text class="val">{{ displayVal }}</text>
    </view>
    <view class="nums">
      <text
        v-for="n in max"
        :key="n"
        class="n"
        :class="{ on: modelValue === n }"
        @tap="$emit('update:modelValue', n)"
      >{{ n }}</text>
    </view>
    <view class="scale">
      <text class="scale-end">1 {{ lowLabel }}</text>
      <text class="scale-mid">{{ scaleMid }}</text>
      <text class="scale-end">{{ max }} {{ highLabel }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    label: string
    modelValue: number
    max?: number
    tip?: string
    /** higher-better：分数越高越好（心情/能量）；higher-worse：越高越重（焦虑/皮肤） */
    polarity?: 'higher-better' | 'higher-worse'
    lowLabel?: string
    highLabel?: string
  }>(),
  {
    max: 10,
    polarity: 'higher-worse',
  },
)

defineEmits<{ 'update:modelValue': [number] }>()

const lowLabel = computed(() => {
  if (props.lowLabel) return props.lowLabel
  return props.polarity === 'higher-better' ? '很差' : '很轻'
})

const highLabel = computed(() => {
  if (props.highLabel) return props.highLabel
  return props.polarity === 'higher-better' ? '很好' : '很重'
})

const scaleMid = computed(() =>
  props.polarity === 'higher-better' ? '← 越低越差 · 越高越好 →' : '← 越轻 · 越重 →',
)

/** 当前分对应的程度词 */
const LEVEL_BETTER_10 = ['', '很差', '差', '偏差', '略差', '一般', '尚可', '较好', '好', '很好', '极好']
const LEVEL_WORSE_10 = ['', '很轻', '轻', '偏轻', '略轻', '中等', '偏重', '较重', '重', '很重', '极重']
const LEVEL_BETTER_5 = ['', '很差', '偏差', '一般', '较好', '很好']
const LEVEL_WORSE_5 = ['', '很轻', '轻', '中等', '较重', '很重']

const levelWord = computed(() => {
  const n = props.modelValue
  if (!n) return ''
  if (props.max === 5) {
    const table = props.polarity === 'higher-better' ? LEVEL_BETTER_5 : LEVEL_WORSE_5
    return table[n] || ''
  }
  const table = props.polarity === 'higher-better' ? LEVEL_BETTER_10 : LEVEL_WORSE_10
  return table[n] || ''
})

const displayVal = computed(() => {
  if (!props.modelValue) return '—'
  return levelWord.value ? `${props.modelValue} · ${levelWord.value}` : String(props.modelValue)
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';
.score-row { margin-bottom: 12px; }
.head { display: flex; align-items: baseline; gap: 6px; margin-bottom: 6px;
  .label { font-size: 12px; color: $text-secondary; flex-shrink: 0; }
  .tip { font-size: 10px; color: $text-muted; flex: 1; min-width: 0; }
  .val { font-size: 12px; font-weight: 700; color: $primary-color; margin-left: auto; flex-shrink: 0; }
}
.nums { display: flex; flex-wrap: wrap; gap: 4px; }
.n {
  @include hit-target(44px);
  width: 44px;
  height: 44px;
  font-size: 12px;
  border-radius: 6px;
  background: $elevated;
  color: $text-secondary;
  &.on { background: $primary-color; color: $on-primary; font-weight: 700; }
}
.scale {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-top: 4px;
  .scale-end { font-size: 10px; color: $text-muted; flex-shrink: 0; }
  .scale-mid { font-size: 9px; color: $text-muted; opacity: 0.85; text-align: center; flex: 1; }
}
</style>
