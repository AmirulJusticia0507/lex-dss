<script setup>
import { ref, computed } from 'vue'
import { ElCard, ElInput, ElSelect, ElOption, ElButton, ElTag, ElDivider, ElRow, ElCol, ElMessage, ElUpload, ElProgress } from 'element-plus'
import { Upload, Document, Warning, CircleCheck, DataAnalysis, Search } from '@element-plus/icons-vue'

const contractTypes = [
  { value: 'general', label: 'Umum' },
  { value: 'employment', label: 'Ketenagakerjaan' },
  { value: 'nda', label: 'NDA / Kerahasiaan' },
  { value: 'lease', label: 'Sewa Menyewa' },
  { value: 'sales', label: 'Jual Beli' },
  { value: 'partnership', label: 'Kemitraan' },
  { value: 'service', label: 'Jasa' },
]

const contractTitle = ref('')
const contractType = ref('general')
const content = ref('')
const analyzing = ref(false)
const analysisResult = ref(null)

const riskScore = computed(() => analysisResult.value?.risk_score || 0)
const riskLevel = computed(() => analysisResult.value?.risk_level || '-')
const riskFactors = computed(() => analysisResult.value?.risk_factors || [])
const suggestions = computed(() => analysisResult.value?.suggestions || [])
const legalReferences = computed(() => analysisResult.value?.legal_references || [])
const clausesAnalyzed = computed(() => analysisResult.value?.clauses_analyzed || 0)

const riskLevelType = computed(() => {
  const level = riskLevel.value
  if (level === 'TINGGI' || level === 'SANGAT TINGGI') return 'danger'
  if (level === 'SEDANG') return 'warning'
  return 'success'
})

const riskPercentage = computed(() => {
  return Math.min(100, Math.max(0, riskScore.value))
})

async function analyzeContract() {
  if (!content.value.trim()) {
    ElMessage.warning('Masukkan konten kontrak terlebih dahulu')
    return
  }

  analyzing.value = true
  try {
    const response = await fetch('/api/v1/contract-analyzer/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contract_title: contractTitle.value || 'Untitled Contract',
        contract_type: contractType.value,
        content: content.value,
      }),
    })
    const data = await response.json()
    analysisResult.value = data
    ElMessage.success('Analisis kontrak selesai')
  } catch (error) {
    console.error('Failed to analyze contract:', error)
    ElMessage.error('Gagal menganalisis kontrak')
  } finally {
    analyzing.value = false
  }
}

function handleFileUpload(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    content.value = e.target.result
    ElMessage.success('File berhasil diupload')
  }
  reader.readAsText(file.raw)
  return false
}

function resetAnalysis() {
  analysisResult.value = null
  content.value = ''
  contractTitle.value = ''
  contractType.value = 'general'
}

function getRiskFactorType(type) {
  const types = { HIGH: 'danger', MEDIUM: 'warning', LOW: 'info' }
  return types[type] || 'info'
}
</script>

<template>
  <div class="contract-analyzer-view mx-auto w-full max-w-[1600px] space-y-6">
    <div class="page-header rounded-2xl border border-slate-200/80 bg-white px-6 py-5 shadow-sm">
      <div>
        <p class="mb-1 text-xs font-semibold uppercase tracking-[0.16em] text-sky-700">Lex-DSS · Analisis</p>
        <h1 class="page-title">Contract Analyzer</h1>
        <p class="page-subtitle">Analisis risiko hukum kontrak dengan AI</p>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="10">
        <el-card class="card">
          <template #header>
            <div class="card-header">
              <span class="card-title">Input Kontrak</span>
            </div>
          </template>

          <div style="display: flex; flex-direction: column; gap: 16px;">
            <el-input
              v-model="contractTitle"
              placeholder="Judul kontrak (opsional)"
              size="default"
            />

            <el-select v-model="contractType" placeholder="Jenis kontrak" style="width: 100%;">
              <el-option
                v-for="t in contractTypes"
                :key="t.value"
                :label="t.label"
                :value="t.value"
              />
            </el-select>

            <el-input
              v-model="content"
              type="textarea"
              :rows="12"
              placeholder="Paste kontrak di sini atau upload file..."
            />

            <el-upload
              :auto-upload="false"
              :show-file-list="false"
              accept=".txt,.md,.doc,.docx"
              :on-change="handleFileUpload"
            >
              <el-button size="small">
                <el-icon><Upload /></el-icon>
                Upload File
              </el-button>
            </el-upload>

            <div style="display: flex; gap: 8px;">
              <el-button
                type="primary"
                :loading="analyzing"
                @click="analyzeContract"
                style="flex: 1;"
              >
                <el-icon><Search /></el-icon>
                Analisis Kontrak
              </el-button>
              <el-button @click="resetAnalysis">Reset</el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="14">
        <el-card v-if="analysisResult" class="card">
          <template #header>
            <div class="card-header">
              <span class="card-title">Hasil Analisis</span>
              <el-tag :type="riskLevelType" effect="dark" size="small">
                {{ riskLevel }}
              </el-tag>
            </div>
          </template>

          <div style="display: flex; flex-direction: column; gap: 20px;">
            <div style="display: flex; align-items: center; gap: 20px;">
              <div style="text-align: center;">
                <div style="font-size: 48px; font-weight: 700; color: #1e3a5f;">
                  {{ riskScore }}
                </div>
                <div style="font-size: 12px; color: #6b7280;">Risk Score</div>
              </div>
              <div style="flex: 1;">
                <el-progress
                  :percentage="riskPercentage"
                  :color="riskLevelType === 'danger' ? '#dc2626' : riskLevelType === 'warning' ? '#d97706' : '#16a34a'"
                  :stroke-width="12"
                />
                <div style="margin-top: 8px; font-size: 13px; color: #6b7280;">
                  {{ clausesAnalyzed }} klausula dianalisis
                </div>
              </div>
            </div>

            <el-divider />

            <div>
              <h4 style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                <el-icon><Warning /></el-icon>
                Risk Factors
              </h4>
              <div v-if="riskFactors.length" style="display: flex; flex-direction: column; gap: 8px;">
                <div
                  v-for="factor in riskFactors"
                  :key="factor.keyword"
                  style="display: flex; align-items: flex-start; gap: 8px; padding: 8px 12px; background: #f9fafb; border-radius: 8px;"
                >
                  <el-tag :type="getRiskFactorType(factor.type)" size="small" effect="plain">
                    {{ factor.type }}
                  </el-tag>
                  <span style="font-size: 13px; color: #4b5563;">{{ factor.description }}</span>
                </div>
              </div>
              <el-tag v-else type="success" effect="plain">Tidak ada risk factor terdeteksi</el-tag>
            </div>

            <el-divider />

            <div>
              <h4 style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                <el-icon><CircleCheck /></el-icon>
                Suggestions
              </h4>
              <ul style="margin: 0; padding-left: 20px; color: #4b5563; font-size: 13px; line-height: 1.8;">
                <li v-for="suggestion in suggestions" :key="suggestion">{{ suggestion }}</li>
              </ul>
            </div>

            <el-divider />

            <div>
              <h4 style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                <el-icon><Document /></el-icon>
                Legal References
              </h4>
              <div style="display: flex; flex-direction: column; gap: 8px;">
                <div
                  v-for="ref in legalReferences"
                  :key="ref.law"
                  style="padding: 8px 12px; background: #f0f9ff; border-radius: 8px; border-left: 3px solid #0ea5e9;"
                >
                  <div style="font-weight: 600; color: #1e3a5f; font-size: 13px;">
                    {{ ref.law }} - {{ ref.article }}
                  </div>
                  <div style="font-size: 12px; color: #6b7280;">{{ ref.description }}</div>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <el-card v-else class="card">
          <div style="padding: 60px 20px; text-align: center; color: #9ca3af;">
            <el-icon style="font-size: 48px; margin-bottom: 16px;"><DataAnalysis /></el-icon>
            <p>Masukkan kontrak dan klik "Analisis Kontrak" untuk melihat hasil</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.contract-analyzer-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
