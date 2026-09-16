<template>
  <div class="bg-layer" aria-hidden="true">
    <div class="bg-glow bg-glow-1"></div>
    <div class="bg-glow bg-glow-2"></div>
    <div class="bg-glow bg-glow-3"></div>
    <canvas ref="canvasRef" class="bg-canvas"></canvas>
    <div class="bg-grid"></div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'

const canvasRef = ref(null)
let raf = 0
let stars = []
let meteors = []
let nextMeteorAt = 0
let ctx = null
let dpr = 1

function spawnMeteor(now) {
  const w = canvasRef.value.width
  const speed = (6 + Math.random() * 5) * dpr
  meteors.push({
    x: w * (0.35 + Math.random() * 0.75),
    y: -30 * dpr,
    vx: -speed * (0.55 + Math.random() * 0.35),
    vy: speed * (0.65 + Math.random() * 0.35),
    life: 0,
    maxLife: 60 + Math.random() * 40,
    len: (90 + Math.random() * 90) * dpr,
    green: Math.random() < 0.35,
  })
  nextMeteorAt = now + 1800 + Math.random() * 4200
}

function resize() {
  const canvas = canvasRef.value
  if (!canvas) return
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  canvas.width = window.innerWidth * dpr
  canvas.height = window.innerHeight * dpr
  canvas.style.width = window.innerWidth + 'px'
  canvas.style.height = window.innerHeight + 'px'
  initStars()
}

function initStars() {
  const count = Math.min(160, Math.floor(window.innerWidth / 9))
  stars = Array.from({ length: count }, () => ({
    x: Math.random() * canvasRef.value.width,
    y: Math.random() * canvasRef.value.height,
    r: (Math.random() * 1.4 + 0.4) * dpr,
    speed: (Math.random() * 0.25 + 0.06) * dpr,
    alpha: Math.random() * 0.6 + 0.2,
    twinkle: Math.random() * Math.PI * 2,
    twinkleSpeed: Math.random() * 0.02 + 0.006,
    green: Math.random() < 0.18,
  }))
}

function tick() {
  const canvas = canvasRef.value
  if (!ctx || !canvas) return
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  for (const s of stars) {
    s.y += s.speed
    s.twinkle += s.twinkleSpeed
    if (s.y - s.r > canvas.height) {
      s.y = -s.r
      s.x = Math.random() * canvas.width
    }
    const a = s.alpha * (0.65 + 0.35 * Math.sin(s.twinkle))
    ctx.beginPath()
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
    ctx.fillStyle = s.green
      ? `rgba(56, 189, 248, ${a})`
      : `rgba(200, 225, 255, ${a * 0.8})`
    ctx.fill()
    // 拖尾：亮星带一条细尾迹
    if (s.r > 1.3 * dpr) {
      ctx.strokeStyle = s.green
        ? `rgba(56, 189, 248, ${a * 0.25})`
        : `rgba(200, 225, 255, ${a * 0.15})`
      ctx.lineWidth = s.r * 0.6
      ctx.beginPath()
      ctx.moveTo(s.x, s.y)
      ctx.lineTo(s.x, s.y - s.speed * 14)
      ctx.stroke()
    }
  }

  // 流星
  const now = performance.now()
  if (now >= nextMeteorAt && meteors.length < 3) spawnMeteor(now)
  meteors = meteors.filter((m) => m.life < m.maxLife)
  for (const m of meteors) {
    m.life++
    m.x += m.vx
    m.y += m.vy
    const t = m.life / m.maxLife
    // 渐入渐出
    const fade = Math.sin(Math.min(1, t) * Math.PI)
    const nx = m.x - m.vx * (m.len / Math.hypot(m.vx, m.vy))
    const ny = m.y - m.vy * (m.len / Math.hypot(m.vx, m.vy))
    const grad = ctx.createLinearGradient(m.x, m.y, nx, ny)
    const head = m.green ? '56, 189, 248' : '190, 220, 255'
    grad.addColorStop(0, `rgba(255, 255, 255, ${0.9 * fade})`)
    grad.addColorStop(0.15, `rgba(${head}, ${0.7 * fade})`)
    grad.addColorStop(1, `rgba(${head}, 0)`)
    ctx.strokeStyle = grad
    ctx.lineWidth = 1.6 * dpr
    ctx.lineCap = 'round'
    ctx.beginPath()
    ctx.moveTo(m.x, m.y)
    ctx.lineTo(nx, ny)
    ctx.stroke()
    // 亮头部
    ctx.beginPath()
    ctx.arc(m.x, m.y, 1.6 * dpr, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(255, 255, 255, ${0.85 * fade})`
    ctx.fill()
  }
  raf = requestAnimationFrame(tick)
}

onMounted(() => {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const canvas = canvasRef.value
  ctx = canvas.getContext('2d')
  resize()
  nextMeteorAt = performance.now() + 1200
  window.addEventListener('resize', resize)
  if (!reduced) raf = requestAnimationFrame(tick)
  else {
    // 静态一帧
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    for (const s of stars) {
      ctx.beginPath()
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
      ctx.fillStyle = s.green
        ? `rgba(56, 189, 248, ${s.alpha})`
        : `rgba(200, 225, 255, ${s.alpha * 0.8})`
      ctx.fill()
    }
  }
})

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  window.removeEventListener('resize', resize)
})
</script>

<style scoped>
.bg-layer {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, rgba(56, 189, 248, 0.06), transparent 60%),
    radial-gradient(ellipse 60% 40% at 90% 100%, rgba(168, 85, 247, 0.05), transparent 60%),
    var(--bg);
}

.bg-canvas {
  position: absolute;
  inset: 0;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.05) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(ellipse 70% 60% at 50% 0%, rgba(0,0,0,.7), transparent 75%);
  -webkit-mask-image: radial-gradient(ellipse 70% 60% at 50% 0%, rgba(0,0,0,.7), transparent 75%);
}

.bg-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.5;
  will-change: transform;
}

.bg-glow-1 {
  width: 480px;
  height: 480px;
  left: -140px;
  top: -120px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.13), transparent 70%);
  animation: drift1 26s ease-in-out infinite alternate;
}

.bg-glow-2 {
  width: 420px;
  height: 420px;
  right: -120px;
  top: 30%;
  background: radial-gradient(circle, rgba(168, 85, 247, 0.1), transparent 70%);
  animation: drift2 32s ease-in-out infinite alternate;
}

.bg-glow-3 {
  width: 520px;
  height: 520px;
  left: 30%;
  bottom: -220px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.08), transparent 70%);
  animation: drift3 38s ease-in-out infinite alternate;
}

@keyframes drift1 {
  from { transform: translate(0, 0) scale(1); }
  to   { transform: translate(120px, 80px) scale(1.15); }
}

@keyframes drift2 {
  from { transform: translate(0, 0) scale(1); }
  to   { transform: translate(-100px, -60px) scale(1.1); }
}

@keyframes drift3 {
  from { transform: translate(0, 0) scale(1); }
  to   { transform: translate(80px, -100px) scale(1.12); }
}

@media (prefers-reduced-motion: reduce) {
  .bg-glow { animation: none; }
}
</style>
