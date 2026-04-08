import { createRouter, createWebHashHistory } from 'vue-router'
import { useStore } from '@/store/index'

const routes = [
  {
    path: '/',
    redirect: '/home',
  },
  {
    path: '/login',
    meta: {
      title: '登录',
    },
    component: () => import('../view/Login.vue'),
  },

  {
    path: '/home',
    name: '主页',
    redirect: '/home/map',
    meta: {
      title: '主页',
    },
    component: () => import('../view/Home.vue'),
    children: [
      {
        path: 'linshi',
        meta: {
          title: '目标产量',
        },
        component: () => import('../view/table.vue'),
      },
      {
        path: 'alogrtable',
        meta: {
          title: 'alogrtable',
        },
        component: () => import('@/view/alogrTable.vue'),
      },
      {
        path: 'linshi',
        meta: {
          title: '目标产量',
        },
        component: () => import('../view/table.vue'),
      },
      {
        path: 'map',
        meta: {
          title: '地图',
        },
        component: () => import('@/view/Map.vue'),
      },
      {
        path: 'table',
        meta: {
          title: '目标产量',
        },
        component: () => import('../view/main.vue'),
      },
      {
        path: 'field',
        meta: {
          title: '目标产量',
        },
        component: () => import('./algor/field.vue'),
      },
      {
        path: 'photosy',
        meta: {
          title: '冠层光合模拟',
        },
        component: () => import('./algor/photosy.vue'),
      },
      {
        path: 'soilwater',
        meta: {
          title: '土壤水分',
        },
        component: () => import('./algor/soilWater.vue'),
      },
      {
        path: 'shine',
        meta: {
          title: '玉米生长模拟',
        },
        component: () => import('./algor/fspm.vue'),
      },
             {
         path: 'production',
         meta: {
          title: '玉米产量预测',
         },
         component: () => import('./algor/production.vue'),
       },
             {
         path: 'maizeEstimate',
         meta: {
          title: '玉米产量预测区域版（API1）',
         },
         component: () => import('./algor/maizeEstimate.vue'),
       },
             {
         path: 'scym',
         meta: {
          title: '玉米产量预测区域版（API2）',
         },
         component: () => import('./algor/scym.vue'),
       },
            {
         path: 'gnah',
         meta: {
          title: '玉米产量预测区域版（GNAH）',
         },
         component: () => import('./algor/gnah.vue'),
       },
             {
         path: 'lai',
         meta: {
           title: 'LAI同化算法',
         },
         component: () => import('./algor/lai.vue'),
       },

       {
         path: 'algor',
         meta: {
           title: '算法选择',
         },
         component: () => import('./algor/algor.vue'),
       },
    ],
    // children: [
    //     {
    //         path: '/index',
    //         meta: {
    //             title: '首页'
    //         },
    //         component: () => import('../view/Main.vue')
    //     },
    //     {
    //         path: '/base',
    //         meta: {
    //             title: '基础表'
    //         },
    //         component: () => import('../view/Main.vue')
    //     },
    //     {
    //         path: '/user/list',
    //         meta: {
    //             title: '用户管理'
    //         },
    //         component: () => import('../view/user/Index.vue'),
    //     },
    //     {
    //         path: '/user/detail',
    //         meta: {
    //             title: '用户详情'
    //         },
    //         component: () => import('../view/user/Detail.vue'),
    //     },
    // ]
  },
]
const router = createRouter({
  history: createWebHashHistory(),
  routes,
})
// 挂载路由导航守卫：to表示将要访问的路径，from表示从哪里来，next是下一个要做的操作
router.beforeEach((to, from, next) => {
  // 修改页面 title
  if (to.meta.title) {
    document.title = '玉米生产力预测平台 - ' + to.meta.title
  }
  // 直接放行所有路由，跳过登录验证
  next()
})

// 导出路由
export default router
