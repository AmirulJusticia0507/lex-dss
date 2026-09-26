<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  draftText: {
    type: String,
    default: '',
  },
  references: {
    type: Array,
    default: () => [],
  },
  aiRecommendation: {
    type: Object,
    default: null,
  },
  conflicts: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['reference-click', 'conflict-click', 'export-opinion'])

const activeReference = ref(null)
const activeConflict = ref(null)
const searchQuery = ref('')
const showHighlights = ref(true)

const filteredReferences = computed(() => {
  if (!searchQuery.value) return props.references
  const query = searchQuery.value.toLowerCase()
  return props.references.filter(ref =>
    ref.title?.toLowerCase().includes(query) ||
    ref.content?.toLowerCase().includes(query) ||
    ref.article_number?.toLowerCase().includes(query)
  )
})

const highlightedDraft = computed(() => {
  if (!props.draftText || !showHighlights.value) return props.draftText

  let html = props.draftText

  props.conflicts.forEach(conflict => {
    const sourceText = conflict.source_article?.content?.substring(0, 100)
    if (sourceText && html.includes(sourceText)) {
      html = html.replace(
        new RegExp(sourceText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'),
        `<span class="conflict-highlight" data-conflict-id="${conflict.id}">${sourceText}</span>`
      )
    }
  })

  return html
})

function selectReference(reference) {
  activeReference.value = activeReference.value?.id === reference.id ? null : reference
  emit('reference-click', reference)
}

function selectConflict(conflict) {
  activeConflict.value = activeConflict.value?.id === conflict.id ? null : conflict
  emit('conflict-click', conflict)
}

function handleExport() {
  emit('export-opinion')
}

function getSeverityClass(severity) {
  const classes = {
    HIGH: 'high',
    MEDIUM: 'medium',
    LOW: 'low',
  }
  return classes[severity] || 'low'
}

function getConflictTypeLabel(type) {
  const labels = {
    LEX_SUPERIOR: 'Lex Superior',
    LEX_SPECIALIS: 'Lex Specialis',
    LEX_POSTERIOR: 'Lex Posterior',
    DIRECT_CONTRADICTION: 'Direct Contradiction',
  }
  return labels[type] || type
}

function getConflictTypeClass(type) {
  return `conflict-type-badge ${type.toLowerCase().replace('_', '-')}`
}

function formatDate(dateString) {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('id-ID', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div class="legal-opinion-panel">
    <div class="panel-section">
      <div class="panel-header">
        <span class="panel-title">Draf Hukum / Input</span>
        <div class="panel-actions">
          <el-switch
            v-model="showHighlights"
            size="small"
            active-text="Highlight"
            inactive-text="Plain"
          />
        </div>
      </div>
      <div class="panel-content">
        <div
          v-if="loading"
          class="loading-placeholder"
        >
          <div class="loading-spinner"></div>
          <p>Menganalisis draf...</p>
        </div>
        <div
          v-else-if="!draftText"
          class="empty-placeholder"
        >
          <i class="el-icon-document" style="font-size: 48px; color: #d1d5db;"></i>
          <p style="margin-top: 16px; color: #9ca3af;">Belum ada draf hukum yang dimasukkan</p>
          <p style="font-size: 12px; color: #9ca3af;">Masukkan teks draf di Conflict Checker untuk memulai analisis</p>
        </div>
        <div
          v-else
          class="document-text"
          v-html="highlightedDraft"
        ></div>
      </div>
    </div>

    <div class="panel-section">
      <div class="panel-header">
        <span class="panel-title">Referensi Hukum Terkait</span>
        <el-input
          v-model="searchQuery"
          size="small"
          placeholder="Cari referensi..."
          prefix-icon="Search"
          clearable
          style="width: 200px;"
        />
      </div>
      <div class="panel-content">
        <div v-if="filteredReferences.length === 0" class="empty-placeholder">
          <i class="el-icon-search" style="font-size: 32px; color: #d1d5db;"></i>
          <p style="margin-top: 12px; color: #9ca3af;">
            {{ searchQuery ? 'Tidak ada referensi yang cocok' : 'Tidak ada referensi hukum ditemukan' }}
          </p>
        </div>
        <div v-else class="references-list">
          <div
            v-for="ref in filteredReferences"
            :key="ref.id"
            class="reference-item"
            :class="{ active: activeReference?.id === ref.id }"
            @click="selectReference(ref)"
          >
            <div class="reference-title">
              {{ ref.document_title }} - Pasal {{ ref.article_number }}
            </div>
            <div class="reference-content">{{ ref.content?.substring(0, 200) }}{{ ref.content?.length > 200 ? '...' : '' }}</div>
            <div class="reference-meta">
              <span><i class="el-icon-collection-tag"></i> {{ ref.domain || 'Umum' }}</span>
              <span><i class="el-icon-rank"></i> Hierarki: {{ ref.hierarchy_rank || '-' }}</span>
              <span v-if="ref.similarity_score"><i class="el-icon-data-analysis"></i> Similarity: {{ (ref.similarity_score * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="panel-section">
      <div class="panel-header">
        <span class="panel-title">Rekomendasi AI & Legal Opinion</span>
        <el-button
          size="small"
          type="primary"
          @click="handleExport"
          :disabled="!aiRecommendation"
        >
          <i class="el-icon-download"></i> Export
        </el-button>
      </div>
      <div class="panel-content">
        <div v-if="loading" class="loading-placeholder">
          <div class="loading-spinner"></div>
          <p>Menghasilkan rekomendasi AI...</p>
        </div>
        <div v-else-if="!aiRecommendation" class="empty-placeholder">
          <i class="el-icon-cpu" style="font-size: 48px; color: #d1d5db;"></i>
          <p style="margin-top: 16px; color: #9ca3af;">Belum ada rekomendasi AI</p>
          <p style="font-size: 12px; color: #9ca3af;">Klik 'Generate Opinion' di DSS Panel untuk memulai</p>
        </div>
        <div v-else class="ai-recommendation">
          <div class="recommendation-header">
            <span
              class="recommendation-badge"
              :class="getSeverityClass(aiRecommendation.risk_level)"
            >
              {{ aiRecommendation.risk_level || 'LOW' }} RISK
            </span>
            <el-tag
              v-if="aiRecommendation.confidence_score"
              size="small"
              :type="aiRecommendation.confidence_score > 0.8 ? 'success' : aiRecommendation.confidence_score > 0.5 ? 'warning' : 'danger'"
            >
              Confidence: {{ (aiRecommendation.confidence_score * 100).toFixed(0) }}%
            </el-tag>
          </div>

          <div class="recommendation-section" v-if="aiRecommendation.summary">
            <h4 style="font-size: 14px; font-weight: 600; color: #1e3a5f; margin-bottom: 8px;">Executive Summary</h4>
            <p style="font-size: 13px; color: #374151; line-height: 1.7;">{{ aiRecommendation.summary }}</p>
          </div>

          <div class="recommendation-section" v-if="aiRecommendation.legal_basis?.length">
            <h4 style="font-size: 14px; font-weight: 600; color: #1e3a5f; margin-bottom: 8px;">Dasar Hukum</h4>
            <div v-for="basis in aiRecommendation.legal_basis" :key="basis.id" class="reference-item" style="margin-bottom: 8px;">
              <div class="reference-title">{{ basis.article_reference }}</div>
              <div class="reference-content">{{ basis.explanation }}</div>
            </div>
          </div>

          <div class="recommendation-section" v-if="aiRecommendation.ratio_decidendi">
            <h4 style="font-size: 14px; font-weight: 600; color: #1e3a5f; margin-bottom: 8px;">Ratio Decidendi</h4>
            <p style="font-size: 13px; color: #374151; line-height: 1.7; white-space: pre-wrap;">{{ aiRecommendation.ratio_decidendi }}</p>
          </div>

          <div class="recommendation-section" v-if="aiRecommendation.recommendations?.length">
            <h4 style="font-size: 14px; font-weight: 600; color: #1e3a5f; margin-bottom: 8px;">Rekomendasi Tindak Lanjut</h4>
            <ol style="font-size: 13px; color: #374151; line-height: 1.8; padding-left: 20px;">
              <li v-for="(rec, idx) in aiRecommendation.recommendations" :key="idx">{{ rec }}</li>
            </ol>
          </div>

          <div class="recommendation-section" v-if="conflicts.length > 0">
            <h4 style="font-size: 14px; font-weight: 600; color: #1e3a5f; margin-bottom: 8px;">Kontradiksi Terdeteksi ({{ conflicts.length }})</h4>
            <div v-for="conflict in conflicts" :key="conflict.id" class="reference-item" style="margin-bottom: 8px;" @click="selectConflict(conflict)">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                <span class="reference-title">{{ conflict.source_article?.document_title }} vs {{ conflict.target_article?.document_title }}</span>
                <span :class="getConflictTypeClass(conflict.conflict_type)">{{ getConflictTypeLabel(conflict.conflict_type) }}</span>
              </div>
              <div class="reference-content">{{ conflict.description }}</div>
              <div class="reference-meta">
                <el-tag :type="getSeverityClass(conflict.severity)" size="small" effect="plain">{{ conflict.severity }}</el-tag>
                <span>{{ formatDate(conflict.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.references-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reference-item {
  cursor: pointer;
  transition: all 0.2s ease;
}

.reference-item:hover {
  border-color: #0ea5e9;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1);
}

.reference-item.active {
  border-color: #0ea5e9;
  background: #f0f9ff;
}

.recommendation-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.recommendation-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.loading-placeholder,
.empty-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  color: #9ca3af;
  text-align: center;
  padding: 20px;
}

.loading-placeholder p,
.empty-placeholder p {
  margin: 8px 0;
}

.document-text .conflict-highlight {
  background: #fee2e2;
  border-left: 3px solid #ef4444;
  padding: 4px 8px;
  margin: 4px 0;
  border-radius: 0 6px 6px 0;
  display: inline-block;
}
</style>