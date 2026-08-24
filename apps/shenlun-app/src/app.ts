import { createApp } from 'vue'
import { createPinia } from 'pinia'
import '@nutui/nutui-taro/dist/style.css'
import './app.scss'

const app = createApp({})
app.use(createPinia())

export default app
