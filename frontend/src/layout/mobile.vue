<template>
  <el-container class="mobile-layout">
    <el-header class="mobile-header">
      <div class="left">
        <el-button :icon="Menu" circle @click="drawerVisible = true" />
        <div class="title">{{ pageTitle }}</div>
      </div>
      <div class="right">
        <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
      </div>
    </el-header>

    <el-main class="mobile-main">
      <router-view />
    </el-main>

    <el-footer class="mobile-footer">
      <div class="tabs">
        <button class="tab" :class="{ active: isActive('/m/home') }" @click="go('/m/home')">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </button>
        <button class="tab" :class="{ active: isActive('/m/inbound') }" @click="go('/m/inbound')">
          <el-icon><Download /></el-icon>
          <span>入库</span>
        </button>
        <button class="tab" :class="{ active: isActive('/m/outbound') }" @click="go('/m/outbound')">
          <el-icon><Upload /></el-icon>
          <span>出库</span>
        </button>
        <button class="tab" :class="{ active: isActive('/m/inventory') }" @click="go('/m/inventory')">
          <el-icon><Box /></el-icon>
          <span>库存</span>
        </button>
        <button class="tab" @click="drawerVisible = true">
          <el-icon><MoreFilled /></el-icon>
          <span>更多</span>
        </button>
      </div>
    </el-footer>
  </el-container>

  <el-drawer v-model="drawerVisible" direction="ltr" size="78%" :with-header="false">
    <div class="drawer-title">功能</div>
    <div class="drawer-list">
      <button class="drawer-item" @click="go('/m/inbound?transit=1')">
        <el-icon><Van /></el-icon>
        <span>在途入库</span>
      </button>
      <button class="drawer-item" @click="go('/m/outbound?create=1')">
        <el-icon><Upload /></el-icon>
        <span>创建出库单</span>
      </button>
      <button class="drawer-item" @click="go('/m/inventory')">
        <el-icon><Box /></el-icon>
        <span>实时库存</span>
      </button>
      <button class="drawer-item" @click="go('/m/borrow')">
        <el-icon><List /></el-icon>
        <span>借用管理</span>
      </button>
      <button class="drawer-item" @click="go('/m/movement')">
        <el-icon><Switch /></el-icon>
        <span>移库管理</span>
      </button>
      <button class="drawer-item" @click="go('/m/inventory-check')">
        <el-icon><Finished /></el-icon>
        <span>盘点管理</span>
      </button>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Menu, HomeFilled, MoreFilled, Download, Upload, Box, Van, List, Switch, Finished } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const drawerVisible = ref(false)

const pageTitle = computed(() => {
  const t = route.meta?.title
  return typeof t === 'string' && t ? t : '仓库管理系统'
})

const isActive = (path: string) => {
  return route.path === path
}

const go = (to: string) => {
  drawerVisible.value = false
  router.push(to)
}

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  localStorage.removeItem('username')
  router.push('/login')
}
</script>

<style scoped>
.mobile-layout {
  height: 100vh;
  background: #f5f6f7;
}
.mobile-header {
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px;
}
.left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.title {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mobile-main {
  padding: 12px;
  overflow: auto;
}
.mobile-main :deep(.inbound-container),
.mobile-main :deep(.outbound-container),
.mobile-main :deep(.inventory-container),
.mobile-main :deep(.transit-container),
.mobile-main :deep(.movement-container),
.mobile-main :deep(.inventory-check-container),
.mobile-main :deep(.borrow-container),
.mobile-main :deep(.materials-container),
.mobile-main :deep(.locations-container),
.mobile-main :deep(.transaction-container),
.mobile-main :deep(.system-container),
.mobile-main :deep(.dashboard-container) {
  padding: 0;
}
.mobile-main :deep(.header-actions) {
  flex-direction: column;
  align-items: stretch;
}
.mobile-main :deep(.left-actions),
.mobile-main :deep(.right-actions) {
  flex-wrap: wrap;
  gap: 10px;
}
.mobile-main :deep(.el-table) {
  font-size: 12px;
}
.mobile-footer {
  background: #fff;
  border-top: 1px solid #ebeef5;
  padding: 0;
}
.tabs {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  height: 56px;
}
.tab {
  border: none;
  background: transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  color: #606266;
  font-size: 12px;
}
.tab.active {
  color: #409eff;
}
.drawer-title {
  font-size: 16px;
  font-weight: 700;
  padding: 10px 6px;
}
.drawer-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  padding: 8px 6px 14px 6px;
}
.drawer-item {
  border: 1px solid #ebeef5;
  background: #fff;
  border-radius: 10px;
  padding: 12px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #303133;
}
</style>
