<template>
  <el-container class="layout-container">
    <el-aside width="200px">
      <div class="logo">仓库管理系统</div>
      <el-menu
        :default-active="route.path"
        class="el-menu-vertical"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/inbound">
          <el-icon><Download /></el-icon>
          <span>入库管理</span>
        </el-menu-item>
        <el-menu-item index="/outbound">
          <el-icon><Upload /></el-icon>
          <span>出库管理</span>
        </el-menu-item>
        <el-menu-item index="/transit">
          <el-icon><Van /></el-icon>
          <span>在途库存</span>
        </el-menu-item>
        <el-menu-item index="/inventory">
          <el-icon><Box /></el-icon>
          <span>实时库存</span>
        </el-menu-item>
        <el-menu-item index="/borrow">
          <el-icon><List /></el-icon>
          <span>借用管理</span>
        </el-menu-item>
        <el-menu-item index="/movement">
          <el-icon><Switch /></el-icon>
          <span>移库管理</span>
        </el-menu-item>
        <el-menu-item index="/inventory-check">
          <el-icon><Finished /></el-icon>
          <span>盘点管理</span>
        </el-menu-item>
        <el-sub-menu v-if="isAdmin" index="/system">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/system">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
          <el-menu-item index="/materials">
            <el-icon><Goods /></el-icon>
            <span>物料管理</span>
          </el-menu-item>
          <el-menu-item index="/locations">
            <el-icon><MapLocation /></el-icon>
            <span>库位管理</span>
          </el-menu-item>
          <el-menu-item index="/transaction">
            <el-icon><List /></el-icon>
            <span>操作流水</span>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header>
        <div class="header-right">
          <el-button type="danger" @click="handleLogout" size="small">退出登录</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view></router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { ref } from 'vue'
import { Odometer, Goods, MapLocation, Download, Upload, Box, Setting, Switch, Finished, Van, List } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const isAdmin = ref(localStorage.getItem('role') === 'admin')

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  localStorage.removeItem('username')
  router.push('/login')
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}
.el-aside {
  background-color: #304156;
}
.el-menu-vertical .el-icon {
  font-size: 18px;
}
.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 20px;
  font-weight: bold;
}
.el-menu-vertical {
  border-right: none;
}
.el-header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  justify-content: flex-end;
  align-items: center;
}
</style>
