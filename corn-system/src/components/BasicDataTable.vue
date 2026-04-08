<template>
  <div class="basic-data-table">
    <!-- 头部操作区 -->
    <el-header class="table-header">
      <div class="header-left">
        <span class="category-title">所属分类: {{ categoryName }}</span>
        <el-select
          v-model="selectedFile"
          placeholder="选择文件"
          style="width: 200px; margin-left: 20px"
          @change="handleFileChange"
          clearable
        >
          <el-option
            v-for="file in fileList"
            :key="file.filename"
            :label="file.filename"
            :value="file.filename"
          />
        </el-select>
      </div>
      <div class="header-right">
        <!-- 模式切换按钮 -->
        <el-button
          :type="dataMode === 'excel' ? 'primary' : 'default'"
          @click="toggleDataMode"
          style="margin-right: 10px"
        >
          <el-icon><Switch /></el-icon>
          {{ dataMode === 'excel' ? 'Excel模式' : 'JSON模式' }}
        </el-button>
        
        <!-- 上传按钮（Excel/JSON 模式均可） -->
        <el-upload
          action
          :accept="dataMode === 'excel' ? '.xlsx, .xls' : '.json'"
          :on-change="handleFileUpload"
          :show-file-list="false"
          :auto-upload="false"
          :before-upload="beforeUpload"
        >
          <el-button type="primary" :loading="uploading">
            <el-icon><Upload /></el-icon>
            {{ dataMode === 'excel' ? '上传Excel' : '上传JSON' }}
          </el-button>
        </el-upload>
        
        <el-button
          type="success"
          @click="handleSave"
          :disabled="!selectedFile || !hasChanges"
          :loading="saving"
          style="margin-left: 10px"
        >
          <el-icon><Check /></el-icon>
          {{ dataMode === 'excel' ? '保存更改' : '保存JSON' }}
        </el-button>
        <el-button
          type="info"
          @click="handleExport"
          :disabled="!selectedFile"
          :loading="exporting"
          style="margin-left: 10px"
        >
          <el-icon><Download /></el-icon>
          {{ dataMode === 'excel' ? '导出表格' : '导出JSON' }}
        </el-button>
        <el-button
          type="danger"
          @click="handleDeleteFile"
          :disabled="!selectedFile"
          :loading="deleting"
          style="margin-left: 10px"
        >
          <el-icon><Delete /></el-icon>
          {{ dataMode === 'excel' ? '删除表格' : '删除JSON' }}
        </el-button>
      </div>
    </el-header>

    <!-- 工作表选择（仅在Excel模式下显示） -->
    <el-header class="sheet-header" v-if="dataMode === 'excel' && selectedFile && sheetNames.length > 0">
      <div class="sheet-selector">
        <span>工作表:</span>
        <el-select
          v-model="activeSheet"
          placeholder="选择工作表"
          style="width: 200px; margin-left: 10px"
          @change="handleSheetChange"
        >
          <el-option
            v-for="sheet in sheetNames"
            :key="sheet"
            :label="sheet"
            :value="sheet"
          />
        </el-select>
      </div>
    </el-header>

    <!-- 数据表格 -->
    <el-main class="table-main">
      <el-table
        :data="paginatedData"
        stripe
        style="width: 100%"
        v-loading="loading"
        :fit="true"
        border
        height="500"
        @cell-click="handleCellClick"
        @cell-blur="handleCellBlur"
        @cell-mouse-down="handleCellMouseDown"
        @cell-mouse-move="handleCellMouseMove"
        @cell-mouse-up="handleCellMouseUp"
        @cell-contextmenu="handleCellContextMenu"
        @header-click="handleHeaderClick"
        @header-contextmenu="handleHeaderContextMenu"
        ref="tableRef"
        class="selectable-table"
      >
        
        <el-table-column
          label="序号"
          width="80"
          align="center"
          fixed="left"
        >
          <template #default="scope">
            {{ (currentPage - 1) * pageSize + scope.$index + 1 }}
          </template>
        </el-table-column>
        
        <el-table-column
          v-for="(column, index) in tableColumns"
          :key="index"
          :prop="column"
          :label="column"
          :min-width="120"
          align="center"
          show-overflow-tooltip
        >
          <template #header>
            <div 
              class="header-cell"
              :class="{ 'editing': editingHeader.column === column }"
              @dblclick="startHeaderEdit(column)"
            >
              <!-- 表头编辑模式 -->
              <el-input
                v-if="editingHeader.column === column"
                v-model="editingHeader.value"
                size="small"
                @blur="saveHeaderEdit"
                @keyup.enter="saveHeaderEdit"
                @keyup.escape="cancelHeaderEdit"
                ref="headerEditInput"
                class="header-edit-input"
              />
              <!-- 表头显示模式 -->
              <span v-else class="header-text" :title="column">
                {{ column }}
              </span>
            </div>
          </template>
          <template #default="scope">
            <div 
              class="cell-content"
              :class="{ 
                'editing': editingCell.rowIndex === scope.$index && editingCell.column === column,
                'selected': isCellSelected(scope.$index, column),
                'selection-start': selectionStart.row === scope.$index && selectionStart.col === tableColumns.indexOf(column),
                'selection-end': selectionEnd.row === scope.$index && selectionEnd.col === tableColumns.indexOf(column)
              }"
              :style="{ 
                backgroundColor: isCellSelected(scope.$index, column) ? '#e6f7ff' : '',
                border: isCellSelected(scope.$index, column) ? '2px solid #1890ff' : ''
              }"
              @click.stop="handleCellClick(scope.$index, column, scope.row, $event)"
              @dblclick.stop="handleCellDoubleClick(scope.$index, column, scope.row, $event)"
              @mousedown.stop="handleCellMouseDown(scope.$index, column, $event)"
              @mousemove.stop="handleCellMouseMove(scope.$index, column, $event)"
              @mouseup.stop="handleCellMouseUp(scope.$index, column, $event)"
              @contextmenu="handleCellContextMenu(scope.$index, column, scope.row, $event)"
            >
              <!-- 编辑模式 -->
              <el-input
                v-if="editingCell.rowIndex === scope.$index && editingCell.column === column"
                v-model="editingCell.value"
                size="small"
                @blur="saveEdit"
                @keyup.enter="saveEdit"
                @keyup.escape="cancelEdit"
                ref="editInput"
                class="inline-edit-input"
              />
              <!-- 显示模式 -->
              <span v-else class="cell-text" :title="scope.row[column]">
                {{ scope.row[column] || '' }}
              </span>
            </div>
          </template>
        </el-table-column>
        
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-if="tableData.length > 0"
        background
        layout="total, prev, pager, next, sizes"
        :total="tableData.length"
        :page-size="pageSize"
        :current-page="currentPage"
        :page-sizes="[10, 20, 50, 100]"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
        style="margin-top: 20px; justify-content: center"
      />
    </el-main>

    <!-- 右键菜单 -->
    <div
      v-if="contextMenuVisible"
      class="context-menu-overlay"
      @click="contextMenuVisible = false"
    >
      <div
        class="context-menu"
        :style="{
          left: contextMenuPosition.x + 'px',
          top: contextMenuPosition.y + 'px'
        }"
        @click.stop
      >
        <!-- 基础操作 -->
        <div class="menu-item" @click="handleContextClear">
          <el-icon><RefreshLeft /></el-icon>
          清空
        </div>
        
        <!-- 插入操作 -->
        <div class="menu-group">
          <div class="menu-group-title">
            <el-icon><Plus /></el-icon>
            插入
          </div>
          <div class="menu-item" @click="handleContextInsertRowAbove">
            <el-icon><ArrowUp /></el-icon>
            在上方插入
            <el-input
              v-model.number="insertRowCount"
              size="small"
              style="width: 40px; margin-left: 5px;"
              @click.stop
              @keyup.enter="handleContextInsertRowAbove"
            />
            行
          </div>
          <div class="menu-item" @click="handleContextInsertRowBelow">
            <el-icon><ArrowDown /></el-icon>
            在下方插入
            <el-input
              v-model.number="insertRowCount"
              size="small"
              style="width: 40px; margin-left: 5px;"
              @click.stop
              @keyup.enter="handleContextInsertRowBelow"
            />
            行
          </div>
          <div class="menu-item" @click="handleContextInsertColumnLeft">
            <el-icon><ArrowLeft /></el-icon>
            在左侧插入
            <el-input
              v-model.number="insertColCount"
              size="small"
              style="width: 40px; margin-left: 5px;"
              @click.stop
              @keyup.enter="handleContextInsertColumnLeft"
            />
            列
          </div>
          <div class="menu-item" @click="handleContextInsertColumnRight">
            <el-icon><ArrowRight /></el-icon>
            在右侧插入
            <el-input
              v-model.number="insertColCount"
              size="small"
              style="width: 40px; margin-left: 5px;"
              @click.stop
              @keyup.enter="handleContextInsertColumnRight"
            />
            列
          </div>
        </div>

        <!-- 删除操作 -->
        <div class="menu-group">
          <div class="menu-group-title">
            <el-icon><Delete /></el-icon>
            删除
          </div>
          <div class="menu-item" @click="handleContextDeleteRow">
            <el-icon><Delete /></el-icon>
            删除所在行
          </div>
          <div class="menu-item" @click="handleContextDeleteColumn">
            <el-icon><Delete /></el-icon>
            删除所在列
          </div>
        </div>

        <!-- 单元格操作 -->
        <div class="menu-group">
          <div class="menu-group-title">
            <el-icon><Grid /></el-icon>
            单元格
          </div>
          <div class="menu-item" @click="handleContextInsertCell">
            <el-icon><Plus /></el-icon>
            插入单元格...
          </div>
          <div class="menu-item" @click="handleContextDeleteCell">
            <el-icon><Delete /></el-icon>
            删除单元格...
          </div>
        </div>
      </div>
    </div>

    <!-- 插入单元格对话框 -->
    <el-dialog
      v-model="insertCellDialogVisible"
      title="插入单元格"
      width="400px"
    >
      <el-radio-group v-model="insertCellDirection">
        <el-radio value="right">现有单元格右移</el-radio>
        <el-radio value="down">现有单元格下移</el-radio>
      </el-radio-group>
      <template #footer>
        <el-button @click="insertCellDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmInsertCell">确定</el-button>
      </template>
    </el-dialog>

    <!-- 删除单元格对话框 -->
    <el-dialog
      v-model="deleteCellDialogVisible"
      title="删除单元格"
      width="400px"
    >
      <el-radio-group v-model="deleteCellDirection">
        <el-radio value="left">现有单元格左移</el-radio>
        <el-radio value="up">现有单元格上移</el-radio>
      </el-radio-group>
      <template #footer>
        <el-button @click="deleteCellDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmDeleteCell">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      :title="isEdit ? '编辑数据' : '新增数据'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        :model="formData"
        label-width="120px"
        ref="formRef"
        :rules="formRules"
      >
        <el-form-item
          v-for="(column, index) in tableColumns"
          :key="index"
          :label="column"
          :prop="column"
        >
          <el-input
            v-model="formData[column]"
            :placeholder="`请输入${column}`"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleSave"
          :loading="saving"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Plus, Check, Delete, RefreshLeft, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Grid, Download, Switch } from '@element-plus/icons-vue'
import * as basicDataApi from '@/api/basicData'

// Props
const props = defineProps({
  category: {
    type: String,
    required: true
  },
  categoryName: {
    type: String,
    required: true
  }
})

// 数据模式：'excel' 或 'json'
const dataMode = ref('json') // 默认JSON模式

// 响应式数据
const loading = ref(false)
const uploading = ref(false)
const saving = ref(false)
const exporting = ref(false)
const deleting = ref(false)
const fileList = ref([])
const selectedFile = ref('')
const sheetNames = ref([])
const activeSheet = ref('')
const tableData = ref([])
const tableColumns = ref([])
const currentPage = ref(1)
const pageSize = ref(20)

// 插入数量配置 - 可以通过修改这些值来设置默认插入的行/列数量
const insertRowCount = ref(1)
const insertColCount = ref(1)

// 编辑相关
const editDialogVisible = ref(false)
const isEdit = ref(false)
const editRowIndex = ref(-1)
const formData = ref({})
const formRef = ref(null)
const formRules = ref({})

// 内联编辑相关
const editingCell = ref({
  rowIndex: -1,
  column: '',
  value: '',
  originalValue: ''
})
const editInput = ref(null)
const autoSaveTimer = ref(null)

// 表头编辑相关
const editingHeader = ref({
  column: '',
  value: '',
  originalValue: ''
})
const headerEditInput = ref(null)

// 多选相关
const tableRef = ref(null)

// 数据变更跟踪
const hasChanges = ref(false)
const pendingChanges = ref([])

// 框选相关
const isSelecting = ref(false)
const selectionStart = ref({ row: -1, col: -1 })
const selectionEnd = ref({ row: -1, col: -1 })
const selectedCells = ref([])

// 右键菜单相关
const contextMenuVisible = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })
const contextMenuTarget = ref({ type: '', row: -1, col: -1, column: '' })


// 对话框相关
const insertCellDialogVisible = ref(false)
const deleteCellDialogVisible = ref(false)
const insertCellDirection = ref('right')
const deleteCellDirection = ref('left')

// 计算属性
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return tableData.value.slice(start, end)
})

// 方法定义
const loadFileList = async () => {
  try {
    loading.value = true
    
    if (dataMode.value === 'json') {
      // JSON模式：从后端接口按分类动态获取 JSON 文件列表
      if (!props.category) {
        fileList.value = []
      } else {
        const response = await basicDataApi.getJsonFiles(props.category)
        const jsonFiles = (response.data && response.data.files) || []
        fileList.value = jsonFiles.map((filename) => ({
          filename,
          category: props.category,
          upload_time: '', // JSON 静态文件没有上传时间
          file_size: 0,
        }))
      }
    } else {
      // Excel模式：从后端API获取
      const response = await basicDataApi.getFiles(props.category)
      fileList.value = response.data.files || []
    }
  } catch (error) {
    ElMessage.error('加载文件列表失败')
    console.error('Load file list error:', error)
  } finally {
    loading.value = false
  }
}

// 切换数据模式
const toggleDataMode = () => {
  dataMode.value = dataMode.value === 'excel' ? 'json' : 'excel'
  // 切换模式时重置状态
  resetTable()
  // 重新加载文件列表
  loadFileList()
}

const resetTable = () => {
  selectedFile.value = ''
  sheetNames.value = []
  activeSheet.value = ''
  tableData.value = []
  tableColumns.value = []
  currentPage.value = 1
  // 重置编辑状态
  editingCell.value = {
    rowIndex: -1,
    column: '',
    value: '',
    originalValue: ''
  }
  // 重置选择状态
  selectedCells.value = []
  isSelecting.value = false
  selectionStart.value = { row: -1, col: -1 }
  selectionEnd.value = { row: -1, col: -1 }
}

// 框选相关方法
const isCellSelected = (rowIndex, column) => {
  const actualRowIndex = typeof rowIndex === 'object' ? rowIndex.$index : rowIndex
  const colIndex = tableColumns.value.indexOf(column)
  const isSelected = selectedCells.value.some(cell => 
    cell.row === actualRowIndex && cell.col === colIndex
  )
  return isSelected
}

const handleCellMouseDown = (rowIndex, column, event) => {
  if (event.button !== 0) return // 只处理左键
  
  const colIndex = tableColumns.value.indexOf(column)
  
  // 清除单击定时器
  if (clickTimer) {
    clearTimeout(clickTimer)
    clickTimer = null
  }
  
  // 开始框选
  isSelecting.value = true
  selectionStart.value = { row: rowIndex, col: colIndex }
  selectionEnd.value = { row: rowIndex, col: colIndex }
  
  // 清除之前的选择
  selectedCells.value = []
  
  event.preventDefault()
}

const handleCellMouseMove = (rowIndex, column, event) => {
  if (!isSelecting.value) return
  
  const colIndex = tableColumns.value.indexOf(column)
  selectionEnd.value = { row: rowIndex, col: colIndex }
  
  // 更新选中的单元格
  updateSelectedCells()
  
  event.preventDefault()
}

const handleCellMouseUp = (rowIndex, column, event) => {
  if (event.button !== 0) return // 只处理左键
  
  isSelecting.value = false
  
  const colIndex = tableColumns.value.indexOf(column)
  selectionEnd.value = { row: rowIndex, col: colIndex }
  
  // 最终更新选中的单元格
  updateSelectedCells()
  
  event.preventDefault()
}

const updateSelectedCells = () => {
  const startRow = Math.min(selectionStart.value.row, selectionEnd.value.row)
  const endRow = Math.max(selectionStart.value.row, selectionEnd.value.row)
  const startCol = Math.min(selectionStart.value.col, selectionEnd.value.col)
  const endCol = Math.max(selectionStart.value.col, selectionEnd.value.col)
  
  selectedCells.value = []
  
  for (let row = startRow; row <= endRow; row++) {
    for (let col = startCol; col <= endCol; col++) {
      if (row >= 0 && row < paginatedData.value.length && 
          col >= 0 && col < tableColumns.value.length) {
        selectedCells.value.push({
          row,
          col,
          column: tableColumns.value[col],
          data: paginatedData.value[row]
        })
      }
    }
  }
}

// 右键菜单相关方法
const handleCellContextMenu = async (rowIndex, column, row, event) => {
  event.preventDefault()
  
  // 只处理数字类型的rowIndex，忽略Proxy对象
  if (typeof rowIndex !== 'number') {
    console.log('忽略Proxy对象事件:', rowIndex)
    return
  }
  
  const colIndex = tableColumns.value.indexOf(column)
  
  // 计算绝对行索引
  const actualRowIndex = (currentPage.value - 1) * pageSize.value + rowIndex
  
  contextMenuTarget.value = {
    type: 'cell',
    row: actualRowIndex, // 使用绝对行索引
    col: colIndex,
    column: column
  }
  
  // 智能定位右键菜单，避免超出屏幕边界
  const padding = 10 // 边距
  
  let x = event.clientX
  let y = event.clientY
  
  // 先显示菜单，然后获取实际尺寸
  contextMenuPosition.value = { x, y }
  contextMenuVisible.value = true
  
  // 使用 nextTick 确保菜单已渲染，然后调整位置
  await nextTick()
  
  // 获取菜单的实际尺寸
  const menuElement = document.querySelector('.context-menu')
  if (menuElement) {
    const menuRect = menuElement.getBoundingClientRect()
    const menuWidth = menuRect.width
    const menuHeight = menuRect.height
    
    // 重新计算位置
    let newX = event.clientX
    let newY = event.clientY
    
    // 检查右边界
    if (newX + menuWidth + padding > window.innerWidth) {
      newX = window.innerWidth - menuWidth - padding
    }
    
    // 检查下边界
    if (newY + menuHeight + padding > window.innerHeight) {
      newY = window.innerHeight - menuHeight - padding
    }
    
    // 确保不超出左边界和上边界
    newX = Math.max(padding, newX)
    newY = Math.max(padding, newY)
    
    // 更新位置
    contextMenuPosition.value = {
      x: newX,
      y: newY
    }
  }
}

const handleHeaderContextMenu = async (column, event) => {
  event.preventDefault()
  
  const colIndex = tableColumns.value.indexOf(column)
  
  contextMenuTarget.value = {
    type: 'header',
    row: -1,
    col: colIndex,
    column: column
  }
  
  // 智能定位右键菜单，避免超出屏幕边界
  const padding = 10 // 边距
  
  let x = event.clientX
  let y = event.clientY
  
  // 先显示菜单，然后获取实际尺寸
  contextMenuPosition.value = { x, y }
  contextMenuVisible.value = true
  
  // 使用 nextTick 确保菜单已渲染，然后调整位置
  await nextTick()
  
  // 获取菜单的实际尺寸
  const menuElement = document.querySelector('.context-menu')
  if (menuElement) {
    const menuRect = menuElement.getBoundingClientRect()
    const menuWidth = menuRect.width
    const menuHeight = menuRect.height
    
    // 重新计算位置
    let newX = event.clientX
    let newY = event.clientY
    
    // 检查右边界
    if (newX + menuWidth + padding > window.innerWidth) {
      newX = window.innerWidth - menuWidth - padding
    }
    
    // 检查下边界
    if (newY + menuHeight + padding > window.innerHeight) {
      newY = window.innerHeight - menuHeight - padding
    }
    
    // 确保不超出左边界和上边界
    newX = Math.max(padding, newX)
    newY = Math.max(padding, newY)
    
    // 更新位置
    contextMenuPosition.value = {
      x: newX,
      y: newY
    }
  }
}

// 右键菜单操作方法
const handleContextClear = () => {
  if (selectedCells.value.length === 0) {
    ElMessage.warning('请先选择要清空的单元格')
    return
  }
  
  selectedCells.value.forEach(cell => {
    if (cell.data && cell.column && typeof cell.data === 'object') {
      cell.data[cell.column] = ''
    }
  })
  
  hasChanges.value = true
  ElMessage.success(`成功清空 ${selectedCells.value.length} 个单元格`)
  contextMenuVisible.value = false
}

const handleContextInsertRowAbove = () => {
  const { row } = contextMenuTarget.value
  if (row === -1) return
  
  const rowCount = insertRowCount.value
  if (rowCount <= 0 || rowCount > 100) {
    ElMessage.warning('行数必须在1-100之间')
    return
  }
  
  // 创建多行数据
  const newRows = []
  for (let i = 0; i < rowCount; i++) {
    const newRow = {}
    tableColumns.value.forEach(column => {
      newRow[column] = ''
    })
    newRows.push(newRow)
  }
  
  // 检查是否有选中的单元格
  if (selectedCells.value.length > 0) {
    // 多选插入：获取所有选中单元格的行索引，并转换为绝对索引
    const selectedRows = [...new Set(selectedCells.value.map(cell => {
      // 将分页索引转换为绝对索引
      return (currentPage.value - 1) * pageSize.value + cell.row
    }))]
    const minRowIndex = Math.min(...selectedRows)
    
    tableData.value.splice(minRowIndex, 0, ...newRows)
    
    hasChanges.value = true
    ElMessage.success(`在上方插入 ${rowCount} 行成功`)
    
    // 清除选择
    selectedCells.value = []
  } else {
    // 单选插入：在当前行上方插入
    tableData.value.splice(row, 0, ...newRows)
    
    hasChanges.value = true
    ElMessage.success(`在上方插入 ${rowCount} 行成功`)
  }
  
  contextMenuVisible.value = false
}

const handleContextInsertRowBelow = () => {
  const { row } = contextMenuTarget.value
  if (row === -1) return
  
  const rowCount = insertRowCount.value
  if (rowCount <= 0 || rowCount > 100) {
    ElMessage.warning('行数必须在1-100之间')
    return
  }
  
  // 创建多行数据
  const newRows = []
  for (let i = 0; i < rowCount; i++) {
    const newRow = {}
    tableColumns.value.forEach(column => {
      newRow[column] = ''
    })
    newRows.push(newRow)
  }
  
  // 检查是否有选中的单元格
  if (selectedCells.value.length > 0) {
    // 多选插入：获取所有选中单元格的行索引，并转换为绝对索引
    const selectedRows = [...new Set(selectedCells.value.map(cell => {
      // 将分页索引转换为绝对索引
      return (currentPage.value - 1) * pageSize.value + cell.row
    }))]
    const maxRowIndex = Math.max(...selectedRows)
    
    tableData.value.splice(maxRowIndex + 1, 0, ...newRows)
    
    hasChanges.value = true
    ElMessage.success(`在下方插入 ${rowCount} 行成功`)
    
    // 清除选择
    selectedCells.value = []
  } else {
    // 单选插入：在当前行下方插入
    tableData.value.splice(row + 1, 0, ...newRows)
    
    hasChanges.value = true
    ElMessage.success(`在下方插入 ${rowCount} 行成功`)
  }
  
  contextMenuVisible.value = false
}

const handleContextInsertColumnLeft = () => {
  const { col } = contextMenuTarget.value
  if (col === -1) return
  
  const colCount = insertColCount.value
  if (colCount <= 0 || colCount > 20) {
    ElMessage.warning('列数必须在1-20之间')
    return
  }
  
  // 创建多列
  const newColumns = []
  for (let i = 0; i < colCount; i++) {
    newColumns.push(`新列${Date.now()}_${i}`)
  }
  
  // 检查是否有选中的单元格
  if (selectedCells.value.length > 0) {
    // 多选插入：获取所有选中单元格的列索引，在最小列索引处插入
    const selectedCols = [...new Set(selectedCells.value.map(cell => cell.col))]
    const minColIndex = Math.min(...selectedCols)
    
    tableColumns.value.splice(minColIndex, 0, ...newColumns)
    
    // 为所有行添加新列
    tableData.value.forEach(row => {
      newColumns.forEach(columnName => {
        row[columnName] = ''
      })
    })
    
    hasChanges.value = true
    ElMessage.success(`在左侧插入 ${colCount} 列成功`)
    
    // 清除选择
    selectedCells.value = []
  } else {
    // 单选插入：在当前列左侧插入
    tableColumns.value.splice(col, 0, ...newColumns)
    
    // 为所有行添加新列
    tableData.value.forEach(row => {
      newColumns.forEach(columnName => {
        row[columnName] = ''
      })
    })
    
    hasChanges.value = true
    ElMessage.success(`在左侧插入 ${colCount} 列成功`)
  }
  
  contextMenuVisible.value = false
}

const handleContextInsertColumnRight = () => {
  const { col } = contextMenuTarget.value
  if (col === -1) return
  
  const colCount = insertColCount.value
  if (colCount <= 0 || colCount > 20) {
    ElMessage.warning('列数必须在1-20之间')
    return
  }
  
  // 创建多列
  const newColumns = []
  for (let i = 0; i < colCount; i++) {
    newColumns.push(`新列${Date.now()}_${i}`)
  }
  
  // 检查是否有选中的单元格
  if (selectedCells.value.length > 0) {
    // 多选插入：获取所有选中单元格的列索引，在最大列索引右侧插入
    const selectedCols = [...new Set(selectedCells.value.map(cell => cell.col))]
    const maxColIndex = Math.max(...selectedCols)
    
    tableColumns.value.splice(maxColIndex + 1, 0, ...newColumns)
    
    // 为所有行添加新列
    tableData.value.forEach(row => {
      newColumns.forEach(columnName => {
        row[columnName] = ''
      })
    })
    
    hasChanges.value = true
    ElMessage.success(`在右侧插入 ${colCount} 列成功`)
    
    // 清除选择
    selectedCells.value = []
  } else {
    // 单选插入：在当前列右侧插入
    tableColumns.value.splice(col + 1, 0, ...newColumns)
    
    // 为所有行添加新列
    tableData.value.forEach(row => {
      newColumns.forEach(columnName => {
        row[columnName] = ''
      })
    })
    
    hasChanges.value = true
    ElMessage.success(`在右侧插入 ${colCount} 列成功`)
  }
  
  contextMenuVisible.value = false
}


const handleContextDeleteRow = () => {
  const { row } = contextMenuTarget.value
  if (row === -1) return
  
  // 检查是否有选中的单元格
  if (selectedCells.value.length > 0) {
    // 多选删除：获取所有选中单元格的行索引，并转换为绝对索引
    const selectedRows = [...new Set(selectedCells.value.map(cell => {
      // 将分页索引转换为绝对索引
      return (currentPage.value - 1) * pageSize.value + cell.row
    }))].sort((a, b) => b - a)
    
    // 从后往前删除，避免索引变化
    selectedRows.forEach(rowIndex => {
      tableData.value.splice(rowIndex, 1)
    })
    
    hasChanges.value = true
    ElMessage.success(`删除 ${selectedRows.length} 行成功`)
    
    // 清除选择
    selectedCells.value = []
  } else {
    // 单选删除：删除当前行
    tableData.value.splice(row, 1)
    
    hasChanges.value = true
    ElMessage.success('删除行成功')
  }
  
  contextMenuVisible.value = false
}

const handleContextDeleteColumn = () => {
  const { col, column } = contextMenuTarget.value
  if (col === -1) return
  
  // 检查是否有选中的单元格
  if (selectedCells.value.length > 0) {
    // 多选删除：获取所有选中单元格的列索引
    const selectedCols = [...new Set(selectedCells.value.map(cell => cell.col))].sort((a, b) => b - a)
    
    // 更新前端数据
    selectedCols.forEach(colIndex => {
      const columnName = tableColumns.value[colIndex]
      tableColumns.value.splice(colIndex, 1)
      tableData.value.forEach(row => {
        delete row[columnName]
      })
    })
    
    hasChanges.value = true
    ElMessage.success(`删除 ${selectedCols.length} 列成功`)
    
    // 清除选择
    selectedCells.value = []
  } else {
    // 单选删除：删除当前列
    tableColumns.value.splice(col, 1)
    tableData.value.forEach(row => {
      delete row[column]
    })
    
    hasChanges.value = true
    ElMessage.success('删除列成功')
  }
  
  contextMenuVisible.value = false
}

const handleContextInsertCell = () => {
  insertCellDialogVisible.value = true
  contextMenuVisible.value = false
}

const handleContextDeleteCell = () => {
  deleteCellDialogVisible.value = true
  contextMenuVisible.value = false
}

const confirmInsertCell = () => {
  const { row, col } = contextMenuTarget.value
  
  // 检查是否有选中的单元格
  if (selectedCells.value.length > 0) {
    // 多选插入：获取所有选中单元格的行列索引，并转换为绝对索引
    const selectedRows = [...new Set(selectedCells.value.map(cell => {
      // 将分页索引转换为绝对索引
      return (currentPage.value - 1) * pageSize.value + cell.row
    }))].sort((a, b) => a - b)
    const selectedCols = [...new Set(selectedCells.value.map(cell => cell.col))].sort((a, b) => a - b)
    
    if (insertCellDirection.value === 'right') {
      // 现有单元格右移
      insertMultipleCellsRight(selectedRows, selectedCols)
    } else {
      // 现有单元格下移
      insertMultipleCellsDown(selectedRows, selectedCols)
    }
    
    // 清除选择
    selectedCells.value = []
  } else {
    // 单选插入
    if (insertCellDirection.value === 'right') {
      insertCellRight(row, col)
    } else {
      insertCellDown(row, col)
    }
  }
  
  insertCellDialogVisible.value = false
}

const insertCellRight = (rowIndex, colIndex) => {
  // 在指定位置插入空单元格，现有单元格右移
  const targetColumn = tableColumns.value[colIndex]
  
  // 保存当前单元格的值
  const currentValue = tableData.value[rowIndex][targetColumn]
  
  // 从右往左移动数据，为新单元格腾出空间
  for (let i = tableColumns.value.length - 1; i > colIndex; i--) {
    const currentColumnName = tableColumns.value[i]
    const prevColumnName = tableColumns.value[i - 1]
    
    // 将前一列的值移到当前列
    tableData.value[rowIndex][currentColumnName] = tableData.value[rowIndex][prevColumnName]
  }
  
  // 在目标位置插入空值
  tableData.value[rowIndex][targetColumn] = ''
  
  hasChanges.value = true
  ElMessage.success('插入单元格成功（右移）')
}

const insertCellDown = (rowIndex, colIndex) => {
  // 在指定位置插入空单元格，现有单元格下移
  const targetColumn = tableColumns.value[colIndex]
  
  // 保存当前单元格的值
  const currentValue = tableData.value[rowIndex][targetColumn]
  
  // 从下往上移动数据，为新单元格腾出空间
  for (let i = tableData.value.length - 1; i > rowIndex; i--) {
    // 将上一行的值移到当前行
    tableData.value[i][targetColumn] = tableData.value[i - 1][targetColumn]
  }
  
  // 在目标位置插入空值
  tableData.value[rowIndex][targetColumn] = ''
  
  hasChanges.value = true
  ElMessage.success('插入单元格成功（下移）')
}

const insertMultipleCellsRight = (selectedRows, selectedCols) => {
  // 多选插入单元格右移
  const cellCount = selectedRows.length * selectedCols.length
  
  // 从右往左移动数据，为多个单元格腾出空间
  // 需要移动的列数等于选中的列数
  for (let i = tableColumns.value.length - 1; i >= selectedCols[0]; i--) {
    const currentColumnName = tableColumns.value[i]
    
    // 对每个选中的行进行移动
    selectedRows.forEach(rowIndex => {
      if (i >= selectedCols[0] + selectedCols.length) {
        // 将前一列的值移到当前列
        const prevColumnName = tableColumns.value[i - selectedCols.length]
        tableData.value[rowIndex][currentColumnName] = tableData.value[rowIndex][prevColumnName]
      } else if (i >= selectedCols[0] && i < selectedCols[0] + selectedCols.length) {
        // 在选中区域插入空值
        tableData.value[rowIndex][currentColumnName] = ''
      }
    })
  }
  
  hasChanges.value = true
  ElMessage.success(`插入 ${cellCount} 个单元格成功（右移）`)
}

const insertMultipleCellsDown = (selectedRows, selectedCols) => {
  // 多选插入单元格下移
  const cellCount = selectedRows.length * selectedCols.length
  
  // 从下往上移动数据，为多个单元格腾出空间
  // 需要移动的行数等于选中的行数
  for (let i = tableData.value.length - 1; i >= selectedRows[0]; i--) {
    // 对每个选中的列进行移动
    selectedCols.forEach(colIndex => {
      const columnName = tableColumns.value[colIndex]
      
      if (i >= selectedRows[0] + selectedRows.length) {
        // 将上一行的值移到当前行
        tableData.value[i][columnName] = tableData.value[i - selectedRows.length][columnName]
      } else if (i >= selectedRows[0] && i < selectedRows[0] + selectedRows.length) {
        // 在选中区域插入空值
        tableData.value[i][columnName] = ''
      }
    })
  }
  
  hasChanges.value = true
  ElMessage.success(`插入 ${cellCount} 个单元格成功（下移）`)
}

const confirmDeleteCell = () => {
  const { row, col } = contextMenuTarget.value
  
  // 检查是否有选中的单元格
  if (selectedCells.value.length > 0) {
    // 多选删除：获取所有选中单元格的行列索引，并转换为绝对索引
    const selectedRows = [...new Set(selectedCells.value.map(cell => {
      // 将分页索引转换为绝对索引
      return (currentPage.value - 1) * pageSize.value + cell.row
    }))].sort((a, b) => a - b)
    const selectedCols = [...new Set(selectedCells.value.map(cell => cell.col))].sort((a, b) => a - b)
    
    if (deleteCellDirection.value === 'left') {
      // 现有单元格左移
      deleteMultipleCellsLeft(selectedRows, selectedCols)
    } else {
      // 现有单元格上移
      deleteMultipleCellsUp(selectedRows, selectedCols)
    }
    
    // 清除选择
    selectedCells.value = []
  } else {
    // 单选删除
    if (deleteCellDirection.value === 'left') {
      deleteCellLeft(row, col)
    } else {
      deleteCellUp(row, col)
    }
  }
  
  deleteCellDialogVisible.value = false
}

const deleteCellLeft = (rowIndex, colIndex) => {
  // 删除指定位置的单元格，现有单元格左移
  const targetColumn = tableColumns.value[colIndex]
  
  // 将该列及其右侧所有列的数据向左移动
  for (let i = colIndex; i < tableColumns.value.length - 1; i++) {
    const currentColumnName = tableColumns.value[i]
    const nextColumnName = tableColumns.value[i + 1]
    
    tableData.value[rowIndex][currentColumnName] = tableData.value[rowIndex][nextColumnName]
  }
  
  // 最后一列设为空
  const lastColumn = tableColumns.value[tableColumns.value.length - 1]
  tableData.value[rowIndex][lastColumn] = ''
  
  hasChanges.value = true
  ElMessage.success('删除单元格成功（左移）')
}

const deleteCellUp = (rowIndex, colIndex) => {
  // 删除指定位置的单元格，现有单元格上移
  const targetColumn = tableColumns.value[colIndex]
  
  // 将该行及其下方所有行的数据向上移动
  for (let i = rowIndex; i < tableData.value.length - 1; i++) {
    tableData.value[i][targetColumn] = tableData.value[i + 1][targetColumn]
  }
  
  // 最后一行设为空
  const lastRow = tableData.value.length - 1
  tableData.value[lastRow][targetColumn] = ''
  
  hasChanges.value = true
  ElMessage.success('删除单元格成功（上移）')
}

const deleteMultipleCellsLeft = (selectedRows, selectedCols) => {
  // 多选删除单元格左移
  const cellCount = selectedRows.length * selectedCols.length
  
  // 从左往右移动数据，删除多个单元格
  for (let i = selectedCols[0]; i < tableColumns.value.length; i++) {
    const currentColumnName = tableColumns.value[i]
    
    // 对每个选中的行进行移动
    selectedRows.forEach(rowIndex => {
      if (i < selectedCols[0] + selectedCols.length) {
        // 在选中区域，将右侧列的值移到当前列
        const nextColumnName = tableColumns.value[i + selectedCols.length]
        if (nextColumnName) {
          tableData.value[rowIndex][currentColumnName] = tableData.value[rowIndex][nextColumnName]
        } else {
          // 如果右侧没有列了，设为空
          tableData.value[rowIndex][currentColumnName] = ''
        }
      } else {
        // 在选中区域右侧，将右侧列的值移到当前列
        const nextColumnName = tableColumns.value[i + selectedCols.length]
        if (nextColumnName) {
          tableData.value[rowIndex][currentColumnName] = tableData.value[rowIndex][nextColumnName]
        } else {
          // 如果右侧没有列了，设为空
          tableData.value[rowIndex][currentColumnName] = ''
        }
      }
    })
  }
  
  hasChanges.value = true
  ElMessage.success(`删除 ${cellCount} 个单元格成功（左移）`)
}

const deleteMultipleCellsUp = (selectedRows, selectedCols) => {
  // 多选删除单元格上移
  const cellCount = selectedRows.length * selectedCols.length
  
  // 从上往下移动数据，删除多个单元格
  for (let i = selectedRows[0]; i < tableData.value.length; i++) {
    // 对每个选中的列进行移动
    selectedCols.forEach(colIndex => {
      const columnName = tableColumns.value[colIndex]
      
      if (i < selectedRows[0] + selectedRows.length) {
        // 在选中区域，将下方行的值移到当前行
        const nextRowIndex = i + selectedRows.length
        if (nextRowIndex < tableData.value.length) {
          tableData.value[i][columnName] = tableData.value[nextRowIndex][columnName]
        } else {
          // 如果下方没有行了，设为空
          tableData.value[i][columnName] = ''
        }
      } else {
        // 在选中区域下方，将下方行的值移到当前行
        const nextRowIndex = i + selectedRows.length
        if (nextRowIndex < tableData.value.length) {
          tableData.value[i][columnName] = tableData.value[nextRowIndex][columnName]
        } else {
          // 如果下方没有行了，设为空
          tableData.value[i][columnName] = ''
        }
      }
    })
  }
  
  hasChanges.value = true
  ElMessage.success(`删除 ${cellCount} 个单元格成功（上移）`)
}

// 内联编辑方法
const startEdit = (rowIndex, column, row) => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  
  editingCell.value = {
    rowIndex,
    column,
    value: row[column] || '',
    originalValue: row[column] || ''
  }
  
  // 确保编辑框获得焦点
  nextTick(() => {
    setTimeout(() => {
      const inputElement = document.querySelector('.inline-edit-input .el-input__inner')
      if (inputElement) {
        inputElement.focus()
        inputElement.select()
      }
    }, 50)
  })
}

const saveEdit = () => {
  if (editingCell.value.rowIndex === -1) return
  
  const { rowIndex, column, value, originalValue } = editingCell.value
  
  // 如果值没有变化，直接退出编辑
  if (value === originalValue) {
    cancelEdit()
    return
  }
  
  // 更新本地数据
  const actualRowIndex = (currentPage.value - 1) * pageSize.value + rowIndex
  tableData.value[actualRowIndex][column] = value
  
  // 标记有变更
  hasChanges.value = true
  
  // 清除编辑状态
  editingCell.value = {
    rowIndex: -1,
    column: '',
    value: '',
    originalValue: '',
    saving: false
  }
}

const cancelEdit = () => {
  if (editingCell.value.rowIndex === -1) return
  
  const { rowIndex, column, originalValue } = editingCell.value
  
  // 恢复原值
  const actualRowIndex = (currentPage.value - 1) * pageSize.value + rowIndex
  tableData.value[actualRowIndex][column] = originalValue
  
  // 清除编辑状态
  editingCell.value = {
    rowIndex: -1,
    column: '',
    value: '',
    originalValue: ''
  }
}

// 添加双击延迟处理
let clickTimer = null
let isDoubleClick = false

const handleCellClick = (rowIndex, column, row, event) => {
  // 如果正在编辑，先保存
  if (editingCell.value.rowIndex !== -1) {
    // 检查是否是点击了其他单元格
    if (editingCell.value.rowIndex !== rowIndex || editingCell.value.column !== column) {
      saveEdit()
    }
    return
  }
  
  // 直接处理单击选中，不等待双击
  // 确保rowIndex是数字
  const actualRowIndex = typeof rowIndex === 'object' ? rowIndex.$index : rowIndex
  const colIndex = tableColumns.value.indexOf(column)
  
  // 清除之前的选择
  selectedCells.value = []
  
  // 选中当前单元格
  selectedCells.value.push({
    row: actualRowIndex,
    col: colIndex,
    column: column,
    data: row
  })
  
  // 更新选择状态
  selectionStart.value = { row: actualRowIndex, col: colIndex }
  selectionEnd.value = { row: actualRowIndex, col: colIndex }
}

const handleCellDoubleClick = (rowIndex, column, row, event) => {
  // 清除单击定时器
  if (clickTimer) {
    clearTimeout(clickTimer)
    clickTimer = null
  }
  
  // 标记为双击
  isDoubleClick = true
  
  // 执行双击编辑
  startEdit(rowIndex, column, row)
  
  // 延迟重置双击标记
  setTimeout(() => {
    isDoubleClick = false
  }, 100)
}

const handleCellBlur = (row, column, cell, event) => {
  // 可以在这里添加失焦处理逻辑
}

// 表头编辑方法
const startHeaderEdit = (column) => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  
  editingHeader.value = {
    column,
    value: column,
    originalValue: column
  }
  
  nextTick(() => {
    if (headerEditInput.value && headerEditInput.value.focus) {
      headerEditInput.value.focus()
      if (headerEditInput.value.select) {
        headerEditInput.value.select()
      }
    }
  })
}

const saveHeaderEdit = () => {
  if (editingHeader.value.column === '') return
  
  const { column, value, originalValue } = editingHeader.value
  
  if (value === originalValue) {
    cancelHeaderEdit()
    return
  }
  
  if (value.trim() === '') {
    ElMessage.warning('列名不能为空')
    return
  }
  
  if (tableColumns.value.includes(value) && value !== originalValue) {
    ElMessage.warning('列名已存在')
    return
  }
  
  // 更新前端数据
  const columnIndex = tableColumns.value.indexOf(column)
  if (columnIndex !== -1) {
    tableColumns.value[columnIndex] = value
    
    // 更新所有行的数据
    tableData.value.forEach(row => {
      if (row.hasOwnProperty(column)) {
        row[value] = row[column]
        delete row[column]
      }
    })
  }
  
  hasChanges.value = true
  ElMessage.success('列名修改成功')
  
  editingHeader.value = {
    column: '',
    value: '',
    originalValue: ''
  }
}

const cancelHeaderEdit = () => {
  editingHeader.value = {
    column: '',
    value: '',
    originalValue: ''
  }
}


const handleHeaderClick = (column, event) => {
  // 可以在这里添加表头点击处理逻辑
}

// 批量操作方法
const handleSave = async () => {
  if (!hasChanges.value) {
    ElMessage.info('没有需要保存的更改')
    return
  }
  
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  
  if (dataMode.value === 'json') {
    // JSON模式：保存到后端
    await saveJsonFile()
    return
  }
  
  // Excel模式：原有的保存逻辑
  // 验证必要字段
  if (!activeSheet.value || activeSheet.value.trim() === '') {
    ElMessage.warning('请先选择工作表')
    return
  }
  
  if (!tableColumns.value || tableColumns.value.length === 0) {
    ElMessage.warning('表格列不能为空')
    return
  }
  
  // 提取文件前缀
  const filePrefix = selectedFile.value.split('_')[0]
  if (!filePrefix || filePrefix.trim() === '') {
    ElMessage.error('文件名格式不正确，无法提取文件前缀')
    return
  }
  
  try {
    saving.value = true
    
    // 确保列名都是字符串类型
    const columnsArray = tableColumns.value.map(col => {
      if (col === null || col === undefined) {
        return ''
      }
      return String(col)
    })
    
    // 准备数据：将所有行数据转换为二维数组
    const dataArray = tableData.value.map(row => 
      columnsArray.map(column => {
        const value = row[column]
        // 确保所有值都是字符串类型，null/undefined/NaN 转换为空字符串
        if (value === null || value === undefined || (typeof value === 'number' && isNaN(value))) {
          return ''
        }
        return String(value)
      })
    )
    
    // 验证数据数组不为空
    if (dataArray.length === 0) {
      ElMessage.warning('表格数据不能为空')
      saving.value = false
      return
    }
    
    // 验证每行数据的长度与列数一致
    const columnCount = columnsArray.length
    for (let i = 0; i < dataArray.length; i++) {
      if (dataArray[i].length !== columnCount) {
        ElMessage.error(`第 ${i + 1} 行数据长度与列数不匹配`)
        saving.value = false
        return
      }
    }
    
    // 构建请求数据，确保所有字段都是正确的类型
    const requestData = {
      sheet_name: String(activeSheet.value).trim(),
      columns: columnsArray,
      data: dataArray,
      file_name_prefix: String(filePrefix).trim()
    }
    
    // 最终验证：确保没有空值
    if (!requestData.sheet_name) {
      ElMessage.error('工作表名称不能为空')
      saving.value = false
      return
    }
    if (!requestData.file_name_prefix) {
      ElMessage.error('文件前缀不能为空')
      saving.value = false
      return
    }
    if (requestData.columns.length === 0) {
      ElMessage.error('列数组不能为空')
      saving.value = false
      return
    }
    
    console.log('Sending save request:', {
      sheet_name: requestData.sheet_name,
      columns_count: requestData.columns.length,
      columns: requestData.columns,
      data_rows: requestData.data.length,
      data_sample: requestData.data.slice(0, 2),
      file_name_prefix: requestData.file_name_prefix
    })
    
    // 调用新的保存整个文件的API
    await basicDataApi.saveFile(requestData)
    
    // 重置状态
    hasChanges.value = false
    pendingChanges.value = []
    
    // 重新加载文件列表以获取更新后的文件名
    await loadFileList()
    
    // 更新selectedFile为新的文件名（.xlsx格式）
    const oldFileName = selectedFile.value
    // 只有当文件名以.xls结尾时才替换，避免重复替换
    const newFileName = oldFileName.endsWith('.xls') ? oldFileName.replace(/\.xls$/, '.xlsx') : oldFileName
    if (newFileName !== oldFileName) {
      selectedFile.value = newFileName
    }
    
    ElMessage.success('保存成功')
    
  } catch (error) {
    // 更详细的错误信息
    let errorMessage = '保存失败'
    if (error.response) {
      // 422 错误通常是数据验证失败
      if (error.response.status === 422) {
        const errorDetails = error.response.data
        console.error('Validation error details:', errorDetails)
        
        // 解析验证错误详情
        if (errorDetails.detail && Array.isArray(errorDetails.detail)) {
          const errorMessages = errorDetails.detail.map(err => {
            if (typeof err === 'string') return err
            if (err.msg) return err.msg
            if (err.loc && err.msg) return `${err.loc.join('.')}: ${err.msg}`
            return JSON.stringify(err)
          }).join('; ')
          errorMessage = `保存失败: ${errorMessages}`
        } else if (errorDetails.detail) {
          errorMessage = `保存失败: ${typeof errorDetails.detail === 'string' ? errorDetails.detail : JSON.stringify(errorDetails.detail)}`
        } else {
          errorMessage = `保存失败: 数据验证错误。请检查工作表名称、列名和数据是否正确`
        }
      } else if (error.response.data && error.response.data.detail) {
        errorMessage = `保存失败: ${error.response.data.detail}`
      }
    }
    ElMessage.error(errorMessage)
    console.error('Save error:', error)
    console.error('Request data:', {
      sheet_name: activeSheet.value,
      columns: tableColumns.value,
      data_length: dataArray.length,
      data_sample: dataArray.slice(0, 2),
      file_name_prefix: filePrefix
    })
  } finally {
    saving.value = false
  }
}

// 保存JSON文件（下载）
const saveJsonFile = async () => {
  try {
    if (!selectedFile.value) {
      ElMessage.warning('请先选择文件')
      return
    }
    if (!props.category) {
      ElMessage.error('缺少分类信息')
      return
    }

    saving.value = true
    
    // 将对象数组转换回二维数组格式
    const jsonArray = [
      tableColumns.value, // 第一行是表头
      ...tableData.value.map(row => 
        tableColumns.value.map(col => row[col] || '')
      )
    ]
    
    // 调用后端保存（覆盖）JSON
    await basicDataApi.saveJsonFile({
      category: props.category,
      filename: selectedFile.value,
      data: jsonArray
    })
    
    hasChanges.value = false
    ElMessage.success('JSON保存成功')
    
    // 保存后刷新列表，保持选中
    await loadFileList()
    if (selectedFile.value) {
      await handleFileChange(selectedFile.value)
    }
    
  } catch (error) {
    let msg = '保存JSON文件失败'
    if (error?.response?.data?.detail) {
      msg = `保存JSON文件失败: ${error.response.data.detail}`
    }
    ElMessage.error(msg)
    console.error('Save JSON file error:', error)
  } finally {
    saving.value = false
  }
}

const handleExport = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  
  if (dataMode.value === 'json') {
    // JSON模式：直接下载JSON文件
    await exportJsonFile()
    return
  }
  
  // Excel模式：原有的导出逻辑
  try {
    exporting.value = true
    
    // 获取完整的文件内容（包含所有工作表）
    const response = await basicDataApi.getFileContent(selectedFile.value, props.category)
    const data = response.data
    
    if (!data.sheets) {
      ElMessage.error('无法获取文件内容')
      return
    }
    
    // 创建Excel文件
    const XLSX = await import('xlsx')
    
    // 创建工作簿
    const wb = XLSX.utils.book_new()
    
    // 遍历所有工作表
    for (const [sheetName, sheetData] of Object.entries(data.sheets)) {
      const columns = sheetData.columns || []
      const dataRows = sheetData.data || []
      
      // 创建工作表数据
      const wsData = [
        columns, // 表头
        ...dataRows.map(row => 
          columns.map(column => row[column] || '')
        ) // 数据行
      ]
      
      // 创建工作表
      const ws = XLSX.utils.aoa_to_sheet(wsData)
      
      // 添加工作表到工作簿
      XLSX.utils.book_append_sheet(wb, ws, sheetName)
    }
    
    // 导出文件
    const fileName = `${selectedFile.value}_完整导出_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.xlsx`
    XLSX.writeFile(wb, fileName)
    
    ElMessage.success('完整表格导出成功')
    
  } catch (error) {
    ElMessage.error('导出失败')
    console.error('Export error:', error)
  } finally {
    exporting.value = false
  }
}

// 导出JSON文件
const exportJsonFile = async () => {
  try {
    exporting.value = true
    
    // 如果已经加载了数据，直接使用当前数据
    if (tableData.value.length > 0 && tableColumns.value.length > 0) {
      // 将对象数组转换回二维数组格式
      const jsonArray = [
        tableColumns.value, // 第一行是表头
        ...tableData.value.map(row => 
          tableColumns.value.map(col => row[col] || '')
        )
      ]
      
      // 创建JSON字符串
      const jsonString = JSON.stringify(jsonArray, null, 2)
      
      // 创建Blob对象
      const blob = new Blob([jsonString], { type: 'application/json' })
      
      // 创建下载链接
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = selectedFile.value
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      ElMessage.success('JSON文件导出成功')
    } else {
      // 如果数据未加载，直接从服务器读取并下载
      const response = await fetch(`/data/BaseData/${selectedFile.value}`)
      if (!response.ok) {
        throw new Error(`无法获取JSON文件: ${selectedFile.value} (HTTP ${response.status})`)
      }
      
      // 检查响应内容类型
      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text()
        console.error('Response is not JSON:', text.substring(0, 200))
        throw new Error(`文件 ${selectedFile.value} 不是有效的JSON文件`)
      }
      
      const jsonData = await response.json()
      const jsonString = JSON.stringify(jsonData, null, 2)
      const blob = new Blob([jsonString], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = selectedFile.value
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      ElMessage.success('JSON文件导出成功')
    }
    
  } catch (error) {
    ElMessage.error('导出JSON文件失败')
    console.error('Export JSON file error:', error)
  } finally {
    exporting.value = false
  }
}

const handleDeleteFile = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除文件 "${selectedFile.value}" 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    deleting.value = true
    
    // 调用删除API（根据模式区分）
    if (dataMode.value === 'json') {
      await basicDataApi.deleteJsonFile(props.category, selectedFile.value)
    } else {
      await basicDataApi.deleteFile(selectedFile.value, props.category)
    }
    
    // 重新加载文件列表
    await loadFileList()
    
    // 重置状态
    selectedFile.value = ''
    tableData.value = []
    tableColumns.value = []
    sheetNames.value = []
    activeSheet.value = ''
    hasChanges.value = false
    
    ElMessage.success('删除成功')
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('Delete error:', error)
    }
  } finally {
    deleting.value = false
  }
}


const handleFileChange = async (filename) => {
  if (!filename) {
    resetTable()
    return
  }
  
  try {
    loading.value = true
    
    if (dataMode.value === 'json') {
      // JSON模式：读取JSON文件
      await loadJsonFile(filename)
    } else {
      // Excel模式：从后端API获取
      const response = await basicDataApi.getFileContent(filename, props.category)
      const data = response.data
      
      if (data.sheets) {
        sheetNames.value = Object.keys(data.sheets)
        if (sheetNames.value.length > 0) {
          activeSheet.value = sheetNames.value[0]
          loadSheetData(data.sheets[activeSheet.value])
        }
      }
    }
  } catch (error) {
    ElMessage.error('加载文件内容失败')
    console.error('Load file content error:', error)
  } finally {
    loading.value = false
  }
}

// 加载JSON文件（老版本方式）
const loadJsonFile = async (filename) => {
  try {
    // 读取JSON文件（从public目录，使用绝对路径）
    const response = await fetch(`/data/BaseData/${filename}`)
    if (!response.ok) {
      throw new Error(`Failed to load JSON file: ${filename} (HTTP ${response.status})`)
    }
    
    // 检查响应内容类型
    const contentType = response.headers.get('content-type')
    if (!contentType || !contentType.includes('application/json')) {
      const text = await response.text()
      console.error('Response is not JSON:', text.substring(0, 200))
      throw new Error(`文件 ${filename} 不是有效的JSON文件`)
    }
    
    const jsonData = await response.json()
    
    // JSON数据是二维数组格式：第一行是表头，后续行是数据
    if (!Array.isArray(jsonData) || jsonData.length < 1) {
      ElMessage.warning('JSON文件格式不正确')
      return
    }
    
    // 第一行是表头
    const headers = jsonData[0]
    // 后续行是数据
    const dataRows = jsonData.slice(1)
    
    // 将二维数组转换为对象数组
    tableColumns.value = headers.map(String) // 确保列名是字符串
    tableData.value = dataRows.map(row => {
      const obj = {}
      headers.forEach((header, index) => {
        obj[String(header)] = row[index] !== undefined && row[index] !== null ? String(row[index]) : ''
      })
      return obj
    })
    
    // JSON模式没有工作表概念，设置为空
    sheetNames.value = []
    activeSheet.value = ''
    currentPage.value = 1
    hasChanges.value = false
    
  } catch (error) {
    ElMessage.error(`加载JSON文件失败: ${error.message}`)
    console.error('Load JSON file error:', error)
  }
}

const handleSheetChange = () => {
  if (selectedFile.value && activeSheet.value) {
    loadCurrentSheetData()
  }
}

const loadSheetData = (sheetData) => {
  if (sheetData) {
    // 确保所有列名都是字符串类型，避免数字列名导致 Element Plus 警告
    tableColumns.value = (sheetData.columns || []).map(col => String(col))
    tableData.value = sheetData.data || []
    currentPage.value = 1
  }
}

const loadCurrentSheetData = async () => {
  if (!selectedFile.value || !activeSheet.value) return
  
  try {
    loading.value = true
    const response = await basicDataApi.getFileContent(selectedFile.value, props.category)
    const data = response.data
    
    if (data.sheets && data.sheets[activeSheet.value]) {
      loadSheetData(data.sheets[activeSheet.value])
    }
  } catch (error) {
    ElMessage.error('加载工作表数据失败')
    console.error('Load sheet data error:', error)
  } finally {
    loading.value = false
  }
}

const beforeUpload = (file) => {
  if (dataMode.value === 'json') {
    const isJson = file.type === 'application/json' || file.name.toLowerCase().endsWith('.json')
    if (!isJson) {
      ElMessage.error('只能上传JSON文件!')
      return false
    }
    const isLt20M = file.size / 1024 / 1024 < 20
    if (!isLt20M) {
      ElMessage.error('JSON 文件大小不能超过20MB!')
      return false
    }
    return true
  }

  // Excel 模式校验
  const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                  file.type === 'application/vnd.ms-excel'
  if (!isExcel) {
    ElMessage.error('只能上传Excel文件!')
    return false
  }
  
  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过50MB!')
    return false
  }
  
  return true
}

const handleFileUpload = async (file) => {
  if (!beforeUpload(file.raw)) return
  
  try {
    uploading.value = true

    if (dataMode.value === 'json') {
      const response = await basicDataApi.uploadJsonFile(file.raw, props.category)
      ElMessage.success('JSON 上传成功')
      await loadFileList()
      const uploaded = response.data.relative_path || response.data.filename
      if (uploaded) {
        selectedFile.value = uploaded
        await handleFileChange(uploaded)
      }
    } else {
      const response = await basicDataApi.uploadFile(file.raw, props.category)
      ElMessage.success('文件上传成功')
      await loadFileList()
      // 自动选择新上传的文件
      if (response.data.filename) {
        selectedFile.value = response.data.filename
        await handleFileChange(response.data.filename)
      }
    }
  } catch (error) {
    ElMessage.error('文件上传失败')
    console.error('Upload error:', error)
  } finally {
    uploading.value = false
  }
}

const handleAddRow = () => {
  isEdit.value = false
  editRowIndex.value = -1
  formData.value = {}
  
  // 初始化表单数据
  tableColumns.value.forEach(column => {
    formData.value[column] = ''
  })
  
  editDialogVisible.value = true
}

const handleEdit = (index, row) => {
  isEdit.value = true
  editRowIndex.value = (currentPage.value - 1) * pageSize.value + index
  formData.value = { ...row }
  editDialogVisible.value = true
}

const handleDelete = async (index, row) => {
  try {
    await ElMessageBox.confirm('确定要删除这条数据吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const rowIndex = (currentPage.value - 1) * pageSize.value + index
    
    const deleteData = {
      row_index: rowIndex,
      sheet_name: activeSheet.value,
      file_name_prefix: selectedFile.value.split('_')[0] // 使用文件ID作为前缀
    }
    
    await basicDataApi.deleteRow(deleteData)
    ElMessage.success('删除成功')
    
    // 重新加载数据
    await loadCurrentSheetData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('Delete error:', error)
    }
  }
}


const handlePageChange = (page) => {
  currentPage.value = page
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

// 初始化表单验证规则
const initFormRules = () => {
  const rules = {}
  tableColumns.value.forEach(column => {
    rules[column] = [
      { required: true, message: `请输入${column}`, trigger: 'blur' }
    ]
  })
  formRules.value = rules
}

// 监听器
watch(() => props.category, (newCategory) => {
  if (newCategory) {
    loadFileList()
    resetTable()
  }
}, { immediate: true })

// 监听数据模式变化
watch(dataMode, () => {
  resetTable()
  loadFileList()
})

// 全局点击事件监听
const handleGlobalClick = () => {
  contextMenuVisible.value = false
}

// 组件挂载时添加全局事件监听
onMounted(() => {
  document.addEventListener('click', handleGlobalClick)
})

// 组件卸载时移除全局事件监听
onUnmounted(() => {
  document.removeEventListener('click', handleGlobalClick)
})

// 监听表格列变化，更新表单验证规则
watch(tableColumns, () => {
  initFormRules()
}, { deep: true })
</script>

<style scoped>
.basic-data-table {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid #e4e7ed;
  background-color: #f5f7fa;
}

.header-left {
  display: flex;
  align-items: center;
}

.category-title {
  font-weight: bold;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
}

.sheet-header {
  padding: 10px 20px;
  border-bottom: 1px solid #e4e7ed;
  background-color: #fafafa;
}

.sheet-selector {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #606266;
}

.table-main {
  flex: 1;
  padding: 20px;
  overflow: auto;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table th) {
  background-color: #f5f7fa;
  color: #303133;
  font-weight: bold;
}

:deep(.el-pagination) {
  margin-top: 20px;
}

/* 内联编辑样式 */
.cell-content {
  position: relative;
  min-height: 32px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cell-content:hover {
  background-color: #f5f7fa;
  border-radius: 4px;
}

.cell-content.editing {
  background-color: #e6f7ff;
  border: 2px solid #1890ff;
  border-radius: 4px;
  padding: 2px;
}

.cell-text {
  flex: 1;
  padding: 4px 8px;
  word-break: break-all;
  line-height: 1.4;
}

.inline-edit-input {
  width: 100%;
}

.inline-edit-input :deep(.el-input__wrapper) {
  border: none;
  box-shadow: none;
  background: transparent;
  padding: 0;
}

.inline-edit-input :deep(.el-input__inner) {
  border: none;
  background: transparent;
  padding: 4px 8px;
  font-size: 14px;
  line-height: 1.4;
}

.inline-edit-input :deep(.el-input__inner):focus {
  border: none;
  box-shadow: none;
}

/* 表格行悬停效果 */
:deep(.el-table__row:hover .cell-content) {
  background-color: #f5f7fa;
}

:deep(.el-table__row:hover .cell-content.editing) {
  background-color: #e6f7ff;
}

/* 表头编辑样式 */
.header-cell {
  position: relative;
  min-height: 32px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 4px 8px;
}

.header-cell:hover {
  background-color: #f5f7fa;
  border-radius: 4px;
}

.header-cell.editing {
  background-color: #e6f7ff;
  border: 2px solid #1890ff;
  border-radius: 4px;
  padding: 2px;
}

.header-text {
  flex: 1;
  font-weight: 600;
  color: #303133;
  word-break: break-all;
  line-height: 1.4;
}

.header-edit-input {
  width: 100%;
}

.header-edit-input :deep(.el-input__wrapper) {
  border: none;
  box-shadow: none;
  background: transparent;
  padding: 0;
}

.header-edit-input :deep(.el-input__inner) {
  border: none;
  background: transparent;
  padding: 4px 8px;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  color: #303133;
}

.header-edit-input :deep(.el-input__inner):focus {
  border: none;
  box-shadow: none;
}


/* 操作按钮样式优化 */
.action-buttons {
  display: flex;
  align-items: center;
  gap: 10px;
}

.action-buttons .el-button {
  margin-left: 0;
}

/* 表格多选样式 */
:deep(.el-table__selection-column) {
  text-align: center;
}

/* 框选样式 */
.selectable-table {
  user-select: none;
}

.cell-content.selected {
  background-color: #e6f7ff !important;
  border: 2px solid #1890ff !important;
  box-shadow: 0 0 0 2px #1890ff !important;
  border-radius: 4px !important;
}

/* 确保选中状态优先级最高 */
:deep(.cell-content.selected) {
  background-color: #e6f7ff !important;
  border: 2px solid #1890ff !important;
  box-shadow: 0 0 0 2px #1890ff !important;
}

.cell-content.selection-start {
  background-color: #e6f7ff !important;
  border: 2px solid #1890ff !important;
}

.cell-content.selection-end {
  background-color: #e6f7ff !important;
  border: 2px solid #1890ff !important;
}

/* 右键菜单样式 */
.context-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  background: transparent;
}

.context-menu {
  position: absolute;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 8px 0;
  min-width: 200px;
  max-height: 400px;
  overflow-y: auto;
  z-index: 10000;
  /* 确保菜单始终可见 */
  max-width: calc(100vw - 20px);
  max-height: calc(100vh - 20px);
}

.menu-group {
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 4px;
  padding-bottom: 4px;
}

.menu-group:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.menu-group-title {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  font-weight: 600;
  color: #606266;
  font-size: 13px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 4px;
}

.menu-group-title .el-icon {
  margin-right: 8px;
  font-size: 14px;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  font-size: 14px;
  color: #303133;
}

.menu-item:hover {
  background-color: #f5f7fa;
}

.menu-item .el-icon {
  margin-right: 8px;
  font-size: 16px;
  color: #606266;
}

/* 删除按钮样式 */
:deep(.el-button--danger.is-circle) {
  width: 28px;
  height: 28px;
  padding: 0;
}

:deep(.el-button--danger.is-circle:hover) {
  transform: scale(1.1);
  transition: transform 0.2s ease;
}
</style>
