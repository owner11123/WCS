<template>
  <div class="print-page">
    <div class="no-print toolbar">
      <el-button type="primary" @click="doPrint">打印</el-button>
      <el-button @click="openSettings = !openSettings">模板设置</el-button>
    </div>

    <div v-if="openSettings" class="no-print settings">
      <el-form label-width="140px">
        <el-form-item label="标题">
          <el-input v-model="cfg.title" />
        </el-form-item>
        <el-form-item label="品牌（固定值）">
          <el-input v-model="cfg.brand" />
        </el-form-item>
        <el-form-item label="单位（固定值）">
          <el-input v-model="cfg.unit" />
        </el-form-item>
        <el-form-item label="左侧字段名称">
          <el-input v-model="cfg.leftLabel" />
        </el-form-item>
        <el-form-item label="右侧字段名称">
          <el-input v-model="cfg.rightLabel" />
        </el-form-item>
        <el-form-item label="显示 Logo">
          <el-switch v-model="cfg.showLogo" />
        </el-form-item>
        <el-form-item label="Logo 图片地址">
          <el-input v-model="cfg.logoUrl" placeholder="/src/assets/xxx.png 或 http(s)://..." />
        </el-form-item>
      </el-form>
      <div style="display:flex;gap:10px;">
        <el-button type="primary" @click="saveCfg">保存</el-button>
        <el-button @click="resetCfg">恢复默认</el-button>
      </div>
    </div>

    <div class="sheet" v-loading="loading">
      <div class="header">
        <div class="logo" v-if="cfg.showLogo">
          <img v-if="cfg.logoUrl" :src="cfg.logoUrl" alt="logo" />
        </div>
        <div class="title">{{ cfg.title }}</div>
      </div>

      <div class="meta">
        <div class="meta-left">{{ cfg.leftLabel }}：{{ data?.header?.customer || '' }}</div>
        <div class="meta-right">{{ cfg.rightLabel }}：{{ formatDate(data?.header?.outbound_time) }}</div>
      </div>

      <div class="meta-2">
        <div class="meta-2-left">单据编号：{{ data?.header?.order_no || '' }}</div>
      </div>

      <table class="table">
        <thead>
          <tr>
            <th style="width:60px;">序号</th>
            <th style="width:140px;">物料编码</th>
            <th style="width:240px;">物资名称</th>
            <th style="width:160px;">型号/备件号</th>
            <th style="width:90px;">品牌</th>
            <th style="width:80px;">单位</th>
            <th style="width:120px;">申请数量</th>
            <th style="width:140px;">使用设备</th>
            <th>备注</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.seq">
            <td class="center">{{ row.seq }}</td>
            <td>{{ row.material_model || '' }}</td>
            <td>{{ row.material_description || '' }}</td>
            <td>{{ row.material_code || '' }}</td>
            <td class="center">{{ cfg.brand }}</td>
            <td class="center">{{ cfg.unit }}</td>
            <td class="center">{{ row.quantity }}</td>
            <td class="center">{{ row.vehicle_model || '' }}</td>
            <td>{{ row.contract_no || '' }}</td>
          </tr>
          <tr v-for="i in fillerCount" :key="'f-'+i">
            <td>&nbsp;</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td>
          </tr>
        </tbody>
      </table>

      <div class="footer">
        <div>领用人：</div>
        <div>仓储复核：</div>
        <div>发货人：{{ data?.header?.operator_name || '' }} {{ formatDate(data?.header?.outbound_time) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import request from '../../utils/request'

type PrintCfg = {
  title: string
  brand: string
  unit: string
  leftLabel: string
  rightLabel: string
  showLogo: boolean
  logoUrl: string
}

const DEFAULT_CFG: PrintCfg = {
  title: '赢联盟西芒杜矿山项目公司寄售件物资领用申请单',
  brand: '徐工',
  unit: '个',
  leftLabel: '申领部门/单位',
  rightLabel: '领用日期',
  showLogo: false,
  logoUrl: ''
}

const route = useRoute()
const loading = ref(false)
const data = ref<any>(null)
const openSettings = ref(false)

const cfg = ref<PrintCfg>({ ...DEFAULT_CFG })

const cfgKey = 'wcs.print.outbound.cfg'

const loadCfg = () => {
  try {
    const raw = localStorage.getItem(cfgKey)
    if (!raw) return
    const parsed = JSON.parse(raw)
    cfg.value = { ...DEFAULT_CFG, ...parsed }
  } catch {}
}

const saveCfg = () => {
  localStorage.setItem(cfgKey, JSON.stringify(cfg.value))
}

const resetCfg = () => {
  cfg.value = { ...DEFAULT_CFG }
  saveCfg()
}

const groupNo = computed(() => String(route.params.groupNo || route.query.order_no || ''))
const autoPrint = computed(() => String(route.query.auto || '') === '1')

const rows = computed(() => data.value?.items || [])
const fillerCount = computed(() => {
  const target = 10
  const n = rows.value.length || 0
  return n >= target ? 0 : target - n
})

const formatDate = (val: any) => {
  if (!val) return ''
  const d = new Date(val)
  if (Number.isNaN(d.getTime())) return ''
  return `${d.getFullYear()}.${d.getMonth() + 1}.${d.getDate()}`
}

const fetchData = async () => {
  if (!groupNo.value) return
  loading.value = true
  try {
    const res: any = await request.get(`/orders/outbound/print/${encodeURIComponent(groupNo.value)}`)
    data.value = res
  } finally {
    loading.value = false
  }
}

const doPrint = () => {
  window.print()
}

onMounted(async () => {
  loadCfg()
  await fetchData()
  if (autoPrint.value) {
    setTimeout(() => doPrint(), 300)
  }
})
</script>

<style scoped>
.print-page {
  padding: 16px;
  background: #f5f6f7;
}
.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}
.settings {
  background: #fff;
  border: 1px solid #ebeef5;
  padding: 12px;
  margin-bottom: 12px;
}
.sheet {
  width: 794px;
  min-height: 1123px;
  margin: 0 auto;
  background: #fff;
  padding: 18px 18px 12px 18px;
  color: #000;
}
.header {
  display: grid;
  grid-template-columns: 90px 1fr;
  align-items: center;
  margin-bottom: 10px;
}
.logo {
  width: 80px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.logo img {
  max-width: 80px;
  max-height: 60px;
}
.title {
  text-align: center;
  font-size: 22px;
  font-weight: 700;
}
.meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border: 2px solid #000;
  border-bottom: none;
}
.meta-left,
.meta-right {
  padding: 8px 10px;
  font-size: 16px;
}
.meta-left {
  border-right: 2px solid #000;
}
.meta-2 {
  border: 2px solid #000;
  border-top: none;
  padding: 8px 10px;
  font-size: 16px;
}
.table {
  width: 100%;
  border-collapse: collapse;
  border: 2px solid #000;
  border-top: none;
  table-layout: fixed;
  font-size: 14px;
}
.table th,
.table td {
  border: 2px solid #000;
  padding: 6px 6px;
  vertical-align: middle;
  word-break: break-all;
}
.table thead th {
  text-align: center;
  font-weight: 700;
}
.center {
  text-align: center;
}
.footer {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  border: 2px solid #000;
  border-top: none;
  padding: 10px;
  font-size: 16px;
}
@media print {
  .no-print {
    display: none !important;
  }
  .print-page {
    padding: 0;
    background: #fff;
  }
  .sheet {
    width: auto;
    min-height: auto;
    margin: 0;
    padding: 0;
  }
}
</style>

