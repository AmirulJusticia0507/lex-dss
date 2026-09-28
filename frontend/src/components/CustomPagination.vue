<script setup>
import { computed } from 'vue'
import { ElButton, ElSelect, ElOption } from 'element-plus'

const props = defineProps({
  currentPage: { type: Number, required: true },
  pageSize: { type: Number, default: 20 },
  total: { type: Number, required: true },
  pageSizes: { type: Array, default: () => [10, 20, 50, 100] },
  maxVisiblePages: { type: Number, default: 5 },
})

const emit = defineEmits(['update:currentPage', 'update:pageSize', 'change'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

const visiblePages = computed(() => {
  const pages = []
  const half = Math.floor(props.maxVisiblePages / 2)
  let start = Math.max(1, props.currentPage - half)
  let end = Math.min(totalPages.value, start + props.maxVisiblePages - 1)

  if (end - start < props.maxVisiblePages - 1) {
    start = Math.max(1, end - props.maxVisiblePages + 1)
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

const hasPrev = computed(() => props.currentPage > 1)
const hasNext = computed(() => props.currentPage < totalPages.value)
const isFirstPage = computed(() => props.currentPage === 1)
const isLastPage = computed(() => props.currentPage === totalPages.value)

function goToPage(p) {
  if (p < 1 || p > totalPages.value || p === props.currentPage) return
  emit('update:currentPage', p)
  emit('change', p)
}

function handleSizeChange(size) {
  emit('update:pageSize', size)
  emit('change', 1)
}
</script>

<template>
  <div v-if="total > 0" class="custom-pagination">
    <div class="pagination-info">
      Showing {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, total) }} of {{ total }}
    </div>

    <div class="pagination-controls">
      <el-select
        :model-value="pageSize"
        size="small"
        style="width: 100px;"
        @change="handleSizeChange"
      >
        <el-option
          v-for="size in pageSizes"
          :key="size"
          :label="`${size} / page`"
          :value="size"
        />
      </el-select>

      <el-button
        size="small"
        :disabled="!hasPrev"
        @click="goToPage(currentPage - 1)"
      >
        &lt;
      </el-button>

      <el-button
        v-if="visiblePages[0] > 1"
        size="small"
        @click="goToPage(1)"
      >
        1
      </el-button>
      <span v-if="visiblePages[0] > 2" class="pagination-ellipsis">...</span>

      <el-button
        v-for="p in visiblePages"
        :key="p"
        size="small"
        :type="p === currentPage ? 'primary' : 'default'"
        @click="goToPage(p)"
      >
        {{ p }}
      </el-button>

      <span v-if="visiblePages[visiblePages.length - 1] < totalPages - 1" class="pagination-ellipsis">...</span>
      <el-button
        v-if="visiblePages[visiblePages.length - 1] < totalPages"
        size="small"
        @click="goToPage(totalPages)"
      >
        {{ totalPages }}
      </el-button>

      <el-button
        size="small"
        :disabled="!hasNext"
        @click="goToPage(currentPage + 1)"
      >
        &gt;
      </el-button>

      <el-button
        size="small"
        :disabled="isLastPage"
        @click="goToPage(totalPages)"
      >
        Last
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.custom-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  flex-wrap: wrap;
  gap: 12px;
}

.pagination-info {
  font-size: 13px;
  color: #6b7280;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pagination-ellipsis {
  padding: 0 4px;
  color: #9ca3af;
  font-size: 13px;
}

@media (max-width: 768px) {
  .custom-pagination {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
