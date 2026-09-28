<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMenu, ElMenuItem, ElSubMenu, ElIcon, ElAvatar, ElDropdown, ElDropdownMenu, ElDropdownItem, ElTooltip } from 'element-plus'
import {
  Monitor, Warning, DataAnalysis, Collection, Setting, User, Lock, SwitchButton, Moon, Sunny, Bell, Message, ArrowRight, FullScreen, Fold, Expand, DataBoard, Document, Cpu, TrendCharts, InfoFilled, QuestionFilled
} from '@element-plus/icons-vue'
import { useUIStore } from '@/stores'
import { useAuthStore } from '@/stores'
import { authApi } from '@/api'

const router = useRouter()
const route = useRoute()
const uiStore = useUIStore()
const authStore = useAuthStore()
onMounted(async () => {
  if (!authStore.token) return
  try {
    const { data } = await authApi.getProfile()
    authStore.user = data
  } catch {
    authStore.logout()
  }
})

const isCollapsed = ref(false)
const activeMenu = ref(route.path)
const isLoginRoute = computed(() => route.name === 'Login')
const isPublicInfoRoute = computed(() => Boolean(route.meta.infoPage))
watch(() => route.path, path => { activeMenu.value = path })
const notifications = ref([
  { id: 1, title: 'Analisis kontradiksi selesai', message: 'Ditemukan 3 kontradiksi baru pada UU No. 12/2011', time: '5 menit lalu', read: false, type: 'warning' },
  { id: 2, title: 'Legal Opinion generated', message: 'Rekomendasi AI untuk draf Perda Pajak Daerah telah siap', time: '1 jam lalu', read: false, type: 'success' },
  { id: 3, title: 'Update basis data hukum', message: '15 pasal baru dari UU No. 1/2023 ditambahkan', time: '3 jam lalu', read: true, type: 'info' },
])

const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)

const menuItems = [
  { path: '/dashboard', label: 'Dashboard', icon: Monitor },
  { path: '/conflict-checker', label: 'Conflict Checker', icon: Warning },
  { path: '/dss-panel', label: 'DSS Panel', icon: DataAnalysis },
  { path: '/legal-library', label: 'Legal Library', icon: Collection },
  { path: '/profile', label: 'Profil & Akun', icon: User },
  { path: '/settings', label: 'Pengaturan', icon: Setting },
]

function handleMenuClick(item) {
  activeMenu.value = item.path
  router.push(item.path)
}

function handleSelect(key, keyPath) {
  activeMenu.value = key
  router.push(key)
}

function toggleSidebar() {
  isCollapsed.value = !isCollapsed.value
  uiStore.setSidebarCollapsed(isCollapsed.value)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function handleNotificationClick(notification) {
  notification.read = true
}

function markAllRead() {
  notifications.value.forEach(n => n.read = true)
}

function getNotificationTypeClass(type) {
  const classes = {
    warning: 'warning',
    success: 'success',
    info: 'info',
    danger: 'danger',
  }
  return classes[type] || 'info'
}
</script>

<template>
  <el-container class="app-container">
    <el-aside v-if="!isLoginRoute && !isPublicInfoRoute" :width="isCollapsed ? '64px' : '280px'" class="sidebar">
      <div class="logo-container">
<div class="logo-icon">
  <svg width="24" height="24" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M16 4C10.48 4 6 8.48 6 14c0 2.5 0.9 4.8 2.4 6.6L16 28l7.6-7.4C25.1 18.8 26 16.5 26 14c0-5.52-4.48-10-10-10z" stroke="currentColor" stroke-width="1.8" fill="none"/>
    <path d="M10 14h12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
    <circle cx="16" cy="14" r="2" fill="currentColor"/>
    <path d="M8 22h16M8 25h12M8 28h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.9"/>
  </svg>
</div>
        <span v-show="!isCollapsed" class="logo-text">Lex-DSS</span>
      </div>

      <nav class="nav-menu sidebar-scroll" aria-label="Main navigation">
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapsed"
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
        <div v-show="!isCollapsed" class="user-info">
          <div class="user-name">{{ authStore.user?.full_name || authStore.user?.email || 'Pengguna' }}</div>
          <div class="user-role">{{ authStore.user?.role || 'user' }}</div>
        </div>
      </div>
    </el-aside>

    <el-container class="app-body">
      <el-header v-if="!isLoginRoute && !isPublicInfoRoute" class="header">
        <div class="header-left">
          <el-button
            v-if="!isCollapsed"
            class="sidebar-toggle"
            @click="toggleSidebar"
            circle
            size="small"
          >
            <el-icon><Fold /></el-icon>
          </el-button>
          <el-button
            v-else
            class="sidebar-toggle"
            @click="toggleSidebar"
            circle
            size="small"
          >
            <el-icon><Expand /></el-icon>
          </el-button>

          <h1 v-show="!isCollapsed" class="page-crumb">
            {{ getPageTitle() }}
          </h1>
        </div>

        <div class="header-actions">
          <div class="search-box">
            <el-input
              v-model="searchQuery"
              placeholder="Cari pasal, UU, atau kontradiksi..."
              size="small"
              prefix-icon="Search"
              clearable
            />
          </div>

          <el-dropdown trigger="click">
            <span class="notification-btn">
              <el-icon><Bell /></el-icon>
              <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <div class="notification-header">
                  <span>Notifikasi</span>
                  <el-button v-if="unreadCount > 0" size="small" link @click="markAllRead">Tandai semua dibaca</el-button>
                </div>
                <div class="notification-list">
                  <el-dropdown-item
                    v-for="notif in notifications"
                    :key="notif.id"
                    :class="{ unread: !notif.read }"
                    @click.native="handleNotificationClick(notif)"
                  >
                    <div class="notification-item">
                      <el-tag :type="getNotificationTypeClass(notif.type)" size="small" effect="plain" class="notif-type">{{ notif.type }}</el-tag>
                      <div class="notif-content">
                        <div class="notif-title">{{ notif.title }}</div>
                        <div class="notif-message">{{ notif.message }}</div>
                        <div class="notif-time">{{ notif.time }}</div>
                      </div>
                    </div>
                  </el-dropdown-item>
                  <el-dropdown-item divided class="notif-footer">
                    <el-button size="small" link>Lihat semua notifikasi</el-button>
                  </el-dropdown-item>
                </div>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-dropdown trigger="click">
            <span class="user-dropdown-trigger">
              <el-avatar size="small" src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" />
              <span v-show="!isCollapsed" class="username">{{ authStore.user?.full_name || authStore.user?.email || 'Akun' }}</span>
              <el-icon class="caret-icon"><Message /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/profile')">
                  <el-icon><User /></el-icon>
                  <span>Profil</span>
                </el-dropdown-item>
                <el-dropdown-item @click="router.push('/profile#security')">
                  <el-icon><Lock /></el-icon>
                  <span>Keamanan</span>
                </el-dropdown-item>
                <el-dropdown-item @click="router.push('/tentang')">
                  <el-icon><InfoFilled /></el-icon>
                  <span>Tentang</span>
                </el-dropdown-item>
                <el-dropdown-item @click="router.push('/privasi-cookies')">
                  <el-icon><Document /></el-icon>
                  <span>Privasi &amp; Cookies</span>
                </el-dropdown-item>
                <el-dropdown-item @click="router.push('/bantuan')">
                  <el-icon><QuestionFilled /></el-icon>
                  <span>Bantuan</span>
                </el-dropdown-item>
                <el-dropdown-item divided>
                  <el-icon><SwitchButton /></el-icon>
                  <span>Ganti Organisasi</span>
                </el-dropdown-item>
                <el-dropdown-item @click.native="handleLogout">
                  <el-icon><ArrowRight /></el-icon>
                  <span>Keluar</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content" :class="{ 'standalone-main': isLoginRoute || isPublicInfoRoute }">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
export default {
  data() {
    return {
      searchQuery: '',
    }
  },
  methods: {
    getPageTitle() {
      const titles = {
        '/dashboard': 'Dashboard',
        '/conflict-checker': 'Conflict Checker',
        '/dss-panel': 'DSS Panel',
        '/legal-library': 'Legal Library',
        '/profile': 'Profil & Akun',
        '/settings': 'Pengaturan',
      }
      return titles[this.$route.path] || 'Lex-DSS'
    },
  },
}
</script>

<style scoped>
.app-container {
  height: 100vh;
  max-width: 100%;
  overflow: hidden;
}

@media (max-width: 768px) {
  .app-container { height: 100dvh; }
  .sidebar { width: 68px !important; }
  .logo-text, .user-info, .nav-menu-el .el-menu-item span { display: none !important; }
  .logo-container { justify-content: center; padding: 14px 8px; }
  .nav-menu { padding: 14px 4px; }
  .nav-menu-el .el-menu-item { justify-content: center; margin-inline: 4px; padding-inline: 0 !important; }
  .user-profile { justify-content: center; padding: 12px 8px; }
  .header { height: 64px; padding: 0 14px; }
  .header-actions { gap: 8px; }
  .search-box { display: none; }
  .page-title-header { font-size: 16px; }
  .main-content { padding: 16px !important; }
}

@media (max-width: 480px) {
  .header { padding-inline: 10px; }
  .user-dropdown-trigger { padding: 4px; }
  .caret-icon, .username { display: none; }
  .main-content { padding: 12px !important; }
}

.app-body {
  min-width: 0;
  min-height: 0;
}

.sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-menu-el {
  flex: 1;
  border: none;
  background: transparent;
}

.nav-menu-el .el-menu-item {
  border-radius: 12px;
  margin: 0 8px 6px;
  height: auto;
  padding: 13px 16px;
  color: rgba(255, 255, 255, 0.8);
}

.nav-menu-el .el-menu-item:hover,
.nav-menu-el .el-menu-item.is-active {
  background-color: rgba(255, 255, 255, 0.1) !important;
  color: white !important;
}

.nav-menu-el .el-menu-item.is-active {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.2), rgba(201, 168, 76, 0.2)) !important;
  border-left: 3px solid #c9a84c;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.06);
}

.sidebar-toggle {
  background: transparent;
  border: none;
  color: #6b7280;
}

.sidebar-toggle:hover {
  background: #f3f4f6;
  color: #0ea5e9;
}

.page-crumb {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0;
  letter-spacing: 0.01em;
}

.search-box {
  width: 320px;
}

.notification-btn {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.notification-btn:hover {
  background: #f3f4f6;
  color: #0ea5e9;
}

.notification-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 18px;
  height: 18px;
  background: #ef4444;
  color: white;
  border-radius: 50%;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  color: #1e3a5f;
}

.notification-list {
  max-height: 300px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
}

.notif-type {
  flex-shrink: 0;
  margin-top: 2px;
}

.notif-content {
  flex: 1;
  min-width: 0;
}

.notif-title {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
}

.notif-message {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.notif-time {
  font-size: 11px;
  color: #9ca3af;
}

.notif-footer {
  padding: 8px 16px !important;
}

.user-dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.2s ease;
}

.user-dropdown-trigger:hover {
  background: #f3f4f6;
}

.username {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
}

.caret-icon {
  font-size: 12px;
  color: #9ca3af;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  background: #f4f7fb;
}

.main-content.standalone-main {
  padding: 0 !important;
}

/* Page transition */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.35s ease, transform 0.35s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Scrollbar */
.sidebar-scroll::-webkit-scrollbar,
.main-content::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.sidebar-scroll::-webkit-scrollbar-track,
.main-content::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-scroll::-webkit-scrollbar-thumb,
.main-content::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}

.sidebar-scroll::-webkit-scrollbar-thumb:hover,
.main-content::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}
</style>
