import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import './style.css'
import './theme-light.css'   // 白天主题的覆盖规则，必须在主样式之后
import App from './App.vue'
import router from './router'

// 主题：在首次渲染前同步应用，避免开页闪一下另一种主题
try {
  const saved = localStorage.getItem('el-theme')
  document.documentElement.dataset.theme = saved === 'light' ? 'light' : 'dark'
} catch (e) {
  document.documentElement.dataset.theme = 'dark'
}

const app = createApp(App)

/**
 * 触屏上的 el-select 要第二次点才展开（第一次只触发聚焦/hover，还会露出清空 ×）。
 * 这个指令在 touchstart 时直接补一次鼠标事件把下拉打开，并拦掉浏览器随后合成的 click，
 * 保证一次触摸 = 一次开关。
 */
app.directive('touch-open', {
  mounted(el) {
    el.__touchOpen = (e) => {
      if (e.target.closest('.el-select__clear')) return   // 点清空按钮时不动
      e.preventDefault()
      const box = el.querySelector('.el-select__wrapper') || el
      box.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }))
      box.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }))
      box.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    }
    el.addEventListener('touchstart', el.__touchOpen, { passive: false })
  },
  unmounted(el) {
    el.removeEventListener('touchstart', el.__touchOpen)
  },
})

app.use(createPinia()).use(router).use(ElementPlus).mount('#app')
