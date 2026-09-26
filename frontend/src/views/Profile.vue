<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi, usersApi } from '@/api'
import { useAuthStore } from '@/stores'
import { confirmAction } from '@/utils/alerts'

const authStore = useAuthStore()
const activeTab = ref('profile')
const loading = ref(false)
const saving = ref(false)
const accountDialog = ref(false)
const accountsLoading = ref(false)
const accounts = ref([])
const roles = ref([])
const editingId = ref(null)
const errorMessage = ref('')
const profile = reactive({ id: '', email: '', full_name: '', institution: '', role: 'user', created_at: null, last_login: null })
const password = reactive({ current_password: '', new_password: '', confirmation: '' })
const accountForm = reactive({ email: '', password: '', full_name: '', institution: '', role: 'user' })
const isAdmin = computed(() => profile.role === 'admin' || authStore.user?.is_superuser)

function errorText(error) {
  return error.response?.data?.detail || error.message || 'Terjadi kesalahan. Coba lagi.'
}

async function loadProfile() {
  loading.value = true
  errorMessage.value = ''
  try {
    const { data } = await authApi.getProfile()
    Object.assign(profile, data)
    authStore.user = data
  } catch (error) {
    errorMessage.value = errorText(error)
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  saving.value = true
  try {
    const { data } = await authApi.updateProfile({
      email: profile.email,
      full_name: profile.full_name || null,
      institution: profile.institution || null,
    })
    Object.assign(profile, data)
    authStore.user = data
    ElMessage.success('Profil berhasil diperbarui')
  } catch (error) {
    ElMessage.error(errorText(error))
  } finally {
    saving.value = false
  }
}

async function savePassword() {
  if (password.new_password !== password.confirmation) {
    ElMessage.warning('Konfirmasi password baru belum cocok')
    return
  }
  saving.value = true
  try {
    await authApi.changePassword({
      current_password: password.current_password,
      new_password: password.new_password,
    })
    password.current_password = ''
    password.new_password = ''
    password.confirmation = ''
    ElMessage.success('Password berhasil diganti')
  } catch (error) {
    ElMessage.error(errorText(error))
  } finally {
    saving.value = false
  }
}

async function loadAccounts() {
  accountsLoading.value = true
  try {
    const [accountResponse, roleResponse] = await Promise.all([usersApi.list(), usersApi.getRoles()])
    accounts.value = Array.isArray(accountResponse.data) ? accountResponse.data : []
    roles.value = Array.isArray(roleResponse.data) ? roleResponse.data : []
  } catch (error) {
    ElMessage.error(errorText(error))
  } finally {
    accountsLoading.value = false
  }
}

function openCreateAccount() {
  editingId.value = null
  Object.assign(accountForm, { email: '', password: '', full_name: '', institution: '', role: 'user' })
  accountDialog.value = true
}

function openEditAccount(account) {
  editingId.value = account.id
  Object.assign(accountForm, {
    email: account.email,
    password: '',
    full_name: account.full_name || '',
    institution: account.institution || '',
    role: account.role,
  })
  accountDialog.value = true
}

async function saveAccount() {
  saving.value = true
  const payload = {
    email: accountForm.email,
    full_name: accountForm.full_name || null,
    institution: accountForm.institution || null,
    role: accountForm.role,
  }
  try {
    if (editingId.value) {
      if (accountForm.password) payload.password = accountForm.password
      await usersApi.update(editingId.value, payload)
      ElMessage.success('Akun berhasil diperbarui')
    } else {
      await usersApi.create({ ...payload, password: accountForm.password })
      ElMessage.success('Akun berhasil dibuat')
    }
    accountDialog.value = false
    await loadAccounts()
  } catch (error) {
    ElMessage.error(errorText(error))
  } finally {
    saving.value = false
  }
}

async function setAccountActive(account, isActive) {
  try {
    if (isActive) await usersApi.activate(account.id)
    else await usersApi.update(account.id, { is_active: false })
    ElMessage.success(isActive ? 'Akun diaktifkan' : 'Akun dinonaktifkan')
    await loadAccounts()
  } catch (error) {
    ElMessage.error(errorText(error))
  }
}

async function deactivateAccount(account) {
  const result = await confirmAction({
    title: 'Nonaktifkan akun?',
    text: `Akun ${account.email} tidak dapat masuk setelah dinonaktifkan.`,
    confirmText: 'Nonaktifkan',
  })
  if (!result.isConfirmed) return
  try {
    await usersApi.deactivate(account.id)
    ElMessage.success('Akun dinonaktifkan')
    await loadAccounts()
  } catch (error) {
    ElMessage.error(errorText(error))
  }
}

function roleLabel(role) {
  return roles.value.find((item) => item.name === role)?.label || role
}

onMounted(async () => {
  if (window.location.hash === '#security') activeTab.value = 'security'
  await loadProfile()
  if (isAdmin.value) await loadAccounts()
})
</script>

<template>
  <main class="mx-auto w-full max-w-6xl space-y-6">
    <header class="rounded-2xl border border-slate-200 bg-white px-6 py-5 shadow-sm">
      <p class="text-sm font-semibold uppercase tracking-wide text-sky-700">Akun</p>
      <h1 class="mt-1 text-2xl font-bold text-slate-900">Profil &amp; akses</h1>
      <p class="mt-1 text-sm text-slate-500">Kelola informasi akun, keamanan, pengguna, dan hak akses.</p>
    </header>

    <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" />

    <el-card v-loading="loading" class="!rounded-2xl">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="Profil" name="profile">
          <section class="grid gap-8 py-4 md:grid-cols-[220px_1fr]">
            <div class="rounded-xl bg-slate-50 p-5 text-center">
              <el-avatar :size="76" class="!bg-sky-700 !text-xl">{{ (profile.full_name || profile.email || 'U').slice(0, 1).toUpperCase() }}</el-avatar>
              <h2 class="mt-3 font-semibold text-slate-900">{{ profile.full_name || 'Pengguna Lex-DSS' }}</h2>
              <p class="text-sm text-slate-500">{{ roleLabel(profile.role) }}</p>
              <p class="mt-4 break-all text-xs text-slate-400">{{ profile.email }}</p>
            </div>
            <el-form label-position="top" @submit.prevent="saveProfile">
              <div class="grid gap-4 sm:grid-cols-2">
                <el-form-item label="Nama lengkap"><el-input v-model="profile.full_name" maxlength="255" /></el-form-item>
                <el-form-item label="Email"><el-input v-model="profile.email" type="email" /></el-form-item>
                <el-form-item label="Instansi"><el-input v-model="profile.institution" maxlength="255" /></el-form-item>
                <el-form-item label="Role"><el-input :model-value="roleLabel(profile.role)" disabled /></el-form-item>
              </div>
              <p class="mb-4 text-xs text-slate-500">Bergabung {{ profile.created_at ? new Date(profile.created_at).toLocaleDateString('id-ID') : '—' }} · Login terakhir {{ profile.last_login ? new Date(profile.last_login).toLocaleString('id-ID') : 'belum tersedia' }}</p>
              <el-button type="primary" :loading="saving" @click="saveProfile">Simpan profil</el-button>
            </el-form>
          </section>
        </el-tab-pane>

        <el-tab-pane label="Keamanan" name="security">
          <section class="max-w-xl py-4">
            <h2 class="mb-1 text-lg font-semibold text-slate-900">Ganti password</h2>
            <p class="mb-5 text-sm text-slate-500">Gunakan minimal 8 karakter. Password lama diperlukan untuk mengonfirmasi perubahan.</p>
            <el-form label-position="top" @submit.prevent="savePassword">
              <el-form-item label="Password saat ini"><el-input v-model="password.current_password" type="password" show-password autocomplete="current-password" /></el-form-item>
              <el-form-item label="Password baru"><el-input v-model="password.new_password" type="password" show-password autocomplete="new-password" minlength="8" /></el-form-item>
              <el-form-item label="Ulangi password baru"><el-input v-model="password.confirmation" type="password" show-password autocomplete="new-password" /></el-form-item>
              <el-button type="primary" :loading="saving" @click="savePassword">Perbarui password</el-button>
            </el-form>
          </section>
        </el-tab-pane>

        <el-tab-pane v-if="isAdmin" label="Manajemen akun" name="accounts">
          <section class="space-y-4 py-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 class="font-semibold text-slate-900">Akun pengguna</h2>
                <p class="text-sm text-slate-500">Buat akun, ubah role, atau nonaktifkan akses.</p>
              </div>
              <el-button type="primary" @click="openCreateAccount">Buat akun</el-button>
            </div>
            <el-table v-loading="accountsLoading" :data="accounts" stripe row-key="id">
              <el-table-column prop="full_name" label="Nama" min-width="150" />
              <el-table-column prop="email" label="Email" min-width="210" />
              <el-table-column label="Role" width="150"><template #default="scope">{{ roleLabel(scope.row.role) }}</template></el-table-column>
              <el-table-column label="Status" width="120"><template #default="scope"><el-tag :type="scope.row.is_active ? 'success' : 'info'">{{ scope.row.is_active ? 'Aktif' : 'Nonaktif' }}</el-tag></template></el-table-column>
              <el-table-column label="Aksi" width="170" fixed="right">
                <template #default="scope">
                  <el-button size="small" @click="openEditAccount(scope.row)">Ubah</el-button>
                  <el-button v-if="scope.row.is_active" size="small" type="danger" plain @click="deactivateAccount(scope.row)">Nonaktifkan</el-button>
                  <el-button v-else size="small" type="success" plain @click="setAccountActive(scope.row, true)">Aktifkan</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div class="grid gap-3 md:grid-cols-3">
              <article v-for="role in roles" :key="role.name" class="rounded-xl border border-slate-200 p-4">
                <h3 class="font-semibold text-slate-800">{{ role.label }}</h3>
                <p class="mt-1 text-xs text-slate-500">{{ role.permissions.includes('*') ? 'Semua hak akses' : role.permissions.join(' · ') }}</p>
              </article>
            </div>
          </section>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="accountDialog" :title="editingId ? 'Ubah akun' : 'Buat akun baru'" width="min(560px, 94vw)">
      <el-form label-position="top">
        <el-form-item label="Nama lengkap"><el-input v-model="accountForm.full_name" /></el-form-item>
        <el-form-item label="Email"><el-input v-model="accountForm.email" type="email" /></el-form-item>
        <el-form-item v-if="!editingId" label="Password awal"><el-input v-model="accountForm.password" type="password" show-password minlength="8" /></el-form-item>
        <el-form-item v-else label="Reset password (opsional)"><el-input v-model="accountForm.password" type="password" show-password minlength="8" placeholder="Kosongkan jika tidak diubah" /></el-form-item>
        <el-form-item label="Instansi"><el-input v-model="accountForm.institution" /></el-form-item>
        <el-form-item label="Role">
          <el-select v-model="accountForm.role" class="w-full">
            <el-option v-for="role in roles" :key="role.name" :label="role.label" :value="role.name" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="accountDialog = false">Batal</el-button>
        <el-button type="primary" :loading="saving" @click="saveAccount">{{ editingId ? 'Simpan perubahan' : 'Buat akun' }}</el-button>
      </template>
    </el-dialog>
  </main>
</template>
