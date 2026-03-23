<template>
  <div class="check-container">
    <div v-if="isMobile" class="mobile-only">
      <el-card shadow="hover" class="mobile-card">
        <div class="mobile-title">盘点管理</div>
        <div class="mobile-actions">
          <el-button type="primary" style="width: 100%" @click="openCreateDialog">新建盘点任务</el-button>
        </div>
      </el-card>
    </div>

    <div v-else class="header-actions">
      <el-button type="primary" @click="openCreateDialog">创建盘点任务</el-button>
    </div>

    <el-table v-if="!isMobile" :data="tableData" style="width: 100%; margin-top: 20px;" v-loading="loading" border>
      <el-table-column prop="check_no" label="盘点单号" width="180" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'completed' ? 'success' : 'warning'">
            {{ scope.row.status === 'completed' ? '已完成' : '进行中' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="remarks" label="备注" min-width="150" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="scope">
          {{ new Date(scope.row.created_at).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column prop="completed_at" label="完成时间" width="180">
        <template #default="scope">
          {{ scope.row.completed_at ? new Date(scope.row.completed_at).toLocaleString() : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" align="center">
        <template #default="scope">
          <el-button type="primary" size="small" @click="openDetail(scope.row)">
            {{ scope.row.status === 'completed' ? '查看明细' : '去盘点' }}
          </el-button>
          <el-button v-if="scope.row.status !== 'completed'" type="danger" size="small" @click="deleteCheck(scope.row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-else class="mobile-list" v-loading="loading">
      <el-card v-for="row in tableData" :key="row.id" shadow="never" class="mobile-row">
        <div class="row-title">
          <div class="row-no">{{ row.check_no }}</div>
          <el-tag size="small" :type="row.status === 'completed' ? 'success' : 'warning'">
            {{ row.status === 'completed' ? '已完成' : '进行中' }}
          </el-tag>
        </div>
        <div class="row-meta">
          <span>创建: {{ row.created_at ? new Date(row.created_at).toLocaleString() : '-' }}</span>
        </div>
        <div class="row-meta" v-if="row.remarks">备注: {{ row.remarks }}</div>
        <el-button type="primary" style="width: 100%; margin-top: 10px;" @click="openDetail(row)">
          {{ row.status === 'completed' ? '查看明细' : '去盘点' }}
        </el-button>
      </el-card>
      <div v-if="!tableData || tableData.length === 0" class="empty">暂无盘点任务</div>
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

    <!-- Create Check Dialog -->
    <el-dialog v-model="createDialogVisible" title="创建盘点任务" :fullscreen="isMobile" :width="isMobile ? '100%' : '500px'">
      <el-form :model="createForm" :label-width="isMobile ? 'auto' : '100px'" :label-position="isMobile ? 'top' : 'right'">
        <el-form-item label="盘点范围">
          <el-select v-model="createForm.location_ids" multiple placeholder="不选则为全库盘点" style="width: 100%">
            <el-option
              v-for="item in locations"
              :key="item.id"
              :label="item.code"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.remarks" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitCreate">创建</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Detail/Execution Dialog -->
    <el-dialog v-model="detailDialogVisible" :title="isCompleted ? '盘点明细' : '执行盘点'" width="900px" fullscreen>
      <div v-if="!isCompleted" style="margin-bottom: 15px;">
        <el-alert title="请核对实物并录入实际数量，系统会自动计算差异并进行平账。" type="info" show-icon />
      </div>

      <div class="detail-toolbar">
        <el-input v-model="detailKeyword" placeholder="搜索库位/物料编码/描述/批次" clearable @keyup.enter="noop" />
        <el-button type="primary" plain @click="downloadCheckCsv">下载盘点表</el-button>
      </div>
      
      <el-table v-if="!isMobile" :data="filteredItems" border style="width: 100%">
        <el-table-column prop="location_code" label="库位" width="120" />
        <el-table-column prop="material_code" label="物料编码" width="120" />
        <el-table-column prop="material_description" label="物料描述" min-width="150" show-overflow-tooltip />
        <el-table-column prop="batch_no" label="批次" width="120" />
        <el-table-column prop="system_quantity" label="账面库存" width="100" />
        
        <el-table-column label="实际数量" width="150">
          <template #default="scope">
            <span v-if="isCompleted">{{ scope.row.actual_quantity }}</span>
            <el-input-number v-else v-model="scope.row.actual_quantity" :min="0" style="width: 100%" @change="() => calculateDiff(scope.row)" />
          </template>
        </el-table-column>
        
        <el-table-column label="差异数量" width="100">
          <template #default="scope">
            <span :style="{ color: scope.row.difference > 0 ? '#67C23A' : (scope.row.difference < 0 ? '#F56C6C' : '#909399') }">
              {{ scope.row.difference > 0 ? '+' : '' }}{{ scope.row.difference || 0 }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column label="差异原因" min-width="150">
          <template #default="scope">
            <span v-if="isCompleted">{{ scope.row.reason || '-' }}</span>
            <el-input v-else v-model="scope.row.reason" placeholder="如有差异请填写原因" :disabled="!scope.row.difference" />
          </template>
        </el-table-column>
      </el-table>

      <div v-else class="mobile-items">
        <el-card v-for="row in filteredItems" :key="row.id" shadow="never" class="mobile-item">
          <div class="item-head">
            <div class="item-loc">{{ row.location_code }}</div>
            <div class="item-batch">{{ row.batch_no }}</div>
          </div>
          <div class="item-code">{{ row.material_code }}</div>
          <div class="item-desc" :title="row.material_description">{{ row.material_description }}</div>
          <div class="item-kv">
            <div class="k">账面</div>
            <div class="v">{{ row.system_quantity }}</div>
          </div>
          <div class="item-kv">
            <div class="k">实际</div>
            <div class="v">
              <span v-if="isCompleted">{{ row.actual_quantity }}</span>
              <el-input-number v-else v-model="row.actual_quantity" :min="0" controls-position="right" style="width: 100%" @change="() => calculateDiff(row)" />
            </div>
          </div>
          <div class="item-kv">
            <div class="k">差异</div>
            <div class="v" :style="{ color: row.difference > 0 ? '#67C23A' : (row.difference < 0 ? '#F56C6C' : '#909399') }">
              {{ row.difference > 0 ? '+' : '' }}{{ row.difference || 0 }}
            </div>
          </div>
          <div style="margin-top: 8px;">
            <span v-if="isCompleted">{{ row.reason || '-' }}</span>
            <el-input v-else v-model="row.reason" placeholder="如有差异请填写原因" :disabled="!row.difference" />
          </div>
        </el-card>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailDialogVisible = false">{{ isCompleted ? '关闭' : '暂存进度' }}</el-button>
          <el-button v-if="!isCompleted" type="warning" @click="saveProgress">保存当前录入</el-button>
          <el-button v-if="!isCompleted" type="primary" @click="completeCheck">完成盘点并平账</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

const isMobile = computed(() => window.innerWidth <= 768)

const tableData = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const locations = ref<any[]>([])
const createDialogVisible = ref(false)
const createForm = ref({
  location_ids: [],
  remarks: ''
})

const detailDialogVisible = ref(false)
const currentCheck = ref<any>(null)
const currentItems = ref<any[]>([])
const detailKeyword = ref('')

const isCompleted = computed(() => currentCheck.value?.status === 'completed')

const noop = () => {}

const filteredItems = computed(() => {
  const kw = detailKeyword.value.trim().toLowerCase()
  if (!kw) return currentItems.value
  return currentItems.value.filter((i: any) => {
    const s = `${i.location_code || ''} ${i.material_code || ''} ${i.material_description || ''} ${i.batch_no || ''}`.toLowerCase()
    return s.includes(kw)
  })
})

const csvEscape = (v: any) => {
  const s = v === null || v === undefined ? '' : String(v)
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`
  return s
}

const downloadCheckCsv = () => {
  const rows = filteredItems.value
  const header = ['库位', '物料编码', '物料描述', '批次', '账面库存', '实际数量', '差异数量', '差异原因']
  const lines = [header.map(csvEscape).join(',')]
  for (const r of rows as any[]) {
    lines.push(
      [
        r.location_code,
        r.material_code,
        r.material_description,
        r.batch_no,
        r.system_quantity,
        r.actual_quantity,
        r.difference,
        r.reason
      ].map(csvEscape).join(',')
    )
  }

  const blob = new Blob([`\ufeff${lines.join('\n')}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  const name = currentCheck.value?.check_no ? `${currentCheck.value.check_no}.csv` : '盘点表.csv'
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const fetchChecks = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const res: any = await request.get(`/inventory-management/checks?skip=${skip}&limit=${pageSize.value}`)
    tableData.value = res.items || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchChecks()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchChecks()
}

const openCreateDialog = async () => {
  createForm.value = { location_ids: [], remarks: '' }
  try {
    const res: any = await request.get('/locations/?limit=10000')
    locations.value = res.items || res
  } catch (e) {}
  createDialogVisible.value = true
}

const submitCreate = async () => {
  try {
    const payload = {
      operator_id: 1, // mock
      location_ids: createForm.value.location_ids.length ? createForm.value.location_ids : null,
      remarks: createForm.value.remarks
    }
    await request.post('/inventory-management/checks', payload)
    ElMessage.success('盘点任务创建成功')
    createDialogVisible.value = false
    fetchChecks()
  } catch (e) {}
}

const openDetail = async (row: any) => {
  try {
    const res: any = await request.get(`/inventory-management/checks/${row.id}`)
    currentCheck.value = res.check
    detailKeyword.value = ''
    currentItems.value = res.items.map((i: any) => ({
      ...i,
      actual_quantity: i.actual_quantity !== null ? i.actual_quantity : i.system_quantity,
      difference: i.difference || 0
    }))
    detailDialogVisible.value = true
  } catch (e) {}
}

const deleteCheck = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确认删除盘点任务 ${row.check_no} 吗？删除后不可恢复。`, '提示', { type: 'warning' })
    await request.delete(`/inventory-management/checks/${row.id}`)
    ElMessage.success('已删除盘点任务')
    fetchChecks()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const calculateDiff = (row: any) => {
  if (row.actual_quantity !== null && row.actual_quantity !== undefined) {
    row.difference = row.actual_quantity - row.system_quantity
  }
}

const saveProgress = async () => {
  try {
    await request.put(`/inventory-management/checks/${currentCheck.value.id}`, {
      items: currentItems.value.map(i => ({
        id: i.id,
        actual_quantity: i.actual_quantity,
        reason: i.reason
      }))
    })
    ElMessage.success('进度已保存')
  } catch (e) {}
}

const completeCheck = async () => {
  const hasUnexplainedDiff = currentItems.value.some(i => i.difference !== 0 && !i.reason)
  if (hasUnexplainedDiff) {
    ElMessage.warning('存在差异的物料必须填写差异原因！')
    return
  }
  
  try {
    await ElMessageBox.confirm('确认完成盘点吗？确认后系统库存将根据实盘数量自动调整且不可撤销！', '提示', {
      type: 'warning'
    })
    
    // First save the latest inputs
    await saveProgress()
    
    // Then post
    await request.post(`/inventory-management/checks/${currentCheck.value.id}/complete`)
    ElMessage.success('盘点已完成，库存已更新！')
    detailDialogVisible.value = false
    fetchChecks()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

onMounted(() => {
  fetchChecks()
})
</script>

<style scoped>
.check-container {
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
.mobile-actions {
  display: flex;
  flex-direction: column;
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
.row-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}
.row-no {
  font-weight: 700;
  color: #303133;
}
.row-meta {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}
.empty {
  color: #909399;
  font-size: 13px;
  text-align: center;
  padding: 12px 0;
}
.mobile-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.mobile-item {
  border-radius: 12px;
}
.item-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 12px;
  color: #606266;
}
.item-loc {
  font-weight: 700;
  color: #303133;
}
.item-batch {
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 55%;
}
.item-code {
  margin-top: 6px;
  font-weight: 700;
  color: #303133;
}
.item-desc {
  margin-top: 2px;
  color: #909399;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-kv {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.item-kv .k {
  color: #909399;
  font-size: 12px;
}
.item-kv .v {
  color: #303133;
  font-size: 13px;
  text-align: right;
  width: 60%;
}
.detail-toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}
</style>
