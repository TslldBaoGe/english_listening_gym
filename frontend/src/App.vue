<template>
  <AnimatedBackground />
  <el-container style="min-height:100vh;position:relative;z-index:1">
    <el-header style="padding:0;height:auto">
      <nav class="navbar">
        <div class="nav-inner">
          <router-link to="/practice" class="nav-logo mono">
            &lt;EL&gt;<span class="nav-logo-sub">ENGLISH·LISTENING</span>
          </router-link>
          <div class="nav-links">
            <router-link v-for="item in navItems" :key="item.to" :to="item.to"
                         class="nav-link mono" :class="{ active: $route.path === item.to }">
              <span class="nav-idx">{{ item.idx }}</span>{{ item.label }}
            </router-link>
          </div>
          <el-select v-touch-open v-model="theme" class="theme-select" size="small"
                     @change="setTheme">
            <el-option v-for="t in themes" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </div>
      </nav>
    </el-header>
    <el-main style="padding:0">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import AnimatedBackground from './components/AnimatedBackground.vue'

const navItems = [
  { to: '/practice', idx: '01', label: '练习' },
  { to: '/quiz', idx: '02', label: '测验' },
  { to: '/stats', idx: '03', label: '统计' },
  { to: '/library', idx: '04', label: '知识库' },
  { to: '/settings', idx: '05', label: '设置' },
]

const themes = [
  { value: 'dark', label: '深空星夜' },
  { value: 'light', label: '白天' },
]
const theme = ref(document.documentElement.dataset.theme === 'light' ? 'light' : 'dark')

function setTheme(v) {
  document.documentElement.dataset.theme = v === 'light' ? 'light' : 'dark'
  try { localStorage.setItem('el-theme', v) } catch (e) { /* 忽略 */ }
}
</script>
