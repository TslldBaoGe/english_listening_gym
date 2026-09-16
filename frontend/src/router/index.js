import { createRouter, createWebHistory } from 'vue-router'

// 静态导入：避免路由懒加载的动态 import —— 手机端在网络不佳时容易卡在加载组件这一步
import PracticeView from '../views/PracticeView.vue'
import QuizView from '../views/QuizView.vue'
import StatsView from '../views/StatsView.vue'
import LibraryView from '../views/LibraryView.vue'
import SettingsView from '../views/SettingsView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/practice' },
    { path: '/practice', component: PracticeView },
    { path: '/quiz', component: QuizView },
    { path: '/stats', component: StatsView },
    { path: '/library', component: LibraryView },
    { path: '/settings', component: SettingsView },
  ]
})
