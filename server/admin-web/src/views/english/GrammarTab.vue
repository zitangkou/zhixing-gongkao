<template>
  <div>
    <div class="toolbar">
      <el-button type="primary" @click="openDialog()">新建语法</el-button>
      <el-button @click="load">刷新</el-button>
    </div>

    <ListState
      :loading="loading"
      :error="loadError"
      :has-data="lessons.length > 0"
      empty-text="暂无语法课程，点击「新建语法」开始"
      @retry="load"
    >
      <template #empty-action>
        <el-button type="primary" @click="openDialog()">新建语法</el-button>
      </template>
      <el-table :data="lessons" v-loading="loading && lessons.length > 0" row-key="id">
      <el-table-column prop="title" label="标题" min-width="180" />
      <el-table-column prop="category" label="分类" width="120" />
      <el-table-column prop="level" label="级别" width="70" />
      <el-table-column prop="sortOrder" label="排序" width="70" />
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

    <el-dialog v-model="visible" :title="editId ? '编辑语法' : '新建语法'" width="720px">
      <el-form label-width="90px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" allow-create filterable>
            <el-option value="时态" label="时态" />
            <el-option value="从句" label="从句" />
            <el-option value="虚拟语气" label="虚拟语气" />
            <el-option value="句式" label="句式" />
            <el-option value="词法" label="词法" />
          </el-select>
        </el-form-item>
        <el-form-item label="级别">
          <el-select v-model="form.level">
            <el-option value="A2" label="A2" />
            <el-option value="B1" label="B1" />
            <el-option value="B2" label="B2" />
            <el-option value="C1" label="C1" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sortOrder" :min="0" /></el-form-item>
        <el-form-item label="讲解"><el-input v-model="form.explanation" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="例句">
          <div v-for="(e, i) in form.examples" :key="i" class="ex-row">
            <el-input v-model="e.en" placeholder="English" style="flex: 1" />
            <el-input v-model="e.zh" placeholder="中文" style="flex: 1" />
            <el-button link type="danger" @click="form.examples.splice(i, 1)">删</el-button>
          </div>
          <el-button size="small" @click="form.examples.push({ en: '', zh: '' })">+ 添加例句</el-button>
        </el-form-item>
        <el-form-item label="常见错误">
          <div v-for="(m, i) in form.commonMistakes" :key="i" class="ex-row">
            <el-input v-model="m.wrong" placeholder="错误" style="flex: 1" />
            <el-input v-model="m.correct" placeholder="正确" style="flex: 1" />
            <el-input v-model="m.note" placeholder="说明" style="width: 180px" />
            <el-button link type="danger" @click="form.commonMistakes.splice(i, 1)">删</el-button>
          </div>
          <el-button size="small" @click="form.commonMistakes.push({ wrong: '', correct: '', note: '' })">+ 添加错误</el-button>
        </el-form-item>
        <el-form-item label="发布"><el-switch v-model="form.isPublished" /></el-form-item>
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
import { createGrammarLesson, deleteGrammarLesson, fetchGrammarLessons, updateGrammarLesson } from '@/api/english'
import ListState from '@/components/ListState.vue'
import { useAdminList } from '@/composables/useAdminList'

const { loading, loadError, runLoad } = useAdminList()
const saving = ref(false)
const lessons = ref<any[]>([])
const visible = ref(false)
const editId = ref<string | null>(null)
const form = reactive({
  title: '', category: '时态', level: 'B1', explanation: '', sortOrder: 0, isPublished: true,
  examples: [] as { en: string; zh: string }[],
  commonMistakes: [] as { wrong: string; correct: string; note: string }[],
})

async function load() {
  await runLoad(async () => {
    lessons.value = await fetchGrammarLessons()
  })
}

function openDialog(row?: any) {
  if (row) {
    editId.value = row.id
    Object.assign(form, {
      title: row.title, category: row.category, level: row.level, explanation: row.explanation,
      sortOrder: row.sortOrder, isPublished: row.isPublished,
      examples: (row.examples || []).map((e: any) => ({ ...e })),
      commonMistakes: (row.commonMistakes || []).map((m: any) => ({ ...m })),
    })
  } else {
    editId.value = null
    Object.assign(form, { title: '', category: '时态', level: 'B1', explanation: '', sortOrder: 0, isPublished: true, examples: [], commonMistakes: [] })
  }
  visible.value = true
}

async function save() {
  if (!form.title.trim()) { ElMessage.warning('请输入标题'); return }
  saving.value = true
  try {
    const data = { ...form, examples: form.examples.filter((e) => e.en), commonMistakes: form.commonMistakes.filter((m) => m.wrong) }
    if (editId.value) { await updateGrammarLesson(editId.value, data); ElMessage.success('已保存') }
    else { await createGrammarLesson(data); ElMessage.success('已创建') }
    visible.value = false; await load()
  } catch (e) { ElMessage.error(e instanceof Error ? e.message : '保存失败') } finally { saving.value = false }
}

async function onToggle(row: any) {
  try { await updateGrammarLesson(row.id, { isPublished: row.isPublished }) } catch { row.isPublished = !row.isPublished }
}

async function onDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.title}」？`, '提示', { type: 'warning' })
    await deleteGrammarLesson(row.id); await load(); ElMessage.success('已删除')
  } catch (e) { if (e !== 'cancel' && e !== 'close') ElMessage.error('删除失败') }
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.ex-row { display: flex; gap: 6px; margin-bottom: 6px; align-items: center; }
</style>
