<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useStore } from '../../store'
import inputData from '@/router/algor/inputData.vue'

const { tableShow, algorshow, mapShow } = useStore()
const router = useRouter()

const formModel = ref({
  DATE: '', // 日期
  LAI: '', // 叶面积指数
  LightExtinctionCoefficient: '', // 光截获系数
  AveAirTemperature: '', // 平均气温
  SunshineDuration: '', // 日照时长
  CO2_ParPressure_Mesophyll: '', // CO2分压
  V_cmax_25: '', // Vcmax(25度)
  V_cmax_opt: '', // Vcmax
  V_cmax_beta: '', // Vcmax
  V_pmax_25: '', // Vpmax(25度)
  V_pmax_opt: '', // Vpmax
  V_pmax_beta: '', // Vpmax
  J_max_25: '', // Jmax(25度)
  J_max_opt: '', // Jmax
  J_max_beta: '', // Jmax
  R_day_25: '', // Rday(25度)
  R_day_opt: '', // Rday
  R_day_beta: '', // Rday
})

const formLabels = {
  DATE: '日期',
  LAI: '叶面积指数',
  LightExtinctionCoefficient: '光截获系数',
  AveAirTemperature: '平均气温',
  SunshineDuration: '日照时长',
  CO2_ParPressure_Mesophyll: 'CO2分压',
  V_cmax_25: 'Vcmax(25度)',
  V_cmax_opt: 'Vcmax_opt',
  V_cmax_beta: 'Vcmax_beta',
  V_pmax_25: 'Vpmax(25度)',
  V_pmax_opt: 'Vpmax_opt',
  V_pmax_beta: 'Vpmax_beta',
  J_max_25: 'Jmax(25度)',
  J_max_opt: 'Jmax_opt',
  J_max_beta: 'Jmax_beta',
  R_day_25: 'Rday(25度)',
  R_day_opt: 'Rday_opt',
  R_day_beta: 'Rday_beta',
}
const units = {
  DATE: '',
  LAI: 'm2 m-2',
  LightExtinctionCoefficient: '',
  AveAirTemperature: '℃',
  SunshineDuration: 'h',
  CO2_ParPressure_Mesophyll: 'μbar',
  V_cmax_25: 'μmol m-2 s-1',
  V_cmax_opt: 'μmol m-2 s-1',
  V_cmax_beta: '',
  V_pmax_25: 'μmol m-2 s-1',
  V_pmax_opt: 'μmol m-2 s-1',
  V_pmax_beta: '',
  J_max_25: 'μmol m-2 s-1',
  J_max_opt: 'μmol m-2 s-1',
  J_max_beta: '',
  R_day_25: 'μmol m-2 s-1',
  R_day_opt: 'μmol m-2 s-1',
  R_day_beta: '',
}
const rules = {
  DATE: [
    { required: true, message: '请选择日期', trigger: 'blur' },
    {
      type: 'date',
      message: '请输入正确的日期格式，例如：YYYY-MM-DD',
      trigger: 'blur',
    },
  ],
  // 为所有浮点型字段添加统一规则
  ...Object.fromEntries(
    Object.keys(formModel.value)
      .filter((key) => key !== 'DATE')
      .map((key) => [
        key,
        [
          {
            required: true,
            message: `请输入${formLabels[key]}`,
            trigger: 'blur',
          },
          {
            type: 'number',
            message: `${formLabels[key]}必须为数字`,
            trigger: 'blur',
          },
        ],
      ]),
  ),
}

const submitForm = (formRef) => {
  formRef.validate((valid) => {
    if (valid) {
      outputFormModel.value = {
        ouputDATE: '2024/6/18',
        DailyCapAssimilatedCO2PerUnitArea: 3.58,
        DailyCapDryMatterPerUnitArea: 4.8,
        DailyCapRUE: 66.8,
      }
      ElMessage.success('表单校验通过，可以提交！')
      console.log('表单数据:', formModel.value)
    } else {
      ElMessage.error('表单校验失败，请检查输入项！')
      return false
    }
  })
}
//输出表单
const outputFormModel = ref({
  ouputDATE: '', // 日期
  DailyCapAssimilatedCO2PerUnitArea: '', // 日吸收CO2
  DailyCapDryMatterPerUnitArea: '', // 日干物质积累
  DailyCapRUE: '', // 日光能利用率
})

const outputFormLabels = {
  ouputDATE: '日期',
  DailyCapAssimilatedCO2PerUnitArea: '日吸收CO2 (单位面积)',
  DailyCapDryMatterPerUnitArea: '日干物质积累 (单位面积)',
  DailyCapRUE: '日光能利用率',
}

const outputFormUnits = {
  ouputDATE: 'Year--Day',
  DailyCapAssimilatedCO2PerUnitArea: ' CO2 m-2 day-1',
  DailyCapDryMatterPerUnitArea: 'gm-2 day-1',
  DailyCapRUE: 'g MJ-1',
}
const goBack = () => {
  /* algorshow.value = true */
  router.push('/home/algor')
}
const drawer = ref(false)

const handleInputData = () => {
  drawer.value = true
}
//往inputdata传入一个数据，判断使用哪一个模型
const agolyTitle = ref({
  title: '冠状光合',
  model: 'plant_model',
})
</script>

<template>
  <div class="common-layout">
    <div class="inputData">
      <el-container>
        <el-header style="position: relative">
          {{ agolyTitle.title }}算法输入数据
          <el-button
            type="primary"
            style="position: absolute; right: 100px"
            @click="handleInputData"
            >导入数据</el-button
          >
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
            label-width="150px"
            :rules="rules"
          >
            <!-- 动态渲染表单 -->
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
              <!-- 其他输入框 -->
              <el-input
                v-else
                v-model.number="formModel[key]"
                placeholder="请输入数据"
              ></el-input>
              <span style="display: block">{{ units[key] }}</span>
            </el-form-item>
          </el-form>
        </el-main>
      </el-container>
    </div>
    <div class="outputData">
      <el-container>
        <el-header>输出数据</el-header>
        <el-main>
          <el-form :model="outputFormModel" label-width="150px">
            <el-form-item
              v-for="(value, key) in outputFormModel"
              :key="key"
              :label="outputFormLabels[key]"
              :prop="key"
            >
              <el-input v-model.number="outputFormModel[key]"></el-input>
              <span style="display: block">{{ outputFormUnits[key] }}</span>
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
  <inputData
    v-model:draw="drawer"
    v-model:formmodel="formModel"
    v-model:formLabel="formLabels"
    :agolyTitle="agolyTitle"
  ></inputData>
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
      width: 500px;
      box-sizing: border-box;
      align-items: center;
      gap: 10px;
      .el-form-item__content {
        width: 280px;
        .el-input {
          width: 220px;
          margin-right: 10px;
        }
      }
      .el-date-picker {
        width: 260px;
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
      width: 500px; /* 每个表单项固定宽度 */
      box-sizing: border-box; /* 确保 padding 不影响宽度 */
      display: flex; /* 使内部子元素在一行排列 */
      align-items: center; /* 垂直居中对齐 */
      gap: 10px; /* 设置子元素之间的间距 */
      .el-form-item__content {
        width: 280px;
        .el-input {
          width: 220px;
          margin-right: 10px;
        }
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
