import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { FLAT_NAV_ITEMS, canAccess } from '@/config/nav'

const router = createRouter({
  history: createWebHistory('/manage/'),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/views/Layout.vue'),
      redirect: '/articles',
      children: [
        {
          path: 'articles',
          name: 'articles',
          component: () => import('@/views/articles/List.vue'),
          meta: { title: '文章管理', permissions: ['article:read'] },
        },
        {
          path: 'articles/new',
          name: 'article-new',
          component: () => import('@/views/articles/Edit.vue'),
          meta: { title: '新建文章', permissions: ['article:write'] },
        },
        {
          path: 'articles/:id',
          name: 'article-edit',
          component: () => import('@/views/articles/Edit.vue'),
          meta: { title: '编辑文章', permissions: ['article:read'] },
        },
        {
          path: 'categories',
          name: 'categories',
          component: () => import('@/views/categories/List.vue'),
          meta: { title: '分类管理', permissions: ['article:read', 'article:write'] },
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/users/List.vue'),
          meta: { title: '用户管理', permissions: ['user:read'] },
        },
        {
          path: 'knowledge',
          name: 'knowledge',
          component: () => import('@/views/knowledge/List.vue'),
          meta: { title: '知识框架', permissions: ['knowledge:read'] },
        },
        {
          path: 'plan',
          name: 'plan',
          component: () => import('@/views/plan/Templates.vue'),
          meta: { title: '学习计划', permissions: ['plan:read'] },
        },
        {
          path: 'exam',
          name: 'exam',
          component: () => import('@/views/exam/Papers.vue'),
          meta: { title: '试卷题库', permissions: ['exam:read'] },
        },
        {
          path: 'english',
          name: 'english',
          component: () => import('@/views/english/List.vue'),
          meta: { title: '英语学习', permissions: ['english:read'] },
        },
        {
          path: 'ziliao',
          name: 'ziliao',
          component: () => import('@/views/ziliao/List.vue'),
          meta: { title: '资料分析', permissions: ['ziliao:read'] },
        },
        {
          path: 'rmrb',
          name: 'rmrb',
          component: () => import('@/views/rmrb/List.vue'),
          meta: { title: '人民日报', permissions: ['rmrb:read'] },
        },
        {
          path: 'corpus',
          name: 'corpus',
          component: () => import('@/views/corpus/List.vue'),
          meta: { title: '语料本', permissions: ['corpus:read'] },
        },
        {
          path: 'events',
          name: 'events',
          component: () => import('@/views/events/List.vue'),
          meta: { title: '时事事件', permissions: ['events:read'] },
        },
        {
          path: 'health',
          name: 'health',
          component: () => import('@/views/health/Dashboard.vue'),
          meta: { title: '健康看板', permissions: ['health:read'] },
        },
        {
          path: 'dushu',
          name: 'dushu',
          component: () => import('@/views/dushu/List.vue'),
          meta: { title: '读书管理', permissions: ['dushu:read'] },
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/settings/Index.vue'),
          meta: { title: '系统设置', permissions: ['setting:read', 'admin:read'] },
        },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.token) {
    return { name: 'articles' }
  }
  if (!to.meta.public && auth.token && !auth.username) {
    try {
      await auth.loadMe()
    } catch {
      auth.logout()
      return { name: 'login', query: { redirect: to.fullPath } }
    }
  }
  const required = (to.meta.permissions as string[] | undefined) || []
  if (required.length && !auth.isSuperAdmin && !canAccess(auth.permissions, required)) {
    const fallback = FLAT_NAV_ITEMS.find((item) =>
      auth.isSuperAdmin || canAccess(auth.permissions, item.permissions),
    )
    return fallback ? fallback.path : { name: 'login' }
  }
})

export default router
