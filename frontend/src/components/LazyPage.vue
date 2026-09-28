<template>
  <div class="page-wrapper">
    <transition name="page" mode="out-in">
      <div v-if="!loading" class="page-enter">
        <slot />
      </div>
      <div v-else class="page-loading">
        <LoadingSpinner :size="spinnerSize" :text="loadingText" />
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import LoadingSpinner from './LoadingSpinner.vue'

const props = defineProps({
  spinnerSize: {
    type: String,
    default: 'lg',
  },
  loadingText: {
    type: String,
    default: 'Memuat halaman...',
  },
  delay: {
    type: Number,
    default: 200,
  },
})

const loading = ref(false)
let timer = null

onMounted(() => {
  loading.value = true
  timer = setTimeout(() => {
    loading.value = false
  }, props.delay)
})
</script>

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