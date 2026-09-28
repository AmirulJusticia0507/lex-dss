<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElRow, ElCol, ElCard, ElStatistic, ElTable, ElTableColumn, ElTag, ElButton, ElIcon, ElEmpty, ElProgress, ElDivider, ElTooltip } from 'element-plus'
import { TrendCharts, Warning, CircleCheck, Clock, Document, Rank, DataAnalysis, ArrowUp, ArrowDown, Minus } from '@element-plus/icons-vue'
import { useLegalStore } from '@/stores'
import { useDSSStore } from '@/stores'
import RiskScoreCard from '@/components/RiskScoreCard.vue'
import ConflictMatrix from '@/components/ConflictMatrix.vue'
import StatCard from '@/components/StatCard.vue'

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

function handleNodeClick(node) {
  console.log('Node clicked:', node)
}

function handleRowClick(row) {
  console.log('Row clicked:', row)
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<template>
  <div class="dashboard-view mx-auto w-full max-w-[1600px] space-y-6">
    <div class="page-header rounded-2xl border border-slate-200/80 bg-white px-6 py-5 shadow-sm">
      <div>
        <p class="mb-1 text-xs font-semibold uppercase tracking-[0.16em] text-sky-700">Lex-DSS · Ringkasan</p>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">Ringkasan analisis kontradiksi norma hukum dan risiko legal</p>
      </div>
      <el-tooltip placement="left" :show-after="300" content="Muat ulang data dashboard">
        <el-button type="primary" @click="fetchDashboardData" :loading="loading" class="refresh-btn">
          <el-icon><TrendCharts /></el-icon>
          Refresh Data
        </el-button>
      </el-tooltip>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-tooltip
          placement="top"
          :show-after="300"
          :content="'Total kasus kontradiksi norma hukum yang terdeteksi oleh engine Lex Integrity'"
        >
          <StatCard
            label="Total Kontradiksi"
            :value="stats.totalConflicts"
            :icon="Warning"
            accent="info"
            trend="+3 dari minggu lalu"
            trend-direction="up"
          />
        </el-tooltip>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <el-tooltip
          placement="top"
          :show-after="300"
          :content="'Kontradiksi dengan severity HIGH memerlukan review segera'"
        >
          <StatCard
            label="Risiko Tinggi"
            :value="stats.highRisk"
            :icon="Warning"
            accent="danger"
            trend="Perlu perhatian segera"
            trend-direction="down"
          />
        </el-tooltip>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <el-tooltip
          placement="top"
          :show-after="300"
          :content="'Jumlah pasal/artikel hukum yang sudah di-load ke basis data'"
        >
          <StatCard
            label="Artikel Hukum"
            :value="stats.totalArticles"
            :icon="Document"
            accent="primary"
            trend="+15 artikel baru"
            trend-direction="up"
          />
        </el-tooltip>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <el-tooltip
          placement="top"
          :show-after="300"
          :content="'Jumlah dokumen peraturan yang sudah dianalisis'"
        >
          <StatCard
            label="Dokumen Dianalisis"
            :value="stats.analyzedDocuments"
            :icon="DataAnalysis"
            accent="gold"
            trend="+2 dokumen hari ini"
            trend-direction="up"
          />
        </el-tooltip>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="16">
        <el-card class="card">
          <template #header>
            <div class="card-header">
              <span class="card-title">Matriks Kontradiksi Norma</span>
              <el-tooltip placement="top" :show-after="300" content="Buka Conflict Checker untuk analisis baru">
                <el-button size="small" type="primary" @click="$router.push('/conflict-checker')">
                  <el-icon><Warning /></el-icon>
                  Analisis Baru
                </el-button>
              </el-tooltip>
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
              <el-tooltip placement="top" :show-after="300" content="Skor risiko gabungan dari semua kontradiksi">
                <el-icon class="info-icon"><DataAnalysis /></el-icon>
              </el-tooltip>
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

        <el-card class="card mt-5">
          <template #header>
            <span class="card-title">Distribusi Risiko</span>
          </template>
          <div class="risk-distribution">
            <el-tooltip
              v-for="item in riskDistribution"
              :key="item.name"
              placement="top"
              :show-after="300"
              :content="`Jumlah kontradiksi dengan risiko ${item.name.toLowerCase()}`"
            >
              <div class="risk-dist-item">
                <div class="risk-dist-head">
                  <span class="risk-dot" :style="{ backgroundColor: item.color }"></span>
                  <span class="risk-name">{{ item.name }}</span>
                  <span class="risk-count">{{ item.value }}</span>
                </div>
                <el-progress
                  :percentage="stats.totalConflicts > 0 ? Math.round((item.value / stats.totalConflicts) * 100) : 0"
                  :stroke-width="8"
                  :color="item.color"
                  :show-text="false"
                />
              </div>
            </el-tooltip>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :xs="24">
        <el-card class="card">
          <template #header>
<div class="card-header">
               <span class="card-title">Kontradiksi Terbaru</span>
               <el-tooltip placement="top" :show-after="300" content="Lihat semua kontradiksi di Conflict Checker">
                 <el-button size="small" link @click="$router.push('/conflict-checker')">Lihat Semua</el-button>
               </el-tooltip>
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
                 <el-tooltip placement="top" :show-after="300" :content="scope.row.description">
                   <span :class="getConflictTypeClass(scope.row.conflict_type)">{{ getConflictTypeLabel(scope.row.conflict_type) }}</span>
                 </el-tooltip>
               </template>
             </el-table-column>
             <el-table-column prop="severity" label="Severity" width="120">
               <template #default="scope">
                 <el-tooltip placement="top" :show-after="300" :content="scope.row.severity === 'HIGH' ? 'Kontradiksi dengan risiko tinggi' : scope.row.severity === 'MEDIUM' ? 'Kontradiksi dengan risiko sedang' : 'Kontradiksi dengan risiko rendah'">
                   <el-tag :type="getSeverityType(scope.row.severity)" effect="plain">{{ scope.row.severity }}</el-tag>
                 </el-tooltip>
               </template>
             </el-table-column>
<el-table-column label="Pasal Sumber" width="200">
               <template #default="scope">
                 <el-tooltip placement="top" :show-after="300" :content="scope.row.source_article?.document_title">
                   <div>
                     <div style="font-weight: 500;">{{ scope.row.source_article?.document_title }}</div>
                     <div style="font-size: 12px; color: #9ca3af;">{{ scope.row.source_article?.article_number }}</div>
                   </div>
                 </el-tooltip>
               </template>
             </el-table-column>
             <el-table-column label="Pasal Target" width="200">
               <template #default="scope">
                 <el-tooltip placement="top" :show-after="300" :content="scope.row.target_article?.document_title">
                   <div>
                     <div style="font-weight: 500;">{{ scope.row.target_article?.document_title }}</div>
                     <div style="font-size: 12px; color: #9ca3af;">{{ scope.row.target_article?.article_number }}</div>
                   </div>
                 </el-tooltip>
               </template>
             </el-table-column>
<el-table-column prop="description" label="Deskripsi" min-width="250">
               <template #default="scope">
                 <el-tooltip placement="top" :show-after="300" :content="scope.row.description">
                   <span>{{ scope.row.description }}</span>
                 </el-tooltip>
               </template>
             </el-table-column>
             <el-table-column prop="created_at" label="Waktu Deteksi" width="180">
               <template #default="scope">
                 <el-tooltip placement="top" :show-after="300" :content="formatDate(scope.row.created_at)">
                   <span>{{ formatDate(scope.row.created_at) }}</span>
                 </el-tooltip>
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

<style scoped>
.dashboard-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-row {
  margin-bottom: 0 !important;
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.risk-distribution {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.risk-dist-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.risk-dist-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.risk-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.risk-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.risk-count {
  margin-left: auto;
  font-size: 13px;
  font-weight: 700;
  color: var(--legal-dark);
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

.section-gap {
    margin-top: 20px;
  }

  .info-icon {
    margin-left: 6px;
    color: #9ca3af;
    cursor: help;
    vertical-align: middle;
  }
</style>
