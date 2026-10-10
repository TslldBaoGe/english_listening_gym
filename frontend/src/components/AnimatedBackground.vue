<template>
  <div class="bg-layer" aria-hidden="true">
    <div class="bg-glow bg-glow-1"></div>
    <div class="bg-glow bg-glow-2"></div>
    <div class="bg-glow bg-glow-3"></div>
    <div class="bg-aurora"></div>
    <canvas ref="canvasRef" class="bg-canvas"></canvas>
    <div class="bg-grid"></div>
    <div class="grid-floor"></div>
    <div class="scanline"></div>
    <div class="vignette"></div>

    <!-- 白天主题的动态背景：飘云 + 光束 + 上浮光斑 -->
    <div class="day-sky">
      <div class="day-ray day-ray-1"></div>
      <div class="day-ray day-ray-2"></div>
      <div class="day-ray day-ray-3"></div>
      <div class="day-bokeh"></div>
      <div class="day-cloud day-cloud-1"></div>
      <div class="day-cloud day-cloud-2"></div>
      <div class="day-cloud day-cloud-3"></div>
      <div class="day-cloud day-cloud-4"></div>
    </div>
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
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.05) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(ellipse 70% 60% at 50% 0%, rgba(0,0,0,.7), transparent 75%);
  -webkit-mask-image: radial-gradient(ellipse 70% 60% at 50% 0%, rgba(0,0,0,.7), transparent 75%);
}

/* 仿参考站：透视网格地面，底部斜置并向上滚动 */
.grid-floor {
  position: absolute;
  left: -50%;
  bottom: -32vh;
  width: 200%;
  height: 60vh;
  background-image:
    linear-gradient(rgba(56, 189, 248, 0.10) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.10) 1px, transparent 1px);
  background-size: 64px 64px;
  transform: perspective(420px) rotateX(64deg);
  animation: gridScroll 2.4s linear infinite;
  -webkit-mask-image: linear-gradient(to top, rgba(0,0,0,.85) 15%, transparent 80%);
  mask-image: linear-gradient(to top, rgba(0,0,0,.85) 15%, transparent 80%);
}

@keyframes gridScroll {
  from { background-position-y: 0; }
  to   { background-position-y: 64px; }
}

/* 仿参考站：极光层（大块模糊流动光晕，高饱和） */
.bg-aurora {
  position: absolute;
  inset: -8%;
  filter: blur(60px) saturate(1.4);
  opacity: 0.55;
  background:
    radial-gradient(ellipse 40% 30% at 20% 30%, rgba(56, 189, 248, 0.18), transparent 70%),
    radial-gradient(ellipse 35% 28% at 75% 20%, rgba(168, 85, 247, 0.14), transparent 70%),
    radial-gradient(ellipse 45% 32% at 55% 75%, rgba(56, 189, 248, 0.10), transparent 70%),
    radial-gradient(ellipse 30% 25% at 30% 85%, rgba(244, 114, 182, 0.08), transparent 70%);
  animation: auroraShift 18s ease-in-out infinite alternate;
}

@keyframes auroraShift {
  from { transform: translateX(-3%) scale(1.02); }
  to   { transform: translateX(3%) scale(1.08); }
}

/* 仿参考站：扫描线改为横扫，竖光带从左向右移动 */
.scanline {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 140px;
  background: linear-gradient(to right, transparent, rgba(56, 189, 248, 0.05), transparent);
  animation: scanMove 9s linear infinite;
}

@keyframes scanMove {
  from { left: -20%; }
  to   { left: 120%; }
}

/* 仿参考站：暗角，聚焦画面中心 */
.vignette {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at center, transparent 45%, rgba(0, 0, 8, 0.65) 100%);
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
  .bg-glow, .grid-floor, .bg-aurora, .scanline { animation: none; }
}

/* ── 白天主题专属动态背景：飘云 + 摆动光束 + 上浮光斑 ──
   默认隐藏，由 theme-light.css 在浅色主题下显示 */
.day-sky {
  position: absolute;
  inset: 0;
  overflow: hidden;
  display: none;
}

/* 光束：从顶部斜洒下来的暖色阳光，缓慢摆动 */
.day-ray {
  position: absolute;
  top: -14%;
  width: 150px;
  height: 130vh;
  background: linear-gradient(180deg, rgba(255, 236, 170, .5), rgba(255, 244, 214, .16) 55%, transparent 85%);
  filter: blur(18px);
  transform-origin: top center;
  opacity: 0;
  animation: dayRaySway 17s ease-in-out infinite;
}
.day-ray-1 { left: 14%; }
.day-ray-2 { left: 46%; width: 90px; animation-delay: -6s; }
.day-ray-3 { left: 72%; width: 190px; animation-delay: -11.5s; }

@keyframes dayRaySway {
  0%, 100% { opacity: 0; transform: rotate(14deg); }
  30%, 70% { opacity: .75; transform: rotate(20deg); }
}

/* 光斑：柔和的圆点缓缓上浮 */
.day-bokeh {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(14px 14px at 18% 88%, rgba(2, 132, 199, .10), transparent),
    radial-gradient(10px 10px at 42% 96%, rgba(124, 58, 237, .09), transparent),
    radial-gradient(18px 18px at 66% 92%, rgba(56, 189, 248, .09), transparent),
    radial-gradient(9px 9px at 84% 98%, rgba(236, 72, 153, .07), transparent);
  animation: dayBokehFloat 22s linear infinite;
}

@keyframes dayBokehFloat {
  from { transform: translate3d(0, 0, 0); }
  to   { transform: translate3d(2%, -55vh, 0); opacity: 0; }
}

/* 云朵：白色柔边，缓慢横飘 */
.day-cloud {
  position: absolute;
  height: 0;
  border-radius: 999px;
  background:
    radial-gradient(closest-side at 30% 50%, rgba(255, 255, 255, .95), transparent),
    radial-gradient(closest-side at 55% 40%, rgba(255, 255, 255, .9), transparent),
    radial-gradient(closest-side at 75% 55%, rgba(244, 248, 255, .85), transparent);
  filter: blur(4px);
  animation: dayCloudDrift linear infinite;
}
.day-cloud-1 { top: 8%;  width: 380px; height: 110px; animation-duration: 95s;  opacity: .95; }
.day-cloud-2 { top: 20%; width: 280px; height: 90px;  animation-duration: 120s; animation-delay: -40s; opacity: .85; }
.day-cloud-3 { top: 42%; width: 460px; height: 130px; animation-duration: 150s; animation-delay: -90s; opacity: .7; }
.day-cloud-4 { top: 62%; width: 240px; height: 80px;  animation-duration: 110s; animation-delay: -20s; opacity: .55; }

@keyframes dayCloudDrift {
  from { transform: translateX(-40vw); }
  to   { transform: translateX(115vw); }
}

@media (prefers-reduced-motion: reduce) {
  .day-ray, .day-bokeh, .day-cloud { animation: none; }
}
</style>
