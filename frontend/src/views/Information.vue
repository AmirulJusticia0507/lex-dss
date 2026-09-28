<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const pages = {
  about: {
    eyebrow: 'Mengenal Lex-DSS',
    title: 'Tentang',
    intro: 'Lex-DSS adalah sistem pendukung keputusan untuk membantu penelusuran, analisis, dan penilaian konsistensi hukum Indonesia.',
    sections: [
      ['Tujuan', 'Lex-DSS membantu pengguna mengidentifikasi hubungan antaraturan, potensi konflik norma, risiko hukum, dan bahan pertimbangan untuk menyusun pendapat hukum.'],
      ['Ruang lingkup', 'Basis pengetahuan mencakup hukum pidana, perdata, tata negara, administrasi negara, serta peraturan perundang-undangan yang relevan dengan proses peradilan.'],
      ['Batasan', 'Hasil analisis bersifat pendukung dan bukan nasihat hukum, putusan pengadilan, atau pengganti pemeriksaan oleh advokat dan aparat penegak hukum. Sumber resmi tetap harus diverifikasi sebelum hasil digunakan.'],
    ],
  },
  privacy: {
    eyebrow: 'Perlindungan data',
    title: 'Kebijakan Privasi & Cookies',
    intro: 'Kami memproses data seperlunya untuk menjalankan akun, menjaga keamanan, dan menyediakan layanan analisis Lex-DSS.',
    sections: [
      ['Data yang diproses', 'Data dapat meliputi identitas akun, instansi, riwayat masuk, preferensi, dokumen atau teks yang dikirim untuk dianalisis, dan catatan audit penggunaan layanan.'],
      ['Penyimpanan sesi', 'Lex-DSS menyimpan token akses dan preferensi antarmuka pada penyimpanan browser. Layanan tidak menggunakan cookie iklan atau pelacakan lintas situs.'],
      ['Penggunaan dan keamanan', 'Data digunakan untuk autentikasi, analisis hukum, peningkatan kualitas, pencegahan penyalahgunaan, dan pemenuhan kewajiban hukum. Akses dibatasi sesuai peran pengguna.'],
      ['Kendali pengguna', 'Pengguna dapat memperbarui profil dan kata sandi dari halaman akun. Permintaan koreksi atau penghapusan data dapat disampaikan kepada administrator sistem.'],
    ],
  },
  help: {
    eyebrow: 'Dukungan penggunaan',
    title: 'Bantuan',
    intro: 'Temukan langkah singkat untuk mengakses akun dan menangani kendala umum di Lex-DSS.',
    sections: [
      ['Masuk dan akun', 'Gunakan email terdaftar dan kata sandi Anda. Jika akses ditolak atau akun nonaktif, hubungi administrator instansi untuk memeriksa status dan role akun.'],
      ['Menjalankan analisis', 'Buka Conflict Checker atau DSS Panel, masukkan materi hukum yang relevan, lalu periksa sumber, tingkat risiko, dan rekomendasi sebelum menggunakan hasil.'],
      ['Hasil tidak tampil', 'Periksa koneksi internet, muat ulang halaman, lalu coba kembali. Simpan salinan teks yang belum terkirim agar pekerjaan tidak hilang.'],
      ['Keamanan akun', 'Jangan membagikan kata sandi atau token akses. Keluar dari akun setelah memakai perangkat bersama dan segera ubah kata sandi jika ditemukan aktivitas mencurigakan.'],
    ],
  },
}

const page = computed(() => pages[route.meta.infoPage] || pages.about)
</script>

<template>
  <div class="info-page">
    <header class="info-hero">
      <div class="topbar">
        <router-link class="brand" to="/">LEX<span>DSS</span></router-link>
        <nav aria-label="Navigasi publik">
          <router-link to="/tentang">Tentang</router-link>
          <router-link to="/privasi-cookies">Privasi</router-link>
          <router-link to="/bantuan">Bantuan</router-link>
          <router-link class="login-link" to="/login">Masuk</router-link>
        </nav>
      </div>
      <div class="hero-copy">
        <p>{{ page.eyebrow }}</p>
        <h1>{{ page.title }}</h1>
        <span>{{ page.intro }}</span>
      </div>
    </header>

    <main class="info-content">
      <div class="section-list">
        <section v-for="(section, index) in page.sections" :key="section[0]">
          <span>{{ String(index + 1).padStart(2, '0') }}</span>
          <div>
            <h2>{{ section[0] }}</h2>
            <p>{{ section[1] }}</p>
          </div>
        </section>
      </div>
    </main>

    <footer>
      <span>Lex-DSS</span>
      <p>Sistem pendukung keputusan hukum Indonesia</p>
    </footer>
  </div>
</template>

<style scoped>
.info-page { min-height: 100dvh; overflow-x: hidden; background: #f7f9f8; color: #172126; }
.info-hero { position: relative; isolation: isolate; min-height: min(560px, 65vh); display: flex; flex-direction: column; justify-content: space-between; padding: 28px clamp(24px, 6vw, 88px) 64px; color: #fff; background: url('@/assets/images/legal-workspace.png') center 54% / cover no-repeat; }
.info-hero::before { position: absolute; z-index: -1; inset: 0; background: rgba(7, 18, 24, .66); content: ''; }
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 24px; }
.brand { color: #fff; font-size: 18px; font-weight: 800; text-decoration: none; }
.brand span { color: #55c2bd; }
.topbar nav { display: flex; align-items: center; gap: clamp(16px, 3vw, 36px); }
.topbar nav a { color: #dbe6e7; font-size: 13px; font-weight: 600; text-decoration: none; }
.topbar nav a:hover, .topbar nav a.router-link-active { color: #fff; }
.topbar .login-link { padding: 9px 16px; border: 1px solid rgba(255,255,255,.6); }
.hero-copy { max-width: 760px; }
.hero-copy p { margin: 0 0 12px; color: #69d3cc; font-size: 12px; font-weight: 800; text-transform: uppercase; }
.hero-copy h1 { max-width: 700px; margin: 0; overflow-wrap: anywhere; font-size: clamp(42px, 6vw, 76px); line-height: 1.02; letter-spacing: 0; }
.hero-copy span { display: block; max-width: 680px; margin-top: 22px; color: #dbe5e6; font-size: 17px; line-height: 1.7; }
.info-content { max-width: 960px; margin: 0 auto; padding: 72px 24px 96px; }
.section-list { border-top: 1px solid #cad5d2; }
.section-list section { display: grid; grid-template-columns: 64px 1fr; gap: 24px; padding: 36px 0; border-bottom: 1px solid #cad5d2; }
.section-list section > span { color: #087f78; font-size: 13px; font-weight: 800; }
.section-list section > div { min-width: 0; }
.section-list h2 { margin: 0 0 10px; color: #172126; font-size: 21px; overflow-wrap: anywhere; }
.section-list p { max-width: 760px; margin: 0; color: #58666c; font-size: 15px; line-height: 1.8; }
footer { display: flex; justify-content: space-between; gap: 24px; padding: 26px clamp(24px, 6vw, 88px); border-top: 1px solid #dce4e1; background: #fff; color: #647278; font-size: 12px; }
footer span { color: #172126; font-weight: 800; }
footer p { margin: 0; }

@media (max-width: 640px) {
  .info-hero { min-height: 500px; padding: 22px 20px 44px; background-position: 38% center; }
  .topbar { align-items: flex-start; }
  .topbar nav { justify-content: flex-end; flex-wrap: wrap; gap: 10px 16px; }
  .topbar nav a:not(.login-link) { display: none; }
  .hero-copy span { font-size: 15px; }
  .hero-copy h1 { font-size: 36px; line-height: 1.08; }
  .info-content { padding: 48px 20px 64px; }
  .section-list section { grid-template-columns: 38px 1fr; gap: 12px; padding: 28px 0; }
  footer { flex-direction: column; gap: 5px; }
}
</style>
