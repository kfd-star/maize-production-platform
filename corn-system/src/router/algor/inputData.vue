<script setup>
import { onMounted, ref } from 'vue'
import { getAllExcel, getInputData } from '@/api/alogrPy'
import { ElMessage } from 'element-plus'
const props = defineProps({
  agolyTitle: {
    type: Object,
    required: true,
  },
})
onMounted(async () => {
  const res = await getAllExcel()

  res.data.forEach((item) => {
    const option = {
      value: item,
      label: item,
    }
    options.push(option)
  })
})
//获取选择器的值
const selectValue = ref(null)
const options = []
//更换select的值触发的事件
const handlechange = async () => {
  const params = {
    fileName: selectValue.value,
    algorithm: props.agolyTitle.model,
  }
  console.log('params', params)

  const res = await getInputData(params)

  console.log(res)
  console.log(res.data.valid)
  // 判断数据是否合法
  if (!res.data.valid) {
    Object.keys(formmodel.value).forEach((key) => {
      formmodel.value[key] = ''
    })
    ElMessage.error('该文件数据字段不正确')
    return
  } else {
    const row = res.data.data[0]
    const englishKeys = Object.keys(formmodel.value) // 英文字段
    const chineseKeys = Object.keys(row) // 中文字段
    // 判断是否是数字字符串且不为空 是string 数字，转换为num
    for (const key in row) {
      const val = row[key]
      const num = Number(val)

      if (!isNaN(num) && val.trim() !== '') {
        // 是数字字符串，转成数字类型
        row[key] = num
      } else {
        // 保持原值
        row[key] = val
      }
    }
    //为formmodel赋值
    for (let i = 0; i < englishKeys.length; i++) {
      const enKey = englishKeys[i]
      const cnKey = chineseKeys[i]

      if (cnKey !== undefined) {
        formmodel.value[enKey] = row[cnKey]
      }
    }
  }
}
//是否显示draw组件
const drawer = defineModel('draw')
// 表单数据
const formmodel = defineModel('formmodel')
// 表单数据的表头
const formLabel = defineModel('formLabel')
//点击取消情况formmel的数值
const cancel = () => {
  Object.keys(formmodel.value).forEach((key) => {
    formmodel.value[key] = ''
  })
  drawer.value = false
}
//点击确定
const submit = () => {
  drawer.value = false
}
</script>
<template>
  <el-drawer
    v-model="drawer"
    :title="`导入${props.agolyTitle.title}数据`"
    :with-header="true"
    :show-close="false"
  >
    <div class="seleExcel">
      <span>选择导入的excel文件</span>
      <el-select
        v-model="selectValue"
        placeholder="Select"
        style="width: 240px"
        @change="handlechange"
      >
        <el-option
          v-for="item in options"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
    </div>

    <div class="body">
      <el-form :model="formmodel" label-width="auto" style="max-width: 600px">
        <el-form-item
          v-for="(value, key) in formmodel"
          :key="key"
          :label="formLabel[key]"
          :prop="key"
        >
          <el-input
            v-model.number="formmodel[key]"
            placeholder="请输入数据"
          ></el-input>
        </el-form-item>
      </el-form>
    </div>
    <template #footer>
      <el-button @click="cancel">取消</el-button>
      <el-button type="primary" @click="submit">确定</el-button>
    </template>
  </el-drawer>
</template>
<style scoped></style>
