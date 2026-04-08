import * as XLSX from 'xlsx'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api/table'
import { useMenuConfig } from '@/store/index'
import { onMounted } from 'vue'
const useMenu = useMenuConfig()

//需要传入一个Buffer流  适用于get请求
export const excelHandle = (arrayBuffer) => {
  const workbook = XLSX.read(arrayBuffer, { type: 'array' }) //  解析 Excel 得到一个workbook工作对象

  const sheets = {} //  创建一个对象，用来存储所有sheet页的数据
  const columns = {} //  创建一个对象，用来存储所有sheet页的表头
  const sheetNames = workbook.SheetNames //  获取所有sheet表的名称 如表 表2
  workbook.SheetNames.forEach((sheetName) => {
    const worksheet = workbook.Sheets[sheetName]
    const jsonData = XLSX.utils.sheet_to_json(worksheet, { defval: '' })
    // 获取表头
    const headerData = XLSX.utils.sheet_to_json(worksheet, {
      header: 1,
      defval: '',
    })
    const headers = headerData.length > 0 ? headerData[0] : [] // 取第一行表头
    sheets[sheetName] = jsonData
    columns[sheetName] = headers
  })
  return { sheets, columns, sheetNames }
}
//上传文件处理  分两步 第一步 先解析文件第二步再上传文件
export const savaFile = (file) => {
  return new Promise((resolve, reject) => {
    //  FileReader 是异步的，它的 onload 事件会在 readAsArrayBuffer 之后触发。
    // return jsonData; 会在 onload 事件之前执行，所以 jsonData 还是 undefined。
    const reader = new FileReader()
    reader.readAsArrayBuffer(file)
    reader.onload = async function (e) {
      //第一步先解析excel文件
      const arrayBuffer = e.target.result
      const { sheets, columns, sheetNames } = excelHandle(arrayBuffer)
      try {
        //  解析完成后，上传文件
        const res = await api.savaFileServe(file)
        const { filename } = res.data
        const cleanFilename = filename.normalize('NFC')
        const forefilename =
          cleanFilename.substring(0, cleanFilename.lastIndexOf('.')) ||
          cleanFilename
        console.log(forefilename)
        const pushObj = {
          title: forefilename,
          key: forefilename,
          type: 'table',
          level: 3,
        }
        useMenu.addFileToMenu(pushObj)
        ElMessage({
          message: '上传成功',
          type: 'success',
        })
        resolve({ sheets, columns, sheetNames })
      } catch (error) {
        if (error.response && error.response.status === 409) {
          ElMessage({
            message: '上传失败: 文件名已存在，禁止上传',
            type: 'error',
            showClose: true,
          })
        }
        throw error // 继续抛出错误，避免影响后续代码
      }
    }
    //文件读取失败触发的 reject
    reader.onerror = function (error) {
      reject(error)
    }
  })
}
