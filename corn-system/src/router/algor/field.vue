<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useStore } from '../../store'
import inputData from '@/router/algor/inputData.vue'
const { tableShow, algorshow, mapShow } = useStore()
const router = useRouter()
const formModel = ref({
  parlat: '', // 纬度
  parlon: '', // 经度
  NORMYSOWDATE: '', // 常年播期
  NORMYHARDATE: '', // 常年收获期
  BEGINDATE: '', // 茬口安排起始日期
  ENDDATE: '', // 茬口安排终止日期
  SFL: '', // 品种丰产性能
  VSL: '', // 土壤肥力水平
  PLOP: '', // 整地质量
  WML: '', // 水分灌排水平
  FL: '', // 施肥水平
  PCL: '', // 病虫草害防治水平
  CML: '', // 栽培技术水平
})
const formLabels = {
  parlat: '纬度',
  parlon: '经度',
  NORMYSOWDATE: '常年播期',
  NORMYHARDATE: '常年收获期',
  BEGINDATE: '茬口安排起始日期',
  ENDDATE: '茬口安排终止日期',
  SFL: '品种丰产性能',
  VSL: '土壤肥力水平',
  PLOP: '整地质量',
  WML: '水分灌排水平',
  FL: '施肥水平',
  PCL: '病虫草害防治水平',
  CML: '栽培技术水平',
}
const rules = {
  parlon: [{ required: true, message: '请输入经度', trigger: 'blur' }],
  parlat: [{ required: true, message: '请输入纬度', trigger: 'blur' }],
  NORMYSOWDATE: [
    { required: true, message: '请选择常年播期', trigger: 'change' },
  ],
  NORMYHARDATE: [
    { required: true, message: '请选择常年收获期', trigger: 'change' },
  ],
  BEGINDATE: [
    { required: true, message: '请选择茬口安排起始日期', trigger: 'change' },
  ],
  ENDDATE: [
    { required: true, message: '请选择茬口安排终止日期', trigger: 'change' },
  ],

  // 最后七个输入框的校验规则：不能为空，类型为字符串
  SFL: [
    { required: true, message: '请输入品种丰产性能', trigger: 'blur' },
    { type: 'number', message: '品种丰产性能必须是字符串', trigger: 'blur' },
  ],
  VSL: [
    { required: true, message: '请输入土壤肥力水平', trigger: 'blur' },
    { type: 'number', message: '土壤肥力水平必须是字符串', trigger: 'blur' },
  ],
  PLOP: [
    { required: true, message: '请输入整地质量', trigger: 'blur' },
    { type: 'number', message: '整地质量必须是字符串', trigger: 'blur' },
  ],
  WML: [
    { required: true, message: '请输入水分灌排水平', trigger: 'blur' },
    { type: 'number', message: '水分灌排水平必须是字符串', trigger: 'blur' },
  ],
  FL: [
    { required: true, message: '请输入施肥水平', trigger: 'blur' },
    { type: 'number', message: '施肥水平必须是字符串', trigger: 'blur' },
  ],
  PCL: [
    { required: true, message: '请输入病虫草害防治水平', trigger: 'blur' },
    {
      type: 'number',
      message: '病虫草害防治水平必须是字符串',
      trigger: 'blur',
    },
  ],
  CML: [
    { required: true, message: '请输入栽培技术水平', trigger: 'blur' },
    { type: 'number', message: '栽培技术水平必须是字符串', trigger: 'blur' },
  ],
}
const outputFormModel = ref({
  outputYield: '', // 产量
})
const outputFormLabels = {
  outputYield: '产量',
}
const submitForm = (formRef) => {
  // 校验逻辑
  formRef.validate((valid) => {
    if (valid) {
      // 表单校验通过
      outputFormModel.value = {
        outputYield: 58,
      }
      ElMessage.success('输出成功！')
      // 在这里添加提交逻辑
      outputYield.value = 20
    } else {
      // 表单校验未通过
      ElMessage.error('表单校验失败，请检查输入项！')
      return false
    }
  })
}
const goBack = () => {
  router.push('/home/algor')
}
////显示展示导入数据页面
const drawer = ref(false)

const handleInputData = () => {
  drawer.value = true
}
const agolyTitle = ref({
  title: '生产力预测',
  model: 'productivity_model',
})
</script>

<template>
  <div class="common-layout">
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
          style="position: absolute; right: 30px"
          @click="goBack"
          >返回</el-button
        >
      </el-header>
      <el-main>
        <!-- 输入数据 -->
        <div class="inputData">
          <el-container>
            <el-header>输入数据</el-header>
            <el-main>
              <el-form
                :model="formModel"
                ref="formRef"
                label-width="160px"
                :rules="rules"
              >
                <!-- 经度 -->
                <el-form-item label="经度" prop="parlon">
                  <el-input
                    v-model="formModel.parlon"
                    placeholder="请输入经度（-180 ~ 180）"
                    :maxlength="9"
                    :minlength="1"
                  />
                </el-form-item>
                <!-- 纬度 -->
                <el-form-item label="纬度" prop="parlat">
                  <el-input
                    v-model="formModel.parlat"
                    placeholder="请输入纬度（-90 ~ 90）"
                    :maxlength="8"
                    :minlength="1"
                  />
                </el-form-item>

                <el-form-item label="常年播期" prop="NORMYSOWDATE">
                  <el-date-picker
                    v-model="formModel.NORMYSOWDATE"
                    type="date"
                    placeholder="常年播期"
                  />
                </el-form-item>

                <!-- 常年收获期 -->
                <el-form-item label="常年收获期" prop="NORMYHARDATE">
                  <el-date-picker
                    v-model="formModel.NORMYHARDATE"
                    type="date"
                    placeholder="常年收获期"
                  />
                </el-form-item>

                <!-- 创建日期 -->
                <el-form-item label="茬口安排起始日期" prop="BEGINDATE">
                  <el-date-picker
                    v-model="formModel.BEGINDATE"
                    type="date"
                    placeholder="茬口安排起始日期"
                  />
                </el-form-item>

                <!-- 更新时间 -->
                <el-form-item label="茬口安排终止日期" prop="ENDDATE">
                  <el-date-picker
                    v-model="formModel.ENDDATE"
                    type="date"
                    placeholder="茬口安排终止日期"
                  />
                </el-form-item>
                <!-- 品种丰产性能 -->
                <el-form-item label="品种丰产性能," prop="SFL">
                  <el-input
                    v-model="formModel.SFL"
                    placeholder="请输入输入品种丰产性能"
                  />
                  <el-tooltip
                    class="box-item"
                    effect="light"
                    content="优:1; 良: 0.8; 中等: 0.6;低: 0.4; 差: 0.2"
                    placement="top-start"
                  >
                    <el-icon :size="20">
                      <WarningFilled />
                    </el-icon>
                  </el-tooltip>
                </el-form-item>

                <!-- 土壤肥力水平 -->
                <el-form-item label="土壤肥力水平" prop="VSL">
                  <el-input
                    v-model="formModel.VSL"
                    placeholder="请输入土壤肥力水平"
                  />
                  <el-tooltip
                    class="box-item"
                    effect="light"
                    content="高肥力:1; 中上肥力:0.9; 中等肥力:0.8; 中下肥力:0.7; 低肥力:0.5"
                    placement="top-start"
                  >
                    <el-icon :size="20">
                      <WarningFilled />
                    </el-icon>
                  </el-tooltip>
                </el-form-item>

                <!-- 整地质量 -->
                <el-form-item label="整地质量" prop="PLOP">
                  <el-input
                    v-model="formModel.PLOP"
                    placeholder="请输入整地质量"
                  />
                  <el-tooltip
                    class="box-item"
                    effect="light"
                    content="优:1; 良: 0.8; 中等: 0.6;低: 0.4; 差: 0.2"
                    placement="top-start"
                  >
                    <el-icon :size="20">
                      <WarningFilled />
                    </el-icon>
                  </el-tooltip>
                </el-form-item>

                <!-- 水分灌排水平 -->
                <el-form-item label="水分灌排水平" prop="WML">
                  <el-input
                    v-model="formModel.WML"
                    placeholder="请输入水分灌排水平"
                  />
                  <el-tooltip
                    class="box-item"
                    effect="light"
                    content="按需供应:1; 基本满足:0.8; 一般:0.6; 低:0.4; 不灌溉:0"
                    placement="top-start"
                  >
                    <el-icon :size="20">
                      <WarningFilled />
                    </el-icon>
                  </el-tooltip>
                </el-form-item>

                <!-- 施肥水平 -->
                <el-form-item label="施肥水平" prop="FL">
                  <el-input
                    v-model="formModel.FL"
                    placeholder="请输入施肥水平"
                  />
                  <el-tooltip
                    class="box-item"
                    effect="light"
                    content="按需供应:1; 基本满足:0.8; 一般:0.6; 低:0.4; 不施肥:0"
                    placement="top-start"
                  >
                    <el-icon :size="20">
                      <WarningFilled />
                    </el-icon>
                  </el-tooltip>
                </el-form-item>

                <!-- 病虫草害防治水平 -->
                <el-form-item label="病虫草害防治水平" prop="PCL">
                  <el-input
                    v-model="formModel.PCL"
                    placeholder="请输入病虫草害防治水平"
                  />
                  <el-tooltip
                    class="box-item"
                    effect="light"
                    content="较高:1; 高:0.9; 一般:0.75; 低:0.6; 不防治:0.3"
                    placement="top-start"
                  >
                    <el-icon :size="20">
                      <WarningFilled />
                    </el-icon>
                  </el-tooltip>
                </el-form-item>
                <!-- 栽培技术水平 -->
                <el-form-item label="栽培技术水平" prop="CML">
                  <el-input
                    v-model="formModel.CML"
                    placeholder="请输入栽培技术水平"
                  />
                  <el-tooltip
                    class="box-item"
                    effect="light"
                    content="较高:1; 高:0.9; 一般:0.75; 低:0.6; 不管理:0.3"
                    placement="top-start"
                  >
                    <el-icon :size="20">
                      <WarningFilled />
                    </el-icon>
                  </el-tooltip>
                </el-form-item>
              </el-form>
            </el-main>
          </el-container>
        </div>
        <!-- 输出数据 -->
        <div class="outputData">
          <el-container>
            <el-header>输出数据</el-header>
            <el-main>
              <!-- <span>产量</span>
              <el-input
              v-model="outputYield"
              style="width: 300px;margin-left: 30px;"
              />
              <el-button type="primary" @click="submitForm($refs.formRef)">
                    输出
              </el-button> -->
              <el-form :model="outputFormModel" label-width="150px">
                <el-form-item
                  v-for="(value, key) in outputFormModel"
                  :key="key"
                  :label="outputFormLabels[key]"
                  :prop="key"
                >
                  <el-input v-model.number="outputFormModel[key]"></el-input>
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
      </el-main>
    </el-container>
  </div>
  <inputData
    v-model:draw="drawer"
    v-model:formmodel="formModel"
    v-model:formLabel="formLabels"
    :agolyTitle="agolyTitle"
  ></inputData>
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
        width: 220px; /* 输入框占据剩余宽度 */
      }
      .el-icon {
        cursor: pointer; /* 鼠标悬停时显示为手型指针 */
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
