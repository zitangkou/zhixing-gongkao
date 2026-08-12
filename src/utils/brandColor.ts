import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useSettingsStore } from '@/store/settings'

/** 图标 / 组件 props 用的品牌色（跟 --zk-primary 一致） */
export function useBrandColor() {
  const { darkMode } = storeToRefs(useSettingsStore())
  const brandColor = computed(() => (darkMode.value ? '#3D5A7A' : '#1E3A5F'))
  const mutedColor = computed(() => (darkMode.value ? '#7C7C84' : '#999999'))
  return { brandColor, mutedColor, darkMode }
}
