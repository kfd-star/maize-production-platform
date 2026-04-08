<script setup>
import { ref, onBeforeUnmount } from 'vue'
import { ElMessage, ElLoading, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { runEnKF, runUKF, runPF, runNLS4DVar, getParams, updateParams, getConfig, updateConfig, listControlFiles, chooseControlFile, getOptions, getDescriptions, startTask as apiStartTask, getTask as apiGetTask, cancelTask as apiCancelTask, getLAITasks, getLAITask, deleteLAITask, downloadLAIResult, previewLAIResult } from '@/api/maizeSM.js'

const router = useRouter()

// 页面状态
const loading = ref(false)
const controller = ref(null)
const loadingService = ref(null)
// 任务模式状态
const taskId = ref('')
const taskStatus = ref('idle') // idle|running|finished|failed|canceled
const taskTimer = ref(null)
const taskRunning = ref(false)
const loadingText = ref('')
const loadingKey = ref(0)

// 任务历史状态
const showTaskHistory = ref(false)
const showTaskDetail = ref(false)
const selectedTask = ref(null)
const taskHistory = ref([])
const taskHistoryLoading = ref(false)
const taskDetailData = ref(null)
const taskDetailLoading = ref(false)
const activeCollapseItems = ref([])
const activeOutputCollapseItems = ref([])
// 将选中文件拷贝为内存中的稳定副本，避免 ERR_UPLOAD_FILE_CHANGED
const toStableFile = async (file) => {
  if (!file) return file
  try {
    const buf = await file.arrayBuffer()
    const copy = new File([new Uint8Array(buf)], file.name, { type: file.type || 'text/csv' })
    return copy
  } catch (_) {
    return file
  }
}
const selectedFile = ref(null)
const stableFile = ref(null)
const selectedFileName = ref('')
const fileInput = ref(null)

// 算法选择
const algo = ref('EnKF')
const algoOptions = [
  { label: 'EnKF（集合卡尔曼滤波）', value: 'EnKF' },
  { label: 'UKF（无迹卡尔曼滤波）', value: 'UKF' },
  { label: 'PF（粒子滤波）', value: 'PF' },
  { label: 'NLS-4DVAR（四维变分）', value: 'NLS4DVar' },
]

// 参数模型
const params = ref({})
const currentBadges = ref([])

// 各算法参数schema（顺序+标签），用于前端固定渲染
const paramSchemas = {
  EnKF: [
    { key: 'en_num', label: '集合成员数量 (en_num)', type: 'int', def: 25 },
    { key: 'err_lai_o', label: '观测误差协方差 (err_lai_o)', type: 'float', def: 0.01 },
    { key: 'err_lai', label: '模型误差协方差 (err_lai)', type: 'float', def: 1.28 },
  ],
  UKF: [
    { key: 'en_num', label: '集合成员数量 (en_num)', type: 'int', def: 1 },
    { key: 'alpha', label: '缩放参数 (alpha)', type: 'float', def: 4.0 },
    { key: 'beta', label: '先验分布参数 (beta)', type: 'float', def: 1.0 },
    { key: 'kappa', label: '缩放参数 (kappa)', type: 'float', def: 0.0 },
    { key: 'err_lai_o', label: '观测误差协方差 (err_lai_o)', type: 'float', def: 2.0 },
    { key: 'err_lai', label: '模型误差协方差 (err_lai)', type: 'float', def: 0.5 },
  ],
  PF: [
    { key: 'en_num', label: '粒子数量 (en_num)', type: 'int', def: 40 },
    { key: 'resample_threshold', label: '重采样阈值 (resample_threshold)', type: 'int', def: 30 },
    { key: 'noise_std', label: '噪声标准差 (noise_std)', type: 'float', def: 0.15 },
  ],
  NLS4DVar: [
    { key: 'b_time_steps', label: '背景段长度 (b_time_steps)', type: 'int', def: 35 },
    { key: 'time_steps', label: '同化窗口长度 (time_steps)', type: 'int', def: 90 },
    { key: 'en_num', label: '集合成员数量 (en_num)', type: 'int', def: 25 },
    { key: 'i_max', label: 'NLS迭代次数 (i_max)', type: 'int', def: 13 },
    { key: 'R_scalar', label: '观测误差方差标量 (R_scalar)', type: 'float', def: 0.01 },
    { key: 'nass', label: '同化窗口数量 (nass)', type: 'int', def: 1 },
  ],
}
const config = ref({ control_file: '', ET_model: 'PT', num_cores: 'submax' })
const controlFiles = ref([])
const options = ref({ ET_model: ['PT'], num_cores: ['submax'] })

// 初始化加载参数与配置
const init = async () => {
  try {
    const [cfgRes, optRes] = await Promise.all([getConfig(), getOptions()])
    config.value = cfgRes.data
    options.value = optRes.data
    await fetchControlFiles()
    await fetchAlgoParams()
    await fetchDescriptions()
  } catch (e) {
    // 忽略
  }
}

const fetchAlgoParams = async () => {
  // 先用 schema 默认值立即渲染
  const schema = paramSchemas[algo.value] || []
  const base = {}
  schema.forEach(s => { base[s.key] = s.def })
  params.value = { ...base }
  renderCurrentBadges()
  // 再尝试获取后端当前参数覆盖
  try {
    const res = await getParams(algo.value)
    if (res && res.data && typeof res.data === 'object') {
      params.value = Object.assign({ ...base }, res.data)
      renderCurrentBadges()
    }
  } catch (e) {
    // 保留默认值，不打断显示
  }
}

const fetchControlFiles = async () => {
  try {
    const res = await listControlFiles()
    controlFiles.value = res.data.files || []
  } catch (e) {}
}

const onAlgoChange = async () => {
  await fetchAlgoParams()
}

// 文件选择
const handleFileChange = async (ev) => {
  const file = ev.target.files[0]
  selectedFile.value = file
  selectedFileName.value = file ? file.name : ''
  // 生成稳定副本，供后续多次上传使用（避免 ERR_UPLOAD_FILE_CHANGED）
  try {
    const buf = await file.arrayBuffer()
    stableFile.value = new File([new Uint8Array(buf)], file.name, { type: file.type || 'text/csv' })
  } catch (_) {
    stableFile.value = file
  }
}
const triggerFile = () => fileInput.value && fileInput.value.click()

// 参数更新
const saveParams = async () => {
  try {
    // 只提交 schema 定义的字段，并做类型规范化
    const schema = paramSchemas[algo.value] || []
    const payload = {}
    schema.forEach(s => {
      let v = params.value[s.key]
      if (s.type === 'int') {
        v = parseInt(String(v || s.def), 10)
        if (Number.isNaN(v)) v = s.def
      } else if (s.type === 'float') {
        v = parseFloat(String(v ?? s.def))
        if (Number.isNaN(v)) v = s.def
      }
      payload[s.key] = v
    })
    await updateParams(algo.value, payload)
    ElMessage.success('参数已保存')
    params.value = { ...payload }
    renderCurrentBadges()
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.response?.data?.error || '参数保存失败'
    ElMessage.error(typeof msg === 'string' ? msg : '参数保存失败')
  }
}

const saveConfig = async () => {
  try {
    await updateConfig(config.value)
    ElMessage.success('全局配置已保存')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const setControlFile = async () => {
  const filename = (config.value.control_file || '').split('/').pop()
  if (!filename) return
  try {
    const res = await chooseControlFile(filename)
    config.value = res.data
    ElMessage.success('控制文件已设定')
  } catch (e) {
    ElMessage.error('设置失败')
  }
}

// 获取当前配置
const getCurrentConfig = async () => {
  try {
    const res = await getConfig()
    config.value = res.data
    ElMessage.success('已获取当前配置')
  } catch (e) {
    ElMessage.error('获取失败')
  }
}

// 执行算法
const run = async () => {
  if (!selectedFile.value && !stableFile.value) {
    ElMessage.error('请上传观测数据 CSV')
    return
  }
  loading.value = true
  controller.value = new AbortController()
  if (loadingService.value) { try { loadingService.value.close() } catch(e){} finally { loadingService.value = null } }
  loadingService.value = ElLoading.service({ fullscreen: true, text: '算法执行中...', background: 'rgba(0,0,0,0.15)' })
  try {
    // 客户端快速校验CSV表头，避免后端直接500
    try {
      const preview = await (stableFile.value || selectedFile.value).text()
      const header = preview.split(/\r?\n/)[0] || ''
      const h = header.toLowerCase()
      if (!(h.includes('date') && (h.includes('lai') || h.includes('leaf') ))) {
        ElMessage.error('CSV首行必须包含列名：date 与 Lai')
        return
      }
    } catch(_) {}
    // 使用已缓存的稳定副本；若无，则现场拷贝一次
    const stable = stableFile.value || await toStableFile(selectedFile.value)
    let res
    if (algo.value === 'EnKF') res = await runEnKF(stable, controller.value)
    else if (algo.value === 'UKF') res = await runUKF(stable, controller.value)
    else if (algo.value === 'PF') res = await runPF(stable, controller.value)
    else if (algo.value === 'NLS4DVar') res = await runNLS4DVar(stable, controller.value)
    ElMessage.success('执行完成')
    output.value = res.data
  } catch (e) {
    if (e?.name === 'CanceledError' || e?.message === 'canceled') {
      ElMessage.info('已取消')
    } else {
      let msg = '执行失败'
      try {
        const data = e?.response?.data
        if (data) {
          if (data instanceof Blob) {
            msg = await data.text()
          } else if (typeof data === 'string') {
            msg = data
          } else if (typeof data === 'object') {
            msg = data.error || data.detail || msg
          }
        }
      } catch(_) {}
      ElMessage.error(msg)
    }
  } finally {
    loading.value = false
    controller.value = null
    if (loadingService.value) { try { loadingService.value.close() } catch(e){} finally { loadingService.value = null } }
    // 为避免连续切换算法后复用已被浏览器标记变更的文件，这里再刷新一次稳定副本
    try {
      if (selectedFile.value) {
        const buf = await selectedFile.value.arrayBuffer()
        stableFile.value = new File([new Uint8Array(buf)], selectedFile.value.name, { type: selectedFile.value.type || 'text/csv' })
      }
    } catch(_) {}
  }
}

const cancelRun = () => {
  if (controller.value) {
    controller.value.abort()
  }
}

// 任务模式：启动
const startTask = async () => {
  if (!selectedFile.value && !stableFile.value) {
    ElMessage.error('请上传观测数据 CSV')
    return
  }
  // 快速校验
  try {
    const preview = await (stableFile.value || selectedFile.value).text()
    const header = preview.split(/\r?\n/)[0] || ''
    const h = header.toLowerCase()
    if (!(h.includes('date') && (h.includes('lai') || h.includes('leaf')))) {
      ElMessage.error('CSV首行必须包含列名：date 与 Lai')
      return
    }
  } catch (_) {}

  try {
    loadingText.value = '算法执行中...'
    loadingKey.value++
    const stable = stableFile.value || await toStableFile(selectedFile.value)
    const res = await apiStartTask(algo.value, stable)
    taskId.value = res?.data?.task_id || ''
    if (!taskId.value) {
      ElMessage.error('任务创建失败')
      return
    }
    taskStatus.value = 'running'
    taskRunning.value = true
    ElMessage.success('任务已创建，开始后台执行')
    // 开始轮询
    if (taskTimer.value) clearInterval(taskTimer.value)
    taskTimer.value = setInterval(pollTask, 5000)
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.response?.data?.error || '任务创建失败'
    ElMessage.error(typeof msg === 'string' ? msg : '任务创建失败')
  }
}

// 任务模式：轮询
const pollTask = async () => {
  if (!taskId.value) return
  try {
    const res = await apiGetTask(taskId.value)
    const status = res?.data?.status
    taskStatus.value = status
    if (status === 'finished') {
      output.value = res?.data?.result || null
      clearInterval(taskTimer.value)
      taskTimer.value = null
      taskRunning.value = false
      ElMessage.success('执行完成')
      // 任务完成后自动加载任务历史
      loadTaskHistory()
    } else if (status === 'failed') {
      clearInterval(taskTimer.value)
      taskTimer.value = null
      taskRunning.value = false
      const err = res?.data?.error || '执行失败'
      ElMessage.error(typeof err === 'string' ? err : '执行失败')
    } else if (status === 'canceled') {
      clearInterval(taskTimer.value)
      taskTimer.value = null
      taskRunning.value = false
      ElMessage.info('任务已取消')
    }
  } catch (_) {}
}

// 任务模式：取消
const cancelTask = async () => {
  if (!taskId.value) return
  try {
    console.log('正在取消任务:', taskId.value)
    await apiCancelTask(taskId.value)
    console.log('取消任务请求已发送')
  } catch (e) {
    console.error('取消任务失败:', e)
    ElMessage.error('取消任务失败: ' + (e.message || '未知错误'))
  }
  if (taskTimer.value) { clearInterval(taskTimer.value); taskTimer.value = null }
  taskRunning.value = false
  taskStatus.value = 'canceled'
  ElMessage.info('任务已取消')
}

// 清理轮询器
onBeforeUnmount(() => {
  if (taskTimer.value) clearInterval(taskTimer.value)
})

// 展示结果
const output = ref(null)

// 参数说明
const descriptions = ref({})
const showDesc = ref(false)
const fetchDescriptions = async () => {
  try {
    const res = await getDescriptions()
    descriptions.value = res.data || {}
  } catch (e) {}
}
const openDesc = async () => {
  if (!Object.keys(descriptions.value).length) await fetchDescriptions()
  showDesc.value = true
}

// 渲染“当前参数值”徽标
const renderCurrentBadges = () => {
  currentBadges.value = Object.entries(params.value || {}).map(([k, v]) => `${k}: ${v}`)
}

// 重置为默认参数
const resetDefaults = () => {
  if (algo.value === 'EnKF') {
    params.value = { en_num: 25, err_lai_o: 0.01, err_lai: 1.28 }
  } else if (algo.value === 'UKF') {
    params.value = { en_num: 1, alpha: 4.0, beta: 1.0, kappa: 0.0, err_lai_o: 2.0, err_lai: 0.5 }
  } else if (algo.value === 'PF') {
    params.value = { en_num: 40, resample_threshold: 30, noise_std: 0.15 }
  } else if (algo.value === 'NLS4DVar') {
    params.value = { b_time_steps: 35, time_steps: 90, en_num: 25, i_max: 13, R_scalar: 0.01, nass: 1 }
  }
  renderCurrentBadges()
  ElMessage.info('已恢复默认参数，记得点击“更新参数”')
}

// 任务历史相关函数
const loadTaskHistory = async () => {
  try {
    taskHistoryLoading.value = true
    const res = await getLAITasks()
    taskHistory.value = res.data.tasks || []
    console.log('任务历史加载完成，任务数量:', taskHistory.value.length)
  } catch (error) {
    console.error('加载任务历史失败:', error)
    ElMessage.error('加载任务历史失败')
  } finally {
    taskHistoryLoading.value = false
  }
}

const showTaskHistoryDialog = () => {
  showTaskHistory.value = true
  loadTaskHistory()
}

const viewTaskDetail = async (task) => {
  try {
    taskDetailLoading.value = true
    selectedTask.value = task
    const res = await getLAITask(task.task_id)
    taskDetailData.value = res.data
    showTaskDetail.value = true
  } catch (error) {
    console.error('获取任务详情失败:', error)
    ElMessage.error('获取任务详情失败')
  } finally {
    taskDetailLoading.value = false
  }
}

const deleteTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务 "${task.task_id}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await deleteLAITask(task.task_id)
    ElMessage.success('任务已删除')
    await loadTaskHistory() // 重新加载任务历史
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
      ElMessage.error('删除任务失败')
    }
  }
}

const downloadTaskResult = async (task, fileType = 'summary') => {
  try {
    const res = await downloadLAIResult(task.task_id, fileType)
    
    // 创建下载链接
    const blob = new Blob([res.data], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 生成文件名：原文件名_任务ID
    let originalFileName = 'result'
    if (fileType === 'summary') {
      // 查找汇总文件名
      if (task.result) {
        for (const [key, value] of Object.entries(task.result)) {
          if ((key.includes('主要输出结果汇总') || key.includes('汇总')) && Array.isArray(value)) {
            originalFileName = key.replace('.csv', '')
            break
          }
        }
      }
    } else if (fileType === 'detailed') {
      // 查找详细文件名
      if (task.result) {
        for (const [key, value] of Object.entries(task.result)) {
          if (key.includes('详细输出结果') && Array.isArray(value)) {
            originalFileName = key.replace('.csv', '')
            break
          }
        }
      }
    }
    
    link.download = `${originalFileName}_${task.task_id}.csv`
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    const fileTypeName = fileType === 'summary' ? '汇总' : '详细'
    ElMessage.success(`${fileTypeName}文件下载成功`)
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

const formatTaskTime = (timeStr) => {
  try {
    const date = new Date(timeStr)
    return date.toLocaleString('zh-CN')
  } catch {
    return timeStr
  }
}

const getStatusTagType = (status) => {
  const statusMap = {
    'pending': 'info',
    'running': 'warning',
    'finished': 'success',
    'failed': 'danger',
    'canceled': 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    'pending': '等待中',
    'running': '运行中',
    'finished': '已完成',
    'failed': '失败',
    'canceled': '已取消'
  }
  return statusMap[status] || status
}

const getAlgorithmTagType = (algorithm) => {
  const algorithmMap = {
    'EnKF': 'primary',
    'UKF': 'success',
    'PF': 'warning',
    'NLS4DVar': 'danger'
  }
  return algorithmMap[algorithm] || 'info'
}

// 获取输入文件名（从完整路径中提取文件名）
const getInputFileName = (inputFilePath) => {
  if (!inputFilePath) {
    return '未知文件'
  }
  
  // 从路径中提取文件名
  const fileName = inputFilePath.split('/').pop() || inputFilePath.split('\\').pop()
  return fileName || '未知文件'
}

// 动态获取汇总数据
const getSummaryData = () => {
  if (!taskDetailData.value || !taskDetailData.value.result) {
    return null
  }
  
  const result = taskDetailData.value.result
  
  // 查找包含"主要输出结果汇总"或"汇总"的键
  for (const [key, value] of Object.entries(result)) {
    if ((key.includes('主要输出结果汇总') || key.includes('汇总')) && 
        Array.isArray(value) && value.length > 0) {
      return value
    }
  }
  
  // 如果没有找到汇总数据，查找第一个包含CSV的数组数据
  for (const [key, value] of Object.entries(result)) {
    if (key.includes('.csv') && Array.isArray(value) && value.length > 0) {
      // 检查是否是汇总数据（通常汇总数据只有一条记录）
      if (value.length === 1) {
        return value
      }
    }
  }
  
  return null
}

// 动态获取详细数据
const getDetailedData = () => {
  if (!taskDetailData.value || !taskDetailData.value.result) {
    return null
  }
  
  const result = taskDetailData.value.result
  
  // 查找包含"详细输出结果"的键
  for (const [key, value] of Object.entries(result)) {
    if (key.includes('详细输出结果') && Array.isArray(value) && value.length > 0) {
      return value
    }
  }
  
  // 如果没有找到详细数据，查找包含CSV的数组数据（多条记录）
  for (const [key, value] of Object.entries(result)) {
    if (key.includes('.csv') && Array.isArray(value) && value.length > 1) {
      // 检查是否包含date字段（详细数据通常包含日期）
      if (value[0] && value[0].date) {
        return value
      }
    }
  }
  
  return null
}

// 从当前输出结果中获取汇总数据
const getSummaryDataFromOutput = () => {
  if (!output.value) {
    return null
  }
  
  // 查找包含"主要输出结果汇总"或"汇总"的键
  for (const [key, value] of Object.entries(output.value)) {
    if ((key.includes('主要输出结果汇总') || key.includes('汇总')) && 
        Array.isArray(value) && value.length > 0) {
      return value
    }
  }
  
  // 如果没有找到汇总数据，查找第一个包含CSV的数组数据
  for (const [key, value] of Object.entries(output.value)) {
    if (key.includes('.csv') && Array.isArray(value) && value.length > 0) {
      // 检查是否是汇总数据（通常汇总数据只有一条记录）
      if (value.length === 1) {
        return value
      }
    }
  }
  
  return null
}

// 从当前输出结果中获取详细数据
const getDetailedDataFromOutput = () => {
  if (!output.value) {
    return null
  }
  
  // 查找包含"详细输出结果"的键
  for (const [key, value] of Object.entries(output.value)) {
    if (key.includes('详细输出结果') && Array.isArray(value) && value.length > 0) {
      return value
    }
  }
  
  // 如果没有找到详细数据，查找包含CSV的数组数据（多条记录）
  for (const [key, value] of Object.entries(output.value)) {
    if (key.includes('.csv') && Array.isArray(value) && value.length > 1) {
      // 检查是否包含date字段（详细数据通常包含日期）
      if (value[0] && value[0].date) {
        return value
      }
    }
  }
  
  return null
}

// 下载当前结果文件
const downloadCurrentResult = async (fileType = 'summary') => {
  try {
    if (!output.value || !output.value._output_dir) {
      ElMessage.error('没有可下载的结果文件')
      return
    }
    
    // 如果有当前任务ID，使用任务历史下载API
    if (taskId.value) {
      try {
        const res = await downloadLAIResult(taskId.value, fileType)
        
        // 创建下载链接
        const blob = new Blob([res.data], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        
        // 生成文件名：原文件名_任务ID
        let originalFileName = 'result'
        if (fileType === 'summary') {
          // 查找汇总文件名
          for (const [key, value] of Object.entries(output.value)) {
            if ((key.includes('主要输出结果汇总') || key.includes('汇总')) && Array.isArray(value)) {
              originalFileName = key.replace('.csv', '')
              break
            }
          }
        } else if (fileType === 'detailed') {
          // 查找详细文件名
          for (const [key, value] of Object.entries(output.value)) {
            if (key.includes('详细输出结果') && Array.isArray(value)) {
              originalFileName = key.replace('.csv', '')
              break
            }
          }
        }
        
        link.download = `${originalFileName}_${taskId.value}.csv`
        
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        const fileTypeName = fileType === 'summary' ? '汇总' : '详细'
        ElMessage.success(`${fileTypeName}文件下载成功`)
        return
      } catch (error) {
        console.log('任务历史下载失败，尝试直接下载:', error)
      }
    }
    
    // 如果任务历史下载失败或没有任务ID，直接从输出目录下载
    ElMessage.info('正在从输出目录下载文件...')
    
    // 这里可以添加直接从文件系统下载的逻辑
    // 或者提示用户手动从输出目录下载
    const outputDir = output.value._output_dir
    ElMessage.info(`请手动从以下目录下载文件: ${outputDir}`)
    
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

// 返回
const goBack = () => router.push('/home/algor')

init()
</script>

<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <div class="header-bar">
          <div class="title">LAI同化算法</div>
          <div class="actions">
            <el-button type="primary" @click="showTaskHistoryDialog">📋 任务历史</el-button>
            <el-button plain @click="openDesc">参数说明</el-button>
            <el-button type="success" @click="startTask" :loading="taskRunning" :disabled="taskRunning">任务模式执行</el-button>
            <el-button v-if="taskRunning" type="warning" @click="cancelTask">取消任务</el-button>
            <el-button @click="goBack">返回</el-button>
          </div>
        </div>
      </el-header>
      <el-main :key="loadingKey" v-loading="loading || taskRunning" :element-loading-text="loadingText || '算法执行中...'" element-loading-background="rgba(255,255,255,0.6)">
        <div class="inputData">
          <el-container>
            <el-header>输入与参数</el-header>
            <el-main>
              <div class="param-grid">
                <div class="param-card">
                  <div class="card-title">算法选择</div>
                  <el-select v-model="algo" style="width:240px" @change="onAlgoChange">
                    <el-option v-for="opt in algoOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                  </el-select>
                </div>

                <div class="param-card">
                  <div class="card-title">上传观测数据（CSV，包含 date 与 Lai 列）</div>
                  <el-button @click="triggerFile">选择文件</el-button>
                  <span v-if="selectedFileName" style="margin-left:10px">{{ selectedFileName }}</span>
                  <input ref="fileInput" type="file" @change="handleFileChange" accept=".csv" style="display:none" />
                </div>

                <div class="param-card">
                  <div class="card-title">当前算法参数</div>
                  <div class="badges">
                    <span v-for="item in currentBadges" :key="item" class="badge">{{ item }}</span>
                  </div>
                  <el-form :model="params" label-width="260px" class="params-form">
                    <el-form-item v-for="item in (paramSchemas[algo]||[])" :key="item.key" :label="item.label">
                      <el-input v-model.number="params[item.key]" style="width:260px" />
                    </el-form-item>
                  </el-form>
                  <div style="display:flex; gap:10px; justify-content:flex-end">
                    <el-button type="primary" @click="saveParams">更新参数</el-button>
                    <el-button @click="fetchAlgoParams">获取当前参数</el-button>
                    <el-button @click="resetDefaults">重置参数</el-button>
                  </div>
                </div>

                <div class="param-card">
                  <div class="card-title">全局配置（config.ini）</div>
                  <div class="badges">
                    <span class="badge" v-if="config.control_file">control_file: {{ config.control_file }}</span>
                    <span class="badge" v-if="config.ET_model">ET_model: {{ config.ET_model }}</span>
                    <span class="badge" v-if="config.num_cores">num_cores: {{ config.num_cores }}</span>
                  </div>
                  <el-form :model="config" label-width="180px">
                    <el-form-item label="控制文件">
                      <el-select v-model="config.control_file" style="width:260px">
                        <el-option v-for="f in controlFiles" :key="f.name" :label="`${f.name} (${(f.size/1024).toFixed(1)} KB)`" :value="`inputfile/${f.name}`" />
                      </el-select>
                      <el-button style="margin-left:10px" @click="fetchControlFiles">刷新列表</el-button>
                    </el-form-item>
                    <el-form-item label="蒸散模型">
                      <el-select v-model="config.ET_model" style="width:260px">
                        <el-option v-for="e in (options.ET_model||[])" :key="e" :label="e" :value="e" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="并行核心数">
                      <el-select v-model="config.num_cores" style="width:260px">
                        <el-option v-for="c in (options.num_cores||[])" :key="c" :label="c" :value="c" />
                      </el-select>
                    </el-form-item>
                  </el-form>
                  <div class="config-actions">
                    <el-button @click="getCurrentConfig">获取当前配置</el-button>
                    <el-button type="primary" @click="saveConfig">保存全局配置</el-button>
                  </div>
                </div>
              </div>
            </el-main>
          </el-container>
        </div>

        <div class="outputData" v-if="output">
          <el-container>
            <el-header>
              <div class="output-header">
                <span>输出结果</span>
                <div class="output-actions" v-if="output._output_dir">
                  <el-button type="success" size="small" @click="downloadCurrentResult('summary')">
                    <i class="el-icon-download"></i> 下载汇总
                  </el-button>
                  <el-button type="warning" size="small" @click="downloadCurrentResult('detailed')">
                    <i class="el-icon-download"></i> 下载详细
                  </el-button>
                </div>
              </div>
            </el-header>
            <el-main>
              <!-- 输出目录 -->
              <el-alert type="success" :closable="false" v-if="output._output_dir" 
                :title="`输出目录：${output._output_dir}`" />
              
              <!-- 主要输出结果汇总 -->
              <div v-if="getSummaryDataFromOutput()" class="summary-section">
                <h5>📋 主要输出结果汇总</h5>
                <el-table :data="getSummaryDataFromOutput()" stripe border>
                  <el-table-column 
                    v-for="(value, key) in getSummaryDataFromOutput()[0]" 
                    :key="key" 
                    :prop="key" 
                    :label="key"
                    :width="key === 'Treatment' ? 120 : undefined"
                  />
                </el-table>
              </div>
              
              <!-- 详细输出结果 - 按日期折叠 -->
              <div v-if="getDetailedDataFromOutput()" class="detailed-section">
                <h5>📅 详细输出结果（按日期）</h5>
                <el-collapse v-model="activeOutputCollapseItems">
                  <el-collapse-item 
                    v-for="(item, index) in getDetailedDataFromOutput()" 
                    :key="index"
                    :title="`${item.date} (DAP: ${item.DAP})`"
                    :name="index"
                  >
                    <el-table :data="[item]" stripe border size="small">
                      <el-table-column 
                        v-for="(value, key) in item" 
                        :key="key" 
                        :prop="key" 
                        :label="key"
                        :width="key === 'date' ? 100 : 80"
                        show-overflow-tooltip
                      />
                    </el-table>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </el-main>
          </el-container>
        </div>
      </el-main>
    </el-container>
  </div>
  <el-dialog v-model="showDesc" title="参数详细说明" width="700px">
    <div v-for="(group, title) in descriptions" :key="title" style="margin-bottom:12px">
      <div style="font-weight:600; margin-bottom:6px">{{ title }}</div>
      <ul style="padding-left:18px">
        <li v-for="(desc, key) in group" :key="key"><strong>{{ key }}</strong>: {{ desc }}</li>
      </ul>
    </div>
    <template #footer>
      <el-button type="primary" @click="showDesc=false">关闭</el-button>
    </template>
  </el-dialog>

  <!-- 任务历史对话框 -->
  <el-dialog v-model="showTaskHistory" title="LAI同化任务历史" width="80%" :close-on-click-modal="false">
    <el-table :data="taskHistory" v-loading="taskHistoryLoading" stripe>
      <el-table-column prop="task_id" label="任务ID" width="200">
        <template #default="{ row }">
          <span class="task-id">{{ row.task_id }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="input_file" label="输入文件" width="180">
        <template #default="{ row }">
          <span class="input-file-name">{{ getInputFileName(row.input_file) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="algorithm" label="算法" width="120">
        <template #default="{ row }">
          <el-tag :type="getAlgorithmTagType(row.algorithm)">
            {{ row.algorithm }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatTaskTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusTagType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="message" label="消息" width="150">
        <template #default="{ row }">
          <span class="message-text">{{ row.message || '无' }}</span>
        </template>
      </el-table-column>
        <el-table-column label="操作" width="380" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewTaskDetail(row)" :disabled="row.status !== 'finished'">查看结果</el-button>
            <el-button size="small" type="success" @click="downloadTaskResult(row, 'summary')" :disabled="row.status !== 'finished'">下载汇总</el-button>
            <el-button size="small" type="warning" @click="downloadTaskResult(row, 'detailed')" :disabled="row.status !== 'finished'">下载详细</el-button>
            <el-button size="small" type="danger" @click="deleteTask(row)">删除</el-button>
          </template>
        </el-table-column>
    </el-table>
  </el-dialog>

  <!-- 任务详情对话框 -->
  <el-dialog v-model="showTaskDetail" title="任务详情" width="70%" :close-on-click-modal="false">
    <div v-loading="taskDetailLoading">
      <div v-if="taskDetailData" class="task-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">{{ taskDetailData.task_id }}</el-descriptions-item>
          <el-descriptions-item label="算法">{{ taskDetailData.algorithm }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTaskTime(taskDetailData.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(taskDetailData.status)">
              {{ getStatusText(taskDetailData.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="进度" v-if="taskDetailData.progress !== undefined">
            <el-progress :percentage="taskDetailData.progress" />
          </el-descriptions-item>
          <el-descriptions-item label="消息" v-if="taskDetailData.message">
            {{ taskDetailData.message }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 参数信息 -->
        <div v-if="taskDetailData.parameters" class="detail-section">
          <h4>📋 算法参数</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item 
              v-for="(value, key) in taskDetailData.parameters" 
              :key="key" 
              :label="key"
            >
              {{ value }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 结果信息 -->
        <div v-if="taskDetailData.result" class="detail-section">
          <h4>📊 执行结果</h4>
          
          <!-- 输出目录 -->
          <el-alert type="success" :closable="false" v-if="taskDetailData.result._output_dir" 
            :title="`输出目录：${taskDetailData.result._output_dir}`" />
          
          <!-- 主要输出结果汇总 -->
          <div v-if="getSummaryData()" class="summary-section">
            <h5>📋 主要输出结果汇总</h5>
            <el-table :data="getSummaryData()" stripe border>
              <el-table-column 
                v-for="(value, key) in getSummaryData()[0]" 
                :key="key" 
                :prop="key" 
                :label="key"
                :width="key === 'Treatment' ? 120 : undefined"
              />
            </el-table>
          </div>
          
          <!-- 详细输出结果 - 按日期折叠 -->
          <div v-if="getDetailedData()" class="detailed-section">
            <h5>📅 详细输出结果（按日期）</h5>
            <el-collapse v-model="activeCollapseItems">
              <el-collapse-item 
                v-for="(item, index) in getDetailedData()" 
                :key="index"
                :title="`${item.date} (DAP: ${item.DAP})`"
                :name="index"
              >
                <el-table :data="[item]" stripe border size="small">
                  <el-table-column 
                    v-for="(value, key) in item" 
                    :key="key" 
                    :prop="key" 
                    :label="key"
                    :width="key === 'date' ? 100 : 80"
                    show-overflow-tooltip
                  />
                </el-table>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>

        <!-- 错误信息 -->
        <div v-if="taskDetailData.error" class="detail-section">
          <h4>❌ 错误信息</h4>
          <el-alert type="error" :closable="false" :title="taskDetailData.error" />
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<style scoped>
.param-grid {
  display: grid;
  grid-template-columns: 1fr; /* <1200px 默认一列 */
  gap: 28px;
}
.param-card {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 18px 20px;
  width: 100%;
  max-width: 720px;
  background: #fff;
}
.card-title {
  font-weight: 600;
  margin-bottom: 12px;
}
.badges { margin-bottom: 10px; }
.badge {
  display: inline-block;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 4px 10px;
  margin: 2px 6px 2px 0;
  font-size: 12px;
}

/* ≥1200px 时两列，≥1440px 仍保持最多两列 */
@media (min-width: 1200px) {
  .param-grid { grid-template-columns: 1fr 1fr; }
}

/* 任务历史相关样式 */
.task-id {
  font-family: monospace;
  font-size: 12px;
  color: #409eff;
  word-break: break-all;
  line-height: 1.4;
}

.input-file-name {
  font-size: 12px;
  color: #67c23a;
  word-break: break-all;
  line-height: 1.4;
  font-weight: 500;
}

.message-text {
  font-size: 12px;
  color: #606266;
  word-break: break-word;
  line-height: 1.4;
}

.task-detail {
  .detail-section {
    margin-top: 20px;
    
    h4 {
      margin-bottom: 10px;
      color: #303133;
      font-size: 16px;
    }
    
    h5 {
      margin-bottom: 10px;
      color: #606266;
      font-size: 14px;
      font-weight: 600;
    }
  }
  
  .summary-section {
    margin-bottom: 20px;
    
    .el-table {
      font-size: 12px;
    }
  }
  
  .detailed-section {
    .el-collapse {
      border: 1px solid #ebeef5;
      border-radius: 4px;
    }
    
    .el-collapse-item__header {
      background-color: #f5f7fa;
      font-weight: 500;
    }
    
    .el-table {
      font-size: 11px;
      margin-top: 10px;
    }
  }
}

/* 输出结果头部样式 */
.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.output-actions {
  display: flex;
  gap: 10px;
}

/* 顶部条布局，避免按钮重叠 */
.header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 20px; /* 顶部下移 */
}
.header-bar .title { font-weight: 600; font-size: 18px; }
.header-bar .actions { display: flex; gap: 10px; }

/* 表单标签宽时，保持单行不折断 */
.params-form :deep(.el-form-item__label) {
  white-space: nowrap;
}

/* 去除横向滚动条：容器超出自动换行且隐藏横向溢出 */
.common-layout, .el-main {
  overflow-x: hidden;
}
.param-grid { /* 允许卡片在容器边界内响应换行，不制造横向滚动 */
  max-width: 100%;
}
.config-actions { display:flex; gap:10px; justify-content:flex-end; flex-wrap: wrap; }
.badges { margin-bottom: 10px; }
.badge {
  display: inline-block;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 4px 10px;
  margin: 2px 6px 2px 0;
  font-size: 12px;
}
</style>


