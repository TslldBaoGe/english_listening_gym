<template>
  <div class="player">
    <button class="ctl play-btn" :class="{ playing }" @click="play"
            :aria-label="playing ? '暂停' : '播放'">
      <SkyBackdrop :delay="0" />
      <span class="ctl-inner">
        <svg v-if="loading" class="icon spin" viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2.4"
                  stroke-linecap="round" stroke-dasharray="42 14" />
        </svg>
        <svg v-else-if="playing" class="icon" viewBox="0 0 24 24" aria-hidden="true">
          <rect x="7" y="5" width="3.6" height="14" rx="1.2" fill="currentColor" />
          <rect x="13.4" y="5" width="3.6" height="14" rx="1.2" fill="currentColor" />
        </svg>
        <svg v-else class="icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M8.5 5.6v12.8c0 .9 1 1.4 1.7.9l9-6.4c.6-.4.6-1.4 0-1.8l-9-6.4c-.7-.5-1.7 0-1.7.9z"
                fill="currentColor" />
        </svg>
      </span>
    </button>

    <div class="player-extra">
      <div class="rate-group">
        <button v-for="(r, i) in rates" :key="r" class="ctl rate-btn"
                :class="{ active: localRate === r, first: i === 0, last: i === rates.length - 1 }"
                @click="setRate(r)">
          <SkyBackdrop :delay="i * 1.3" />
          <span class="ctl-inner mono">{{ r }}x</span>
        </button>
      </div>
      <LoopPill :model-value="loop" @update:model-value="$emit('update:loop', $event)" />
    </div>
    <span v-if="error" class="player-error">{{ error }}</span>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import LoopPill from './LoopPill.vue'
import SkyBackdrop from './SkyBackdrop.vue'

const props = defineProps({
  sentenceId: Number,
  rate: { type: Number, default: 1.0 },
  loop: { type: Boolean, default: false },
})
defineEmits(['update:loop'])

const rates = [1.0, 0.85, 0.75, 0.5]
const localRate = ref(props.rate)
const loading = ref(false)
const playing = ref(false)
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
    el.onplaying = () => { loading.value = false; playing.value = true }
    el.onpause = () => { playing.value = false }
    el.onended = () => { playing.value = false }   // 循环时不会触发
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

function play() {  const el = element()
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

/** 切倍速：换 URL 重新加载，保持播放位置与播放状态 */
function setRate(r) {
  const wasPlaying = playing.value || loading.value
  const at = current ? current.currentTime : 0
  localRate.value = r
  const el = element()
  if (current && current !== el) current.pause()
  current = el
  el.currentTime = at
  if (wasPlaying) {
    loading.value = true
    const p = el.play()
    if (p && typeof p.catch === 'function') p.catch(blocked)
  } else {
    loading.value = false
  }
}
</script>


<style scoped>
/* ── 统一控制条：电脑/平板/手机同一套外观，只有排布不同 ── */
.player {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  --ctl-h: 44px;
}

.player-extra {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(148, 163, 184, .06), rgba(148, 163, 184, .02));
  backdrop-filter: blur(6px);
}

/* 所有控制键共用同一套「夜空玻璃」外观：深底 + 星点 + 霓虹描边 */
.ctl {
  position: relative;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(16, 22, 36, .92), rgba(9, 13, 22, .96));
  color: var(--text-dim);
  cursor: pointer;
  transition: color .18s, border-color .18s, box-shadow .2s, transform .16s;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
}

.ctl:hover {
  color: var(--accent);
  border-color: rgba(56, 189, 248, .5);
}

.ctl:active {
  transform: scale(.96);
}

.ctl-inner {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.icon {
  width: 20px;
  height: 20px;
  display: block;
}

/* 播放键：圆形 */
.play-btn {
  width: var(--ctl-h);
  height: var(--ctl-h);
  flex: 0 0 auto;
  border-radius: 50%;
  color: var(--accent);
  border-color: rgba(56, 189, 248, .35);
  box-shadow: 0 2px 10px rgba(0, 0, 0, .35);
}

.play-btn:hover {
  border-color: rgba(56, 189, 248, .6);
  box-shadow: 0 2px 14px rgba(56, 189, 248, .16);
}

.play-btn.playing {
  border-color: rgba(56, 189, 248, .6);
}

/* 播放中只有很淡的呼吸，不要闪 */
.play-btn.playing .icon {
  animation: playBreathe 2.6s ease-in-out infinite;
}

@keyframes playBreathe {
  0%, 100% { opacity: .82; }
  50%      { opacity: 1; }
}

.play-btn .spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 倍速键：连体分段控件——中间无缝相接，只保留一圈外轮廓 */
.rate-group {
  display: inline-flex;
  align-items: stretch;
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(16, 22, 36, .92), rgba(9, 13, 22, .96));
}

.rate-group .rate-btn {
  border: none;
  border-radius: 0;
  height: 28px;
  min-width: 48px;
  padding: 0 10px;
  font-size: 12px;
  letter-spacing: .5px;
  background: transparent;
}

.rate-group .rate-btn + .rate-btn {
  border-left: 1px solid var(--border);
}

.rate-group .rate-btn.active {
  color: var(--accent);
  background: rgba(56, 189, 248, .12);
  box-shadow: inset 0 0 12px rgba(56, 189, 248, .14);
}

.rate-group .rate-btn:hover {
  color: var(--accent);
  background: rgba(56, 189, 248, .07);
}

.player-error {
  color: #f56c6c;
  font-size: 13px;
}

@media (prefers-reduced-motion: reduce) {
  .play-btn.playing .icon, .play-btn .spin { animation: none; }
}

/* 手机/窄屏：竖排两行，控件本身外观不变，只放大主播放键和点按区域 */
@media (max-width: 720px) {
  .player {
    flex-direction: column;
    align-items: center;
    gap: 14px;
    --ctl-h: 62px;
  }
  .player-extra {
    padding: 6px;
    gap: 6px;
    max-width: 100%;
    flex-wrap: wrap;
    justify-content: center;
    border-radius: 22px;
  }
  .icon {
    width: 22px;
    height: 22px;
  }
  .play-btn .icon {
    width: 26px;
    height: 26px;
  }
  .rate-group .rate-btn {
    height: 38px;
    min-width: 58px;
    font-size: 13px;
  }
  .player-error {
    text-align: center;
  }
}
</style>
