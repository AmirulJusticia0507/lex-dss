<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElForm, ElFormItem, ElInput, ElButton, ElSelect, ElOption, ElRadioGroup, ElRadio, ElCard, ElTable, ElTableColumn, ElTag, ElDivider, ElTabs, ElTabPane, ElAlert, ElSteps, ElStep, ElDescriptions, ElDescriptionsItem, ElIcon, ElTooltip, ElPopover, ElDrawer, ElScrollbar } from 'element-plus'
import { Search, Delete, Document, Warning, CircleCheck, CircleClose, QuestionFilled, ArrowRight, Upload, Download, Refresh, Setting } from '@element-plus/icons-vue'
import { useLegalStore } from '@/stores'
import ConflictMatrix from '@/components/ConflictMatrix.vue'
import LegalOpinionPanel from '@/components/LegalOpinionPanel.vue'
import RiskScoreCard from '@/components/RiskScoreCard.vue'

const legalStore = useLegalStore()

const activeStep = ref(1)
const analysisId = ref(null)
const draftText = ref('')
const analysisType = ref('comprehensive')
const selectedDomain = ref('all')
const jurisdiction = ref('indonesia')

const analysisResult = ref(null)
const conflicts = ref([])
const references = ref([])
const aiRecommendation = ref(null)
const riskAssessment = ref(null)
const loading = ref(false)
const analyzing = ref(false)

const draftRules = {
  draftText: [
    { required: true, message: 'Silakan masukkan teks draf hukum', trigger: 'blur' },
    { min: 50, message: 'Teks draf minimal 50 karakter', trigger: 'blur' },
  ],
}

const guideSteps = [
  { title: 'Preprocessing', desc: 'Teks draf dibersihkan dan dipecah per pasal.' },
  { title: 'Lex Integrity Check', desc: 'Kontradiksi hierarki & norma dideteksi otomatis.' },
  { title: 'Vector Search (RAG)', desc: 'Pasal hukum relevan diambil dari basis data.' },
  { title: 'AI Reasoning', desc: 'Legal opinion & ratio decidendi disintesis LLM.' },
  { title: 'Risk Assessment', desc: 'Risk score 0-100 dan rekomendasi mitigasi dihitung.' },
]

const analysisTypes = [
  { value: 'comprehensive', label: 'Komprehensif', description: 'Analisis menyeluruh: hierarki, kontradiksi, rekomendasi AI' },
  { value: 'hierarchy', label: 'Hierarki Saja', description: 'Hanya cek hierarki perundang-undangan (Lex Superior)' },
  { value: 'contradiction', label: 'Kontradiksi', description: 'Fokus deteksi kontradiksi langsung antar pasal' },
  { value: 'criminal', label: 'Hukum Pidana', description: 'Analisis khusus asas legalitas & tumpang tindih sanksi' },
  { value: 'civil', label: 'Hukum Perdata', description: 'Analisis syarat sah perjanjian & klausula baku' },
]

const domains = [
  { value: 'all', label: 'Semua Domain' },
  { value: 'HTN', label: 'Hukum Tata Negara & Administrasi' },
  { value: 'PIDANA', label: 'Hukum Pidana' },
  { value: 'PERDATA', label: 'Hukum Perdata' },
]

const sampleDrafts = {
  ht: `PERATURAN DAERAH KOTA JAKARTA
NOMOR 5 TAHUN 2023
TENTANG PAJAK DAERAH

Pasal 1
Dalam Peraturan Daerah ini yang dimaksud dengan:
1. Pajak Daerah adalah pajak yang dikenakan oleh Pemerintah Daerah berdasarkan Undang-Undang.
2. Wajib Pajak adalah orang pribadi atau badan yang berdasarkan peraturan perundang-undangan wajib membayar pajak.

Pasal 5
(1) Tarif Pajak Hotel ditetapkan sebesar 15% dari jumlah pembayaran.
(2) Tarif Pajak Restoran ditetapkan sebesar 15% dari jumlah pembayaran.
(3) Tarif Pajak Hiburan ditetapkan sebesar 25% dari jumlah pembayaran.

Pasal 12
(1) Wajib Pajak yang tidak membayar pajak tepat waktu dikenakan sanksi administratif berupa denda 2% per bulan.
(2) Wajib Pajak yang sengaja tidak mendaftarkan usahanya dipidana kurangan 1 tahun atau denda Rp100.000.000.

Pasal 15
Peraturan Daerah ini mulai berlaku pada tanggal diundangkan.`,

  criminal: `DRAFT KITAB UNDANG-UNDANG HUKUM PIDANA (KUHP) BARU

Pasal 101
Setiap orang yang dengan sengaja mengambil milik orang lain, sebagian atau seluruhnya, dengan maksud untuk dimiliki secara melawan hukum, dipidana dengan pidana penjara paling lama 5 (lima) tahun atau denda paling banyak Rp500.000.000,00 (lima ratus juta rupiah).

Pasal 102
Setiap orang yang dengan sengaja dan melawan hukum memasuki tempat tinggal orang lain atau tempat yang dijaga, dipidana dengan pidana penjara paling lama 1 (satu) tahun atau denda paling banyak Rp100.000.000,00 (seratus juta rupiah).

Pasal 280
Setiap orang yang dengan sengaja melanggar Undang-Undang tentang Informasi dan Transaksi Elektronik dengan cara menyebarkan informasi bohong, dipidana dengan pidana penjara paling lama 6 (enam) tahun atau denda paling banyak Rp1.000.000.000,00 (satu miliar rupiah).`,

  civil: `PERJANJIAN KERJA WAKTU TERTENTU (PKWT)
ANTARA PT. MAJU JAYA DENGAN BUDI SANTOSO

Pasal 1 - Ruang Lingkup Pekerjaan
Pekerja bertugas sebagai Operator Mesin di bagian Produksi dengan jam kerja 8 jam/hari, 6 hari/minggu.

Pasal 5 - Hak dan Kewajiban Pekerja
Pekerja wajib mematuhi segala peraturan perusahaan dan perintah atasan. Pekerja tidak berhak mengajukan gugatan apapun terhadap Perusahaan atas alasan pemutusan hubungan kerja (klausula waiver hak).

Pasal 8 - Gaji dan Tunjangan
Gaji pokok sebulan Rp4.500.000. Tidak ada tunjangan hari raya, transport, atau makan.

Pasal 12 - Pemutusan Hubungan Kerja
Perusahaan berhak memutuskan hubungan kerja sewaktu-waktu tanpa alasan dan tanpa pemberitahuan sebelumnya. Pekerja tidak berhak menuntut ganti rugi, pesangon, atau uang pengupahan hak lainnya.`
}

async function handleAnalyze() {
  const form = document.querySelector('#draftForm')
  if (!form) return

  form.validate((valid) => {
    if (!valid) return

    analyzing.value = true
    activeStep.value = 2

    setTimeout(async () => {
      try {
        const mockResult = generateMockAnalysis(draftText.value, analysisType.value)
        analysisResult.value = mockResult
        conflicts.value = mockResult.conflicts || []
        references.value = mockResult.references || []
        aiRecommendation.value = mockResult.ai_recommendation || null
        riskAssessment.value = mockResult.risk_assessment || null
        analysisId.value = 'ANL-' + Date.now()
        activeStep.value = 3
      } catch (error) {
        console.error('Analysis failed:', error)
        activeStep.value = 1
      } finally {
        analyzing.value = false
      }
    }, 2000)
  })
}

function generateMockAnalysis(text, type) {
  const conflicts = [
    {
      id: 'CONF-001',
      conflict_type: 'LEX_SUPERIOR',
      severity: 'HIGH',
      description: 'Pasal 12 ayat (2) Perda mengatur pidana penjara, bertentangan dengan Pasal 7 UU No. 12/2011 yang melarang Perda mengatur pidana penjara',
      source_article: { id: 'ART-001', document_title: 'UU No. 12/2011', article_number: 'Pasal 7', content: 'Peraturan Daerah tidak dapat mengatur pidana penjara', domain: 'HTN', hierarchy_rank: 3 },
      target_article: { id: 'ART-002', document_title: 'Perda No. 5/2023', article_number: 'Pasal 12', content: 'Wajib Pajak yang sengaja tidak mendaftarkan usahanya dipidana kurangan 1 tahun', domain: 'HTN', hierarchy_rank: 5 },
      created_at: new Date().toISOString(),
    },
    {
      id: 'CONF-002',
      conflict_type: 'DIRECT_CONTRADICTION',
      severity: 'HIGH',
      description: 'Klausula waiver hak pada Pasal 5 bertentangan dengan Pasal 1320 KUHPerdata tentang syarat sah perjanjian',
      source_article: { id: 'ART-003', document_title: 'KUHPerdata', article_number: 'Pasal 1320', content: 'Untuk sahnya suatu perjanjian diperlukan: 1. Sepakat; 2. Cakap; 3. Suatu hal; 4. Halalan', domain: 'PERDATA', hierarchy_rank: 4 },
      target_article: { id: 'ART-004', document_title: 'PKWT Draft', article_number: 'Pasal 5', content: 'Pekerja tidak berhak mengajukan gugatan apapun terhadap Perusahaan (klausula waiver hak)', domain: 'PERDATA', hierarchy_rank: 6 },
      created_at: new Date().toISOString(),
    },
    {
      id: 'CONF-003',
      conflict_type: 'LEX_SPECIALIS',
      severity: 'MEDIUM',
      description: 'Pasal 280 Draft KUHP mengatur sanksi penyebaran informasi bohong, tumpang tindih dengan Pasal 27 UU ITE',
      source_article: { id: 'ART-005', document_title: 'UU ITE', article_number: 'Pasal 27', content: 'Setiap orang sengaja menyebarkan informasi bohong... dipidana penjara 6 tahun', domain: 'PIDANA', hierarchy_rank: 3 },
      target_article: { id: 'ART-006', document_title: 'Draft KUHP Baru', article_number: 'Pasal 280', content: 'Setiap orang sengaja melanggar UU ITE dengan menyebarkan informasi bohong dipidana 6 tahun', domain: 'PIDANA', hierarchy_rank: 3 },
      created_at: new Date().toISOString(),
    },
  ]

  const references = [
    { id: 'REF-001', document_title: 'UU No. 12/2011', article_number: 'Pasal 7', content: 'Peraturan Daerah tidak dapat mengatur pidana penjara dan pidana kurungan.', domain: 'HTN', hierarchy_rank: 3, similarity_score: 0.95 },
    { id: 'REF-002', document_title: 'KUHPerdata', article_number: 'Pasal 1320', content: 'Untuk sahnya suatu perjanjian diperlukan: 1. Sepakat; 2. Cakap; 3. Suatu hal; 4. Halalan.', domain: 'PERDATA', hierarchy_rank: 4, similarity_score: 0.88 },
    { id: 'REF-003', document_title: 'KUHPerdata', article_number: 'Pasal 1337', content: 'Perjanjian yang dibuat untuk hal yang tidak halal, atau bertentangan dengan ketertiban umum atau kesusilaan, adalah batal demi hukum.', domain: 'PERDATA', hierarchy_rank: 4, similarity_score: 0.82 },
    { id: 'REF-004', document_title: 'UU ITE', article_number: 'Pasal 27', content: 'Setiap orang dengan sengaja dan tanpa hak mendistribusikan/mentransmisikan/menyebarkan informasi bohong...', domain: 'PIDANA', hierarchy_rank: 3, similarity_score: 0.92 },
    { id: 'REF-005', document_title: 'UUD 1945', article_number: 'Pasal 28D', content: 'Setiap orang berhak atas pengakuan, jaminan, perlindungan, dan kepastian hukum yang adil serta perlakuan yang sama di hadapan hukum.', domain: 'HTN', hierarchy_rank: 1, similarity_score: 0.75 },
  ]

  const aiRecommendation = {
    summary: 'Draf Perda Pajak Daerah mengandung kontradiksi serius dengan hierarki perundang-undangan. Pasal 12 ayat (2) mengatur pidana penjara yang dilarang oleh UU No. 12/2011. Disarankan revisi sanksi ke pidana denda atau administratif.',
    risk_level: 'HIGH',
    confidence_score: 0.92,
    legal_basis: [
      { id: 1, article_reference: 'Pasal 7 UU No. 12/2011', explanation: 'Perda tidak boleh mengatur pidana penjara/kurungan' },
      { id: 2, article_reference: 'Pasal 1320 KUHPerdata', explanation: 'Syarat sah perjanjian tidak boleh dikecualikan' },
      { id: 3, article_reference: 'Pasal 1 ayat 1 KUHP', explanation: 'Asas legalitas: tidak ada pidana tanpa undang-undang' },
    ],
    ratio_decidendi: 'Berdasarkan asas Lex Superior Derogat Legi Inferiori (Pasal 7 UU No. 12/2011), Peraturan Daerah tidak memiliki kewenangan mengatur pidana penjara. Sanksi pidana hanya dapat diatur oleh Undang-Undang. Klausula waiver hak dalam perjanjian kerja bertentangan dengan ketertiban umum (Pasal 1337 KUHPerdata) dan syarat sah perjanjian (Pasal 1320 KUHPerdata).',
    recommendations: [
      'Hapus ketentuan pidana penjara pada Pasal 12 ayat (2), ganti dengan sanksi administratif/denda',
      'Hapus klausula waiver hak (Pasal 5), tambahkan klausula penyelesaian perselisihan via mediasi/arbitrase',
      'Tambahkan tunjangan hari raya (THR) minimal sesuai UU No. 13/2003',
      'Perpanjang masa pemberitahuan PHK minimal 30 hari sesuai UU Cipta Kerja',
      'Konsultasikan revisi dengan Kemenkumham dan DPRD setempat',
    ],
  }

  const riskAssessment = {
    score: 78,
    level: 'TINGGI',
    factors: [
      { id: 1, title: 'Pelanggaran Hierarki Perundangan', description: 'Perda mengatur pidana penjara (dilarang UU No. 12/2011)', severity: 'HIGH' },
      { id: 2, title: 'Klausula Tidak Sah Perjanjian', description: 'Waiver hak pekerja bertentangan Pasal 1320 & 1337 KUHPerdata', severity: 'HIGH' },
      { id: 3, title: 'Tumpang Tindih Sanksi Pidana', description: 'Pasal 280 Draft KUHP overlap dengan UU ITE', severity: 'MEDIUM' },
      { id: 4, title: 'Ketidaksesuaian Standar Buruh', description: 'Gaji di bawah UMK, tidak ada THR, PHK sembarangan', severity: 'MEDIUM' },
    ],
    mitigation: [
      'Revisi Pasal 12: hapus pidana penjara, gunakan sanksi administratif',
      'Revisi Pasal 5: hapus klausula waiver, tambahkan mekanisme bande',
      'Harmonisasi Pasal 280 dengan UU ITE via lex specialis',
      'Sesuaikan gaji & tunjangan dengan UU Cipta Kerja & Peraturan Menteri',
    ],
  }

  return { conflicts, references, ai_recommendation: aiRecommendation, risk_assessment: riskAssessment }
}

function loadSampleDraft(type) {
  draftText.value = sampleDrafts[type] || ''
}

function handleNodeClick(node) {
  console.log('Node clicked:', node)
}

function handleReferenceClick(ref) {
  console.log('Reference clicked:', ref)
}

function handleConflictClick(conflict) {
  console.log('Conflict clicked:', conflict)
}

function handleExportOpinion() {
  const content = generateExportContent()
  const blob = new Blob([content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `Legal_Opinion_${analysisId.value}_${new Date().toISOString().split('T')[0]}.md`
  a.click()
  URL.revokeObjectURL(url)
}

function generateExportContent() {
  return `# Legal Opinion - ${analysisId.value}

**Tanggal:** ${new Date().toLocaleDateString('id-ID')}
**Tipe Analisis:** ${analysisTypes.find(t => t.value === analysisType.value)?.label}
**Domain:** ${domains.find(d => d.value === selectedDomain.value)?.label}

---

## Executive Summary
${aiRecommendation.value?.summary || 'Tidak ada ringkasan'}

---

## Risk Assessment
**Score:** ${riskAssessment.value?.score || 0}/100
**Level:** ${riskAssessment.value?.level || 'UNKNOWN'}

### Faktor Risiko
${riskAssessment.value?.factors?.map(f => `- **${f.title}** (${f.severity}): ${f.description}`).join('\n') || 'Tidak ada'}

### Mitigasi
${riskAssessment.value?.mitigation?.map((m, i) => `${i+1}. ${m}`).join('\n') || 'Tidak ada'}

---

## Dasar Hukum
${aiRecommendation.value?.legal_basis?.map(b => `- **${b.article_reference}**: ${b.explanation}`).join('\n') || 'Tidak ada'}

---

## Ratio Decidendi
${aiRecommendation.value?.ratio_decidendi || 'Tidak ada'}

---

## Rekomendasi
${aiRecommendation.value?.recommendations?.map((r, i) => `${i+1}. ${r}`).join('\n') || 'Tidak ada'}

---

## Kontradiksi Terdeteksi
${conflicts.value.map(c => `### ${c.conflict_type} (${c.severity})
**Sumber:** ${c.source_article?.document_title} - ${c.source_article?.article_number}
**Target:** ${c.target_article?.document_title} - ${c.target_article?.article_number}
**Deskripsi:** ${c.description}
`).join('\n')}

---

*Generated by Lex-DSS AI Legal Decision Support System*
`
}

function resetAnalysis() {
  activeStep.value = 1
  analysisResult.value = null
  conflicts.value = []
  references.value = []
  aiRecommendation.value = null
  riskAssessment.value = null
  analysisId.value = null
}

function getConflictTypeLabel(type) {
  const labels = { LEX_SUPERIOR: 'Lex Superior', LEX_SPECIALIS: 'Lex Specialis', LEX_POSTERIOR: 'Lex Posterior', DIRECT_CONTRADICTION: 'Direct Contradiction' }
  return labels[type] || type
}

function getConflictTypeClass(type) {
  return `conflict-type-badge ${type.toLowerCase().replace('_', '-')}`
}

function getSeverityType(severity) {
  const types = { HIGH: 'danger', MEDIUM: 'warning', LOW: 'success' }
  return types[severity] || 'info'
}

onMounted(() => {
  draftText.value = sampleDrafts.ht
})
</script>

<template>
  <div class="conflict-checker-view mx-auto w-full max-w-[1600px] space-y-6">
    <div class="page-header rounded-2xl border border-slate-200/80 bg-white px-6 py-5 shadow-sm">
      <div>
        <h1 class="page-title">Conflict Checker</h1>
        <p class="page-subtitle">Analisis kontradiksi norma hukum terhadap draf peraturan/perjanjian</p>
      </div>
    </div>

    <el-card class="card" style="margin-bottom: 24px;">
      <el-steps :active="activeStep" finish-status="success" class="analysis-steps">
        <el-step title="Input Draf" description="Masukkan teks draf hukum" />
        <el-step title="Analisis" description="Lex Integrity Engine memproses" />
        <el-step title="Hasil" description="Legal Opinion & Risk Score" />
      </el-steps>
    </el-card>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <el-card class="card">
          <template #header>
            <div class="card-header">
              <span class="card-title">1. Input Draf Hukum</span>
            </div>
          </template>

          <el-form ref="draftForm" :model="draftForm" :rules="draftRules" label-width="132px" class="draft-form">
            <el-form-item label="Tipe Analisis" prop="analysisType">
              <el-select v-model="analysisType" placeholder="Pilih tipe analisis" style="width: 100%;" clearable>
                <el-option v-for="type in analysisTypes" :key="type.value" :label="type.label" :value="type.value">
                  <div style="display: flex; flex-direction: column;">
                    <span style="font-weight: 500;">{{ type.label }}</span>
                    <span style="font-size: 11px; color: #9ca3af;">{{ type.description }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>

            <el-form-item label="Domain Hukum" prop="domain">
              <el-select v-model="selectedDomain" placeholder="Pilih domain" style="width: 100%;" clearable>
                <el-option v-for="domain in domains" :key="domain.value" :label="domain.label" :value="domain.value" />
              </el-select>
            </el-form-item>

            <el-form-item label="Yurisdiksi" prop="jurisdiction">
              <el-select v-model="jurisdiction" placeholder="Pilih yurisdiksi" style="width: 100%;" clearable>
                <el-option label="Indonesia" value="indonesia" />
                <el-option label="DKI Jakarta" value="dki-jakarta" />
                <el-option label="Provinsi Lain" value="other-province" />
              </el-select>
            </el-form-item>

            <el-form-item label="Teks Draf" prop="draftText">
              <el-input
                v-model="draftText"
                type="textarea"
                :rows="15"
                placeholder="Masukkan teks draf peraturan, perjanjian, atau dokumen hukum di sini..."
                show-word-limit
                maxlength="50000"
                style="font-family: 'Merriweather', serif; font-size: 13px;"
              />
              <template #append>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                  <el-button size="small" @click="loadSampleDraft('ht')" type="text"><el-icon><Document /></el-icon> Sample Perda</el-button>
                  <el-button size="small" @click="loadSampleDraft('criminal')" type="text"><el-icon><Warning /></el-icon> Sample Pidana</el-button>
                  <el-button size="small" @click="loadSampleDraft('civil')" type="text"><el-icon><Rank /></el-icon> Sample Perdata</el-button>
                  <el-button size="small" @click="draftText = ''" type="text"><el-icon><Delete /></el-icon> Bersihkan</el-button>
                </div>
              </template>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" size="large" @click="handleAnalyze" :loading="analyzing" :disabled="activeStep > 1" style="width: 100%;">
                <el-icon v-if="!analyzing"><Search /></el-icon>
                <el-icon v-else class="is-loading"><Refresh /></el-icon>
                {{ analyzing ? 'Menganalisis...' : 'Mulai Analisis' }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card v-if="activeStep === 1" class="card">
          <template #header>
            <span class="card-title">Contoh Cepat</span>
          </template>
          <div class="quick-list">
            <el-radio-group v-model="analysisType" class="quick-group">
              <el-radio v-for="type in analysisTypes" :key="type.value" :label="type.value" class="quick-option">
                <div class="quick-title">{{ type.label }}</div>
                <div class="quick-desc">{{ type.description }}</div>
              </el-radio>
            </el-radio-group>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card class="card h-full-side">
          <template #header>
            <div class="card-header">
              <span class="card-title">2. Proses Analisis</span>
              <el-tag v-if="analyzing" type="info">Processing</el-tag>
              <el-tag v-else-if="activeStep === 3" type="success">Selesai</el-tag>
            </div>
          </template>

          <div v-if="activeStep === 1" class="guide">
            <h3 class="guide-title">Cara Kerja Analisis</h3>
            <p class="guide-desc">
              Lex Integrity Engine membandingkan draf Anda dengan basis data hukum
              untuk mendeteksi kontradiksi norma dan hierarki.
            </p>
            <ol class="guide-steps">
              <li v-for="(s, i) in guideSteps" :key="i">
                <span class="guide-num">{{ i + 1 }}</span>
                <div>
                  <div class="guide-step-title">{{ s.title }}</div>
                  <div class="guide-step-desc">{{ s.desc }}</div>
                </div>
              </li>
            </ol>
          </div>

          <div v-else-if="analyzing" class="analysis-progress">
            <div class="progress-step" v-for="(step, index) in progressSteps" :key="step.name" :class="{ active: index === currentProgressIndex, completed: index < currentProgressIndex }">
              <div class="step-icon">
                <el-icon v-if="index < currentProgressIndex"><CircleCheck /></el-icon>
                <el-icon v-else-if="index === currentProgressIndex"><Refresh class="is-loading" /></el-icon>
                <el-icon v-else><QuestionFilled /></el-icon>
              </div>
              <div class="step-info">
                <div class="step-name">{{ step.name }}</div>
                <div class="step-desc">{{ step.desc }}</div>
              </div>
            </div>
          </div>

          <div v-else-if="activeStep === 3 && analysisResult" class="analysis-summary">
            <el-alert title="Analisis Selesai" type="success" show-icon closable @close="resetAnalysis" />
            <el-descriptions border column="1" style="margin-top: 16px;">
              <el-descriptions-item label="ID Analisis">{{ analysisId }}</el-descriptions-item>
              <el-descriptions-item label="Tipe Analisis">{{ analysisTypes.find(t => t.value === analysisType)?.label }}</el-descriptions-item>
              <el-descriptions-item label="Domain">{{ domains.find(d => d.value === selectedDomain)?.label }}</el-descriptions-item>
              <el-descriptions-item label="Kontradiksi Ditemukan">{{ conflicts.length }}</el-descriptions-item>
              <el-descriptions-item label="Referensi Hukum">{{ references.length }}</el-descriptions-item>
              <el-descriptions-item label="Risk Score">{{ riskAssessment?.score || 0 }}/100 ({{ riskAssessment?.level || 'UNKNOWN' }})</el-descriptions-item>
            </el-descriptions>
            <div style="margin-top: 16px; display: flex; gap: 12px;">
              <el-button type="primary" @click="activeStep = 3" style="flex: 1;">
                <el-icon><ArrowRight /></el-icon> Lihat Hasil Lengkap
              </el-button>
              <el-button @click="resetAnalysis">
                <el-icon><Refresh /></el-icon> Analisis Baru
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="activeStep === 3 && analysisResult" class="card" style="margin-top: 24px;">
      <template #header>
        <div class="card-header">
          <span class="card-title">3. Hasil Analisis & Legal Opinion</span>
          <div style="display: flex; gap: 8px;">
            <el-button size="small" @click="handleExportOpinion"><el-icon><Download /></el-icon> Export Opinion</el-button>
            <el-button size="small" type="primary" @click="resetAnalysis"><el-icon><Refresh /></el-icon> Analisis Baru</el-button>
          </div>
        </div>
      </template>

      <LegalOpinionPanel
        :draft-text="draftText"
        :references="references"
        :ai-recommendation="aiRecommendation"
        :conflicts="conflicts"
        :loading="false"
        @reference-click="handleReferenceClick"
        @conflict-click="handleConflictClick"
        @export-opinion="handleExportOpinion"
      />
    </el-card>
  </div>
</template>

<script>
export default {
  data() {
    return {
      draftForm: {},
      progressSteps: [
        { name: 'Preprocessing', desc: 'Membersihkan & memparsing teks draf' },
        { name: 'Lex Integrity Check', desc: 'Mendeteksi kontradiksi hierarki & norma' },
        { name: 'Vector Search', desc: 'Mencari pasal hukum relevan (RAG)' },
        { name: 'AI Reasoning', desc: 'LLM mensintesis legal opinion' },
        { name: 'Risk Assessment', desc: 'Menghitung risk score & rekomendasi' },
      ],
      currentProgressIndex: 0,
    }
  },
  mounted() {
    this.simulateProgress()
  },
  methods: {
    simulateProgress() {
      const interval = setInterval(() => {
        if (this.currentProgressIndex < this.progressSteps.length - 1) {
          this.currentProgressIndex++
        } else {
          clearInterval(interval)
        }
      }, 400)
    },
  },
}
</script>

<style scoped>
.analysis-steps {
  margin: 0 -24px;
  padding: 0 24px;
  border-radius: 0;
}

.h-full-side {
  height: 100%;
  min-height: 560px;
}

.guide {
  padding: 4px 2px;
}

.guide-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--legal-dark);
  margin: 0 0 6px;
}

.guide-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.65;
  margin: 0 0 20px;
}

.guide-steps {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.guide-steps li {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.guide-num {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--stat-primary-soft);
  color: var(--legal-dark);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.guide-step-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.guide-step-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-top: 2px;
}

.quick-list {
  padding: 16px;
}

.quick-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.quick-option {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 12px 14px;
  margin: 0 !important;
  height: auto;
  align-items: flex-start;
  transition: all var(--transition-normal);
}

.quick-option:hover {
  border-color: var(--primary-color);
  background: var(--bg-secondary);
}

.quick-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
}

.quick-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-top: 2px;
}

.draft-form .el-form-item {
  margin-bottom: 20px;
}

.analysis-progress {
  padding: 20px 0;
}

.progress-step {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px 0;
  position: relative;
}

.progress-step:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 11px;
  top: 40px;
  bottom: 0;
  width: 2px;
  background: #e5e7eb;
}

.progress-step.completed::before {
  background: #16a34a;
}

.progress-step.active::before {
  background: #0ea5e9;
}

.step-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  color: #9ca3af;
  flex-shrink: 0;
  z-index: 1;
}

.progress-step.completed .step-icon {
  background: #16a34a;
  color: white;
}

.progress-step.active .step-icon {
  background: #0ea5e9;
  color: white;
}

.step-info {
  flex: 1;
}

.step-name {
  font-weight: 500;
  color: #1f2937;
}

.step-desc {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 2px;
}

.progress-step.completed .step-name,
.progress-step.completed .step-desc {
  color: #16a34a;
}

.progress-step.active .step-name,
.progress-step.active .step-desc {
  color: #0ea5e9;
}

.analysis-summary {
  padding: 20px 0;
}
</style>
