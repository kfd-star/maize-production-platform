import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index.js'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './style.css'
import * as Icons from '@element-plus/icons-vue'
import commonJs from './assets/js/common'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import pinia from './store/index.js'
import horizontalScroll from 'el-table-horizontal-scroll'

// Vue3
const app = createApp(App)
for (let i in Icons) {
  app.component(i, Icons[i])
}
app.use(ElementPlus, {
  locale: zhCn,
})
/* app.config.devtools = true */

app.use(router)
app.use(pinia)
app.use(horizontalScroll)

app.mount('#app')
