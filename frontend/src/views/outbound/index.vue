<template>
  <div class="outbound-container">
    <div v-if="isMobile" class="mobile-only">
      <el-card shadow="hover" class="mobile-card">
        <div class="mobile-title">出库管理</div>
        <el-button type="primary" style="width: 100%" @click="openDialog">创建出库单</el-button>
      </el-card>
    </div>

    <div v-if="!isMobile" class="header-actions">
      <div class="left-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索物料编码"
          clearable
          style="width: 200px; margin-right: 10px;"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button :icon="Search" @click="handleSearch" />
          </template>
        </el-input>
        <el-input
          v-model="batchPrint.customer"
          placeholder="客户（用于批量下载申请单）"
          clearable
          style="width: 220px; margin-right: 10px;"
        />
        <el-date-picker
          v-model="batchPrint.date_range"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width: 280px; margin-right: 10px;"
        />
        <el-button type="primary" @click="downloadBatchRequestExcel">按日期+客户下载申请单</el-button>
        <el-button type="primary" @click="openDialog">创建出库单</el-button>
        <el-button type="info" @click="downloadTemplate">下载导入模板</el-button>
        <el-upload
          class="upload-demo"
          action="/api/v1/excel/import/outbound"
          :headers="uploadHeaders"
          :show-file-list="false"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          accept=".xlsx,.xls"
          style="display: inline-block; margin-left: 10px; margin-right: 10px;"
        >
          <el-button type="warning">Excel 导入出库</el-button>
        </el-upload>
        <el-button type="success" @click="exportData">导出出库记录</el-button>
      </div>
    </div>

    <el-table v-if="!isMobile" :data="tableData" style="width: 100%; margin-top: 20px;" v-loading="loading">
      <el-table-column prop="order_no" label="出库单号" width="160" />
      <el-table-column prop="customer" label="客户" width="120" />
      <el-table-column prop="contract_no" label="合同号(批次)" width="140" />
      <el-table-column prop="material_code" label="物料编码" width="120" />
      <el-table-column prop="material_description" label="物料描述" min-width="180" show-overflow-tooltip />
      <el-table-column prop="location_code" label="库位" width="100" />
      <el-table-column prop="quantity" label="出库数量" width="100" />
      <el-table-column prop="sale_price" label="销售单价" width="100" />
      <el-table-column prop="currency" label="货币" width="80" />
      <el-table-column prop="receiver" label="领用人" width="100" />
      <el-table-column label="申请单" width="110" align="center">
        <template #default="scope">
          <el-button v-if="isFirstOfOrder(scope.$index)" type="primary" size="small" @click="downloadRequestExcel(scope.row)">下载Excel</el-button>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'completed' ? 'success' : 'info'">
            {{ scope.row.status === 'completed' ? '已完成' : '待处理' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="outbound_time" label="出库时间" width="180">
        <template #default="scope">
          {{ new Date(scope.row.outbound_time).toLocaleString() }}
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

    <el-dialog v-model="dialogVisible" title="创建出库单" :fullscreen="isMobile" :width="isMobile ? '100%' : '80%'" top="5vh">
      <div style="margin-bottom: 15px;">
        <el-form :inline="!isMobile" :model="form" :label-position="isMobile ? 'top' : 'right'">
          <el-form-item label="出库单号">
            <el-input v-model="form.order_no" placeholder="不填则自动生成" />
          </el-form-item>
        <el-form-item label="客户名称" required>
          <el-autocomplete
            v-model="form.customer"
            :fetch-suggestions="querySearchCustomer"
            placeholder="请输入客户名称"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="领用人" required>
          <el-autocomplete
            v-model="form.receiver"
            :fetch-suggestions="querySearchReceiver"
            placeholder="请输入领用人"
            style="width: 100%"
          />
        </el-form-item>
        </el-form>
      </div>

      <div style="margin-bottom: 10px;">
        <el-button type="primary" plain @click="addRow">添加明细行</el-button>
      </div>

      <div v-if="isMobile" class="mobile-items">
        <el-card v-for="(row, idx) in form.items" :key="idx" shadow="never" class="mobile-item-card">
          <div class="mobile-item-header">
            <div class="mobile-item-title">明细 {{ idx + 1 }}</div>
            <el-button type="danger" size="small" :icon="Delete" circle @click="removeRow(idx)" />
          </div>

          <el-form :model="row" label-position="top">
            <el-form-item label="物料" required>
              <el-select v-model="row.material_id" placeholder="请选择物料" filterable style="width: 100%" @change="() => handleMaterialChange(row)">
                <el-option
                  v-for="item in materials"
                  :key="item.id"
                  :label="item.code + (item.description ? ' - ' + item.description : '')"
                  :value="item.id"
                />
              </el-select>
              <div v-if="(row as any).actual_material_code" class="mobile-substitute">
                替代料: {{ (row as any).actual_material_code }}
              </div>
            </el-form-item>

            <el-form-item label="库位(含批次)" required>
              <el-select v-model="row.location_key" placeholder="请选择库位" filterable style="width: 100%" :loading="inventoryLoading" @change="() => handleLocationChange(row)">
                <el-option
                  v-for="item in getAvailableLocations((row as any).material_id)"
                  :key="item.key"
                  :label="item.code + ' | ' + item.batch_no + ' | 库存:' + item.stock_qty"
                  :value="item.key"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="出库数量" required>
              <el-input-number v-model="row.quantity" :min="1" :max="getMaxStock(row)" style="width: 100%" controls-position="right" @change="() => calculateAmount(row)" />
            </el-form-item>

            <el-form-item label="销售单价 / 货币">
              <div class="mobile-inline">
                <el-input-number v-model="row.sale_price" :min="0" :precision="2" :step="0.1" style="width: 65%" controls-position="right" disabled />
                <el-input v-model="row.currency" style="width: 35%" disabled />
              </div>
            </el-form-item>

            <el-form-item label="出库金额">
              <el-input-number v-model="row.total_amount" :precision="2" style="width: 100%" controls-position="right" disabled />
            </el-form-item>
          </el-form>
        </el-card>
      </div>

      <el-table v-else :data="form.items" border style="width: 100%">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column label="物料" min-width="150">
          <template #default="scope">
            <el-select v-model="scope.row.material_id" placeholder="请选择物料" filterable style="width: 100%" @change="() => handleMaterialChange(scope.row)">
              <el-option
                v-for="item in materials"
                :key="item.id"
                :label="item.code + (item.description ? ' - ' + item.description : '')"
                :value="item.id"
              />
            </el-select>
            <div v-if="scope.row.actual_material_code" style="font-size: 12px; color: #E6A23C; margin-top: 4px;">
              替代料: {{ scope.row.actual_material_code }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="库位(含批次)" min-width="250">
          <template #default="scope">
            <el-select v-model="scope.row.location_key" placeholder="请选择库位" filterable style="width: 100%" :loading="inventoryLoading" @change="() => handleLocationChange(scope.row)">
              <el-option
                v-for="item in getAvailableLocations(scope.row.material_id)"
                :key="item.key"
                :label="item.code + ' - 批次:' + item.batch_no + ' (库存:' + item.stock_qty + ')'"
                :value="item.key"
              >
                <span style="float: left">{{ item.code }} | {{ item.batch_no }}</span>
                <span v-if="item.is_substitute" style="float: right; color: #E6A23C; font-size: 12px; margin-left: 10px;">替代料库存</span>
                <span style="float: right; color: #8492a6; font-size: 13px; margin-left: 10px;">库存: {{ item.stock_qty }}</span>
              </el-option>
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="出库数量" width="120">
          <template #default="scope">
            <el-input-number v-model="scope.row.quantity" :min="1" :max="getMaxStock(scope.row)" style="width: 100%" controls-position="right" @change="() => calculateAmount(scope.row)" />
          </template>
        </el-table-column>
        <el-table-column label="销售单价" width="120">
          <template #default="scope">
            <el-input-number v-model="scope.row.sale_price" :min="0" :precision="2" :step="0.1" style="width: 100%" controls-position="right" disabled />
          </template>
        </el-table-column>
        <el-table-column label="货币" width="100">
          <template #default="scope">
            <el-input v-model="scope.row.currency" disabled />
          </template>
        </el-table-column>
        <el-table-column label="出库金额" width="120">
          <template #default="scope">
            <el-input-number v-model="scope.row.total_amount" :precision="2" style="width: 100%" controls-position="right" disabled />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center">
          <template #default="scope">
            <el-button type="danger" size="small" @click="removeRow(scope.$index)" :icon="Delete" circle />
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定出库</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Delete, Search } from '@element-plus/icons-vue'
import request from '../../utils/request'
import { downloadFile } from '../../utils/download'

const route = useRoute()
const router = useRouter()

const isMobile = computed(() => window.innerWidth <= 768)

const tableData = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const searchQuery = ref('')

const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const handleSearch = () => {
  currentPage.value = 1
  fetchOrders()
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchOrders()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchOrders()
}

const downloadRequestExcel = (row: any) => {
  const orderNo = row?.order_no
  if (!orderNo) return
  const url = `/api/v1/excel/print/outbound/${encodeURIComponent(orderNo)}?rows=10`
  downloadFile(url, `${orderNo}_领用申请单.xlsx`)
}

const isFirstOfOrder = (index: number) => {
  if (index === 0) return true
  const prev = (tableData.value as any[])[index - 1]
  const curr = (tableData.value as any[])[index]
  return !prev || !curr || prev.order_no !== curr.order_no
}

const batchPrint = reactive({
  customer: '',
  date_range: [] as string[]
})

const downloadBatchRequestExcel = () => {
  if (!batchPrint.customer) {
    ElMessage.warning('请输入客户名称')
    return
  }
  if (!batchPrint.date_range || batchPrint.date_range.length !== 2) {
    ElMessage.warning('请选择日期段')
    return
  }
  const url = `/api/v1/excel/print/outbound-batch?customer=${encodeURIComponent(batchPrint.customer)}&start_date=${encodeURIComponent(batchPrint.date_range[0])}&end_date=${encodeURIComponent(batchPrint.date_range[1])}&rows=10`
  downloadFile(url, `outbound_request_${batchPrint.customer}.xlsx`)
}

const uploadHeaders = computed(() => {
  return {
    Authorization: 'Bearer ' + localStorage.getItem('token')
  }
})

const handleUploadSuccess = (res: any) => {
  ElMessage.success(res.message || '导入成功')
  fetchOrders()
}

const handleUploadError = (err: any) => {
  const msg =
    err?.response?.data?.detail ||
    err?.response?.data?.message ||
    err?.message ||
    '导入失败'
  ElMessage.error(String(msg))
}

const downloadTemplate = () => {
  downloadFile('/api/v1/excel/template/outbound', 'outbound_template.xlsx')
}

const materials = ref<any[]>([])
const locations = ref<any[]>([])
const inventoryByMaterialId = reactive<Record<string, any[]>>({})
const inventoryLoading = ref(false)
const inventoryInFlight = new Set<string>()

const form = reactive({
  order_no: '',
  customer: '',
  receiver: '',
  operator_id: 1,
  items: [
    { material_id: null, price_version_id: null, location_id: null, location_key: null, quantity: 1, sale_price: undefined, currency: '', total_amount: 0 }
  ]
})

const fetchOptions = async () => {
  try {
    const resMaterials: any = await request.get('/materials/?limit=10000')
    materials.value = resMaterials.items || resMaterials
    
    const resLocations: any = await request.get('/locations/?limit=10000')
    locations.value = resLocations.items || resLocations
  } catch (error) {
    console.error('Failed to fetch options', error)
  }
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
    const res: any = await request.get(`/inventory/?limit=2000&material_code=${encodeURIComponent(code)}`)
    inventoryByMaterialId[key] = res.items || res
  } finally {
    inventoryInFlight.delete(key)
    inventoryLoading.value = inventoryInFlight.size > 0
  }
}

const getAvailableLocations = (materialId: any) => {
  const mid = Number(materialId)
  if (!mid) return []
  
  // Find current material and its substitute
  const material = materials.value.find(m => Number(m.id) === mid)
  const substituteCode = material?.substitute_code
  let substituteId = null
  if (substituteCode) {
    const subMaterial = materials.value.find(m => m.code === substituteCode)
    if (subMaterial) substituteId = Number(subMaterial.id)
  }

  ensureInventoryLoaded(mid)
  if (substituteId) ensureInventoryLoaded(substituteId)

  const stocks: any[] = []
  const mainKey = String(mid)
  if (inventoryByMaterialId[mainKey]) stocks.push(...inventoryByMaterialId[mainKey])
  if (substituteId) {
    const subKey = String(substituteId)
    if (inventoryByMaterialId[subKey]) stocks.push(...inventoryByMaterialId[subKey])
  }

  // Filter stock for main material OR substitute material
  const availableStock = stocks.filter(inv => 
    (Number(inv.material_id) === mid || (substituteId && Number(inv.material_id) === substituteId)) && 
    inv.quantity > 0
  )
  
  // Create a map to aggregate stock by location AND batch_no
  const locMap = new Map()
  availableStock.forEach(stock => {
    // Use a composite key of location_id + batch_no to separate different batches in the same location
    const key = `${stock.location_id}_${stock.batch_no || 'DEFAULT'}`
    if (!locMap.has(key)) {
      locMap.set(key, {
        key: key,
        id: stock.location_id,
        code: stock.location_code,
        name: stock.location_name,
        batch_no: stock.batch_no || 'DEFAULT',
        stock_qty: 0,
        is_substitute: Number(stock.material_id) !== mid,
        actual_material_id: stock.material_id,
        actual_material_code: stock.material_code,
        price_version_id: stock.price_version_id,
        sale_price: stock.sale_price,
        currency: stock.currency
      })
    }
    locMap.get(key).stock_qty += stock.quantity
  })
  
  return Array.from(locMap.values())
}

const handleMaterialChange = (row: any) => {
  row.location_key = null
  row.location_id = null
  row.sale_price = undefined
  row.currency = ''
  row.total_amount = 0
  row.quantity = 1
  row.actual_material_id = null
  row.actual_material_code = ''
  ensureInventoryLoaded(row.material_id)
}

const handleLocationChange = (row: any) => {
  if (row.material_id && row.location_key) {
    const locations = getAvailableLocations(row.material_id)
    const loc = locations.find(l => l.key === row.location_key)
    
    if (loc) {
      row.location_id = loc.id
      row.sale_price = loc.sale_price || 0
      row.currency = loc.currency || 'CNY'
      row.actual_material_id = loc.actual_material_id
      row.actual_material_code = loc.is_substitute ? loc.actual_material_code : ''
      row.batch_no = loc.batch_no
      calculateAmount(row)
    }
  }
}

const getMaxStock = (row: any) => {
  if (!row.material_id || !row.location_key) return 999999
  const locations = getAvailableLocations(row.material_id)
  const loc = locations.find(l => l.key === row.location_key)
  return loc ? loc.stock_qty : 1
}

const calculateAmount = (row: any) => {
  if (row.sale_price !== undefined && row.quantity) {
    row.total_amount = row.sale_price * row.quantity
  } else {
    row.total_amount = 0
  }
}

const openDialog = () => {
  form.order_no = ''
  form.customer = ''
  form.receiver = ''
  form.items = [{ material_id: null, price_version_id: null, location_id: null, location_key: null, quantity: 1, sale_price: undefined, currency: '', total_amount: 0 }]
  dialogVisible.value = true
  fetchOptions()
}

const addRow = () => {
  form.items.push({ material_id: null, price_version_id: null, location_id: null, location_key: null, quantity: 1, sale_price: undefined, currency: '', total_amount: 0 })
}

const removeRow = (index: number) => {
  if (form.items.length <= 1) {
    ElMessage.warning('至少需要保留一条明细')
    return
  }
  form.items.splice(index, 1)
}

const customers = ref<any[]>([])
const receivers = ref<any[]>([])

const fetchOrders = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    let url = `/orders/outbound?skip=${skip}&limit=${pageSize.value}`
    if (searchQuery.value) {
      url += `&material_code=${searchQuery.value}`
    }
    const res: any = await request.get(url)
    tableData.value = res.items || res
    total.value = res.total || 0
    
    // Extract unique customers and receivers for autocomplete
    if (res.items) {
      const uniqueCustomers = new Set(res.items.map((item: any) => item.customer).filter(Boolean))
      const uniqueReceivers = new Set(res.items.map((item: any) => item.receiver).filter(Boolean))
      customers.value = Array.from(uniqueCustomers).map(c => ({ value: c }))
      receivers.value = Array.from(uniqueReceivers).map(r => ({ value: r }))
    }
  } finally {
    loading.value = false
  }
}

const querySearchCustomer = (queryString: string, cb: any) => {
  const results = queryString
    ? customers.value.filter(createFilter(queryString))
    : customers.value
  cb(results)
}

const querySearchReceiver = (queryString: string, cb: any) => {
  const results = queryString
    ? receivers.value.filter(createFilter(queryString))
    : receivers.value
  cb(results)
}

const createFilter = (queryString: string) => {
  return (item: any) => {
    return (item.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0)
  }
}

const exportData = () => {
  downloadFile('/api/v1/excel/export/outbound', 'outbound_records.xlsx')
}

const submitForm = async () => {
  if (!form.customer) {
    ElMessage.warning('客户名称不能为空')
    return
  }
  if (!form.receiver) {
    ElMessage.warning('领用人不能为空')
    return
  }
  if (form.items.length === 0) {
    ElMessage.warning('请添加出库明细')
    return
  }
  
  for (const item of form.items) {
    if (!item.material_id || !item.location_key || !item.quantity) {
      ElMessage.warning('请完善出库明细（物料、库位、数量必填）')
      return
    }
  }
  
  try {
    const payload = {
      ...form,
      order_no: form.order_no || undefined,
      operator_id: 1, // Mock user ID
      items: form.items.map((item: any) => {
        // Find the matching price version id from inventory based on location_key
        const locations = getAvailableLocations(item.material_id)
        const loc = locations.find(l => l.key === item.location_key)
        
        return {
          ...item,
          price_version_id: loc ? loc.price_version_id : null
        }
      })
    }
    
    const res: any = await request.post('/orders/outbound/bulk', payload)
    ElMessage.success(`出库单创建成功：${res.order_no || ''}`)
    dialogVisible.value = false
    fetchOrders()
  } catch (error) {
    // Error handled by interceptor
  }
}

onMounted(() => {
  fetchOrders()
  fetchOptions()
  if (route.query.create === '1') {
    openDialog()
    router.replace({ query: {} })
  }
})
</script>

<style scoped>
.outbound-container {
  padding: 20px;
}
.header-actions {
  display: flex;
  gap: 10px;
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
.mobile-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.mobile-item-card {
  border-radius: 12px;
}
.mobile-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.mobile-item-title {
  font-weight: 700;
  color: #303133;
}
.mobile-substitute {
  font-size: 12px;
  color: #e6a23c;
  margin-top: 6px;
}
.mobile-inline {
  display: flex;
  gap: 8px;
}
</style>
