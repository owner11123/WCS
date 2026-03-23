import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: 'Login' }
  },
  {
    path: '/outbound/print/:groupNo',
    name: 'OutboundPrint',
    component: () => import('../views/outbound/print.vue'),
    meta: { title: '打印出库单' }
  },
  {
    path: '/m',
    component: () => import('../layout/mobile.vue'),
    redirect: '/m/home',
    children: [
      {
        path: 'home',
        name: 'MobileHome',
        component: () => import('../views/mobile/Home.vue'),
        meta: { title: '手机首页' }
      },
      {
        path: 'inbound',
        name: 'MobileInbound',
        component: () => import('../views/inbound/index.vue'),
        meta: { title: '入库管理' }
      },
      {
        path: 'outbound',
        name: 'MobileOutbound',
        component: () => import('../views/outbound/index.vue'),
        meta: { title: '出库管理' }
      },
      {
        path: 'inventory',
        name: 'MobileInventory',
        component: () => import('../views/inventory/index.vue'),
        meta: { title: '实时库存' }
      },
      {
        path: 'borrow',
        name: 'MobileBorrow',
        component: () => import('../views/borrow/index.vue'),
        meta: { title: '借用管理' }
      },
      {
        path: 'movement',
        name: 'MobileStockMovement',
        component: () => import('../views/movement/index.vue'),
        meta: { title: '移库管理' }
      },
      {
        path: 'inventory-check',
        name: 'MobileInventoryCheck',
        component: () => import('../views/inventory-check/index.vue'),
        meta: { title: '盘点管理' }
      }
    ]
  },
  {
    path: '/',
    component: () => import('../layout/index.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '仪表盘', icon: 'Odometer' }
      },
      {
        path: 'materials',
        name: 'Materials',
        component: () => import('../views/materials/index.vue'),
        meta: { title: '物料管理', icon: 'Goods' }
      },
      {
        path: 'locations',
        name: 'Locations',
        component: () => import('../views/locations/index.vue'),
        meta: { title: '库位管理', icon: 'MapLocation' }
      },
      {
        path: 'inbound',
        name: 'Inbound',
        component: () => import('../views/inbound/index.vue'),
        meta: { title: '入库管理', icon: 'Download' }
      },
      {
        path: 'outbound',
        name: 'Outbound',
        component: () => import('../views/outbound/index.vue'),
        meta: { title: '出库管理', icon: 'Upload' }
      },
      {
        path: '/inventory',
        name: 'Inventory',
        component: () => import('../views/inventory/index.vue'),
        meta: { title: '实时库存' }
      },
      {
        path: '/movement',
        name: 'StockMovement',
        component: () => import('../views/movement/index.vue'),
        meta: { title: '移库管理' }
      },
      {
        path: '/inventory-check',
        name: 'InventoryCheck',
        component: () => import('../views/inventory-check/index.vue'),
        meta: { title: '盘点管理' }
      },
      {
        path: '/transit',
        name: 'TransitInventory',
        component: () => import('../views/transit/index.vue'),
        meta: { title: '在途库存' }
      },
      {
        path: '/transaction',
        name: 'Transaction',
        component: () => import('../views/transaction/index.vue'),
        meta: { title: '操作流水' }
      },
      {
        path: '/borrow',
        name: 'Borrow',
        component: () => import('../views/borrow/index.vue'),
        meta: { title: '借用管理' }
      },
      {
        path: '/system',
        name: 'System',
        component: () => import('../views/system/index.vue'),
        meta: { title: '系统管理' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    const role = localStorage.getItem('role') || ''
    if (to.path.startsWith('/system') && role !== 'admin') {
      next('/dashboard')
      return
    }
    next()
  }
})

export default router
