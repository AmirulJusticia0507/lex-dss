<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  riskScore: {
    type: Number,
    default: 0,
  },
  riskLevel: {
    type: String,
    default: 'LOW',
  },
  riskFactors: {
    type: Array,
    default: () => [],
  },
  mitigationSteps: {
    type: Array,
    default: () => [],
  },
  trend: {
    type: Object,
    default: null,
  },
  animate: {
    type: Boolean,
    default: true,
  },
  size: {
    type: Number,
    default: 200,
  },
})

const emits = defineEmits(['factor-click'])

const animatedScore = ref(0)
const showDetails = ref(false)
const svgRef = ref(null)

const scoreColor = computed(() => {
  if (props.riskScore >= 75) return '#dc2626'
  if (props.riskScore >= 50) return '#d97706'
  if (props.riskScore >= 25) return '#ca8a04'
  return '#16a34a'
})

const scoreLabel = computed(() => {
  if (props.riskScore >= 75) return 'SANGAT TINGGI'
  if (props.riskScore >= 50) return 'TINGGI'
  if (props.riskScore >= 25) return 'SEDANG'
  return 'RENDAH'
})

const circumference = computed(() => 2 * Math.PI * 80)

const strokeDashoffset = computed(() => {
  const progress = props.riskScore / 100
  return circumference.value * (1 - progress)
})

onMounted(() => {
  if (props.animate) {
    animateScore()
  } else {
    animatedScore.value = props.riskScore
  }
})

watch(() => props.riskScore, (newScore) => {
  if (props.animate) {
    animateScore(newScore)
  } else {
    animatedScore.value = newScore
  }
})

function animateScore(targetScore = props.riskScore) {
  const startScore = animatedScore.value
  const duration = 1000
  const startTime = performance.now()

  function animate(currentTime) {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    const easedProgress = 1 - Math.pow(1 - progress, 3)
    animatedScore.value = startScore + (targetScore - startScore) * easedProgress

    if (progress < 1) {
      requestAnimationFrame(animate)
    }
  }

  requestAnimationFrame(animate)
}

function getRiskLevelClass(level) {
  const classes = {
    'SANGAT TINGGI': 'very-high',
    'TINGGI': 'high',
    'SEDANG': 'medium',
    'RENDAH': 'low',
  }
  return classes[level] || 'low'
}

function toggleDetails() {
  showDetails.value = !showDetails.value
}

function handleFactorClick(factor) {
  emits('factor-click', factor)
}
</script>

<template>
  <div class="risk-score-card">
    <div class="card-header-main">
      <div>
        <h3 class="card-title">Risk Score</h3>
        <p class="card-subtitle">Penilaian Risiko Hukum</p>
      </div>
      <el-button
        size="small"
        :plain="true"
        @click="toggleDetails"
        class="details-toggle"
      >
        <i :class="showDetails ? 'el-icon-arrow-up' : 'el-icon-arrow-down'"></i>
        Detail
      </el-button>
    </div>

    <div class="score-visualization">
      <svg :width="size" :height="size" ref="svgRef" class="risk-score-circle">
        <circle
          class="risk-score-bg"
          :cx="size / 2"
          :cy="size / 2"
          r="80"
        />
        <circle
          class="risk-score-progress"
          :cx="size / 2"
          :cy="size / 2"
          r="80"
          :stroke="scoreColor"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="strokeDashoffset"
          style="transition: stroke-dashoffset 1s ease-out;"
        />
        <text
          class="risk-score-text"
          :x="size / 2"
          :y="size / 2 - 10"
          :font-size="size * 0.18"
          :fill="scoreColor"
          font-weight="700"
          font-family="'Merriweather', serif"
        >
          {{ animatedScore.toFixed(0) }}
        </text>
        <text
          class="risk-score-text"
          :x="size / 2"
          :y="size / 2 + 25"
          :font-size="size * 0.07"
          fill="#6b7280"
          font-weight="500"
        >
          / 100
        </text>
      </svg>

      <div class="score-labels">
        <div class="score-level" :class="getRiskLevelClass(scoreLabel)">
          {{ scoreLabel }}
        </div>
        <div class="score-description">
          {{ getRiskDescription(props.riskLevel) }}
        </div>
      </div>
    </div>

    <transition name="slide">
      <div v-if="showDetails" class="risk-details">
        <div class="detail-section" v-if="riskFactors.length > 0">
          <h4 class="detail-title">Faktor Risiko</h4>
          <div class="factors-list">
            <div
              v-for="(factor, index) in riskFactors"
              :key="factor.id || index"
              class="factor-item"
              @click="handleFactorClick(factor)"
            >
              <div class="factor-indicator" :style="{ backgroundColor: getFactorColor(factor.severity) }"></div>
              <div class="factor-content">
                <div class="factor-title">{{ factor.title }}</div>
                <div class="factor-desc">{{ factor.description }}</div>
              </div>
              <el-tag :type="getSeverityType(factor.severity)" size="small" effect="plain">
                {{ factor.severity }}
              </el-tag>
            </div>
          </div>
        </div>

        <div class="detail-section" v-if="mitigationSteps.length > 0">
          <h4 class="detail-title">Langkah Mitigasi</h4>
          <ol class="mitigation-list">
            <li v-for="(step, index) in mitigationSteps" :key="index" class="mitigation-item">
              <span class="mitigation-number">{{ index + 1 }}</span>
              <span class="mitigation-text">{{ step }}</span>
            </li>
          </ol>
        </div>

        <div class="detail-section" v-if="trend">
          <h4 class="detail-title">Trend Risiko</h4>
          <div class="trend-display">
            <div class="trend-value" :class="trend.direction === 'up' ? 'negative' : trend.direction === 'down' ? 'positive' : 'neutral'">
              <i :class="trend.direction === 'up' ? 'el-icon-arrow-up' : trend.direction === 'down' ? 'el-icon-arrow-down' : 'el-icon-minus'"></i>
              {{ trend.percentage }}%
            </div>
            <div class="trend-label">{{ trend.label }}</div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
export default {
  methods: {
    getRiskDescription(level) {
      const descriptions = {
        'SANGAT TINGGI': 'Risiko hukum sangat tinggi, diperlukan tindakan segera dan konsultasi ahli hukum',
        'TINGGI': 'Risiko hukum tinggi, disarankan revisi draf dan review mendalam',
        'SEDANG': 'Risiko hukum sedang, perlu perhatian pada klausul-klaul spesifik',
        'RENDAH': 'Risiko hukum rendah, draf relatif aman namun tetap perlu review rutin',
      }
      return descriptions[level] || descriptions['RENDAH']
    },
    getFactorColor(severity) {
      const colors = {
        HIGH: '#dc2626',
        MEDIUM: '#d97706',
        LOW: '#16a34a',
      }
      return colors[severity] || '#6b7280'
    },
    getSeverityType(severity) {
      const types = {
        HIGH: 'danger',
        MEDIUM: 'warning',
        LOW: 'success',
      }
      return types[severity] || 'info'
    },
  },
}
</script>

<style scoped>
.risk-score-card {
  background: var(--bg-tertiary);
  border-radius: 12px;
  border: 1px solid var(--border-light);
  padding: 24px;
  transition: all 0.2s ease;
}

.risk-score-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.card-header-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--legal-dark);
  margin-bottom: 4px;
}

.card-subtitle {
  font-size: 12px;
  color: #9ca3af;
}

.details-toggle {
  color: #6b7280;
}

.details-toggle:hover {
  color: #0ea5e9;
}

.score-visualization {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
}

.score-labels {
  margin-top: 16px;
  text-align: center;
}

.score-level {
  display: inline-block;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.score-level.very-high { background: #fee2e2; color: #dc2626; }
.score-level.high { background: #fef3c7; color: #d97706; }
.score-level.medium { background: #fef9c3; color: #ca8a04; }
.score-level.low { background: #dcfce7; color: #16a34a; }

.score-description {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
}

.risk-details {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-title {
  font-size: 13px;
  font-weight: 600;
  color: #1e3a5f;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f3f4f6;
}

.factors-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.factor-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.factor-item:hover {
  background: #f0f9ff;
  border-color: #bae6fd;
}

.factor-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

.factor-content {
  flex: 1;
  min-width: 0;
}

.factor-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.factor-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.mitigation-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-left: 0;
  list-style: none;
}

.mitigation-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: #f0fdf4;
  border-radius: 8px;
  border: 1px solid #dcfce7;
}

.mitigation-number {
  width: 24px;
  height: 24px;
  background: #16a34a;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.mitigation-text {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.5;
  flex: 1;
}

.trend-display {
  display: flex;
  align-items: center;
  gap: 12px;
}

.trend-value {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 18px;
  font-weight: 700;
  font-family: 'Merriweather', serif;
}

.trend-value.positive { color: #16a34a; }
.trend-value.negative { color: #dc2626; }
.trend-value.neutral { color: #6b7280; }

.trend-label {
  font-size: 13px;
  color: #6b7280;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
  max-height: 0;
}
</style>
