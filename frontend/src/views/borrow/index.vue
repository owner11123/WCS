<template>
  <div class="borrow-container">
    <div v-if="isMobile" class="mobile-only">
      <el-card shadow="hover" class="mobile-card">
        <div class="mobile-title">备件借用</div>
        <el-button type="primary" style="width: 100%" @click="openCreateDialog">新增借用单</el-button>
      </el-card>
    </div>

    <div v-else class="header-actions">
      <el-button type="primary" @click="openCreateDialog">新增借用单</el-button>
    </div>

    <el-form v-if="!isMobile" :inline="true" :model="query" class="demo-form-inline" style="margin-top: 10px;">
      <el-form-item label="状态">
        <el-select v-model="query.status" clearable placeholder="全部">
          <el-option label="未归还" value="open" />
          <el-option label="已归还" value="closed" />
        </el-select>
      </el-form-item>
      <el-form-item label="借用方">
        <el-input v-model="query.borrower" clearable placeholder="输入借用方" @keyup.enter="handleSearch" @clear="handleSearch" />
      </el-form-item>
      <el-form-item label="日期段">
        <el-date-picker
          v-model="query.date_range"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          @change="handleSearch"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-if="!isMobile" :data="tableData" style="width: 100%; margin-top: 20px;" v-loading="loading" border stripe>
      <el-table-column prop="borrow_no" label="借用单号" width="180" />
      <el-table-column prop="borrower" label="借用方" width="160" />
      <el-table-column prop="borrower_unit" label="单位" width="160" />
      <el-table-column prop="borrow_time" label="借用时间" width="180">
        <template #default="scope">
          {{ new Date(scope.row.borrow_time).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'closed' ? 'success' : 'warning'">
            {{ scope.row.status === 'closed' ? '已归还' : '未归还' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240" align="center">
        <template #default="scope">
          <el-button size="small" @click="openDetail(scope.row)">详情</el-button>
          <el-button v-if="scope.row.status === 'open'" type="primary" size="small" @click="openReturn(scope.row)">归还</el-button>
          <el-button v-if="scope.row.status === 'open'" type="danger" size="small" @click="deleteOrder(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="!isMobile" style="margin-top: 20px; display: flex; justify-content: flex-end;">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <el-dialog v-model="createDialogVisible" title="新增借用单" :fullscreen="isMobile" :width="isMobile ? '100%' : '900px'">
      <el-form :model="createForm" :label-width="isMobile ? 'auto' : '120px'" :label-position="isMobile ? 'top' : 'right'">
        <el-form-item label="借用方">
          <el-input v-model="createForm.borrower" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="createForm.borrower_unit" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.remark" />
        </el-form-item>
      </el-form>

      <div v-if="isMobile" class="mobile-search">
        <el-input v-model="inventoryQuery.material_code" placeholder="搜索物料编码/描述" clearable @keyup.enter="searchInventory" />
        <el-input v-model="inventoryQuery.location_code" placeholder="搜索库位编码" clearable @keyup.enter="searchInventory" />
        <el-button type="primary" style="width: 100%" @click="searchInventory">查询库存</el-button>
      </div>
      <div v-else style="display:flex; gap:10px; margin: 10px 0;">
        <el-input v-model="inventoryQuery.material_code" placeholder="搜索物料编码/描述" clearable @keyup.enter="searchInventory" style="width: 260px;" />
        <el-input v-model="inventoryQuery.location_code" placeholder="搜索库位编码" clearable @keyup.enter="searchInventory" style="width: 220px;" />
        <el-button type="primary" @click="searchInventory">查询库存</el-button>
      </div>

      <el-table v-if="!isMobile" :data="inventoryList" height="220" border stripe v-loading="invLoading">
        <el-table-column prop="material_code" label="物料编码" width="130" />
        <el-table-column prop="material_description" label="物料描述" min-width="180" show-overflow-tooltip />
        <el-table-column prop="location_code" label="库位" width="120" />
        <el-table-column prop="batch_no" label="批次/合同号" width="140" />
        <el-table-column prop="quantity" label="可用库存" width="100" />
        <el-table-column label="操作" width="100" align="center">
          <template #default="scope">
            <el-button size="small" @click="addBorrowItem(scope.row)">添加</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-else class="mobile-inv" v-loading="invLoading">
        <el-card v-for="row in inventoryList" :key="`${row.id}_${row.price_version_id}`" shadow="never" class="mobile-inv-row">
          <div class="inv-title">
            <div class="inv-code">{{ row.material_code }}</div>
            <div class="inv-qty">可用 {{ row.quantity }}</div>
          </div>
          <div class="inv-desc" :title="row.material_description">{{ row.material_description }}</div>
          <div class="inv-meta">{{ row.location_code }} | {{ row.batch_no }}</div>
          <el-button type="primary" plain style="width: 100%; margin-top: 10px;" @click="addBorrowItem(row)">添加</el-button>
        </el-card>
        <div v-if="!inventoryList || inventoryList.length === 0" class="empty">请先查询库存</div>
      </div>

      <div style="margin-top: 12px; font-weight: bold;">借用明细</div>
      <el-table v-if="!isMobile" :data="createForm.items" height="220" border stripe style="margin-top: 8px;">
        <el-table-column prop="material_code" label="物料编码" width="130" />
        <el-table-column prop="material_description" label="物料描述" min-width="180" show-overflow-tooltip />
        <el-table-column prop="location_code" label="库位" width="120" />
        <el-table-column prop="batch_no" label="批次/合同号" width="140" />
        <el-table-column prop="available" label="可用库存" width="100" />
        <el-table-column label="借用数量" width="140">
          <template #default="scope">
            <el-input-number v-model="scope.row.quantity" :min="1" :max="scope.row.available" controls-position="right" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="scope">
            <el-button type="danger" size="small" @click="removeBorrowItem(scope.$index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-else class="mobile-items">
        <el-card v-for="(it, idx) in createForm.items" :key="idx" shadow="never" class="mobile-item-card">
          <div class="inv-title">
            <div class="inv-code">{{ it.material_code }}</div>
            <el-button type="danger" size="small" @click="removeBorrowItem(idx)">删除</el-button>
          </div>
          <div class="inv-desc" :title="it.material_description">{{ it.material_description }}</div>
          <div class="inv-meta">{{ it.location_code }} | {{ it.batch_no }}</div>
          <div class="inv-meta">可用 {{ it.available }}</div>
          <div style="margin-top: 10px;">
            <el-input-number v-model="it.quantity" :min="1" :max="it.available" controls-position="right" style="width: 100%" />
          </div>
        </el-card>
        <div v-if="!createForm.items || createForm.items.length === 0" class="empty">暂无借用明细</div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitBorrow">提交借用</el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog v-if="!isMobile" v-model="detailDialogVisible" title="借用单详情" width="820px">
      <div style="margin-bottom: 10px;">
        <div>借用单号：{{ detail?.borrow_no }}</div>
        <div>借用方：{{ detail?.borrower }} {{ detail?.borrower_unit || '' }}</div>
        <div>状态：{{ detail?.status === 'closed' ? '已归还' : '未归还' }}</div>
      </div>
      <el-table :data="detail?.items || []" border stripe>
        <el-table-column prop="id" label="行ID" width="80" />
        <el-table-column prop="material_id" label="物料ID" width="90" />
        <el-table-column prop="location_id" label="库位ID" width="90" />
        <el-table-column prop="price_version_id" label="批次ID" width="90" />
        <el-table-column prop="quantity" label="借用数量" width="100" />
        <el-table-column prop="returned_quantity" label="已归还" width="100" />
        <el-table-column label="未归还" width="100">
          <template #default="scope">
            {{ scope.row.quantity - scope.row.returned_quantity }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="行状态" width="100" />
      </el-table>
    </el-dialog>

    <el-dialog v-if="!isMobile" v-model="returnDialogVisible" title="归还借用单" width="820px">
      <div style="margin-bottom: 10px;">
        <div>借用单号：{{ detail?.borrow_no }}</div>
        <div>借用方：{{ detail?.borrower }} {{ detail?.borrower_unit || '' }}</div>
      </div>
      <el-table :data="returnItems" border stripe>
        <el-table-column prop="borrow_item_id" label="行ID" width="90" />
        <el-table-column prop="material_id" label="物料ID" width="90" />
        <el-table-column prop="location_id" label="原库位ID" width="90" />
        <el-table-column prop="price_version_id" label="批次ID" width="90" />
        <el-table-column prop="remaining" label="可归还" width="100" />
        <el-table-column label="归还数量" width="140">
          <template #default="scope">
            <el-input-number v-model="scope.row.return_quantity" :min="1" :max="scope.row.remaining" controls-position="right" />
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="returnDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitReturn">确认归还</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

const isMobile = computed(() => window.innerWidth <= 768)

const tableData = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const query = reactive({
  status: '',
  borrower: '',
  date_range: [] as string[]
})

const fetchOrders = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    let url = `/borrow/orders?skip=${skip}&limit=${pageSize.value}`
    if (query.status) url += `&status=${encodeURIComponent(query.status)}`
    if (query.borrower) url += `&borrower=${encodeURIComponent(query.borrower)}`
    if (query.date_range && query.date_range.length === 2) {
      url += `&start_date=${encodeURIComponent(query.date_range[0])}&end_date=${encodeURIComponent(query.date_range[1])}`
    }
    const res: any = await request.get(url)
    tableData.value = res.items || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

const deleteOrder = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确认删除借用单 ${row.borrow_no} 吗？删除后不可恢复。`, '提示', { type: 'warning' })
    await request.delete(`/borrow/orders/${encodeURIComponent(row.borrow_no)}`)
    ElMessage.success('已删除借用单')
    fetchOrders()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

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

const createDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const returnDialogVisible = ref(false)
const detail = ref<any>(null)

const createForm = ref({
  borrower: '',
  borrower_unit: '',
  remark: '',
  items: [] as any[]
})

const inventoryQuery = reactive({
  material_code: '',
  location_code: ''
})
const inventoryList = ref<any[]>([])
const invLoading = ref(false)

const searchInventory = async () => {
  invLoading.value = true
  try {
    let url = `/inventory/?skip=0&limit=100`
    if (inventoryQuery.material_code) url += `&material_code=${encodeURIComponent(inventoryQuery.material_code)}`
    if (inventoryQuery.location_code) url += `&location_code=${encodeURIComponent(inventoryQuery.location_code)}`
    const res: any = await request.get(url)
    inventoryList.value = res.items || []
  } finally {
    invLoading.value = false
  }
}

const openCreateDialog = () => {
  createForm.value = {
    borrower: '',
    borrower_unit: '',
    remark: '',
    items: []
  }
  inventoryQuery.material_code = ''
  inventoryQuery.location_code = ''
  inventoryList.value = []
  createDialogVisible.value = true
}

const addBorrowItem = (row: any) => {
  const exists = createForm.value.items.find((x: any) => x.material_id === row.material_id && x.location_id === row.location_id && x.price_version_id === row.price_version_id)
  if (exists) {
    ElMessage.warning('该明细已添加')
    return
  }
  createForm.value.items.push({
    material_id: row.material_id,
    location_id: row.location_id,
    price_version_id: row.price_version_id,
    material_code: row.material_code,
    material_description: row.material_description,
    location_code: row.location_code,
    batch_no: row.batch_no,
    available: row.quantity,
    quantity: 1
  })
}

const removeBorrowItem = (index: number) => {
  createForm.value.items.splice(index, 1)
}

const submitBorrow = async () => {
  if (!createForm.value.borrower) {
    ElMessage.warning('请填写借用方')
    return
  }
  if (!createForm.value.items.length) {
    ElMessage.warning('请添加借用明细')
    return
  }
  const payload = {
    borrower: createForm.value.borrower,
    borrower_unit: createForm.value.borrower_unit,
    remark: createForm.value.remark,
    items: createForm.value.items.map((x: any) => ({
      material_id: x.material_id,
      location_id: x.location_id,
      price_version_id: x.price_version_id,
      quantity: x.quantity
    }))
  }
  const res: any = await request.post('/borrow/orders', payload)
  ElMessage.success(`创建成功：${res.borrow_no}`)
  createDialogVisible.value = false
  fetchOrders()
}

const openDetail = async (row: any) => {
  const res: any = await request.get(`/borrow/orders/${encodeURIComponent(row.borrow_no)}`)
  detail.value = res
  detailDialogVisible.value = true
}

const returnItems = ref<any[]>([])

const openReturn = async (row: any) => {
  const res: any = await request.get(`/borrow/orders/${encodeURIComponent(row.borrow_no)}`)
  detail.value = res
  returnItems.value = (res.items || [])
    .filter((x: any) => (x.quantity - x.returned_quantity) > 0)
    .map((x: any) => ({
      borrow_item_id: x.id,
      material_id: x.material_id,
      location_id: x.location_id,
      price_version_id: x.price_version_id,
      remaining: x.quantity - x.returned_quantity,
      return_quantity: x.quantity - x.returned_quantity
    }))
  returnDialogVisible.value = true
}

const submitReturn = async () => {
  if (!detail.value?.borrow_no) return
  const payload = {
    items: returnItems.value
      .filter(x => x.return_quantity && x.return_quantity > 0)
      .map(x => ({
        borrow_item_id: x.borrow_item_id,
        return_quantity: x.return_quantity
      }))
  }
  if (!payload.items.length) {
    ElMessage.warning('请填写归还数量')
    return
  }
  const res: any = await request.post(`/borrow/orders/${encodeURIComponent(detail.value.borrow_no)}/return`, payload)
  ElMessage.success(res.status === 'closed' ? '归还完成，已核销' : '归还成功')
  returnDialogVisible.value = false
  fetchOrders()
}

onMounted(() => {
  if (!isMobile.value) {
    fetchOrders()
  }
})
</script>

<style scoped>
.borrow-container {
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
.mobile-search {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 10px 0;
}
.mobile-inv {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 10px;
}
.mobile-inv-row {
  border-radius: 12px;
}
.inv-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}
.inv-code {
  font-weight: 700;
  color: #303133;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.inv-qty {
  font-weight: 700;
  color: #409eff;
  font-size: 14px;
  flex-shrink: 0;
}
.inv-desc {
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.inv-meta {
  margin-top: 4px;
  color: #606266;
  font-size: 12px;
}
.mobile-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 10px;
}
.mobile-item-card {
  border-radius: 12px;
}
.empty {
  color: #909399;
  font-size: 13px;
  text-align: center;
  padding: 10px 0;
}
</style>
