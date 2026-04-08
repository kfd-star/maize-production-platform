import http from '../utils/http/http.js'

const API_BASE = '/api'

// 玉米产量预测主接口
export const runMaizeYield = async (formData) => {
  return http.post(`${API_BASE}/maize_yield`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 获取玉米产量预测参数
export const getMaizeYieldParams = async () => {
  return http.get(`${API_BASE}/parameters/maize_yield`)
}

// 更新玉米产量预测参数
export const updateMaizeYieldParams = async (params) => {
  return http.put(`${API_BASE}/parameters/maize_yield`, params)
}

// 获取默认参数
export const getMaizeYieldDefaults = async () => {
  return http.get(`${API_BASE}/parameters/maize_yield/defaults`)
}

// 获取必需文件列表
export const getMaizeYieldFiles = async () => {
  return http.get(`${API_BASE}/maize_yield/files`)
}

// 获取参数说明
export const getMaizeYieldDescriptions = async () => {
  return http.get(`${API_BASE}/maize_yield/descriptions`)
}

// 获取玉米产量预测任务列表
export const getMaizeYieldTasks = async () => {
  return http.get(`${API_BASE}/maize_yield/tasks`)
}

// 获取特定任务详情
export const getMaizeYieldTask = async (taskId) => {
  return http.get(`${API_BASE}/maize_yield/tasks/${taskId}`)
}

// 删除任务
export const deleteMaizeYieldTask = async (taskId) => {
  return http.del(`${API_BASE}/maize_yield/tasks/${taskId}`)
}

// 下载任务结果文件
export const downloadMaizeYieldResult = async (taskId) => {
  return http.get(`${API_BASE}/maize_yield/download/${taskId}`, {
    responseType: 'blob'
  })
}

// 预览任务结果
export const previewMaizeYieldResult = async (taskId, limit = 100) => {
  return http.get(`${API_BASE}/maize_yield/tasks/${taskId}/preview?limit=${limit}`)
}