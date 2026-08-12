<template>
  <div>
    <div class="toolbar">
      <el-button @click="load">刷新</el-button>
      <el-button type="warning" @click="onSeed" :loading="seeding">重置默认 48 音标</el-button>
    </div>

    <el-alert type="info" :closable="false" style="margin-bottom: 12px">
      DJ 音标体系共 48 个（12 单元音 + 8 双元音 + 28 辅音），系统启动时会自动初始化。
    </el-alert>

    <ListState
      :loading="loading"
      :error="loadError"
      :has-data="phonetics.length > 0"
      empty-text="暂无音标数据，可点击「重置默认 48 音标」初始化"
      @retry="load"
    >
      <template #empty-action>
        <el-button type="warning" @click="onSeed" :loading="seeding">重置默认 48 音标</el-button>
      </template>
      <el-table :data="phonetics" v-loading="loading && phonetics.length > 0" row-key="id">
      <el-table-column prop="sortOrder" label="序号" width="60" />
      <el-table-column prop="symbol" label="音标" width="80" />
      <el-table-column label="分类" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="catType(row.category)">{{ catLabel(row.category) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="发音说明" min-width="200" />
      <el-table-column label="示例词" width="140">
        <template #default="{ row }">
          {{ (row.exampleWords || []).map((w: any) => w.word).join(', ') }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button link type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    </ListState>

    <el-dialog v-model="visible" :title="editId ? '编辑音标' : '新增音标'" width="560px">
      <el-form label-width="90px">
        <el-form-item label="音标符号"><el-input v-model="form.symbol" placeholder="/iː/" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category">
            <el-option value="unit_vowel" label="单元音" />
            <el-option value="diphthong" label="双元音" />
            <el-option value="consonant" label="辅音" />
          </el-select>
        </el-form-item>
        <el-form-item label="发音说明"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="口型舌位"><el-input v-model="form.mouthShape" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="发音技巧"><el-input v-model="form.tips" /></el-form-item>
        <el-form-item label="示例单词">
          <div v-for="(w, i) in form.exampleWords" :key="i" class="word-row">
            <el-input v-model="w.word" placeholder="word" style="width: 140px" />
            <el-input v-model="w.meaning" placeholder="中文" style="width: 140px" />
            <el-button link type="danger" @click="form.exampleWords.splice(i, 1)">删</el-button>
          </div>
          <el-button size="small" @click="form.exampleWords.push({ word: '', meaning: '' })">+ 添加</el-button>
        </el-form-item>
        <el-form-item label="常见拼写">
          <el-select v-model="form.commonSpellings" multiple allow-create filterable default-first-option />
        </el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sortOrder" :min="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http, { getData } from '@/api/http'
import ListState from '@/components/ListState.vue'
import { useAdminList } from '@/composables/useAdminList'

const { loading, loadError, runLoad } = useAdminList()
const saving = ref(false)
const seeding = ref(false)
const phonetics = ref<any[]>([])
const visible = ref(false)
const editId = ref<string | null>(null)
const form = reactive({
  symbol: '', category: 'consonant', description: '', mouthShape: '', tips: '',
  exampleWords: [] as { word: string; meaning: string }[],
  commonSpellings: [] as string[],
  sortOrder: 0,
})

function catLabel(c: string) {
  return { unit_vowel: '单元音', diphthong: '双元音', consonant: '辅音' }[c] || c
}
function catType(c: string): any {
  return { unit_vowel: 'danger', diphthong: 'warning', consonant: '' }[c] || ''
}

async function load() {
  await runLoad(async () => {
    phonetics.value = await getData<any[]>(http.get('/admin/english/phonetics'))
  })
}

function openDialog(row?: any) {
  if (row) {
    editId.value = row.id
    Object.assign(form, {
      symbol: row.symbol, category: row.category, description: row.description,
      mouthShape: row.mouthShape, tips: row.tips,
      exampleWords: (row.exampleWords || []).map((w: any) => ({ ...w })),
      commonSpellings: [...(row.commonSpellings || [])],
      sortOrder: row.sortOrder,
    })
  } else {
    editId.value = null
    Object.assign(form, { symbol: '', category: 'consonant', description: '', mouthShape: '', tips: '', exampleWords: [], commonSpellings: [], sortOrder: 0 })
  }
  visible.value = true
}

async function save() {
  if (!form.symbol.trim()) { ElMessage.warning('请输入音标符号'); return }
  saving.value = true
  try {
    const data = { ...form, mouthShape: form.mouthShape, exampleWords: form.exampleWords.filter((w) => w.word) }
    if (editId.value) {
      await getData(http.put(`/admin/english/phonetic/${editId.value}`, data))
      ElMessage.success('已保存')
    } else {
      await getData(http.post('/admin/english/phonetic', data))
      ElMessage.success('已创建')
    }
    visible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '保存失败')
  } finally {
    saving.value = false
  }
}

async function onDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.symbol}」？`, '提示', { type: 'warning' })
    await getData(http.delete(`/admin/english/phonetic/${row.id}`))
    await load()
    ElMessage.success('已删除')
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') ElMessage.error('删除失败')
  }
}

async function onSeed() {
  try {
    await ElMessageBox.confirm('将重新写入 48 个默认音标（已有自定义数据不受影响）', '提示')
    seeding.value = true
    await getData(http.post('/admin/english/phonetics/seed'))
    await load()
    ElMessage.success('已重置默认音标')
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') ElMessage.error('操作失败')
  } finally {
    seeding.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.word-row { display: flex; gap: 6px; margin-bottom: 6px; align-items: center; }
</style>
