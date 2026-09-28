<script setup>
import { ref, onMounted } from 'vue'
import { ElCard, ElInput, ElSelect, ElOption, ElButton, ElTag, ElTable, ElTableColumn, ElEmpty, ElDialog, ElDivider, ElRow, ElCol, ElStatistic, ElMessage } from 'element-plus'
import { Search, Document, Collection, Rank, DataAnalysis, Warning, CircleCheck } from '@element-plus/icons-vue'
import CustomPagination from '@/components/CustomPagination.vue'

const cases = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const selectedCourt = ref('')
const selectedType = ref('')

const courts = [
  { value: '', label: 'Semua Pengadilan' },
  { value: 'Mahkamah Agung', label: 'Mahkamah Agung' },
  { value: 'Pengadilan Negeri', label: 'Pengadilan Negeri' },
  { value: 'Pengadilan Tinggi', label: 'Pengadilan Tinggi' },
  { value: 'Pengadilan Tata Usaha Negara', label: 'PTUN' },
  { value: 'Pengadilan Pajak', label: 'Pengadilan Pajak' },
  { value: 'Pengadilan Militer', label: 'Pengadilan Militer' },
  { value: 'Pengadilan Agama', label: 'Pengadilan Agama' },
]

const caseTypes = [
  { value: '', label: 'Semua Jenis' },
  { value: 'pidana', label: 'Pidana' },
  { value: 'perdata', label: 'Perdata' },
  { value: 'tata_usaha_negara', label: 'Tata Usaha Negara' },
  { value: 'pajak', label: 'Pajak' },
  { value: 'agama', label: 'Agama' },
  { value: 'militer', label: 'Militer' },
]

const stats = ref({
  totalCases: 0,
  byCourt: [],
  byType: [],
})

const selectedCase = ref(null)
const detailVisible = ref(false)

async function fetchCases() {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: page.value,
      page_size: pageSize.value,
    })
    if (searchQuery.value) params.append('search', searchQuery.value)
    if (selectedCourt.value) params.append('court_name', selectedCourt.value)
    if (selectedType.value) params.append('case_type', selectedType.value)

    const response = await fetch(`/api/v1/case-law/?${params}`)
    const data = await response.json()
    cases.value = data.items || []
    total.value = data.pagination?.total || 0
  } catch (error) {
    console.error('Failed to fetch cases:', error)
    useMockData()
  } finally {
    loading.value = false
  }
}

function useMockData() {
  cases.value = [
    { id: '1', case_number: '123/Pid/2024/PN.JKT', case_title: 'Terdakwa dakwaan pencucian uang', court_name: 'Pengadilan Negeri', case_type: 'pidana', verdict_date: '2024-01-15T00:00:00', judge_name: 'H. Budi Santoso, SH', summary: 'Terdakwa terbukti melakukan tindak pidana pencucian uang...', legal_articles: ['UU No. 8/2010', 'KUHP Pasal 372'] },
    { id: '2', case_number: '456/PDT/2024/PT.BDG', case_title: 'Gugatan wanprestasi kontrak', court_name: 'Pengadilan Tinggi', case_type: 'perdata', verdict_date: '2024-02-20T00:00:00', judge_name: 'Hj. Siti Rahmawati, SH', summary: 'Penggugat menggugat tergugat atas wanprestasi...', legal_articles: ['KUHPerdata Pasal 1238', 'KUHPerdata Pasal 1243'] },
    { id: '3', case_number: '789/TUN/2024/PTUN.JKT', case_title: 'Gugatan pembatalan keputusan BPN', court_name: 'Pengadilan Tata Usaha Negara', case_type: 'tata_usaha_negara', verdict_date: '2024-03-10T00:00:00', judge_name: 'H. Ahmad Wijaya, SH', summary: 'Penggugat meminta pembatalan keputusan BPN...', legal_articles: ['UU No. 5/1986', 'UU No. 30/2014'] },
    { id: '4', case_number: '321/PDT.P/2024/PN.SBY', case_title: 'Perceraian gugatan istri', court_name: 'Pengadilan Agama', case_type: 'agama', verdict_date: '2024-01-25T00:00:00', judge_name: 'H. Muhammad Hasan, SH', summary: 'Istri mengajukan gugatan perceraian...', legal_articles: ['UU No. 1/1974', 'Kompilasi Hukum Islam'] },
    { id: '5', case_number: '654/PDT/2024/PN.MDN', case_title: 'Sengketa tanah antar warga', court_name: 'Pengadilan Negeri', case_type: 'perdata', verdict_date: '2024-04-05T00:00:00', judge_name: 'H. Dedi Kurniawan, SH', summary: 'Sengketa kepemilikan tanah...', legal_articles: ['UU No. 5/1960', 'PP No. 24/1997'] },
  ]
  total.value = 5
  stats.value = {
    totalCases: 5,
    byCourt: [
      { name: 'Pengadilan Negeri', count: 2 },
      { name: 'Pengadilan Tinggi', count: 1 },
      { name: 'PTUN', count: 1 },
      { name: 'Pengadilan Agama', count: 1 },
    ],
    byType: [
      { name: 'pidana', count: 1 },
      { name: 'perdata', count: 2 },
      { name: 'tata_usaha_negara', count: 1 },
      { name: 'agama', count: 1 },
    ],
  }
}

function handleSearch() {
  page.value = 1
  fetchCases()
}

function handlePageChange(newPage) {
  page.value = newPage
  fetchCases()
}

function handlePageSizeChange(newSize) {
  pageSize.value = newSize
  page.value = 1
  fetchCases()
}

function viewCase(item) {
  selectedCase.value = item
  detailVisible.value = true
}

function getCaseTypeLabel(type) {
  const labels = {
    pidana: 'Pidana',
    perdata: 'Perdata',
    tata_usaha_negara: 'Tata Usaha Negara',
    pajak: 'Pajak',
    agama: 'Agama',
    militer: 'Militer',
  }
  return labels[type] || type
}

function getCaseTypeClass(type) {
  const classes = {
    pidana: 'danger',
    perdata: 'success',
    tata_usaha_negara: 'warning',
    pajak: 'info',
    agama: 'primary',
    militer: 'danger',
  }
  return classes[type] || 'info'
}

function formatDate(dateString) {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('id-ID', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

onMounted(() => {
  fetchCases()
})
</script>

<template>
  <div class="case-law-view mx-auto w-full max-w-[1600px] space-y-6">
    <div class="page-header rounded-2xl border border-slate-200/80 bg-white px-6 py-5 shadow-sm">
      <div>
        <p class="mb-1 text-xs font-semibold uppercase tracking-[0.16em] text-sky-700">Lex-DSS · Yurisprudensi</p>
        <h1 class="page-title">Case Law Search</h1>
        <p class="page-subtitle">Pencarian putusan pengadilan dan yurisprudensi Indonesia</p>
      </div>
      <el-button type="primary" @click="fetchCases" :loading="loading">
        <el-icon><Search /></el-icon>
        Refresh
      </el-button>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="card">
          <el-statistic title="Total Putusan" :value="total">
            <template #prefix><el-icon><Document /></el-icon></template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="card">
          <el-statistic title="Pengadilan Negeri" :value="stats.byCourt.find(c => c.name === 'Pengadilan Negeri')?.count || 0">
            <template #prefix><el-icon><Rank /></el-icon></template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="card">
          <el-statistic title="Pengadilan Tinggi" :value="stats.byCourt.find(c => c.name === 'Pengadilan Tinggi')?.count || 0">
            <template #prefix><el-icon><Collection /></el-icon></template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="card">
          <el-statistic title="PTUN" :value="stats.byCourt.find(c => c.name === 'Pengadilan Tata Usaha Negara')?.count || 0">
            <template #prefix><el-icon><DataAnalysis /></el-icon></template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="card">
      <template #header>
        <div class="card-header">
          <div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: center;">
            <el-input
              v-model="searchQuery"
              placeholder="Cari nomor perkara, judul, atau ringkasan..."
              size="small"
              prefix-icon="Search"
              clearable
              @keyup.enter="handleSearch"
              style="width: 300px;"
            />
            <el-select v-model="selectedCourt" placeholder="Pengadilan" size="small" style="width: 200px;" clearable>
              <el-option v-for="c in courts" :key="c.value" :label="c.label" :value="c.value" />
            </el-select>
            <el-select v-model="selectedType" placeholder="Jenis Perkara" size="small" style="width: 180px;" clearable>
              <el-option v-for="t in caseTypes" :key="t.value" :label="t.label" :value="t.value" />
            </el-select>
            <el-button size="small" @click="handleSearch">
              <el-icon><Search /></el-icon>
              Cari
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="cases"
        border
        stripe
        style="width: 100%"
        :row-style="{ cursor: 'pointer' }"
        @row-click="viewCase"
      >
        <el-table-column prop="case_number" label="Nomor Perkara" min-width="200" />
        <el-table-column prop="case_title" label="Judul" min-width="250" show-overflow-tooltip />
        <el-table-column prop="court_name" label="Pengadilan" width="180" />
        <el-table-column prop="case_type" label="Jenis" width="150">
          <template #default="scope">
            <el-tag :type="getCaseTypeClass(scope.row.case_type)" effect="plain" size="small">
              {{ getCaseTypeLabel(scope.row.case_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="verdict_date" label="Tanggal Putusan" width="140">
          <template #default="scope">{{ formatDate(scope.row.verdict_date) }}</template>
        </el-table-column>
        <el-table-column prop="judge_name" label="Hakim" width="180" />
      </el-table>

      <div v-if="cases.length === 0 && !loading" style="padding: 40px 0; text-align: center;">
        <el-empty description="Tidak ada data putusan" />
      </div>

      <CustomPagination
        v-if="total > 0"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        @update:current-page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </el-card>

    <el-dialog v-model="detailVisible" :title="selectedCase?.case_title" width="800px" destroy-on-close>
      <div v-if="selectedCase" class="case-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="Nomor Perkara">{{ selectedCase.case_number }}</el-descriptions-item>
          <el-descriptions-item label="Pengadilan">{{ selectedCase.court_name }}</el-descriptions-item>
          <el-descriptions-item label="Jenis Perkara">{{ getCaseTypeLabel(selectedCase.case_type) }}</el-descriptions-item>
          <el-descriptions-item label="Tanggal Putusan">{{ formatDate(selectedCase.verdict_date) }}</el-descriptions-item>
          <el-descriptions-item label="Hakim">{{ selectedCase.judge_name }}</el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <h4 style="margin-bottom: 12px;">Ringkasan</h4>
        <p style="color: #4b5563; line-height: 1.7;">{{ selectedCase.summary }}</p>

        <template v-if="selectedCase.legal_articles?.length">
          <el-divider />
          <h4 style="margin-bottom: 12px;">Dasar Hukum</h4>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <el-tag v-for="article in selectedCase.legal_articles" :key="article" type="info" effect="plain">
              {{ article }}
            </el-tag>
          </div>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.case-law-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-row {
  margin-bottom: 0 !important;
}

.case-detail {
  padding: 0 8px;
}
</style>
