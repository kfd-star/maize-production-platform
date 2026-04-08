<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { CirclePlusFilled, RemoveFilled } from '@element-plus/icons-vue'
import { useStore } from '../../store/index.js'
import { storeToRefs } from 'pinia'
import bus from '../../utils/EventBus.js'

const { editDataDialog } = storeToRefs(useStore())

const fields = ref([])
// const
let table = null
const dataItem = ref([])
let currentDataItem = null

onMounted(() => {})

onUnmounted(() => {
  fields.value = []
})

// 移除未使用的 watch

function onConfirm() {
  const v = dataItem.value
  if (table) {
    //新增数据项
    const item = {}
    v.forEach((d) => {
      item[d.field] = d.value
    })
    table.value.dataItems.push(item)
  } else if (currentDataItem) {
    //编辑数据项
    v.forEach((d) => {
      currentDataItem[d.field] = d.value
    })
  }
  bus.emit('updateDataItem')
  onCancel()
}

function onCancel() {
  editDataDialog.value = false
  table = null
  currentDataItem = null
  dataItem.value = []
}

bus.on('addDataItem', (e) => {
  const tableData = e.tableData
  const fields = tableData.value.fields
  fields.forEach((f) => {
    dataItem.value.push({
      field: f,
      value: '',
    })
  })
  table = tableData
})

bus.on('editDataItem', (e) => {
  const item = e.dataItem
  currentDataItem = item
  for (const k in item) {
    dataItem.value.push({
      field: k,
      value: item[k],
    })
  }
})
</script>
<template>
  <el-dialog
    title="编辑数据"
    width="30%"
    v-model="editDataDialog"
    custom-class="prop-dialog"
  >
    <div>
      <el-form label-width="120px">
        <el-form-item
          v-for="(item, ind) in dataItem"
          :key="ind"
          class="prop-item"
          :label="item.field"
        >
          <el-input
            placeholder="输入值"
            class="value-input"
            v-model="item.value"
          ></el-input>
        </el-form-item>
      </el-form>
    </div>
    <span slot="footer" class="dialog-footer">
      <el-button @click="onCancel">取 消</el-button>
      <el-button type="primary" @click="onConfirm">确 定</el-button>
    </span>
  </el-dialog>
</template>
<style lang="less">
.prop-item {
  display: flex;
  align-items: center;
  margin: 4px 0;
  width: 90%;
}

.value-input {
  width: 90%;
}

.type-inp {
  margin-right: 10px;
  width: 90%;
}
</style>
