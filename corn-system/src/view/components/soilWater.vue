<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const formModel = ref({
  SoilDepth: '', // 土壤深度
  SoilBD: '', // 土壤容重
  SoilLL: '', // 土壤田间持水量
  SoilDUL: '', // 土壤干容重
  SoilSAT: '', // 土壤饱和度
  SoilSC: '', // 土壤盐分含量
  SoilPH: '', // 土壤PH值
  SoilSW: '', // 土壤含水量
  Soil_NO3_N: '', // 土壤硝态氮
  Soil_NH4_N: '', // 土壤铵态氮
  Soil_Total_N: '', // 土壤总氮
  Soil_Organic_C: '', // 土壤有机碳
  SoilType: '', // 土壤类型
  Soilcover: '', // 土壤覆盖率
  windspeed: '', // 风速
  daylight: '', // 日照时数
  averageT: '', // 平均温度
  highestT: '', // 最高温度
  lowestT: '', // 最低温度
  humidity: '', // 湿度
  precipitation: '', // 降水量
})
const formLabels = {
  SoilDepth: '土层深度/cm',
  SoilBD: '土壤容重/g cm3',
  SoilLL: '萎蔫含水量 cm3 cm-3',
  SoilDUL: '田间持水量cm3 cm-3',
  SoilSAT: '饱和含水量cm3 cm-3',
  SoilSC: '饱和导水率 cm d-1',
  SoilPH: '土壤pH值',
  SoilSW: '初始土壤含水量cm3 cm-3',
  Soil_NO3_N: '初始土壤硝态氮含量 mg kg-1',
  Soil_NH4_N: '初始土壤铵态氮含量mg kg-1',
  Soil_Total_N: '土壤全氮含量 g/kg',
  Soil_Organic_C: '土壤有机质含量g/kg',
  SoilType: '土壤类型常数',
  Soilcover: '地表覆盖率',
  windspeed: '风速 m s-1',
  daylight: '日照时数 h',
  averageT: '平均气温 ℃',
  highestT: '最高气温 ℃',
  lowestT: '最低气温 ℃',
  humidity: '空气湿度 %',
  precipitation: '降雨量 mm',
}

const rules = {
  // 浮点型校验规则
  SoilDepth: [
    { required: true, message: '请输入土壤深度', trigger: 'blur' },
    { type: 'number', message: '土壤深度必须为数字', trigger: 'blur' },
  ],
  SoilBD: [
    { required: true, message: '请输入土壤容重', trigger: 'blur' },
    { type: 'number', message: '土壤容重必须为数字', trigger: 'blur' },
  ],
  SoilLL: [
    { required: true, message: '请输入土壤田间持水量', trigger: 'blur' },
    { type: 'number', message: '土壤田间持水量必须为数字', trigger: 'blur' },
  ],
  SoilDUL: [
    { required: true, message: '请输入土壤干容重', trigger: 'blur' },
    { type: 'number', message: '土壤干容重必须为数字', trigger: 'blur' },
  ],
  SoilSAT: [
    { required: true, message: '请输入土壤饱和度', trigger: 'blur' },
    { type: 'number', message: '土壤饱和度必须为数字', trigger: 'blur' },
  ],
  SoilSC: [
    { required: true, message: '请输入土壤盐分含量', trigger: 'blur' },
    { type: 'number', message: '土壤盐分含量必须为数字', trigger: 'blur' },
  ],
  SoilPH: [
    { required: true, message: '请输入土壤PH值', trigger: 'blur' },
    { type: 'number', message: '土壤PH值必须为数字', trigger: 'blur' },
  ],
  SoilSW: [
    { required: true, message: '请输入土壤含水量', trigger: 'blur' },
    { type: 'number', message: '土壤含水量必须为数字', trigger: 'blur' },
  ],
  Soil_NO3_N: [
    { required: true, message: '请输入土壤硝态氮', trigger: 'blur' },
    { type: 'number', message: '土壤硝态氮必须为数字', trigger: 'blur' },
  ],
  Soil_NH4_N: [
    { required: true, message: '请输入土壤铵态氮', trigger: 'blur' },
    { type: 'number', message: '土壤铵态氮必须为数字', trigger: 'blur' },
  ],
  Soil_Total_N: [
    { required: true, message: '请输入土壤总氮', trigger: 'blur' },
    { type: 'number', message: '土壤总氮必须为数字', trigger: 'blur' },
  ],
  Soil_Organic_C: [
    { required: true, message: '请输入土壤有机碳', trigger: 'blur' },
    { type: 'number', message: '土壤有机碳必须为数字', trigger: 'blur' },
  ],
  // 字符串校验规则
  SoilType: [{ required: true, message: '请输入土壤类型', trigger: 'blur' }],
  Soilcover: [{ required: true, message: '请输入土壤覆盖率', trigger: 'blur' }],
  windspeed: [
    { required: true, message: '请输入风速', trigger: 'blur' },
    { type: 'number', message: '风速必须为数字', trigger: 'blur' },
  ],
  daylight: [
    { required: true, message: '请输入日照时数', trigger: 'blur' },
    { type: 'number', message: '日照时数必须为数字', trigger: 'blur' },
  ],
  averageT: [
    { required: true, message: '请输入平均温度', trigger: 'blur' },
    { type: 'number', message: '平均温度必须为数字', trigger: 'blur' },
  ],
  highestT: [
    { required: true, message: '请输入最高温度', trigger: 'blur' },
    { type: 'number', message: '最高温度必须为数字', trigger: 'blur' },
  ],
  lowestT: [
    { required: true, message: '请输入最低温度', trigger: 'blur' },
    { type: 'number', message: '最低温度必须为数字', trigger: 'blur' },
  ],
  humidity: [
    { required: true, message: '请输入湿度', trigger: 'blur' },
    { type: 'number', message: '湿度必须为数字', trigger: 'blur' },
  ],
  precipitation: [
    { required: true, message: '请输入降水量', trigger: 'blur' },
    { type: 'number', message: '数字', trigger: 'blur' },
  ],
}
const outputFormModel = ref({
  ET0: '', // ET0
  ETP: '', // ETP
  ESP: '', // ESP
  ES: '', // ES
  'SW(i,L)': '', // SW(i,L)
})
const outputFormLabels = {
  ET0: '参考作物蒸散量 ',
  ETP: '潜在蒸散量',
  ESP: '潜在蒸腾量',
  ES: '实际蒸发',
  'SW(i,L)': '分层土壤含水量',
}

const submitForm = (formRef) => {
  // 校验逻辑
  formRef.validate((valid) => {
    if (valid) {
      ElMessage.success('输出成功')
      console.log('表单数据:', formModel.value)
    } else {
      ElMessage.error('表单校验失败，请检查输入项！')
      return false
    }
  })
}
</script>

<template>
  <div class="common-layout">
    <div class="inputData">
      <el-container>
        <el-header>算法输入数据</el-header>
        <el-main>
          <el-form
            :model="formModel"
            ref="formRef"
            label-width="220px"
            :rules="rules"
          >
            <el-form-item
              v-for="(value, key) in formModel"
              :key="key"
              :label="formLabels[key]"
              :prop="key"
            >
              <el-input
                v-model.number="formModel[key]"
                placeholder="请输入数据"
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
              :label="outputFormLabels[key]"
            >
              <el-input v-model="outputFormModel[key]"></el-input>
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

<style lang="less" scoped>
.inputData {
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
