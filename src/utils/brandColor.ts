import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useSettingsStore } from '@/store/settings'
import { brandPrimary } from '@/constants/theme'

/** 图标 / 组件 props 用的品牌色（跟 --zk-primary 一致，跟随品牌主题） */
export function useBrandColor() {
  const { darkMode, brandTheme } = storeToRefs(useSettingsStore())
  const brandColor = computed(() => brandPrimary(darkMode.value, brandTheme.value))
  const mutedColor = computed(() => (darkMode.value ? '#7C7C84' : '#999999'))
  return { brandColor, mutedColor, darkMode }
}

/** hex 合成 rgba 字符串（供 swiper 指示点等只吃字符串的原生属性） */
export function withAlpha(hex: string, alpha: number): string {
  const h = hex.replace('#', '')
  const full =
    h.length === 3
      ? h
          .split('')
          .map((c) => c + c)
          .join('')
      : h
  const r = parseInt(full.slice(0, 2), 16)
  const g = parseInt(full.slice(2, 4), 16)
  const b = parseInt(full.slice(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}
