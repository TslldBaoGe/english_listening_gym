<template>
  <div class="player">
    <div class="player-main">
      <el-button class="glow-btn play-btn" circle size="large" @click="play" :loading="loading">
        ▶
      </el-button>
      <el-button class="replay-btn" text @click="restart">重播</el-button>
    </div>
    <div class="player-extra">
      <el-radio-group v-model="localRate" size="small" @change="play">
        <el-radio-button v-for="r in [1.0, 0.85, 0.75, 0.5]" :key="r" :value="r"
                         class="mono">{{ r }}x</el-radio-button>
      </el-radio-group>
      <el-button size="small" text class="loop-btn" :class="{ on: loop }"
                 @click="$emit('update:loop', !loop)">
        {{ loop ? '🔁 循环中' : '🔁 循环' }}
      </el-button>
    </div>
    <span v-if="error" class="player-error">{{ error }}</span>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  sentenceId: Number,
  rate: { type: Number, default: 1.0 },
  loop: { type: Boolean, default: false },
})
defineEmits(['update:loop'])

const localRate = ref(props.rate)
const loading = ref(false)
const error = ref('')

// 模块级缓存：同一个音频只下载/缓冲一次。重复点播放 = 直接从头出声，不再转圈。
const CACHE_MAX = 40
const cache = new Map()      // url -> HTMLAudioElement
let current = null           // 当前在播的元素，切句时把它停掉

// 设置是异步加载的，外部 rate 到位后同步到本地
watch(() => props.rate, (r) => { localRate.value = Number(r) || 1.0 })

// 循环开关一变，立刻同步到已缓存/正在播的音频
watch(() => props.loop, (v) => {
  cache.forEach(el => { el.loop = v })
  if (current) current.loop = v
}, { immediate: true })

function src() {
  return `/api/audio/${props.sentenceId}?rate=${localRate.value}`
}

function element() {
  const u = src()
  let el = cache.get(u)
  if (!el) {
    el = new Audio(u)
    el.preload = 'auto'
    el.loop = props.loop
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
  const el = element()
  // 正在播同一句：再点就是暂停，不用重新走一遍加载
  if (current === el && !el.paused && !el.ended) { el.pause(); return }
  error.value = ''
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

/** 重播：无论当前是否在播，都从头开始 */
function restart() {
  error.value = ''
  const el = element()
  if (current && current !== el) current.pause()
  current = el
  if (el.readyState >= 3) loading.value = false
  start(el)
}
</script>

<style scoped>
/* 桌面：一行排开，和原来一致 */
.player {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.player-main,
.player-extra {
  display: flex;
  align-items: center;
  gap: 10px;
}

.replay-btn {
  color: var(--text-dim);
}

.player-error {
  color: #f56c6c;
  font-size: 13px;
}

.loop-btn {
  color: var(--text-dim);
  border: 1px solid transparent;
}
.loop-btn.on {
  color: var(--accent);
  border-color: var(--accent);
  background: rgba(56, 189, 248, .08);
}

/* 手机/窄屏：纵向居中成两行——大播放键一行，次要控件一行 */
@media (max-width: 720px) {
  .player {
    flex-direction: column;
    align-items: center;
    gap: 14px;
  }
  .player-main {
    gap: 16px;
  }
  .player-extra {
    gap: 8px;
    justify-content: center;
    flex-wrap: wrap;
    padding: 6px 10px;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: rgba(148, 163, 184, .04);
  }
  .play-btn {
    width: 58px !important;
    height: 58px !important;
    font-size: 22px !important;
    padding: 0 !important;
  }
  .player-error {
    text-align: center;
  }
}
</style>
