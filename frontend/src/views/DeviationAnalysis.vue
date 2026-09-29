<script setup>
import { ref } from 'vue'
import { deviationApi } from '@/api'
import { showToast } from '@/utils/alerts'

const loading = ref(false)
const result = ref(null)
const form = ref({ verdict_number: '', court_name: '', judge_panel: '', ratio_decidendi_text: '', verdict_amar_text: '', referenced_articles: '', domain: 'PIDANA', save_report: true })

async function score() {
  if (!form.value.verdict_number || !form.value.court_name || !form.value.ratio_decidendi_text || !form.value.verdict_amar_text) return
  loading.value = true
  try {
    const { data } = await deviationApi.scoreDeviation({ ...form.value, judge_panel: form.value.judge_panel.split('\n').filter(Boolean), referenced_articles: form.value.referenced_articles.split('\n').filter(Boolean) })
    result.value = data
    showToast('success', 'Analisis deviasi selesai')
  } catch (error) {
    showToast('error', error.response?.data?.detail || 'Analisis gagal dijalankan')
  } finally { loading.value = false }
}

function tagType(level) { return { RED: 'danger', YELLOW: 'warning', GREEN: 'success' }[level] || 'info' }
</script>

<template>
  <div class="deviation-view">
    <div class="page-header"><div><h1 class="page-title">Deviation Analysis</h1><p class="page-subtitle">Nilai potensi penyimpangan pertimbangan putusan secara terstruktur.</p></div></div>
    <el-row :gutter="20">
      <el-col :xs="24" :lg="12"><el-card>
        <el-form label-position="top" @submit.prevent="score">
          <el-row :gutter="12"><el-col :span="12"><el-form-item label="Nomor Putusan"><el-input v-model="form.verdict_number" /></el-form-item></el-col><el-col :span="12"><el-form-item label="Pengadilan"><el-input v-model="form.court_name" /></el-form-item></el-col></el-row>
          <el-form-item label="Majelis Hakim (satu nama per baris)"><el-input v-model="form.judge_panel" type="textarea" :rows="2" /></el-form-item>
          <el-form-item label="Ratio Decidendi"><el-input v-model="form.ratio_decidendi_text" type="textarea" :rows="7" /></el-form-item>
          <el-form-item label="Amar Putusan"><el-input v-model="form.verdict_amar_text" type="textarea" :rows="4" /></el-form-item>
          <el-form-item label="Referensi Pasal (satu per baris)"><el-input v-model="form.referenced_articles" type="textarea" :rows="3" /></el-form-item>
          <el-row :gutter="12"><el-col :span="12"><el-form-item label="Domain"><el-select v-model="form.domain" style="width:100%"><el-option value="PIDANA" label="Pidana" /><el-option value="PERDATA" label="Perdata" /><el-option value="HTN" label="HTN" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="Simpan laporan"><el-switch v-model="form.save_report" /></el-form-item></el-col></el-row>
          <el-button native-type="submit" type="primary" :loading="loading" style="width:100%">Mulai Analisis</el-button>
        </el-form>
      </el-card></el-col>
      <el-col :xs="24" :lg="12"><el-card class="result-card"><template #header>Hasil Analisis</template>
        <el-empty v-if="!result" description="Masukkan data putusan untuk memulai" />
        <template v-else><div class="score"><strong>{{ result.total_deviation_score }}</strong><span>/100</span><el-tag :type="tagType(result.risk_level)">{{ result.risk_level }}</el-tag></div><p>{{ result.anomaly_summary }}</p><el-alert :title="result.recommended_action" :type="tagType(result.risk_level)" :closable="false" show-icon />
          <div v-for="(value, name) in result.indicators" :key="name" class="indicator"><span>{{ name.replaceAll('_', ' ') }}</span><el-progress :percentage="value" :status="value >= 60 ? 'exception' : value >= 30 ? 'warning' : 'success'" /></div>
          <el-divider>Temuan</el-divider><el-collapse><el-collapse-item v-for="item in result.anomalies" :key="item.code + item.finding" :title="item.code"><el-tag :type="tagType(item.severity)">{{ item.severity }}</el-tag><p>{{ item.finding }}</p><small>{{ item.legal_basis?.join(', ') }}</small></el-collapse-item></el-collapse>
        </template>
      </el-card></el-col>
    </el-row>
  </div>
</template>

<style scoped>
.deviation-view { max-width: 1500px; margin: 0 auto; }.page-header { margin-bottom: 20px; padding: 20px 24px; border: 1px solid #e2e8f0; border-radius: 14px; background: white; }.page-title { margin: 0; color: #16324f; }.page-subtitle { margin: 6px 0 0; color: #64748b; }.result-card { min-height: 100%; }.score { display: flex; align-items: baseline; gap: 8px; }.score strong { font-size: 52px; color: #16324f; }.score .el-tag { margin-left: auto; }.indicator { margin-top: 18px; text-transform: capitalize; font-size: 13px; }.indicator span { display:block; margin-bottom: 6px; }
</style>
