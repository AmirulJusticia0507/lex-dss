<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElRow, ElCol, ElCard, ElStatistic, ElTable, ElTableColumn, ElTag, ElButton, ElIcon, ElEmpty, ElProgress, ElDivider, ElTooltip } from 'element-plus'
import { TrendCharts, Warning, CircleCheck, Clock, Document, Rank, DataAnalysis, ArrowUp, ArrowDown, Minus } from '@element-plus/icons-vue'
import { useLegalStore } from '@/stores'
import { useDSSStore } from '@/stores'
import RiskScoreCard from '@/components/RiskScoreCard.vue'
import ConflictMatrix from '@/components/ConflictMatrix.vue'

const legalStore = useLegalStore()
const dssStore = useDSSStore()

const stats = ref({
  totalConflicts: 0,
  highRisk: 0,
  mediumRisk: 0,
  lowRisk: 0,
  totalArticles: 0,
  analyzedDocuments: 0,
})

const recentConflicts = ref([])
const riskDistribution = ref([
  { name: 'High', value: 0, color: '#dc2626' },
  { name: 'Medium', value: 0, color: '#d97706' },
  { name: 'Low', value: 0, color: '#16a34a' },
])

const loading = ref(false)
const matrixLoading = ref(false)

const riskScore = ref(0)
const riskLevel = ref('LOW')
const riskFactors = ref([])
const mitigationSteps = ref([])
const riskTrend = ref(null)

async function fetchDashboardData() {
  loading.value = true
  try {
    await Promise.all([
      legalStore.fetchStats(),
      legalStore.fetchConflicts({ limit: 10, sort: '-created_at' }),
    ])

    if (legalStore.stats) {
      stats.value = {
        totalConflicts: legalStore.stats.total_conflicts || 0,
        highRisk: legalStore.stats.high_severity || 0,
        mediumRisk: legalStore.stats.medium_severity || 0,
        lowRisk: legalStore.stats.low_severity || 0,
        totalArticles: legalStore.stats.total_articles || 0,
        analyzedDocuments: legalStore.stats.analyzed_documents || 0,
      }
    }

    recentConflicts.value = legalStore.conflicts.slice(0, 5)

    riskDistribution.value = [
      { name: 'High', value: stats.value.highRisk, color: '#dc2626' },
      { name: 'Medium', value: stats.value.mediumRisk, color: '#d97706' },
      { name: 'Low', value: stats.value.lowRisk, color: '#16a34a' },
    ]

    calculateRiskScore()
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
    useMockData()
  } finally {
    loading.value = false
  }
}

function useMockData() {
  stats.value = {
    totalConflicts: 24,
    highRisk: 5,
    mediumRisk: 12,
    lowRisk: 7,
    totalArticles: 1250,
    analyzedDocuments: 48,
  }

  recentConflicts.value = [
    { id: 1, conflict_type: 'LEX_SUPERIOR', severity: 'HIGH', source_article: { document_title: 'UU No. 12/2011', article_number: 'Pasal 7' }, target_article: { document_title: 'Perda No. 5/2023', article_number: 'Pasal 12' }, description: 'Perda bertentangan dengan hierarki perundang-undangan', created_at: '2024-01-15T10:30:00Z' },
    { id: 2, conflict_type: 'LEX_SPECIALIS', severity: 'MEDIUM', source_article: { document_title: 'KUHP Baru', article_number: 'Pasal 101' }, target_article: { document_title: 'UU ITE', article_number: 'Pasal 27' }, description: 'Tumpang tindih sanksi pidana', created_at: '2024-01-14T14:20:00Z' },
    { id: 3, conflict_type: 'DIRECT_CONTRADICTION', severity: 'HIGH', source_article: { document_title: 'KUHPerdata', article_number: 'Pasal 1320' }, target_article: { document_title: 'Perjanjian Kerja', article_number: 'Pasal 5' }, description: 'Klausula waiver hak tidak sah', created_at: '2024-01-13T09:15:00Z' },
    { id: 4, conflict_type: 'LEX_POSTERIOR', severity: 'LOW', source_article: { document_title: 'UU No. 1/2023', article_number: 'Pasal 5' }, target_article: { document_title: 'KUHP Lama', article_number: 'Pasal 12' }, description: 'UU baru mengubah ketentuan lama', created_at: '2024-01-12T16:45:00Z' },
    { id: 5, conflict_type: 'LEX_SUPERIOR', severity: 'MEDIUM', source_article: { document_title: 'UUD 1945', article_number: 'Pasal 28D' }, target_article: { document_title: 'Perpres No. 10/2024', article_number: 'Pasal 3' }, description: 'Pelanggaran HAM dasar', created_at: '2024-01-11T11:00:00Z' },
  ]

  riskDistribution.value = [
    { name: 'High', value: 5, color: '#dc2626' },
    { name: 'Medium', value: 12, color: '#d97706' },
    { name: 'Low', value: 7, color: '#16a34a' },
  ]

  calculateRiskScore()
}

function calculateRiskScore() {
  const total = stats.value.totalConflicts
  if (total === 0) {
    riskScore.value = 15
    riskLevel.value = 'RENDAH'
    return
  }

  const weightedScore = (stats.value.highRisk * 100 + stats.value.mediumRisk * 50 + stats.value.lowRisk * 10) / total
  riskScore.value = Math.min(Math.round(weightedScore), 100)

  if (riskScore.value >= 75) riskLevel.value = 'SANGAT TINGGI'
  else if (riskScore.value >= 50) riskLevel.value = 'TINGGI'
  else if (riskScore.value >= 25) riskLevel.value = 'SEDANG'
  else riskLevel.value = 'RENDAH'

  riskFactors.value = [
    { id: 1, title: 'Kontradiksi Lex Superior', description: `${stats.value.highRisk} kontradiksi hierarki perundang-undangan terdeteksi`, severity: stats.value.highRisk > 0 ? 'HIGH' : 'LOW' },
    { id: 2, title: 'Tumpang Tindih Sanksi', description: `${stats.value.mediumRisk} kasus overlapping penalty dalam hukum pidana`, severity: stats.value.mediumRisk > 5 ? 'MEDIUM' : 'LOW' },
    { id: 3, title: 'Klausula Tidak Sah', description: 'Beberapa klausula standar bertentangan dengan Pasal 1337 KUHPerdata', severity: 'MEDIUM' },
    { id: 4, title: 'Ketidaksesuaian Prosedur', description: 'Proses pembentukan peraturan tidak mengikuti UU No. 12/2011', severity: 'LOW' },
  ]

  mitigationSteps.value = [
    'Lakukan review menyeluruh terhadap Perda yang bermasalah',
    'Koordinasi dengan Kemenkumham untuk harmonisasi',
    'Revisi klausula standar sesuai Pasal 1320 & 1337 KUHPerdata',
    'Sosialisasi hierarki perundang-undangan ke pemangku kepentingan',
  ]

  riskTrend.value = {
    direction: 'down',
    percentage: 12,
    label: 'Risiko menurun 12% dari bulan lalu',
  }
}

function getConflictTypeLabel(type) {
  const labels = {
    LEX_SUPERIOR: 'Lex Superior',
    LEX_SPECIALIS: 'Lex Specialis',
    LEX_POSTERIOR: 'Lex Posterior',
    DIRECT_CONTRADICTION: 'Direct Contradiction',
  }
  return labels[type] || type
}

function getConflictTypeClass(type) {
  return `conflict-type-badge ${type.toLowerCase().replace('_', '-')}`
}

function getSeverityType(severity) {
  const types = { HIGH: 'danger', MEDIUM: 'warning', LOW: 'success' }
  return types[severity] || 'info'
}

function formatDate(dateString) {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('id-ID', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getTrendIcon(direction) {
  if (direction === 'up') return ArrowUp
  if (direction === 'down') return ArrowDown
  return Minus
}

function getTrendClass(direction) {
  if (direction === 'up') return 'negative'
  if (direction === 'down') return 'positive'
  return 'neutral'
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<template>
  <div class="dashboard-view">
    <div class="page-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">Ringkasan analisis kontradiksi norma hukum dan risiko legal</p>
      </div>
      <el-button type="primary" @click="fetchDashboardData" :loading="loading" class="refresh-btn">
        <el-icon><TrendCharts /></el-icon>
        Refresh Data
      </el-button>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 13px; color: #6b7280;">Total Kontradiksi</span>
              <el-icon style="color: #0ea5e9;"><Warning /></el-icon>
            </div>
          </template>
          <el-statistic :value="stats.totalConflicts" value-style="font-size: 32px; color: #1e3a5f;" />
          <template #footer>
            <div class="stat-trend positive">
              <el-icon><ArrowUp /></el-icon>
              <span>+3 dari minggu lalu</span>
            </div>
          </template>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 13px; color: #6b7280;">Risiko Tinggi</span>
              <el-icon style="color: #dc2626;"><ArrowUp /></el-icon>
            </div>
          </template>
          <el-statistic :value="stats.highRisk" value-style="font-size: 32px; color: #dc2626;" />
          <template #footer>
            <div class="stat-trend negative">
              <el-icon><ArrowUp /></el-icon>
              <span>Perlu perhatian segera</span>
            </div>
          </template>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 13px; color: #6b7280;">Artikel Hukum</span>
              <el-icon style="color: #16a34a;"><Document /></el-icon>
            </div>
          </template>
          <el-statistic :value="stats.totalArticles" value-style="font-size: 32px; color: #1e3a5f;" />
          <template #footer>
            <div class="stat-trend positive">
              <el-icon><ArrowUp /></el-icon>
              <span>+15 artikel baru</span>
            </div>
          </template>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 13px; color: #6b7280;">Dokuman Dianalisis</span>
              <el-icon style="color: #c9a84c;"><DataAnalysis /></el-icon>
            </div>
          </template>
          <el-statistic :value="stats.analyzedDocuments" value-style="font-size: 32px; color: #1e3a5f;" />
          <template #footer>
            <div class="stat-trend positive">
              <el-icon><ArrowUp /></el-icon>
              <span>+2 dokumen hari ini</span>
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 24px;">
      <el-col :xs="24" :lg="16">
        <el-card class="card">
          <template #header>
            <div class="card-header">
              <span class="card-title">Matriks Kontradiksi Norma</span>
              <el-button size="small" type="primary" @click="$router.push('/conflict-checker')">
                <el-icon><Warning /></el-icon>
                Analisis Baru
              </el-button>
            </div>
          </template>
          <ConflictMatrix
            :conflicts="recentConflicts"
            :width="800"
            :height="450"
            @node-click="handleNodeClick"
          />
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card class="card">
          <template #header>
            <div class="card-header">
              <span class="card-title">Risk Score Overview</span>
            </div>
          </template>
          <RiskScoreCard
            :risk-score="riskScore"
            :risk-level="riskLevel"
            :risk-factors="riskFactors"
            :mitigation-steps="mitigationSteps"
            :trend="riskTrend"
            :size="180"
          />
        </el-card>

        <el-card class="card" style="margin-top: 20px;">
          <template #header>
            <span class="card-title">Distribusi Risiko</span>
          </template>
          <div class="risk-distribution">
            <div v-for="item in riskDistribution" :key="item.name" class="risk-dist-item">
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <div style="width: 12px; height: 12px; border-radius: 50%;" :style="{ backgroundColor: item.color }"></div>
                <span style="font-weight: 500;">{{ item.name }}</span>
                <span style="margin-left: auto; font-weight: 600;">{{ item.value }}</span>
              </div>
              <el-progress
                :percentage="stats.totalConflicts > 0 ? (item.value / stats.totalConflicts * 100) : 0"
                :stroke-width="8"
                :color="item.color"
                show-text
                format="percent"
                :text-inside="true"
                status="success"
              />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 24px;">
      <el-col :xs="24">
        <el-card class="card">
          <template #header>
            <div class="card-header">
              <span class="card-title">Kontradiksi Terbaru</span>
              <el-button size="small" type="text" @click="$router.push('/conflict-checker')">Lihat Semua</el-button>
            </div>
          </template>
          <el-table
            v-loading="loading"
            :data="recentConflicts"
            border
            stripe
            style="width: 100%"
            :row-style="{ cursor: 'pointer' }"
            @row-click="handleRowClick"
          >
            <el-table-column prop="conflict_type" label="Jenis Kontradiksi" width="180">
              <template #default="scope">
                <span :class="getConflictTypeClass(scope.row.conflict_type)">{{ getConflictTypeLabel(scope.row.conflict_type) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="severity" label="Severity" width="120">
              <template #default="scope">
                <el-tag :type="getSeverityType(scope.row.severity)" effect="plain">{{ scope.row.severity }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="Pasal Sumber" width="200">
              <template #default="scope">
                <div>
                  <div style="font-weight: 500;">{{ scope.row.source_article?.document_title }}</div>
                  <div style="font-size: 12px; color: #9ca3af;">{{ scope.row.source_article?.article_number }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="Pasal Target" width="200">
              <template #default="scope">
                <div>
                  <div style="font-weight: 500;">{{ scope.row.target_article?.document_title }}</div>
                  <div style="font-size: 12px; color: #9ca3af;">{{ scope.row.target_article?.article_number }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="Deskripsi" min-width="250" show-overflow-tooltip />
            <el-table-column prop="created_at" label="Waktu Deteksi" width="180">
              <template #default="scope">
                {{ formatDate(scope.row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
          <div v-if="recentConflicts.length === 0" class="empty-state">
            <el-empty description="Belum ada data kontradiksi" image="https://fuss10.elemecdn.com/e/bf/352815f91f3b80189f0a48140c2efpng.png">
              <template #image>
                <el-icon style="font-size: 48px; color: #d1d5db;"><Warning /></el-icon>
              </template>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
export default {
  methods: {
    handleNodeClick(node) {
      console.log('Node clicked:', node)
    },
    handleRowClick(row) {
      console.log('Row clicked:', row)
      this.$router.push(`/conflict-checker/detail/${row.id}`)
    },
  },
}
</script>

<style scoped>
.dashboard-view {
  height: 100%;
  overflow-y: auto;
}

.stats-row {
  margin-bottom: 0;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 8px;
}

.risk-distribution {
  padding: 8px 0;
}

.risk-dist-item {
  margin-bottom: 16px;
}

.risk-dist-item:last-child {
  margin-bottom: 0;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}
</style>