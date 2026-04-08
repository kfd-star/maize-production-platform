import http from '../utils/http/http.js'

const API_BASE = '/api'

// SCYM主接口（支持文件上传）
export const runScym = async (formData, controller = null) => {
  const config = {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 3600000 // 1小时超时（SCYM任务可能需要较长时间）
  }
  if (controller) {
    config.signal = controller.signal
  }
  return http.post(`${API_BASE}/scym/predict`, formData, config)
}

// 获取SCYM参数
export const getScymParams = async () => {
  return http.get(`${API_BASE}/parameters/scym`)
}

// 更新SCYM参数
export const updateScymParams = async (params) => {
  return http.put(`${API_BASE}/parameters/scym`, params)
}

// 获取SCYM默认参数
export const getScymDefaults = async () => {
  return http.get(`${API_BASE}/parameters/scym/defaults`)
}

// 获取SCYM任务列表
export const getScymTasks = async () => {
  return http.get(`${API_BASE}/scym/tasks`)
}

// 获取特定任务详情
export const getScymTask = async (taskId) => {
  return http.get(`${API_BASE}/scym/tasks/${taskId}`)
}

// 删除任务
export const deleteScymTask = async (taskId) => {
  return http.del(`${API_BASE}/scym/tasks/${taskId}`)
}

// 下载任务结果文件
export const downloadScymResult = async (taskId, format = 'tif') => {
  return http.get(`${API_BASE}/scym/download/${taskId}?format=${format}`, {
    responseType: 'blob'
  })
}

// 取消正在运行的任务
export const cancelScymTask = async (taskId) => {
  return http.post(`${API_BASE}/scym/tasks/${taskId}/cancel`)
}
