<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElCard, ElTable, ElTableColumn, ElInput, ElSelect, ElOption, ElButton, ElTag, ElIcon, ElTooltip, ElDropdown, ElDropdownMenu, ElDropdownItem, ElPagination, ElDialog, ElForm, ElFormItem, ElRadioGroup, ElRadio, ElDivider, ElEmpty, ElTabs, ElTabPane, ElStatistic, ElRow, ElCol, ElProgress, ElBadge, ElPopover, ElDrawer } from 'element-plus'
import { Search, Filter, Download, Upload, Edit, Delete, View, CopyDocument, Star, More, Document, Collection, Rank, Warning, CircleCheck, ArrowRight, Setting, FullScreen } from '@element-plus/icons-vue'
import { useLegalStore } from '@/stores'

const legalStore = useLegalStore()

const articles = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const searchQuery = ref('')
const selectedDomain = ref('all')
const selectedHierarchy = ref('all')
const sortBy = ref('relevance')

const domains = [
  { value: 'all', label: 'Semua Domain' },
  { value: 'HTN', label: 'Hukum Tata Negara & Administrasi' },
  { value: 'PIDANA', label: 'Hukum Pidana' },
  { value: 'PERDATA', label: 'Hukum Perdata' },
]

const hierarchies = [
  { value: 'all', label: 'Semua Tingkat' },
  { value: '1', label: 'UUD 1945' },
  { value: '2', label: 'TAP MPR' },
  { value: '3', label: 'UU / PERPPU' },
  { value: '4', label: 'PP' },
  { value: '5', label: 'Perpres' },
  { value: '6', label: 'Permen' },
  { value: '7', label: 'Perda' },
]

const sortOptions = [
  { value: 'relevance', label: 'Relevansi' },
  { value: 'date_desc', label: 'Terbaru' },
  { value: 'date_asc', label: 'Terlama' },
  { value: 'hierarchy', label: 'Hierarki' },
  { value: 'title', label: 'Judul' },
]

const articleDetail = ref(null)
const detailVisible = ref(false)
const drawerVisible = ref(false)

const stats = ref({
  totalArticles: 0,
  byDomain: {},
  byHierarchy: {},
})

async function fetchArticles() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      limit: pageSize.value,
      search: searchQuery.value,
      domain: selectedDomain.value !== 'all' ? selectedDomain.value : '',
      hierarchy: selectedHierarchy.value !== 'all' ? selectedHierarchy.value : '',
      sort: sortBy.value,
    }
    await legalStore.fetchArticles(params)
    articles.value = legalStore.articles
    total.value = legalStore.stats?.total_articles || articles.value.length

    if (legalStore.stats) {
      stats.value = {
        totalArticles: legalStore.stats.total_articles || 0,
        byDomain: legalStore.stats.by_domain || {},
        byHierarchy: legalStore.stats.by_hierarchy || {},
      }
    }
  } catch (error) {
    console.error('Failed to fetch articles:', error)
    useMockData()
  } finally {
    loading.value = false
  }
}

function useMockData() {
  articles.value = [
    { id: 'ART-001', document_title: 'UUD 1945', article_number: 'Pasal 1', content: 'Negara Indonesia adalah negara kesatuan, berupa negara kesatuan republik, dengan kedaulatan ada di tangan rakyat dan dilaksanakan sepenuhnya oleh Majelis Permusyawaratan Rakyat.', domain: 'HTN', hierarchy_rank: 1, embedding_id: 'emb-001', created_at: '2024-01-10T10:00:00Z' },
    { id: 'ART-002', document_title: 'UUD 1945', article_number: 'Pasal 7', content: 'Presiden dan Wakil Presiden dipilih dalam satu pasangan oleh rakyat melalui pemilihan umum.', domain: 'HTN', hierarchy_rank: 1, embedding_id: 'emb-002', created_at: '2024-01-10T10:00:00Z' },
    { id: 'ART-003', document_title: 'UU No. 12/2011', article_number: 'Pasal 7', content: 'Peraturan Daerah tidak dapat mengatur pidana penjara dan pidana kurungan. Peraturan Daerah hanya dapat mengatur pidana denda paling banyak Rp50.000.000,00.', domain: 'HTN', hierarchy_rank: 3, embedding_id: 'emb-003', created_at: '2024-01-11T10:00:00Z' },
    { id: 'ART-004', document_title: 'UU No. 12/2011', article_number: 'Pasal 8', content: 'Hierarki perundang-undangan: 1. UUD 1945; 2. TAP MPR; 3. UU/Perppu; 4. PP; 5. Perpres; 6. Permen; 7. Perda.', domain: 'HTN', hierarchy_rank: 3, embedding_id: 'emb-004', created_at: '2024-01-11T10:00:00Z' },
    { id: 'ART-005', document_title: 'KUHP Baru (UU No. 1/2023)', article_number: 'Pasal 1', content: 'Tidak ada suatu perbuatu pun yang dapat dipidana, kecuali berdasarkan peraturan perundang-undangan yang sudah ada sebelum perbuatan itu dilakukan.', domain: 'PIDANA', hierarchy_rank: 3, embedding_id: 'emb-005', created_at: '2024-01-12T10:00:00Z' },
    { id: 'ART-006', document_title: 'KUHP Baru', article_number: 'Pasal 101', content: 'Setiap orang yang dengan sengaja mengambil milik orang lain, sebagian atau seluruhnya, dengan maksud untuk dimiliki secara melawan hukum, dipidana dengan pidana penjara paling lama 5 tahun.', domain: 'PIDANA', hierarchy_rank: 3, embedding_id: 'emb-006', created_at: '2024-01-12T10:00:00Z' },
    { id: 'ART-007', document_title: 'UU ITE', article_number: 'Pasal 27', content: 'Setiap orang dengan sengaja dan tanpa hak mendistribusikan/mentransmisikan/menyebarkan informasi bohong... dipidana penjara 6 tahun atau denda 1 miliar.', domain: 'PIDANA', hierarchy_rank: 3, embedding_id: 'emb-007', created_at: '2024-01-13T10:00:00Z' },
    { id: 'ART-008', document_title: 'KUHPerdata', article_number: 'Pasal 1320', content: 'Untuk sahnya suatu perjanjian diperlukan: 1. Sepakat; 2. Cakap; 3. Suatu hal; 4. Halalan.', domain: 'PERDATA', hierarchy_rank: 4, embedding_id: 'emb-008', created_at: '2024-01-14T10:00:00Z' },
    { id: 'ART-009', document_title: 'KUHPerdata', article_number: 'Pasal 1337', content: 'Perjanjian yang dibuat untuk hal yang tidak halal, atau bertentangan dengan ketertiban umum atau kesusilaan, adalah batal demi hukum.', domain: 'PERDATA', hierarchy_rank: 4, embedding_id: 'emb-009', created_at: '2024-01-14T10:00:00Z' },
    { id: 'ART-010', document_title: 'KUHPerdata', article_number: 'Pasal 1338', content: 'Segala perjanjian yang dibuat dengan sah bertindak sebagai undang-undang bagi mereka yang membuatnya.', domain: 'PERDATA', hierarchy_rank: 4, embedding_id: 'emb-010', created_at: '2024-01-14T10:00:00Z' },
    { id: 'ART-011', document_title: 'PP No. 5/2024', article_number: 'Pasal 15', content: 'Pemerintah Daerah wajib menyusun Rencana Aksi Daerah (RAD) perlindungan anak.', domain: 'HTN', hierarchy_rank: 4, embedding_id: 'emb-011', created_at: '2024-01-15T10:00:00Z' },
    { id: 'ART-012', document_title: 'Perpres No. 10/2024', article_number: 'Pasal 3', content: 'Pelaksanaan hak asasi manusia wajib menghormati keanekaragaman, toleransi, dan kesetaraan.', domain: 'HTN', hierarchy_rank: 5, embedding_id: 'emb-012', created_at: '2024-01-15T10:00:00Z' },
    { id: 'ART-013', document_title: 'Permenkumham No. 2/2024', article_number: 'Pasal 5', content: 'Prosedur pendaftaran Hak Kekayaan Intelektual dilakukan secara elektronik melalui sistem DJKI.', domain: 'HTN', hierarchy_rank: 6, embedding_id: 'emb-013', created_at: '2024-01-16T10:00:00Z' },
    { id: 'ART-014', document_title: 'Perda Jabar No. 12/2024', article_number: 'Pasal 8', content: 'Besaran retribusi pelayanan kesehatan rumah sakit daerah: Kelas I Rp500.000, Kelas II Rp300.000, Kelas III Rp150.000 per hari.', domain: 'HTN', hierarchy_rank: 7, embedding_id: 'emb-014', created_at: '2024-01-16T10:00:00Z' },
    { id: 'ART-015', document_title: 'Perda DKI No. 5/2023', article_number: 'Pasal 12', content: 'Wajib Pajak yang sengaja tidak mendaftarkan usahanya dipidana kurangan 1 tahun atau denda Rp100.000.000.', domain: 'HTN', hierarchy_rank: 7, embedding_id: 'emb-015', created_at: '2024-01-17T10:00:00Z' },
  ]

  total.value = articles.value.length
  stats.value = {
    totalArticles: 15,
    byDomain: { HTN: 8, PIDANA: 3, PERDATA: 4 },
    byHierarchy: { 1: 2, 3: 4, 4: 1, 5: 1, 6: 1, 7: 2 },
  }
}

function handleSearch() {
  page.value = 1
  fetchArticles()
}

function handlePageChange(newPage) {
  page.value = newPage
  fetchArticles()
}

function handlePageSizeChange(newSize) {
  pageSize.value = newSize
  page.value = 1
  fetchArticles()
}

function viewArticle(article) {
  articleDetail.value = article
  detailVisible.value = true
}

function getHierarchyLabel(rank) {
  const labels = { 1: 'UUD 1945', 2: 'TAP MPR', 3: 'UU/PERPPU', 4: 'PP', 5: 'Perpres', 6: 'Permen', 7: 'Perda' }
  return labels[rank] || `Tingkat ${rank}`
}

function getHierarchyClass(rank) {
  const classes = { 1: 'primary', 2: 'success', 3: 'info', 4: 'warning', 5: 'warning', 6: 'info', 7: 'danger' }
  return classes[rank] || 'info'
}

function getDomainClass(domain) {
  const classes = { HTN: 'primary', PIDANA: 'danger', PERDATA: 'success' }
  return classes[domain] || 'info'
}

function formatDate(dateString) {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('id-ID', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function copyArticleContent(content) {
  navigator.clipboard.writeText(content)
  ElMessage.success('Teks disalin ke clipboard')
}

function exportArticle(article) {
  const content = `# ${article.document_title} - ${article.article_number}

**Domain:** ${article.domain}
**Hierarki:** ${getHierarchyLabel(article.hierarchy_rank)}
**ID:** ${article.id}

---

${article.content}

---

*Source: Lex-DSS Legal Library*`
  const blob = new Blob([content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${article.document_title}_${article.article_number}.md`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  fetchArticles()
})
</script>

<template>
  <div class="legal-library-view">
    <div class="page-header">
      <div>
        <h1 class="page-title">Legal Library</h1>
        <p class="page-subtitle">Basis data pasal hukum Indonesia dengan pencarian semantik & vektorisasi</p>
      </div>
      <el-button type="primary" @click="fetchArticles"><el-icon><Refresh /></el-icon> Refresh</el-button>
    </div>

    <el-row :gutter="20" style="margin-bottom: 24px;">
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="stat-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 13px; color: #6b7280;">Total Pasal</span>
              <el-icon style="color: #0ea5e9;"><Document /></el-icon>
            </div>
          </template>
          <el-statistic :value="stats.totalArticles" value-style="font-size: 28px; color: #1e3a5f;" />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="stat-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 13px; color: #6b7280;">HTN</span>
              <el-icon style="color: #0ea5e9;"><Rank /></el-icon>
            </div>
          </template>
          <el-statistic :value="stats.byDomain.HTN || 0" value-style="font-size: 28px; color: #0ea5e9;" />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="stat-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 13px; color: #6b7280;">Pidana</span>
              <el-icon style="color: #dc2626;"><Warning /></el-icon>
            </div>
          </template>
          <el-statistic :value="stats.byDomain.PIDANA || 0" value-style="font-size: 28px; color: #dc2626;" />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="stat-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 13px; color: #6b7280;">Perdata</span>
              <el-icon style="color: #16a34a;"><CircleCheck /></el-icon>
            </div>
          </template>
          <el-statistic :value="stats.byDomain.PERDATA || 0" value-style="font-size: 28px; color: #16a34a;" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="card">
      <template #header>
        <div class="card-header">
          <div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: center;">
            <el-input
              v-model="searchQuery"
              placeholder="Cari pasal, UU, atau kata kunci..."
              size="small"
              prefix-icon="Search"
              clearable
              @keyup.enter="handleSearch"
              style="width: 300px;"
            />
            <el-select v-model="selectedDomain" placeholder="Domain" size="small" style="width: 200px;" clearable>
              <el-option v-for="d in domains" :key="d.value" :label="d.label" :value="d.value" />
            </el-select>
            <el-select v-model="selectedHierarchy" placeholder="Hierarki" size="small" style="width: 160px;" clearable>
              <el-option v-for="h in hierarchies" :key="h.value" :label="h.label" :value="h.value" />
            </el-select>
            <el-select v-model="sortBy" placeholder="Urutkan" size="small" style="width: 140px;">
              <el-option v-for="s in sortOptions" :key="s.value" :label="s.label" :value="s.value" />
            </el-select>
            <el-button size="small" @click="handleSearch"><el-icon><Search /></el-icon> Cari</el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="articles"
        border
        stripe
        style="width: 100%"
        row-key="id"
        @row-click="viewArticle"
        highlight-current-row
      >
        <el-table-column type="index" width="50" label="#" />
        <el-table-column prop="document_title" label="Dokumen" min-width="180">
          <template #default="scope">
            <div style="font-weight: 500;">{{ scope.row.document_title }}</div>
            <div style="font-size: 12px; color: #9ca3af;">{{ scope.row.article_number }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="domain" label="Domain" width="120">
          <template #default="scope">
            <el-tag :type="getDomainClass(scope.row.domain)" effect="plain" size="small">{{ scope.row.domain }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="hierarchy_rank" label="Hierarki" width="140">
          <template #default="scope">
            <el-tag :type="getHierarchyClass(scope.row.hierarchy_rank)" effect="plain" size="small">{{ getHierarchyLabel(scope.row.hierarchy_rank) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Konten" min-width="300" show-overflow-tooltip>
          <template #default="scope">
            {{ scope.row.content?.substring(0, 150) }}{{ scope.row.content?.length > 150 ? '...' : '' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Dibuat" width="140">
          <template #default="scope">{{ formatDate(scope.row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="Aksi" width="140" fixed="right">
          <template #default="scope">
            <el-dropdown trigger="click">
              <el-button size="small" circle><el-icon><More /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click.native.prevent="viewArticle(scope.row)"><el-icon><View /></el-icon> Lihat Detail</el-dropdown-item>
                  <el-dropdown-item @click.native.prevent="copyArticleContent(scope.row.content)"><el-icon><CopyDocument /></el-icon> Salin Teks</el-dropdown-item>
                  <el-dropdown-item @click.native.prevent="exportArticle(scope.row)"><el-icon><Download /></el-icon> Export MD</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > pageSize"
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        :page-sizes="[10, 20, 50, 100]"
        @size-change="handlePageSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>

    <el-dialog v-model="detailVisible" :title="articleDetail?.document_title" width="800px" destroy-on-close>
      <div v-if="articleDetail" class="article-detail">
        <div class="detail-header">
          <div class="detail-meta">
            <el-tag :type="getDomainClass(articleDetail.domain)" effect="plain">{{ articleDetail.domain }}</el-tag>
            <el-tag :type="getHierarchyClass(articleDetail.hierarchy_rank)" effect="plain">{{ getHierarchyLabel(articleDetail.hierarchy_rank) }}</el-tag>
            <span style="font-size: 12px; color: #9ca3af;">ID: {{ articleDetail.id }}</span>
          </div>
          <div class="detail-actions">
            <el-button size="small" @click="copyArticleContent(articleDetail.content)"><el-icon><CopyDocument /></el-icon> Salin</el-button>
            <el-button size="small" @click="exportArticle(articleDetail)"><el-icon><Download /></el-icon> Export</el-button>
          </div>
        </div>
        <el-divider />
        <div class="detail-content">
          <h3 style="font-family: 'Merriweather', serif; color: #1e3a5f; margin-bottom: 16px;">{{ articleDetail.article_number }}</h3>
          <div class="legal-text" style="font-family: 'Merriweather', serif; font-size: 15px; line-height: 1.9; color: #374151; white-space: pre-wrap;">{{ articleDetail.content }}</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'
export default {
  components: { ElMessage },
}
</script>

<style scoped>
.legal-text {
  background: #fafafa;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}
</style>