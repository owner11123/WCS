<template>
  <div class="inventory-container">
    <div v-if="isMobile" class="mobile-only">
      <el-card shadow="hover" class="mobile-card">
        <div class="mobile-title">实时库存</div>
        <div class="mobile-search">
          <el-input v-model="mobileKeyword" placeholder="搜索库位/物料编码/描述" clearable @clear="handleSearch" @keyup.enter="handleSearch" />
          <el-button type="primary" @click="handleSearch">查询</el-button>
        </div>
      </el-card>
    </div>

    <div v-if="!isMobile" class="header-actions">
      <div class="left-actions">
        <el-input
          v-model="searchQuery.material"
          placeholder="搜索物料号/描述"
          clearable
          style="width: 200px; margin-right: 10px;"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        />
        <el-input
          v-model="searchQuery.location"
          placeholder="搜索库位"
          clearable
          style="width: 150px; margin-right: 10px;"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
      </div>
    </div>

    <el-table v-if="!isMobile" :data="tableData" style="width: 100%; margin-top: 20px;" v-loading="loading">
      <el-table-column prop="material_code" label="物料编码" width="150" />
      <el-table-column prop="material_description" label="物料描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="location_code" label="库位" width="150" />
      <el-table-column prop="batch_no" label="合同号(批次)" width="150" />
      <el-table-column prop="quantity" label="当前库存" width="100" />
      <el-table-column prop="borrow" label="借用" width="90">
        <template #default="scope">
          <span :style="{ color: scope.row.borrow < 0 ? '#F56C6C' : '#909399' }">
            {{ scope.row.borrow }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="check_diff" label="盘点差异" width="100">
        <template #default="scope">
          <span :style="{ color: scope.row.check_diff > 0 ? '#67C23A' : (scope.row.check_diff < 0 ? '#F56C6C' : '#909399') }">
            {{ scope.row.check_diff > 0 ? '+' : '' }}{{ scope.row.check_diff }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="total_inbound" label="总入库量" width="100" />
      <el-table-column prop="total_outbound" label="总出库量" width="100" />
      <el-table-column prop="purchase_price" label="采购价" width="100" />
      <el-table-column prop="sale_price" label="销售价" width="100" />
      <el-table-column prop="currency" label="货币" width="80" />
    </el-table>

    <div v-else class="mobile-list" v-loading="loading">
      <el-card v-for="row in tableData" :key="row.id" shadow="never" class="mobile-row">
        <div class="material">
          <div class="code">{{ row.material_code }}</div>
          <div class="desc" :title="row.material_description">{{ row.material_description }}</div>
        </div>
        <div class="line">
          <div class="k">库位</div>
          <div class="v">{{ row.location_code }}</div>
        </div>
        <div class="line">
          <div class="k">批次</div>
          <div class="v">{{ row.batch_no }}</div>
        </div>
        <div class="line">
          <div class="k">库存</div>
          <div class="v strong">{{ row.quantity }}</div>
        </div>
      </el-card>
      <div v-if="!tableData || tableData.length === 0" class="empty">暂无数据</div>
    </div>

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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'
import request from '../../utils/request'

const isMobile = computed(() => window.innerWidth <= 768)

const tableData = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const searchQuery = reactive({
  material: '',
  location: ''
})

const mobileKeyword = ref('')

const handleSearch = () => {
  currentPage.value = 1
  fetchInventory()
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchInventory()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchInventory()
}

const fetchInventory = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const limit = isMobile.value ? 200 : pageSize.value
    let url = `/inventory/?skip=${skip}&limit=${limit}`

    if (isMobile.value && mobileKeyword.value) {
      const kw = mobileKeyword.value.trim()
      if (kw) {
        url += `&q=${encodeURIComponent(kw)}`
      }
    } else {
      if (searchQuery.material) {
        url += `&material_code=${encodeURIComponent(searchQuery.material)}`
      }
      if (searchQuery.location) {
        url += `&location_code=${encodeURIComponent(searchQuery.location)}`
      }
    }
    
    const res: any = await request.get(url)
    tableData.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchInventory()
})
</script>

<style scoped>
.inventory-container {
  padding: 20px;
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  gap: 10px;
}
.mobile-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}
.mobile-row {
  border-radius: 12px;
}
.material {
  margin-bottom: 6px;
}
.code {
  font-weight: 700;
  color: #303133;
  font-size: 14px;
}
.desc {
  margin-top: 2px;
  color: #909399;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}
.k {
  color: #909399;
  font-size: 12px;
}
.v {
  color: #303133;
  font-size: 13px;
  max-width: 70%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: right;
}
.strong {
  font-weight: 700;
  font-size: 16px;
}
.empty {
  color: #909399;
  font-size: 13px;
  text-align: center;
  padding: 12px 0;
}
</style>
