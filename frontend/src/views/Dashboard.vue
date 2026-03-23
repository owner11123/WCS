<template>
  <div class="dashboard-container">
    <div class="filters">
      <el-form :inline="true" :model="filters">
        <el-form-item label="USD→CNY">
          <el-input-number v-model="filters.usd_to_cny" :min="0" :step="0.01" controls-position="right" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="refreshAll">刷新</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-row :gutter="12" class="kpi-row">
      <el-col :span="8">
        <el-card shadow="hover" class="kpi-card" v-loading="loadingKpi">
          <template #header>当前库存金额（CNY）</template>
          <div class="kpi-value">{{ formatAmount(kpi.stock_amount_cny) }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="kpi-card" v-loading="loadingKpi">
          <template #header>在途库存金额（CNY）</template>
          <div class="kpi-value">{{ formatAmount(kpi.transit_amount_cny) }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="kpi-card" v-loading="loadingKpi">
          <template #header>{{ kpiModeLabel }}出库数量</template>
          <div class="kpi-value">{{ formatInt(kpiMode === 'week' ? kpi.week_outbound_qty : kpi.month_outbound_qty) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12" class="kpi-row">
      <el-col :span="8">
        <el-card shadow="hover" class="kpi-card" v-loading="loadingKpi">
          <template #header>总库存金额（CNY）</template>
          <div class="kpi-value">{{ formatAmount(kpi.total_stock_amount_cny) }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="kpi-card" v-loading="loadingKpi">
          <template #header>{{ kpiModeLabel }}出库金额（CNY）</template>
          <div class="kpi-value">{{ formatAmount(kpiMode === 'week' ? kpi.week_outbound_amount_cny : kpi.month_outbound_amount_cny) }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="kpi-card" v-loading="loadingKpi">
          <template #header>USD→CNY</template>
          <div class="kpi-value">{{ formatAmount(filters.usd_to_cny) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <div class="kpi-mode">
      <el-radio-group v-model="kpiMode" size="small">
        <el-radio-button label="week">本周</el-radio-button>
        <el-radio-button label="month">本月</el-radio-button>
      </el-radio-group>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="库存金额（按合同号）" name="contract">
        <el-row :gutter="12" class="chart-row">
          <el-col :span="12">
            <el-card shadow="hover" class="chart-card" v-loading="loadingStockTotal">
              <template #header>库存金额对账（总计）</template>
              <v-chart class="chart" :option="stockReconcileBarOption" autoresize />
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover" class="chart-card" v-loading="loadingStockContractTotal">
              <template #header>按合同号筛选（金额对账）</template>
              <div class="chart-filter">
                <el-select v-model="selectedContract" filterable clearable placeholder="选择合同号" style="width: 100%;" @change="fetchStockContractReconcile">
                  <el-option v-for="c in contractOptions" :key="c" :label="c" :value="c" />
                </el-select>
              </div>
              <v-chart class="chart" :option="stockContractReconcileBarOption" autoresize />
            </el-card>
          </el-col>
        </el-row>

        <el-card shadow="hover" class="chart-card" v-loading="loadingStockTopn">
          <template #header>TopN 合同号（入库/出库/剩余金额）</template>
          <v-chart class="chart chart-tall" :option="stockTopnBarOption" autoresize />
        </el-card>

        <div class="table-actions">
          <el-button type="success" @click="downloadContract">下载</el-button>
        </div>
        <el-table :data="contractRows" v-loading="loadingContract" border stripe style="width: 100%;">
          <el-table-column prop="contract_no" label="合同号" width="180" />
          <el-table-column prop="inbound_qty" label="总入库数量" width="110" />
          <el-table-column prop="inbound_amount_cny" label="总入库金额(CNY)" width="140" />
          <el-table-column prop="outbound_qty" label="总出库数量" width="110" />
          <el-table-column prop="outbound_amount_cny" label="总出库金额(CNY)" width="140" />
          <el-table-column prop="stock_qty" label="剩余库存数量" width="120" />
          <el-table-column prop="stock_amount_cny" label="剩余库存金额(CNY)" width="150" />
          <el-table-column prop="transit_qty" label="在途数量" width="90" />
          <el-table-column prop="transit_amount_cny" label="在途金额(CNY)" width="130" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="物料大类分析" name="category">
        <el-card shadow="hover" class="chart-card" v-loading="loadingCategoryPie">
          <template #header>物料大类金额占比</template>
          <el-tabs v-model="categoryPieKind">
            <el-tab-pane label="入库金额" name="inbound" />
            <el-tab-pane label="出库金额" name="outbound" />
            <el-tab-pane label="剩余金额" name="stock" />
          </el-tabs>
          <v-chart class="chart" :option="categoryPieOption" autoresize />
        </el-card>

        <div class="table-actions">
          <el-button type="success" @click="downloadCategory">下载</el-button>
        </div>
        <el-table :data="categoryRows" v-loading="loadingCategory" border stripe style="width: 100%;">
          <el-table-column prop="category_major" label="物料大类" width="180" />
          <el-table-column prop="inbound_qty" label="总入库数量" width="110" />
          <el-table-column prop="inbound_amount_cny" label="总入库金额(CNY)" width="140" />
          <el-table-column prop="outbound_qty" label="总出库数量" width="110" />
          <el-table-column prop="outbound_amount_cny" label="总出库金额(CNY)" width="140" />
          <el-table-column prop="stock_qty" label="剩余库存数量" width="120" />
          <el-table-column prop="stock_amount_cny" label="剩余库存金额(CNY)" width="150" />
          <el-table-column prop="transit_qty" label="在途数量" width="90" />
          <el-table-column prop="transit_amount_cny" label="在途金额(CNY)" width="130" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="车型金额（车型+合同号）" name="vehicle">
        <el-card shadow="hover" class="chart-card" v-loading="loadingVehiclePie">
          <template #header>车型金额占比</template>
          <el-tabs v-model="vehiclePieKind">
            <el-tab-pane label="入库金额" name="inbound" />
            <el-tab-pane label="出库金额" name="outbound" />
            <el-tab-pane label="剩余金额" name="stock" />
          </el-tabs>
          <v-chart class="chart" :option="vehiclePieOption" autoresize />
        </el-card>

        <div class="table-actions">
          <el-button type="success" @click="downloadVehicle">下载</el-button>
        </div>
        <el-table :data="vehiclePivotRows" v-loading="loadingVehicle" border stripe style="width: 100%;">
          <el-table-column prop="contract_no" label="合同号" width="160" fixed />
          <el-table-column v-for="v in vehicleColumns" :key="v.id" :label="v.name" min-width="360">
            <el-table-column :prop="`${v.id}_inbound_amount_cny`" label="入库金额(CNY)" width="120" />
            <el-table-column :prop="`${v.id}_outbound_amount_cny`" label="出库金额(CNY)" width="120" />
            <el-table-column :prop="`${v.id}_stock_amount_cny`" label="剩余金额(CNY)" width="120" />
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="出库汇总（按年月×车型）" name="outbound-summary">
        <el-card shadow="hover" class="chart-card" v-loading="loadingOutboundMonth">
          <template #header>出库金额（月度）</template>
          <v-chart class="chart chart-tall" :option="outboundMonthBarOption" autoresize />
        </el-card>

        <div class="table-actions">
          <el-button type="success" @click="downloadOutboundSummary">下载</el-button>
        </div>
        <el-table :data="outboundSummaryRows" v-loading="loadingOutboundSummary" border stripe style="width: 100%;">
          <el-table-column prop="month" label="年月" width="120" fixed />
          <el-table-column v-for="v in outboundSummaryColumns" :key="v.id" :prop="`${v.id}_outbound_amount_cny`" :label="v.name" width="140" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="出库统计（按日期明细）" name="outbound-detail">
        <div class="detail-actions">
          <el-date-picker
            v-model="outboundDetailRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
          <el-button type="primary" @click="fetchOutboundDetail">查询</el-button>
          <el-button type="success" @click="downloadOutboundDetail">下载</el-button>
        </div>
        <el-table :data="outboundDetailRows" v-loading="loadingOutboundDetail" border stripe style="width: 100%;">
          <el-table-column prop="outbound_time" label="出库时间" width="180">
            <template #default="scope">
              {{ scope.row.outbound_time ? new Date(scope.row.outbound_time).toLocaleString() : '' }}
            </template>
          </el-table-column>
          <el-table-column prop="group_no" label="出库单号" width="180" />
          <el-table-column prop="order_no" label="行单号" width="190" />
          <el-table-column prop="customer" label="客户" width="120" />
          <el-table-column prop="receiver" label="领用人" width="100" />
          <el-table-column prop="vehicle_model" label="车型" width="130" />
          <el-table-column prop="contract_no" label="合同号" width="140" />
          <el-table-column prop="material_code" label="物料编码" width="120" />
          <el-table-column prop="material_description" label="物料描述" min-width="180" show-overflow-tooltip />
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="sale_price" label="销售价" width="100" />
          <el-table-column prop="currency" label="币种" width="80" />
          <el-table-column prop="amount_cny" label="出库金额(CNY)" width="140" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="库龄分析" name="stock-age">
        <el-card shadow="hover" class="chart-card" v-loading="loadingStockAge">
          <template #header>当前库存库龄分布（按入库时间）</template>
          <v-chart class="chart" :option="stockAgeBarOption" autoresize />
        </el-card>

        <el-table :data="stockAgeRows" v-loading="loadingStockAge" border stripe style="width: 100%; margin-top: 12px;">
          <el-table-column prop="bucket" label="库龄区间" width="140" />
          <el-table-column prop="stock_qty" label="当前库存数量" width="140" />
          <el-table-column prop="stock_amount_cny" label="当前库存金额(CNY)" width="180" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import request from '../utils/request'
import { downloadFile } from '../utils/download'

use([CanvasRenderer, PieChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const activeTab = ref('contract')

const filters = reactive({
  usd_to_cny: 7.2
})

const loadingKpi = ref(false)
const kpiMode = ref<'week' | 'month'>('week')
const kpiModeLabel = computed(() => (kpiMode.value === 'week' ? '本周' : '本月'))

const kpi = reactive({
  stock_amount_cny: 0,
  transit_amount_cny: 0,
  total_stock_amount_cny: 0,
  week_outbound_qty: 0,
  week_outbound_amount_cny: 0,
  month_outbound_qty: 0,
  month_outbound_amount_cny: 0
})

const loadingContract = ref(false)
const loadingCategory = ref(false)
const loadingVehicle = ref(false)
const loadingOutboundSummary = ref(false)
const loadingOutboundDetail = ref(false)

const loadingStockTotal = ref(false)
const loadingStockContractTotal = ref(false)
const loadingStockTopn = ref(false)
const loadingCategoryPie = ref(false)
const loadingVehiclePie = ref(false)
const loadingOutboundMonth = ref(false)

const contractRows = ref<any[]>([])
const categoryRows = ref<any[]>([])
const vehicleColumns = ref<any[]>([])
const vehiclePivotRows = ref<any[]>([])
const outboundSummaryColumns = ref<any[]>([])
const outboundSummaryRows = ref<any[]>([])
const outboundDetailRange = ref<string[]>([new Date().toISOString().slice(0, 10), new Date().toISOString().slice(0, 10)])
const outboundDetailRows = ref<any[]>([])

const contractOptions = ref<string[]>([])
const selectedContract = ref<string>('')
const stockReconcile = reactive({
  inbound_amount_cny: 0,
  outbound_amount_cny: 0,
  stock_amount_cny: 0,
  borrow_outstanding_amount_cny: 0,
  check_net_amount_cny: 0,
  reconcile_delta_cny: 0
})
const stockContractReconcile = reactive({
  inbound_amount_cny: 0,
  outbound_amount_cny: 0,
  stock_amount_cny: 0,
  borrow_outstanding_amount_cny: 0,
  check_net_amount_cny: 0,
  reconcile_delta_cny: 0
})
const stockTopn = ref<any[]>([])
const categoryPieData = reactive<{ inbound: any[]; outbound: any[]; stock: any[] }>({ inbound: [], outbound: [], stock: [] })
const vehiclePieData = reactive<{ inbound: any[]; outbound: any[]; stock: any[] }>({ inbound: [], outbound: [], stock: [] })
const categoryPieKind = ref<'inbound' | 'outbound' | 'stock'>('stock')
const vehiclePieKind = ref<'inbound' | 'outbound' | 'stock'>('stock')
const outboundMonth = ref<any[]>([])

const loadingStockAge = ref(false)
const stockAgeRows = ref<any[]>([])

const buildQuery = () => {
  const params: string[] = []
  if (filters.usd_to_cny !== null && filters.usd_to_cny !== undefined) {
    params.push(`usd_to_cny=${encodeURIComponent(String(filters.usd_to_cny))}`)
  }
  return params.length ? `?${params.join('&')}` : ''
}

const formatAmount = (v: any) => {
  const n = Number(v || 0)
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatInt = (v: any) => {
  const n = Number(v || 0)
  return n.toLocaleString()
}

const fetchKpi = async () => {
  loadingKpi.value = true
  try {
    const res: any = await request.get(`/dashboard/kpi${buildQuery()}`)
    kpi.stock_amount_cny = res.stock_amount_cny || 0
    kpi.transit_amount_cny = res.transit_amount_cny || 0
    kpi.total_stock_amount_cny = res.total_stock_amount_cny || 0
    kpi.week_outbound_qty = res.week_outbound_qty || 0
    kpi.week_outbound_amount_cny = res.week_outbound_amount_cny || 0
    kpi.month_outbound_qty = res.month_outbound_qty || 0
    kpi.month_outbound_amount_cny = res.month_outbound_amount_cny || 0
  } finally {
    loadingKpi.value = false
  }
}

const limitPieItems = (items: any[], top: number = 12) => {
  const arr = (items || []).slice()
  arr.sort((a, b) => Number(b.value || 0) - Number(a.value || 0))
  const head = arr.slice(0, top)
  const tail = arr.slice(top)
  if (!tail.length) return head
  const other = tail.reduce((s, x) => s + Number(x.value || 0), 0)
  return [...head, { name: '其他', value: Number(other.toFixed(2)) }]
}

const buildReconcileBarOption = (data: any) => {
  const inbound = Number(data.inbound_amount_cny || 0)
  const outbound = Number(data.outbound_amount_cny || 0)
  const stock = Number(data.stock_amount_cny || 0)
  const borrow = Number(data.borrow_outstanding_amount_cny || 0)
  const checkNet = Number(data.check_net_amount_cny || 0)
  const delta = Number(data.reconcile_delta_cny || 0)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: ['累计入库', '累计出库', '当前库存', '借用未还', '盘点净差', '对账差额'] },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      data: [inbound, outbound, stock, borrow, checkNet, delta]
    }]
  }
}

const stockReconcileBarOption = computed(() => buildReconcileBarOption(stockReconcile))
const stockContractReconcileBarOption = computed(() => buildReconcileBarOption(stockContractReconcile))

const stockTopnBarOption = computed(() => {
  const rows = stockTopn.value || []
  const x = rows.map((r: any) => r.contract_no)
  const inbound = rows.map((r: any) => Number(r.inbound_amount_cny || 0))
  const outbound = rows.map((r: any) => Number(r.outbound_amount_cny || 0))
  const stock = rows.map((r: any) => Number(r.stock_amount_cny || 0))
  return {
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 50, right: 20, top: 40, bottom: 80 },
    xAxis: {
      type: 'category',
      data: x,
      axisLabel: {
        rotate: 30,
        formatter: (v: string) => (v && v.length > 10 ? `${v.slice(0, 10)}…` : v)
      }
    },
    yAxis: { type: 'value' },
    series: [
      { name: '入库金额', type: 'bar', data: inbound },
      { name: '出库金额', type: 'bar', data: outbound },
      { name: '剩余金额', type: 'bar', data: stock }
    ]
  }
})

const categoryPieOption = computed(() => {
  const items = limitPieItems(categoryPieData[categoryPieKind.value] || [])
  return {
    tooltip: { trigger: 'item' },
    legend: { top: 0 },
    series: [{ type: 'pie', radius: ['35%', '70%'], label: { formatter: '{b}\n{d}%' }, data: items }]
  }
})

const vehiclePieOption = computed(() => {
  const items = limitPieItems(vehiclePieData[vehiclePieKind.value] || [])
  return {
    tooltip: { trigger: 'item' },
    legend: { top: 0 },
    series: [{ type: 'pie', radius: ['35%', '70%'], label: { formatter: '{b}\n{d}%' }, data: items }]
  }
})

const outboundMonthBarOption = computed(() => {
  const rows = outboundMonth.value || []
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: rows.map((x: any) => x.month) },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: rows.map((x: any) => Number(x.outbound_amount_cny || 0)) }]
  }
})

const withSummary = (items: any[], summary: any) => {
  if (!summary) return items
  return [...items, summary]
}

const fetchContractOptions = async () => {
  const res: any = await request.get(`/dashboard/stock-amount/contracts${buildQuery()}`)
  contractOptions.value = res.items || []
}

const fetchStockReconcile = async () => {
  loadingStockTotal.value = true
  try {
    const res: any = await request.get(`/dashboard/stock-reconcile/total${buildQuery()}`)
    stockReconcile.inbound_amount_cny = res.inbound_amount_cny || 0
    stockReconcile.outbound_amount_cny = res.outbound_amount_cny || 0
    stockReconcile.stock_amount_cny = res.stock_amount_cny || 0
    stockReconcile.borrow_outstanding_amount_cny = res.borrow_outstanding_amount_cny || 0
    stockReconcile.check_net_amount_cny = res.check_net_amount_cny || 0
    stockReconcile.reconcile_delta_cny = res.reconcile_delta_cny || 0
  } finally {
    loadingStockTotal.value = false
  }
}

const fetchStockContractReconcile = async () => {
  loadingStockContractTotal.value = true
  try {
    if (!selectedContract.value) {
      stockContractReconcile.inbound_amount_cny = 0
      stockContractReconcile.outbound_amount_cny = 0
      stockContractReconcile.stock_amount_cny = 0
      stockContractReconcile.borrow_outstanding_amount_cny = 0
      stockContractReconcile.check_net_amount_cny = 0
      stockContractReconcile.reconcile_delta_cny = 0
      return
    }
    const q = `${buildQuery()}${buildQuery() ? '&' : '?'}contract_no=${encodeURIComponent(selectedContract.value)}`
    const res: any = await request.get(`/dashboard/stock-reconcile/total${q}`)
    stockContractReconcile.inbound_amount_cny = res.inbound_amount_cny || 0
    stockContractReconcile.outbound_amount_cny = res.outbound_amount_cny || 0
    stockContractReconcile.stock_amount_cny = res.stock_amount_cny || 0
    stockContractReconcile.borrow_outstanding_amount_cny = res.borrow_outstanding_amount_cny || 0
    stockContractReconcile.check_net_amount_cny = res.check_net_amount_cny || 0
    stockContractReconcile.reconcile_delta_cny = res.reconcile_delta_cny || 0
  } finally {
    loadingStockContractTotal.value = false
  }
}

const fetchStockTopn = async () => {
  loadingStockTopn.value = true
  try {
    const q = `${buildQuery()}${buildQuery() ? '&' : '?'}n=10`
    const res: any = await request.get(`/dashboard/stock-amount/topn/by-contract${q}`)
    stockTopn.value = res.items || []
  } finally {
    loadingStockTopn.value = false
  }
}

const fetchCategoryPie = async () => {
  loadingCategoryPie.value = true
  try {
    const res: any = await request.get(`/dashboard/pie/by-category${buildQuery()}`)
    categoryPieData.inbound = res.inbound || []
    categoryPieData.outbound = res.outbound || []
    categoryPieData.stock = res.stock || []
  } finally {
    loadingCategoryPie.value = false
  }
}

const fetchVehiclePie = async () => {
  loadingVehiclePie.value = true
  try {
    const res: any = await request.get(`/dashboard/pie/by-vehicle${buildQuery()}`)
    vehiclePieData.inbound = res.inbound || []
    vehiclePieData.outbound = res.outbound || []
    vehiclePieData.stock = res.stock || []
  } finally {
    loadingVehiclePie.value = false
  }
}

const fetchOutboundMonth = async () => {
  loadingOutboundMonth.value = true
  try {
    const q = `${buildQuery()}${buildQuery() ? '&' : '?'}months=12`
    const res: any = await request.get(`/dashboard/outbound-amount/by-month${q}`)
    outboundMonth.value = res.items || []
  } finally {
    loadingOutboundMonth.value = false
  }
}

const fetchContract = async () => {
  loadingContract.value = true
  try {
    const res: any = await request.get(`/dashboard/stock-amount/by-contract${buildQuery()}`)
    contractRows.value = withSummary(res.items || [], res.summary)
  } finally {
    loadingContract.value = false
  }
}

const fetchCategory = async () => {
  loadingCategory.value = true
  try {
    const res: any = await request.get(`/dashboard/stock-amount/by-category${buildQuery()}`)
    categoryRows.value = withSummary(res.items || [], res.summary)
  } finally {
    loadingCategory.value = false
  }
}

const fetchVehicle = async () => {
  loadingVehicle.value = true
  try {
    const res: any = await request.get(`/dashboard/vehicle-amount/pivot${buildQuery()}`)
    vehicleColumns.value = res.vehicles || []
    vehiclePivotRows.value = res.items || []
  } finally {
    loadingVehicle.value = false
  }
}

const fetchOutboundSummary = async () => {
  loadingOutboundSummary.value = true
  try {
    const res: any = await request.get(`/dashboard/outbound-summary/month-vehicle${buildQuery()}`)
    outboundSummaryColumns.value = res.vehicles || []
    outboundSummaryRows.value = res.items || []
  } finally {
    loadingOutboundSummary.value = false
  }
}

const fetchOutboundDetail = async () => {
  if (!outboundDetailRange.value || outboundDetailRange.value.length !== 2) return
  loadingOutboundDetail.value = true
  try {
    const q = `?start_date=${encodeURIComponent(outboundDetailRange.value[0])}&end_date=${encodeURIComponent(outboundDetailRange.value[1])}&usd_to_cny=${encodeURIComponent(String(filters.usd_to_cny))}`
    const res: any = await request.get(`/dashboard/outbound-detail${q}`)
    outboundDetailRows.value = [...(res.items || []), res.summary].filter(Boolean)
  } finally {
    loadingOutboundDetail.value = false
  }
}

const fetchStockAge = async () => {
  loadingStockAge.value = true
  try {
    const res: any = await request.get(`/dashboard/stock-age/buckets${buildQuery()}`)
    stockAgeRows.value = res.items || []
  } finally {
    loadingStockAge.value = false
  }
}

const stockAgeBarOption = computed(() => {
  const rows = stockAgeRows.value || []
  const x = rows.map((r: any) => r.bucket)
  const y = rows.map((r: any) => Number(r.stock_amount_cny || 0))
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: x },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: y }]
  }
})

const refreshAll = () => {
  fetchKpi()
  fetchContractOptions()
  fetchStockReconcile()
  fetchStockContractReconcile()
  fetchStockTopn()
  fetchCategoryPie()
  fetchVehiclePie()
  fetchOutboundMonth()
  fetchContract()
  fetchCategory()
  fetchVehicle()
  fetchOutboundSummary()
  fetchOutboundDetail()
  fetchStockAge()
}

const downloadContract = () => {
  downloadFile(`/api/v1/dashboard/export/stock-amount/by-contract${buildQuery()}`, '库存金额_按合同号.xlsx')
}

const downloadCategory = () => {
  downloadFile(`/api/v1/dashboard/export/stock-amount/by-category${buildQuery()}`, '库存金额_按物料大类.xlsx')
}

const downloadVehicle = () => {
  downloadFile(`/api/v1/dashboard/export/vehicle-amount/pivot${buildQuery()}`, '车型金额_按合同号透视.xlsx')
}

const downloadOutboundSummary = () => {
  downloadFile(`/api/v1/dashboard/export/outbound-summary/month-vehicle${buildQuery()}`, '出库汇总_按年月车型.xlsx')
}

const downloadOutboundDetail = () => {
  if (!outboundDetailRange.value || outboundDetailRange.value.length !== 2) return
  const q = `?start_date=${encodeURIComponent(outboundDetailRange.value[0])}&end_date=${encodeURIComponent(outboundDetailRange.value[1])}&usd_to_cny=${encodeURIComponent(String(filters.usd_to_cny))}`
  downloadFile(`/api/v1/dashboard/export/outbound-detail${q}`, `出库明细_${outboundDetailRange.value[0]}_${outboundDetailRange.value[1]}.xlsx`)
}

onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}
.filters {
  margin-bottom: 12px;
}
.kpi-row {
  margin-bottom: 10px;
}
.kpi-card :deep(.el-card__header) {
  padding: 10px 12px;
}
.kpi-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  text-align: center;
  padding: 6px 0;
}
.kpi-mode {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}
.table-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}
.detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-bottom: 10px;
}
.chart-row {
  margin-bottom: 12px;
}
.chart-card {
  margin-bottom: 12px;
}
.chart-filter {
  margin-bottom: 10px;
}
.chart {
  width: 100%;
  height: 320px;
}
.chart-tall {
  height: 380px;
}
</style>
