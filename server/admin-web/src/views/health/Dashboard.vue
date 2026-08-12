<template>
  <div class="page">
    <div class="toolbar">
      <el-select v-model="selectedUserId" placeholder="选择用户" filterable style="width: 240px" @change="onUserChange">
        <el-option v-for="u in users" :key="u.userId" :label="u.nickname || u.userId" :value="u.userId" />
      </el-select>
      <el-button type="primary" :disabled="!selectedUserId" @click="loadDetail">查看详情</el-button>
    </div>

    <!-- 用户列表 -->
    <ListState v-if="!selectedUserId" :loading="loading" :error="loadError" :has-data="users.length > 0" empty-text="暂无健康计划用户" @retry="loadUsers">
      <el-table :data="users" stripe>
        <el-table-column prop="userId" label="用户 ID" width="160" />
        <el-table-column prop="nickname" label="昵称" width="140" />
        <el-table-column prop="programStartDate" label="计划开始" width="130" />
        <el-table-column prop="privateFocus" label="个人重点" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link size="small" @click="selectedUserId = row.userId; onUserChange()">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </ListState>

    <!-- 用户详情 -->
    <template v-if="selectedUserId && overview">
      <el-descriptions title="健康总览" :column="4" border class="overview-card">
        <el-descriptions-item label="当前周">第 {{ overview.currentWeek }} 周</el-descriptions-item>
        <el-descriptions-item label="阶段">{{ overview.phaseName }}</el-descriptions-item>
        <el-descriptions-item label="身体评分">{{ overview.bodyScore }}</el-descriptions-item>
        <el-descriptions-item label="CBT 评分">{{ overview.cbtScore }}</el-descriptions-item>
        <el-descriptions-item label="连续打卡">{{ overview.streak }} 天</el-descriptions-item>
        <el-descriptions-item label="累计天数">{{ overview.totalDays }} 天</el-descriptions-item>
      </el-descriptions>

      <h4 style="margin: 16px 0 8px">近期打卡记录</h4>
      <el-table :data="dailyLogs" stripe max-height="400">
        <el-table-column prop="logDate" label="日期" width="120" />
        <el-table-column prop="sleepHours" label="睡眠(h)" width="90" />
        <el-table-column prop="sleepQuality" label="睡眠质量" width="90" />
        <el-table-column prop="exerciseMinutes" label="运动(min)" width="100" />
        <el-table-column prop="exerciseType" label="运动类型" width="110" />
        <el-table-column label="CBT" width="70">
          <template #default="{ row }">
            <el-tag :type="row.cbtDone ? 'success' : 'info'" size="small">{{ row.cbtDone ? '✓' : '—' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ruminationLevel" label="反刍" width="70" />
        <el-table-column prop="bodyScore" label="身体分" width="80" />
        <el-table-column prop="cbtScore" label="CBT分" width="80" />
        <el-table-column prop="note" label="备注" min-width="160" show-overflow-tooltip />
      </el-table>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getHealthDaily, getHealthOverview, listHealthUsers } from '@/api/health'
import type { HealthDailyLog, HealthOverview, HealthUser } from '@/api/health'
import ListState from '@/components/ListState.vue'
import { useAdminList } from '@/composables/useAdminList'

const { loading, loadError, runLoad } = useAdminList()
const users = ref<HealthUser[]>([])
const selectedUserId = ref('')
const overview = ref<HealthOverview | null>(null)
const dailyLogs = ref<HealthDailyLog[]>([])

async function loadUsers() {
  await runLoad(async () => {
    users.value = await listHealthUsers()
  })
}

async function onUserChange() {
  overview.value = null
  dailyLogs.value = []
  if (selectedUserId.value) await loadDetail()
}

async function loadDetail() {
  if (!selectedUserId.value) return
  const [ov, logs] = await Promise.all([
    getHealthOverview(selectedUserId.value),
    getHealthDaily(selectedUserId.value),
  ])
  overview.value = ov
  dailyLogs.value = logs
}

onMounted(loadUsers)
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.overview-card {
  margin-bottom: 8px;
}
</style>
