import axios from 'axios'
import { ElMessage } from 'element-plus'
// 1. 创建axios实例
const instance = axios.create({})
// 2.请求拦截
instance.interceptors.request.use(
  (config) => {
    let token = sessionStorage.getItem('token')
    if (token) {
      config.headers['token'] = token
    }
    config.timeout = config.timeout || 50000
    return config
  },
  (error) => {
    //  请求发生错误，抛出异常
    Promise.reject(error)
  },
)

// 3.响应拦截
instance.interceptors.response.use(
  (res) => {
    return res
  },
  (error) => {
    if (error && error.response) {
      const status = error.response.status
      const data = error.response.data || {}
      const detail = data.error || data.detail || data.message
      // 优先使用后端返回的明确错误信息
      if (detail) {
        ElMessage.error(typeof detail === 'string' ? detail : '请求失败')
      } else {
        switch (status) {
          case 400:
            ElMessage.error('请求错误')
            break
          case 401:
            ElMessage.error('未授权，请重新登录')
            break
          case 403:
            ElMessage.error('拒绝访问')
            break
          case 404:
            ElMessage.error('请求错误，未找到相应的资源')
            break
          case 408:
            ElMessage.error('请求超时')
            break
          case 500:
            ElMessage.error('服务器内部错误')
            break
          default:
            ElMessage.error('请求失败')
        }
      }
    } else {
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        ElMessage.error('服务器响应超时，请刷新页面')
      } else if (error.code === 'ERR_UPLOAD_FILE_CHANGED') {
        ElMessage.error('上传过程中文件被修改，请重新选择文件后重试')
      }
    }
    return Promise.reject(error)
  },
)
// 4.导出 axios 实例
export default instance
