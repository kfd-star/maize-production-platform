import http from '../utils/http/http.js'

export const alogr_EnKf = (file, controller) => {
  console.log('开始调用 EnKF 算法')

  const url = '/api/EnKf'
  // 构造 FormData 对象
  const formData = new FormData()
  console.log('file', file)

  formData.append('inputFile', file) // 'inputFile' 是后端接收的字段名
  const config = {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  }
  if (controller) {
    config.signal = controller.signal
  }
  return http.post(url, formData, config)
}
export const alogr_pf = (file) => {
  const url = '/api/alogyPf'
  // 构造 FormData 对象
  const formData = new FormData()
  console.log('file', file)

  formData.append('inputFile', file) // 'file' 是后端接收的字段名

  return http.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 300000,
  })
}
//下载 在http.get请求中设置config参数
export function downloadFolder(folderPath) {
  const url = `/api/download?output_path=${folderPath}`
  // 不需要 encodeURIComponent，这会导致“二次编码”
  return http.get(url, { responseType: 'blob' })
}

//editor 编辑数据接口
export const editorData = (data) => {
  const RowReplaceRequest = data
  return http.post('/api/edit', RowReplaceRequest)
}
// editor 删除数据接口
export const deleteData = (data) => {
  const RowReplaceRequest = data
  return http.post('/api/delete', RowReplaceRequest)
}
//获取所有的excel 文件，用于导入数据
export const getAllExcel = () => {
  const url = `/api/getFilesName`
  return http.get(url)
}

//读取excel文件数据，用于数据导入
export const getInputData = (filequery) => {
  const url = `/api/validate_file`
  console.log(filequery)

  return http.get(url, { params: filequery })
}

//用于冠状光合算法请求文件夹下所有文件的接口
export const getShineFiles = () => {
  const url = `/api/ShineFiles`

  return http.get(url)
}
export const getShineFilesPath = (params) => {
  const url = `/api/ShineFilePath`

  return http.get(url, {
    params: params,
  })
}
