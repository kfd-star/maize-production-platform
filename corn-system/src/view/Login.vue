<script setup>
import { UserFilled, Lock, Right } from '@element-plus/icons-vue'
import { ref, onMounted, watch } from 'vue'
import tableApi from '../api/table'
import { ElMessage } from 'element-plus'
import { useRemmenber, useStore } from '@/store/index'

import router from '@/router/index'
const remmenberInfo = useRemmenber() //获取记住密码的仓库
const userInfoStore = useStore() //获取用户信息的仓库
//控制登录注册界面显隐
const isregister = ref(true)
onMounted(() => {
  // 将用户名密码赋值给form
  form.value.username = remmenberInfo.username
  form.value.password = remmenberInfo.password
})
//获取记住密码的用户名和密码
const form = ref({
  username: remmenberInfo.username,
  password: remmenberInfo.password,
  repassword: '',
})

//用于控制记住密码的按钮状态
const remenber = ref(true)
//获取form表单的引用 用于登录逻辑validate函数的验证
const formref = ref()
const formrules = {
  username: [
    {
      required: true,
      message: '请输入用户名',
      trigger: 'blur',
    },
    {
      min: 3,
      max: 10,
      message: '长度在 3 到 10 个字符',
      trigger: 'blur',
    },
  ],
  password: [
    {
      required: true,
      message: '请输入密码',
      trigger: 'blur',
    },
    {
      min: 6,
      max: 20,
      message: '长度在 6 到 20 个字符',
      trigger: 'blur',
    },
  ],
  repassword: [
    {
      required: true,
      message: '请输入密码',
      trigger: 'blur',
    },
    {
      min: 6,
      max: 20,
      message: '长度在 6 到 20 个字符',
      trigger: 'blur',
    },
    {
      validator: (rule, value, callback) => {
        if (value !== form.value.password) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

//登录逻辑
const login = async () => {
  //选择记住密码时将密码存入pinia仓库
  if (remenber.value) {
    remmenberInfo.remmenber_userinfo(form.value)
  }
  await formref.value.validate()
  const res = await tableApi.login(form.value)

  if (res.data.status === 200) {
    //调用这个函数存入用户名
    remmenberInfo.setUsername_home(res.data.user.username)
    userInfoStore.setToken(res.data.token)
    router.push('/home')
  } else {
    ElMessage.error(res.data.message)
  }
}

//注册逻辑
const register = async () => {
  await formref.value.validate()
  const res = await tableApi.register(form.value)
  if (res.data.status === 200) {
    isregister.value = true
  } else {
    ElMessage.error(res.data.message)
  }
}

//切换登录 注册  切换之后账号密码存在可以将其拆分为两个路由解决 也可以使用watch函数来解决
watch(isregister, () => {
  form.value = {
    username: '',
    password: '',
    repassword: '',
  }
})
</script>

<template>
  <el-container class="login-container">
    <el-header class="login-header">
      <div style="width: 400px">
        <p style="float: left">
          <el-icon color="#409EFF" :size="52" class="el-sys-logo">
            <!-- <ElementPlus /> -->
          </el-icon>
        </p>
        <p
          style="
            font-size: 25px;
            font-weight: bold;
            position: absolute;
            color: white;
            font-family: cursive;
            top: -8px;
          "
        >
          玉米生产力预测平台
        </p>
        <p
          style="
            font-size: 16px;
            font-weight: bold;
            position: absolute;
            color: white;
            font-family: cursive;
            top: 32px;
          "
        >
          Corn Productivity Forecast System
        </p>
      </div>
    </el-header>
    <el-main class="login-main">
      <el-row class="login-manager" v-if="isregister">
        <el-col :span="12" class="bg"> </el-col>
        <el-col :span="6" :offset="3" class="form">
          <!-- 登录 -->
          <el-form
            label-position="top"
            label-width="auto"
            style="
              max-width: 600px;
              margin-top: -200px;
              margin-right: -580px;
              border: #77bc50 1px solid;
              background-color: rgba(25, 69, 14, 0.5);
              color: white;
            "
            :model="form"
            :rules="formrules"
            ref="formref"
          >
            <el-form-item>
              <h1 style="color: white">登录</h1>
            </el-form-item>
            <el-form-item label="用户名:" prop="username">
              <template #label>
                <span style="color: white">用户名:</span>
              </template>
              <el-input
                v-model="form.username"
                :prefix-icon="UserFilled"
                placeholder="请输入用户名"
              />
            </el-form-item>
            <el-form-item label="密码:" prop="password" class="label-item">
              <template #label>
                <span style="color: white">密码:</span>
              </template>
              <el-input
                v-model="form.password"
                :prefix-icon="Lock"
                type="password"
                placeholder="请输入密码"
              />
            </el-form-item>
            <el-form-item>
              <el-checkbox v-model="remenber" style="color: aliceblue">
                记住密码
              </el-checkbox>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="login" auto-insert-space
                >登录</el-button
              >
            </el-form-item>
            <el-form-item>
              <el-link
                :icon="Right"
                @click="isregister = false"
                style="color: white"
              >
                去注册
              </el-link>
            </el-form-item>
          </el-form>
        </el-col>
      </el-row>
      <!-- 注册 -->
      <el-row class="login-manager" v-else>
        <el-col :span="12" class="bg"> </el-col>
        <el-col :span="6" :offset="3" class="form">
          <el-form
            label-position="top"
            label-width="auto"
            style="
              max-width: 600px;
              margin-top: -200px;
              margin-right: -580px;
              border: #77bc50 1px solid;
              background-color: rgba(25, 69, 14, 0.5);
              color: white;
            "
            :model="form"
            :rules="formrules"
            ref="formref"
          >
            <el-form-item>
              <h1>注册</h1>
            </el-form-item>
            <el-form-item prop="username">
              <el-input
                v-model="form.username"
                :prefix-icon="UserFilled"
                placeholder="请输入用户名"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                :prefix-icon="Lock"
                type="password"
                show-password
                placeholder="请输入密码"
              />
            </el-form-item>
            <el-form-item prop="repassword">
              <el-input
                v-model="form.repassword"
                type="password"
                placeholder="请确认密码"
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="register" auto-insert-space
                >注册</el-button
              >
            </el-form-item>
            <el-form-item>
              <el-link
                :icon="Right"
                @click="isregister = true"
                style="color: white"
              >
                去登录
              </el-link>
            </el-form-item>
          </el-form>
        </el-col>
      </el-row>
    </el-main>
    <el-footer></el-footer>
  </el-container>
</template>

<style lang="scss" scoped>
.el-footer {
  height: 5%;
}
.login-container {
  height: 100vh;
  .login-header {
    height: 10vh;
  }
  .login-main {
    overflow: hidden;
    height: 85vh;
    background-image: url('../assets/img/2-m.jpg');
    background-repeat: no-repeat;
    background-size: 100% 100%;

    .login-manager {
      height: 100vh;

      .form {
        height: 100%;
        display: flex;
        justify-content: center; /* 水平居中 */
        align-items: center;
        .el-form {
          padding: 15px;

          width: 70%;
          border-radius: 10px;
          .el-button {
            width: 100%;
          }
        }
      }
    }
  }
}
</style>
