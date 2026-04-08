<script setup>
import alogrTable from '@/view/alogrTable.vue'
import { storeToRefs } from 'pinia'
import { useStore } from '../../store/index.js'
import bus from '../../utils/EventBus.js'
import { ref, onMounted } from 'vue'
import { alogr_EnKf, alogr_pf } from '@/api/alogrPy.js'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, emitChangeFn } from 'element-plus'
import loadingMask from './component/loadingMask.vue'
const router = useRouter()
const { tableShow, algorshow, mapShow } = storeToRefs(useStore())
const totalAlgor = ref()
onMounted(() => {
  algorshow.value = true
})
const loading = ref(false)
//对话框控制变量
const dialogVisible = ref(false)
bus.on('showalgor', (item) => {
  //console.log(item);
  mapShow.value = false
  tableShow.value = false
  algorshow.value = true
})

const algoritem = ref([
  { title: 'LAI同化算法', key: 'lai', level: 2, icon: '1' },
  { title: '玉米生长模拟', key: 'shine', level: 2, icon: '5' },
  { title: '玉米产量预测', key: 'production', level: 2, icon: '7' },
  { title: '玉米产量预测区域版（API1）', key: 'maizeEstimate', level: 2, icon: '7' },
  { title: '玉米产量预测区域版（GNAH）', key: 'gnah', level: 2, icon: '7' },
  // 已隐藏的算法：
  // { title: '土壤水分模拟', key: 'soilwater', level: 2, icon: '2' },
  // { title: '生产力预测', key: 'field', level: 2, icon: '3' },
  // { title: '冠层光合模拟', key: 'photosy', level: 2, icon: '4' },
])

const getIconUrl = (icon) =>
  new URL(`../../assets/img/${icon}.png`, import.meta.url).href

const openAlgor = (item) => {
  if (item.key === 'lai') {
    algorshow.value = false
    router.push('/home/lai')
  } else if (item.key === 'shine') {
    algorshow.value = false
    router.push('/home/shine')
  } else if (item.key === 'production') {
    algorshow.value = false
    router.push('/home/production')
  } else if (item.key === 'maizeEstimate') {
    algorshow.value = false
    router.push('/home/maizeEstimate')
  } else if (item.key === 'gnah') {
    algorshow.value = false
    router.push('/home/gnah')
  }
  // 已移除的算法路由：
  // else if (item.key === 'soilwater') { ... }
  // else if (item.key === 'field') { ... }
  // else if (item.key === 'photosy') { ... }
}

const algorMaizevalue = ref('') //用于控制select选择器选择哪一个算法 与 alogrMaize.value 绑定
//用于select组件中option选项的值
const algorMaize = ref([
  {
    name: '基于EnKF（集合卡尔曼滤波）的站点',
    title: 'MaizeSM_EnKF',
    value: 'EnKF',
  },
  { name: '基于PF（粒子滤波）的站点', title: 'MaizeSM_EnKF', value: 'alogyPf' },
  {
    name: '基于NLS-4DVAR（粒子滤波）的站点',
    title: 'MaizeSM_NLS-4DVAR',
    value: 'NLS-4DVAR',
  },
  { name: '基于UKF（粒子滤波）的站点', title: 'MaizeSM_UKF', value: 'UKF' },
])

const selectedFileName = ref('') // 用于存储选中的文件的文件名
const selectedFile = ref(null) // 用于存储选中的文件
const fileInput = ref(null) // 通过 ref 来触发click点击事件  fileInput绑定了一个input标签
const dialongTitle = ref(null) //对话框标题
// 模拟点击文件选择框
const handleFileChange = (event) => {
  const file = event.target.files[0]
  selectedFile.value = file // 存储选中的文件
  if (file) {
    selectedFileName.value = file.name // 更新文件名
  }
}
const triggerFileInput = () => {
  fileInput.value.click() // 通过 .value 访问 DOM 元素并触发点击事件
}
//这个是lai同化算法处理函数
const visibleTable = async () => {
  if (!algorMaizevalue.value) {
    ElMessageBox.alert('请选择算法', '温馨提示', {
      confirmButtonText: '确认',
      callback: () => {},
    })
    return
  }
  if (!selectedFile.value) {
    ElMessageBox.alert('请上传文件', '温馨提示', {
      confirmButtonText: '确认',
    })
    return
  }

  try {
    dialogVisible.value = false // 关闭对话框
    loading.value = true
    controller.value = new AbortController() // 创建控制器
    let res
    // 根据算法类型调用不同接口
    if (algorMaizevalue.value === 'EnKF') {
      // res = await alogr_EnKf(selectedFile.value, controller.value)
      res = await new Promise((resolve, reject) => {
        setTimeout(() => {
          resolve(alogr_EnKf(selectedFile.value, controller.value))
        }, 120 * 1000)
      })
    } else if (algorMaizevalue.value === 'alogyPf') {
      res = await alogr_pf(selectedFile.value)
    } else {
      // 未知算法类型
      res = await alogr_EnKf(selectedFile.value)
    }

    loading.value = false
    Data.value = res.data
    ElMessage({
      message: '计算成功',
      type: 'success',
    })

    // 清理状态
    algorshow.value = false // 隐藏算法列表
    algorMaizevalue.value = ''
    selectedFileName.value = ''
    selectedFile.value = null
    if (fileInput.value) {
      fileInput.value.value = ''
    }

    showAlogrTable.value = true // 显示表格
    console.log('上传成功', res.data)
    /* // 调用 EnKF 算法处理选中的文件 上传成功将返回结果给tableData
    const res = await alogr_EnKf(selectedFile.value)
    loading.value = false
    Data.value = res.data
    ElMessage({
      message: '计算成功',
      type: 'success',
    })
    algorshow.value = false // 隐藏算法列表
    algorMaizevalue.value = ''
    selectedFileName.value = ''
    selectedFile.value = null
    if (fileInput.value) {
      fileInput.value.value = ''
    }
    showAlogrTable.value = true // 显示表格
    console.log('上传成功', res.data) */
  } catch (err) {
    if (err.name === 'CanceledError' || err.message === 'canceled') {
      loading.value = false
      ElMessage.info('计算已取消')
    } else {
      loading.value = false
      ElMessage.error('上传失败，请稍后再试')
    }
  } finally {
    loading.value = false
    controller.value = null
  }
}

const showAlogrTable = ref(false) //展示算法表格
const Data = ref() //算法表格数据
const controller = ref(null) // 用于取消请求的控制器
const handleCancelRequest = () => {
  if (controller) {
    controller.value.abort() //  使用 value
    controller.value = null
  }
  loading.value = false
}
</script>

<template>
  <loadingMask
    v-model:loading="loading"
    @cancelReq="handleCancelRequest"
  ></loadingMask>
  <div class="contain" v-if="algorshow">
    <el-container>
      <el-main>
        <div class="algor">
          <el-card
            v-for="(item, index) in algoritem"
            :key="item.key"
            @click="openAlgor(item)"
          >
            <img
              :src="getIconUrl(item.icon)"
              style="width: 60%; background-size: 100% 100%"
            />
            <template #footer>{{ item.title }}</template>
          </el-card>
        </div>
      </el-main>
    </el-container>

    <!-- 弹出对话框 专属于lai同化算法 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialongTitle"
      style="position: fixed; top: 150px; left: 700px"
      width="500px"
    >
      <!-- slot="append" 放置一个原生 input[type=file] 选择文件 -->
      <div>
        <div class="elselect" style="">
          <span>选择算法:</span>
          <el-select
            v-model="algorMaizevalue"
            placeholder="Select"
            size="large"
            style="width: 240px"
          >
            <el-option
              v-for="item in algorMaize"
              :value="item.value"
              :label="item.name"
            ></el-option>
          </el-select>
        </div>
        <div class="inputbox">
          <el-button @click="triggerFileInput" style="border: 2px solid black">
            点击导入参数文件:</el-button
          >
          <span v-if="selectedFileName" style="margin-left: 10px">{{
            selectedFileName
          }}</span>
          <input
            type="file"
            @change="handleFileChange"
            style="display: none; line-height: 30px"
            ref="fileInput"
          />
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="visibleTable"> 确认 </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
  <!-- 表格 -->
  <alogrTable
    v-if="showAlogrTable"
    :data="{
      Data: Data,
      algorMaizevalue: algorMaizevalue,
    }"
    @closeAlogrTable="
      () => {
        showAlogrTable = false
        algorshow = true
      }
    "
  ></alogrTable>
</template>

<style scoped>
.el-main {
  .algor {
    display: flex; /* 使用弹性布局 */
    flex-wrap: wrap; /* 允许换行，分成两行显示 */
    gap: 30px; /* 设置卡片之间的间距 */
    justify-content: center; /* 居中对齐 */
    align-items: center; /* 垂直居中对齐 */
    padding: 20px;
    .el-card {
      box-sizing: border-box;
      width: calc(50% - 15px); /* 每行2个，每个占50%减去间距的一半 */
      max-width: 480px; /* 保持原来的最大宽度限制 */
      min-width: 300px; /* 设置最小宽度，确保在小屏幕上也能正常显示 */
      flex-grow: 0; /* 防止卡片扩大 */
      flex-shrink: 0; /* 防止卡片缩小 */
      justify-content: center;
      text-align: center;
    }
  }
}
.el-card:hover {
  box-shadow: 0px 4px 20px rgba(169, 16, 16, 0.1); /* 添加自定义阴影 */
  border: 1px solid #2d1ed6; /* 鼠标悬停时改变背景色 */
  cursor: pointer; /* 鼠标悬停时变成手型 */
}

.elselect {
  display: flex; /* 设置为弹性布局 */
  align-items: center; /* 垂直居中对齐 */
  gap: 20px; /* 设置子元素之间的间距为20px */
  margin-bottom: 20px;
  span {
    margin-left: 16px;
    margin-right: 40px;
    font-size: 16px;
    line-height: 40px;
  }
}
.inputbox {
  display: flex;
  margin: 0 5px 5px 5px;
  align-items: center;
  height: 30;
  border: 1px solid #e5dbdb;
  .el-button {
    font-size: 16px;
  }
}
.el-table {
  height: 800px;
}
</style>
