<template>
  <div class="materials-container">
    <div class="header-actions">
      <el-button type="primary" @click="openDialog">新增物料</el-button>
      <el-button type="success" @click="handleExport">导出 Excel</el-button>
      <el-upload
        class="upload-demo"
        action="/api/v1/excel/import/materials"
        :headers="headers"
        :on-success="handleImportSuccess"
        :show-file-list="false"
        style="display: inline-block; margin-left: 10px;"
      >
        <el-button type="warning">导入 Excel</el-button>
      </el-upload>
    </div>

    <el-table :data="tableData" style="width: 100%; margin-top: 20px;" v-loading="loading">
      <el-table-column prop="code" label="物料编码" width="150" />
      <el-table-column prop="model" label="型号" width="150" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="category_major" label="物料大类" width="140" />
      <el-table-column prop="category_minor" label="物料二类" width="140" />
      <el-table-column prop="substitute_code" label="替代物料号" width="150" />
      <el-table-column prop="vehicle_model" label="适用车型" width="150" />
      <el-table-column label="操作" width="100" align="center">
        <template #default="scope">
          <el-button type="primary" size="small" @click="editMaterial(scope.row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑物料' : '新增物料'" width="50%">
      <el-form :model="form" label-width="120px">
        <el-form-item label="物料编码">
          <el-input v-model="form.code" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="物料型号">
          <el-input v-model="form.model" />
        </el-form-item>
        <el-form-item label="物料描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="物料大类">
          <el-input v-model="form.category_major" />
        </el-form-item>
        <el-form-item label="物料二类">
          <el-input v-model="form.category_minor" />
        </el-form-item>
        <el-form-item label="替代物料号">
          <el-input v-model="form.substitute_code" placeholder="输入替代物料号" />
        </el-form-item>
        <el-form-item label="适用车型">
          <el-input v-model="form.vehicle_model" placeholder="多个车型用逗号隔开" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../../utils/request'
import { downloadFile } from '../../utils/download'

const tableData = ref([])
const loading = ref(false)
const dialogVisible = ref(false)

const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchMaterials()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchMaterials()
}

const form = ref({
  id: null,
  code: '',
  model: '',
  description: '',
  category_major: '',
  category_minor: '',
  substitute_code: '',
  vehicle_model: ''
})

const isEdit = ref(false)

const openDialog = () => {
  isEdit.value = false
  form.value = {
    id: null,
    code: '',
    model: '',
    description: '',
    category_major: '',
    category_minor: '',
    substitute_code: '',
    vehicle_model: ''
  }
  dialogVisible.value = true
}

const editMaterial = (row: any) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

const headers = {
  Authorization: `Bearer ${localStorage.getItem('token')}`
}

const fetchMaterials = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const res: any = await request.get(`/materials/?skip=${skip}&limit=${pageSize.value}`)
    tableData.value = res.items || res
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

const submitForm = async () => {
  try {
    if (isEdit.value) {
      await request.put(`/materials/${form.value.id}`, form.value)
      ElMessage.success('物料更新成功')
    } else {
      await request.post('/materials/', form.value)
      ElMessage.success('物料添加成功')
    }
    dialogVisible.value = false
    fetchMaterials()
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleExport = () => {
  downloadFile('/api/v1/excel/export/materials', 'materials.xlsx')
}

const handleImportSuccess = () => {
  ElMessage.success('导入成功')
  fetchMaterials()
}

onMounted(() => {
  fetchMaterials()
})
</script>

<style scoped>
.materials-container {
  padding: 20px;
}
.header-actions {
  display: flex;
  gap: 10px;
}
</style>
