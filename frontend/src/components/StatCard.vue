<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [Number, String], default: 0 },
  icon: { type: [Object, Function], default: null },
  accent: { type: String, default: 'primary' },
  trend: { type: String, default: '' },
  trendDirection: { type: String, default: 'up' },
  hint: { type: String, default: '' },
  suffix: { type: String, default: '' },
})

const accentVar = computed(() => `var(--stat-${props.accent})`)
const formatted = computed(() =>
  typeof props.value === 'number' ? props.value.toLocaleString('id-ID') : props.value
)
</script>

<template>
  <div class="stat-card" :style="{ '--stat-accent': accentVar }">
    <div class="stat-top">
      <span class="stat-label">{{ label }}</span>
      <span v-if="icon" class="stat-icon"><el-icon><component :is="icon" /></el-icon></span>
    </div>

    <div class="stat-value-row">
      <span class="stat-value">{{ formatted }}</span>
      <span v-if="suffix" class="stat-suffix">{{ suffix }}</span>
    </div>

    <div class="stat-foot">
      <span v-if="trend" class="stat-trend" :class="trendDirection">
        <i :class="trendDirection === 'down' ? 'el-icon-bottom' : trendDirection === 'flat' ? 'el-icon-minus' : 'el-icon-top'" />
        {{ trend }}
      </span>
      <span v-else-if="hint" class="stat-hint">{{ hint }}</span>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition-normal), transform var(--transition-normal);
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.stat-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  min-height: 36px;
}

.stat-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  line-height: 1.35;
  letter-spacing: 0.01em;
}

.stat-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: 8px;
  font-size: 16px;
  color: var(--stat-accent);
  background: var(--stat-accent-soft);
}

.stat-value-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.stat-value {
  font-family: 'Merriweather', serif;
  font-size: 30px;
  font-weight: 700;
  line-height: 1.1;
  color: var(--stat-accent);
  letter-spacing: -0.01em;
}

.stat-suffix {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-secondary);
}

.stat-foot {
  margin-top: auto;
  padding-top: 4px;
  min-height: 18px;
}

.stat-trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
}

.stat-trend.up { color: var(--success-color); }
.stat-trend.down { color: var(--danger-color); }
.stat-trend.flat { color: var(--text-tertiary); }

.stat-hint {
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>
