<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useStore } from '../../store'

const { tableShow, algorshow, mapShow } = useStore()
import { getShineFiles, getShineFilesPath } from '@/api/alogrPy'
const router = useRouter()
const shineUploadUrl =
  import.meta.env.VITE_APP_SHINE_UPLOAD_URL || '/api/ShineUpload'
onMounted(async () => {
  const res = await getShineFiles()
  console.log(res)
  res.data.files.forEach((item) => {
    const option = {
      value: item,
      label: item,
    }
    options.push(option)
  })
})
const formModel = ref({
  DATE: '', // 日期
  TIME: '', // 时间
  parlon: '', // 经度
  parlat: '', // 纬度
  inlight: '', // 光照强度
  scalight: '', // 散射光强度
  Angle: '', // 角度
  path: '', // 路径
})

const formLabels = {
  DATE: '日期',
  TIME: '时间',
  parlon: '经度',
  parlat: '纬度',
  inlight: '光照强度',
  scalight: '散射光强度',
  Angle: '角度',
  path: '选择文件路径',
}

const rules = {
  DATE: [
    { required: true, message: '请输入日期', trigger: 'blur' },
    {
      type: 'date',
      message: '请输入正确的日期格式，例如：YYYY-MM-DD',
      trigger: 'blur',
    },
  ],
  parlon: [
    { required: true, message: '请输入经度', trigger: 'blur' },
    { type: 'number', message: '经度必须为数字', trigger: 'blur' },
  ],
  parlat: [
    { required: true, message: '请输入纬度', trigger: 'blur' },
    { type: 'number', message: '纬度必须为数字', trigger: 'blur' },
  ],
  inlight: [
    { required: true, message: '请输入光照强度', trigger: 'blur' },
    { type: 'number', message: '光照强度必须为数字', trigger: 'blur' },
  ],
  scalight: [
    { required: true, message: '请输入散射光强度', trigger: 'blur' },
    { type: 'number', message: '散射光强度必须为数字', trigger: 'blur' },
  ],
  Angle: [
    { required: true, message: '请输入角度', trigger: 'blur' },
    { type: 'number', message: '角度必须为数字', trigger: 'blur' },
  ],
}

const submitForm = (formRef) => {
  formRef.validate((valid) => {
    if (valid) {
      ElMessage.success('表单校验通过，可以提交！')
      console.log('表单数据:', formModel.value)
    } else {
      ElMessage.error('表单校验失败，请检查输入项！')
      return false
    }
  })
}

const outputFormModel = ref({
  crownScroe: '',
})
const outputFormModellabes = ref({
  crownScroe: ' 冠隙分数',
})
const goBack = () => {
  router.push('/home/algor')
}
//上传成功提示
const handleSuccess = () => {
  ElMessage.success('上传成功')
}
//路径字段的相关处理
const selectname = ref('')
const options = []
const handleSelectChange = async () => {
  const params = {
    filename: selectname.value,
  }
  const res = await getShineFilesPath(params)
  console.log(res)
  //保存文件路径
  formModel.value.path = res.data.path
}
</script>

<template>
  <div class="common-layout">
    <div class="inputData">
      <el-container>
        <el-header style="position: relative">
          算法输入数据
          <el-upload
            :action="shineUploadUrl"
            :show-file-list="false"
            :on-success="handleSuccess"
            style="position: absolute; right: 100px; top: 0"
          >
            <el-button type="primary">上传冠状路径参数文件</el-button>
          </el-upload>
          <el-button
            type="primary"
            style="position: absolute; right: 20px"
            @click="goBack"
            >返回</el-button
          >
        </el-header>
        <el-main>
          <el-form
            :model="formModel"
            ref="formRef"
            label-width="160px"
            :rules="rules"
          >
            <el-form-item
              v-for="(value, key) in formModel"
              :key="key"
              :label="formLabels[key]"
              :prop="key"
            >
              <!-- 日期选择器 -->
              <el-date-picker
                v-if="key === 'DATE'"
                v-model="formModel[key]"
                type="date"
                placeholder="请选择日期"
              ></el-date-picker>
              <!-- 时间输入框，不需要校验 -->
              <el-time-picker
                v-else-if="key === 'TIME'"
                v-model="formModel[key]"
                placeholder="请选择时间"
              ></el-time-picker>
              <!-- 文件选择框 -->
              <el-select
                v-else-if="key === 'path'"
                v-model="selectname"
                placeholder="Select"
                style="width: 240px"
                @change="handleSelectChange"
              >
                <el-option
                  v-for="item in options"
                  :key="item.value"
                  :value="item.value"
                />
              </el-select>
              <!-- 其他输入框 -->
              <el-input
                v-else
                v-model.number="formModel[key]"
                placeholder="请输入对应数据"
              ></el-input>
            </el-form-item>
          </el-form>
        </el-main>
      </el-container>
    </div>
    <div class="outputData">
      <el-container>
        <el-header>输出数据</el-header>
        <el-main>
          <el-form :model="outputFormModel" label-width="220px">
            <el-form-item
              v-for="(value, key) in outputFormModel"
              :key="key"
              :label="outputFormModellabes[key]"
              :prop="key"
            >
              <el-input
                v-model.number="outputFormModel[key]"
                placeholder="请输入数据"
              ></el-input>
            </el-form-item>
          </el-form>
          <div class="el-button-container">
            <el-button type="primary" @click="submitForm($refs.formRef)">
              输出
            </el-button>
          </div>
        </el-main>
      </el-container>
    </div>
  </div>
</template>

<style scoped lang="less">
.inputData {
  .el-form {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    justify-content: flex-start;
    .el-form-item {
      width: 480px;
      box-sizing: border-box;
      display: flex;
      align-items: center;
      gap: 10px;
      .el-time-picker {
        width: 220px;
      }
      .el-button {
        line-height: 32px;
      }
    }
  }
}

.outputData {
  margin-top: 20px;
  .el-form {
    width: 100%; /* 表单宽度 */
    display: flex; /* 使用 flex 布局 */
    flex-wrap: wrap; /* 自动换行 */
    gap: 20px; /* 表单项之间的间距 */
    justify-content: flex-start; /* 左对齐（或使用 space-between/center 来调整布局） */
    .el-form-item {
      width: 480px; /* 每个表单项固定宽度 */
      box-sizing: border-box; /* 确保 padding 不影响宽度 */
      display: flex; /* 使内部子元素在一行排列 */
      align-items: center; /* 垂直居中对齐 */
      gap: 10px; /* 设置子元素之间的间距 */
      .el-input {
        flex: 1; /* 输入框占据剩余宽度 */
      }
    }
  }
  .el-button-container {
    display: flex; /* 使用 flex 布局 */
    justify-content: flex-end; /* 将按钮放在最右侧 */
    width: 100%; /* 占满父容器宽度 */
    margin-top: 20px; /* 添加顶部间距 */
  }
}
</style>
