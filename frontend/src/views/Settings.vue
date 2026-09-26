<script setup>
import { ref, reactive, computed } from 'vue'
import { ElCard, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElButton, ElSwitch, ElRadioGroup, ElRadio, ElDivider, ElTabs, ElTabPane, ElTag, ElIcon, ElAlert, ElDescriptions, ElDescriptionsItem, ElSlider, ElColorPicker, ElTimePicker, ElDatePicker, ElUpload, ElMessage, ElDrawer } from 'element-plus'
import { Setting, User, Lock, Bell, Moon, Sunny, Monitor, Brush, Coordinate, Box, Cloudy, Cpu, Key, Download, Upload as UploadIcon, Delete, Refresh, CircleCheck, Warning } from '@element-plus/icons-vue'

const activeTab = ref('general')
const saving = ref(false)

const settings = reactive({
  general: {
    appName: 'Lex-DSS',
    appVersion: '1.0.0',
    language: 'id',
    timezone: 'Asia/Jakarta',
    dateFormat: 'DD/MM/YYYY',
    theme: 'light',
    sidebarCollapsed: false,
    compactMode: false,
    animationsEnabled: true,
  },
  appearance: {
    primaryColor: '#0ea5e9',
    secondaryColor: '#c9a84c',
    darkMode: false,
    fontSize: 'medium',
    borderRadius: 'medium',
    density: 'comfortable',
  },
  notifications: {
    emailEnabled: true,
    pushEnabled: true,
    analysisComplete: true,
    conflictDetected: true,
    highRiskAlert: true,
    weeklyDigest: false,
    soundEnabled: true,
  },
  api: {
    baseUrl: 'http://localhost:8000/api/v1',
    timeout: 30000,
    retryAttempts: 3,
    cacheEnabled: true,
    cacheTTL: 300,
    rateLimit: 100,
  },
  ai: {
    model: 'gpt-4-turbo',
    temperature: 0.3,
    maxTokens: 4000,
    confidenceThreshold: 0.7,
    enableRAG: true,
    maxReferences: 10,
    enableCitations: true,
    hallucinationGuard: true,
  },
  database: {
    vectorDimension: 1536,
    indexType: 'HNSW',
    similarityThreshold: 0.75,
    batchSize: 100,
    autoSync: true,
    syncInterval: 3600,
  },
  security: {
    sessionTimeout: 480,
    maxLoginAttempts: 5,
    lockoutDuration: 15,
    passwordMinLength: 8,
    require2FA: false,
    auditLogEnabled: true,
    dataEncryption: true,
  },
  advanced: {
    debugMode: false,
    logLevel: 'info',
    telemetryEnabled: true,
    autoUpdate: true,
    betaFeatures: false,
    exportFormat: 'markdown',
  },
})

const languages = [
  { value: 'id', label: 'Bahasa Indonesia' },
  { value: 'en', label: 'English' },
]

const timezones = [
  { value: 'Asia/Jakarta', label: 'WIB (UTC+7) - Jakarta' },
  { value: 'Asia/Makassar', label: 'WITA (UTC+8) - Makassar' },
  { value: 'Asia/Jayapura', label: 'WIT (UTC+9) - Jayapura' },
  { value: 'UTC', label: 'UTC' },
]

const themes = [
  { value: 'light', label: 'Light', icon: Sunny },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'auto', label: 'System', icon: Monitor },
]

const fontSizes = [
  { value: 'small', label: 'Kecil (12px)' },
  { value: 'medium', label: 'Sedang (14px)' },
  { value: 'large', label: 'Besar (16px)' },
]

const densities = [
  { value: 'compact', label: 'Compact' },
  { value: 'comfortable', label: 'Comfortable' },
  { value: 'spacious', label: 'Spacious' },
]

const aiModels = [
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
  { value: 'gpt-4', label: 'GPT-4' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
  { value: 'claude-3-opus', label: 'Claude 3 Opus' },
  { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
  { value: 'llama-3-70b', label: 'Llama 3 70B (Local)' },
  { value: 'custom', label: 'Custom Model' },
]

const logLevels = [
  { value: 'debug', label: 'Debug' },
  { value: 'info', label: 'Info' },
  { value: 'warn', label: 'Warning' },
  { value: 'error', label: 'Error' },
]

async function saveSettings(tab) {
  saving.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    localStorage.setItem(`lex-dss-${tab}`, JSON.stringify(settings[tab]))
    ElMessage.success(`Pengaturan ${getTabLabel(tab)} berhasil disimpan`)
  } catch (error) {
    ElMessage.error('Gagal menyimpan pengaturan')
  } finally {
    saving.value = false
  }
}

function resetSettings(tab) {
  ElMessageBox.confirm('Yakin ingin reset pengaturan ke default?', 'Konfirmasi', {
    confirmButtonText: 'Ya, Reset',
    cancelButtonText: 'Batal',
    type: 'warning',
  }).then(() => {
    resetToDefaults(tab)
    ElMessage.success('Pengaturan direset ke default')
  }).catch(() => {})
}

function resetToDefaults(tab) {
  const defaults = {
    general: { appName: 'Lex-DSS', appVersion: '1.0.0', language: 'id', timezone: 'Asia/Jakarta', dateFormat: 'DD/MM/YYYY', theme: 'light', sidebarCollapsed: false, compactMode: false, animationsEnabled: true },
    appearance: { primaryColor: '#0ea5e9', secondaryColor: '#c9a84c', darkMode: false, fontSize: 'medium', borderRadius: 'medium', density: 'comfortable' },
    notifications: { emailEnabled: true, pushEnabled: true, analysisComplete: true, conflictDetected: true, highRiskAlert: true, weeklyDigest: false, soundEnabled: true },
    api: { baseUrl: 'http://localhost:8000/api/v1', timeout: 30000, retryAttempts: 3, cacheEnabled: true, cacheTTL: 300, rateLimit: 100 },
    ai: { model: 'gpt-4-turbo', temperature: 0.3, maxTokens: 4000, confidenceThreshold: 0.7, enableRAG: true, maxReferences: 10, enableCitations: true, hallucinationGuard: true },
    database: { vectorDimension: 1536, indexType: 'HNSW', similarityThreshold: 0.75, batchSize: 100, autoSync: true, syncInterval: 3600 },
    security: { sessionTimeout: 480, maxLoginAttempts: 5, lockoutDuration: 15, passwordMinLength: 8, require2FA: false, auditLogEnabled: true, dataEncryption: true },
    advanced: { debugMode: false, logLevel: 'info', telemetryEnabled: true, autoUpdate: true, betaFeatures: false, exportFormat: 'markdown' },
  }
  Object.assign(settings[tab], defaults[tab])
}

function getTabLabel(tab) {
  const labels = {
    general: 'Umum',
    appearance: 'Tampilan',
    notifications: 'Notifikasi',
    api: 'API & Integrasi',
    ai: 'AI & Model',
    database: 'Database & Vector',
    security: 'Keamanan',
    advanced: 'Lanjutan',
  }
  return labels[tab] || tab
}

function exportAllSettings() {
  const allSettings = { ...settings, exportedAt: new Date().toISOString(), version: '1.0.0' }
  const blob = new Blob([JSON.stringify(allSettings, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `lex-dss-settings-${new Date().toISOString().split('T')[0]}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('Pengaturan diekspor')
}

function importSettings(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const imported = JSON.parse(e.target.result)
      Object.keys(settings).forEach(key => {
        if (imported[key]) Object.assign(settings[key], imported[key])
      })
      ElMessage.success('Pengaturan diimpor berhasil')
    } catch (error) {
      ElMessage.error('File pengaturan tidak valid')
    }
  }
  reader.readAsText(file.raw)
}

function clearCache() {
  ElMessageBox.confirm('Ini akan menghapus cache API dan data lokal. Lanjutkan?', 'Hapus Cache', {
    confirmButtonText: 'Ya, Hapus',
    cancelButtonText: 'Batal',
    type: 'warning',
  }).then(() => {
    localStorage.clear()
    sessionStorage.clear()
    ElMessage.success('Cache dibersihkan. Silakan refresh halaman.')
  }).catch(() => {})
}

function testApiConnection() {
  ElMessage.info('Menguji koneksi API...')
  setTimeout(() => {
    ElMessage.success('Koneksi API berhasil (mock)')
  }, 1000)
}

function syncDatabase() {
  ElMessage.info('Memulai sinkronisasi database...')
  setTimeout(() => {
    ElMessage.success('Sinkronisasi selesai (mock)')
  }, 2000)
}
</script>

<template>
  <div class="settings-view">
    <div class="page-header">
      <div>
        <h1 class="page-title">Pengaturan</h1>
        <p class="page-subtitle">Konfigurasi sistem Lex-DSS</p>
      </div>
      <div style="display: flex; gap: 8px;">
        <el-button @click="exportAllSettings"><el-icon><Download /></el-icon> Export Settings</el-button>
        <el-upload
          action="#"
          :on-change="importSettings"
          :show-file-list="false"
          accept=".json"
        >
          <el-button><el-icon><UploadIcon /></el-icon> Import Settings</el-button>
        </el-upload>
      </div>
    </div>

    <el-card class="card">
      <el-tabs v-model="activeTab" type="border-card" class="settings-tabs">
        <el-tab-pane label="Umum" name="general">
          <el-icon><Setting /></el-icon>
        </el-tab-pane>
        <el-tab-pane label="Tampilan" name="appearance">
          <el-icon><Brush /></el-icon>
        </el-tab-pane>
        <el-tab-pane label="Notifikasi" name="notifications">
          <el-icon><Bell /></el-icon>
        </el-tab-pane>
        <el-tab-pane label="API & Integrasi" name="api">
          <el-icon><Cloudy /></el-icon>
        </el-tab-pane>
        <el-tab-pane label="AI & Model" name="ai">
          <el-icon><Cpu /></el-icon>
        </el-tab-pane>
        <el-tab-pane label="Database & Vector" name="database">
          <el-icon><Box /></el-icon>
        </el-tab-pane>
        <el-tab-pane label="Keamanan" name="security">
          <el-icon><Lock /></el-icon>
        </el-tab-pane>
        <el-tab-pane label="Lanjutan" name="advanced">
          <el-icon><Key /></el-icon>
        </el-tab-pane>
      </el-tabs>

      <div class="settings-content">
        <el-tab-pane v-if="activeTab === 'general'" name="general">
          <el-form :model="settings.general" label-width="180px" class="settings-form">
            <el-form-item label="Nama Aplikasi">
              <el-input v-model="settings.general.appName" placeholder="Nama aplikasi" />
            </el-form-item>
            <el-form-item label="Versi">
              <el-input v-model="settings.general.appVersion" placeholder="Versi" disabled />
            </el-form-item>
            <el-form-item label="Bahasa Default">
              <el-select v-model="settings.general.language" placeholder="Pilih bahasa" style="width: 200px;">
                <el-option v-for="l in languages" :key="l.value" :label="l.label" :value="l.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="Zona Waktu">
              <el-select v-model="settings.general.timezone" placeholder="Pilih zona waktu" style="width: 300px;">
                <el-option v-for="t in timezones" :key="t.value" :label="t.label" :value="t.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="Format Tanggal">
              <el-input v-model="settings.general.dateFormat" placeholder="Format tanggal" style="width: 200px;" />
            </el-form-item>
            <el-form-item label="Tema">
              <el-radio-group v-model="settings.general.theme" style="display: flex; gap: 20px;">
                <el-radio v-for="t in themes" :key="t.value" :label="t.value" :style="{ display: 'flex', alignItems: 'center', gap: '8px' }">
                  <el-icon><component :is="t.icon" /></el-icon>
                  {{ t.label }}
                </el-radio>
              </el-radio-group>
            </el-form-item>
            <el-divider>UI Preferences</el-divider>
            <el-form-item label="Sidebar Collapsed Default">
              <el-switch v-model="settings.general.sidebarCollapsed" active-text="Ya" inactive-text="Tidak" />
            </el-form-item>
            <el-form-item label="Mode Kompak">
              <el-switch v-model="settings.general.compactMode" active-text="Ya" inactive-text="Tidak" />
            </el-form-item>
            <el-form-item label="Animasi">
              <el-switch v-model="settings.general.animationsEnabled" active-text="Aktif" inactive-text="Nonaktif" />
            </el-form-item>
            <el-divider style="margin: 24px 0;" />
            <el-form-item>
              <el-button type="primary" @click="saveSettings('general')" :loading="saving"><el-icon><CircleCheck /></el-icon> Simpan</el-button>
              <el-button @click="resetSettings('general')"><el-icon><Refresh /></el-icon> Reset Default</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane v-if="activeTab === 'appearance'" name="appearance">
          <el-form :model="settings.appearance" label-width="180px" class="settings-form">
            <el-form-item label="Warna Primer">
              <el-color-picker v-model="settings.appearance.primaryColor" show-alpha predefine />
            </el-form-item>
            <el-form-item label="Warna Sekunder (Legal Gold)">
              <el-color-picker v-model="settings.appearance.secondaryColor" show-alpha predefine />
            </el-form-item>
            <el-form-item label="Dark Mode">
              <el-switch v-model="settings.appearance.darkMode" active-text="Aktif" inactive-text="Nonaktif" />
            </el-form-item>
            <el-form-item label="Ukuran Font">
              <el-select v-model="settings.appearance.fontSize" placeholder="Pilih ukuran" style="width: 200px;">
                <el-option v-for="f in fontSizes" :key="f.value" :label="f.label" :value="f.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="Border Radius">
              <el-select v-model="settings.appearance.borderRadius" placeholder="Pilih radius" style="width: 200px;">
                <el-option label="None (0px)" value="none" />
                <el-option label="Small (4px)" value="small" />
                <el-option label="Medium (8px)" value="medium" />
                <el-option label="Large (12px)" value="large" />
                <el-option label="Full (9999px)" value="full" />
              </el-select>
            </el-form-item>
            <el-form-item label="Kepadatan UI">
              <el-radio-group v-model="settings.appearance.density" style="display: flex; gap: 20px;">
                <el-radio v-for="d in densities" :key="d.value" :label="d.value">{{ d.label }}</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-divider style="margin: 24px 0;" />
            <el-form-item>
              <el-button type="primary" @click="saveSettings('appearance')" :loading="saving"><el-icon><CheckCircle /></el-icon> Simpan</el-button>
              <el-button @click="resetSettings('appearance')"><el-icon><Refresh /></el-icon> Reset Default</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane v-if="activeTab === 'notifications'" name="notifications">
          <el-form :model="settings.notifications" label-width="220px" class="settings-form">
            <el-form-item label="Notifikasi Email">
              <el-switch v-model="settings.notifications.emailEnabled" active-text="Aktif" inactive-text="Nonaktif" />
            </el-form-item>
            <el-form-item label="Notifikasi Push (Browser)">
              <el-switch v-model="settings.notifications.pushEnabled" active-text="Aktif" inactive-text="Nonaktif" />
            </el-form-item>
            <el-form-item label="Suara Notifikasi">
              <el-switch v-model="settings.notifications.soundEnabled" active-text="Aktif" inactive-text="Nonaktif" />
            </el-form-item>
            <el-divider>Event Triggers</el-divider>
            <el-form-item label="Analisis Selesai">
              <el-switch v-model="settings.notifications.analysisComplete" active-text="Aktif" inactive-text="Nonaktif" />
            </el-form-item>
            <el-form-item label="Kontradiksi Terdeteksi">
              <el-switch v-model="settings.notifications.conflictDetected" active-text="Aktif" inactive-text="Nonaktif" />
            </el-form-item>
            <el-form-item label="Peringatan Risiko Tinggi">
              <el-switch v-model="settings.notifications.highRiskAlert" active-text="Aktif" inactive-text="Nonaktif" />
            </el-form-item>
            <el-form-item label="Weekly Digest">
              <el-switch v-model="settings.notifications.weeklyDigest" active-text="Aktif" inactive-text="Nonaktif" />
            </el-form-item>
            <el-divider style="margin: 24px 0;" />
            <el-form-item>
              <el-button type="primary" @click="saveSettings('notifications')" :loading="saving"><el-icon><CheckCircle /></el-icon> Simpan</el-button>
              <el-button @click="resetSettings('notifications')"><el-icon><Refresh /></el-icon> Reset Default</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane v-if="activeTab === 'api'" name="api">
          <el-form :model="settings.api" label-width="180px" class="settings-form">
            <el-form-item label="Base URL API">
              <el-input v-model="settings.api.baseUrl" placeholder="https://api.example.com/v1" style="width: 400px;" />
            </el-form-item>
            <el-form-item label="Timeout (ms)">
              <el-input-number v-model="settings.api.timeout" :min="5000" :max="120000" :step="5000" style="width: 200px;" controls-position="right" />
            </el-form-item>
            <el-form-item label="Retry Attempts">
              <el-input-number v-model="settings.api.retryAttempts" :min="1" :max="10" style="width: 100px;" />
            </el-form-item>
            <el-form-item label="Cache Enabled">
              <el-switch v-model="settings.api.cacheEnabled" active-text="Ya" inactive-text="Tidak" />
            </el-form-item>
            <el-form-item label="Cache TTL (seconds)">
              <el-input-number v-model="settings.api.cacheTTL" :min="60" :max="3600" :step="60" style="width: 200px;" controls-position="right" />
            </el-form-item>
            <el-form-item label="Rate Limit (req/min)">
              <el-input-number v-model="settings.api.rateLimit" :min="10" :max="1000" :step="10" style="width: 200px;" controls-position="right" />
            </el-form-item>
            <el-divider style="margin: 24px 0;" />
            <el-form-item>
              <el-button type="primary" @click="saveSettings('api')" :loading="saving"><el-icon><CheckCircle /></el-icon> Simpan</el-button>
              <el-button @click="testApiConnection"><el-icon><Refresh /></el-icon> Test Koneksi</el-button>
              <el-button @click="resetSettings('api')"><el-icon><Refresh /></el-icon> Reset Default</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane v-if="activeTab === 'ai'" name="ai">
          <el-form :model="settings.ai" label-width="200px" class="settings-form">
            <el-form-item label="Model AI">
              <el-select v-model="settings.ai.model" placeholder="Pilih model" style="width: 300px;">
                <el-option v-for="m in aiModels" :key="m.value" :label="m.label" :value="m.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="Temperature">
              <el-slider v-model="settings.ai.temperature" :min="0" :max="1" :step="0.1" show-tooltip :format-tooltip="v => v.toFixed(1)" style="width: 300px;" />
              <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">{{ settings.ai.temperature }} (0 = deterministik, 1 = kreatif)</div>
            </el-form-item>
            <el-form-item label="Max Tokens">
              <el-input-number v-model="settings.ai.maxTokens" :min="500" :max="8000" :step="500" style="width: 200px;" controls-position="right" />
            </el-form-item>
            <el-form-item label="Confidence Threshold">
              <el-slider v-model="settings.ai.confidenceThreshold" :min="0.5" :max="0.95" :step="0.05" show-tooltip :format-tooltip="v => (v * 100).toFixed(0) + '%'" style="width: 300px;" />
            </el-form-item>
            <el-form-item label="Max References (RAG)">
              <el-input-number v-model="settings.ai.maxReferences" :min="3" :max="20" style="width: 150px;" />
            </el-form-item>
            <el-divider>Guardrails</el-divider>
            <el-form-item label="Enable RAG">
              <el-switch v-model="settings.ai.enableRAG" active-text="Ya" inactive-text="Tidak" />
            </el-form-item>
            <el-form-item label="Enable Citations">
              <el-switch v-model="settings.ai.enableCitations" active-text="Ya" inactive-text="Tidak" />
            </el-form-item>
            <el-form-item label="Hallucination Guard">
              <el-switch v-model="settings.ai.hallucinationGuard" active-text="Aktif" inactive-text="Nonaktif" />
              <template #append>
                <el-tag size="small" type="info">Mencegah AI mengutip pasal yang tidak ada</el-tag>
              </template>
            </el-form-item>
            <el-divider style="margin: 24px 0;" />
            <el-form-item>
              <el-button type="primary" @click="saveSettings('ai')" :loading="saving"><el-icon><CheckCircle /></el-icon> Simpan</el-button>
              <el-button @click="resetSettings('ai')"><el-icon><Refresh /></el-icon> Reset Default</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane v-if="activeTab === 'database'" name="database">
          <el-form :model="settings.database" label-width="200px" class="settings-form">
            <el-form-item label="Vector Dimension">
              <el-input-number v-model="settings.database.vectorDimension" :min="384" :max="4096" :step="128" style="width: 200px;" controls-position="right" disabled />
              <template #append>
                <el-tag size="small" type="info">Fixed: 1536 (text-embedding-ada-002)</el-tag>
              </template>
            </el-form-item>
            <el-form-item label="Index Type">
              <el-select v-model="settings.database.indexType" placeholder="Pilih index type" style="width: 200px;">
                <el-option label="HNSW (Hierarchical NSW)" value="HNSW" />
                <el-option label="IVFFlat" value="IVFFlat" />
                <el-option label="IVFPQ" value="IVFPQ" />
              </el-select>
            </el-form-item>
            <el-form-item label="Similarity Threshold">
              <el-slider v-model="settings.database.similarityThreshold" :min="0.5" :max="0.99" :step="0.01" show-tooltip :format-tooltip="v => v.toFixed(2)" style="width: 300px;" />
            </el-form-item>
            <el-form-item label="Batch Size">
              <el-input-number v-model="settings.database.batchSize" :min="10" :max="500" :step="10" style="width: 150px;" controls-position="right" />
            </el-form-item>
            <el-form-item label="Auto Sync">
              <el-switch v-model="settings.database.autoSync" active-text="Ya" inactive-text="Tidak" />
            </el-form-item>
            <el-form-item label="Sync Interval (seconds)">
              <el-input-number v-model="settings.database.syncInterval" :min="300" :max="86400" :step="300" style="width: 200px;" controls-position="right" />
            </el-form-item>
            <el-divider style="margin: 24px 0;" />
            <el-form-item>
              <el-button type="primary" @click="saveSettings('database')" :loading="saving"><el-icon><CheckCircle /></el-icon> Simpan</el-button>
              <el-button @click="syncDatabase"><el-icon><Refresh /></el-icon> Sync Sekarang</el-button>
              <el-button @click="resetSettings('database')"><el-icon><Refresh /></el-icon> Reset Default</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane v-if="activeTab === 'security'" name="security">
          <el-form :model="settings.security" label-width="220px" class="settings-form">
            <el-form-item label="Session Timeout (menit)">
              <el-input-number v-model="settings.security.sessionTimeout" :min="30" :max="1440" :step="30" style="width: 150px;" controls-position="right" />
            </el-form-item>
            <el-form-item label="Max Login Attempts">
              <el-input-number v-model="settings.security.maxLoginAttempts" :min="3" :max="10" style="width: 100px;" />
            </el-form-item>
            <el-form-item label="Lockout Duration (menit)">
              <el-input-number v-model="settings.security.lockoutDuration" :min="5" :max="60" :step="5" style="width: 150px;" controls-position="right" />
            </el-form-item>
            <el-form-item label="Password Min Length">
              <el-input-number v-model="settings.security.passwordMinLength" :min="6" :max="32" style="width: 100px;" />
            </el-form-item>
            <el-form-item label="Require 2FA">
              <el-switch v-model="settings.security.require2FA" active-text="Ya" inactive-text="Tidak" />
            </el-form-item>
            <el-form-item label="Audit Log Enabled">
              <el-switch v-model="settings.security.auditLogEnabled" active-text="Ya" inactive-text="Tidak" />
            </el-form-item>
            <el-form-item label="Data Encryption">
              <el-switch v-model="settings.security.dataEncryption" active-text="Ya" inactive-text="Tidak" />
            </el-form-item>
            <el-divider style="margin: 24px 0;" />
            <el-form-item>
              <el-button type="primary" @click="saveSettings('security')" :loading="saving"><el-icon><CheckCircle /></el-icon> Simpan</el-button>
              <el-button @click="resetSettings('security')"><el-icon><Refresh /></el-icon> Reset Default</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane v-if="activeTab === 'advanced'" name="advanced">
          <el-form :model="settings.advanced" label-width="180px" class="settings-form">
            <el-form-item label="Debug Mode">
              <el-switch v-model="settings.advanced.debugMode" active-text="Aktif" inactive-text="Nonaktif" />
              <template #append>
                <el-tag size="small" type="warning">Menampilkan log detail di console</el-tag>
              </template>
            </el-form-item>
            <el-form-item label="Log Level">
              <el-select v-model="settings.advanced.logLevel" placeholder="Pilih level" style="width: 200px;">
                <el-option v-for="l in logLevels" :key="l.value" :label="l.label" :value="l.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="Telemetry/Analytics">
              <el-switch v-model="settings.advanced.telemetryEnabled" active-text="Aktif" inactive-text="Nonaktif" />
            </el-form-item>
            <el-form-item label="Auto Update Check">
              <el-switch v-model="settings.advanced.autoUpdate" active-text="Ya" inactive-text="Tidak" />
            </el-form-item>
            <el-form-item label="Beta Features">
              <el-switch v-model="settings.advanced.betaFeatures" active-text="Aktif" inactive-text="Nonaktif" />
              <template #append>
                <el-tag size="small" type="warning">Fitur eksperimental, bisa tidak stabil</el-tag>
              </template>
            </el-form-item>
            <el-form-item label="Default Export Format">
              <el-select v-model="settings.advanced.exportFormat" placeholder="Pilih format" style="width: 200px;">
                <el-option label="Markdown (.md)" value="markdown" />
                <el-option label="JSON (.json)" value="json" />
                <el-option label="PDF (.pdf)" value="pdf" />
                <el-option label="Word (.docx)" value="docx" />
              </el-select>
            </el-form-item>
            <el-divider style="margin: 24px 0;" />
            <el-alert title="Zona Bahaya" type="warning" show-icon :closable="false" style="margin-bottom: 16px;">
              <template #description>
                Tindakan di bawah ini bersifat destruktif dan tidak dapat dibatalkan.
              </template>
            </el-alert>
            <el-form-item label="Clear All Cache & Storage">
              <el-button type="danger" @click="clearCache"><el-icon><Delete /></el-icon> Hapus Cache & LocalStorage</el-button>
            </el-form-item>
            <el-divider style="margin: 24px 0;" />
            <el-form-item>
              <el-button type="primary" @click="saveSettings('advanced')" :loading="saving"><el-icon><CheckCircle /></el-icon> Simpan</el-button>
              <el-button @click="resetSettings('advanced')"><el-icon><Refresh /></el-icon> Reset Default</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ElMessage, ElMessageBox } from 'element-plus'
export default {
  components: { ElMessage, ElMessageBox },
}
</script>

<style scoped>
.settings-tabs {
  margin-bottom: 24px;
}

.settings-form .el-form-item {
  margin-bottom: 20px;
}

.settings-content {
  padding: 8px 0;
}
</style>