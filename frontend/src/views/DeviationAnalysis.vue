<script setup>
import { onMounted, ref } from 'vue'
import { deviationApi } from '@/api'
import { showToast } from '@/utils/alerts'

const loading = ref(false)
const uploading = ref(false)
const reportLoading = ref(false)
const result = ref(null)
const reports = ref([])
const selectedReport = ref(null)
const uploadFile = ref(null)
const form = ref({ verdict_number: '', court_name: '', judge_panel: '', ratio_decidendi_text: '', verdict_amar_text: '', referenced_articles: '', domain: 'PIDANA', save_report: true })
const uploadForm = ref({ verdict_number: '', court_name: '', domain: 'PIDANA' })

function message(error, fallback) { return error.response?.data?.detail || fallback }
function tagType(level) { return { RED: 'danger', YELLOW: 'warning', GREEN: 'success', HIGH: 'danger', MEDIUM: 'warning', LOW: 'success' }[level] || 'info' }

async function score() {
  if (!form.value.verdict_number || !form.value.court_name || !form.value.ratio_decidendi_text || !form.value.verdict_amar_text) return showToast('warning', 'Lengkapi data putusan')
  loading.value = true
  try {
    const { data } = await deviationApi.scoreDeviation({ ...form.value, judge_panel: form.value.judge_panel.split('\n').filter(Boolean), referenced_articles: form.value.referenced_articles.split('\n').filter(Boolean) })
    result.value = data
    await loadReports()
    showToast('success', 'Analisis deviasi selesai')
  } catch (error) { showToast('error', message(error, 'Analisis gagal dijalankan')) } finally { loading.value = false }
}

async function loadReports() {
  reportLoading.value = true
  try { reports.value = (await deviationApi.listReports({ page_size: 50 })).data.items || [] } catch (error) { showToast('error', message(error, 'Laporan tidak dapat dimuat')) } finally { reportLoading.value = false }
}

async function openReport(id) {
  try { selectedReport.value = (await deviationApi.getReport(id)).data } catch (error) { showToast('error', message(error, 'Detail laporan tidak dapat dimuat')) }
}

async function setKYFlag(action) {
  try {
    await deviationApi.updateKYFlag(selectedReport.value.id, { action, notes: action === 'DISMISS' ? 'Ditutup melalui dashboard' : undefined })
    selectedReport.value.flagged_for_ky = action !== 'DISMISS'
    await loadReports()
    showToast('success', 'Status KY diperbarui')
  } catch (error) { showToast('error', message(error, 'Status KY gagal diperbarui')) }
}

async function downloadReport(format) {
  try {
    const response = await deviationApi.exportReport(selectedReport.value.id, format)
    const url = URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url; link.download = `deviation-${selectedReport.value.verdict_number}.${format}`; link.click()
    URL.revokeObjectURL(url)
  } catch (error) { showToast('error', message(error, 'Export laporan gagal')) }
}

function selectFile(file) { uploadFile.value = file; return false }
async function uploadDocument() {
  if (!uploadFile.value || !uploadForm.value.court_name) return showToast('warning', 'Pilih berkas dan isi pengadilan')
  uploading.value = true
  try {
    const data = new FormData()
    data.append('file', uploadFile.value.raw)
    Object.entries(uploadForm.value).forEach(([key, value]) => value && data.append(key, value))
    const job = (await deviationApi.scoreDocument(data)).data
    showToast('success', `Berkas masuk antrean (${job.job_id})`)
  } catch (error) { showToast('error', message(error, 'Upload berkas gagal')) } finally { uploading.value = false }
}

onMounted(loadReports)
</script>

<template>
  <div class="deviation-view">
    <div class="page-header"><h1 class="page-title">Deviation Analysis</h1><p class="page-subtitle">Analisis, pantau, dan tindak lanjuti penyimpangan putusan.</p></div>
    <el-row :gutter="20">
      <el-col :xs="24" :lg="12"><el-card><template #header>Analisis Teks Putusan</template>
        <el-form label-position="top" @submit.prevent="score">
          <el-row :gutter="12"><el-col :span="12"><el-form-item label="Nomor Putusan"><el-input v-model="form.verdict_number" /></el-form-item></el-col><el-col :span="12"><el-form-item label="Pengadilan"><el-input v-model="form.court_name" /></el-form-item></el-col></el-row>
          <el-form-item label="Majelis Hakim (satu nama per baris)"><el-input v-model="form.judge_panel" type="textarea" :rows="2" /></el-form-item>
          <el-form-item label="Ratio Decidendi"><el-input v-model="form.ratio_decidendi_text" type="textarea" :rows="6" /></el-form-item><el-form-item label="Amar Putusan"><el-input v-model="form.verdict_amar_text" type="textarea" :rows="3" /></el-form-item><el-form-item label="Referensi Pasal (satu per baris)"><el-input v-model="form.referenced_articles" type="textarea" :rows="2" /></el-form-item>
          <el-row :gutter="12"><el-col :span="12"><el-form-item label="Domain"><el-select v-model="form.domain" style="width:100%"><el-option value="PIDANA" label="Pidana" /><el-option value="PERDATA" label="Perdata" /><el-option value="HTN" label="HTN" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="Simpan Laporan"><el-switch v-model="form.save_report" /></el-form-item></el-col></el-row><el-button native-type="submit" type="primary" :loading="loading" style="width:100%">Mulai Analisis</el-button>
        </el-form>
      </el-card></el-col>
      <el-col :xs="24" :lg="12"><el-card class="result-card"><template #header>Hasil Analisis</template><el-empty v-if="!result" description="Masukkan data putusan untuk memulai" /><template v-else><div class="score"><strong>{{ result.total_deviation_score }}</strong><span>/100</span><el-tag :type="tagType(result.risk_level)">{{ result.risk_level }}</el-tag></div><p>{{ result.anomaly_summary }}</p><el-alert :title="result.recommended_action" :type="tagType(result.risk_level)" :closable="false" show-icon /><div v-for="(value, name) in result.indicators" :key="name" class="indicator"><span>{{ name.replaceAll('_', ' ') }}</span><el-progress :percentage="value" :status="value >= 60 ? 'exception' : value >= 30 ? 'warning' : 'success'" /></div><el-divider>Temuan</el-divider><el-collapse><el-collapse-item v-for="item in result.anomalies" :key="item.code + item.finding" :title="item.code"><el-tag :type="tagType(item.severity)">{{ item.severity }}</el-tag><p>{{ item.finding }}</p></el-collapse-item></el-collapse></template></el-card></el-col>
    </el-row>
    <el-row :gutter="20" class="section"><el-col :xs="24" :lg="9"><el-card><template #header>Analisis Berkas Putusan</template><el-form label-position="top"><el-form-item label="Pengadilan"><el-input v-model="uploadForm.court_name" /></el-form-item><el-form-item label="Nomor Putusan"><el-input v-model="uploadForm.verdict_number" /></el-form-item><el-form-item label="Domain"><el-select v-model="uploadForm.domain" style="width:100%"><el-option value="PIDANA" label="Pidana" /><el-option value="PERDATA" label="Perdata" /><el-option value="HTN" label="HTN" /></el-select></el-form-item><el-upload :auto-upload="false" :limit="1" accept=".pdf,.docx" :on-change="selectFile"><el-button>Pilih PDF/DOCX</el-button></el-upload><el-button class="upload-button" type="primary" :loading="uploading" @click="uploadDocument">Analisis Berkas</el-button></el-form></el-card></el-col>
      <el-col :xs="24" :lg="15"><el-card><template #header><div class="report-header"><span>Laporan Tersimpan</span><el-button size="small" @click="loadReports" :loading="reportLoading">Muat ulang</el-button></div></template><el-table :data="reports" v-loading="reportLoading" @row-click="row => openReport(row.id)" style="cursor:pointer"><el-table-column prop="verdict_number" label="Putusan" /><el-table-column prop="court_name" label="Pengadilan" /><el-table-column prop="total_deviation_score" label="Skor" width="70" /><el-table-column prop="risk_level" label="Risiko" width="100"><template #default="scope"><el-tag :type="tagType(scope.row.risk_level)">{{ scope.row.risk_level }}</el-tag></template></el-table-column><el-table-column prop="flagged_for_ky" label="KY" width="65"><template #default="scope">{{ scope.row.flagged_for_ky ? 'Ya' : '-' }}</template></el-table-column></el-table></el-card></el-col></el-row>
    <el-drawer v-model="selectedReport" title="Detail Laporan Deviasi" size="520px"><template v-if="selectedReport"><div class="score"><strong>{{ selectedReport.total_deviation_score }}</strong><span>/100</span><el-tag :type="tagType(selectedReport.risk_level)">{{ selectedReport.risk_level }}</el-tag></div><p>{{ selectedReport.anomaly_summary }}</p><el-descriptions :column="1" border><el-descriptions-item label="Putusan">{{ selectedReport.verdict_number }}</el-descriptions-item><el-descriptions-item label="Pengadilan">{{ selectedReport.court_name }}</el-descriptions-item><el-descriptions-item label="KY">{{ selectedReport.flagged_for_ky ? 'Ditandai' : 'Belum ditandai' }}</el-descriptions-item></el-descriptions><el-divider>Temuan</el-divider><el-collapse><el-collapse-item v-for="item in selectedReport.meta_data?.anomalies || []" :key="item.code + item.finding" :title="item.code"><p>{{ item.finding }}</p></el-collapse-item></el-collapse><div class="actions"><el-button type="danger" @click="setKYFlag('SUBMIT')">Kirim ke KY</el-button><el-button @click="setKYFlag('DISMISS')">Tutup Flag</el-button><el-button @click="downloadReport('pdf')">PDF</el-button><el-button @click="downloadReport('csv')">CSV</el-button></div></template></el-drawer>
  </div>
</template>

<style scoped>
.deviation-view { max-width: 1500px; margin: 0 auto; }.page-header { margin-bottom: 20px; padding: 20px 24px; border: 1px solid #e2e8f0; border-radius: 14px; background: white; }.page-title { margin: 0; color: #16324f; }.page-subtitle { margin: 6px 0 0; color: #64748b; }.result-card { min-height: 100%; }.score { display: flex; align-items: baseline; gap: 8px; }.score strong { font-size: 52px; color: #16324f; }.score .el-tag { margin-left: auto; }.indicator { margin-top: 18px; text-transform: capitalize; font-size: 13px; }.indicator span { display:block; margin-bottom: 6px; }.section { margin-top: 20px; }.upload-button { margin-top: 16px; width: 100%; }.report-header, .actions { display: flex; gap: 8px; align-items: center; justify-content: space-between; flex-wrap: wrap; }.actions { margin-top: 20px; justify-content: flex-start; }
</style>
