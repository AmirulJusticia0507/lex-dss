<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores'

const router = useRouter()
const authStore = useAuthStore()
const isRegister = ref(false)
const loading = ref(false)
const form = reactive({ email: '', password: '', full_name: '', institution: '' })

// Captcha state
const captchaEnabled = ref(import.meta.env.VITE_CAPTCHA_ENABLED !== 'false')
const captchaChallenge = ref(null) // { challenge_id, question }
const captchaAnswer = ref('')

function errorText(error) {
  return error.response?.data?.detail || error.message || 'Permintaan gagal.'
}

async function loadCaptcha() {
  if (!captchaEnabled.value) return
  try {
    const { data } = await authApi.getCaptchaChallenge()
    captchaChallenge.value = data
    captchaAnswer.value = ''
  } catch (error) {
    console.error('Failed to load captcha:', error)
  }
}

async function submit() {
  loading.value = true
  try {
    // Build captcha token: "challenge_id:answer"
    let recaptchaToken = null
    if (captchaEnabled.value && captchaChallenge.value) {
      recaptchaToken = `${captchaChallenge.value.challenge_id}:${captchaAnswer.value}`
    }

    if (isRegister.value) {
      await authApi.register({
        email: form.email,
        password: form.password,
        full_name: form.full_name || null,
        institution: form.institution || null,
        recaptcha_token: recaptchaToken,
      })
      isRegister.value = false
      form.full_name = ''
      form.institution = ''
      ElMessage.success('Akun baru dibuat. Silakan masuk.')
      await loadCaptcha()
      return
    }

    const { data } = await authApi.login({
      email: form.email,
      password: form.password,
      recaptcha_token: recaptchaToken,
    })
    const profile = await authApi.getProfileWithToken(data.access_token)
    authStore.setAuth({ token: data.access_token, user: profile.data })
    ElMessage.success('Berhasil masuk')
    router.replace('/dashboard')
  } catch (error) {
    ElMessage.error(errorText(error))
    // Refresh captcha on error
    await loadCaptcha()
  } finally {
    loading.value = false
  }
}

// Load captcha on mount
loadCaptcha()
</script>

<template>
  <div class="mx-auto flex min-h-[75vh] w-full max-w-5xl items-center justify-center px-4 py-10">
    <div class="grid w-full overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl md:grid-cols-[1fr_1.1fr]">
      <section class="hidden flex-col justify-between bg-slate-950 p-10 text-white md:flex">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.2em] text-sky-300">Lex-DSS</p>
          <h1 class="mt-8 text-3xl font-bold leading-tight">Sistem pendukung keputusan hukum</h1>
          <p class="mt-4 max-w-sm text-sm leading-6 text-slate-300">Analisis, kelola referensi, dan akses fitur sesuai peran akun Anda.</p>
        </div>
        <p class="text-xs text-slate-400">Hak akses akun ditentukan oleh administrator.</p>
      </section>
      <section class="p-7 sm:p-10">
        <p class="text-sm font-semibold text-sky-700">{{ isRegister ? 'Buat akun pengguna' : 'Selamat datang kembali' }}</p>
        <h2 class="mt-2 text-2xl font-bold text-slate-900">{{ isRegister ? 'Daftar Lex-DSS' : 'Masuk ke akun' }}</h2>
        <p class="mt-2 text-sm text-slate-500">{{ isRegister ? 'Akun baru mendapat role Pengguna. Administrator dapat mengubah hak akses.' : 'Gunakan email dan password akun Anda.' }}</p>

        <el-form class="mt-7" label-position="top" @submit.prevent="submit">
          <template v-if="isRegister">
            <el-form-item label="Nama lengkap"><el-input v-model="form.full_name" autocomplete="name" /></el-form-item>
            <el-form-item label="Instansi"><el-input v-model="form.institution" autocomplete="organization" /></el-form-item>
          </template>
          <el-form-item label="Email"><el-input v-model="form.email" type="email" autocomplete="email" /></el-form-item>
          <el-form-item label="Password"><el-input v-model="form.password" type="password" show-password :autocomplete="isRegister ? 'new-password' : 'current-password'" /></el-form-item>

          <!-- CAPTCHA Section -->
          <el-form-item v-if="captchaEnabled && captchaChallenge" label="Verifikasi Keamanan">
            <div class="flex gap-2 w-full">
              <el-input
                v-model="captchaAnswer"
                placeholder="Jawaban"
                clearable
                @keyup.enter="submit"
              >
                <template #prepend>
                  <span class="text-slate-600 text-sm">{{ captchaChallenge.question }}</span>
                </template>
              </el-input>
              <el-button
                icon="Refresh"
                @click="loadCaptcha"
                :loading="loading"
              />
            </div>
            <small class="text-slate-400 text-xs">Selesaikan soal matematika di atas</small>
          </el-form-item>

          <el-button class="!mt-2 !w-full" type="primary" native-type="submit" :loading="loading">{{ isRegister ? 'Buat akun' : 'Masuk' }}</el-button>
        </el-form>

        <p class="mt-6 text-center text-sm text-slate-500">
          {{ isRegister ? 'Sudah punya akun?' : 'Belum punya akun?' }}
          <button class="font-semibold text-sky-700 hover:text-sky-900" type="button" @click="isRegister = !isRegister; loadCaptcha()">{{ isRegister ? 'Masuk' : 'Daftar sebagai pengguna' }}</button>
        </p>
      </section>
    </div>
  </div>
</template>