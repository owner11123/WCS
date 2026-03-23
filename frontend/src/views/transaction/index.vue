<template>
  <div class="transaction-container">
    <div class="header-actions">
      <el-form :inline="true" :model="searchQuery" class="demo-form-inline">
        <el-form-item label="物料编码/描述">
          <el-input v-model="searchQuery.material_code" placeholder="输入关键字" clearable @clear="handleSearch" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="操作类型">
          <el-select v-model="searchQuery.transaction_type" placeholder="全部类型" clearable @change="handleSearch">
            <el-option label="入库 (Inbound)" value="inbound" />
            <el-option label="出库 (Outbound)" value="outbound" />
            <el-option label="移库移出 (Move Out)" value="movement_out" />
            <el-option label="移库移入 (Move In)" value="movement_in" />
            <el-option label="盘盈入库 (Check In)" value="check_in" />
            <el-option label="盘亏出库 (Check Out)" value="check_out" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期段">
          <el-date-picker
            v-model="searchQuery.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            @change="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
        </el-form-item>
        <el-form-item>
          <el-button type="success" @click="downloadExcel">下载Excel</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-table :data="tableData" style="width: 100%;" v-loading="loading" border stripe>
      <el-table-column prop="transaction_time" label="操作时间" width="180">
        <template #default="scope">
          {{ new Date(scope.row.transaction_time).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column prop="operator_name" label="操作人" width="120" />
      <el-table-column prop="transaction_type" label="操作类型" width="120">
        <template #default="scope">
          <el-tag :type="getTypeColor(scope.row.transaction_type)">
            {{ getTypeName(scope.row.transaction_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="material_code" label="物料编码" width="120" />
      <el-table-column prop="material_description" label="物料描述" min-width="180" show-overflow-tooltip />
      <el-table-column prop="batch_no" label="批次/合同号" width="140" />
      <el-table-column prop="location_code" label="涉及库位" width="120" />
      <el-table-column prop="quantity_change" label="变动数量" width="100">
        <template #default="scope">
          <span :style="{ color: scope.row.quantity_change > 0 ? '#67C23A' : '#F56C6C', fontWeight: 'bold' }">
            {{ scope.row.quantity_change > 0 ? '+' : '' }}{{ scope.row.quantity_change }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="balance" label="结余库存" width="100" />
      <el-table-column prop="reference_order" label="关联单号" width="180" />
    </el-table>

    <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import request from '../../utils/request'
import { downloadFile } from '../../utils/download'

const tableData = ref([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const searchQuery = reactive({
  material_code: '',
  transaction_type: '',
  date_range: [] as string[]
})

const getTypeName = (type: string) => {
  const map: Record<string, string> = {
    'inbound': '入库',
    'outbound': '出库',
    'borrow_out': '借用出库',
    'borrow_return': '借用归还',
    'movement_out': '移库移出',
    'movement_in': '移库移入',
    'check_in': '盘盈入库',
    'check_out': '盘亏出库'
  }
  return map[type] || type
}

const getTypeColor = (type: string) => {
  if (['inbound', 'movement_in', 'check_in', 'borrow_return'].includes(type)) return 'success'
  if (['outbound', 'movement_out', 'check_out', 'borrow_out'].includes(type)) return 'danger'
  return 'info'
}

const fetchTransactions = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    let url = `/inventory/transactions?skip=${skip}&limit=${pageSize.value}`
    
    if (searchQuery.material_code) url += `&material_code=${searchQuery.material_code}`
    if (searchQuery.transaction_type) url += `&transaction_type=${searchQuery.transaction_type}`
    if (searchQuery.date_range && searchQuery.date_range.length === 2) {
      url += `&start_date=${encodeURIComponent(searchQuery.date_range[0])}&end_date=${encodeURIComponent(searchQuery.date_range[1])}`
    }
    
    const res: any = await request.get(url)
    tableData.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

const downloadExcel = () => {
  let url = '/api/v1/excel/export/transactions'
  if (searchQuery.date_range && searchQuery.date_range.length === 2) {
    url += `?start_date=${encodeURIComponent(searchQuery.date_range[0])}&end_date=${encodeURIComponent(searchQuery.date_range[1])}`
  }
  downloadFile(url, 'transactions.xlsx')
}

const handleSearch = () => {
  currentPage.value = 1
  fetchTransactions()
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchTransactions()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchTransactions()
}

onMounted(() => {
  fetchTransactions()
})
</script>

<style scoped>
.transaction-container {
  padding: 20px;
}
.header-actions {
  margin-bottom: 20px;
}
</style>
