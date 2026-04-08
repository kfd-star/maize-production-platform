<script setup>
import { onBeforeMount, onMounted, ref, getCurrentInstance } from 'vue'
import { useRouter } from 'vue-router'
import { CirclePlus } from '@element-plus/icons-vue'
import bus from '../utils/EventBus.js'
import { useStore, useMenuConfig } from '@/store/index.js'
import { storeToRefs } from 'pinia'
import BasicDataTable from '@/components/BasicDataTable.vue'

// 1. 首先定义所有响应式变量
const { tableShow, editDataDialog, mapShow } = storeToRefs(useStore())
const useMenu = useMenuConfig()
const searchWord = ref('')
const options = ref([])
const total = ref(0)
const currentPage = ref(1)
const defaultPageSize = 20
const loading = ref(false)

const tableData = ref({
  fields: [],
  name: '',
  dataItems: [],
})
const totalDataTable = ref(null)

// 当前选中的数据分类
const currentCategory = ref('')
const currentCategoryName = ref('')

// 2. 定义常量
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

// 3. 定义所有函数
function updateTableData(dataItems) {
  if (!dataItems) return
  tableData.value.dataItems = []
  const size = defaultPageSize
  const idx = currentPage.value - 1
  for (let i = idx * size; i < idx * size + size; i++) {
    const item = dataItems[i]
    if (item) {
      tableData.value.dataItems.push(item)
    }
  }
}

function pageChange(page) {
  currentPage.value = page
  if (totalDataTable.value && totalDataTable.value.dataItems) {
    updateTableData(totalDataTable.value.dataItems)
  }
}

function addDataItem() {
  editDataDialog.value = true
  bus.emit('addDataItem', {
    tableData: totalDataTable,
  })
}

function tableRowClassName({ row, rowIndex }) {
  if (rowIndex % 2 === 0) {
    return 'warning-row'
  } else if (rowIndex % 2 === 1) {
    return 'success-row'
  }
  return ''
}

function handleEdit(index, row) {
  editDataDialog.value = true
  bus.emit('editDataItem', {
    dataItem: row,
  })
}

function handleDelete(index, row) {
  if (totalDataTable.value && totalDataTable.value.dataItems) {
    totalDataTable.value.dataItems.splice(index, 1)
    bus.emit('updateDataItem')
  }
}

function search(value) {
  const results = []
  if (totalDataTable.value && totalDataTable.value.dataItems) {
    const dataItems = totalDataTable.value.dataItems
    for (let i = 0; i < dataItems.length; i++) {
      const item = dataItems[i]
      let searchStr = ''
      for (const p in item) {
        searchStr += item[p]
      }
      if (searchStr.indexOf(value) > -1 || value === '') {
        results.push(item)
      }
    }
  }
  searchWord.value = value
  updateTableData(results)
}

function clearSearch() {
  search('')
}

function searchOptions(qString) {
  if (!qString) {
    options.value = []
    return
  }
  loading.value = true
  setTimeout(() => {
    loading.value = false
    const results = []
    if (totalDataTable.value && totalDataTable.value.dataItems) {
      const dataItems = totalDataTable.value.dataItems
      for (let i = 0; i < dataItems.length; i++) {
        const item = dataItems[i]
        for (const p in item) {
          const str = `${item[p]}`
          if (str.indexOf(qString) > -1) {
            results.push({
              key: i,
              value: str,
            })
            break
          }
        }
      }
    }
    options.value = results
  }, 1000)
  searchWord.value = qString
}

bus.on('showtable', (data) => {
  tableShow.value = true
  mapShow.value = false
  totalDataTable.value = data.table
  
  // 安全地访问数据
  if (totalDataTable.value && totalDataTable.value.dataItems) {
    total.value = totalDataTable.value.dataItems.length
    tableData.value.fields = totalDataTable.value.fields || []
    tableData.value.name = totalDataTable.value.name || ''
    
    // 设置当前分类
    currentCategory.value = data.category || ''
    currentCategoryName.value = categoryMapping[data.category] || data.category || '未知分类'
    
    updateTableData(totalDataTable.value.dataItems)
  }
})

// 4. 最后设置事件监听器
bus.on('updateDataItem', (e) => {
  if (totalDataTable.value && totalDataTable.value.dataItems) {
    updateTableData(totalDataTable.value.dataItems)
    total.value = totalDataTable.value.dataItems.length
  }
})

// 页面加载时初始化
onMounted(() => {
  // 检查URL参数，如果有category参数则直接设置
  const router = useRouter()
  const route = router.currentRoute.value
  
  if (route.query) {
    // 优先使用category参数
    if (route.query.category) {
      currentCategory.value = route.query.category
      currentCategoryName.value = categoryMapping[route.query.category] || route.query.category
      tableShow.value = true
      mapShow.value = false
    } 
    // 如果没有category参数，尝试从name参数反向查找
    else if (route.query.name) {
      const nameParam = route.query.name
      
      // 检查name参数是否是英文key（如climate）
      if (categoryMapping[nameParam]) {
        // 如果name参数直接对应category key
        currentCategory.value = nameParam
        currentCategoryName.value = categoryMapping[nameParam]
        tableShow.value = true
        mapShow.value = false
      } else {
        // 如果name参数是中文名称，反向查找
        const category = Object.keys(categoryMapping).find(key => 
          categoryMapping[key] === nameParam
        )
        
        if (category) {
          currentCategory.value = category
          currentCategoryName.value = nameParam
          tableShow.value = true
          mapShow.value = false
        }
      }
    }
  }
})

</script>
<template>
  <div class="main" v-if="tableShow">
    <!-- 使用新的基础数据表格组件 -->
    <BasicDataTable
      v-if="currentCategory"
      :category="currentCategory"
      :category-name="currentCategoryName"
    />
    
    <!-- 保留原有的表格显示逻辑作为备用 -->
    <el-container class="main_one" v-else>
      <el-header class="title">
        <span style="padding-left: 20px"
          >所属分类:{{ useMenu.belongCategory }}</span
        >
        <el-upload
          action
          accept=".xlsx, .xls"
          style="padding-right: 20px"
          :on-change="() => {}"
          :show-file-list="false"
          :auto-upload="false"
        >
          <el-button type="primary">上传 Excel</el-button>
        </el-upload>
      </el-header>
      <el-main>
        <el-container class="main_two">
          <el-header class="search-and-add">
            <el-select
              v-model="searchWord"
              filterable
              clearable
              remote
              reserve-keyword
              v-if="tableShow"
              :remote-method="searchOptions"
              :loading="loading"
              @change="search"
              @clear="clearSearch"
              placeholder="输入检索关键字"
            >
              <el-option
                class="add-button"
                v-for="item in options"
                :key="item.key"
                :label="item.value"
                :value="item.value"
              >
              </el-option>
              <template #loading>
                <svg class="circular" viewBox="0 0 50 50">
                  <circle class="path" cx="25" cy="25" r="20" fill="none" />
                </svg>
              </template>
            </el-select>
            <el-button
              style="color: cornflowerblue"
              v-if="tableShow"
              @click="addDataItem"
            >
              <el-icon style="margin-right: 5px"><CirclePlus /></el-icon
              >新增数据
            </el-button>
          </el-header>
          <el-main class="main_table"
            ><el-table
              :data="tableData.dataItems"
              :default-sort="{
                prop: 'ID',
                order: 'descending',
              }"
              style="width: 100%; margin-top: 45px"
              :row-class-name="tableRowClassName"
            >
              <el-table-column
                type="index"
                width="150"
                label="序号"
                sortable="true"
              />
              <el-table-column
                v-for="field in tableData.fields"
                :prop="field"
                :label="field"
              />
              <el-table-column width="150" label="操作">
                <template #default="scope">
                  <el-button
                    size="small"
                    @click="handleEdit(scope.$index, scope.row)"
                  >
                    编辑
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click="handleDelete(scope.$index, scope.row)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table></el-main
          >
          <el-footer class="page-div">
            <el-pagination
              size="small"
              background
              layout="prev, pager, next"
              :default-page-size="defaultPageSize"
              :total="total"
              class="mt-4"
              @change="pageChange"
          /></el-footer>
        </el-container>
      </el-main>
    </el-container>
  </div>
</template>
<style scoped>
.title {
  display: flex;
  align-items: center; /* 让子元素垂直居中 */
  justify-content: space-between;
  margin-bottom: 30px;
}
.search-and-add {
  width: 400px;
  display: flex;
  gap: 10px; /* 设置搜索框和按钮之间的间距 */
  margin-left: auto;
  margin-bottom: -10px;
  padding-bottom: 0;
}
.main_table {
  margin-top: -40px; /* 确保表格紧贴搜索框 */
  padding-top: 0;
}
.add-button {
  color: cornflowerblue;
}
</style>
