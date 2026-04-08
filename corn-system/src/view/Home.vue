<script setup>
import {
  onBeforeMount,
  onMounted,
  onUnmounted,
  ref,
  getCurrentInstance,
  watch,
  nextTick,
} from 'vue'
// import avatar from '../assets/img/avator.png' // 已移除用户头像显示
import { useRouter, useRoute } from 'vue-router'
import { Coin, Memo, Document, Plus } from '@element-plus/icons-vue'
import Main from './main.vue'
import { storeToRefs } from 'pinia'
import ProcessView from './ProcessView.vue'
import tableApi from '../api/table'
import fieldDialog from './table/fieldDialog.vue'
import editDataDialog from './table/editDataDialog.vue'
import bus from '../utils/EventBus.js'
import { useStore, useRemmenber, useMenuConfig } from '../store/index.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import Map from './Map.vue'
import axios from 'axios'
//import algor from './algor.vue';
// const remmenberInfo = useRemmenber() // 已移除用户信息显示
// useMenyConfig()时存储着目录结构的仓库
const useConfig = useMenuConfig()
// 使用响应式引用，避免取到非响应数据
const { menuConfig } = storeToRefs(useConfig)
const {
  fieldDialogShow,
  dataStructure,
  needPublish,
  showView,
  tableShow,
  mapShow,
  algorshow,
} = storeToRefs(useStore())
const userInfoStore = useStore()
onMounted(() => {
  console.log(dataStructure.value)
})
const router = useRouter()
const route = useRoute()
const toBeAddedDatabase = ref(null)
const toBeAddedGySet = ref(null)
const gysetName = ref('')
const gyDialogShow = ref(false)
const rnDialogShow = ref(false)
let isCollapse = ref(false)
let activePath = ref('')
const openMenus = ref(['jcb', 'jcbj', 'algorithm'])
const activeMenu = ref('')
const mainMenu = ref(null)
const selectdMenuItem = ref('')
const { proxy } = getCurrentInstance()
const showRightMenu = ref(false)
const positionX = ref(0)
const positionY = ref(0)
let curRightMenuTarget = null
const renameValue = ref('')
const searchWord = ref('')

// 面包屑导航路径
const breadcrumbPath = ref([])

// 获取菜单图标路径
const getMenuIcon = (key) => {
  // 从public目录加载图片（现在publicDir设置为'public'）
  // 图片文件已复制到public目录
  return `/${key}.png`
}

// 查找菜单项的完整路径（从一级到当前项）
function findMenuPath(item, menu = menuConfig.value) {
  // 推断目标层级：
  // - 如果有 type 属性且是 'table' 或 'geojson' 或 'image'，通常是三级菜单
  // - 如果有 type 属性且是 'algor'，通常是二级菜单
  // - 如果有 childrend 且长度 > 0，是一级菜单
  // - 否则是二级菜单
  const isThirdLevel = item.type && ['table', 'geojson', 'image'].includes(item.type)
  const isSecondLevel = item.level === 2 || (item.type === 'algor') || (!isThirdLevel && !item.childrend)
  const targetLevel = item.level || (isThirdLevel ? 3 : (isSecondLevel ? 2 : 1))
  
  for (const menuItem of menu) {
    // 如果是一级菜单匹配
    if (menuItem.key === item.key && (targetLevel === 1 || (!item.type && !item.childrend))) {
      return [{ title: menuItem.title, level: 1 }]
    }
    
    // 如果有子菜单，递归查找
    if (menuItem.childrend && menuItem.childrend.length > 0) {
      // 优先查找三级菜单（如果 item 有 type 属性且是 table/geojson/image）
      if (isThirdLevel || targetLevel === 3) {
        for (const child of menuItem.childrend) {
          if (child.childrend && child.childrend.length > 0) {
            for (const grandChild of child.childrend) {
              // 三级菜单匹配：检查 key（如果 level 不明确，通过 type 判断）
              if (grandChild.key === item.key && (grandChild.level === 3 || grandChild.type)) {
                return [
                  { title: menuItem.title, level: 1 },
                  { title: child.title, level: 2 },
                  { title: grandChild.title, level: 3 }
                ]
              }
            }
          }
        }
      }
      
      // 再查找二级菜单（包括 type: 'algor' 的情况）
      if (isSecondLevel || targetLevel === 2 || (item.childrend && item.childrend.length === 0)) {
        for (const child of menuItem.childrend) {
          // 二级菜单匹配：检查 key 和 level，允许 type: 'algor'
          if (child.key === item.key && child.level === 2) {
            return [
              { title: menuItem.title, level: 1 },
              { title: child.title, level: 2 }
            ]
          }
        }
      }
    }
  }
  return []
}

// 更新面包屑路径
function updateBreadcrumb(item) {
  breadcrumbPath.value = findMenuPath(item)
}

// 挂载 DOM 之前
onBeforeMount(() => {
  activePath.value = sessionStorage.getItem('activePath')
    ? sessionStorage.getItem('activePath')
    : '/home'
  // 防止持久化缓存导致算法子菜单为空，启动时兜底注入
  const algorithmMenu = menuConfig.value.find((item) => item.key === 'algorithm')
  if (algorithmMenu && (!algorithmMenu.childrend || algorithmMenu.childrend.length === 0)) {
    algorithmMenu.childrend = [
      { title: 'LAI同化算法', key: 'lai', level: 2, type: 'algor' },
      { title: '玉米生长模拟', key: 'shine', level: 2, type: 'algor' },
      { title: '玉米产量预测', key: 'production', level: 2, type: 'algor' },
      { title: '玉米产量预测区域版（API1）', key: 'maizeEstimate', level: 2, type: 'algor' },
      { title: '玉米产量预测区域版（GNAH）', key: 'gnah', level: 2, type: 'algor' },
    ]
  } else if (algorithmMenu && algorithmMenu.childrend) {
    // 确保文案同步
    const prod = algorithmMenu.childrend.find((c) => c.key === 'production')
    if (prod) prod.title = '玉米产量预测'
    const maizeEst = algorithmMenu.childrend.find((c) => c.key === 'maizeEstimate')
    if (maizeEst) maizeEst.title = '玉米产量预测区域版（API1）'
    const gnah = algorithmMenu.childrend.find((c) => c.key === 'gnah')
    if (gnah) gnah.title = '玉米产量预测区域版（GNAH）'
  }
  initData()
})
onMounted(() => {
  // window.addEventListener('beforeunload', showConfirmation);
})
onUnmounted(() => {
  window.removeEventListener('beforeunload', showConfirmation)
})

watch(dataStructure, () => {
  needPublish.value = true
})

// 监听路由变化，更新面包屑
watch(() => route.path, (newPath) => {
  // 根据路由路径查找对应的菜单项
  if (newPath === '/home/lai') {
    selectdMenuItem.value = 'lai'
    updateBreadcrumb({ key: 'lai', level: 2, type: 'algor' })
  } else if (newPath === '/home/shine') {
    selectdMenuItem.value = 'shine'
    updateBreadcrumb({ key: 'shine', level: 2, type: 'algor' })
  } else if (newPath === '/home/production') {
    selectdMenuItem.value = 'production'
    updateBreadcrumb({ key: 'production', level: 2, type: 'algor' })
  } else if (newPath === '/home/maizeEstimate') {
    selectdMenuItem.value = 'maizeEstimate'
    updateBreadcrumb({ key: 'maizeEstimate', level: 2, type: 'algor' })
  } else if (newPath === '/home/scym') {
    selectdMenuItem.value = 'scym'
    updateBreadcrumb({ key: 'scym', level: 2, type: 'algor' })
  } else if (newPath === '/home/gnah') {
    selectdMenuItem.value = 'gnah'
    updateBreadcrumb({ key: 'gnah', level: 2, type: 'algor' })
  } else if (newPath === '/home/algor') {
    selectdMenuItem.value = 'algorithm'
    updateBreadcrumb({ key: 'algorithm', level: 1 })
  } else if (newPath === '/home/map') {
    // 地图页面显示"首页"
    breadcrumbPath.value = [{ title: '首页', level: 1 }]
  }
}, { immediate: true })

// 退出系统逻辑已移除

const showConfirmation = (event) => {
  event.preventDefault() // 阻止默认行为
  event.returnValue = '您有未保存的更改，确定要离开吗？'
}

function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    var r = (Math.random() * 16) | 0
    var v = c === 'x' ? r : (r & 3) | 8
    return v.toString(16)
  })
}

async function initData() {
  //    const res = await tableApi.all();
  //    dataStructure.value = res.data.data;
  //    changeTable('jcb', 'jcbj', 'gyfl');
}
//展示不同层次数据逻辑
function showData(item) {
  // 更新面包屑路径
  updateBreadcrumb(item)
  
  if (item.type === 'table') {
    //通过事件总线来向linsh.vue传递要发送请求的数据的提示
    selectdMenuItem.value = item.key
    useConfig.findParentTitle(item.title)

    // 检查是否是基础数据分类
    const categoryMapping = {
      'climate': '气象数据',
      'soil': '土壤数据',
      // 其他分类直接使用英文，不翻译
      'fertilization': 'fertilization',
      'future': 'future',
      'irrigation': 'irrigation',
      'multi_site': 'multi_site',
      'nitrogen_limited': 'nitrogen_limited',
      'potential_bj': 'potential_bj',
      'potential_fz': 'potential_fz',
      'sowing': 'sowing',
      'variety': 'variety',
      'water_limited': 'water_limited',
      'water_limited_fz': 'water_limited_fz',
      '2023': '2023'
    }
    
    // 特殊映射 - 处理菜单配置中的特殊命名
    const specialMapping = {
      'Soil': 'soil',
      'climate': 'climate',
      'fertilization': 'fertilization',
      'future': 'future',
      'irrigation': 'irrigation',
      'multi_site_fertilizer': 'multi_site',
      'nitrogen_limited_fertilizer': 'nitrogen_limited',
      'potential_bj_fertilizer': 'potential_bj',
      'potential_fz_fertilizer': 'potential_fz',
      'sowing': 'sowing',
      'variety': 'variety',
      // water_limited_fz 独立为一个分类
      'water_limited_fz': 'water_limited_fz',
      '2023数据': '2023'
    }
    
    // 查找对应的分类 - 修复匹配逻辑
    let category = ''
    
    // 首先检查特殊映射
    if (specialMapping[item.key]) {
      category = specialMapping[item.key]
    } else if (specialMapping[item.title]) {
      category = specialMapping[item.title]
    } else if (categoryMapping[item.key]) {
      category = item.key
    } else {
      // 然后检查item.title是否匹配
      for (const [key, value] of Object.entries(categoryMapping)) {
        if (value === item.title) {
          category = key
          break
        }
      }
    }
    
    // 调试信息
    console.log('点击的数据项:', item)
    console.log('匹配到的分类:', category)
    
    // 通过事件总线传递数据，包含分类信息
    bus.emit('showtable', {
      table: {
        fields: [],
        name: item.title,
        dataItems: []
      },
      category: category
    })
    
    tableShow.value = true
    mapShow.value = false

    // 跳转到表格页面，传递分类名称
    const categoryName = categoryMapping[category] || item.title
    router.push({ path: '/home/table', query: { name: categoryName, category: category } })
  } else if (item.type === 'geojson') {
    selectdMenuItem.value = item.key
    showGeoJson(item)
    router.push('/home/map')
  } else if (item.type === 'image') {
    selectdMenuItem.value = item.key
    showImageLayer(item)
  } else if (item.level === 1 && item.key === 'algorithm') {
    selectdMenuItem.value = item.key
    mapShow.value = true
    showalgor()
    router.push('/home/algor')
  } else if (item.level === 2 && item.type === 'algor') {
    selectdMenuItem.value = item.key
    tableShow.value = false
    mapShow.value = false
    algorshow.value = false
    if (item.key === 'lai') {
      router.push('/home/lai')
    } else if (item.key === 'shine') {
      router.push('/home/shine')
    } else if (item.key === 'production') {
      router.push('/home/production')
    } else if (item.key === 'maizeEstimate') {
      router.push('/home/maizeEstimate')
    } else if (item.key === 'scym') {
      router.push('/home/scym')
    } else if (item.key === 'gnah') {
      router.push('/home/gnah')
    } else {
      router.push('/home/algor')
    }
  } /* else if (item.level === 3 && item.type === "subject") {
  } */
} //显示算法右边页面
function showalgor() {
  bus.emit('showalgor')
}
function homeToAlgorShowTable(item) {
  bus.emit('homeToAlgorShowTable', item)
}

function showTable(item) {
  const key = item.key
  axios
    .get(`./data/BaseData/${key}.json`)
    .then((response) => {
      const data = response.data
      if (data.length < 1) {
        return
      }
      const first = data[0]
      const fields = []
      for (let i = 0; i < first.length; i++) {
        fields.push(i.toString())
      }
      bus.emit('showtable', {
        table: {
          fields,
          name: key,
          dataItems: data,
        },
      })
    })
    .catch((error) => {
      console.error('Error fetching the JSON file:', error)
    })
}

function showGeoJson(item) {
  tableShow.value = false
  mapShow.value = true
  const key = item.key
  axios
    .get(`/data/geojson/${key}.json`)
    .then((response) => {
      const data = response.data

      bus.emit('showMapData', data)
    })
    .catch((error) => {
      console.error('Error fetching the JSON file:', error)
    })
}

function showImageLayer(item) {
  item.checked = !item.checked
  tableShow.value = false
  mapShow.value = true
  console.log(1)

  bus.emit('showImageLayer', item)
}

function createdField(data) {
  const { fields, name } = data
  const result = findGySet(toBeAddedGySet.value)
  if (!result) {
    return
  }
  const { database, gy } = result
  const tables = gy.tables
  const repeat = tables.find((t) => {
    return t.name === name
  })
  if (repeat) {
    ElMessage({
      type: 'error',
      message: '表名已存在，请重新创建！',
    })
    return
  }
  const table = {
    name,
    key: uuidv4(),
    fields,
    dataItems: [],
  }
  tables.push(table)
  bus.off('createdfield', createdField)
  proxy.$refs.mainMenu.open(database.key)
  ElMessage({
    type: 'success',
    message: '创建数据表成功',
  })
}

function findGySet(gyKey) {
  const dst = dataStructure.value
  for (let i = 0; i < dst.length; i++) {
    const db = dst[i]
    const gyset = db.gySet
    for (let j = 0; j < gyset.length; j++) {
      if (gyset[j].key === gyKey) {
        return { database: db, gy: gyset[j] }
      }
    }
  }
}

function addTable(gysetKey) {
  toBeAddedGySet.value = gysetKey
  fieldDialogShow.value = true
  bus.on('createdfield', createdField)
}

function deleteTable(databaseKey, gysetKey, tableKey) {
  ElMessageBox.confirm('确认删除该数据表？', '删除提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      const database = dataStructure.value.find((db) => {
        return db.key === databaseKey
      })
      const gyset = database.gySet.find((gy) => {
        return gy.key === gysetKey
      })
      const table = gyset.tables.find((tb) => {
        return tb.key === tableKey
      })
      const index = gyset.tables.indexOf(table)
      if (index > -1) {
        gyset.tables.splice(index, 1)
      }
      ElMessage({
        type: 'success',
        message: '删除成功',
      })
    })
    .catch(() => {
      ElMessage({
        type: 'info',
        message: '取消删除',
      })
    })
}

function addGySet(key) {
  toBeAddedDatabase.value = key
  gyDialogShow.value = true
}

function changeTable(databaseKey, gysetKey, tableKey) {
  selectdMenuItem.value = tableKey
  const database = dataStructure.value.find((d) => {
    return d.key === databaseKey
  })
  const gyset = database.gySet.find((gy) => {
    return gy.key === gysetKey
  })
  const table = gyset.tables.find((tb) => {
    return tb.key === tableKey
  })
  bus.emit('showtable', { table })
}

async function publish() {
  if (!dataStructure.value || !dataStructure.value.length) {
    return
  }
  const res = await tableApi.commitAll({
    data: dataStructure.value,
  })
  if (res.data.status === 200) {
    ElMessage({
      type: 'success',
      message: '发布成功',
    })
    needPublish.value = false
  }
}

function close() {}

function updateInput(e) {
  gysetName.value = e
}

function updateRNInput(e) {
  renameValue.value = e
}

function deleteGySet(databaseKey, gysetKey) {
  ElMessageBox.confirm('确认删除该工艺及其所有数据表吗？', '删除提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      const database = dataStructure.value.find((d) => {
        return d.key === databaseKey
      })
      const gyset = database.gySet.find((gy) => {
        return gy.key === gysetKey
      })
      const index = database.gySet.indexOf(gyset)
      if (index > -1) {
        database.gySet.splice(index, 1)
      }
      ElMessage({
        type: 'success',
        message: '删除成功',
      })
    })
    .catch(() => {
      ElMessage({
        type: 'info',
        message: '取消删除',
      })
    })
}

function onContextGYMenu(e, gyset, database) {
  gyset._dbKey = database.key
  onContextMenu(e, gyset)
}

function onContextDBMenu(e, table, gyset, database) {
  table._gykey = gyset.key
  table._dbkey = database.key
  onContextMenu(e, table)
}

function onContextMenu(e, item) {
  e.preventDefault()
  showRightMenu.value = true
  positionX.value = e.x
  positionY.value = e.y
  curRightMenuTarget = null
  curRightMenuTarget = item
}

function handleMenuItem(task) {
  const curItem = curRightMenuTarget
  switch (task) {
    case 'add':
      if (curItem.type === 'gyset') {
        addTable(curItem.key)
      }
      break
    case 'delete':
      if (curItem.type === 'gyset') {
        deleteGySet(curItem._dbKey, curItem.key)
      } else {
        deleteTable(curItem._dbKey, curItem._gykey, curItem.key)
      }
      break
    case 'view':
      // if (curItem.type === 'datatable') {
      //     changeTable(curItem._dbKey, curItem._gykey, curItem.key);
      // }
      bus.emit('showView')
      break
    case 'rename':
      rnDialogShow.value = true
      renameValue.value = curItem.name
      break
    default:
      break
  }
  showRightMenu.value = false
}

function confirmRename() {
  const curItem = curRightMenuTarget
  curItem.name = renameValue.value
  rnDialogShow.value = false
}
function cancelRename() {
  rnDialogShow.value = false
}
document.addEventListener('mousedown', (e) => {
  showRightMenu.value = false
})
//监听algor中的algorToHome函数
bus.on('algorToHome', (data) => {
  if (menuConfig.value[1]?.childrend) {
    // 先查找是否已存在相同的 key，如果存在则删除
    const index = menuConfig.value[1].childrend.findIndex(
      (item) => item.key === data.key,
    )
    if (index !== -1) {
      // 删除重复项
      menuConfig.value[1].childrend.splice(index, 1)
    }

    // 添加新的数据项
    menuConfig.value[1].childrend.push(data)
  }
})

//点击+号新增数据模块

const isAddShow = ref(false)
const clickPlus = (e) => {
  console.log(e)

  e.stopPropagation()
  console.log(isAddShow.value)
  isAddShow.value = true
}

const excelInput = ref(null) // 通过 ref 来引用文件输入框
const selectedFileName = ref(null)
// 用于存储上传文件对象（中转）
const file = ref('')
// 模拟点击文件选择框
const handleFileChange = (e) => {
  file.value = e.target.files[0]
  console.log(file)

  if (file) {
    selectedFileName.value = file.value.name // 更新文件名
  }
}
const triggerFileInput = (e) => {
  excelInput.value.click() // 通过 .value 访问 DOM 元素并触发点击事件
}
//点击添加文件的对话框的确认按钮
const postAddExcel = async () => {
  isAddShow.value = false
  const formData = new FormData()
  formData.append('file', file.value) // 将文件添加到 FormData
  try {
    const response = await tableApi.saveFiles(formData) // 调用后端 API
    console.log('上传成功:', response)
  } catch (error) {
    console.error('上传失败:', error)
  }
}
</script>

<template>
  <div>
    <el-container class="home-container">
      <!-- header -->
      <el-header>
        <el-row class="header-row">
          <el-col :span="0.99">
            <span class="header-logo"></span>
          </el-col>
          <el-col :span="5" style="flex: auto; max-width: 15.5%">
            <p class="system-name">玉米生产力预测平台</p>
          </el-col>
          <!-- <el-col :span="1"></el-col> -->
          <!-- 移除用户信息显示区域 -->
        </el-row>
      </el-header>

      <el-container style="overflow: auto">
        <!-- 菜单 -->
        <el-aside>
          <div class="aside-wrapper">
            <!-- 第一层数据 -->
            <el-menu
              ref="mainMenu"
              :default-openeds="openMenus"
              :default-active="selectdMenuItem"
              class="el-menu-vertical-demo"
              :collapse="isCollapse"
            >
              <el-sub-menu
                v-for="(menuItem, index) in menuConfig"
                :index="menuItem.key"
                style="margin-left: -12px"
              >
                <template #title>
                <img
                  style="width: 24px; height: 24px; margin-left: 10px"
                  :src="getMenuIcon(menuItem.key)"
                  fit="fill"
                />
                <span style="width: 98px; margin-left: 14px">{{
                  menuItem.title
                }}</span>
                </template>
                <!-- 第二层数据 -->
                <template v-for="child in menuItem.childrend" :key="child.key">
                  <!-- 如果有子菜单，渲染为 el-sub-menu -->
                  <el-sub-menu
                    v-if="child.childrend && child.childrend.length > 0"
                    :index="child.key"
                    :open="true"
                  >
                    <template #title>
                      <el-icon>
                        <Memo />
                      </el-icon>
                      <span
                        style="width: auto; max-width: 200px; min-width: 108px"
                        class="data-name"
                        :title="child.title"
                        >{{ child.title }}</span
                      >

                      <!--  <el-icon style="margin-left: auto" @click="clickPlus">
                      <Plus />
                    </el-icon> -->
                    </template>

                    <!-- 第三层数据 -->
                    <!--   :class="
                      selectdMenuItem === item.key ? 'menu-item-selected' : ''
                    "  动态设置类，为其添加背景颜色 -->
                    <el-menu-item
                      v-for="(item, key) in child.childrend"
                      :index="item.key"
                      @click="showData(item)"
                      :key="item.key"
                      :class="
                        selectdMenuItem === item.key ? 'menu-item-selected' : ''
                      "
                    >
                      <el-icon>
                        <Document />
                      </el-icon>
                      <span
                        style="
                        width: 188px;
                        font-size: 12px;
                        white-space: normal;
                        word-wrap: break-word;
                        line-height: 1.4; /* 让行距舒适，不重叠 */
                        display: inline-block; /* 让 width 生效并可换行 */
                      "
                        class="data-name"
                        :title="item.title"
                        >{{ item.title }}</span
                      >
                    </el-menu-item>
                  </el-sub-menu>
                  <!-- 如果没有子菜单，渲染为 el-menu-item -->
                  <el-menu-item
                    v-else
                    :index="child.key"
                    @click="showData(child)"
                    :class="
                      selectdMenuItem === child.key ? 'menu-item-selected' : ''
                    "
                  >
                    <el-icon>
                      <Memo />
                    </el-icon>
                    <span
                      style="width: auto; max-width: 200px; min-width: 108px"
                      class="data-name"
                      :title="child.title"
                      >{{ child.title }}</span
                    >
                  </el-menu-item>
                </template>
              </el-sub-menu>
            </el-menu>

            <div class="collapse-toggle" @click="isCollapse = !isCollapse">
              <el-icon :size="20">
                <Expand v-if="isCollapse" />
                <Fold v-else />
              </el-icon>
            </div>
          </div>
          <!-- 点击+号跳出对话框 -->

          <!-- <el-menu
                        v-if="showRightMenu"
                        ellipsis
                         class="el-menu-vertical-demo"
                         :style="{ top: positionY + 'px', left: positionX + 'px', position: 'absolute' }"
                        :popper-offset="16"
                        style="max-width: 160px;min-height: 120px;z-index: 9999;border: 1px solid #888888;border-radius: 2px;"
                    >
                        <el-menu-item class="right-menu-item" index="1" @pointerdown.stop="handleMenuItem('add')">新增</el-menu-item>
                        <el-menu-item class="right-menu-item" index="2" @pointerdown.stop="handleMenuItem('delete')">删除</el-menu-item>
                        <el-menu-item class="right-menu-item" index="3" @pointerdown.stop="handleMenuItem('view')">查看流程图</el-menu-item>
                        <el-menu-item class="right-menu-item" index="3" @pointerdown.stop ="handleMenuItem('rename')">重命名</el-menu-item>
                    </el-menu> -->
        </el-aside>
        <el-container>
          <el-main>
            <!-- 面包屑导航 -->
            <div class="breadcrumb-container" v-if="breadcrumbPath.length > 0">
              <span
                v-for="(crumb, index) in breadcrumbPath"
                :key="index"
                class="breadcrumb-item"
              >
                {{ crumb.title }}
                <span v-if="index < breadcrumbPath.length - 1" class="breadcrumb-separator"> / </span>
              </span>
            </div>
            <div class="main-content">
              <router-view></router-view>
            </div>
          </el-main>
        </el-container>
      </el-container>
    </el-container>
    <fieldDialog />
    <editDataDialog />
    <el-dialog v-model="gyDialogShow" title="创建工艺" width="400">
      <el-form label-width="80px">
        <el-form-item label="工艺名称">
          <el-input
            placeholder="输入工艺名称"
            class="field-input"
            v-model="gysetName"
            @input="updateInput"
          ></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="cancelGySet">取 消</el-button>
        <el-button type="primary" @click="confirmGySet">确 定</el-button>
      </span>
    </el-dialog>
    <el-dialog v-model="rnDialogShow" title="重命名" width="400">
      <el-form label-width="100px">
        <el-form-item label="输入新名称">
          <el-input
            placeholder="输入新名称"
            class="field-input"
            v-model="renameValue"
            @input="updateRNInput"
          ></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer" style="margin-left: 20px">
        <el-button @click="cancelRename">取 消</el-button>
        <el-button type="primary" @click="confirmRename">确 定</el-button>
      </span>
    </el-dialog>
    <el-dialog
      title="选择要上传的文件"
      :visible.sync="isAddShow"
      width="30%"
      center
      v-model="isAddShow"
    >
      <p style="margin-left: 5px; font-size: 16px; color: red">
        只允许上传.xls和.xlsx文件!!!
      </p>
      <div class="inputbox">
        <el-button @click="triggerFileInput" style="border: 0"
          >选择文件:</el-button
        >
        <p style="margin-left: 5px; font-size: 16px">{{ selectedFileName }}</p>
        <input
          type="file"
          @change="handleFileChange"
          style="display: none; line-height: 30px"
          ref="excelInput"
        />
      </div>

      <span
        slot="footer"
        class="dialog-footer"
        style="display: inline-flex; justify-content: flex-end; width: 100%"
      >
        <el-button @click="isAddShow = false">取 消</el-button>
        <el-button type="primary" @click="postAddExcel">确 定</el-button>
      </span>
    </el-dialog>
  </div>
</template>
<style scoped>
.home-container {
  position: absolute;
  height: 100%;
  top: 0px;
  left: 0px;
  width: 100%;
  background: #f2f3f5;
}

.el-header {
  background: white; /* 与侧边栏一致 */
  padding: 0 10px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.header-row {
  background: white; /* 与侧边栏一致 */
}

.system-name {
  color: #1f1f1f; /* 在浅色背景下保持可读 */
  font-size: 18px;
  margin-left: 10px;
}

.el-aside {
  background: white;
  width: auto !important;
  display: flex;
}

.aside-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.aside-wrapper .el-menu {
  flex: 1;
  overflow: auto;
}

.el-menu-vertical-demo:not(.el-menu--collapse) {
  width: 288px;
  min-height: 400px;
}

.el-footer {
  color: #cccccc;
  text-align: center;
  line-height: 60px;
}

.el-footer:hover {
  color: #2661ef;
}

.el-menu-vertical-demo:not(.el-menu--collapse) {
  width: 288px;
  min-height: 400px;
}

/* 一级 / 二级（含有子级的）菜单选中态：文字高亮为主色 */
.el-menu-vertical-demo .el-sub-menu.is-active > .el-sub-menu__title {
  color: #0aa979 !important;
}
.el-menu-vertical-demo .el-sub-menu.is-active > .el-sub-menu__title span,
.el-menu-vertical-demo .el-sub-menu.is-active > .el-sub-menu__title .el-icon {
  color: #0aa979 !important;
}
/* 一级菜单图标选中态：使用 filter 改变图片颜色为绿色 */
.el-menu-vertical-demo .el-sub-menu.is-active > .el-sub-menu__title img {
  filter: brightness(0) saturate(100%) invert(48%) sepia(79%) saturate(2476%) hue-rotate(130deg) brightness(95%) contrast(85%);
}

/* 二级 / 三级菜单选中态：文字与背景、右侧高亮条 */
.el-menu-vertical-demo .el-menu-item.is-active,
.menu-item-selected {
  color: #128864 !important;
  background-color: rgba(18, 165, 148, 0.1) !important; /* #12A594 10% */
  border-right: 3px solid #0aa979;
  border-radius: 2px 0 0 2px;
}
.el-menu-vertical-demo .el-menu-item.is-active .el-icon,
.menu-item-selected .el-icon {
  color: #128864 !important;
}

/* 悬浮未选中菜单（一级 / 二级 / 三级）：统一文字高亮 */
.el-menu-vertical-demo .el-menu-item:not(.is-active):hover,
.el-menu-vertical-demo .el-sub-menu:not(.is-active) > .el-sub-menu__title:hover {
  color: #0aa979 !important;
}
.el-menu-vertical-demo .el-menu-item:not(.is-active):hover .el-icon,
.el-menu-vertical-demo .el-menu-item:not(.is-active):hover span,
.el-menu-vertical-demo .el-sub-menu:not(.is-active) > .el-sub-menu__title:hover .el-icon,
.el-menu-vertical-demo .el-sub-menu:not(.is-active) > .el-sub-menu__title:hover span {
  color: #0aa979 !important;
}
/* 一级菜单图标悬浮态：使用 filter 改变图片颜色为绿色 */
.el-menu-vertical-demo .el-sub-menu:not(.is-active) > .el-sub-menu__title:hover img {
  filter: brightness(0) saturate(100%) invert(48%) sepia(79%) saturate(2476%) hue-rotate(130deg) brightness(95%) contrast(85%);
}

/* 折叠状态下的悬浮效果 */
.el-menu-vertical-demo.el-menu--collapse .el-menu-item:not(.is-active):hover,
.el-menu-vertical-demo.el-menu--collapse .el-sub-menu:not(.is-active) > .el-sub-menu__title:hover {
  color: #0aa979 !important;
}
.el-menu-vertical-demo.el-menu--collapse .el-menu-item:not(.is-active):hover .el-icon,
.el-menu-vertical-demo.el-menu--collapse .el-menu-item:not(.is-active):hover span,
.el-menu-vertical-demo.el-menu--collapse .el-sub-menu:not(.is-active) > .el-sub-menu__title:hover .el-icon,
.el-menu-vertical-demo.el-menu--collapse .el-sub-menu:not(.is-active) > .el-sub-menu__title:hover span,
.el-menu-vertical-demo.el-menu--collapse .el-sub-menu:not(.is-active) > .el-sub-menu__title:hover img {
  color: #0aa979 !important;
  filter: brightness(0) saturate(100%) invert(48%) sepia(79%) saturate(2476%) hue-rotate(130deg) brightness(95%) contrast(85%);
}


/* 折叠状态下的选中效果 */
.el-menu-vertical-demo.el-menu--collapse .el-sub-menu.is-active > .el-sub-menu__title {
  color: #0aa979 !important;
}
.el-menu-vertical-demo.el-menu--collapse .el-sub-menu.is-active > .el-sub-menu__title .el-icon,
.el-menu-vertical-demo.el-menu--collapse .el-sub-menu.is-active > .el-sub-menu__title img {
  color: #0aa979 !important;
  filter: brightness(0) saturate(100%) invert(48%) sepia(79%) saturate(2476%) hue-rotate(130deg) brightness(95%) contrast(85%);
}
.el-menu-vertical-demo.el-menu--collapse .el-menu-item.is-active,
.el-menu-vertical-demo.el-menu--collapse .menu-item-selected {
  color: #128864 !important;
  background-color: rgba(18, 165, 148, 0.1) !important;
}
.el-menu-vertical-demo.el-menu--collapse .el-menu-item.is-active .el-icon,
.el-menu-vertical-demo.el-menu--collapse .menu-item-selected .el-icon {
  color: #128864 !important;
}

.add-table {
  text-align: right;
  font-size: 24px;
  margin-left: 5px;
}

.delete-table {
  text-align: right;
  font-size: 28px;
  margin-left: 5px;
}

.add-table:hover {
  color: #2661ef;
}

.delete-table:hover {
  color: #f00;
}

.header-logo {
  background-image: url('../assets/img/icon/logo.png');
  display: block;
  width: 32px;
  height: 32px;
  background-size: 100% 100%;
  margin-top: 12px;
  background-color: #054705; /* 给 logo 增加底色以在浅色背景下可见 */
  border-radius: 6px;
}

.on-publish {
  position: absolute;
  width: 25px;
  height: 26px;
  top: 18px;
  right: 130px;
  cursor: pointer;
}

.on-publish:hover {
  top: 19px;
  right: 129px;
}

.menu-item-selected {
  background-color: #7297ec;
}

.field-input {
  width: 85%;
}

.data-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  /* 对于二级菜单项，允许更宽的显示 */
  flex: 1;
}

.right-menu-item {
  height: 36px;
}
.inputbox {
  display: flex;
  margin: 0 5px 5px 5px;
  align-items: center;
  height: 30;
  border: 1px solid #e5dbdb;
  .el-button {
    font-size: 16px;
  }
}
.el-table {
  height: 800px;
}

/* el-main 设置 padding，内容区域对齐到 el-main 边沿 */
.el-container > .el-main {
  padding: 48px 24px 24px 24px !important;
  min-height: 100%;
  box-sizing: border-box;
  position: relative;
}

/* 面包屑导航样式 */
.breadcrumb-container {
  position: absolute;
  top: 17px; /* 内容上方31px：48px(padding-top) - 31px = 17px */
  left: 24px; /* 与内容左对齐 */
  font-family: 'PingFang SC', sans-serif;
  font-weight: 400;
  font-size: 12px;
  line-height: 20px;
  letter-spacing: 0px;
  color: #000000;
  opacity: 0.65;
  height: 20px;
  display: flex;
  align-items: center;
  z-index: 10;
}

.breadcrumb-item {
  display: inline-block;
  height: 20px;
  line-height: 20px;
  width: auto;
  min-width: 48px;
}

.breadcrumb-separator {
  margin: 0 4px;
  opacity: 0.65;
}

/* 主内容区域填满 el-main，对齐边沿，高度自适应内容，背景色只填充内容区域 */
.main-content {
  width: 100%;
  min-height: 100%;
  background-color: #ffffff;
  box-sizing: border-box;
  position: relative;
}

/* 地图页面特殊处理：地图容器保留 padding，填满内容区域 */
.main-content #map-container {
  width: 100%;
  height: 100%;
  min-height: calc(100vh - 60px - 72px); /* 视口高度 - header高度 - 上下padding */
}
.collapse-toggle {
  border-top: 1px solid #e6e6e6;
  padding: 10px 10px; /* 与一级菜单图标左边距对齐 */
  display: flex;
  align-items: center;
  justify-content: flex-start;
  cursor: pointer;
  color: #00000073;
  margin-top: auto; /* 固定在底部 */
}
.collapse-toggle .el-icon {
  margin-left: 0; /* 与一级菜单图标对齐 */
}
.menu-item-selected[data-v-83883e7f] {
  background-color: #68e7d2;
}
</style>
