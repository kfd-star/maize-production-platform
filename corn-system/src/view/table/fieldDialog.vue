<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { CirclePlusFilled, RemoveFilled } from '@element-plus/icons-vue'
import { useStore } from '../../store/index.js'
import { storeToRefs } from 'pinia'
import bus from '../../utils/EventBus'
import { ElMessage, ElMessageBox } from 'element-plus'

const { fieldDialogShow } = storeToRefs(useStore())

const fields = ref(['ID'])
const tableName = ref('')
onMounted(() => {})

onUnmounted(() => {
  fields.value = ['ID']
  tableName.value = ''
})

watch(fieldDialogShow, async (newVal) => {
  if (newVal) {
  }
})

function onDel(ind) {
  fields.value.splice(ind, 1)
}

function onAddProp() {
  fields.value.push('')
}

function onConfirm() {
  if (!tableName.value || invalidFields()) {
    ElMessage({
      type: 'error',
      message: '表名或字段名不合法，请检查后确认',
    })
    return
  }
  bus.emit('createdfield', { fields: fields.value, name: tableName.value })
  fieldDialogShow.value = false
  fields.value = ['ID']
  tableName.value = ''
}

function onCancel() {
  fieldDialogShow.value = false
}

function updateInput(e) {
  tableName.value = e
}

function invalidFields() {
  return fields.value.find((f) => {
    return f === ''
  })
}
</script>
<template>
  <el-dialog
    title="创建表结构"
    width="30%"
    v-model="fieldDialogShow"
    custom-class="prop-dialog"
  >
    <div>
      <el-form label-width="80px">
        <el-form-item label="表  名">
          <el-input
            placeholder="输入表名称"
            class="field-input"
            v-model="tableName"
            @input="updateInput"
          ></el-input>
        </el-form-item>
        <el-form-item label="字段列表">
          <div v-for="(item, ind) in fields" :key="ind" class="prop-item">
            <el-input
              placeholder="输入字段名称"
              class="type-inp"
              v-model="fields[ind]"
            ></el-input>
            <el-icon
              size="25"
              style="cursor: pointer"
              v-show="ind !== 0"
              @click="onDel(ind)"
              ><RemoveFilled
            /></el-icon>
          </div>
          <el-icon size="25" style="cursor: pointer" @click="onAddProp"
            ><CirclePlusFilled
          /></el-icon>
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
//   .prop-dialog {
//     .prop-item {
//       display: flex;
//       align-items: center;
//       margin: 4px 0;
//       .type-sel {
//         width: 80px;
//         flex-shrink: 0;
//       }

//       .el-icon-delete {
//         margin-left: 8px;
//         cursor: pointer;
//       }
//     }
//   }
.prop-item {
  display: flex;
  align-items: center;
  margin: 4px 0;
  width: 90%;
}

.field-input {
  width: 90%;
}

.type-inp {
  margin-right: 10px;
  width: 90%;
}
</style>
