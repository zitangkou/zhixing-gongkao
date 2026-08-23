<template>
  <PageShell title="账号内容运营">
    <template #extra>
      <el-button v-if="canWrite" type="primary" @click="openCreate">新建发布包</el-button>
      <el-button @click="loadAll">刷新</el-button>
    </template>

    <el-alert type="info" :closable="false" class="intro">
      从已审核教学母资产派生渠道内容。发布包必须依次经过教研审核、运营审核和待发布状态；首期导出后人工发布。
    </el-alert>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="发布包" name="packages">
        <div class="toolbar">
          <el-select v-model="filters.productKey" clearable placeholder="全部产品" style="width: 150px" @change="loadPackages">
            <el-option label="申论" value="shenlun" />
            <el-option label="政治理论" value="theory" />
          </el-select>
          <el-select v-model="filters.status" clearable placeholder="全部状态" style="width: 160px" @change="loadPackages">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
        <ListState :loading="loading" :error="loadError" :has-data="packages.length > 0" empty-text="暂无发布包" @retry="loadPackages">
          <el-table :data="packages" row-key="id">
            <el-table-column label="母资产" min-width="220">
              <template #default="{ row }">
                <div class="strong">{{ row.sourceTitle || row.sourceId }}</div>
                <div class="muted">{{ row.sourceType }} · {{ templateName(row.templateId) }}</div>
              </template>
            </el-table-column>
            <el-table-column label="产品" width="100">
              <template #default="{ row }">{{ productLabel(row.productKey) }}</template>
            </el-table-column>
            <el-table-column label="渠道" min-width="190">
              <template #default="{ row }">
                <el-tag v-for="channel in Object.keys(row.variants)" :key="channel" size="small" class="channel-tag">
                  {{ channelLabel(channel) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="排期" width="170">
              <template #default="{ row }">{{ formatTime(row.plannedAt) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }"><el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag></template>
            </el-table-column>
            <el-table-column label="操作" width="230" fixed="right">
              <template #default="{ row }">
                <el-button v-if="canEdit(row)" link type="primary" @click="openEdit(row)">编辑</el-button>
                <el-button v-if="canWrite && nextStatus(row.status)" link type="success" @click="advance(row)">
                  {{ nextAction(row.status) }}
                </el-button>
                <el-button v-if="canWrite && canReject(row.status)" link type="danger" @click="reject(row)">驳回</el-button>
              </template>
            </el-table-column>
          </el-table>
        </ListState>
      </el-tab-pane>

      <el-tab-pane label="固定栏目模板" name="templates">
        <div class="template-grid">
          <el-card v-for="item in templates" :key="item.id" shadow="never" class="template-card">
            <div class="template-head">
              <div>
                <div class="template-name">{{ item.name }}</div>
                <div class="muted">{{ productLabel(item.productKey) }} · {{ item.code }}</div>
              </div>
              <el-tag size="small">{{ item.slots.length }} 个槽位</el-tag>
            </div>
            <p>{{ item.description }}</p>
            <div class="slot-row"><span v-for="slot in item.slots" :key="slot">{{ slot }}</span></div>
            <div class="channel-row">{{ item.channels.map(channelLabel).join(' / ') }}</div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑发布包' : '新建发布包'" width="760px" destroy-on-close>
      <el-form label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="产品">
              <el-select v-model="form.productKey" :disabled="!!editingId" style="width: 100%" @change="onProductChange">
                <el-option label="申论" value="shenlun" /><el-option label="政治理论" value="theory" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="栏目模板">
              <el-select v-model="form.templateId" :disabled="!!editingId" style="width: 100%" @change="onTemplateChange">
                <el-option v-for="item in availableTemplates" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8"><el-form-item label="母资产类型"><el-input v-model="form.sourceType" :disabled="!!editingId" placeholder="daily_task" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="母资产 ID"><el-input v-model="form.sourceId" :disabled="!!editingId" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="母资产标题"><el-input v-model="form.sourceTitle" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="小程序深链"><el-input v-model="form.deepLink" placeholder="/pages/...?...&channel=xiaohongshu" /></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="活动标识"><el-input v-model="form.campaignKey" placeholder="栏目-日期-批次" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="计划发布时间"><el-date-picker v-model="form.plannedAt" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="目标渠道">
          <el-checkbox-group v-model="selectedChannels">
            <el-checkbox v-for="channel in currentTemplate?.channels || []" :key="channel" :value="channel">{{ channelLabel(channel) }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-tabs v-if="selectedChannels.length" type="border-card">
          <el-tab-pane v-for="channel in selectedChannels" :key="channel" :label="channelLabel(channel)">
            <el-form-item label="渠道标题"><el-input v-model="variantForms[channel].title" /></el-form-item>
            <el-form-item label="渠道正文"><el-input v-model="variantForms[channel].body" type="textarea" :rows="5" /></el-form-item>
          </el-tab-pane>
        </el-tabs>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="savePackage">保存草稿</el-button>
      </template>
    </el-dialog>
  </PageShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageShell from '@/components/PageShell.vue'
import ListState from '@/components/ListState.vue'
import { useAdminList } from '@/composables/useAdminList'
import { useAuthStore } from '@/stores/auth'
import {
  createContentPackage, fetchContentPackages, fetchContentTemplates, updateContentPackage,
  updateContentPackageStatus, type ContentOpsStatus, type ContentOpsTemplate, type ContentPackage,
} from '@/api/contentOps'

const auth = useAuthStore()
const canWrite = computed(() => auth.hasPermission('content_ops:write'))
const { loading, loadError, runLoad } = useAdminList()
const activeTab = ref('packages')
const templates = ref<ContentOpsTemplate[]>([])
const packages = ref<ContentPackage[]>([])
const filters = reactive({ productKey: '', status: '' })
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref('')
const selectedChannels = ref<string[]>([])
const variantForms = reactive<Record<string, { title: string; body: string }>>({})
const form = reactive({ productKey: 'shenlun', templateId: '', sourceType: 'daily_task', sourceId: '', sourceTitle: '', campaignKey: '', deepLink: '', plannedAt: '' })
const statusOptions = [
  ['draft', '草稿'], ['teaching_review', '教研审核'], ['ops_review', '运营审核'],
  ['ready', '待发布'], ['published', '已发布'], ['rejected', '已驳回'],
].map(([value, label]) => ({ value, label }))
const availableTemplates = computed(() => templates.value.filter((item) => item.productKey === form.productKey || item.productKey === 'general'))
const currentTemplate = computed(() => templates.value.find((item) => item.id === form.templateId))

const productLabel = (key: string) => ({ shenlun: '申论', theory: '政治理论', general: '通用' }[key] || key)
const channelLabel = (key: string) => ({ xiaohongshu: '小红书', douyin: '抖音', bilibili: 'B站', wechat: '公众号' }[key] || key)
const statusLabel = (key: string) => statusOptions.find((item) => item.value === key)?.label || key
const statusType = (status: string) => status === 'published' ? 'success' : status === 'rejected' ? 'danger' : status === 'ready' ? 'warning' : 'info'
const templateName = (id: string) => templates.value.find((item) => item.id === id)?.name || id
const formatTime = (value?: string) => value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '未排期'
const nextStatusMap: Record<ContentOpsStatus, ContentOpsStatus | null> = { draft: 'teaching_review', teaching_review: 'ops_review', ops_review: 'ready', ready: 'published', rejected: 'draft', published: null }
const nextActionLabels: Partial<Record<ContentOpsStatus, string>> = { draft: '送教研', teaching_review: '教研通过', ops_review: '运营通过', ready: '确认发布', rejected: '退回草稿' }
const nextStatus = (status: ContentOpsStatus) => nextStatusMap[status]
const nextAction = (status: ContentOpsStatus) => nextActionLabels[status] || ''
const canReject = (status: ContentOpsStatus) => ['teaching_review', 'ops_review', 'ready'].includes(status)
const canEdit = (row: ContentPackage) => canWrite.value && ['draft', 'rejected'].includes(row.status)

async function loadTemplates() { templates.value = await fetchContentTemplates() }
async function loadPackages() { await runLoad(async () => { packages.value = await fetchContentPackages({ productKey: filters.productKey || undefined, status: filters.status || undefined }) }) }
async function loadAll() { await Promise.all([loadTemplates(), loadPackages()]) }

function initVariant(channel: string, value?: { title?: string; body?: string }) {
  variantForms[channel] = { title: value?.title || '', body: value?.body || '' }
}
function onProductChange() { form.templateId = availableTemplates.value[0]?.id || ''; onTemplateChange() }
function onTemplateChange() {
  selectedChannels.value = [...(currentTemplate.value?.channels || [])]
  selectedChannels.value.forEach((channel) => initVariant(channel, variantForms[channel]))
}
function resetForm() {
  editingId.value = ''; Object.assign(form, { productKey: 'shenlun', templateId: '', sourceType: 'daily_task', sourceId: '', sourceTitle: '', campaignKey: '', deepLink: '', plannedAt: '' })
  onProductChange()
}
function openCreate() { resetForm(); dialogVisible.value = true }
function openEdit(row: ContentPackage) {
  editingId.value = row.id
  Object.assign(form, { productKey: row.productKey, templateId: row.templateId, sourceType: row.sourceType, sourceId: row.sourceId, sourceTitle: row.sourceTitle, campaignKey: row.campaignKey, deepLink: row.deepLink, plannedAt: row.plannedAt || '' })
  selectedChannels.value = Object.keys(row.variants)
  selectedChannels.value.forEach((channel) => initVariant(channel, row.variants[channel]))
  dialogVisible.value = true
}
async function savePackage() {
  if (!form.templateId || !form.sourceId.trim() || !selectedChannels.value.length) { ElMessage.warning('请补齐模板、母资产和至少一个渠道'); return }
  const variants = Object.fromEntries(selectedChannels.value.map((channel) => [channel, { ...variantForms[channel] }]))
  saving.value = true
  try {
    const common = { sourceTitle: form.sourceTitle, campaignKey: form.campaignKey, deepLink: form.deepLink, plannedAt: form.plannedAt || null, variants }
    if (editingId.value) await updateContentPackage(editingId.value, common)
    else await createContentPackage({ ...common, productKey: form.productKey, templateId: form.templateId, sourceType: form.sourceType, sourceId: form.sourceId })
    dialogVisible.value = false; await loadPackages(); ElMessage.success('发布包草稿已保存')
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '保存失败') } finally { saving.value = false }
}
async function advance(row: ContentPackage) {
  const target = nextStatus(row.status); if (!target) return
  try {
    if (target === 'published') await ElMessageBox.confirm('确认已人工发布到对应平台？', '确认发布', { type: 'warning' })
    await updateContentPackageStatus(row.id, target); await loadPackages(); ElMessage.success(nextAction(row.status))
  } catch (error) { if (error !== 'cancel' && error !== 'close') ElMessage.error(error instanceof Error ? error.message : '操作失败') }
}
async function reject(row: ContentPackage) {
  try {
    const result = await ElMessageBox.prompt('请填写明确的驳回原因', '驳回发布包', { inputValidator: (value) => !!value.trim() || '驳回原因不能为空' })
    await updateContentPackageStatus(row.id, 'rejected', result.value); await loadPackages(); ElMessage.success('已驳回')
  } catch (error) { if (error !== 'cancel' && error !== 'close') ElMessage.error(error instanceof Error ? error.message : '操作失败') }
}
onMounted(loadAll)
</script>

<style scoped>
.intro { margin-bottom: 14px; }
.strong { font-weight: 600; line-height: 1.5; }
.muted { color: #909399; font-size: 12px; margin-top: 3px; }
.channel-tag { margin: 2px 5px 2px 0; }
.template-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 14px; }
.template-card { border-color: #e8e8e8; }
.template-head { display: flex; justify-content: space-between; gap: 12px; }
.template-name { font-size: 16px; font-weight: 650; }
.template-card p { color: #606266; font-size: 13px; line-height: 1.6; min-height: 42px; }
.slot-row { display: flex; flex-wrap: wrap; gap: 6px; }
.slot-row span { padding: 3px 8px; border-radius: 5px; background: #f2f4f7; color: #606266; font-size: 12px; }
.channel-row { margin-top: 12px; color: #909399; font-size: 12px; }
</style>
