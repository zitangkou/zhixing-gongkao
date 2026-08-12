import Taro from '@tarojs/taro'
import { api, isMock } from '@/api'
import { useArticleStore } from '@/store/article'
import { useQuestionStore } from '@/store/question'
import { useUserStore } from '@/store/user'
import { getToken, isAuthPageRoute } from '@/utils/auth'

let bootstrapped = false

function redirectToLogin() {
  const pages = Taro.getCurrentPages()
  const route = pages[pages.length - 1]?.route
  if (isAuthPageRoute(route)) return
  Taro.reLaunch({ url: '/pages/auth/login' })
}

/** 应用启动时校验登录并同步数据 */
export async function bootstrapApp(force = false) {
  if (isMock) return
  if (!getToken()) {
    bootstrapped = false
    redirectToLogin()
    return
  }
  if (bootstrapped && !force) return

  const userStore = useUserStore()
  const articleStore = useArticleStore()
  const questionStore = useQuestionStore()

  const ok = await userStore.bootstrap()
  if (!ok) {
    userStore.logout()
    return
  }

  bootstrapped = true
  await Promise.all([
    articleStore.syncStudyData(),
    questionStore.loadWrongQuestions(),
  ])
}

export function resetBootstrap() {
  bootstrapped = false
}
