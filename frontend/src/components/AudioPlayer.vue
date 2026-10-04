<template>
  <div class="player" style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
    <el-button class="glow-btn" circle size="large" @click="play" :loading="loading">
      ▶
    </el-button>
    <el-button text style="color:var(--text-dim)" @click="play">重播</el-button>
    <el-radio-group v-model="localRate" size="small" @change="play">
      <el-radio-button v-for="r in [1.0, 0.85, 0.75, 0.5]" :key="r" :value="r"
                       class="mono">{{ r }}x</el-radio-button>
    </el-radio-group>
    <span v-if="error" style="color:#f56c6c;font-size:13px">{{ error }}</span>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({ sentenceId: Number, rate: { type: Number, default: 1.0 } })
const localRate = ref(props.rate)
const loading = ref(false)
const error = ref('')

// 模块级缓存：同一个音频只下载/缓冲一次。重复点播放 = 直接从头出声，不再转圈。
const CACHE_MAX = 40
const cache = new Map()      // url -> HTMLAudioElement
let current = null           // 当前在播的元素，切句时把它停掉

// 设置是异步加载的，外部 rate 到位后同步到本地
watch(() => props.rate, (r) => { localRate.value = Number(r) || 1.0 })

function src() {
  return `/api/audio/${props.sentenceId}?rate=${localRate.value}`
}

function element() {
  const u = src()
  let el = cache.get(u)
  if (!el) {
    el = new Audio(u)
    el.preload = 'auto'
    cache.set(u, el)
    if (cache.size > CACHE_MAX) {              // 超出上限就释放最旧的一个
      const [oldU, oldEl] = cache.entries().next().value
      if (oldEl !== current) { oldEl.src = ''; cache.delete(oldU) }
    }
  }
  return el
}

// 进页面就预取，连第一次点击也可以不出声等待
onMounted(() => {
  const el = element()
  try { el.load() } catch (e) { /* 浏览器不支持预取就算了 */ }
})

onBeforeUnmount(() => {
  const el = cache.get(src())
  if (el && el === current) el.pause()
})

function blocked() {
  loading.value = false
  error.value = '浏览器拦截了播放，请再点一次播放键'
}

function start(el) {
  el.currentTime = 0
  // 关键：仍在用户手势里直接调用 play()，放到回调里会被 iOS Safari 拦截
  const p = el.play()
  if (p && typeof p.catch === 'function') p.catch(blocked)
}

function play() {
  error.value = ''
  const el = element()
  if (current && current !== el) current.pause()
  current = el
  el.onerror = () => { loading.value = false; error.value = '音频加载失败' }

  // 已经缓冲好：立即出声，完全不显示转圈
  if (el.readyState >= 3) {
    loading.value = false
    start(el)
    return
  }
  loading.value = true
  el.oncanplay = () => { loading.value = false }
  el.onplaying = () => { loading.value = false }
  start(el)
}
</script>
