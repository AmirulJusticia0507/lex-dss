<script setup>
import { computed } from 'vue'
import { ElMenu, ElMenuItem, ElIcon } from 'element-plus'
import { Monitor, Warning, DataAnalysis, Collection, Setting, User, Document, Files } from '@element-plus/icons-vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores'

const props = defineProps({
  collapsed: { type: Boolean, default: false },
})

const emit = defineEmits(['navigate'])

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

const menuItems = [
  { path: '/dashboard', label: 'Dashboard', icon: Monitor },
  { path: '/conflict-checker', label: 'Conflict Checker', icon: Warning },
  { path: '/dss-panel', label: 'DSS Panel', icon: DataAnalysis },
  { path: '/legal-library', label: 'Legal Library', icon: Collection },
  { path: '/case-law', label: 'Case Law Search', icon: Files },
  { path: '/contract-analyzer', label: 'Contract Analyzer', icon: Document },
  { path: '/profile', label: 'Profil & Akun', icon: User },
  { path: '/settings', label: 'Pengaturan', icon: Setting },
]

function handleSelect(key) {
  router.push(key)
  emit('navigate')
}
</script>

<template>
  <div class="sidebar">
    <div class="logo-container">
      <div class="logo-icon">
        <svg width="24" height="24" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M16 4C10.48 4 6 8.48 6 14c0 2.5 0.9 4.8 2.4 6.6L16 28l7.6-7.4C25.1 18.8 26 16.5 26 14c0-5.52-4.48-10-10-10z" stroke="currentColor" stroke-width="1.8" fill="none"/>
          <path d="M10 14h12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
          <circle cx="16" cy="14" r="2" fill="currentColor"/>
          <path d="M8 22h16M8 25h12M8 28h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.9"/>
        </svg>
      </div>
      <span v-show="!collapsed" class="logo-text">Lex-DSS</span>
    </div>

    <nav class="nav-menu" aria-label="Main navigation">
      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        :unique-opened="true"
        :router="true"
        mode="vertical"
        @select="handleSelect"
        class="nav-menu-el"
      >
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.label }}</template>
        </el-menu-item>
      </el-menu>
    </nav>

    <div class="user-profile">
      <div class="user-avatar">
        <el-icon><User /></el-icon>
      </div>
      <div v-show="!collapsed" class="user-info">
        <div class="user-name">{{ authStore.user?.full_name || authStore.user?.email || 'Pengguna' }}</div>
        <div class="user-role">{{ authStore.user?.role || 'user' }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: linear-gradient(180deg, var(--sidebar-bg) 0%, #0f2744 100%);
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: linear-gradient(135deg, #0ea5e9, #c9a84c);
  color: white;
  flex-shrink: 0;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: white;
  letter-spacing: -0.02em;
}

.nav-menu {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px 0;
}

.nav-menu-el {
  border: none;
  background: transparent;
}

.nav-menu-el .el-menu-item {
  border-radius: 10px;
  margin: 2px 12px;
  height: auto;
  padding: 12px 16px;
  color: rgba(255, 255, 255, 0.75);
  transition: all 0.2s ease;
}

.nav-menu-el .el-menu-item:hover {
  background-color: rgba(255, 255, 255, 0.08) !important;
  color: white !important;
}

.nav-menu-el .el-menu-item.is-active {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.25), rgba(201, 168, 76, 0.25)) !important;
  color: white !important;
  border-left: 3px solid #c9a84c;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.8);
  flex-shrink: 0;
}

.user-info {
  min-width: 0;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: white;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  text-transform: capitalize;
}

.nav-menu::-webkit-scrollbar {
  width: 4px;
}

.nav-menu::-webkit-scrollbar-track {
  background: transparent;
}

.nav-menu::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}
</style>
