import http from '../utils/http/http.js'

// 使用 Vite 代理，统一走同源 /api，避免跨域
const API_BASE = '/api'

// 执行四种算法（文件上传）
export const runEnKF = (file, controller) => {
  const url = `${API_BASE}/EnKf`
  const formData = new FormData()
  formData.append('inputFile', file)
  const config = { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 300000 }
  if (controller) config.signal = controller.signal
  return http.post(url, formData, config)
}

export const runUKF = (file, controller) => {
  const url = `${API_BASE}/UKF`
  const formData = new FormData()
  formData.append('inputFile', file)
  const config = { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 300000 }
  if (controller) config.signal = controller.signal
  return http.post(url, formData, config)
}

export const runPF = (file, controller) => {
  const url = `${API_BASE}/PF`
  const formData = new FormData()
  formData.append('inputFile', file)
  const config = { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 300000 }
  if (controller) config.signal = controller.signal
  return http.post(url, formData, config)
}

export const runNLS4DVar = (file, controller) => {
  const url = `${API_BASE}/NLS4DVar`
  const formData = new FormData()
  formData.append('inputFile', file)
  const config = { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 300000 }
  if (controller) config.signal = controller.signal
  return http.post(url, formData, config)
}

// 参数获取与更新
export const getParams = (algo) => http.get(`${API_BASE}/parameters/${algo}`)
export const updateParams = (algo, params) => http.put(`${API_BASE}/parameters/${algo}`, params)

// 全局配置
export const getConfig = () => http.get(`${API_BASE}/parameters/config`)
export const updateConfig = (cfg) => http.put(`${API_BASE}/parameters/config`, cfg)
export const listControlFiles = () => http.get(`${API_BASE}/parameters/config/control-files`)
export const chooseControlFile = (filename) =>
  http.put(`${API_BASE}/parameters/config/control-file`, null, { params: { filename } })
export const getOptions = () => http.get(`${API_BASE}/parameters/options`)
export const getDescriptions = () => http.get(`${API_BASE}/parameters/description`)

// 任务模式API
export const startTask = (algo, file) => {
  const url = `${API_BASE}/tasks?algo=${algo}`
  const formData = new FormData()
  formData.append('inputFile', file)
  const config = { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 300000 }
  return http.post(url, formData, config)
}

export const getTask = (taskId) => http.get(`${API_BASE}/tasks/${taskId}`)

export const cancelTask = (taskId) => http.del(`${API_BASE}/tasks/${taskId}`)

// LAI任务历史管理
export const getLAITasks = async () => {
  return http.get(`${API_BASE}/lai/tasks`)
}

export const getLAITask = async (taskId) => {
  return http.get(`${API_BASE}/lai/tasks/${taskId}`)
}

export const deleteLAITask = async (taskId) => {
  return http.del(`${API_BASE}/lai/tasks/${taskId}`)
}

export const downloadLAIResult = async (taskId, fileType = 'summary') => {
  return http.get(`${API_BASE}/lai/download/${taskId}?file_type=${fileType}`, {
    responseType: 'blob'
  })
}

export const previewLAIResult = async (taskId, limit = 100) => {
  return http.get(`${API_BASE}/lai/tasks/${taskId}/preview?limit=${limit}`)
}

