<template>
  <div class="mobile-home">
    <el-card shadow="hover" class="welcome">
      <div class="welcome-title">手机操作入口</div>
      <div class="welcome-sub">建议将此页面添加到手机桌面</div>
    </el-card>

    <div class="grid">
      <button class="grid-item" @click="go('/m/inbound?transit=1')">
        <el-icon><Van /></el-icon>
        <div class="name">在途入库</div>
      </button>
      <button class="grid-item" @click="go('/m/outbound?create=1')">
        <el-icon><Upload /></el-icon>
        <div class="name">创建出库单</div>
      </button>
      <button class="grid-item" @click="go('/m/inventory')">
        <el-icon><Box /></el-icon>
        <div class="name">实时库存</div>
      </button>
      <button class="grid-item" @click="go('/m/borrow')">
        <el-icon><List /></el-icon>
        <div class="name">借用管理</div>
      </button>
      <button class="grid-item" @click="go('/m/movement')">
        <el-icon><Switch /></el-icon>
        <div class="name">移库管理</div>
      </button>
      <button class="grid-item" @click="go('/m/inventory-check')">
        <el-icon><Finished /></el-icon>
        <div class="name">盘点管理</div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Van, Upload, Box, List, Switch, Finished } from '@element-plus/icons-vue'

const router = useRouter()

const go = (to: string) => {
  router.push(to)
}
</script>

<style scoped>
.mobile-home {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.welcome {
  border-radius: 12px;
}
.welcome-title {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
}
.welcome-sub {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
.grid-item {
  border: 1px solid #ebeef5;
  background: #fff;
  border-radius: 14px;
  padding: 16px 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.grid-item :deep(.el-icon) {
  font-size: 28px;
  color: #409eff;
}
.name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
</style>

