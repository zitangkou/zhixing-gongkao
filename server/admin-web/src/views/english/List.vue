<template>
  <div class="page">
    <el-tabs v-model="activeTab" class="english-tabs">
      <el-tab-pane label="英文文章" name="articles">
        <ArticlesTab />
      </el-tab-pane>
      <el-tab-pane label="口语" name="speaking">
        <SpeakingTab />
      </el-tab-pane>
      <el-tab-pane label="语法" name="grammar">
        <GrammarTab />
      </el-tab-pane>
      <el-tab-pane label="音标管理" name="phonetics">
        <PhoneticsTab />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ArticlesTab from './ArticlesTab.vue'
import SpeakingTab from './SpeakingTab.vue'
import GrammarTab from './GrammarTab.vue'
import PhoneticsTab from './PhoneticsTab.vue'

const activeTab = ref('articles')
</script>

<style scoped>
.english-tabs :deep(.el-tabs__header) {
  margin-bottom: 16px;
}
.english-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
}
.english-tabs :deep(.el-tabs__item) {
  padding: 0 20px;
  height: 40px;
  line-height: 40px;
  font-size: 14px;
}
</style>
