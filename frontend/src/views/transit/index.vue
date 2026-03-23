<template>
  <div class="transit-container">
    <div class="header-actions">
      <div class="left-actions">
        <el-input
          v-model="searchQuery.keyword"
          placeholder="搜索箱号/物料编码"
          clearable
          style="width: 200px; margin-right: 10px;"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        />
        <el-select v-model="searchQuery.status" placeholder="状态" clearable style="width: 150px; margin-right: 10px;" @change="handleSearch">
          <el-option label="在途中" value="in_transit" />
          <el-option label="已入库" value="received" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
      </div>
      <div class="right-actions">
        <el-button type="success" :icon="Download" @click="downloadTemplate">下载模板</el-button>
        <el-upload
          class="upload-demo"
          action="/api/v1/excel/import/transit"
          :headers="uploadHeaders"
          :show-file-list="false"
          :on-success="handleImportSuccess"
          :on-error="handleImportError"
          style="display: inline-block; margin-left: 10px;"
        >
          <el-button type="primary" :icon="Upload">导入在途库存</el-button>
        </el-upload>
      </div>
    </div>

    <el-table :data="tableData" style="width: 100%; margin-top: 20px;" v-loading="loading" border>
      <el-table-column prop="box_no" label="箱号" width="150" />
      <el-table-column prop="material_code" label="物料编码" width="120" />
      <el-table-column prop="material_description" label="物料描述" min-width="180" show-overflow-tooltip />
      <el-table-column prop="vehicle_model" label="适用车型" width="120" />
      <el-table-column prop="contract_no" label="采购合同号" width="140" />
      <el-table-column prop="quantity" label="待入库数量" width="100" />
      <el-table-column prop="received_quantity" label="已入库数量" width="100" />
      <el-table-column prop="purchase_price" label="采购价" width="100" />
      <el-table-column prop="sale_price" label="销售价" width="100" />
      <el-table-column prop="currency" label="货币" width="80" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'received' ? 'success' : 'warning'">
            {{ scope.row.status === 'received' ? '已入库' : '在途中' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="导入时间" width="180">
        <template #default="scope">
          {{ new Date(scope.row.created_at).toLocaleString() }}
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { Search, Download, Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '../../utils/request'
import { downloadFile } from '../../utils/download'

const uploadHeaders = computed(() => {
  return {
    Authorization: 'Bearer ' + localStorage.getItem('token')
  }
})

const tableData = ref([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const searchQuery = reactive({
  keyword: '',
  status: ''
})

const fetchTransit = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    let url = `/transit/?skip=${skip}&limit=${pageSize.value}`
    if (searchQuery.keyword) url += `&q=${encodeURIComponent(searchQuery.keyword)}`
    if (searchQuery.status) url += `&status=${searchQuery.status}`
    
    const res: any = await request.get(url)
    tableData.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchTransit()
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchTransit()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchTransit()
}

const downloadTemplate = () => {
  downloadFile('/api/v1/excel/template/transit', 'transit_template.xlsx')
}

const handleImportSuccess = (res: any) => {
  ElMessage.success(res.message || '导入成功')
  fetchTransit()
}

const handleImportError = (_err: any) => {
  ElMessage.error('导入失败')
}

onMounted(() => {
  fetchTransit()
})
</script>

<style scoped>
.transit-container {
  padding: 20px;
}
.header-actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}
</style>
