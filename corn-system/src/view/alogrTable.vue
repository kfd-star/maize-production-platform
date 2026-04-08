<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { downloadFolder } from '@/api/alogrPy.js'
import { ElMessage, ElMessageBox, emitChangeFn } from 'element-plus'

const tableData = ref({}) // 存储多个表数据
const tableColumns = ref({}) // 存储表头
const excelSheetname = ref([]) // 存储所有工作表名
const activeSheet = ref('') // 当前选中的表格
const currentPage = ref(1) // 当前页
const pageSize = ref(6) // 每页显示多少条数据
const props = defineProps(['data'])

onMounted(() => {
  showalogrOuputData()
})
const showalogrOuputData = () => {
  const { Data } = props.data || {}
  tableData.value = Data.result
  downloadUrl.value = Data.output_path // 获取下载链接
  excelSheetname.value = Object.keys(tableData.value || {}) // 存储所有工作表名
  activeSheet.value = excelSheetname.value[0] || ''

  const firstRow = tableData.value[activeSheet.value]?.[0] || {}
  tableColumns.value = Object.keys(firstRow || {})

  console.log(tableColumns)
  console.log(tableData.value)
  console.log(tableData.value[activeSheet.value])
}

const loading = ref(false)
// 计算当前页的数据
const paginatedData = computed(() => {
  if (!tableData.value[activeSheet.value]) return []
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  console.log(tableData.value[activeSheet.value].slice(start, end))

  return tableData.value[activeSheet.value].slice(start, end)
})

// 监听分页变化
const handlePageChange = (page) => {
  currentPage.value = page
}
// 监听工作表变化，更新表头
watch(activeSheet, (newSheet) => {
  const firstRow = tableData.value[newSheet]?.[0] || {}
  tableColumns.value = Object.keys(firstRow)
})

//编辑函数
const editRow = (index, row) => {
  console.log(index, row)

  editDateRow.value = index
  drawer.value = true
  formdata.value = { ...row }
  console.log(formdata.value)
}
//删除函数
const deleteRow = (index) => {
  ElMessageBox.confirm('确定要删除这条数据吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      const rowIndex = (currentPage.value - 1) * pageSize.value + index
      tableData.value[activeSheet.value].splice(rowIndex, 1) // 删除数据
      ElMessage.success('删除成功')
    })
    .catch(() => {
      ElMessage.info('取消删除')
    })
}

//抽屉组件
const drawer = ref(false)
const formdata = ref({}) // 存储编辑数据
const refForm = ref(null) // 表单 ref
const editDateRow = ref()
const submitForm = () => {
  tableData.value[activeSheet.value][editDateRow.value] = { ...formdata.value } // 更新数据
  ElMessage.success('修改成功')
  drawer.value = false
}
//返回 通知alogy组件
const emit = defineEmits(['closeAlogrTable'])
const goBack = () => {
  emit('closeAlogrTable')
}
//下载
const downloadUrl = ref('')
// 从后端传入的 zip 文件链接
const downloadFile = async () => {
  if (!downloadUrl.value) {
    ElMessage.warning('暂无可下载文件')
    return
  }
  const output = downloadUrl.value

  try {
    const response = await downloadFolder(output)
    const blob = new Blob([response.data], { type: 'application/zip' })
    const blobUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = output.split('/').pop() + '.zip' // ✅ 取文件夹名作为文件名
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(blobUrl)
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}
</script>
<template>
  <el-container>
    <el-main>
      <el-container>
        <el-header class="search-and-add">
          <div class="left" style="display: flex; width: 100%">
            <span>所选表格:</span>
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
            <el-button
              type="primary"
              style="margin-left: 1000px"
              @click="downloadFile"
              >下载</el-button
            >
            <el-button type="primary" style="margin-left: auto" @click="goBack"
              >返回</el-button
            >
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
              fixed="left"
              align="center"
            >
              <template #default="scope">
                {{ (currentPage - 1) * pageSize + scope.$index + 1 }}
              </template>
            </el-table-column>
            <el-table-column
              v-for="(col, index) in tableColumns || []"
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
