<template>
  <div class="loading-spinner" :class="sizeClass" :style="style">
    <svg class="spinner" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg">
      <circle class="track" cx="25" cy="25" r="20" fill="none" stroke-width="4"/>
      <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="4" stroke-linecap="round"/>
    </svg>
    <p v-if="text" class="loading-text">{{ text }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg', 'xl'].includes(v),
  },
  text: {
    type: String,
    default: '',
  },
  color: {
    type: String,
    default: '#0ea5e9',
  },
})

const sizeClass = computed(() => `spinner-${props.size}`)

const style = computed(() => ({
  '--spinner-color': props.color,
}))
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.spinner {
  width: 100%;
  height: 100%;
  animation: rotate 1s linear infinite;
}

.track {
  stroke: rgba(0, 0, 0, 0.1);
}

.path {
  stroke: var(--spinner-color, #0ea5e9);
  stroke-dasharray: 1, 200;
  stroke-dashoffset: 0;
  animation: dash 1.5s ease-in-out infinite;
}

@keyframes rotate {
  100% { transform: rotate(360deg); }
}

@keyframes dash {
  0% {
    stroke-dasharray: 1, 200;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 89, 200;
    stroke-dashoffset: -35px;
  }
  100% {
    stroke-dasharray: 1, 200;
    stroke-dashoffset: -125px;
  }
}

.loading-text {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

/* Sizes */
.spinner-sm { width: 24px; height: 24px; }
.spinner-md { width: 40px; height: 40px; }
.spinner-lg { width: 56px; height: 56px; }
.spinner-xl { width: 72px; height: 72px; }
</style>