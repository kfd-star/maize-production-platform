<!-- 遮罩组件 -->
<script setup>
import { ref } from 'vue'
import { defineModel, defineEmits } from 'vue'
const loading = defineModel('loading', {
  type: Boolean,
  required: true,
})
const emit = defineEmits(['cancelReq'])
const handCancel = () => {
  // 发出 cancel 事件，通知父组件
  emit('cancelReq')
}
</script>
<template>
  <div v-if="loading" class="fullscreen-mask">
    <div class="mask-content">
      <p>计算中,请稍等1-2分钟...</p>
      <el-button type="danger" @click="handCancel">取消</el-button>
    </div>
  </div>
</template>

<style scoped>
.fullscreen-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}
.mask-content {
  text-align: center;
  color: #fff;
}
</style>
