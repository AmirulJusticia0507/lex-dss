<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElCard, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElButton, ElRadioGroup, ElRadio, ElTable, ElTableColumn, ElTag, ElDivider, ElTabs, ElTabPane, ElAlert, ElDescriptions, ElDescriptionsItem, ElIcon, ElTooltip, ElDrawer, ElScrollbar, ElProgress, ElStatistic, ElRow, ElCol, ElSwitch, ElDatePicker, ElTimePicker, ElSlider, ElCollapse, ElCollapseItem } from 'element-plus'
import { DataAnalysis, Cpu, Rank, Document, Warning, CircleCheck, ArrowRight, Download, Upload, Refresh, Setting, TrendCharts, Search, Filter, History, Star, Share, More, Edit, Delete, View, CopyDocument, FullScreen } from '@element-plus/icons-vue'
import { useDSSStore } from '@/stores'
import { useLegalStore } from '@/stores'
import LegalOpinionPanel from '@/components/LegalOpinionPanel.vue'
import RiskScoreCard from '@/components/RiskScoreCard.vue'

const dssStore = useDSSStore()
const legalStore = useLegalStore()

const activeTab = ref('generate')
const generating = ref(false)
const currentOpinion = ref(null)
const currentRisk = ref(null)
const history = ref([])
const historyLoading = ref(false)

const generationForm = reactive({
  draftText: '',
  analysisType: 'comprehensive',
  domain: 'all',
  jurisdiction: 'indonesia',
  includeRiskAssessment: true,
  includeRecommendations: true,
  includeCitations: true,
  confidenceThreshold: 0.7,
  maxReferences: 10,
  language: 'id',
})

const analysisTypes = [
  { value: 'comprehensive', label: 'Komprehensif', desc: 'Full legal opinion dengan risk assessment & rekomendasi' },
  { value: 'risk-only', label: 'Risk Assessment Only', desc: 'Hanya perhitungan risk score & faktor risiko' },
  { value: 'opinion-only', label: 'Legal Opinion Only', desc: 'Hanya legal opinion & ratio decidendi' },
  { value: 'comparative', label: 'Comparative Analysis', desc: 'Perbandingan draf dengan multiple referensi' },
]

const domains = [
  { value: 'all', label: 'Semua Domain' },
  { value: 'HTN', label: 'Hukum Tata Negara & Administrasi' },
  { value: 'PIDANA', label: 'Hukum Pidana' },
  { value: 'PERDATA', label: 'Hukum Perdata' },
]

const sampleDrafts = {
  ht: `PERATURAN DAERAH PROVINSI JAWA BARAT
NOMOR 12 TAHUN 2024
TENTANG RETRIBUSI DAERAH

Pasal 1
Dalam Peraturan Daerah ini yang dimaksud dengan:
1. Retribusi Daerah adalah pembayaran yang wajib dibayarkan oleh orang atau badan atas pelayanan khusus yang diberikan oleh Pemerintah Daerah.

Pasal 8
(1) Besaran retribusi pelayanan kesehatan rumah sakit daerah ditetapkan:
a. Kelas I: Rp500.000 per hari
b. Kelas II: Rp300.000 per hari
c. Kelas III: Rp150.000 per hari

Pasal 15
(1) Wajib bayar yang tidak membayar retribusi tepat waktu dikenai sanksi administratif berupa denda 2% per bulan.
(2) Pengelola layanan yang tidak memberikan pelayanan sesuai standar dipidana kurangan 6 bulan.`,

  criminal: `DRAFT PERATURAN DAERAH TENTANG KETERTIBAN UMUM

Pasal 10
Setiap orang dilarang:
a. Membuang sampah di tempat yang tidak disediakan;
b. Mencoret-coret dinding bangunan umum;
c. Berkendara tanpa helm standar SNI.

Pasal 25
Pelanggaran ketentuan Pasal 10 huruf a dipidana dengan pidana kurangan 3 bulan atau denda Rp5.000.000.
Pelanggaran ketentuan Pasal 10 huruf b dipidana dengan pidana kurangan 6 bulan atau denda Rp10.000.000.
Pelanggaran ketentuan Pasal 10 huruf c dipidana dengan pidana kurangan 1 tahun atau denda Rp25.000.000.`,

  civil: `PERJANJIAN KERJASAMA OPERASIONAL (PKO)
ANTARA PT. INFRASTRUKTUR NUSANTARA DENGAN CV. BANGUNAN JAYA

Pasal 2 - Ruang Lingkup
Pihak Kedua melakukan konstruksi jalan tol segmen 3A sepanjang 15 km.

Pasal 7 - Force Majeure
Kecuali bencana alam, kedua pihak tidak dibebaskan dari kewajiban. Pandemi, kebijakan pemerintah, dan demonstrations tidak termasuk force majeure.

Pasal 11 - Wanprestasi
Apabila Pihak Kedua terlambat menyelesaikan pekerjaan, dikenakan denda 0.1% per hari keterlambatan dari total nilai kontrak tanpa batas maksimum.

Pasal 14 - Putusan Akhir
Segala perselisihan diselesaikan melalui Pengadilan Negeri Jakarta Pusat. Keputusan hakim bersifat final dan binding, tidak dapat dibanding atau dikasasi.`
}

async function handleGenerate() {
  const form = document.querySelector('#generationForm')
  if (!form) return

  form.validate(async (valid) => {
    if (!valid) return

    generating.value = true
    try {
      const result = await generateMockOpinion(generationForm.draftText, generationForm.analysisType)
      currentOpinion.value = result.opinion
      currentRisk.value = result.risk
      dssStore.legalOpinion = result.opinion
      dssStore.riskAssessment = result.risk
      dssStore.recommendations = result.recommendations
    } catch (error) {
      console.error('Generation failed:', error)
    } finally {
      generating.value = false
      activeTab.value = 'result'
    }
  })
}

function generateMockOpinion(text, type) {
  const opinion = {
    summary: 'Draf Perda Retribusi Daerah mengandung kontradiksi dengan hierarki perundang-undangan. Pasal 15 ayat (2) mengatur pidana kurangan yang dilarang oleh Pasal 7 UU No. 12/2011 untuk Peraturan Daerah. Disarankan revisi sanksi ke administratif/denda.',
    risk_level: 'HIGH',
    confidence_score: 0.91,
    legal_basis: [
      { id: 1, article_reference: 'Pasal 7 UU No. 12/2011', explanation: 'Peraturan Daerah tidak boleh mengatur pidana penjara/kurungan, hanya pidana denda maksimal Rp50.000.000' },
      { id: 2, article_reference: 'Pasal 18 UUD 1945', explanation: 'Otonomi daerah tidak melampaui kewenangan yang diatur undang-undang' },
      { id: 3, article_reference: 'Pasal 1337 KUHPerdata', explanation: 'Klausula yang bertentangan dengan ketertiban umum/kesusilaan batal demi hukum' },
      { id: 4, article_reference: 'Pasal 1 ayat 1 KUHP', explanation: 'Asas legalitas: tidak ada pidana tanpa undang-undang (nullum crimen sine lege)' },
    ],
    ratio_decidendi: `Berdasarkan analisis Lex Integrity Engine:

1. LEX SUPERIOR VIOLATION: Pasal 15 ayat (2) Perda mengancam "pidana kurangan 6 bulan" bagi pengelola layanan. Pasal 7 UU No. 12/2011 secara tegas melarang Peraturan Daerah mengatur pidana penjara dan pidana kurungan. Hanya pidana denda yang diperbolehkan (maksimal Rp50.000.000).

2. ASAS LEGALITAS: Penetapan pidana kurangan oleh Perda melanggar asas legalitas (Pasal 1 ayat 1 KUHP / Pasal 1 ayat 1 KUHP Baru UU No. 1/2023) karena pidana hanya dapat ditetapkan oleh Undang-Undang.

3. KETERTIBAN UMUM: Klausula "pandemi, kebijakan pemerintah, demonstrasi tidak termasuk force majeure" (Pasal 7 PKO sample) bermasalah karena mengontrakkan risiko yang di luar kendali pihak dan bertentangan dengan ketertiban umum (Pasal 1337 KUHPerdata).

4. DENDA TANPA BATAS MAKSIMUM: Denda 0.1% per hari tanpa batas maksimum (Pasal 11 PKO) tidak proporsional dan dapat dikategorikan sebagai klausula lek (onrechtmatige voorwaarde).

Kesimpulan: Draf memerlukan revisi substansial sebelum dapat disahkan.`,
    recommendations: [
      'REVISI WAJIB: Hapus pidana kurangan pada Pasal 15 ayat (2), ganti dengan sanksi administratif (denda administratif, pencabutan izin, atau penutupan sementara)',
      'SESUAIKAN DENDA: Batasi denda retribusi maksimal Rp50.000.000 sesuai Pasal 7 UU No. 12/2011',
      'REVISI FORCE MAJEURE: Tambahkan pandemi, kebijakan pemerintah, dan situasi darurat sebagai force majeure',
      'BATASI DENDA KETERLAMBATAN: Tambahkan cap maksimal denda (misal 10% nilai kontrak) agar tidak lek',
      'KLAUSULA PENYELESAIAN: Tambahkan mediasi/arbitrase sebelum pengadilan, hapus klausula "final dan binding tidak dapat dikasasi"',
      'KONSULTASI: Koordinasi dengan Kemenkumham RI dan DPRD Provinsi sebelum plenary',
    ],
  }

  const risk = {
    score: 82,
    level: 'TINGGI',
    factors: [
      { id: 1, title: 'Pelanggaran Hierarki Perundangan (Lex Superior)', description: 'Perda mengatur pidana kurangan - dilarang UU No. 12/2011', severity: 'HIGH' },
      { id: 2, title: 'Pelanggaran Asas Legalitas', description: 'Pidana hanya boleh diatur Undang-Undang (Pasal 1 KUHP)', severity: 'HIGH' },
      { id: 3, title: 'Klausula Force Majeure Tidak Adil', description: 'Mengecualikan risiko sistemik (pandemi, kebijakan pemerintah)', severity: 'MEDIUM' },
      { id: 4, title: 'Denda Tanpa Batas Maksimum (Unconscionable)', description: 'Denda 0.1%/hari tanpa cap - berpotensi lek', severity: 'MEDIUM' },
      { id: 5, title: 'Klausula Final Binding Tanpa Kasasi', description: 'Mencabut hak konstitusional banding/kasasi', severity: 'HIGH' },
      { id: 6, title: 'Retribusi Tanpa Dasar Biaya', description: 'Besaran retribusi tidak merujuk analisis biaya pelayanan', severity: 'LOW' },
    ],
    mitigation: [
      'Revisi Pasal 15: Hapus pidana kurangan, gunakan sanksi administratif bertingkat',
      'Tambahkan analisis biaya pelayanan (Cost Recovery Analysis) untuk retribusi',
      'Perbaiki klausula force majeure sesuai standar internasional (ICC)',
      'Batasi denda keterlambatan maksimal 10% nilai kontrak',
      'Hapus klausula anti-kasasi, gunakan klausula arbitrase BANI/ICC',
      'Lakukan Regulatory Impact Assessment (RIA) sebelum sidang plenary',
    ],
  }

  const recommendations = [
    { id: 1, title: 'Immediate Action Required', items: ['Hapus pidana kurangan Pasal 15(2)', 'Batasi denda retribusi'] },
    { id: 2, title: 'Contractual Revisions', items: ['Perbaiki force majeure', 'Batasi denda keterlambatan', 'Tambahkan mediasi'] },
    { id: 3, title: 'Process Compliance', items: ['RIA wajib', 'Konsultasi Kemenkumham', 'Harmonisasi akademik'] },
  ]

  return { opinion, risk, recommendations }
}

async function loadHistory() {
  historyLoading.value = true
  try {
    history.value = [
      { id: 'DSS-2024-001', title: 'Perda Retribusi Jabar', type: 'comprehensive', riskScore: 82, riskLevel: 'HIGH', date: '2024-01-15T10:30:00Z', status: 'completed' },
      { id: 'DSS-2024-002', title: 'PKO Konstruksi Tol', type: 'comparative', riskScore: 65, riskLevel: 'MEDIUM', date: '2024-01-14T14:20:00Z', status: 'completed' },
      { id: 'DSS-2024-003', title: 'Perda Ketertibum', type: 'risk-only', riskScore: 78, riskLevel: 'HIGH', date: '2024-01-13T09:15:00Z', status: 'completed' },
      { id: 'DSS-2024-004', title: 'Draft KUHP Baru', type: 'opinion-only', riskScore: 45, riskLevel: 'MEDIUM', date: '2024-01-12T16:45:00Z', status: 'completed' },
      { id: 'DSS-2024-005', title: 'Perjanjian Kerja PKWT', type: 'comprehensive', riskScore: 71, riskLevel: 'HIGH', date: '2024-01-11T11:00:00Z', status: 'completed' },
    ]
  } catch (error) {
    console.error('Failed to load history:', error)
  } finally {
    historyLoading.value = false
  }
}

function loadSampleDraft(type) {
  generationForm.draftText = sampleDrafts[type] || ''
}

function handleExportOpinion() {
  if (!currentOpinion.value) return
  const content = generateExportContent()
  const blob = new Blob([content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `DSS_Opinion_${Date.now()}.md`
  a.click()
  URL.revokeObjectURL(url)
}

function generateExportContent() {
  return `# DSS Legal Opinion

**Generated:** ${new Date().toLocaleString('id-ID')}
**Analysis Type:** ${analysisTypes.find(t => t.value === generationForm.analysisType)?.label}
**Domain:** ${domains.find(d => d.value === generationForm.domain)?.label}

---

## Executive Summary
${currentOpinion.value?.summary || 'N/A'}

## Risk Assessment
**Score:** ${currentRisk.value?.score || 0}/100
**Level:** ${currentRisk.value?.level || 'N/A'}

### Risk Factors
${currentRisk.value?.factors?.map(f => `- **${f.title}** (${f.severity}): ${f.description}`).join('\n') || 'N/A'}

### Mitigation Steps
${currentRisk.value?.mitigation?.map((m, i) => `${i+1}. ${m}`).join('\n') || 'N/A'}

## Legal Basis
${currentOpinion.value?.legal_basis?.map(b => `- **${b.article_reference}**: ${b.explanation}`).join('\n') || 'N/A'}

## Ratio Decidendi
${currentOpinion.value?.ratio_decidendi || 'N/A'}

## Recommendations
${currentOpinion.value?.recommendations?.map((r, i) => `${i+1}. ${r}`).join('\n') || 'N/A'}

---

*Generated by Lex-DSS AI Decision Support System*
`
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

function getRiskLevelClass(level) {
  const classes = { 'SANGAT TINGGI': 'very-high', 'TINGGI': 'high', 'SEDANG': 'medium', 'RENDAH': 'low' }
  return classes[level] || 'low'
}

function getRiskLevelType(level) {
  const types = { 'SANGAT TINGGI': 'danger', 'TINGGI': 'danger', 'SEDANG': 'warning', 'RENDAH': 'success' }
  return types[level] || 'info'
}

function viewHistoryItem(item) {
  console.log('View history:', item)
}

function deleteHistoryItem(item) {
  history.value = history.value.filter(h => h.id !== item.id)
}

onMounted(() => {
  loadHistory()
})
</script>

<template>
  <div class="dss-panel-view">
    <div class="page-header">
      <div>
        <h1 class="page-title">DSS Panel</h1>
        <p class="page-subtitle">AI Legal Decision Support System - Generate Legal Opinion & Risk Assessment</p>
      </div>
    </div>

    <el-card class="card" style="margin-bottom: 24px;">
      <el-tabs v-model="activeTab" type="card" @tab-click="handleTabClick">
        <el-tab-pane label="Generate Opinion" name="generate">
          <el-icon><Cpu /></el-icon>
        </el-tab-pane>
        <el-tab-pane label="Legal Opinion" name="result" :disabled="!currentOpinion">
          <el-icon><Rank /></el-icon>
        </el-tab-pane>
        <el-tab-pane label="Risk Assessment" name="risk" :disabled="!currentRisk">
          <el-icon><TrendCharts /></el-icon>
        </el-tab-pane>
        <el-tab-pane label="History" name="history">
          <el-icon><History /></el-icon>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <div v-if="activeTab === 'generate'">
      <el-row :gutter="20">
        <el-col :xs="24" :lg="12">
          <el-card class="card">
            <template #header>
              <div class="card-header">
                <span class="card-title">Konfigurasi Generasi</span>
              </div>
            </template>

            <el-form ref="generationForm" :model="generationForm" label-width="140px" class="gen-form">
              <el-form-item label="Tipe Analisis">
                <el-radio-group v-model="generationForm.analysisType" style="display: flex; flex-direction: column; gap: 8px;">
                  <el-radio v-for="type in analysisTypes" :key="type.value" :label="type.value" :style="{ border: '1px solid #e5e7eb', borderRadius: '8px', padding: '12px' }">
                    <div style="font-weight: 500;">{{ type.label }}</div>
                    <div style="font-size: 12px; color: #6b7280;">{{ type.desc }}</div>
                  </el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item label="Domain Hukum">
                <el-select v-model="generationForm.domain" placeholder="Pilih domain" style="width: 100%;" clearable>
                  <el-option v-for="d in domains" :key="d.value" :label="d.label" :value="d.value" />
                </el-select>
              </el-form-item>

              <el-form-item label="Yurisdiksi">
                <el-select v-model="generationForm.jurisdiction" placeholder="Pilih yurisdiksi" style="width: 100%;" clearable>
                  <el-option label="Indonesia" value="indonesia" />
                  <el-option label="DKI Jakarta" value="dki-jakarta" />
                  <el-option label="Provinsi Lain" value="other-province" />
                </el-select>
              </el-form-item>

              <el-divider>Opsi Output</el-divider>

              <el-form-item label="Risk Assessment">
                <el-switch v-model="generationForm.includeRiskAssessment" active-text="Ya" inactive-text="Tidak" />
              </el-form-item>

              <el-form-item label="Rekomendasi AI">
                <el-switch v-model="generationForm.includeRecommendations" active-text="Ya" inactive-text="Tidak" />
              </el-form-item>

              <el-form-item label="Sitasi Hukum">
                <el-switch v-model="generationForm.includeCitations" active-text="Ya" inactive-text="Tidak" />
              </el-form-item>

              <el-form-item label="Confidence Threshold">
                <el-slider
                  v-model="generationForm.confidenceThreshold"
                  :min="0.5"
                  :max="0.95"
                  :step="0.05"
                  show-tooltip
                  format-tooltip="v => (v * 100).toFixed(0) + '%'"
                />
                <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">{{ (generationForm.confidenceThreshold * 100).toFixed(0) }}%</div>
              </el-form-item>

              <el-form-item label="Max Referensi">
                <el-input-number v-model="generationForm.maxReferences" :min="5" :max="50" :step="5" style="width: 100%;" />
              </el-form-item>
            </el-form>
          </el-card>

          <el-card class="card">
            <template #header>
              <div class="card-header">
                <span class="card-title">Input Draf</span>
              </div>
            </template>
            <el-form ref="generationForm" :model="generationForm" label-width="0">
              <el-form-item label="Teks Draf" prop="draftText">
                <el-input
                  v-model="generationForm.draftText"
                  type="textarea"
                  :rows="12"
                  placeholder="Masukkan teks draf peraturan, perjanjian, atau dokumen hukum..."
                  show-word-limit
                  maxlength="50000"
                  style="font-family: 'Merriweather', serif; font-size: 13px;"
                />
                <template #append>
                  <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px;">
                    <el-button size="small" @click="loadSampleDraft('ht')" type="text"><el-icon><Document /></el-icon> Sample Perda</el-button>
                    <el-button size="small" @click="loadSampleDraft('criminal')" type="text"><el-icon><Warning /></el-icon> Sample Pidana</el-button>
                    <el-button size="small" @click="loadSampleDraft('civil')" type="text"><el-icon><Scale /></el-icon> Sample Perdata</el-button>
                    <el-button size="small" @click="generationForm.draftText = ''" type="text"><el-icon><Delete /></el-icon> Bersihkan</el-button>
                  </div>
                </template>
              </el-form-item>

              <el-form-item>
                <el-button type="primary" size="large" @click="handleGenerate" :loading="generating" :disabled="!generationForm.draftText.trim()" style="width: 100%;">
                  <el-icon v-if="!generating"><Cpu /></el-icon>
                  <el-icon v-else class="is-loading"><Refresh /></el-icon>
                  {{ generating ? 'Menghasilkan Legal Opinion...' : 'Generate Legal Opinion' }}
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="12">
          <el-card class="card" style="height: 100%; min-height: 600px;">
            <template #header>
              <div class="card-header">
                <span class="card-title">Preview & Quick Stats</span>
              </div>
            </template>

            <div v-if="!currentOpinion" class="empty-preview">
              <el-icon style="font-size: 64px; color: #d1d5db; margin-bottom: 16px;"><DataAnalysis /></el-icon>
              <h3 style="color: #1f2937; margin-bottom: 8px;">Belum Ada Legal Opinion</h3>
              <p style="color: #6b7280; margin-bottom: 24px;">Isi form di sebelah kiri dan klik "Generate Legal Opinion" untuk memulai analisis AI</p>

              <el-card style="width: 100%;">
                <template #header>
                  <span style="font-weight: 600;">Fitur DSS Panel</span>
                </template>
                <ul style="line-height: 2; color: #374151;">
                  <li><el-icon style="color: #16a34a; margin-right: 8px;"><CircleCheck /></el-icon> Legal Opinion dengan Ratio Decidendi</li>
                  <li><el-icon style="color: #16a34a; margin-right: 8px;"><CheckCircle /></el-icon> Risk Score (0-100) dengan faktor detail</li>
                  <li><el-icon style="color: #16a34a; margin-right: 8px;"><CheckCircle /></el-icon> Sitasi pasal hukum otomatis (RAG)</li>
                  <li><el-icon style="color: #16a34a; margin-right: 8px;"><CheckCircle /></el-icon> Rekomendasi mitigasi actionable</li>
                  <li><el-icon style="color: #16a34a; margin-right: 8px;"><CheckCircle /></el-icon> Export ke Markdown/PDF</li>
                  <li><el-icon style="color: #16a34a; margin-right: 8px;"><CheckCircle /></el-icon> History & versioning</li>
                </ul>
              </el-card>
            </div>

            <div v-else class="preview-content">
              <RiskScoreCard
                :risk-score="currentRisk?.score || 0"
                :risk-level="currentRisk?.level || 'LOW'"
                :risk-factors="currentRisk?.factors || []"
                :mitigation-steps="currentRisk?.mitigation || []"
                :size="160"
              />

              <el-divider style="margin: 20px 0;" />

              <div class="preview-stats">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-statistic :value="currentOpinion?.legal_basis?.length || 0" label="Dasar Hukum" value-style="color: #0ea5e9;" />
                  </el-col>
                  <el-col :span="12">
                    <el-statistic :value="currentOpinion?.recommendations?.length || 0" label="Rekomendasi" value-style="color: #16a34a;" />
                  </el-col>
                  <el-col :span="12">
                    <el-statistic :value="currentRisk?.factors?.filter(f => f.severity === 'HIGH').length || 0" label="Faktor High Risk" value-style="color: #dc2626;" />
                  </el-col>
                  <el-col :span="12">
                    <el-statistic :value="Math.round((currentOpinion?.confidence_score || 0) * 100)" label="Confidence" value-style="color: #c9a84c;" suffix="%" />
                  </el-col>
                </el-row>
              </div>

              <el-divider style="margin: 20px 0;" />

              <el-alert
                title="Siap untuk Review"
                :description="`Legal Opinion dengan ${currentOpinion?.legal_basis?.length || 0} dasar hukum dan ${currentOpinion?.recommendations?.length || 0} rekomendasi telah digenerate. Klik tab 'Legal Opinion' untuk review lengkap.`"
                type="success"
                show-icon
                closable
              />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div v-if="activeTab === 'result' && currentOpinion">
      <LegalOpinionPanel
        :draft-text="generationForm.draftText"
        :references="[]"
        :ai-recommendation="currentOpinion"
        :conflicts="[]"
        :loading="false"
        @export-opinion="handleExportOpinion"
      />
    </div>

    <div v-if="activeTab === 'risk' && currentRisk">
      <el-row :gutter="20">
        <el-col :xs="24" :lg="8">
          <el-card class="card">
            <template #header>
              <span class="card-title">Risk Score</span>
            </template>
            <RiskScoreCard
              :risk-score="currentRisk.score"
              :risk-level="currentRisk.level"
              :risk-factors="currentRisk.factors"
              :mitigation-steps="currentRisk.mitigation"
              :size="220"
            />
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="16">
          <el-card class="card">
            <template #header>
              <span class="card-title">Detail Faktor Risiko</span>
            </template>
            <el-table :data="currentRisk.factors" border stripe style="width: 100%">
              <el-table-column prop="title" label="Faktor Risiko" min-width="200" />
              <el-table-column prop="description" label="Deskripsi" min-width="300" show-overflow-tooltip />
              <el-table-column prop="severity" label="Severity" width="120">
                <template #default="scope">
                  <el-tag :type="getSeverityTagType(scope.row.severity)" effect="plain">{{ scope.row.severity }}</el-tag>
                </template>
              </el-table-column>
            </el-table>

            <el-divider style="margin: 20px 0;" />

            <div class="card-title" style="margin-bottom: 16px;">Langkah Mitigasi</div>
            <ol style="line-height: 2.2; color: #374151; padding-left: 20px;">
              <li v-for="(step, index) in currentRisk.mitigation" :key="index">{{ step }}</li>
            </ol>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div v-if="activeTab === 'history'">
      <el-card class="card">
        <template #header>
          <div class="card-header">
            <span class="card-title">Riwayat Analisis DSS</span>
            <el-button size="small" @click="loadHistory" :loading="historyLoading"><el-icon><Refresh /></el-icon></el-button>
          </div>
        </template>

        <el-table
          v-loading="historyLoading"
          :data="history"
          border
          stripe
          style="width: 100%"
          @row-click="viewHistoryItem"
        >
          <el-table-column prop="id" label="ID" width="150" />
          <el-table-column prop="title" label="Judul Analisis" min-width="200" />
          <el-table-column prop="type" label="Tipe" width="160">
            <template #default="scope">
              <el-tag size="small" effect="plain">{{ analysisTypes.find(t => t.value === scope.row.type)?.label || scope.row.type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="riskScore" label="Risk Score" width="120">
            <template #default="scope">
              <el-tag :type="getRiskLevelType(scope.row.riskLevel)" effect="plain">{{ scope.row.riskScore }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="riskLevel" label="Level" width="120">
            <template #default="scope">
              <el-tag :type="getRiskLevelType(scope.row.riskLevel)" effect="plain">{{ scope.row.riskLevel }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="date" label="Tanggal" width="180">
            <template #default="scope">{{ formatDate(scope.row.date) }}</template>
          </el-table-column>
          <el-table-column prop="status" label="Status" width="120">
            <template #default="scope">
              <el-tag :type="scope.row.status === 'completed' ? 'success' : 'info'" effect="plain">{{ scope.row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="Aksi" width="120" fixed="right">
            <template #default="scope">
              <el-button size="small" type="text" @click.stop="viewHistoryItem(scope.row)"><el-icon><View /></el-icon></el-button>
              <el-button size="small" type="text" danger @click.stop="deleteHistoryItem(scope.row)"><el-icon><Delete /></el-icon></el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    handleTabClick(tab) {
      if (tab.name === 'result' && !this.currentOpinion) {
        this.activeTab = 'generate'
      }
      if (tab.name === 'risk' && !this.currentRisk) {
        this.activeTab = 'generate'
      }
    },
    getSeverityTagType(severity) {
      const types = { HIGH: 'danger', MEDIUM: 'warning', LOW: 'success' }
      return types[severity] || 'info'
    },
  },
}
</script>

<style scoped>
.gen-form .el-form-item {
  margin-bottom: 20px;
}

.empty-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  height: 100%;
}

.preview-content {
  padding: 10px 0;
}

.preview-stats {
  padding: 10px 0;
}
</style>