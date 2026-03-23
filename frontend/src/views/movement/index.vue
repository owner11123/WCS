<template>
  <div class="movement-container">
    <div v-if="isMobile" class="mobile-only">
      <el-card shadow="hover" class="mobile-card">
        <div class="mobile-title">移库管理</div>
        <el-button type="primary" style="width: 100%" @click="openDialog">新建移库单</el-button>
      </el-card>
    </div>

    <div v-else class="header-actions">
      <el-button type="primary" @click="openDialog">新建移库单</el-button>
    </div>

    <el-table v-if="!isMobile" :data="tableData" style="width: 100%; margin-top: 20px;" v-loading="loading" border>
      <el-table-column prop="movement_no" label="移库单号" width="160" />
      <el-table-column prop="material_code" label="物料编码" width="120" />
      <el-table-column prop="material_description" label="物料描述" min-width="180" show-overflow-tooltip />
      <el-table-column prop="batch_no" label="批次/合同号" width="140" />
      <el-table-column prop="source_location_code" label="原库位" width="120">
        <template #default="scope">
          <el-tag type="warning">{{ scope.row.source_location_code }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="target_location_code" label="目标库位" width="120">
        <template #default="scope">
          <el-tag type="success">{{ scope.row.target_location_code }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="quantity" label="移动数量" width="100" />
      <el-table-column prop="movement_time" label="移库时间" width="180">
        <template #default="scope">
          {{ new Date(scope.row.movement_time).toLocaleString() }}
        </template>
      </el-table-column>
    </el-table>

    <div v-if="!isMobile" style="margin-top: 20px; display: flex; justify-content: flex-end;">
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

    <!-- Create Movement Dialog -->
    <el-dialog v-model="dialogVisible" title="新建移库" :fullscreen="isMobile" :width="isMobile ? '100%' : '600px'">
      <el-form :model="form" :label-width="isMobile ? 'auto' : '100px'" :label-position="isMobile ? 'top' : 'right'">
        <el-form-item label="选择物料" required>
          <el-select v-model="form.material_id" placeholder="请选择物料" filterable style="width: 100%" @change="handleMaterialChange">
            <el-option
              v-for="item in materials"
              :key="item.id"
              :label="item.code + (item.description ? ' - ' + item.description : '')"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="原库位(批次)" required>
          <el-select v-model="form.source_key" placeholder="请选择要移出的库位和批次" style="width: 100%" :loading="inventoryLoading" @change="handleSourceChange">
            <el-option
              v-for="item in availableSources"
              :key="item.key"
              :label="item.location_code + ' | 批次:' + item.batch_no + ' (库存:' + item.quantity + ')'"
              :value="item.key"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标库位" required>
          <el-select v-model="form.target_location_id" placeholder="请选择移入的目标库位" filterable style="width: 100%">
            <el-option
              v-for="item in locations"
              :key="item.id"
              :label="item.code"
              :value="item.id"
              :disabled="item.id === form.source_location_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="移动数量" required>
          <el-input-number v-model="form.quantity" :min="1" :max="form.max_quantity" style="width: 100%" />
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
import { ref, onMounted, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../../utils/request'

const isMobile = computed(() => window.innerWidth <= 768)

const tableData = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)

const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const materials = ref<any[]>([])
const locations = ref<any[]>([])
const inventoryByMaterialId = reactive<Record<string, any[]>>({})
const inventoryLoading = ref(false)
const inventoryInFlight = new Set<string>()
const availableSources = ref<any[]>([])

const form = ref({
  material_id: null,
  source_key: null,
  source_location_id: null,
  price_version_id: null,
  target_location_id: null,
  quantity: 1,
  max_quantity: 999999
})

const fetchMovements = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const res: any = await request.get(`/inventory-management/movements?skip=${skip}&limit=${pageSize.value}`)
    tableData.value = res.items || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

const fetchOptions = async () => {
  try {
    const resMaterials: any = await request.get('/materials/?limit=10000')
    materials.value = resMaterials.items || resMaterials
    
    const resLocations: any = await request.get('/locations/?limit=10000')
    locations.value = resLocations.items || resLocations
  } catch (error) {}
}

const ensureInventoryLoaded = async (materialId: any) => {
  const mid = Number(materialId)
  if (!mid) return
  const key = String(mid)
  if (inventoryByMaterialId[key]) return
  if (inventoryInFlight.has(key)) return

  const mat = materials.value.find(m => Number(m.id) === mid)
  const code = mat?.code
  if (!code) return

  inventoryInFlight.add(key)
  inventoryLoading.value = true
  try {
    const res: any = await request.get(`/inventory/?skip=0&limit=2000&material_code=${encodeURIComponent(code)}`)
    inventoryByMaterialId[key] = res.items || res
  } finally {
    inventoryInFlight.delete(key)
    inventoryLoading.value = inventoryInFlight.size > 0
  }
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchMovements()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchMovements()
}

const openDialog = async () => {
  form.value = {
    material_id: null,
    source_key: null,
    source_location_id: null,
    price_version_id: null,
    target_location_id: null,
    quantity: 1,
    max_quantity: 999999
  }
  availableSources.value = []
  await fetchOptions()
  dialogVisible.value = true
}

const handleMaterialChange = async () => {
  form.value.source_key = null
  form.value.source_location_id = null
  form.value.price_version_id = null
  form.value.quantity = 1
  form.value.max_quantity = 999999
  
  if (!form.value.material_id) {
    availableSources.value = []
    return
  }

  const mid = Number(form.value.material_id)
  await ensureInventoryLoaded(mid)
  if (Number(form.value.material_id) !== mid) return

  const key = String(mid)
  const stocks = (inventoryByMaterialId[key] || []).filter((inv: any) => Number(inv.material_id) === mid && inv.quantity > 0)
  availableSources.value = stocks.map((s: any) => ({
    ...s,
    key: `${s.location_id}_${s.price_version_id}`
  }))
}

const handleSourceChange = () => {
  const source = availableSources.value.find(s => s.key === form.value.source_key)
  if (source) {
    form.value.source_location_id = source.location_id
    form.value.price_version_id = source.price_version_id
    form.value.max_quantity = source.quantity
    form.value.quantity = 1
    
    if (form.value.target_location_id === source.location_id) {
      form.value.target_location_id = null
    }
  }
}

const submitForm = async () => {
  if (!form.value.material_id || !form.value.source_location_id || !form.value.target_location_id || !form.value.quantity) {
    ElMessage.warning('请完整填写移库信息')
    return
  }
  
  try {
    const payload = {
      material_id: form.value.material_id,
      price_version_id: form.value.price_version_id,
      source_location_id: form.value.source_location_id,
      target_location_id: form.value.target_location_id,
      quantity: form.value.quantity,
      operator_id: 1 // mock
    }
    await request.post('/inventory-management/movements', payload)
    ElMessage.success('移库成功')
    dialogVisible.value = false
    fetchMovements()
  } catch (error) {
    // handled by interceptor
  }
}

onMounted(() => {
  if (!isMobile.value) {
    fetchMovements()
  }
})
</script>

<style scoped>
.movement-container {
  padding: 20px;
}
.header-actions {
  margin-bottom: 20px;
}
.mobile-only {
  margin-bottom: 12px;
}
.mobile-card {
  border-radius: 12px;
}
.mobile-title {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 10px;
}
</style>
