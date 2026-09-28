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
  <div class="min-h-screen bg-slate-50 text-slate-800">
    <header class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-5xl items-center justify-between px-5 py-4">
        <router-link class="text-lg font-bold text-slate-950" to="/">Lex-DSS</router-link>
        <router-link class="text-sm font-semibold text-sky-700 hover:text-sky-900" to="/login">Masuk</router-link>
      </div>
    </header>

    <main class="mx-auto max-w-3xl px-5 py-12 sm:py-16">
      <p class="text-sm font-semibold text-sky-700">{{ page.eyebrow }}</p>
      <h1 class="mt-2 text-3xl font-bold text-slate-950 sm:text-4xl">{{ page.title }}</h1>
      <p class="mt-5 text-base leading-7 text-slate-600">{{ page.intro }}</p>

      <div class="mt-10 divide-y divide-slate-200 border-y border-slate-200">
        <section v-for="section in page.sections" :key="section[0]" class="py-7">
          <h2 class="text-lg font-semibold text-slate-900">{{ section[0] }}</h2>
          <p class="mt-2 leading-7 text-slate-600">{{ section[1] }}</p>
        </section>
      </div>

      <nav class="mt-8 flex flex-wrap gap-x-5 gap-y-2 text-sm" aria-label="Halaman informasi">
        <router-link class="text-sky-700 hover:text-sky-900" to="/tentang">Tentang</router-link>
        <router-link class="text-sky-700 hover:text-sky-900" to="/privasi-cookies">Privasi &amp; Cookies</router-link>
        <router-link class="text-sky-700 hover:text-sky-900" to="/bantuan">Bantuan</router-link>
      </nav>
    </main>
  </div>
</template>
