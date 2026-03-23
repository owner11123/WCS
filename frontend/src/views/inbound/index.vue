<template>
  <div class="inbound-container">
    <div class="header-actions" v-if="!isMobile">
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
        <el-button type="primary" @click="openDialog">创建入库单</el-button>
        <el-button type="info" @click="downloadTemplate">下载导入模板</el-button>
        <el-upload
          class="upload-demo"
          action="/api/v1/excel/import/inbound"
          :headers="uploadHeaders"
          :show-file-list="false"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          accept=".xlsx,.xls"
          style="display: inline-block; margin-left: 10px; margin-right: 10px;"
        >
          <el-button type="warning">Excel 导入入库</el-button>
        </el-upload>
        <el-button type="success" @click="exportData">导出入库记录</el-button>
        <el-button type="warning" :icon="Box" @click="openTransitDialog" style="margin-left: 10px;">在途入库</el-button>
      </div>
    </div>

    <el-table v-if="!isMobile" :data="tableData" style="width: 100%; margin-top: 20px;" v-loading="loading">
      <el-table-column prop="order_no" label="入库单号" width="160" />
      <el-table-column prop="contract_no" label="采购合同号(批次)" width="140" />
      <el-table-column prop="material_code" label="物料编码" width="120" />
      <el-table-column prop="material_description" label="物料描述" min-width="180" show-overflow-tooltip />
      <el-table-column prop="location_code" label="库位" width="100" />
      <el-table-column prop="quantity" label="入库数量" width="100" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'completed' ? 'success' : 'info'">
            {{ scope.row.status === 'completed' ? '已完成' : '待处理' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="inbound_time" label="入库时间" width="180">
        <template #default="scope">
          {{ new Date(scope.row.inbound_time).toLocaleString() }}
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

    <el-dialog v-model="dialogVisible" title="创建入库单" width="80%" top="5vh">
      <div style="margin-bottom: 15px;">
        <el-form :inline="true" :model="form">
          <el-form-item label="入库单号">
            <el-input v-model="form.order_no" placeholder="不填则自动生成" />
          </el-form-item>
        </el-form>
      </div>
      
      <div style="margin-bottom: 10px;">
        <el-button type="primary" plain @click="addRow">添加明细行</el-button>
      </div>

      <el-table :data="form.items" border style="width: 100%">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column label="采购合同号" width="150">
          <template #default="scope">
            <el-input v-model="scope.row.contract_no" placeholder="输入合同号" />
          </template>
        </el-table-column>
        <el-table-column label="物料" min-width="150">
          <template #default="scope">
            <el-select v-model="scope.row.material_id" placeholder="请选择物料" filterable style="width: 100%">
              <el-option
                v-for="item in materials"
                :key="item.id"
                :label="item.code + (item.description ? ' - ' + item.description : '')"
                :value="item.id"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="库位" min-width="150">
          <template #default="scope">
            <el-select v-model="scope.row.location_id" placeholder="请选择库位" filterable style="width: 100%">
              <el-option
                v-for="item in locations"
                :key="item.id"
                :label="item.code + ' - ' + item.name"
                :value="item.id"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="入库数量" width="120">
          <template #default="scope">
            <el-input-number v-model="scope.row.quantity" :min="1" style="width: 100%" controls-position="right" />
          </template>
        </el-table-column>
        <el-table-column label="采购单价" width="120">
          <template #default="scope">
            <el-input-number v-model="scope.row.purchase_price" :min="0" :precision="2" :step="0.1" style="width: 100%" controls-position="right" placeholder="0.00" />
          </template>
        </el-table-column>
        <el-table-column label="销售单价" width="120">
          <template #default="scope">
            <el-input-number v-model="scope.row.sale_price" :min="0" :precision="2" :step="0.1" style="width: 100%" controls-position="right" placeholder="0.00" />
          </template>
        </el-table-column>
        <el-table-column label="货币" width="100">
          <template #default="scope">
            <el-select v-model="scope.row.currency" placeholder="货币">
              <el-option label="CNY" value="CNY" />
              <el-option label="USD" value="USD" />
              <el-option label="EUR" value="EUR" />
            </el-select>
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
          <el-button type="primary" @click="submitForm">确定入库</el-button>
        </span>
      </template>
    </el-dialog>
    <!-- Transit Inbound Dialog -->
    <el-dialog v-model="transitDialogVisible" title="在途入库" :fullscreen="isMobile" :width="isMobile ? '100%' : '700px'">
      <el-form :model="transitForm" label-width="80px">
        <el-form-item label="选择箱号" required>
          <el-select v-model="transitForm.box_no" placeholder="请选择在途箱号" filterable style="width: 100%" @change="handleBoxChange">
            <el-option
              v-for="item in availableBoxes"
              :key="item.box_no"
              :label="item.box_no + ' (' + item.items.length + ' 种物料)'"
              :value="item.box_no"
            />
          </el-select>
        </el-form-item>
        
        <div v-if="selectedBoxInfo" style="margin-top: 15px;">
          <h4 style="margin-bottom: 10px;">箱内物料明细（填写库位和入库数量即可部分入库）：</h4>
          <el-table :data="selectedBoxInfo.items" border style="width: 100%;" size="small">
            <el-table-column prop="material_code" label="物料" min-width="100">
              <template #default="scope">
                <div style="font-weight: bold">{{ scope.row.material_code }}</div>
                <div style="font-size: 12px; color: #666; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" :title="scope.row.material_description">
                  {{ scope.row.material_description }}
                </div>
              </template>
            </el-table-column>
            <el-table-column label="本次入库" width="100">
              <template #default="scope">
                <el-input-number 
                  v-model="scope.row.inbound_quantity" 
                  :min="0" 
                  :max="scope.row.quantity" 
                  size="small" 
                  style="width: 100%" 
                  controls-position="right"
                />
              </template>
            </el-table-column>
            <el-table-column label="入库库位" width="110">
              <template #default="scope">
                <el-select v-model="scope.row.location_id" placeholder="选择库位" filterable size="small" style="width: 100%">
                  <el-option
                    v-for="loc in locations"
                    :key="loc.id"
                    :label="loc.code"
                    :value="loc.id"
                  />
                </el-select>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="transitDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitTransitInbound">确认入库</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Delete, Search, Box } from '@element-plus/icons-vue'
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
  ElMessage.error('导入失败')
  console.error(err)
}

const downloadTemplate = () => {
  downloadFile('/api/v1/excel/template/inbound', 'inbound_template.xlsx')
}

const materials = ref<any[]>([])
const locations = ref<any[]>([])

// Transit Inbound State
const transitDialogVisible = ref(false)
const availableBoxes = ref<any[]>([])
const selectedBoxInfo = ref<any>(null)
const transitForm = ref({
  box_no: '',
  location_id: null
})

const openTransitDialog = async () => {
  transitForm.value = { box_no: '', location_id: null }
  selectedBoxInfo.value = null
  try {
    const res: any = await request.get('/transit/available-boxes')
    availableBoxes.value = res
    
    if (locations.value.length === 0) {
      const resLoc: any = await request.get('/locations/?limit=10000')
      locations.value = resLoc.items || resLoc
    }
  } catch (e) {}
  transitDialogVisible.value = true
}

const handleBoxChange = () => {
  const box = availableBoxes.value.find(b => b.box_no === transitForm.value.box_no)
  // Deep clone to avoid mutating the original data before submission
  if (box) {
    const clonedBox = JSON.parse(JSON.stringify(box))
    // Initialize inbound_quantity to full available quantity by default
    clonedBox.items.forEach((item: any) => {
      item.inbound_quantity = item.quantity
    })
    selectedBoxInfo.value = clonedBox
  } else {
    selectedBoxInfo.value = null
  }
}

const submitTransitInbound = async () => {
  if (!transitForm.value.box_no) {
    ElMessage.warning('请选择箱号')
    return
  }
  
  if (!selectedBoxInfo.value || !selectedBoxInfo.value.items) return
  const itemsToInbound = selectedBoxInfo.value.items.filter((i: any) => i.location_id && i.inbound_quantity && i.inbound_quantity > 0)
  if (itemsToInbound.length === 0) {
    ElMessage.warning('请至少填写一条明细的入库库位和入库数量')
    return
  }
  for (const item of itemsToInbound) {
    if (item.inbound_quantity > item.quantity) {
      ElMessage.warning(`物料 ${item.material_code} 的入库数量不能大于待入库数量`)
      return
    }
  }
  
  try {
    const payload = {
      box_no: transitForm.value.box_no,
      operator_id: 1, // mock
      items: itemsToInbound.map((i: any) => ({
        transit_id: i.id,
        location_id: i.location_id,
        inbound_quantity: i.inbound_quantity
      }))
    }
    
    await request.post('/orders/inbound/transit', payload)
    ElMessage.success('在途入库成功')
    const res: any = await request.get('/transit/available-boxes')
    availableBoxes.value = res
    const updatedBox = availableBoxes.value.find((b: any) => b.box_no === transitForm.value.box_no)
    if (updatedBox) {
      const clonedBox = JSON.parse(JSON.stringify(updatedBox))
      clonedBox.items.forEach((item: any) => {
        item.inbound_quantity = item.quantity
      })
      selectedBoxInfo.value = clonedBox
    } else {
      transitDialogVisible.value = false
    }
    fetchOrders()
  } catch (e) {}
}

const form = reactive({
  order_no: '',
  operator_id: 1,
  items: [
    { material_id: null, price_version_id: null, location_id: null, quantity: 1, contract_no: '', purchase_price: undefined, sale_price: undefined, currency: 'CNY' }
  ]
})

const fetchOptions = async () => {
  try {
    const resMaterials: any = await request.get('/materials/?limit=10000')
    materials.value = resMaterials.items || resMaterials
    
    const resLocations: any = await request.get('/locations/?limit=10000')
    locations.value = resLocations.items || resLocations
  } catch (error) {
    console.error('Failed to fetch options')
  }
}

const openDialog = () => {
  form.order_no = 'IN-' + new Date().getTime()
  form.items = [{ material_id: null, price_version_id: null, location_id: null, quantity: 1, contract_no: '', purchase_price: undefined, sale_price: undefined, currency: 'CNY' }]
  dialogVisible.value = true
  if (materials.value.length === 0) {
    fetchOptions()
  }
}

const addRow = () => {
  form.items.push({ material_id: null, price_version_id: null, location_id: null, quantity: 1, contract_no: '', purchase_price: undefined, sale_price: undefined, currency: 'CNY' })
}

const removeRow = (index: number) => {
  if (form.items.length <= 1) {
    ElMessage.warning('至少需要保留一条明细')
    return
  }
  form.items.splice(index, 1)
}

const fetchOrders = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    let url = `/orders/inbound?skip=${skip}&limit=${pageSize.value}`
    if (searchQuery.value) {
      url += `&material_code=${searchQuery.value}`
    }
    const res: any = await request.get(url)
    tableData.value = res.items || res
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

const exportData = () => {
  downloadFile('/api/v1/excel/export/inbound', 'inbound_records.xlsx')
}

const submitForm = async () => {
  if (form.items.length === 0) {
    ElMessage.warning('请添加入库明细')
    return
  }
  
  for (const item of form.items) {
    if (!item.material_id || !item.location_id) {
      ElMessage.warning('请完善物料和库位信息')
      return
    }
  }
  
  try {
    await request.post('/orders/inbound/bulk', form)
    ElMessage.success('批量入库单创建成功')
    dialogVisible.value = false
    fetchOrders()
  } catch (error) {
    // Error handled by interceptor
  }
}

onMounted(() => {
  fetchOrders()
  fetchOptions()
  if (route.query.transit === '1') {
    openTransitDialog()
    router.replace({ query: {} })
  }
})
</script>

<style scoped>
.inbound-container {
  padding: 20px;
}
.header-actions {
  display: flex;
  gap: 10px;
}
</style>
