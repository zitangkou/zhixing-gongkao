export default defineAppConfig({
  pages: ['pages/today/index', 'pages/reading/index', 'pages/training/index', 'pages/profile/index'],
  window: {
    navigationBarBackgroundColor: '#A80116',
    navigationBarTitleText: '知行申论',
    navigationBarTextStyle: 'white',
    backgroundColor: '#F4F5F7',
  },
  tabBar: {
    color: '#8A8F98',
    selectedColor: '#A80116',
    backgroundColor: '#FFFFFF',
    list: [
      { pagePath: 'pages/today/index', text: '今日' },
      { pagePath: 'pages/reading/index', text: '精读' },
      { pagePath: 'pages/training/index', text: '训练' },
      { pagePath: 'pages/profile/index', text: '我的' },
    ],
  },
})
