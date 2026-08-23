import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './app.scss'

const app = createApp({})
app.use(createPinia())

export default app
