import { ref } from 'vue'
import { defineStore } from 'pinia'
export const useRemmenber = defineStore(
  'remmenber',
  () => {
    //home界面的用户名名
    const username_home = ref('')
    const setUsername_home = (name) => {
      username_home.value = name
    }
    //登陆界面
    const username = ref('')
    const password = ref('')
    const remmenber_userinfo = (form) => {
      username.value = form.username
      password.value = form.password
    }

    return {
      username_home,
      username,
      password,
      remmenber_userinfo,
      setUsername_home,
    }
  },
  {
    persist: true,
  },
)
