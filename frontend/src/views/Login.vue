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
  <main class="login-shell">
    <section class="login-story">
      <router-link class="brand" to="/">LEX<span>DSS</span></router-link>
      <div class="story-copy">
        <p class="story-kicker">Legal decision support system</p>
        <h1>Keputusan hukum yang lebih terang.</h1>
        <p>Telusuri dasar hukum, uji konsistensi norma, dan dokumentasikan pertimbangan dalam satu ruang kerja.</p>
      </div>
      <p class="story-note">Analisis terstruktur. Sumber tetap dapat diverifikasi.</p>
    </section>

    <section class="login-panel">
      <div class="form-wrap">
        <p class="form-kicker">{{ isRegister ? 'Akun baru' : 'Akses aman' }}</p>
        <h2>{{ isRegister ? 'Daftar ke Lex-DSS' : 'Selamat datang' }}</h2>
        <p class="form-intro">{{ isRegister ? 'Akun baru mendapat role Pengguna. Administrator dapat mengubah hak akses.' : 'Masuk untuk melanjutkan pekerjaan hukum Anda.' }}</p>

        <el-form class="login-form" label-position="top" @submit.prevent="submit">
          <template v-if="isRegister">
            <el-form-item label="Nama lengkap"><el-input v-model="form.full_name" autocomplete="name" /></el-form-item>
            <el-form-item label="Instansi"><el-input v-model="form.institution" autocomplete="organization" /></el-form-item>
          </template>
          <el-form-item label="Email"><el-input v-model="form.email" type="email" autocomplete="email" /></el-form-item>
          <el-form-item label="Password"><el-input v-model="form.password" type="password" show-password :autocomplete="isRegister ? 'new-password' : 'current-password'" /></el-form-item>

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
            <small class="captcha-help">Selesaikan soal matematika di atas</small>
          </el-form-item>

          <el-button class="submit-button" type="primary" native-type="submit" :loading="loading">{{ isRegister ? 'Buat akun' : 'Masuk' }}</el-button>
        </el-form>

        <p class="account-switch">
          {{ isRegister ? 'Sudah punya akun?' : 'Belum punya akun?' }}
          <button type="button" @click="isRegister = !isRegister; loadCaptcha()">{{ isRegister ? 'Masuk' : 'Daftar sebagai pengguna' }}</button>
        </p>
        <nav class="public-links" aria-label="Informasi">
          <router-link to="/tentang">Tentang</router-link>
          <router-link to="/privasi-cookies">Privasi &amp; Cookies</router-link>
          <router-link to="/bantuan">Bantuan</router-link>
        </nav>
      </div>
    </section>
  </main>
</template>

<style scoped>
.login-shell { min-height: 100dvh; display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(390px, .75fr); background: #fff; }
.login-story { position: relative; isolation: isolate; min-height: 100dvh; display: flex; flex-direction: column; justify-content: space-between; padding: clamp(32px, 5vw, 72px); color: #fff; background: url('@/assets/images/legal-workspace.png') center / cover no-repeat; }
.login-story::before { position: absolute; z-index: -1; inset: 0; background: rgba(8, 20, 27, .46); content: ''; }
.brand { width: max-content; color: #fff; font-size: 18px; font-weight: 800; text-decoration: none; }
.brand span { color: #55c2bd; }
.story-copy { max-width: 650px; }
.story-kicker, .form-kicker { margin: 0; color: #69d3cc; font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 0; }
.story-copy h1 { max-width: 610px; margin: 14px 0 20px; font-size: clamp(42px, 5.6vw, 78px); line-height: 1.02; letter-spacing: 0; }
.story-copy > p:last-child { max-width: 530px; margin: 0; color: #d7e2e4; font-size: 17px; line-height: 1.7; }
.story-note { margin: 0; color: #cbd7d9; font-size: 13px; }
.login-panel { min-height: 100dvh; display: flex; align-items: center; justify-content: center; padding: 40px clamp(28px, 5vw, 72px); background: #fff; }
.form-wrap { width: min(100%, 420px); }
.form-kicker { color: #087f78; }
.form-wrap h2 { margin: 10px 0 8px; color: #111827; font-size: 34px; line-height: 1.15; }
.form-intro { margin: 0; color: #64748b; font-size: 14px; line-height: 1.65; }
.login-form { margin-top: 30px; }
.captcha-help { color: #94a3b8; font-size: 12px; }
.submit-button { width: 100%; height: 44px; margin-top: 4px; font-weight: 700; }
.account-switch { margin: 22px 0 0; color: #64748b; text-align: center; font-size: 14px; }
.account-switch button { color: #087f78; font-weight: 700; }
.public-links { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px 20px; margin-top: 28px; padding-top: 22px; border-top: 1px solid #e2e8f0; }
.public-links a { color: #64748b; font-size: 12px; text-decoration: none; }
.public-links a:hover { color: #087f78; }
:deep(.el-input__wrapper) { min-height: 43px; box-shadow: 0 0 0 1px #cbd5e1 inset; }
:deep(.el-input__wrapper.is-focus) { box-shadow: 0 0 0 1px #087f78 inset; }

@media (max-width: 860px) {
  .login-shell { grid-template-columns: 1fr; }
  .login-story { min-height: 260px; padding: 28px; background-position: 35% 62%; }
  .story-copy h1 { max-width: 520px; margin-bottom: 0; font-size: clamp(34px, 9vw, 52px); }
  .story-copy > p:last-child, .story-note { display: none; }
  .login-panel { min-height: auto; padding: 38px 24px 48px; }
}
</style>
