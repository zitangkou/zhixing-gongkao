<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="filters.userId" placeholder="用户 ID" clearable style="width: 180px" @clear="load" @keyup.enter="load" />
      <el-select v-model="filters.status" placeholder="状态" clearable style="width: 130px" @change="load">
        <el-option label="在读" value="reading" />
        <el-option label="已读完" value="finished" />
        <el-option label="想读" value="wishlist" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="书架" name="books">
        <ListState :loading="loading" :error="loadError" :has-data="books.length > 0" empty-text="暂无书籍" @retry="load">
          <el-table :data="books" stripe>
            <el-table-column prop="title" label="书名" min-width="180" show-overflow-tooltip />
            <el-table-column prop="author" label="作者" width="120" />
            <el-table-column prop="category" label="分类" width="100" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status === 'finished' ? 'success' : row.status === 'reading' ? '' : 'info'" size="small">
                  {{ ({ reading: '在读', finished: '已读完', wishlist: '想读' } as Record<string, string>)[row.status] || row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="currentChapter" label="当前章节" width="140" show-overflow-tooltip />
            <el-table-column prop="createdAt" label="添加时间" width="170" :formatter="(row: DushuBook) => (row.createdAt || '').slice(0, 16).replace('T', ' ')" />
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button link size="small" @click="openEdit(row)">编辑</el-button>
                <el-popconfirm title="删除书籍将同时删除关联的日志、人物卡和总结，确定？" @confirm="onDelete(row.id)">
                  <template #reference>
                    <el-button link size="small" type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </ListState>
      </el-tab-pane>

      <el-tab-pane label="每日输出卡" name="daily">
        <el-alert v-if="!filters.userId" type="info" :closable="false" style="margin-bottom: 12px">
          请先在上方输入用户 ID 后查询
        </el-alert>
        <el-table v-else :data="dailyLogs" stripe>
          <el-table-column prop="logDate" label="日期" width="120" />
          <el-table-column prop="bookTitle" label="书名" width="160" show-overflow-tooltip />
          <el-table-column prop="chapter" label="章节" width="140" show-overflow-tooltip />
          <el-table-column prop="outputCard" label="输出卡" min-width="260" show-overflow-tooltip />
          <el-table-column prop="reflection" label="反思" min-width="200" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="人物卡" name="persons">
        <el-alert v-if="!filters.userId" type="info" :closable="false" style="margin-bottom: 12px">
          请先在上方输入用户 ID 后查询
        </el-alert>
        <el-table v-else :data="persons" stripe>
          <el-table-column prop="name" label="人物" width="120" />
          <el-table-column prop="era" label="时代" width="100" />
          <el-table-column prop="role" label="角色" width="120" />
          <el-table-column prop="bookTitle" label="出处" width="160" show-overflow-tooltip />
          <el-table-column prop="keyEvents" label="关键事件" min-width="240" show-overflow-tooltip />
          <el-table-column prop="evaluation" label="评价" min-width="200" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="一书一页" name="summaries">
        <el-alert v-if="!filters.userId" type="info" :closable="false" style="margin-bottom: 12px">
          请先在上方输入用户 ID 后查询
        </el-alert>
        <el-table v-else :data="summaries" stripe>
          <el-table-column prop="bookTitle" label="书名" width="180" show-overflow-tooltip />
          <el-table-column prop="onePageSummary" label="一页总结" min-width="320" show-overflow-tooltip />
          <el-table-column prop="updatedAt" label="更新时间" width="170" :formatter="(row: DushuBookSummary) => (row.updatedAt || '').slice(0, 16).replace('T', ' ')" />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 编辑抽屉 -->
    <el-drawer v-model="drawerVisible" title="编辑书籍" size="400px">
      <el-form v-if="editing" label-position="top">
        <el-form-item label="书名">
          <el-input v-model="editing.title" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="editing.author" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="editing.category" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editing.status" style="width: 100%">
            <el-option label="在读" value="reading" />
            <el-option label="已读完" value="finished" />
            <el-option label="想读" value="wishlist" />
          </el-select>
        </el-form-item>
        <el-form-item label="当前章节">
          <el-input v-model="editing.currentChapter" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSave">保存</el-button>
        </el-form-item>
      </el-form>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  deleteDushuBook,
  listDushuBooks,
  listDushuDaily,
  listDushuPersons,
  listDushuSummaries,
  updateDushuBook,
} from '@/api/dushu'
import type { DushuBook, DushuBookSummary, DushuDailyLog, DushuPersonCard } from '@/api/dushu'
import ListState from '@/components/ListState.vue'
import { useAdminList } from '@/composables/useAdminList'

const { loading, loadError, runLoad } = useAdminList()
const activeTab = ref('books')
const filters = reactive({ userId: '', status: '' })
const books = ref<DushuBook[]>([])
const dailyLogs = ref<DushuDailyLog[]>([])
const persons = ref<DushuPersonCard[]>([])
const summaries = ref<DushuBookSummary[]>([])
const drawerVisible = ref(false)
const editing = ref<DushuBook | null>(null)

async function load() {
  await runLoad(async () => {
    books.value = await listDushuBooks({
      userId: filters.userId || undefined,
      status: filters.status || undefined,
    })
  })
}

async function loadUserTabs() {
  if (!filters.userId) {
    dailyLogs.value = []
    persons.value = []
    summaries.value = []
    return
  }
  const [d, p, s] = await Promise.all([
    listDushuDaily(filters.userId),
    listDushuPersons(filters.userId),
    listDushuSummaries(filters.userId),
  ])
  dailyLogs.value = d
  persons.value = p
  summaries.value = s
}

watch(activeTab, (tab) => {
  if (tab !== 'books' && filters.userId) loadUserTabs()
})

function openEdit(row: DushuBook) {
  editing.value = { ...row }
  drawerVisible.value = true
}

async function onSave() {
  if (!editing.value) return
  await updateDushuBook(editing.value.id, {
    title: editing.value.title,
    author: editing.value.author,
    category: editing.value.category,
    status: editing.value.status,
    current_chapter: editing.value.currentChapter,
  })
  ElMessage.success('已保存')
  drawerVisible.value = false
  load()
}

async function onDelete(id: string) {
  await deleteDushuBook(id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
</style>
