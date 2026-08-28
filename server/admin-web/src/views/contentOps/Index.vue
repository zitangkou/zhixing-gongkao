<template>
  <PageShell title="账号内容运营">
    <template #extra>
      <el-button v-if="canWrite" type="success" @click="openGenerate">从审核文章生成</el-button>
      <el-button v-if="canWrite" type="primary" @click="openCreate">新建发布包</el-button>
      <el-button @click="loadAll">刷新</el-button>
    </template>

    <el-alert type="info" :closable="false" class="intro">
      从已审核教学母资产派生渠道内容。发布包必须依次经过教研审核、运营审核和待发布状态；首期导出后人工发布。
    </el-alert>

    <div v-if="overview" class="metrics-grid">
      <el-card shadow="never" class="metric-card"><div class="metric-value">{{ overview.scheduledCount }}</div><div class="metric-label">未来 7 天已排期</div><div class="metric-note">申论 {{ overview.productMix.shenlun }} · 政治理论 {{ overview.productMix.theory }}</div></el-card>
      <el-card shadow="never" class="metric-card"><div class="metric-value">{{ overview.readyInventory }}</div><div class="metric-label">待发布库存</div><div class="metric-note">已过双审核，可导出发布</div></el-card>
      <el-card shadow="never" class="metric-card"><div class="metric-value">{{ overview.reviewBacklog }}</div><div class="metric-label">审核处理中</div><div class="metric-note">教研审核 + 运营审核</div></el-card>
      <el-card shadow="never" class="metric-card"><div class="metric-value">{{ overview.unplannedDrafts }}</div><div class="metric-label">未排期草稿</div><div class="metric-note">草稿与已驳回内容</div></el-card>
    </div>
    <div v-if="overview?.alerts.length" class="inventory-alerts">
      <el-alert v-for="item in overview.alerts" :key="item.code" :title="item.message" :type="item.level" :closable="false" show-icon />
    </div>

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
            <el-table-column type="expand" width="44">
              <template #default="{ row }">
                <div class="review-history">
                  <div class="review-history-title">双审核记录</div>
                  <el-empty v-if="!row.reviewHistory?.length" description="尚无审核决定" :image-size="48" />
                  <el-timeline v-else>
                    <el-timeline-item v-for="record in row.reviewHistory" :key="record.id" :timestamp="formatTime(record.createdAt)" placement="top">
                      <div class="review-record-head">
                        <el-tag :type="record.decision === 'approved' ? 'success' : 'danger'" size="small">
                          {{ reviewStageLabel(record.stage) }}{{ record.decision === 'approved' ? '通过' : '驳回' }}
                        </el-tag>
                        <span>{{ record.reviewerName || record.reviewerUsername || '未知审核人' }}</span>
                      </div>
                      <div class="review-record-note">{{ record.note }}</div>
                    </el-timeline-item>
                  </el-timeline>
                </div>
              </template>
            </el-table-column>
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
            <el-table-column label="操作" width="280" fixed="right">
              <template #default="{ row }">
                <el-button v-if="canEdit(row)" link type="primary" @click="openEdit(row)">编辑</el-button>
                <el-button v-if="canExport(row)" link type="primary" @click="downloadPackage(row)">导出</el-button>
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

      <el-tab-pane label="人民日报参考库" name="references">
        <el-alert
          v-if="referenceLibrary"
          :title="`资料版本 ${referenceLibrary.updatedAt}：公众号来自知识库原生模板与成稿；小红书按仓库运营规范整理。`"
          type="info"
          :closable="false"
          class="reference-alert"
        />
        <div class="reference-sources" v-if="referenceLibrary">
          <el-tag v-for="source in referenceLibrary.sources" :key="source.path" effect="plain">
            {{ source.label }} · {{ source.path }}
          </el-tag>
        </div>
        <div class="template-grid">
          <el-card v-for="platform in referenceLibrary?.platforms || []" :key="platform.key" shadow="never" class="reference-card">
            <div class="template-head">
              <div>
                <div class="template-name">{{ platform.name }}</div>
                <div class="muted">{{ platform.format }}</div>
              </div>
              <el-tag :type="platform.sourceStatus === 'knowledge_base_verified' ? 'success' : 'warning'" size="small">
                {{ platform.sourceStatusLabel }}
              </el-tag>
            </div>
            <h4>固定结构</h4>
            <ol><li v-for="item in platform.structure" :key="item">{{ item }}</li></ol>
            <h4>交付物</h4>
            <ul><li v-for="item in platform.deliverables" :key="item">{{ item }}</li></ul>
            <div class="reference-example">
              <div class="strong">示例：{{ platform.example.title }}</div>
              <p>{{ platform.example.hook }}</p>
              <div v-for="item in platform.example.sections" :key="item" class="example-line">{{ item }}</div>
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <el-tab-pane label="排期日历" name="schedule">
        <el-alert v-if="!scheduledPackages.length" title="暂无已排期内容，可在发布包草稿中设置计划发布时间" type="warning" :closable="false" />
        <el-calendar v-else v-model="calendarMonth" class="schedule-calendar">
          <template #date-cell="{ data }">
            <div class="calendar-day">{{ Number(data.day.slice(-2)) }}</div>
            <button
              v-for="item in packagesForDay(data.day)"
              :key="item.id"
              class="calendar-item"
              type="button"
              :disabled="!canExport(item)"
              :title="`${item.sourceTitle || item.sourceId} · ${statusLabel(item.status)}`"
              @click.stop="downloadPackage(item)"
            >
              <span>{{ plannedTime(item.plannedAt) }}</span>{{ item.sourceTitle || item.sourceId }}
            </button>
          </template>
        </el-calendar>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="generateVisible" title="从审核文章生成发布包" width="620px" destroy-on-close>
      <el-alert title="系统只填充能从原文确定的槽位；其余字段会留空，补齐后才能送教研。" type="info" :closable="false" class="generate-tip" />
      <el-form label-width="110px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="产品">
              <el-select v-model="generateForm.productKey" style="width: 100%" @change="onGenerateProductChange">
                <el-option label="申论" value="shenlun" /><el-option label="政治理论" value="theory" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="栏目模板">
              <el-select v-model="generateForm.templateId" style="width: 100%">
                <el-option v-for="item in generateTemplates" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="审核文章">
          <el-select v-model="generateForm.articleId" filterable style="width: 100%" placeholder="选择已发布文章">
            <el-option v-for="article in publishedArticles" :key="article.id" :label="article.title" :value="article.id">
              <span>{{ article.title }}</span><span class="option-meta">{{ article.source }} · {{ article.publishDate }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="小程序深链"><el-input v-model="generateForm.deepLink" placeholder="系统会自动附加渠道归因参数" /></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="活动标识"><el-input v-model="generateForm.campaignKey" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="计划发布时间"><el-date-picker v-model="generateForm.plannedAt" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="generateVisible = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="generateFromArticle">生成并继续编辑</el-button>
      </template>
    </el-dialog>

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
        <el-divider content-position="left">栏目结构化槽位</el-divider>
        <el-form-item v-for="slot in currentTemplate?.slots || []" :key="slot" :label="slot">
          <el-input v-model="slotForms[slot]" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }" :placeholder="`填写${slot}`" />
        </el-form-item>
        <el-divider content-position="left">渠道变体</el-divider>
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

    <el-dialog v-model="reviewVisible" :title="`${currentReviewConfig?.label || ''}确认`" width="620px" destroy-on-close>
      <el-alert
        :title="reviewStage === 'teaching' ? '教研通过后结构化事实字段将锁定；如需修改必须驳回草稿。' : '运营审核只调整渠道表达，不得改变教研已确认的事实。'"
        type="warning"
        :closable="false"
        class="review-tip"
      />
      <div class="review-target">{{ reviewRow?.sourceTitle }}</div>
      <el-checkbox-group v-model="reviewChecked" class="review-checklist">
        <el-checkbox v-for="item in currentReviewConfig?.checklist || []" :key="item.key" :value="item.key">
          {{ item.label }}
        </el-checkbox>
      </el-checkbox-group>
      <el-input v-model="reviewNote" type="textarea" :rows="4" placeholder="填写具名审核意见（必填）" />
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button type="primary" :loading="reviewSubmitting" @click="submitReview">确认通过</el-button>
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
import { fetchArticles } from '@/api/articles'
import type { Article } from '@/types'
import {
  createContentPackage, exportContentPackage, fetchContentOpsOverview, fetchContentPackages, fetchContentReferenceLibrary, fetchContentReviewConfig, fetchContentTemplates, generateContentPackageFromArticle, updateContentPackage,
  updateContentPackageStatus, type ContentOpsOverview, type ContentOpsStatus, type ContentOpsTemplate, type ContentPackage, type ContentReferenceLibrary, type ReviewStage, type ReviewStageConfig,
} from '@/api/contentOps'

const auth = useAuthStore()
const canWrite = computed(() => auth.hasPermission('content_ops:write'))
const { loading, loadError, runLoad } = useAdminList()
const activeTab = ref('packages')
const templates = ref<ContentOpsTemplate[]>([])
const packages = ref<ContentPackage[]>([])
const overview = ref<ContentOpsOverview | null>(null)
const referenceLibrary = ref<ContentReferenceLibrary | null>(null)
const filters = reactive({ productKey: '', status: '' })
const dialogVisible = ref(false)
const generateVisible = ref(false)
const reviewVisible = ref(false)
const saving = ref(false)
const generating = ref(false)
const reviewSubmitting = ref(false)
const calendarMonth = ref(new Date())
const editingId = ref('')
const selectedChannels = ref<string[]>([])
const variantForms = reactive<Record<string, { title: string; body: string }>>({})
const slotForms = reactive<Record<string, string>>({})
const publishedArticles = ref<Article[]>([])
const reviewStages = ref<ReviewStageConfig[]>([])
const reviewRow = ref<ContentPackage | null>(null)
const reviewStage = ref<ReviewStage>('teaching')
const reviewChecked = ref<string[]>([])
const reviewNote = ref('')
const form = reactive({ productKey: 'shenlun', templateId: '', sourceType: 'daily_task', sourceId: '', sourceTitle: '', campaignKey: '', deepLink: '', plannedAt: '' })
const generateForm = reactive({ productKey: 'shenlun', templateId: '', articleId: '', campaignKey: '', deepLink: '', plannedAt: '' })
const statusOptions = [
  ['draft', '草稿'], ['teaching_review', '教研审核'], ['ops_review', '运营审核'],
  ['ready', '待发布'], ['published', '已发布'], ['rejected', '已驳回'],
].map(([value, label]) => ({ value, label }))
const availableTemplates = computed(() => templates.value.filter((item) => item.productKey === form.productKey || item.productKey === 'general'))
const currentTemplate = computed(() => templates.value.find((item) => item.id === form.templateId))
const generateTemplates = computed(() => templates.value.filter((item) => item.productKey === generateForm.productKey || item.productKey === 'general'))
const currentReviewConfig = computed(() => reviewStages.value.find((item) => item.key === reviewStage.value))

const productLabel = (key: string) => ({ shenlun: '申论', theory: '政治理论', general: '通用' }[key] || key)
const channelLabel = (key: string) => ({ xiaohongshu: '小红书', douyin: '抖音', bilibili: 'B站', wechat: '公众号' }[key] || key)
const statusLabel = (key: string) => statusOptions.find((item) => item.value === key)?.label || key
const statusType = (status: string) => status === 'published' ? 'success' : status === 'rejected' ? 'danger' : status === 'ready' ? 'warning' : 'info'
const reviewStageLabel = (stage: ReviewStage) => reviewStages.value.find((item) => item.key === stage)?.label || stage
const templateName = (id: string) => templates.value.find((item) => item.id === id)?.name || id
const formatTime = (value?: string) => value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '未排期'
const nextStatusMap: Record<ContentOpsStatus, ContentOpsStatus | null> = { draft: 'teaching_review', teaching_review: 'ops_review', ops_review: 'ready', ready: 'published', rejected: 'draft', published: null }
const nextActionLabels: Partial<Record<ContentOpsStatus, string>> = { draft: '送教研', teaching_review: '教研通过', ops_review: '运营通过', ready: '确认发布', rejected: '退回草稿' }
const nextStatus = (status: ContentOpsStatus) => nextStatusMap[status]
const nextAction = (status: ContentOpsStatus) => nextActionLabels[status] || ''
const canReject = (status: ContentOpsStatus) => ['teaching_review', 'ops_review', 'ready'].includes(status)
const canEdit = (row: ContentPackage) => canWrite.value && ['draft', 'rejected'].includes(row.status)
const canExport = (row: ContentPackage) => ['ready', 'published'].includes(row.status)
const scheduledPackages = computed(() => packages.value.filter((item) => item.plannedAt).sort((a, b) => String(a.plannedAt).localeCompare(String(b.plannedAt))))
const dateKey = (value?: string) => {
  if (!value) return ''
  const date = new Date(value)
  const pad = (part: number) => String(part).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}
const packagesForDay = (day: string) => scheduledPackages.value.filter((item) => dateKey(item.plannedAt) === day)
const plannedTime = (value?: string) => value ? new Date(value).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false }) : ''

async function loadTemplates() { templates.value = await fetchContentTemplates() }
async function loadReviewConfig() { reviewStages.value = (await fetchContentReviewConfig()).stages }
async function loadReferenceLibrary() { referenceLibrary.value = await fetchContentReferenceLibrary() }
async function loadPackages() { await runLoad(async () => { packages.value = await fetchContentPackages({ productKey: filters.productKey || undefined, status: filters.status || undefined }) }) }
async function loadOverview() { overview.value = await fetchContentOpsOverview() }
async function loadAll() { await Promise.all([loadTemplates(), loadReviewConfig(), loadReferenceLibrary(), loadPackages(), loadOverview()]) }
async function refreshOperations() { await Promise.all([loadPackages(), loadOverview()]) }

function initVariant(channel: string, value?: { title?: string; body?: string }) {
  variantForms[channel] = { title: value?.title || '', body: value?.body || '' }
}
function onProductChange() { form.templateId = availableTemplates.value[0]?.id || ''; onTemplateChange() }
function onTemplateChange() {
  Object.keys(variantForms).forEach((key) => delete variantForms[key])
  Object.keys(slotForms).forEach((key) => delete slotForms[key])
  selectedChannels.value = [...(currentTemplate.value?.channels || [])]
  selectedChannels.value.forEach((channel) => initVariant(channel))
  currentTemplate.value?.slots.forEach((slot) => { slotForms[slot] ||= '' })
}
function onGenerateProductChange() { generateForm.templateId = generateTemplates.value[0]?.id || '' }
async function openGenerate() {
  Object.assign(generateForm, { productKey: 'shenlun', templateId: '', articleId: '', campaignKey: '', deepLink: '', plannedAt: '' })
  if (!templates.value.length) {
    try { await loadTemplates() }
    catch (error) { ElMessage.error(error instanceof Error ? error.message : '栏目模板加载失败'); return }
  }
  onGenerateProductChange()
  generateVisible.value = true
  if (!publishedArticles.value.length) {
    try { publishedArticles.value = (await fetchArticles({ page: 1, page_size: 100, status: 'published' })).items }
    catch (error) { ElMessage.error(error instanceof Error ? error.message : '审核文章加载失败') }
  }
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
  currentTemplate.value?.slots.forEach((slot) => { slotForms[slot] = row.slotValues?.[slot] || '' })
  dialogVisible.value = true
}
async function savePackage() {
  if (!form.templateId || !form.sourceId.trim() || !selectedChannels.value.length) { ElMessage.warning('请补齐模板、母资产和至少一个渠道'); return }
  const variants = Object.fromEntries(selectedChannels.value.map((channel) => [channel, { ...variantForms[channel] }]))
  const slotValues = Object.fromEntries((currentTemplate.value?.slots || []).map((slot) => [slot, slotForms[slot] || '']))
  saving.value = true
  try {
    const common = { sourceTitle: form.sourceTitle, campaignKey: form.campaignKey, deepLink: form.deepLink, plannedAt: form.plannedAt || null, slotValues, variants }
    if (editingId.value) await updateContentPackage(editingId.value, common)
    else await createContentPackage({ ...common, productKey: form.productKey, templateId: form.templateId, sourceType: form.sourceType, sourceId: form.sourceId })
    dialogVisible.value = false; await refreshOperations(); ElMessage.success('发布包草稿已保存')
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '保存失败') } finally { saving.value = false }
}
async function generateFromArticle() {
  if (!generateForm.templateId || !generateForm.articleId) { ElMessage.warning('请选择栏目模板和审核文章'); return }
  generating.value = true
  try {
    const row = await generateContentPackageFromArticle({ ...generateForm, plannedAt: generateForm.plannedAt || null })
    generateVisible.value = false
    await refreshOperations()
    openEdit(row)
    const missing = (templates.value.find((item) => item.id === row.templateId)?.slots || []).filter((slot) => !row.slotValues[slot])
    ElMessage.success(missing.length ? `草稿已生成，请补齐 ${missing.length} 个待确认槽位` : '草稿已生成，请复核后送审')
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '生成失败') } finally { generating.value = false }
}
async function advance(row: ContentPackage) {
  const target = nextStatus(row.status); if (!target) return
  if (target === 'ops_review' || target === 'ready') {
    reviewRow.value = row
    reviewStage.value = target === 'ops_review' ? 'teaching' : 'operations'
    reviewChecked.value = []
    reviewNote.value = ''
    reviewVisible.value = true
    return
  }
  try {
    if (target === 'published') await ElMessageBox.confirm('确认已人工发布到对应平台？', '确认发布', { type: 'warning' })
    await updateContentPackageStatus(row.id, target); await refreshOperations(); ElMessage.success(nextAction(row.status))
  } catch (error) { if (error !== 'cancel' && error !== 'close') ElMessage.error(error instanceof Error ? error.message : '操作失败') }
}
async function submitReview() {
  if (!reviewRow.value || !currentReviewConfig.value) return
  const required = currentReviewConfig.value.checklist.map((item) => item.key)
  if (required.some((key) => !reviewChecked.value.includes(key))) { ElMessage.warning('请逐项完成审核清单'); return }
  if (!reviewNote.value.trim()) { ElMessage.warning('请填写审核意见'); return }
  const target: ContentOpsStatus = reviewStage.value === 'teaching' ? 'ops_review' : 'ready'
  const checklist = Object.fromEntries(required.map((key) => [key, true]))
  reviewSubmitting.value = true
  try {
    await updateContentPackageStatus(reviewRow.value.id, target, reviewNote.value.trim(), checklist)
    reviewVisible.value = false
    await refreshOperations()
    ElMessage.success(`${currentReviewConfig.value.label}已通过并留痕`)
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '审核失败') } finally { reviewSubmitting.value = false }
}
async function reject(row: ContentPackage) {
  try {
    const result = await ElMessageBox.prompt('请填写明确的驳回原因', '驳回发布包', { inputValidator: (value) => !!value.trim() || '驳回原因不能为空' })
    await updateContentPackageStatus(row.id, 'rejected', result.value); await refreshOperations(); ElMessage.success('已驳回')
  } catch (error) { if (error !== 'cancel' && error !== 'close') ElMessage.error(error instanceof Error ? error.message : '操作失败') }
}
async function downloadPackage(row: ContentPackage) {
  try {
    const bundle = await exportContentPackage(row.id)
    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${row.campaignKey || row.id}-发布包.json`
    anchor.click()
    URL.revokeObjectURL(url)
    ElMessage.success('发布素材包已导出，请人工发布并回填状态')
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '导出失败') }
}
onMounted(loadAll)
</script>

<style scoped>
.intro { margin-bottom: 14px; }
.metrics-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 12px; }
.metric-card { border-color: #ebeef5; }
.metric-value { color: #303133; font-size: 28px; font-weight: 650; line-height: 1.2; }
.metric-label { margin-top: 6px; color: #606266; font-size: 14px; }
.metric-note { margin-top: 5px; color: #909399; font-size: 12px; }
.inventory-alerts { display: grid; gap: 8px; margin-bottom: 12px; }
.generate-tip { margin-bottom: 18px; }
.review-tip { margin-bottom: 16px; }
.review-target { margin-bottom: 12px; color: #303133; font-weight: 650; }
.review-checklist { display: grid; gap: 10px; margin-bottom: 18px; }
.review-history { padding: 8px 28px 4px 54px; }
.review-history-title { margin-bottom: 14px; color: #303133; font-weight: 650; }
.review-record-head { display: flex; align-items: center; gap: 8px; color: #606266; font-size: 13px; }
.review-record-note { margin-top: 7px; color: #606266; line-height: 1.6; }
.reference-alert { margin-bottom: 12px; }
.reference-sources { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
.reference-card h4 { margin: 16px 0 8px; color: #303133; }
.reference-card ol, .reference-card ul { margin: 0; padding-left: 22px; color: #606266; font-size: 13px; line-height: 1.8; }
.reference-example { margin-top: 16px; padding: 12px; border-radius: 8px; background: #f7f8fa; }
.reference-example p { min-height: 0; margin: 8px 0; }
.example-line { color: #606266; font-size: 12px; line-height: 1.7; }
.option-meta { float: right; margin-left: 16px; color: #909399; font-size: 12px; }
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
.schedule-calendar { margin-top: 4px; }
.schedule-calendar :deep(.el-calendar-day) { height: 116px; padding: 6px; overflow: auto; }
.calendar-day { color: #606266; font-size: 13px; margin-bottom: 4px; }
.calendar-item { display: block; width: 100%; margin: 3px 0; padding: 4px 6px; overflow: hidden; border: 0; border-radius: 4px; background: #ecf5ff; color: #337ecc; font-size: 11px; text-align: left; text-overflow: ellipsis; white-space: nowrap; cursor: pointer; }
.calendar-item:disabled { background: #f4f4f5; color: #909399; cursor: default; }
.calendar-item span { margin-right: 4px; font-weight: 650; }
@media (max-width: 1000px) { .metrics-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
