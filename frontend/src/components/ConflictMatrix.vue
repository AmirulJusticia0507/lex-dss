<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  conflicts: {
    type: Array,
    default: () => [],
  },
  articles: {
    type: Array,
    default: () => [],
  },
  width: {
    type: Number,
    default: 800,
  },
  height: {
    type: Number,
    default: 600,
  },
  selectedNode: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['node-click', 'node-hover'])

const containerRef = ref(null)
const svgRef = ref(null)
let simulation = null
let svg = null

const colorScale = d3.scaleOrdinal()
  .domain(['LEX_SUPERIOR', 'LEX_SPECIALIS', 'LEX_POSTERIOR', 'DIRECT_CONTRADICTION'])
  .range(['#dc2626', '#d97706', '#2563eb', '#db2777'])

const severityScale = d3.scaleOrdinal()
  .domain(['HIGH', 'MEDIUM', 'LOW'])
  .range(['#dc2626', '#d97706', '#16a34a'])

function initializeSimulation(nodes, links) {
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(150).strength(0.7))
    .force('charge', d3.forceManyBody().strength(-400))
    .force('center', d3.forceCenter(props.width / 2, props.height / 2))
    .force('collision', d3.forceCollide().radius(d => Math.max(d.radius || 30, 30)).strength(0.8))
    .force('x', d3.forceX(props.width / 2).strength(0.1))
    .force('y', d3.forceY(props.height / 2).strength(0.1))
    .alphaDecay(0.02)
    .velocityDecay(0.4)

  simulation.on('tick', () => {
    if (!svg) return

    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    node
      .attr('transform', d => `translate(${d.x},${d.y})`)
  })
}

function createGraph() {
  if (!containerRef.value) return

  const nodes = props.conflicts.flatMap(conflict => [
    { ...conflict.source_article, id: `source-${conflict.source_article.id}`, type: 'source', conflictId: conflict.id, conflictType: conflict.conflict_type, severity: conflict.severity },
    { ...conflict.target_article, id: `target-${conflict.target_article.id}`, type: 'target', conflictId: conflict.id, conflictType: conflict.conflict_type, severity: conflict.severity },
  ])

  const uniqueNodes = Array.from(new Map(nodes.map(n => [n.id, n])).values())
  const links = props.conflicts.map(conflict => ({
    source: `source-${conflict.source_article.id}`,
    target: `target-${conflict.target_article.id}`,
    conflictId: conflict.id,
    conflictType: conflict.conflict_type,
    severity: conflict.severity,
  }))

  uniqueNodes.forEach((node, i) => {
    node.radius = 30 + (node.article_number?.length || 0) * 2
    node.x = node.x || props.width / 2 + (Math.random() - 0.5) * 200
    node.y = node.y || props.height / 2 + (Math.random() - 0.5) * 200
  })

  initializeSimulation(uniqueNodes, links)

  svg = d3.select(containerRef.value)
    .append('svg')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('viewBox', `0 0 ${props.width} ${props.height}`)
    .attr('preserveAspectRatio', 'xMidYMid meet')

  const defs = svg.append('defs')

  defs.append('marker')
    .attr('id', 'arrowhead')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 25)
    .attr('refY', 0)
    .attr('orient', 'auto')
    .attr('markerWidth', 8)
    .attr('markerHeight', 8)
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', '#9ca3af')

  defs.append('marker')
    .attr('id', 'arrowhead-high')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 25)
    .attr('refY', 0)
    .attr('orient', 'auto')
    .attr('markerWidth', 10)
    .attr('markerHeight', 10)
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', '#dc2626')

  const link = svg.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(links)
    .enter()
    .append('line')
    .attr('class', 'conflict-link')
    .attr('stroke', d => colorScale(d.conflictType))
    .attr('stroke-width', d => d.severity === 'HIGH' ? 3 : d.severity === 'MEDIUM' ? 2 : 1.5)
    .attr('stroke-dasharray', d => d.conflictType === 'DIRECT_CONTRADICTION' ? '8,4' : 'none')
    .attr('marker-end', d => d.severity === 'HIGH' ? 'url(#arrowhead-high)' : 'url(#arrowhead)')
    .style('cursor', 'pointer')
    .on('mouseover', (event, d) => {
      d3.select(event.currentTarget)
        .attr('stroke-width', d => (d.severity === 'HIGH' ? 4 : d.severity === 'MEDIUM' ? 3 : 2.5))
        .attr('stroke-opacity', 1)
      emit('node-hover', { type: 'link', data: d })
    })
    .on('mouseout', (event, d) => {
      d3.select(event.currentTarget)
        .attr('stroke-width', d => d.severity === 'HIGH' ? 3 : d.severity === 'MEDIUM' ? 2 : 1.5)
        .attr('stroke-opacity', 0.6)
    })

  const linkLabels = svg.append('g')
    .attr('class', 'link-labels')
    .selectAll('text')
    .data(links)
    .enter()
    .append('text')
    .attr('class', 'link-label')
    .attr('font-size', '10px')
    .attr('fill', '#6b7280')
    .attr('text-anchor', 'middle')
    .attr('pointer-events', 'none')
    .text(d => d.conflictType.replace('_', ' '))

  const node = svg.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(uniqueNodes)
    .enter()
    .append('g')
    .attr('class', 'conflict-node')
    .attr('data-id', d => d.id)
    .call(drag(simulation))

  node.append('circle')
    .attr('r', d => d.radius)
    .attr('fill', d => d.type === 'source' ? '#dbeafe' : '#fef3c7')
    .attr('stroke', d => colorScale(d.conflictType))
    .attr('stroke-width', d => d.severity === 'HIGH' ? 3 : 2)
    .attr('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))')

  node.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '-0.3em')
    .attr('font-size', '11px')
    .attr('font-weight', 600)
    .attr('fill', '#1e3a5f')
    .text(d => d.article_number || d.id)

  node.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '1.1em')
    .attr('font-size', '9px')
    .attr('fill', '#6b7280')
    .text(d => d.document_title?.substring(0, 20) + (d.document_title?.length > 20 ? '...' : ''))

  node.append('circle')
    .attr('class', 'severity-indicator')
    .attr('cx', d => d.radius - 8)
    .attr('cy', d => -d.radius + 8)
    .attr('r', 6)
    .attr('fill', d => severityScale(d.severity))
    .attr('stroke', 'white')
    .attr('stroke-width', 1.5)

  node.on('click', (event, d) => {
    event.stopPropagation()
    emit('node-click', d)
  })
    .on('mouseover', (event, d) => {
      d3.select(event.currentTarget).select('circle')
        .attr('stroke-width', 4)
        .attr('filter', 'drop-shadow(0 4px 8px rgba(0,0,0,0.2))')
      emit('node-hover', { type: 'node', data: d })
    })
    .on('mouseout', (event, d) => {
      d3.select(event.currentTarget).select('circle')
        .attr('stroke-width', d => d.severity === 'HIGH' ? 3 : 2)
        .attr('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))')
    })

  const legend = svg.append('g')
    .attr('class', 'legend')
    .attr('transform', `translate(20, 20)`)

  const legendData = [
    { type: 'LEX_SUPERIOR', label: 'Lex Superior' },
    { type: 'LEX_SPECIALIS', label: 'Lex Specialis' },
    { type: 'LEX_POSTERIOR', label: 'Lex Posterior' },
    { type: 'DIRECT_CONTRADICTION', label: 'Direct Contradiction' },
  ]

  legendData.forEach((item, i) => {
    const g = legend.append('g')
      .attr('transform', `translate(0, ${i * 24})`)

    g.append('line')
      .attr('x1', 0)
      .attr('x2', 30)
      .attr('y1', 0)
      .attr('y2', 0)
      .attr('stroke', colorScale(item.type))
      .attr('stroke-width', 2)

    g.append('text')
      .attr('x', 38)
      .attr('y', 4)
      .attr('font-size', '12px')
      .attr('fill', '#374151')
      .text(item.label)
  })

  const severityLegend = svg.append('g')
    .attr('class', 'severity-legend')
    .attr('transform', `translate(20, ${20 + legendData.length * 24 + 16})`)

  const severityData = [
    { level: 'HIGH', label: 'High Severity' },
    { level: 'MEDIUM', label: 'Medium Severity' },
    { level: 'LOW', label: 'Low Severity' },
  ]

  severityData.forEach((item, i) => {
    const g = severityLegend.append('g')
      .attr('transform', `translate(0, ${i * 24})`)

    g.append('circle')
      .attr('cx', 8)
      .attr('cy', 0)
      .attr('r', 8)
      .attr('fill', severityScale(item.level))
      .attr('stroke', 'white')
      .attr('stroke-width', 1.5)

    g.append('text')
      .attr('x', 22)
      .attr('y', 4)
      .attr('font-size', '12px')
      .attr('fill', '#374151')
      .text(item.label)
  })

  return { node, link, linkLabels }
}

function drag(simulation) {
  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    d.fx = d.x
    d.fy = d.y
  }

  function dragged(event, d) {
    d.fx = event.x
    d.fy = event.y
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0)
    d.fx = null
    d.fy = null
  }

  return d3.drag()
    .on('start', dragstarted)
    .on('drag', dragged)
    .on('end', dragended)
}

function destroyGraph() {
  if (simulation) {
    simulation.stop()
    simulation = null
  }
  if (svg) {
    svg.remove()
    svg = null
  }
}

onMounted(() => {
  nextTick(() => {
    createGraph()
  })
})

onUnmounted(() => {
  destroyGraph()
})

watch(() => props.conflicts, () => {
  destroyGraph()
  nextTick(() => {
    createGraph()
  })
}, { deep: true })

watch(() => [props.width, props.height], () => {
  if (simulation) {
    simulation.force('center', d3.forceCenter(props.width / 2, props.height / 2))
    simulation.alpha(0.3).restart()
  }
})

defineExpose({
  destroyGraph,
  createGraph,
})
</script>

<template>
  <div
    ref="containerRef"
    class="conflict-matrix-container"
    style="width: 100%; height: 100%; min-height: 500px;"
  >
    <div v-if="conflicts.length === 0" class="empty-state">
      <div class="empty-icon"><i class="el-icon-s-data"></i></div>
      <p>Tidak ada data kontradiksi norma untuk divisualisasikan</p>
      <p class="empty-hint">Jalankan analisis kontradiksi dari menu Conflict Checker</p>
    </div>
  </div>
</template>

<style scoped>
.conflict-matrix-container {
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
  color: #9ca3af;
  text-align: center;
  padding: 40px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-hint {
  font-size: 13px;
  margin-top: 8px;
  opacity: 0.7;
}

.link-label {
  pointer-events: none;
  user-select: none;
}

.conflict-node text {
  user-select: none;
  pointer-events: none;
}

.legend text,
.severity-legend text {
  user-select: none;
}
</style>