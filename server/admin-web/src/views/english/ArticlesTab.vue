<template>
  <div>
    <div class="toolbar">
      <el-button type="primary" @click="openDialog()">新建文章</el-button>
      <el-button @click="load">刷新</el-button>
    </div>

    <ListState
      :loading="loading"
      :error="loadError"
      :has-data="articles.length > 0"
      empty-text="暂无英文文章，点击「新建文章」开始"
      @retry="load"
    >
      <template #empty-action>
        <el-button type="primary" @click="openDialog()">新建文章</el-button>
      </template>
      <el-table :data="articles" v-loading="loading && articles.length > 0" row-key="id">
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column prop="source" label="来源" width="120" />
      <el-table-column prop="level" label="级别" width="70" />
      <el-table-column label="生词数" width="80">
        <template #default="{ row }">{{ row.vocabHighlights?.length || 0 }}</template>
      </el-table-column>
      <el-table-column prop="readCount" label="阅读数" width="80" />
      <el-table-column label="发布" width="70">
        <template #default="{ row }">
          <el-switch v-model="row.isPublished" @change="onToggle(row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button link type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    </ListState>

    <el-dialog v-model="visible" :title="editId ? '编辑文章' : '新建文章'" width="720px">
      <el-form label-width="90px">
        <el-form-item label="标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="form.source" placeholder="BBC / VOA / China Daily" />
        </el-form-item>
        <el-form-item label="级别">
          <el-select v-model="form.level">
            <el-option value="A2" label="A2" />
            <el-option value="B1" label="B1" />
            <el-option value="B2" label="B2" />
            <el-option value="C1" label="C1" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-rate v-model="form.difficulty" :max="5" />
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="form.tags" multiple allow-create filterable default-first-option />
        </el-form-item>
        <el-form-item label="正文">
          <el-input v-model="form.content" type="textarea" :rows="8" />
        </el-form-item>
        <el-form-item label="生词高亮">
          <div v-for="(v, i) in form.vocabHighlights" :key="i" class="vocab-row">
            <el-input v-model="v.word" placeholder="word" style="width: 120px" />
            <el-input v-model="v.pos" placeholder="词性" style="width: 80px" />
            <el-input v-model="v.meaning" placeholder="中文释义" style="width: 180px" />
            <el-input v-model="v.sentence" placeholder="例句" style="flex: 1" />
            <el-button link type="danger" @click="form.vocabHighlights.splice(i, 1)">删</el-button>
          </div>
          <el-button size="small" @click="form.vocabHighlights.push({ word: '', pos: '', meaning: '', sentence: '' })">+ 添加生词</el-button>
        </el-form-item>
        <el-form-item label="发布">
          <el-switch v-model="form.isPublished" />
        </el-form-item>
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
import { createEnglishArticle, deleteEnglishArticle, fetchEnglishArticles, updateEnglishArticle } from '@/api/english'
import ListState from '@/components/ListState.vue'
import { useAdminList } from '@/composables/useAdminList'

const { loading, loadError, runLoad } = useAdminList()
const saving = ref(false)
const articles = ref<any[]>([])
const visible = ref(false)
const editId = ref<string | null>(null)
const form = reactive({
  title: '', source: '', level: 'B1', content: '', tags: [] as string[],
  difficulty: 3, isPublished: true, vocabHighlights: [] as { word: string; pos: string; meaning: string; sentence: string }[],
})

async function load() {
  await runLoad(async () => {
    articles.value = await fetchEnglishArticles()
  })
}

function openDialog(row?: any) {
  if (row) {
    editId.value = row.id
    form.title = row.title; form.source = row.source; form.level = row.level
    form.content = row.content; form.tags = [...(row.tags || [])]
    form.difficulty = row.difficulty; form.isPublished = row.isPublished
    form.vocabHighlights = (row.vocabHighlights || []).map((v: any) => ({ ...v }))
  } else {
    editId.value = null
    form.title = ''; form.source = ''; form.level = 'B1'; form.content = ''
    form.tags = []; form.difficulty = 3; form.isPublished = true; form.vocabHighlights = []
  }
  visible.value = true
}

async function save() {
  if (!form.title.trim()) { ElMessage.warning('请输入标题'); return }
  saving.value = true
  try {
    const data = { ...form, vocabHighlights: form.vocabHighlights.filter((v) => v.word.trim()) }
    if (editId.value) {
      await updateEnglishArticle(editId.value, data)
      ElMessage.success('已保存')
    } else {
      await createEnglishArticle(data)
      ElMessage.success('已创建')
    }
    visible.value = false
    await load()
  } catch (e) { ElMessage.error(e instanceof Error ? e.message : '保存失败') } finally { saving.value = false }
}

async function onToggle(row: any) {
  try { await updateEnglishArticle(row.id, { isPublished: row.isPublished }) } catch { row.isPublished = !row.isPublished }
}

async function onDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.title}」？`, '提示', { type: 'warning' })
    await deleteEnglishArticle(row.id)
    await load()
    ElMessage.success('已删除')
  } catch (e) { if (e !== 'cancel' && e !== 'close') ElMessage.error('删除失败') }
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.vocab-row { display: flex; gap: 6px; margin-bottom: 6px; align-items: center; }
</style>
