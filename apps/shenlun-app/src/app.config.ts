export default defineAppConfig({
  pages: ['pages/today/index', 'pages/reading/index', 'pages/training/index', 'pages/profile/index'],
  window: {
    navigationBarBackgroundColor: '#D0021B',
    navigationBarTitleText: '知行申论',
    navigationBarTextStyle: 'white',
    backgroundColor: '#F4F5F7',
  },
  tabBar: {
    color: '#8A8F98',
    selectedColor: '#D0021B',
    backgroundColor: '#FFFFFF',
    list: [
      { pagePath: 'pages/today/index', text: '今日', iconPath: './assets/icons/today.png', selectedIconPath: './assets/icons/today-active.png' },
      { pagePath: 'pages/reading/index', text: '精读', iconPath: './assets/icons/study.png', selectedIconPath: './assets/icons/study-active.png' },
      { pagePath: 'pages/training/index', text: '训练', iconPath: './assets/icons/practice.png', selectedIconPath: './assets/icons/practice-active.png' },
      { pagePath: 'pages/profile/index', text: '我的', iconPath: './assets/icons/profile.png', selectedIconPath: './assets/icons/profile-active.png' },
    ],
  },
})
