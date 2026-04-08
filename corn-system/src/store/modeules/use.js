import { ref } from 'vue'
import { defineStore } from 'pinia'
export const useStore = defineStore(
  'toolTtore',
  () => {
    const fieldDialogShow = ref(false)
    const tableShow = ref(false)
    const editDataDialog = ref(false)
    const dataStructure = ref([])
    const needPublish = ref(false)
    const showView = ref(false)
    const mapShow = ref(true)
    const algorshow = ref(false) //控制算法组件
    const token = ref('')
    const setToken = (value) => {
      token.value = value
    }
    const removeToken = () => {
      token.value = ''
    }
    return {
      dataStructure,
      fieldDialogShow,
      tableShow,
      editDataDialog,
      needPublish,
      showView,
      mapShow,
      algorshow,
      token,
      setToken,
      removeToken,
    }
  },
  {
    persist: true,
  },
)
