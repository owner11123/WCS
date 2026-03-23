<template>
  <div class="locations-container">
    <div class="header-actions">
      <el-button type="primary" @click="dialogVisible = true">新增库位</el-button>
      <el-button type="success" @click="generateDialogVisible = true">自动生成</el-button>
    </div>

    <el-table :data="tableData" style="width: 100%; margin-top: 20px;" v-loading="loading">
      <el-table-column prop="warehouse_code" label="仓库代码" width="120" />
      <el-table-column prop="area_code" label="库区" width="100" />
      <el-table-column prop="row_no" label="排" width="80" />
      <el-table-column prop="layer_no" label="层" width="80" />
      <el-table-column prop="col_no" label="列" width="80" />
      <el-table-column prop="code" label="库位编码" />
      <el-table-column label="状态">
        <template #default="scope">
          <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
            {{ scope.row.is_active ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" align="center">
        <template #default="scope">
          <el-popconfirm title="确定要删除该库位吗？" @confirm="deleteLocation(scope.row.id)">
            <template #reference>
              <el-button type="danger" size="small">删除</el-button>
            </template>
          </el-popconfirm>
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

    <el-dialog v-model="dialogVisible" title="新增库位" width="50%">
      <el-form :model="form" label-width="120px">
        <el-form-item label="仓库代码">
          <el-input v-model="form.warehouse_code" placeholder="例如：WCS" />
        </el-form-item>
        <el-form-item label="库区">
          <el-input v-model="form.area_code" placeholder="例如：A" />
        </el-form-item>
        <el-form-item label="排">
          <el-input-number v-model="form.row_no" :min="1" controls-position="right" />
        </el-form-item>
        <el-form-item label="层">
          <el-input-number v-model="form.layer_no" :min="1" controls-position="right" />
        </el-form-item>
        <el-form-item label="列">
          <el-input-number v-model="form.col_no" :min="1" controls-position="right" />
        </el-form-item>
        <el-form-item label="完整编码">
          <el-input :model-value="previewCode" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog v-model="generateDialogVisible" title="自动生成库位（排-层-列）" width="520px">
      <el-form :model="generateForm" label-width="120px">
        <el-form-item label="仓库代码">
          <el-input v-model="generateForm.warehouse_code" placeholder="例如：WCS" />
        </el-form-item>
        <el-form-item label="库区">
          <el-input v-model="generateForm.area_code" placeholder="例如：A" />
        </el-form-item>
        <el-form-item label="起止排">
          <div style="display:flex;gap:10px;width:100%;">
            <el-input-number v-model="generateForm.row_start" :min="1" controls-position="right" style="flex:1;" />
            <el-input-number v-model="generateForm.row_end" :min="1" controls-position="right" style="flex:1;" />
          </div>
        </el-form-item>
        <el-form-item label="起止层">
          <div style="display:flex;gap:10px;width:100%;">
            <el-input-number v-model="generateForm.layer_start" :min="1" controls-position="right" style="flex:1;" />
            <el-input-number v-model="generateForm.layer_end" :min="1" controls-position="right" style="flex:1;" />
          </div>
        </el-form-item>
        <el-form-item label="起止列">
          <div style="display:flex;gap:10px;width:100%;">
            <el-input-number v-model="generateForm.col_start" :min="1" controls-position="right" style="flex:1;" />
            <el-input-number v-model="generateForm.col_end" :min="1" controls-position="right" style="flex:1;" />
          </div>
        </el-form-item>
        <el-form-item label="预计生成">
          <div style="color:#606266;">
            {{ previewGenerate }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="generateDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitGenerate">开始生成</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../../utils/request'

const tableData = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const generateDialogVisible = ref(false)

const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchLocations()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchLocations()
}

const form = ref({
  warehouse_code: '',
  area_code: '',
  row_no: 1,
  layer_no: 1,
  col_no: 1,
  is_active: true
})

const previewCode = computed(() => {
  const wh = (form.value.warehouse_code || '').trim()
  const area = (form.value.area_code || '').trim()
  const r = form.value.row_no
  const l = form.value.layer_no
  const c = form.value.col_no
  if (!wh || !area || !r || !l || !c) return ''
  return `${wh}-${area}-${r}-${l}-${c}`
})

const generateForm = ref({
  warehouse_code: '',
  area_code: '',
  row_start: 1,
  row_end: 1,
  layer_start: 1,
  layer_end: 1,
  col_start: 1,
  col_end: 1
})

const previewGenerate = computed(() => {
  const wh = (generateForm.value.warehouse_code || '').trim()
  const area = (generateForm.value.area_code || '').trim()
  const rs = generateForm.value.row_start
  const re = generateForm.value.row_end
  const ls = generateForm.value.layer_start
  const le = generateForm.value.layer_end
  const cs = generateForm.value.col_start
  const ce = generateForm.value.col_end
  if (!wh || !area) return '请先填写仓库代码与库区'
  if (re < rs || le < ls || ce < cs) return '范围不合法'
  const total = (re - rs + 1) * (le - ls + 1) * (ce - cs + 1)
  return `共 ${total} 个，例如：${wh}-${area}-${rs}-${ls}-${cs}`
})

const fetchLocations = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const res: any = await request.get(`/locations/?skip=${skip}&limit=${pageSize.value}`)
    tableData.value = res.items || res
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

const deleteLocation = async (id: number) => {
  try {
    await request.delete(`/locations/${id}`)
    ElMessage.success('库位删除成功')
    fetchLocations()
  } catch (error) {
    // Error handled by interceptor
  }
}

const submitForm = async () => {
  if (!form.value.warehouse_code || !form.value.area_code) {
    ElMessage.warning('请填写仓库代码与库区')
    return
  }
  if (!form.value.row_no || !form.value.layer_no || !form.value.col_no) {
    ElMessage.warning('请填写排、层、列')
    return
  }
  try {
    await request.post('/locations/', form.value)
    ElMessage.success('库位添加成功')
    dialogVisible.value = false
    fetchLocations()
  } catch (error) {
    // Error handled by interceptor
  }
}

const submitGenerate = async () => {
  const payload = {
    warehouse_code: generateForm.value.warehouse_code,
    area_code: generateForm.value.area_code,
    row_start: generateForm.value.row_start,
    row_end: generateForm.value.row_end,
    layer_start: generateForm.value.layer_start,
    layer_end: generateForm.value.layer_end,
    col_start: generateForm.value.col_start,
    col_end: generateForm.value.col_end
  }
  try {
    const res: any = await request.post('/locations/generate', payload)
    ElMessage.success(`生成完成：新增 ${res.created}，已存在 ${res.existing}，总计 ${res.total}`)
    generateDialogVisible.value = false
    fetchLocations()
  } catch (e) {}
}

onMounted(() => {
  fetchLocations()
})
</script>

<style scoped>
.locations-container {
  padding: 20px;
}
.header-actions {
  display: flex;
  gap: 10px;
}
</style>
