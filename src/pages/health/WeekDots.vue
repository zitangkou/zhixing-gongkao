<template>
  <view class="week-dots">
    <text class="label">{{ label }}</text>
    <view class="dots">
      <view v-for="p in points" :key="p.date" class="col" :class="{ today: p.isToday }">
        <text class="v">{{ p.value || '' }}</text>
        <view class="bar" :style="{ height: (p.value ? 6 + p.value * 3 : 4) + 'px' }" />
        <text class="d">{{ p.label }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import type { HealthWeekPoint } from '@/types'
defineProps<{ label: string; points: HealthWeekPoint[] }>()
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';
.week-dots { margin-bottom: 14px;
  .label { font-size: 12px; color: $text-secondary; margin-bottom: 6px; display: block; }
  .dots { display: flex; align-items: flex-end; height: 56px; gap: 2px; }
  .col { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end;
    &.today .d { color: $primary-color; font-weight: 700; }
  }
  .v { font-size: 9px; color: $text-muted; height: 12px; }
  .bar { width: 10px; border-radius: 3px; background: $primary-soft; min-height: 4px; }
  .d { font-size: 10px; color: $text-muted; margin-top: 2px; }
}
</style>
