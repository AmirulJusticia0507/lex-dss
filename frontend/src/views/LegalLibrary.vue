<script setup>
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { usePageLoader } from '@/composables/usePageLoader'
import LegalLibraryModule from '@/components/modules/LegalLibraryModule.vue'

const { loading } = usePageLoader(300)
</script>

<template>
  <div class="page-wrapper">
    <div v-if="!loading" class="page-enter">
      <LegalLibraryModule />
    </div>
    <div v-else class="page-loading">
      <LoadingSpinner size="lg" text="Memuat halaman..." />
    </div>
  </div>
</template>

<style scoped>
.page-wrapper {
  position: relative;
  min-height: 200px;
  width: 100%;
}

.page-enter {
  animation: pageFadeIn 0.4s ease-out;
}

.page-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  border-radius: 12px;
  z-index: 10;
}

@keyframes pageFadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
