<template>
  <div class="system-container">
    <el-tabs type="border-card">
      <el-tab-pane label="用户管理">
        <div class="header-actions" style="margin-bottom: 20px;">
          <el-button type="primary" @click="openDialog">新增用户</el-button>
        </div>

        <el-table :data="tableData" style="width: 100%" v-loading="loading" border>
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="role" label="角色">
            <template #default="scope">
              <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'info'">
                {{ scope.row.role === 'admin' ? '管理员' : '普通用户' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态">
            <template #default="scope">
              <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
                {{ scope.row.is_active ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" align="center">
            <template #default="scope">
              <el-button type="primary" size="small" @click="editUser(scope.row)">编辑</el-button>
              <el-popconfirm
                v-if="scope.row.username !== 'admin'"
                title="确定要删除该用户吗？"
                @confirm="deleteUser(scope.row.id)"
              >
                <template #reference>
                  <el-button type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="数据管理">
        <el-card class="box-card" shadow="never" style="border-color: #f56c6c;">
          <template #header>
            <div class="card-header">
              <span style="color: #f56c6c; font-weight: bold; display: flex; align-items: center;">
                <el-icon style="margin-right: 8px;"><Warning /></el-icon>
                危险操作区
              </span>
            </div>
          </template>
          <div style="margin-bottom: 20px; color: #606266;">
            清空系统数据将删除所有：物料、库位、入库单、出库单、库存以及价格批次等全部业务数据。此操作不可逆！
          </div>
          <el-button type="danger" @click="dataDialogVisible = true">清空系统数据</el-button>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="模板管理">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>出库申请单模板（Excel）</span>
            </div>
          </template>
          <div style="color:#606266;margin-bottom:10px;">
            上传后系统会优先使用你上传的模板文件进行填充下载；未上传则使用系统内置模板生成。
          </div>
          <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
            <el-upload
              action="/api/v1/system/templates/outbound-request"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleTemplateUploadSuccess"
              :on-error="handleTemplateUploadError"
              accept=".xlsx"
            >
              <el-button type="primary">上传模板</el-button>
            </el-upload>
            <el-button @click="downloadCurrentTemplate">下载当前模板</el-button>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- User Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新增用户'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" :disabled="isEdit && form.username === 'admin'" />
        </el-form-item>
        <el-form-item label="密码" :rules="[{ required: !isEdit, message: '密码不能为空' }]">
          <el-input v-model="form.password" type="password" show-password :placeholder="isEdit ? '不修改请留空' : '请输入密码'" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" :disabled="form.username === 'admin'">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="warehouse_manager" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" :disabled="form.username === 'admin'" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Clear Data Dialog -->
    <el-dialog v-model="dataDialogVisible" title="安全验证" width="400px">
      <div style="margin-bottom: 20px; color: #f56c6c;">请输入 admin 的密码以确认清空操作：</div>
      <el-input v-model="adminPassword" type="password" show-password placeholder="请输入管理员密码" />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dataDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="confirmClearData" :loading="clearing">确定清空</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'
import request from '../../utils/request'
import { downloadFile } from '../../utils/download'

// User Management
const tableData = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = ref({
  id: null,
  username: '',
  password: '',
  role: 'warehouse_manager',
  is_active: true
})

const fetchUsers = async () => {
  loading.value = true
  try {
    const res: any = await request.get('/system/users')
    tableData.value = res
  } finally {
    loading.value = false
  }
}

const openDialog = () => {
  isEdit.value = false
  form.value = { id: null, username: '', password: '', role: 'warehouse_manager', is_active: true }
  dialogVisible.value = true
}

const editUser = (row: any) => {
  isEdit.value = true
  form.value = { ...row, password: '' }
  dialogVisible.value = true
}

const submitForm = async () => {
  if (!isEdit.value && !form.value.password) {
    ElMessage.warning('密码不能为空')
    return
  }
  try {
    if (isEdit.value) {
      await request.put(`/system/users/${form.value.id}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await request.post('/system/users', form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchUsers()
  } catch (error) {
    // handled by interceptor
  }
}

const deleteUser = async (id: number) => {
  try {
    await request.delete(`/system/users/${id}`)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch (error) {}
}

// Data Management
const dataDialogVisible = ref(false)
const adminPassword = ref('')
const clearing = ref(false)

const confirmClearData = async () => {
  if (!adminPassword.value) {
    ElMessage.warning('请输入密码')
    return
  }
  
  try {
    clearing.value = true
    await request.post('/system/clear-data', { password: adminPassword.value })
    ElMessage.success('系统数据已全部清空')
    dataDialogVisible.value = false
    adminPassword.value = ''
  } catch (error) {
    // handled by interceptor
  } finally {
    clearing.value = false
  }
}

const uploadHeaders = computed(() => {
  return {
    Authorization: 'Bearer ' + localStorage.getItem('token')
  }
})

const handleTemplateUploadSuccess = (res: any) => {
  ElMessage.success(res.message || '上传成功')
}

const handleTemplateUploadError = () => {
  ElMessage.error('上传失败')
}

const downloadCurrentTemplate = () => {
  downloadFile('/api/v1/system/templates/outbound-request', 'outbound_request_template.xlsx')
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.system-container {
  padding: 20px;
}
</style>
