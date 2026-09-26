<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElForm, ElFormItem, ElInput, ElButton, ElSelect, ElOption, ElRadioGroup, ElRadio, ElCard, ElTag, ElAlert, ElSteps, ElStep, ElDescriptions, ElDescriptionsItem, ElIcon } from 'element-plus'
import { Search, Delete, Document, Warning, ArrowRight, Download, Refresh, Rank } from '@element-plus/icons-vue'
import { useLegalStore } from '@/stores'
import { showToast } from '@/utils/alerts'
import LegalOpinionPanel from '@/components/LegalOpinionPanel.vue'

const legalStore = useLegalStore()

const activeStep = ref(1)
const analysisId = ref(null)
const draftFormRef = ref(null)
const draftText = ref('')
const analysisType = ref('comprehensive')
const selectedDomain = ref('all')
const jurisdiction = ref('indonesia')

const analysisResult = ref(null)
const conflicts = ref([])
const references = ref([])
const aiRecommendation = ref(null)
const riskAssessment = ref(null)
const analyzing = ref(false)

const formModel = computed(() => ({
  draftText: draftText.value,
  analysisType: analysisType.value,
  domain: selectedDomain.value,
  jurisdiction: jurisdiction.value,
}))

const draftRules = {
  draftText: [
    { required: true, message: 'Silakan masukkan teks draf hukum', trigger: 'blur' },
    { min: 50, message: 'Teks draf minimal 50 karakter', trigger: 'blur' },
  ],
  analysisType: [{ required: true, message: 'Silakan pilih tipe analisis', trigger: 'change' }],
}

const guideSteps = [
  { title: 'Pencarian Norma', desc: 'Draf digunakan untuk mencari pasal yang relevan di basis data hukum.' },
  { title: 'Lex Integrity Check', desc: 'Mesin membandingkan isi draf dengan norma kandidat yang ditemukan.' },
  { title: 'AI Reasoning', desc: 'Temuan dan referensi menjadi konteks rekomendasi hukum.' },
  { title: 'Risk Assessment', desc: 'Skor risiko dihitung dari temuan dan dilengkapi langkah mitigasi.' },
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
  if (!draftFormRef.value || analyzing.value) return

  const valid = await draftFormRef.value.validate().catch(() => false)
  if (!valid) return

  analyzing.value = true
  activeStep.value = 2

  try {
    const result = await legalStore.analyzeConflict({
      draft_text: draftText.value.trim(),
      analysis_type: analysisType.value,
      domain: selectedDomain.value === 'all' ? null : selectedDomain.value,
      jurisdiction: jurisdiction.value,
    })

    analysisResult.value = result
    conflicts.value = result.conflicts || []
    references.value = result.references || []
    aiRecommendation.value = result.ai_recommendation || null
    riskAssessment.value = result.risk_assessment || null
    analysisId.value = result.analysis_id
    activeStep.value = 3
    showToast('success', 'Analisis berhasil diselesaikan')
  } catch (error) {
    const detail = error.response?.data?.detail
    const message = typeof detail === 'string'
      ? detail
      : detail?.message || error.response?.data?.message || error.message || 'Analisis gagal dijalankan'
    console.error('Analysis failed:', error)
    activeStep.value = 1
    showToast('error', message)
  } finally {
    analyzing.value = false
  }
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

          <el-form ref="draftFormRef" :model="formModel" :rules="draftRules" label-width="132px" class="draft-form">
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

            <el-form-item label="Teks Draf" prop="draftText" class="draft-text-item">
              <div class="draft-editor">
                <el-input
                  v-model="draftText"
                  class="draft-textarea"
                  type="textarea"
                  :rows="13"
                  placeholder="Tempelkan teks draf peraturan, perjanjian, atau dokumen hukum di sini..."
                  show-word-limit
                  maxlength="50000"
                />
                <div class="draft-toolbar">
                  <div class="draft-samples" aria-label="Muat contoh draf">
                    <span class="draft-toolbar-label">Isi contoh:</span>
                    <el-button size="small" link @click="loadSampleDraft('ht')"><el-icon><Document /></el-icon> Perda</el-button>
                    <el-button size="small" link @click="loadSampleDraft('criminal')"><el-icon><Warning /></el-icon> Pidana</el-button>
                    <el-button size="small" link @click="loadSampleDraft('civil')"><el-icon><Rank /></el-icon> Perdata</el-button>
                  </div>
                  <el-button size="small" link type="danger" :disabled="!draftText" @click="draftText = ''">
                    <el-icon><Delete /></el-icon> Bersihkan
                  </el-button>
                </div>
                <p class="draft-helper">Minimal 50 karakter. Teks draf tetap bisa diedit setelah memilih contoh.</p>
              </div>
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
            <p class="quick-hint">Pilih fokus analisis. Pilihan ini akan ikut terkirim saat draf dianalisis.</p>
            <el-radio-group v-model="analysisType" class="quick-group">
              <el-radio v-for="type in analysisTypes" :key="type.value" :label="type.value" class="quick-option">
                <span class="quick-copy">
                  <span class="quick-title">{{ type.label }}</span>
                  <span class="quick-desc">{{ type.description }}</span>
                </span>
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

          <div v-else-if="analyzing" class="analysis-progress" role="status" aria-live="polite">
            <div class="loading-spinner"></div>
            <h3 class="guide-title">Analisis sedang diproses</h3>
            <p class="guide-desc">
              Permintaan sudah dikirim ke backend Lex-DSS. Hasil akan ditampilkan setelah seluruh proses selesai.
            </p>
            <div class="progress-indicator" aria-hidden="true"></div>
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
  padding: 4px 2px 2px;
}

.quick-hint {
  margin: 0 0 14px;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.quick-group {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  width: 100%;
}

.quick-option {
  box-sizing: border-box;
  display: flex;
  align-items: flex-start;
  width: 100%;
  min-height: 78px;
  height: auto;
  margin: 0 !important;
  padding: 13px 14px;
  border: 1px solid var(--border-light);
  border-radius: 12px;
  background: #fff;
  white-space: normal;
  transition: border-color var(--transition-normal), background-color var(--transition-normal), box-shadow var(--transition-normal), transform var(--transition-normal);
}

.quick-option:nth-child(1) {
  grid-column: 1 / -1;
}

.quick-option:hover,
.quick-option:focus-within {
  border-color: var(--primary-color);
  background: var(--bg-secondary);
  transform: translateY(-1px);
}

.quick-option.is-checked {
  border-color: var(--primary-color);
  background: var(--stat-primary-soft, #eff6ff);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 12%, transparent);
}

.quick-option :deep(.el-radio__input) {
  margin-top: 2px;
}

.quick-option :deep(.el-radio__label) {
  min-width: 0;
  padding-left: 10px;
  white-space: normal;
}

.quick-copy {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.quick-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.35;
}

.quick-desc {
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.45;
}

@media (max-width: 640px) {
  .quick-group {
    grid-template-columns: minmax(0, 1fr);
  }

  .quick-option:nth-child(1) {
    grid-column: auto;
  }
}

.draft-form .el-form-item {
  margin-bottom: 20px;
}

.draft-text-item :deep(.el-form-item__content) {
  display: block;
  min-width: 0;
}

.draft-editor {
  width: 100%;
  min-width: 0;
}

.draft-textarea :deep(.el-textarea__inner) {
  min-height: 280px !important;
  padding: 14px 15px;
  border-color: var(--border-light);
  border-radius: 10px;
  background: #fbfdff;
  color: var(--text-primary);
  font-family: 'Merriweather', Georgia, serif;
  font-size: 13px;
  line-height: 1.75;
  resize: vertical;
  transition: border-color var(--transition-normal), box-shadow var(--transition-normal), background-color var(--transition-normal);
}

.draft-textarea :deep(.el-textarea__inner:focus) {
  border-color: var(--primary-color);
  background: #fff;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary-color) 12%, transparent);
}

.draft-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 9px;
}

.draft-samples {
  display: flex;
  align-items: center;
  gap: 4px 10px;
  flex-wrap: wrap;
}

.draft-toolbar-label,
.draft-helper {
  color: var(--text-secondary);
  font-size: 11px;
}

.draft-helper {
  margin: 6px 0 0;
  line-height: 1.5;
}

.analysis-progress {
  padding: 20px 0;
}

.progress-indicator {
  height: 5px;
  margin-top: 20px;
  overflow: hidden;
  border-radius: 999px;
  background: #e8eef3;
}

.progress-indicator::after {
  content: '';
  display: block;
  width: 38%;
  height: 100%;
  border-radius: inherit;
  background: var(--primary-color, #0ea5e9);
  animation: analysis-sweep 1.2s ease-in-out infinite alternate;
}

@keyframes analysis-sweep {
  from { transform: translateX(-5%); }
  to { transform: translateX(170%); }
}

@media (prefers-reduced-motion: reduce) {
  .progress-indicator::after { animation-duration: 3s; }
}

.analysis-summary {
  padding: 20px 0;
}
</style>
