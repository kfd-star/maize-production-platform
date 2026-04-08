import http from '../utils/http/http.js'

const API_BASE = '/api'

// GNAH主接口（支持文件上传）
export const runGNAH = async (formData, controller = null) => {
  const config = {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 3600000 // 1小时超时（预测任务可能需要较长时间）
  }
  if (controller) {
    config.signal = controller.signal
  }
  return http.post(`${API_BASE}/gnah`, formData, config)
}

// 获取GNAH参数
export const getGNAHParams = async () => {
  return http.get(`${API_BASE}/parameters/gnah`)
}

// 更新GNAH参数
export const updateGNAHParams = async (params) => {
  return http.put(`${API_BASE}/parameters/gnah`, params)
}

// 获取默认参数
export const getGNAHDefaults = async () => {
  return http.get(`${API_BASE}/parameters/gnah/defaults`)
}

// 获取GNAH任务列表
export const getGNAHTasks = async () => {
  return http.get(`${API_BASE}/gnah/tasks`)
}

// 获取特定任务详情
export const getGNAHTask = async (taskId) => {
  return http.get(`${API_BASE}/gnah/tasks/${taskId}`)
}

// 删除任务
export const deleteGNAHTask = async (taskId) => {
  return http.del(`${API_BASE}/gnah/tasks/${taskId}`)
}

// 下载任务结果文件
export const downloadGNAHResult = async (taskId, format = 'tif') => {
  return http.get(`${API_BASE}/gnah/download/${taskId}?format=${format}`, {
    responseType: 'blob'
  })
}

// 预览任务结果
export const previewGNAHResult = async (taskId) => {
  return http.get(`${API_BASE}/gnah/tasks/${taskId}/preview`, {
    responseType: 'blob'
  })
}

// 取消正在运行的任务
export const cancelGNAHTask = async (taskId) => {
  return http.post(`${API_BASE}/gnah/tasks/${taskId}/cancel`)
}
