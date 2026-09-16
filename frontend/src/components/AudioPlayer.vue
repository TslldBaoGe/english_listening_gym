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
import { ref, watch } from 'vue'

const props = defineProps({ sentenceId: Number, rate: { type: Number, default: 1.0 } })
const localRate = ref(props.rate)
const loading = ref(false)
const error = ref('')
let audio = null

// 设置是异步加载的，外部 rate 到位后同步到本地
watch(() => props.rate, (r) => { localRate.value = Number(r) || 1.0 })

function play() {
  error.value = ''
  loading.value = true
  if (audio) { audio.pause() }
  const el = new Audio(`/api/audio/${props.sentenceId}?rate=${localRate.value}`)
  audio = el
  const done = () => { loading.value = false }
  el.oncanplay = done
  el.onplaying = done
  el.onerror = () => { done(); error.value = '音频加载失败' }
  // 关键：直接在用户手势里调用 play()，若放到 oncanplay 回调里会被 iOS Safari 拦截
  const p = el.play()
  if (p && typeof p.catch === 'function') {
    p.catch(() => { done(); error.value = '浏览器拦截了播放，请再点一次播放键' })
  }
}
</script>
