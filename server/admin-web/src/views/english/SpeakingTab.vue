<template>
  <div>
    <el-alert
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 12px"
      title="日常口语已改为「跟读本」：用户在英文文章中收藏句子即可练习。"
      description="本页精品对话课为可选项，非必需维护。优先把精力放在「英文文章」内容上。"
    />
    <div class="toolbar">
      <el-button type="primary" @click="openDialog()">新建课程（可选）</el-button>
      <el-button @click="load">刷新</el-button>
    </div>

    <ListState
      :loading="loading"
      :error="loadError"
      :has-data="lessons.length > 0"
      empty-text="暂无口语课程（可选维护项）"
      @retry="load"
    >
      <template #empty-action>
        <el-button type="primary" @click="openDialog()">新建课程</el-button>
      </template>
      <el-table :data="lessons" v-loading="loading && lessons.length > 0" row-key="id">
      <el-table-column prop="title" label="标题" min-width="180" />
      <el-table-column prop="topic" label="主题" width="100" />
      <el-table-column prop="level" label="级别" width="70" />
      <el-table-column label="对话数" width="80">
        <template #default="{ row }">{{ row.dialogue?.length || 0 }}</template>
      </el-table-column>
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

    <el-dialog v-model="visible" :title="editId ? '编辑课程' : '新建课程'" width="720px">
      <el-form label-width="90px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="主题">
          <el-select v-model="form.topic">
            <el-option value="daily" label="日常" />
            <el-option value="work" label="职场" />
            <el-option value="travel" label="旅行" />
            <el-option value="exam" label="考试" />
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
        <el-form-item label="提示"><el-input v-model="form.tips" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="对话">
          <div v-for="(d, i) in form.dialogue" :key="i" class="dialogue-row">
            <el-input v-model="d.speaker" placeholder="说话人" style="width: 100px" />
            <el-input v-model="d.en" placeholder="English" style="flex: 1" />
            <el-input v-model="d.zh" placeholder="中文" style="flex: 1" />
            <el-button link type="danger" @click="form.dialogue.splice(i, 1)">删</el-button>
          </div>
          <el-button size="small" @click="form.dialogue.push({ speaker: 'A', en: '', zh: '' })">+ 添加对话</el-button>
        </el-form-item>
        <el-form-item label="重点句式">
          <div v-for="(s, i) in form.keySentences" :key="i" class="dialogue-row">
            <el-input v-model="s.en" placeholder="English" style="flex: 1" />
            <el-input v-model="s.zh" placeholder="中文" style="flex: 1" />
            <el-input v-model="s.pattern" placeholder="句式说明" style="width: 160px" />
            <el-button link type="danger" @click="form.keySentences.splice(i, 1)">删</el-button>
          </div>
          <el-button size="small" @click="form.keySentences.push({ en: '', zh: '', pattern: '' })">+ 添加句式</el-button>
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
import { createSpeakingLesson, deleteSpeakingLesson, fetchSpeakingLessons, updateSpeakingLesson } from '@/api/english'
import ListState from '@/components/ListState.vue'
import { useAdminList } from '@/composables/useAdminList'

const { loading, loadError, runLoad } = useAdminList()
const saving = ref(false)
const lessons = ref<any[]>([])
const visible = ref(false)
const editId = ref<string | null>(null)
const form = reactive({
  title: '', topic: 'daily', level: 'B1', tips: '',
  dialogue: [] as { speaker: string; en: string; zh: string }[],
  keySentences: [] as { en: string; zh: string; pattern: string }[],
  isPublished: true,
})

async function load() {
  await runLoad(async () => {
    lessons.value = await fetchSpeakingLessons()
  })
}

function openDialog(row?: any) {
  if (row) {
    editId.value = row.id
    Object.assign(form, {
      title: row.title, topic: row.topic, level: row.level, tips: row.tips,
      dialogue: (row.dialogue || []).map((d: any) => ({ ...d })),
      keySentences: (row.keySentences || []).map((s: any) => ({ ...s })),
      isPublished: row.isPublished,
    })
  } else {
    editId.value = null
    Object.assign(form, { title: '', topic: 'daily', level: 'B1', tips: '', dialogue: [], keySentences: [], isPublished: true })
  }
  visible.value = true
}

async function save() {
  if (!form.title.trim()) { ElMessage.warning('请输入标题'); return }
  saving.value = true
  try {
    const data = { ...form, dialogue: form.dialogue.filter((d) => d.en), keySentences: form.keySentences.filter((s) => s.en) }
    if (editId.value) { await updateSpeakingLesson(editId.value, data); ElMessage.success('已保存') }
    else { await createSpeakingLesson(data); ElMessage.success('已创建') }
    visible.value = false; await load()
  } catch (e) { ElMessage.error(e instanceof Error ? e.message : '保存失败') } finally { saving.value = false }
}

async function onToggle(row: any) {
  try { await updateSpeakingLesson(row.id, { isPublished: row.isPublished }) } catch { row.isPublished = !row.isPublished }
}

async function onDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.title}」？`, '提示', { type: 'warning' })
    await deleteSpeakingLesson(row.id); await load(); ElMessage.success('已删除')
  } catch (e) { if (e !== 'cancel' && e !== 'close') ElMessage.error('删除失败') }
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.dialogue-row { display: flex; gap: 6px; margin-bottom: 6px; align-items: center; }
</style>
