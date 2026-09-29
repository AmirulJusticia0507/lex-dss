<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { civicPollApi } from '@/api'

const status = ref('PENDING')
const items = ref([])
const loading = ref(false)
const uploading = ref(false)
const selectedFile = ref(null)
const sourceUrl = ref('')
const promoteVisible = ref(false)
const selected = ref(null)
const poll = reactive({ event_id: '', question: '', options: 'Setuju\nTidak setuju', disclaimer: '' })

async function loadQueue() {
  loading.value = true
  try {
    items.value = (await civicPollApi.listQueue(status.value)).data.items || []
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Antrean tidak dapat dimuat')
  } finally {
    loading.value = false
  }
}

async function upload() {
  if (!selectedFile.value) return ElMessage.warning('Pilih berkas transkrip')
  uploading.value = true
  const data = new FormData()
  data.append('file', selectedFile.value)
  data.append('source_url', sourceUrl.value)
  try {
    const response = await civicPollApi.queueTranscript(data)
    ElMessage.success(`${response.data.queued} kandidat masuk antrean`)
    selectedFile.value = null
    await loadQueue()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Transkrip gagal diunggah')
  } finally {
    uploading.value = false
  }
}

async function review(item, decision) {
  let notes = ''
  if (decision === 'REJECTED') {
    try {
      notes = (await ElMessageBox.prompt('Tuliskan alasan penolakan', 'Tolak kandidat', { inputValidator: value => Boolean(value?.trim()) || 'Alasan wajib diisi' })).value
    } catch { return }
  }
  await civicPollApi.reviewCandidate(item.id, { decision, notes: notes || undefined })
  ElMessage.success(decision === 'APPROVED' ? 'Kandidat disetujui' : 'Kandidat ditolak')
  await loadQueue()
}

function openPromote(item) {
  selected.value = item
  poll.event_id = `CIVIC-${Date.now()}`
  poll.question = item.title.endsWith('?') ? item.title : `${item.title}?`
  poll.options = 'Setuju\nTidak setuju'
  poll.disclaimer = 'Jajak pendapat konsultatif; hasilnya bukan keputusan hukum yang mengikat.'
  promoteVisible.value = true
}

async function promote() {
  const labels = poll.options.split('\n').map(value => value.trim()).filter(Boolean)
  if (labels.length < 2) return ElMessage.warning('Isi minimal dua opsi')
  try {
    await civicPollApi.promoteCandidate(selected.value.id, {
      event_id: poll.event_id,
      question: poll.question,
      options: labels.map((label, index) => ({ code: String.fromCharCode(65 + index), label })),
      disclaimer: poll.disclaimer,
    })
    ElMessage.success('Draf polling dikirim ke E-Netizen')
    promoteVisible.value = false
    await loadQueue()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Draf gagal dikirim')
  }
}

onMounted(loadQueue)
</script>

<template>
  <div class="civic-page">
    <div class="page-header">
      <h1>Civic Moderation</h1>
      <p>Periksa transkrip sebelum membuat jajak pendapat publik.</p>
    </div>

    <el-card>
      <template #header>Unggah Transkrip</template>
      <el-form label-position="top">
        <el-form-item label="Sumber (opsional)"><el-input v-model="sourceUrl" placeholder="https://..." /></el-form-item>
        <el-upload :auto-upload="false" :limit="1" accept=".txt,.srt,.vtt" :on-change="file => selectedFile = file.raw" :on-remove="() => selectedFile = null">
          <el-button>Pilih TXT/SRT/VTT</el-button>
        </el-upload>
        <el-button type="primary" :loading="uploading" :disabled="!selectedFile" @click="upload">Masukkan ke Antrean</el-button>
      </el-form>
    </el-card>

    <el-card class="queue-card">
      <template #header>
        <div class="queue-header">
          <span>Antrean Moderator</span>
          <el-segmented v-model="status" :options="['PENDING', 'APPROVED', 'REJECTED']" @change="loadQueue" />
        </div>
      </template>
      <el-table :data="items" v-loading="loading">
        <el-table-column prop="title" label="Kandidat Isu" min-width="220" />
        <el-table-column prop="filename" label="Berkas" width="180" />
        <el-table-column label="Waktu" width="130"><template #default="scope">{{ scope.row.start_seconds }}–{{ scope.row.end_seconds ?? '?' }} dtk</template></el-table-column>
        <el-table-column label="Tindakan" width="250">
          <template #default="scope">
            <template v-if="status === 'PENDING'">
              <el-button size="small" type="success" @click="review(scope.row, 'APPROVED')">Setujui</el-button>
              <el-button size="small" type="danger" @click="review(scope.row, 'REJECTED')">Tolak</el-button>
            </template>
            <el-tag v-else-if="scope.row.promoted_event_id" type="success">{{ scope.row.promoted_event_id }}</el-tag>
            <el-button v-else-if="status === 'APPROVED'" size="small" type="primary" @click="openPromote(scope.row)">Buat Draf Polling</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="promoteVisible" title="Buat Draf Polling" width="600px">
      <el-form label-position="top">
        <el-form-item label="Event ID"><el-input v-model="poll.event_id" /></el-form-item>
        <el-form-item label="Pertanyaan"><el-input v-model="poll.question" type="textarea" /></el-form-item>
        <el-form-item label="Opsi (satu per baris)"><el-input v-model="poll.options" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="Disclaimer"><el-input v-model="poll.disclaimer" type="textarea" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="promoteVisible = false">Batal</el-button><el-button type="primary" @click="promote">Kirim Draf</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.civic-page { max-width: 1400px; margin: 0 auto; }
.page-header { margin-bottom: 20px; }
.page-header h1 { margin: 0; color: #16324f; }
.page-header p { margin: 6px 0 0; color: #64748b; }
.queue-card { margin-top: 20px; }
.queue-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.el-upload { margin-bottom: 12px; }
</style>
