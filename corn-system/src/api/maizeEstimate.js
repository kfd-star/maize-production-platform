import http from '../utils/http/http.js'

const API_BASE = '/api'

// Maize_Yield_API1主接口（支持文件夹路径或文件上传）
export const runMaizeEstimate = async (formData, controller = null) => {
  const config = {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 600000 // 10分钟超时（预测任务可能需要较长时间）
  }
  if (controller) {
    config.signal = controller.signal
  }
  return http.post(`${API_BASE}/maize_estimate`, formData, config)
}

// 获取Maize_Yield_API1参数
export const getMaizeEstimateParams = async () => {
  return http.get(`${API_BASE}/parameters/maize_estimate`)
}

// 更新Maize_Yield_API1参数
export const updateMaizeEstimateParams = async (params) => {
  return http.put(`${API_BASE}/parameters/maize_estimate`, params)
}

// 获取默认参数
export const getMaizeEstimateDefaults = async () => {
  return http.get(`${API_BASE}/parameters/maize_estimate/defaults`)
}

// 获取Maize_Yield_API1任务列表
export const getMaizeEstimateTasks = async () => {
  return http.get(`${API_BASE}/maize_estimate/tasks`)
}

// 获取特定任务详情
export const getMaizeEstimateTask = async (taskId) => {
  return http.get(`${API_BASE}/maize_estimate/tasks/${taskId}`)
}

// 删除任务
export const deleteMaizeEstimateTask = async (taskId) => {
  return http.del(`${API_BASE}/maize_estimate/tasks/${taskId}`)
}

// 下载任务结果文件
export const downloadMaizeEstimateResult = async (taskId, format = 'geojson') => {
  return http.get(`${API_BASE}/maize_estimate/download/${taskId}?format=${format}`, {
    responseType: 'blob'
  })
}

// 预览任务结果
export const previewMaizeEstimateResult = async (taskId, limit = 100) => {
  return http.get(`${API_BASE}/maize_estimate/tasks/${taskId}/preview?limit=${limit}`)
}

// 取消正在运行的任务
export const cancelMaizeEstimateTask = async (taskId) => {
  return http.post(`${API_BASE}/maize_estimate/tasks/${taskId}/cancel`)
}
