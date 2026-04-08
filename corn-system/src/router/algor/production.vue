<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage, ElLoading, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { runMaizeYield, getMaizeYieldParams, updateMaizeYieldParams, getMaizeYieldDefaults, getMaizeYieldFiles, getMaizeYieldDescriptions, getMaizeYieldTasks, getMaizeYieldTask, deleteMaizeYieldTask, downloadMaizeYieldResult, previewMaizeYieldResult } from '@/api/maizeYield.js'

const router = useRouter()

// 页面状态
const loading = ref(false)
const showMaizeYieldUpload = ref(false)
const showTaskHistory = ref(false)
const showTaskDetail = ref(false)
const selectedTask = ref(null)

// 玉米产量预测相关状态
const maizeYieldLoading = ref(false)
const maizeYieldUploadedFiles = ref(new Array(12).fill(null))
const maizeYieldFiles = ref([
  { label: '气候数据文件', key: 'climate_file', desc: 'climate_data_even.npy - 气候数据' },
  { label: '作物参数文件', key: 'params_file', desc: 'param_values_corn.npy - 作物参数' },
  { label: '种植日期文件', key: 'plant_doy_file', desc: 'plant_DOY_even.npy - 种植日期' },
  { label: '氮肥施用文件', key: 'n_fertilizer_file', desc: 'sim_N_fertilizer_even.npy - 氮肥施用' },
  { label: '种植密度文件', key: 'density_file', desc: 'Density.npy - 种植密度' },
  { label: '土壤AD文件', key: 'soil_ad_file', desc: 'Soil_AD.npy - 土壤AD值' },
  { label: '土壤BD文件', key: 'soil_bd_file', desc: 'Soil_BD.npy - 土壤BD值' },
  { label: '土壤DUL文件', key: 'soil_dul_file', desc: 'Soil_DUL.npy - 土壤DUL值' },
  { label: '土壤LL文件', key: 'soil_ll_file', desc: 'Soil_LL.npy - 土壤LL值' },
  { label: '土壤PH文件', key: 'soil_ph_file', desc: 'Soil_PH.npy - 土壤PH值' },
  { label: '土壤饱和度文件', key: 'soil_sat_file', desc: 'Soil_Sat.npy - 土壤饱和度' },
  { label: '土壤有机碳文件', key: 'soil_soc_file', desc: 'Soil_SOC.npy - 土壤有机碳' }
])

// 模型配置参数
const modelParams = ref({
  FEATURE_DIM: 35,
  HIDDEN_DIM: 64,
  NUM_LAYERS: 1,
  OUTPUT_DIM: 1,
  DROPOUT: 0.5,
  SEQ_LEN: 365,
  BATCH_SIZE: 32
})

// 归一化参数
const normalizationParams = ref({
  MIN_VALUES: {
    'Yield': 0, 'RADN': 0, 'TMAX_AIR': -20, 'TMIN_AIR': -30, 'PRECN': 0,
    'tt_emerg_to_endjuv': 100, 'photoperiod_slope': 10, 'tt_flower_to_start_grain': 70,
    'tt_flower_to_maturity': 400, 'potKernelWt': 260, 'rue': 2.0, 'tt_flag_to_flower': 11,
    'Plant_DOY': 152, 'N_fertilizer': 0, 'Density': 6, 'AD': 0, 'BD': 1, 'DUL': 0,
    'LL': 0, 'PH': 4.946, 'Sat': 0.35, 'SOC': 0
  },
  MAX_VALUES: {
    'Yield': 702, 'RADN': 30, 'TMAX_AIR': 45, 'TMIN_AIR': 35, 'PRECN': 330,
    'tt_emerg_to_endjuv': 195, 'photoperiod_slope': 20, 'tt_flower_to_start_grain': 120,
    'tt_flower_to_maturity': 600, 'potKernelWt': 350, 'rue': 3.3, 'tt_flag_to_flower': 41,
    'Plant_DOY': 182, 'N_fertilizer': 280, 'Density': 9, 'AD': 0.31, 'BD': 1.6,
    'DUL': 0.537, 'LL': 0.31, 'PH': 9.493, 'Sat': 0.543, 'SOC': 5.703
  }
})

// 配置管理
const config = ref({
  model_path: 'data/models/LSTM_1l_64_U_case_3I_Yield3.sav',
  current_model: 'LSTM_1l_64_U_case_3I_Yield3.sav'
})

// 可用模型列表 - 使用真实文件名
const availableModels = ref([
  'LSTM_1l_64_U_case_3I_Yield3.sav',
  'LSTM_1l_64_U_case_3I_Yield3.savbest'
])

// 扫描模型文件
const scanModelFiles = async () => {
  try {
    // 这里可以调用后端API扫描models目录下的文件
    // 暂时使用硬编码的列表，后续可以通过API动态获取
    ElMessage.info('模型文件列表已更新')
  } catch (e) {
    ElMessage.error('扫描模型文件失败')
  }
}

// 参数说明
const descriptions = ref({})
const showDesc = ref(false)

// 预测结果
const output = ref(null)
const csvContent = ref('')

// 任务历史相关状态
const taskHistory = ref([])
const taskHistoryLoading = ref(false)
const taskDetailData = ref(null)
const taskDetailLoading = ref(false)

// 读取CSV文件内容
const readCsvContent = async (filePath) => {
  try {
    // 由于后端没有实现read-csv接口，我们直接使用预测结果中的static_info
    // 这里可以显示一个提示信息
    csvContent.value = 'CSV文件内容：\n' + 
      '由于技术限制，无法直接读取CSV文件内容。\n' +
      '但预测结果已在上方统计信息中显示。\n' +
      '如需查看完整数据，请查看输出文件：' + filePath
  } catch (error) {
    console.error('读取CSV文件失败:', error)
    csvContent.value = '读取CSV文件失败'
  }
}

// 初始化
const init = async () => {
  try {
    await fetchAlgoParams()
    await fetchDescriptions()
    
    // 初始化完成后，确保配置正确显示
    console.log('初始化完成，当前配置:', config.value)
  } catch (e) {
    console.log('初始化失败:', e)
  }
}

// 获取算法参数
const fetchAlgoParams = async () => {
  try {
    const res = await getMaizeYieldParams()
    if (res && res.data) {
      // 更新模型参数
      if (res.data.model_config) {
        modelParams.value = { ...modelParams.value, ...res.data.model_config }
      }
      // 更新归一化参数
      if (res.data.normalization_params) {
        normalizationParams.value = { ...normalizationParams.value, ...res.data.normalization_params }
      }
      // 更新配置
      if (res.data.config) {
        config.value = { ...config.value, ...res.data.config }
      }
    }
  } catch (e) {
    console.log('获取参数失败:', e)
  }
}

// 获取参数说明
const fetchDescriptions = async () => {
  try {
    const res = await getMaizeYieldDescriptions()
    descriptions.value = res.data || {}
    
    // 添加系统说明到参数说明中
    descriptions.value['系统说明'] = {
      '玉米产量预测系统': '基于LSTM（长短期记忆网络）深度学习算法，通过分析以下数据来预测玉米产量：',
      '气候数据': '温度、降水、日照等气象因素',
      '土壤数据': '土壤类型、肥力、水分等土壤特性',
      '作物参数': '品种特性、种植密度、施肥情况',
      '管理措施': '种植日期、灌溉、病虫害防治等',
      '处理流程': '系统会自动处理数据，进行特征工程和模型训练，最终输出产量预测结果'
    }
    
    // 添加LSTM模型配置参数说明
    descriptions.value['LSTM模型配置参数'] = {
      '特征维度 (FEATURE_DIM)': '输入特征的数量，决定了模型能处理的数据维度',
      '隐藏层维度 (HIDDEN_DIM)': 'LSTM隐藏层的神经元数量，影响模型的记忆能力和复杂度',
      'LSTM层数 (NUM_LAYERS)': 'LSTM层的数量，多层可以学习更复杂的时序模式',
      '输出维度 (OUTPUT_DIM)': '输出预测值的维度，玉米产量预测通常为1',
      'Dropout率 (DROPOUT)': '防止过拟合的Dropout比例，值越大正则化效果越强',
      '序列长度 (SEQ_LEN)': '输入序列的时间步长，通常对应一年的天数',
      '批次大小 (BATCH_SIZE)': '训练时的批次大小，影响训练稳定性和内存使用'
    }
    
    // 添加数据归一化参数说明
    descriptions.value['数据归一化参数'] = {
      'Yield (产量)': '玉米产量的归一化范围，用于数据预处理',
      'RADN (辐射)': '太阳辐射数据的归一化范围',
      'TMAX_AIR (最高气温)': '日最高气温的归一化范围',
      'TMIN_AIR (最低气温)': '日最低气温的归一化范围',
      'PRECN (降水量)': '日降水量的归一化范围',
      'tt_emerg_to_endjuv (出苗到幼穗期积温)': '作物发育阶段的积温参数',
      'photoperiod_slope (光周期斜率)': '光周期响应的斜率参数',
      'tt_flower_to_start_grain (开花到开始灌浆积温)': '开花到灌浆期的积温参数',
      'tt_flower_to_maturity (开花到成熟积温)': '开花到成熟的积温参数',
      'potKernelWt (潜在籽粒重量)': '作物的潜在籽粒重量参数',
      'rue (辐射利用效率)': '作物对辐射的利用效率',
      'tt_flag_to_flower (抽穗到开花积温)': '抽穗到开花的积温参数',
      'Plant_DOY (种植日期)': '作物的种植日期（一年中的第几天）',
      'N_fertilizer (氮肥)': '氮肥施用量',
      'Density (密度)': '作物种植密度',
      'AD (土壤AD值)': '土壤的空气干燥度',
      'BD (土壤BD值)': '土壤的容重',
      'DUL (土壤DUL值)': '土壤的排水上限',
      'LL (土壤LL值)': '土壤的萎蔫点',
      'PH (土壤PH值)': '土壤的酸碱度',
      'Sat (土壤饱和度)': '土壤的饱和度',
      'SOC (土壤有机碳)': '土壤的有机碳含量'
    }
    
    // 添加必需文件说明
    descriptions.value['必需文件'] = {
      'climate_data_even.npy': '气候数据文件，包含温度、降水、辐射等气象数据',
      'param_values_corn.npy': '作物参数文件，包含品种特性、发育参数等',
      'plant_DOY_even.npy': '种植日期文件，记录作物的种植时间',
      'sim_N_fertilizer_even.npy': '氮肥施用文件，记录施肥量和时间',
      'Density.npy': '种植密度文件，记录作物的种植密度',
      'Soil_AD.npy': '土壤AD值文件，土壤空气干燥度参数',
      'Soil_BD.npy': '土壤BD值文件，土壤容重参数',
      'Soil_DUL.npy': '土壤DUL值文件，土壤排水上限参数',
      'Soil_LL.npy': '土壤LL值文件，土壤萎蔫点参数',
      'Soil_PH.npy': '土壤PH值文件，土壤酸碱度参数',
      'Soil_Sat.npy': '土壤饱和度文件，土壤饱和度参数',
      'Soil_SOC.npy': '土壤有机碳文件，土壤有机碳含量参数'
    }
    
  } catch (e) {
    console.log('获取参数说明失败:', e)
  }
}

// 保存LSTM模型参数
const saveModelParams = async () => {
  try {
    const payload = {
      model_config_params: {
        FEATURE_DIM: modelParams.value.FEATURE_DIM,
        HIDDEN_DIM: modelParams.value.HIDDEN_DIM,
        NUM_LAYERS: modelParams.value.NUM_LAYERS,
        OUTPUT_DIM: modelParams.value.OUTPUT_DIM,
        DROPOUT: modelParams.value.DROPOUT,
        SEQ_LEN: modelParams.value.SEQ_LEN,
        BATCH_SIZE: modelParams.value.BATCH_SIZE
      }
    }
    await updateMaizeYieldParams(payload)
    ElMessage.success('LSTM模型参数已保存')
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.response?.data?.error || 'LSTM模型参数保存失败'
    ElMessage.error(typeof msg === 'string' ? msg : 'LSTM模型参数保存失败')
  }
}

// 获取当前LSTM模型参数
const getCurrentModelParams = async () => {
  try {
    const res = await getMaizeYieldParams()
    if (res && res.data) {
      if (res.data.model_config) {
        modelParams.value = { ...modelParams.value, ...res.data.model_config }
      }
      if (res.data.config) {
        config.value = { ...config.value, ...res.data.config }
      }
      ElMessage.success('已获取当前LSTM模型参数')
    }
  } catch (e) {
    ElMessage.error('获取LSTM模型参数失败')
  }
}

// 重置LSTM模型参数为默认值
const resetModelDefaults = async () => {
  try {
    const res = await getMaizeYieldDefaults()
    if (res && res.data) {
      if (res.data.model_config) {
        modelParams.value = { ...modelParams.value, ...res.data.model_config }
      }
      if (res.data.config) {
        config.value = { ...config.value, ...res.data.config }
      }
      ElMessage.success('已恢复LSTM模型默认参数')
    }
  } catch (e) {
    ElMessage.error('恢复LSTM模型默认参数失败')
  }
}

// 保存归一化参数
const saveNormalizationParams = async () => {
  try {
    const payload = {
      normalization_params: {
        min_values: normalizationParams.value.MIN_VALUES,
        max_values: normalizationParams.value.MAX_VALUES
      }
    }
    await updateMaizeYieldParams(payload)
    ElMessage.success('归一化参数已保存')
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.response?.data?.error || '归一化参数保存失败'
    ElMessage.error(typeof msg === 'string' ? msg : '归一化参数保存失败')
  }
}

// 获取当前归一化参数
const getCurrentNormalizationParams = async () => {
  try {
    const res = await getMaizeYieldParams()
    if (res && res.data && res.data.normalization_params) {
      // 确保正确更新MIN_VALUES和MAX_VALUES
      if (res.data.normalization_params.min_values) {
        normalizationParams.value.MIN_VALUES = { ...normalizationParams.value.MIN_VALUES, ...res.data.normalization_params.min_values }
      }
      if (res.data.normalization_params.max_values) {
        normalizationParams.value.MAX_VALUES = { ...normalizationParams.value.MAX_VALUES, ...res.data.normalization_params.max_values }
      }
      ElMessage.success('已获取当前归一化参数')
    }
  } catch (e) {
    ElMessage.error('获取归一化参数失败')
  }
}

// 重置归一化参数为默认值
const resetNormalizationDefaults = async () => {
  try {
    const res = await getMaizeYieldDefaults()
    if (res && res.data && res.data.normalization_params) {
      // 确保正确更新MIN_VALUES和MAX_VALUES
      if (res.data.normalization_params.min_values) {
        normalizationParams.value.MIN_VALUES = { ...normalizationParams.value.MIN_VALUES, ...res.data.normalization_params.min_values }
      }
      if (res.data.normalization_params.max_values) {
        normalizationParams.value.MAX_VALUES = { ...normalizationParams.value.MAX_VALUES, ...res.data.normalization_params.max_values }
      }
      ElMessage.success('已恢复归一化默认参数')
    }
  } catch (e) {
    ElMessage.error('恢复归一化默认参数失败')
  }
}

// 保存参数（保留原有函数用于兼容）
const saveParams = async () => {
  try {
    const payload = {
      model_config: modelParams.value,
      normalization_params: normalizationParams.value,
      config: config.value
    }
    await updateMaizeYieldParams(payload)
    ElMessage.success('参数已保存')
  } catch (e) {
    ElMessage.error('参数保存失败')
  }
}

// 获取当前参数（保留原有函数用于兼容）
const getCurrentParams = async () => {
  await fetchAlgoParams()
  ElMessage.success('已获取当前参数')
}

// 重置为默认参数（保留原有函数用于兼容）
const resetDefaults = async () => {
  try {
    const res = await getMaizeYieldDefaults()
    if (res && res.data) {
      if (res.data.model_config) {
        modelParams.value = { ...modelParams.value, ...res.data.model_config }
      }
      if (res.data.normalization_params) {
        normalizationParams.value = { ...normalizationParams.value, ...res.data.normalization_params }
      }
      if (res.data.config) {
        config.value = { ...config.value, ...res.data.config }
      }
      ElMessage.success('已恢复默认参数')
    }
  } catch (e) {
    ElMessage.error('恢复默认参数失败')
  }
}

// 保存配置
const saveConfig = async () => {
  try {
    // 更新模型路径以匹配当前选择的模型
    config.value.model_path = `data/models/${config.value.current_model}`
    
    const payload = {
      config: {
        model_path: config.value.model_path,
        current_model: config.value.current_model
      }
    }
    
    console.log('保存配置，payload:', payload) // 添加调试日志
    
    const result = await updateMaizeYieldParams(payload)
    console.log('保存配置结果:', result) // 添加调试日志
    
    if (result && result.data) {
      ElMessage.success('模型配置已保存')
      // 保存成功后，重新获取配置以确保同步
      await getCurrentConfig()
    } else {
      ElMessage.warning('配置保存成功，但返回结果异常')
    }
  } catch (e) {
    console.error('保存配置错误:', e) // 添加错误日志
    const msg = e?.response?.data?.detail || e?.response?.data?.error || '模型配置保存失败'
    ElMessage.error(typeof msg === 'string' ? msg : '模型配置保存失败')
  }
}

// 获取当前配置
const getCurrentConfig = async () => {
  try {
    const res = await getMaizeYieldParams()
    console.log('获取配置响应:', res) // 添加调试日志
    
    if (res && res.data && res.data.config) {
      config.value = { ...config.value, ...res.data.config }
      console.log('更新后的配置:', config.value) // 添加调试日志
      ElMessage.success('已获取当前模型配置')
    } else {
      // 如果没有找到已保存的配置，使用默认配置
      config.value = {
        model_path: 'data/models/LSTM_1l_64_U_case_3I_Yield3.sav',
        current_model: 'LSTM_1l_64_U_case_3I_Yield3.sav'
      }
      console.log('使用默认配置:', config.value) // 添加调试日志
      ElMessage.info('使用默认模型配置')
    }
  } catch (e) {
    console.error('获取配置错误:', e) // 添加错误日志
    ElMessage.error('获取模型配置失败')
  }
}

// 玉米产量预测相关函数
const selectMaizeYieldFile = (index) => {
  nextTick(() => {
    // 使用refs数组访问DOM元素
    if (fileInputRefs.value[index]) {
      fileInputRefs.value[index].click()
    } else {
      console.log(`文件输入框 ${index} 未找到`)
    }
  })
}

// 创建refs数组用于文件输入
const fileInputRefs = ref([])

// 关键词匹配函数
const matchFileToSlot = (fileName) => {
  const fileNameLower = fileName.toLowerCase()
  
  // 定义关键词映射
  const keywordMap = {
    'climate': 0,        // 气候数据文件
    'param': 1,          // 作物参数文件
    'plant': 2,          // 种植日期文件
    'fertilizer': 3,     // 氮肥施用文件
    'density': 4,        // 种植密度文件
    'soil_ad': 5,        // 土壤AD文件
    'soil_bd': 6,        // 土壤BD文件
    'soil_dul': 7,       // 土壤DUL文件
    'soil_ll': 8,        // 土壤LL文件
    'soil_ph': 9,        // 土壤PH文件
    'soil_sat': 10,      // 土壤饱和度文件
    'soil_soc': 11       // 土壤有机碳文件
  }
  
  // 查找匹配的关键词
  for (const [keyword, index] of Object.entries(keywordMap)) {
    if (fileNameLower.includes(keyword)) {
      return index
    }
  }
  
  // 如果没有匹配到，返回-1
  return -1
}

const handleMaizeYieldFileChange = (event, index) => {
  const file = event.target.files[0]
  if (file) {
    // 检查文件扩展名
    if (!file.name.endsWith('.npy')) {
      ElMessage.error('请选择.npy格式的文件')
      return
    }
    maizeYieldUploadedFiles.value[index] = file
  }
}

// 拖拽上传处理
const handleDragOver = (event, index) => {
  event.preventDefault()
  event.currentTarget.classList.add('drag-over')
}

const handleDragLeave = (event) => {
  event.currentTarget.classList.remove('drag-over')
}

const handleDrop = (event, index) => {
  event.preventDefault()
  event.currentTarget.classList.remove('drag-over')
  
  const files = event.dataTransfer.files
  if (files.length > 0) {
    const file = files[0]
    if (!file.name.endsWith('.npy')) {
      ElMessage.error('请选择.npy格式的文件')
      return
    }
    maizeYieldUploadedFiles.value[index] = file
  }
}

// 处理一次性拖拽多个文件到上传区域
const handleMultipleFileDrop = (event) => {
  event.preventDefault()
  
  const files = event.dataTransfer.files
  if (files.length === 0) return
  
  let successCount = 0
  let errorCount = 0
  
  for (const file of files) {
    if (!file.name.endsWith('.npy')) {
      errorCount++
      continue
    }
    
    // 尝试匹配文件到对应的槽位
    const slotIndex = matchFileToSlot(file.name)
    if (slotIndex !== -1 && !maizeYieldUploadedFiles.value[slotIndex]) {
      maizeYieldUploadedFiles.value[slotIndex] = file
      successCount++
    } else {
      errorCount++
    }
  }
  
  if (successCount > 0) {
    ElMessage.success(`成功分配 ${successCount} 个文件`)
  }
  if (errorCount > 0) {
    ElMessage.warning(`${errorCount} 个文件无法分配或格式不正确`)
  }
}

const runMaizeYieldPrediction = async () => {
  const missingFiles = maizeYieldUploadedFiles.value.findIndex(file => !file)
  if (missingFiles !== -1) {
    ElMessage.error(`请上传所有必需文件，缺少第${missingFiles + 1}个文件`)
    return
  }

  maizeYieldLoading.value = true
  try {
    // 创建FormData对象
    const formData = new FormData()
    
    // 添加所有文件 - 使用后端期望的字段名
    const fileFieldNames = [
      'climate_file',
      'params_file', 
      'plant_doy_file',
      'n_fertilizer_file',
      'density_file',
      'soil_ad_file',
      'soil_bd_file',
      'soil_dul_file',
      'soil_ll_file',
      'soil_ph_file',
      'soil_sat_file',
      'soil_soc_file'
    ]
    
    // 添加所有文件
    maizeYieldUploadedFiles.value.forEach((file, index) => {
      if (file) {
        formData.append(fileFieldNames[index], file)
      }
    })

    // 调用玉米产量预测API
    const result = await runMaizeYield(formData)
    
    // 检查响应状态 - 参考lai.vue的处理方式
    if (result && result.data && result.data.code === 200) {
      ElMessage.success('玉米产量预测完成！')
      showMaizeYieldUpload.value = false
      
      // 显示预测结果
      const staticInfo = JSON.parse(result.data.result.static_info)
      ElMessage.success(`预测完成！平均产量: ${staticInfo.mean}, 最高: ${staticInfo.max}, 最低: ${staticInfo.min}, 样本数: ${staticInfo.count}`)
      
      // 保存预测结果用于展示 - 使用result.data
      output.value = result.data
      
      // 自动读取CSV文件内容
      if (result.data.result?.output_path) {
        await readCsvContent(result.data.result.output_path)
      }
      
      // 这里可以进一步处理预测结果
      console.log('预测结果:', result.data)
      
      // 重新加载任务历史
      await loadTaskHistory()
    } else {
      ElMessage.error(`预测失败: ${result?.data?.msg || result?.msg || '未知错误'}`)
    }
  } catch (error) {
    console.error('预测错误:', error)
    ElMessage.error(`预测失败: ${error.message || '未知错误'}`)
  } finally {
    maizeYieldLoading.value = false
  }
}

// 打开参数说明
const openDesc = async () => {
  if (!Object.keys(descriptions.value).length) {
    await fetchDescriptions()
  }
  showDesc.value = true
}

// 任务历史管理函数
const loadTaskHistory = async () => {
  console.log('开始加载任务历史...') // 添加调试日志
  taskHistoryLoading.value = true
  try {
    const res = await getMaizeYieldTasks()
    console.log('任务历史API响应:', res) // 添加调试日志
    if (res && res.data) {
      // 后端直接返回 {tasks: []}，不需要 res.data.tasks
      taskHistory.value = res.data.tasks || []
      console.log('任务历史加载完成，任务数量:', taskHistory.value.length)
    }
  } catch (error) {
    console.error('加载任务历史失败:', error)
    ElMessage.error('加载任务历史失败')
  } finally {
    taskHistoryLoading.value = false
  }
}

// 显示任务历史对话框
const showTaskHistoryDialog = () => {
  console.log('点击任务历史按钮') // 添加调试日志
  showTaskHistory.value = true
  loadTaskHistory() // 自动加载任务历史
}

// 下载当前预测结果
const downloadCurrentResult = async () => {
  if (!output.value || !output.value.result?.task_id) {
    ElMessage.error('没有可下载的结果文件')
    return
  }
  
  try {
    const res = await downloadMaizeYieldResult(output.value.result.task_id)
    
    // 创建下载链接
    const blob = new Blob([res.data], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `yield_predictions_${output.value.result.task_id}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('文件下载成功')
  } catch (error) {
    console.error('下载文件失败:', error)
    ElMessage.error('下载文件失败')
  }
}

const viewTaskDetail = async (task) => {
  selectedTask.value = task
  taskDetailLoading.value = true
  try {
    const res = await getMaizeYieldTask(task.task_id)
    console.log('任务详情API响应:', res) // 添加调试日志
    if (res && res.data) {
      taskDetailData.value = res.data
      showTaskDetail.value = true
    }
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
    
    await deleteMaizeYieldTask(task.task_id)
    ElMessage.success('任务删除成功')
    await loadTaskHistory() // 重新加载任务列表
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
      ElMessage.error('删除任务失败')
    }
  }
}

const downloadTaskResult = async (task) => {
  try {
    const res = await downloadMaizeYieldResult(task.task_id)
    
    // 创建下载链接
    const blob = new Blob([res.data], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `yield_predictions_${task.task_id}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('文件下载成功')
  } catch (error) {
    console.error('下载文件失败:', error)
    ElMessage.error('下载文件失败')
  }
}

const formatTaskTime = (timeStr) => {
  if (!timeStr) return '未知时间'
  try {
    const date = new Date(timeStr)
    return date.toLocaleString('zh-CN')
  } catch {
    return timeStr
  }
}

// 获取模型名称显示
const getModelName = (modelName) => {
  if (!modelName) return 'LSTM模型'
  // 提取模型文件名，去掉路径和扩展名
  const fileName = modelName.split('/').pop() || modelName
  const nameWithoutExt = fileName.replace('.sav', '')
  return nameWithoutExt || 'LSTM模型'
}

// 获取文件标签
const getFileLabel = (key) => {
  const labelMap = {
    'climate_json_path': '气候数据文件',
    'params_json_path': '作物参数文件',
    'plant_doy_json_path': '种植日期文件',
    'n_fertilizer_json_path': '氮肥施用文件',
    'density_json_path': '种植密度文件',
    'soil_ad_json_path': '土壤AD文件',
    'soil_bd_json_path': '土壤BD文件',
    'soil_dul_json_path': '土壤DUL文件',
    'soil_ll_json_path': '土壤LL文件',
    'soil_ph_json_path': '土壤PH文件',
    'soil_sat_json_path': '土壤饱和度文件',
    'soil_soc_json_path': '土壤有机碳文件'
  }
  return labelMap[key] || key
}

// 获取文件名
const getFileName = (filePath) => {
  if (!filePath) return '未知文件'
  if (typeof filePath !== 'string') {
    console.warn('getFileName received non-string value:', filePath)
    return '未知文件'
  }
  return filePath.split('/').pop() || filePath.split('\\').pop() || filePath
}

// 获取配置标签
const getConfigLabel = (key) => {
  const labelMap = {
    'FEATURE_DIM': '特征维度',
    'HIDDEN_DIM': '隐藏层维度',
    'NUM_LAYERS': 'LSTM层数',
    'OUTPUT_DIM': '输出维度',
    'DROPOUT': 'Dropout率',
    'SEQ_LEN': '序列长度',
    'BATCH_SIZE': '批次大小'
  }
  return labelMap[key] || key
}

// 返回
const goBack = () => router.push('/home/algor')

onMounted(() => {
  init()
  loadTaskHistory() // 加载任务历史
})
</script>

<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <div class="header-bar">
          <div class="title">玉米产量预测（LSTM）</div>
          <div class="actions">
            <el-button type="primary" @click="showTaskHistoryDialog">📋 任务历史</el-button>
            <el-button plain @click="openDesc">参数说明</el-button>
            <el-button @click="goBack">返回</el-button>
          </div>
        </div>
      </el-header>
      <el-main>
                 <div class="maize-yield-main">
           <el-container>
             <el-main>
                              <div class="content-grid">
                  <!-- 左侧：模型文件选择 + LSTM模型配置 -->
                  <div class="left-column">
                    <!-- 模型文件选择 -->
                    <div class="param-card">
                      <div class="card-title">模型文件选择</div>
                      <div class="param-description">
                        选择要使用的预训练LSTM模型文件
                      </div>
                                             <el-form :model="config" label-width="100px">
                         <el-form-item label="模型文件">
                           <el-select v-model="config.current_model" style="width:280px" placeholder="请选择模型文件">
                             <el-option 
                               v-for="model in availableModels" 
                               :key="model" 
                               :label="model" 
                               :value="model" 
                             />
                           </el-select>
                         </el-form-item>
                       </el-form>
                                             <div class="config-actions">
                         <el-button @click="scanModelFiles" size="small">扫描模型文件</el-button>
                         <el-button @click="getCurrentConfig" size="small">获取当前配置</el-button>
                         <el-button type="primary" @click="saveConfig" size="small">保存配置</el-button>
                       </div>
                    </div>

                    <!-- LSTM模型配置参数 -->
                    <div class="param-card">
                      <div class="card-title">LSTM模型配置</div>
                      <div class="param-description">
                        调整LSTM神经网络的配置参数以优化预测性能
                      </div>
                      
                                             <div class="model-params-section">
                         <h4>模型参数配置</h4>
                         <div class="model-params-grid">
                           <div class="model-param-item">
                             <label>特征维度 (FEATURE_DIM):</label>
                             <el-input v-model.number="modelParams.FEATURE_DIM" size="small" style="width:100px" />
                             <span class="param-help">输入特征的数量</span>
                           </div>
                           <div class="model-param-item">
                             <label>隐藏层维度 (HIDDEN_DIM):</label>
                             <el-input v-model.number="modelParams.HIDDEN_DIM" size="small" style="width:100px" />
                             <span class="param-help">LSTM隐藏层的神经元数量</span>
                           </div>
                           <div class="model-param-item">
                             <label>LSTM层数 (NUM_LAYERS):</label>
                             <el-input v-model.number="modelParams.NUM_LAYERS" size="small" style="width:100px" />
                             <span class="param-help">LSTM层的数量</span>
                           </div>
                           <div class="model-param-item">
                             <label>输出维度 (OUTPUT_DIM):</label>
                             <el-input v-model.number="modelParams.OUTPUT_DIM" size="small" style="width:100px" />
                             <span class="param-help">输出预测值的维度</span>
                           </div>
                           <div class="model-param-item">
                             <label>Dropout率 (DROPOUT):</label>
                             <el-input v-model.number="modelParams.DROPOUT" size="small" style="width:100px" />
                             <span class="param-help">防止过拟合的Dropout比例</span>
                           </div>
                           <div class="model-param-item">
                             <label>序列长度 (SEQ_LEN):</label>
                             <el-input v-model.number="modelParams.SEQ_LEN" size="small" style="width:100px" />
                             <span class="param-help">输入序列的时间步长</span>
                           </div>
                           <div class="model-param-item">
                             <label>批次大小 (BATCH_SIZE):</label>
                             <el-input v-model.number="modelParams.BATCH_SIZE" size="small" style="width:100px" />
                             <span class="param-help">训练时的批次大小</span>
                           </div>
                         </div>
                         <div class="model-param-actions">
                           <el-button type="primary" @click="saveModelParams" size="small">更新参数</el-button>
                           <el-button @click="getCurrentModelParams" size="small">获取当前参数</el-button>
                           <el-button @click="resetModelDefaults" size="small">重置参数</el-button>
                         </div>
                       </div>
                    </div>
                  </div>

                                    <!-- 右侧：数据文件上传 + 数据归一化参数范围 -->
                  <div class="right-column">
                                         <!-- 数据文件上传 -->
                     <div class="param-card">
                       <div class="card-title">数据文件上传</div>
                       <div class="upload-description">
                         上传12个必需的.npy格式数据文件，这些文件包含气候、土壤、作物等数据
                       </div>
                       <el-button type="primary" @click="showMaizeYieldUpload = true" size="large">
                         开始上传数据文件并预测
                       </el-button>
                       
                       <!-- 系统说明 -->
                       <div class="system-description">
                         <p>基于LSTM（长短期记忆网络）深度学习算法，通过分析以下数据来预测玉米产量：</p>
                         <ul>
                           <li><strong>气候数据：</strong>温度、降水、日照等气象因素</li>
                           <li><strong>土壤数据：</strong>土壤类型、肥力、水分等土壤特性</li>
                           <li><strong>作物参数：</strong>品种特性、种植密度、施肥情况</li>
                           <li><strong>管理措施：</strong>种植日期、灌溉、病虫害防治等</li>
                         </ul>
                       </div>
                     </div>

                    <!-- 数据归一化参数范围 -->
                    <div class="param-card">
                      <div class="card-title">数据归一化参数范围</div>
                      <div class="param-description">
                        配置数据预处理时的归一化范围，每个参数对应一个最小值和一个最大值输入
                      </div>
                      
                      <div class="normalization-section">
                        <div class="param-grid-compact">
                          <div v-for="(minValue, key) in normalizationParams.MIN_VALUES" :key="key" class="param-item-compact">
                            <label>{{ key }}:</label>
                            <div class="range-inputs-compact">
                              <el-input 
                                v-model.number="normalizationParams.MIN_VALUES[key]" 
                                size="small" 
                                style="width:80px" 
                                placeholder="最小值"
                              />
                              <span class="range-separator">~</span>
                              <el-input 
                                v-model.number="normalizationParams.MAX_VALUES[key]" 
                                size="small" 
                                style="width:80px" 
                                placeholder="最大值"
                              />
                            </div>
                          </div>
                        </div>
                                                 <div class="normalization-param-actions">
                           <el-button type="primary" @click="saveNormalizationParams" size="small">更新参数</el-button>
                           <el-button @click="getCurrentNormalizationParams" size="small">获取当前参数</el-button>
                           <el-button @click="resetNormalizationDefaults" size="small">重置参数</el-button>
                         </div>
                      </div>
                    </div>
                  </div>
                </div>
            </el-main>
          </el-container>
                 </div>
       </el-main>
     </el-container>

     <!-- 预测结果展示区域 -->
     <div class="outputData" v-if="output">
       <el-container>
         <el-header class="result-header">
           <div class="result-header-content">
             <i class="el-icon-success"></i>
             <span>玉米产量预测结果</span>
           </div>
         </el-header>
         <el-main>
           <!-- 成功提示 -->
           <el-alert 
             type="success" 
             :closable="false" 
             v-if="output.result?.output_path" 
             :title="`预测完成！输出文件已生成`"
             description="文件已保存到指定路径，可下载查看详细结果"
             show-icon
             class="result-alert"
           />
           
           <!-- 统计信息展示 -->
           <div class="result-stats" v-if="output.result?.static_info">
             <h4>📊 预测统计信息</h4>
             <div class="stats-grid">
               <div class="stat-item">
                 <div class="stat-icon">📈</div>
                 <div class="stat-content">
                   <span class="stat-label">平均产量</span>
                   <span class="stat-value">{{ JSON.parse(output.result.static_info).mean }} kg/ha</span>
                 </div>
               </div>
               <div class="stat-item">
                 <div class="stat-icon">🏆</div>
                 <div class="stat-content">
                   <span class="stat-label">最高产量</span>
                   <span class="stat-value">{{ JSON.parse(output.result.static_info).max }} kg/ha</span>
                 </div>
               </div>
               <div class="stat-item">
                 <div class="stat-icon">📉</div>
                 <div class="stat-content">
                   <span class="stat-label">最低产量</span>
                   <span class="stat-value">{{ JSON.parse(output.result.static_info).min }} kg/ha</span>
                 </div>
               </div>
               <div class="stat-item">
                 <div class="stat-icon">🔢</div>
                 <div class="stat-content">
                   <span class="stat-label">样本数量</span>
                   <span class="stat-value">{{ JSON.parse(output.result.static_info).count }} 个</span>
                 </div>
               </div>
             </div>
           </div>
           
           <!-- CSV文件内容展示 -->
           <div class="csv-content" v-if="csvContent">
             <h4>📋 预测结果详情</h4>
             <div class="csv-container">
               <div class="csv-info">
                 <div class="info-grid">
                   <div class="info-item">
                     <span class="info-label">📁 输出文件路径</span>
                     <span class="info-value">{{ output.result?.output_path }}</span>
                   </div>
                   <div class="info-item">
                     <span class="info-label">📏 文件大小</span>
                     <span class="info-value">183 字节</span>
                   </div>
                   <div class="info-item">
                     <span class="info-label">📊 数据行数</span>
                     <span class="info-value">23 行</span>
                   </div>
                   <div class="info-item">
                     <span class="info-label">📝 数据格式</span>
                     <span class="info-value">每行一个产量预测值（kg/ha）</span>
                   </div>
                 </div>
                 
                 <!-- 下载按钮 -->
                 <div class="result-actions">
                   <el-button type="success" @click="downloadCurrentResult" size="large">
                     <i class="el-icon-download"></i> 下载CSV文件
                   </el-button>
                 </div>
                 
                 <div class="result-note">
                   <i class="el-icon-info"></i>
                   <span>完整数据请查看输出文件，统计信息已在上方显示</span>
                 </div>
               </div>
             </div>
           </div>
         </el-main>
       </el-container>
     </div>

     <!-- 玉米产量预测文件上传界面 -->
    <el-dialog v-model="showMaizeYieldUpload" title="玉米产量预测 - 数据文件上传" width="90%" :close-on-click-modal="false">
      <div class="maize-yield-upload">
        <div class="upload-header">
          <el-alert
            title="文件上传说明"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              请上传12个必需的.npy格式数据文件。这些文件包含用于玉米产量预测的所有输入数据。
              支持点击选择文件、单个拖拽上传和一次性拖拽多个文件三种方式。所有文件上传完成后，点击预测按钮开始分析。
            </template>
          </el-alert>
          
          <!-- 一次性拖拽多个文件区域 -->
          <div 
            class="multiple-upload-zone"
            @dragover="(e) => e.preventDefault()"
            @drop="handleMultipleFileDrop"
          >
            <div class="upload-zone-content">
              <i class="el-icon-upload"></i>
              <p>拖拽多个.npy文件到此处，系统将自动匹配分配到对应位置</p>
              <p class="upload-hint">支持的文件名关键词：climate, param, plant, fertilizer, density, soil_ad, soil_bd, soil_dul, soil_ll, soil_ph, soil_sat, soil_soc</p>
            </div>
          </div>
        </div>
        
        <div class="upload-grid">
          <div 
            v-for="(fileInfo, index) in maizeYieldFiles" 
            :key="index" 
            class="upload-item"
            @dragover="handleDragOver($event, index)"
            @dragleave="handleDragLeave"
            @drop="handleDrop($event, index)"
          >
            <div class="file-header">
              <div class="file-label">{{ fileInfo.label }}</div>
              <div class="file-desc">{{ fileInfo.desc }}</div>
            </div>
            <div class="file-actions">
              <el-button @click="selectMaizeYieldFile(index)" size="small" type="primary">
                {{ maizeYieldUploadedFiles[index] ? '重新选择' : '选择文件' }}
              </el-button>
              <span v-if="maizeYieldUploadedFiles[index]" class="file-name">
                {{ maizeYieldUploadedFiles[index].name }}
              </span>
            </div>
            <div class="drag-hint">或拖拽文件到此处</div>
            <input
              :ref="el => { if (el) fileInputRefs[index] = el }"
              type="file"
              @change="handleMaizeYieldFileChange($event, index)"
              accept=".npy"
              style="display:none"
            />
          </div>
        </div>
        
        <div class="upload-actions">
          <el-button type="primary" @click="runMaizeYieldPrediction" :loading="maizeYieldLoading" size="large">
            开始玉米产量预测
          </el-button>
          <el-button @click="showMaizeYieldUpload = false" size="large">关闭</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 任务历史对话框 -->
    <el-dialog v-model="showTaskHistory" title="玉米产量预测任务历史" width="80%" :close-on-click-modal="false">
      <div class="task-history">
        <div class="task-history-header">
          <el-button @click="loadTaskHistory" :loading="taskHistoryLoading" size="small">
            <i class="el-icon-refresh"></i> 刷新
          </el-button>
          <span class="task-count">共 {{ taskHistory.length }} 个任务</span>
        </div>
        
        <el-table :data="taskHistory" v-loading="taskHistoryLoading" stripe>
          <el-table-column prop="task_id" label="任务ID" width="250">
            <template #default="{ row }">
              <span class="task-id">{{ row.task_id }}</span>
            </template>
          </el-table-column>
           <el-table-column prop="model_name" label="模型" width="250">
            <template #default="{ row }">
              <span class="model-name">{{ getModelName(row.model_name) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatTaskTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'completed' ? 'success' : 'danger'">
                {{ row.status === 'completed' ? '完成' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="消息" width="150">
            <template #default="{ row }">
              <span class="message-text">{{ row.message || '无' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="viewTaskDetail(row)">查看结果</el-button>
              <el-button size="small" type="success" @click="downloadTaskResult(row)">下载</el-button>
              <el-button size="small" type="danger" @click="deleteTask(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showTaskHistory = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 任务详情对话框 -->
    <el-dialog v-model="showTaskDetail" title="任务详情" width="70%" :close-on-click-modal="false">
      <div class="task-detail" v-loading="taskDetailLoading">
        <div v-if="taskDetailData" class="task-detail-content">
          <!-- 任务基本信息 -->
          <div class="task-info-section">
            <h4>📋 任务信息</h4>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">任务ID:</span>
                <span class="info-value">{{ taskDetailData.task_id }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">创建时间:</span>
                <span class="info-value">{{ formatTaskTime(taskDetailData.created_at) }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">状态:</span>
                <el-tag :type="taskDetailData.status === 'completed' ? 'success' : 'danger'">
                  {{ taskDetailData.status === 'completed' ? '完成' : '失败' }}
                </el-tag>
              </div>
              <div class="info-item">
                <span class="info-label">消息:</span>
                <span class="info-value">{{ taskDetailData.message || '无' }}</span>
              </div>
              <div class="info-item" v-if="taskDetailData.model_name">
                <span class="info-label">使用模型:</span>
                <span class="info-value">{{ getModelName(taskDetailData.model_name) }}</span>
              </div>
              <div class="info-item" v-if="taskDetailData.algorithm">
                <span class="info-label">算法类型:</span>
                <span class="info-value">{{ taskDetailData.algorithm }}</span>
              </div>
            </div>
          </div>

          <!-- 输入文件信息 -->
          <div class="input-files-section" v-if="taskDetailData.input_files">
            <h4>📁 输入文件</h4>
            <div class="files-grid">
              <div class="file-item" v-for="(filePath, key) in taskDetailData.input_files" :key="key">
                <span class="file-label">{{ getFileLabel(key) }}:</span>
                <span class="file-value">{{ getFileName(filePath) }}</span>
              </div>
            </div>
          </div>

          <!-- 模型配置参数 -->
          <div class="model-config-section" v-if="taskDetailData.model_config">
            <h4>⚙️ 模型配置参数</h4>
            <div class="config-grid">
              <div class="config-item" v-for="(value, key) in taskDetailData.model_config" :key="key">
                <span class="config-label">{{ getConfigLabel(key) }}:</span>
                <span class="config-value">{{ value }}</span>
              </div>
            </div>
          </div>

          <!-- 归一化参数 -->
          <div class="normalization-section" v-if="taskDetailData.normalization_params">
            <h4>📊 归一化参数</h4>
            <el-collapse>
              <el-collapse-item title="最小值参数" name="min">
                <div class="param-grid">
                  <div class="param-item" v-for="(value, key) in (taskDetailData.normalization_params.min_values || taskDetailData.normalization_params.MIN_VALUES)" :key="key">
                    <span class="param-label">{{ key }}:</span>
                    <span class="param-value">{{ value }}</span>
                  </div>
                </div>
              </el-collapse-item>
              <el-collapse-item title="最大值参数" name="max">
                <div class="param-grid">
                  <div class="param-item" v-for="(value, key) in (taskDetailData.normalization_params.max_values || taskDetailData.normalization_params.MAX_VALUES)" :key="key">
                    <span class="param-label">{{ key }}:</span>
                    <span class="param-value">{{ value }}</span>
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>

          <!-- 预测结果统计 -->
          <div class="result-summary-section" v-if="taskDetailData.data_summary">
            <h4>📊 预测结果统计</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-icon">📈</div>
                <div class="stat-content">
                  <span class="stat-label">平均产量</span>
                  <span class="stat-value">{{ taskDetailData.data_summary.mean_yield }} kg/ha</span>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">🏆</div>
                <div class="stat-content">
                  <span class="stat-label">最高产量</span>
                  <span class="stat-value">{{ taskDetailData.data_summary.max_yield }} kg/ha</span>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">📉</div>
                <div class="stat-content">
                  <span class="stat-label">最低产量</span>
                  <span class="stat-value">{{ taskDetailData.data_summary.min_yield }} kg/ha</span>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">🔢</div>
                <div class="stat-content">
                  <span class="stat-label">记录数量</span>
                  <span class="stat-value">{{ taskDetailData.data_summary.total_records }} 条</span>
                </div>
              </div>
            </div>
          </div>


          <!-- 错误信息 -->
          <div class="error-section" v-if="taskDetailData.data_error">
            <h4>❌ 错误信息</h4>
            <el-alert :title="taskDetailData.data_error" type="error" :closable="false" />
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showTaskDetail = false">关闭</el-button>
        <el-button type="success" @click="downloadTaskResult(selectedTask)" v-if="selectedTask">
          下载结果文件
        </el-button>
      </template>
    </el-dialog>

    <!-- 参数说明对话框 -->
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
  </div>
</template>

<style scoped>
.maize-yield-main {
  padding: 10px 20px 20px 20px;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.left-column,
.right-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 0; /* 确保列高度一致 */
}

/* 确保左右两列高度平衡 */
.left-column .param-card,
.right-column .param-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.param-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
  background: #fff;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.card-title {
  font-weight: 600;
  font-size: 18px;
  margin-bottom: 16px;
  color: #303133;
  border-bottom: 2px solid #409eff;
  padding-bottom: 8px;
}

.param-description,
.upload-description {
  color: #606266;
  margin-bottom: 20px;
  font-size: 14px;
  line-height: 1.6;
}

/* 系统说明样式 */
.system-description {
  margin-top: 24px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.system-description h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 8px;
}

.system-description p {
  margin: 12px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}

.system-description ul {
  margin: 12px 0;
  padding-left: 20px;
}

.system-description li {
  margin: 8px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}

.system-description strong {
  color: #303133;
  font-weight: 600;
}

.params-form {
  margin-bottom: 20px;
}

.param-help {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}

.param-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.config-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

/* 模型配置样式 */
.model-params-section,
.model-file-section {
  margin-bottom: 32px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

/* 新的模型参数网格布局 */
.model-params-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.model-param-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fff;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.model-param-item label {
  font-size: 13px;
  color: #606266;
  min-width: 140px;
  font-weight: 500;
  flex-shrink: 0;
}

.model-param-item .param-help {
  color: #909399;
  font-size: 12px;
  flex: 1;
}

/* 模型参数按钮组 */
.model-param-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
  margin-top: 20px;
}

/* 归一化参数按钮组 */
.normalization-param-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
  margin-top: 20px;
}

.model-params-section h4,
.model-file-section h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 8px;
}

.model-file-section {
  border-top: 2px solid #409eff;
}

/* 归一化参数样式 */
.normalization-section {
  margin-bottom: 24px;
}

.range-inputs,
.range-inputs-wide {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-separator {
  color: #909399;
  font-weight: 500;
}

.param-grid-wide {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.param-item-wide {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.param-item-wide label {
  font-size: 13px;
  color: #606266;
  min-width: 100px;
  font-weight: 500;
}

.param-grid-compact {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.param-item-compact {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.param-item-compact label {
  font-size: 12px;
  color: #606266;
  min-width: 80px;
  font-weight: 500;
}

.range-inputs-compact {
  display: flex;
  align-items: center;
  gap: 4px;
}

.param-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.param-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.param-item label {
  font-size: 12px;
  color: #606266;
  min-width: 80px;
}

.file-info {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
}

.file-info ul {
  margin: 8px 0;
  padding-left: 20px;
}

.file-info li {
  margin: 4px 0;
  color: #606266;
}

.system-info {
  line-height: 1.8;
  color: #606266;
}

.system-info ul {
  margin: 12px 0;
  padding-left: 20px;
}

.system-info li {
  margin: 6px 0;
}

/* 顶部条布局 */
.header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 20px; /* 顶部下移 */
}

.header-bar .title { 
  font-weight: 600; 
  font-size: 20px; 
  color: #303133;
}

/* 文件上传界面样式 */
.maize-yield-upload {
  padding: 20px;
}

.upload-header {
  margin-bottom: 24px;
}

.multiple-upload-zone {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 30px;
  text-align: center;
  background: #fafafa;
  margin-top: 20px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.multiple-upload-zone:hover {
  border-color: #409eff;
  background: #f0f9ff;
}

.upload-zone-content {
  color: #606266;
}

.upload-zone-content i {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.upload-zone-content p {
  margin: 8px 0;
  font-size: 14px;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 12px;
}

.upload-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.upload-item {
  border: 2px dashed #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
  transition: all 0.3s ease;
  text-align: center;
}

.upload-item:hover,
.upload-item.drag-over {
  border-color: #409eff;
  background: #f0f9ff;
}

.upload-item.drag-over {
  border-style: solid;
  transform: scale(1.02);
}

.file-header {
  margin-bottom: 16px;
}

.file-label {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
  margin-bottom: 4px;
}

.file-desc {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  margin-bottom: 12px;
}

.file-name {
  font-size: 13px;
  color: #67c23a;
  font-weight: 500;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drag-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.upload-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

/* 结果展示样式 */
.outputData {
  margin-top: 20px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

/* 结果头部样式 */
.result-header {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px 8px 0 0;
}

.result-header-content {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.result-header-content i {
  font-size: 20px;
}

/* 结果提示样式 */
.result-alert {
  margin-bottom: 20px;
}

.result-stats {
  margin: 20px 0;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.result-stats h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.stat-icon {
  font-size: 24px;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f9ff;
  border-radius: 50%;
  flex-shrink: 0;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.stat-label {
  font-weight: 500;
  color: #606266;
  font-size: 14px;
}

.stat-value {
  font-weight: 600;
  color: #409eff;
  font-size: 18px;
}



.csv-content {
  margin-top: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.csv-content h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 8px;
}

.csv-container {
  background: #fff;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.csv-text {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
}

.csv-info {
  line-height: 1.6;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.info-label {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.info-value {
  color: #606266;
  font-size: 13px;
  word-break: break-all;
}

.result-note {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #e0f2fe;
  margin-top: 20px;
}

.result-note i {
  color: #409eff;
  font-size: 16px;
}

.result-note span {
  color: #606266;
  font-size: 14px;
}

/* 结果操作按钮样式 */
.result-actions {
  display: flex;
  justify-content: center;
  margin: 20px 0;
  padding: 20px;
  background: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #e0f2fe;
}

/* 新增的任务详情样式 */
.model-name {
  font-size: 12px;
  color: #67c23a;
  font-weight: 500;
}

.input-files-section,
.model-config-section,
.normalization-section {
  margin-top: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.files-grid,
.config-grid,
.param-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.file-item,
.config-item,
.param-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #fff;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.file-label,
.config-label,
.param-label {
  font-weight: 500;
  color: #495057;
  font-size: 13px;
}

.file-value,
.config-value,
.param-value {
  color: #6c757d;
  font-size: 12px;
  font-family: monospace;
  word-break: break-all;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-grid { 
    grid-template-columns: 1fr; 
  }
  
  .left-column,
  .right-column {
    gap: 20px;
  }
  
  .param-grid-compact {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

@media (min-width: 1600px) {
  .content-grid { 
    grid-template-columns: 1fr 1fr; 
  }
}

/* 任务历史样式 */
.task-history {
  padding: 20px;
}

.task-history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.task-count {
  color: #606266;
  font-size: 14px;
}

.task-id {
  font-family: monospace;
  font-size: 12px;
  color: #409eff;
  word-break: break-all;
  line-height: 1.4;
}

.message-text {
  font-size: 12px;
  color: #606266;
  word-break: break-word;
  line-height: 1.4;
}

/* 任务详情样式 */
.task-detail {
  padding: 20px;
}

.task-detail-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.task-info-section,
.result-summary-section,
.data-preview-section,
.error-section {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.task-info-section h4,
.result-summary-section h4,
.data-preview-section h4,
.error-section h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 8px;
}

.preview-note {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 6px;
  border: 1px solid #e0f2fe;
  color: #606266;
  font-size: 14px;
}

.preview-note i {
  color: #409eff;
  font-size: 16px;
}
</style>


