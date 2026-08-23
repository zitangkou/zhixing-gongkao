export default defineAppConfig({
  pages: ['pages/today/index', 'pages/topics/index', 'pages/practice/index', 'pages/profile/index'],
  window: { navigationBarBackgroundColor: '#193451', navigationBarTitleText: '知行政治理论', navigationBarTextStyle: 'white', backgroundColor: '#F4F5F7' },
  tabBar: { color: '#8A8F98', selectedColor: '#193451', backgroundColor: '#FFFFFF', list: [
    { pagePath: 'pages/today/index', text: '今日' }, { pagePath: 'pages/topics/index', text: '专题' }, { pagePath: 'pages/practice/index', text: '刷题' }, { pagePath: 'pages/profile/index', text: '我的' },
  ] },
})
