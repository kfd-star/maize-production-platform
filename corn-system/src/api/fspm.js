import http from '../utils/http/http.js'

// 使用 Vite 代理，统一走同源 /api，避免跨域
const API_BASE = '/api'

// FSPM参数管理
export function getFSPMParameters() {
  return http.get(`${API_BASE}/parameters/fspm`)
}

export function updateFSPMParameters(data) {
  return http.put(`${API_BASE}/parameters/fspm`, data)
}

export function getFSPMDefaults() {
  return http.get(`${API_BASE}/parameters/fspm/defaults`)
}

export function getFSPMDescriptions() {
  return http.get(`${API_BASE}/fspm/descriptions`)
}

export function getFSPMFiles() {
  return http.get(`${API_BASE}/fspm/files`)
}

// FSPM任务管理
export function startFSPMTask(formData) {
  return http.post(`${API_BASE}/fspm/start`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000
  })
}

export function getFSPMTaskStatus(taskId) {
  return http.get(`${API_BASE}/fspm/status/${taskId}`)
}

export function cancelFSPMTask(taskId) {
  return http.post(`${API_BASE}/fspm/cancel/${taskId}`)
}

export function listFSPMTasks() {
  return http.get(`${API_BASE}/fspm/tasks`)
}

export function deleteFSPMTask(taskId) {
  return http.del(`${API_BASE}/fspm/tasks/${taskId}`)
}

// FSPM直接执行（同步方式）
export function runFSPM(formData) {
  return http.post(`${API_BASE}/fspm`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000
  })
}
