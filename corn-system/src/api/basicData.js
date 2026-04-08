import http from '../utils/http/http.js'

// 基础数据管理API接口

// 上传文件
export const uploadFile = (file, category) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('category', category)
  
  return http.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000 // 60秒超时
  })
}

// 获取文件列表
export const getFiles = (category = null) => {
  const params = category ? { category } : {}
  return http.get('/api/files', { params })
}

// 获取 JSON 基础数据文件列表（从后端列目录）
export const getJsonFiles = (category) => {
  return http.get('/api/json_files', {
    params: { category }
  })
}

// 上传 JSON 基础数据文件
export const uploadJsonFile = (file, category) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('category', category)
  return http.post('/api/json_files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000
  })
}

// 保存（覆盖）JSON 基础数据文件
export const saveJsonFile = (data) => {
  return http.post('/api/json_files/save', data)
}

// 删除 JSON 基础数据文件
export const deleteJsonFile = (category, filename) => {
  return http.del(`/api/json_files/${category}/${filename}`)
}

// 获取文件内容
export const getFileContent = (name, category) => {
  return http.get('/api/getFiles', {
    params: { name, category }
  })
}

// 验证文件格式
export const validateFile = (fileName, algorithm, category) => {
  return http.get('/api/validate_file', {
    params: { fileName, algorithm, category }
  })
}

// 编辑行数据
export const editRow = (data) => {
  return http.post('/api/edit', data)
}

// 删除行数据
export const deleteRow = (data) => {
  return http.post('/api/delete', data)
}

// 添加行数据
export const addRow = (data) => {
  return http.post('/api/add', data)
}

// 删除文件
export const deleteFile = (filename, category) => {
  return http.del(`/api/file/${category}/${filename}`)
}

// 修改列名
export const renameColumn = (data) => {
  return http.post('/api/rename_column', data)
}

// 删除列
export const deleteColumn = (data) => {
  return http.post('/api/delete_column', data)
}

// 保存整个文件
export const saveFile = (data) => {
  return http.post('/api/save_file', data)
}

// 获取数据分类信息
export const getCategories = () => {
  return http.get('/api/categories')
}

export default {
  uploadFile,
  getFiles,
  getJsonFiles,
  uploadJsonFile,
  saveJsonFile,
  deleteJsonFile,
  getFileContent,
  validateFile,
  editRow,
  deleteRow,
  addRow,
  deleteFile,
  getCategories
}
