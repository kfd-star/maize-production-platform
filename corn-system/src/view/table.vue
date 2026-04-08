<script setup>
/* -------------------- 1. import 导入 -------------------- */
import { ref, watch, computed, onMounted } from 'vue'
import api from '@/api/table'
import { editorData, deleteData } from '@/api/alogrPy'
import { excelHandle, savaFile } from '@/utils/excel'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useMenuConfig } from '../store/index.js'
import { useRoute } from 'vue-router'

/* -------------------- 2. 变量声明 -------------------- */
const tableData = ref({}) // 所有表数据
const tableColumns = ref({}) // 所有表头
const excelSheetname = ref([]) // 所有工作表名
const activeSheet = ref('') // 当前选中表
const currentPage = ref(1) // 当前页码
const pageSize = ref(6) // 每页显示条数
const route = useRoute()
const useMenu = useMenuConfig()
const rowIndex = ref(0) // 编辑时实际 row 索引
const loading = ref(false)

const drawer = ref(false)
const formdata = ref({}) // 编辑的数据
const refForm = ref(null) // 表单 ref
const editDateRow = ref() // 当前编辑行索引（分页内）

/* -------------------- 3. 生命周期钩子 -------------------- */
onMounted(() => {
  if (route.query.name) {
    getFilesServer(route.query.name)
  }
})

/* -------------------- 4. watch 监听器 -------------------- */
// 切换文件时，重新加载数据
watch(
  () => route.query.name,
  (newFilename, oldFilename) => {
    if (newFilename !== oldFilename && newFilename) {
      getFilesServer(newFilename)
    }
  },
)

// 切换表时，重置当前页为 1
watch(activeSheet, () => {
  currentPage.value = 1
})

/* -------------------- 5. computed 计算属性 -------------------- */
const paginatedData = computed(() => {
  if (!tableData.value[activeSheet.value]) return []
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return tableData.value[activeSheet.value].slice(start, end)
})

/* -------------------- 6. 核心函数逻辑 -------------------- */

// Excel 上传
const handel = async (e) => {
  const file = e.raw
  if (!file) return
  try {
    const { sheets, columns, sheetNames } = await savaFile(file)
    tableData.value = sheets // 存储所有工作表数据
    tableColumns.value = columns // 存储所有工作表列名
    excelSheetname.value = sheetNames // 存储所有工作表名
    activeSheet.value = sheetNames[0]
    currentPage.value = 1
  } catch {
    ElMessage.error('文件格式错误')
  }
}

// 获取 Excel 数据（支持可选是否重置分页/表名）
const getFilesServer = async (
  filename,
  options = { ResetSheet: true, ResetPage: true },
) => {
  const { ResetSheet, ResetPage } = options
  try {
    loading.value = true
    const data = await api.getFiles(filename)
    const arrayBuffer = new Uint8Array(data.data.content).buffer
    const { sheets, columns, sheetNames } = excelHandle(arrayBuffer)
    tableData.value = sheets
    tableColumns.value = columns
    excelSheetname.value = sheetNames
    if (ResetSheet) activeSheet.value = sheetNames[0]
    if (ResetPage) currentPage.value = 1
    loading.value = false
  } catch (error) {
    if (error.response) {
      ElMessage.error(
        `请求失败：${error.response.status} ${error.response.data.detail || error.response.statusText}`,
      )
    } else if (error.request) {
      ElMessage.error('服务器无响应，请稍后重试')
    } else {
      ElMessage.error(`错误：${error.message || error}`)
    }
  }
}

// 分页切换
const handlePageChange = (page) => {
  currentPage.value = page
}

// 编辑
const editRow = (index, row) => {
  // 计算全表中的行索引 +2原因
  rowIndex.value = (currentPage.value - 1) * pageSize.value + index + 2
  editDateRow.value = index
  drawer.value = true
  formdata.value = { ...row }
}

// 删除
const deleteRow = async (index) => {
  try {
    await ElMessageBox.confirm('确定要删除这条数据吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    rowIndex.value = (currentPage.value - 1) * pageSize.value + index + 2
    console.log(`删除行索引: ${rowIndex.value}`)

    const data = {
      row_index: rowIndex.value,
      sheet_name: activeSheet.value,
      file_name_prefix: route.query.name,
    }

    // 等待接口调用完成
    const res = await deleteData(data)

    if (res.data.message === '行删除成功') {
      const sheet = activeSheet.value
      // 删除本地数据
      tableData.value[sheet].splice(rowIndex.value - 2, 1) // 注意这里应该是 rowIndex - 2，因为之前 +2 是为了 openpyxl

      // 计算分页逻辑
      const totalItems = tableData.value[sheet].length
      const maxPage = Math.ceil(totalItems / pageSize.value)
      if (currentPage.value > maxPage) {
        currentPage.value = Math.max(1, maxPage)
      }

      ElMessage.success('删除成功')
    }
  } catch (err) {
    if (err === 'cancel') {
      ElMessage.info('取消删除')
    } else {
      ElMessage.error('删除失败，网络或未知错误')
    }
  }
}

// 提交编辑
const submitForm = async () => {
  try {
    await ElMessageBox.confirm('确定修改这条数据吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    const data = {
      row_index: rowIndex.value,
      sheet_name: activeSheet.value,
      new_row: Object.values(formdata.value).map((item) => String(item)), //// 确保是数组（后端接收的是 List[str]）
      file_name_prefix: route.query.name,
    }

    const res = await editorData(data)
    if (res.data.message === '行替换成功') {
      getFilesServer(route.query.name, {
        ResetSheet: false,
        ResetPage: false,
      })
      ElMessage.success('修改成功')
      drawer.value = false
    }
  } catch (err) {
    if (err?.response) {
      ElMessage.error(`修改失败：${err.response.data.detail}`)
    } else {
      ElMessage.error('修改失败，网络或未知错误')
    }
  }
}
</script>

<template>
  <el-container>
    <el-header class="views_header">
      <span>所属分类: {{ useMenu.belongCategory }}</span>
      <el-upload
        action
        accept=".xlsx, .xls"
        :on-change="handel"
        :show-file-list="false"
        :auto-upload="false"
      >
        <el-button type="primary">上传 Excel</el-button>
      </el-upload>
    </el-header>

    <el-main>
      <el-container>
        <el-header class="search-and-add">
          <div class="left">
            <span>所选表格：{{ route.query.filename }}</span>
            <el-select
              v-model="activeSheet"
              placeholder="选择工作表"
              style="margin-left: 10px; width: 200px"
            >
              <el-option
                v-for="sheet in excelSheetname"
                :key="sheet"
                :label="sheet"
                :value="sheet"
              />
            </el-select>
          </div>
        </el-header>

        <el-main class="excel_table" width="100%">
          <el-table
            :data="paginatedData"
            stripe
            style="width: 100%; margin-top: 20px"
            :fit="true"
            v-loading="loading"
            scrollbar-always-on
          >
            <el-table-column
              label="序号"
              :min-width="120"
              align="center"
              fixed="left"
            >
              <template #default="scope">
                {{ (currentPage - 1) * pageSize + scope.$index + 1 }}
              </template>
            </el-table-column>
            <el-table-column
              v-for="(col, index) in tableColumns[activeSheet] || []"
              :key="index"
              :prop="String(col)"
              :label="String(col)"
              :min-width="120"
              align="center"
            />
            <el-table-column label="操作" :min-width="180" align="center">
              <template #default="scope">
                <el-button
                  type="primary"
                  @click="editRow(scope.$index, scope.row)"
                  >编辑</el-button
                >
                <el-button type="danger" @click="deleteRow(scope.$index)"
                  >删除</el-button
                >
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            background
            layout="prev, pager, next"
            :total="tableData[activeSheet] ? tableData[activeSheet].length : 0"
            :page-size="pageSize"
            :current-page="currentPage"
            @current-change="handlePageChange"
            style="justify-content: flex-end"
          />
        </el-main>
      </el-container>
    </el-main>
  </el-container>
  <el-drawer v-model="drawer" title="编辑数据">
    <el-form
      :model="formdata"
      label-width="auto"
      style="max-width: 600px"
      ref="refForm"
    >
      <el-form-item
        style="color: black"
        label-position="top"
        v-for="item in tableColumns[activeSheet]"
        :key="String(item)"
        :label="String(item)"
      >
        <el-input v-model="formdata[item]" style="color: black" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="submitForm()">提交</el-button>
        <el-button @click="drawer = false">取消</el-button>
      </el-form-item>
    </el-form>
  </el-drawer>
</template>

<style scoped>
.views_header {
  margin-left: 20px;
  margin-right: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.search-and-add {
  padding-bottom: 0;
  margin: 0 0 -20px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.excel_table {
  margin-top: 0px;
}
::v-deep(.el-scrollbar__thumb) {
  background-color: #000000;
}
</style>
