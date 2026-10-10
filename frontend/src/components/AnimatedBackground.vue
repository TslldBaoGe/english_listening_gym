<template>
  <div class="bg-layer" aria-hidden="true">
    <!-- 夜间层：深空星夜 -->
    <div class="bg-glow bg-glow-1"></div>
    <div class="bg-glow bg-glow-2"></div>
    <div class="bg-glow bg-glow-3"></div>
    <div class="bg-aurora"></div>
    <canvas ref="canvasRef" class="bg-canvas"></canvas>
    <div class="bg-grid"></div>
    <div class="grid-floor"></div>
    <div class="scanline"></div>
    <div class="vignette"></div>

    <!-- 白天层：白天（canvas 手绘晴空场景，仅浅色主题显示） -->
    <canvas ref="dayCanvasRef" class="day-canvas"></canvas>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'

/* ═══════════ 夜间：星空 + 流星（保持原有体验） ═══════════ */
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
  resizeDay()
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

function tick(now) {
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

  const t = performance.now()
  if (t >= nextMeteorAt && meteors.length < 3) spawnMeteor(t)
  meteors = meteors.filter((m) => m.life < m.maxLife)
  for (const m of meteors) {
    m.life++
    m.x += m.vx
    m.y += m.vy
    const fade = Math.sin(Math.min(1, m.life / m.maxLife) * Math.PI)
    const len = Math.hypot(m.vx, m.vy)
    const nx = m.x - m.vx * (m.len / len)
    const ny = m.y - m.vy * (m.len / len)
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
    ctx.beginPath()
    ctx.arc(m.x, m.y, 1.6 * dpr, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(255, 255, 255, ${0.85 * fade})`
    ctx.fill()
  }
  raf = requestAnimationFrame(tick)
}

/* ═══════════ 白天：晴空 + 太阳 + 视差云 + 鸟群 + 光尘 ═══════════ */
const dayCanvasRef = ref(null)
let dayCtx = null
let dayRaf = 0
let dayRunning = false
let dayDpr = 1
let dayW = 0
let dayH = 0
let clouds = []       // { sprite, x, y, w, h, speed, alpha }
let birds = []        // { x, y, size, speed, dir, phase, flap }
let motes = []        // { x, y, r, vy, wob, wobSpeed, alpha, hue }
let sunSprite = null
let lastTs = 0

// 稳定的伪随机：同一场景每次刷新长得一致，不会乱跳
function mulberry32(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/** 预渲染一朵积云：多圆叠加 + 底部淡影，边缘柔和 */
function makeCloudSprite(rnd, w, h) {
  const c = document.createElement('canvas')
  c.width = w * 2
  c.height = h * 2
  const g = c.getContext('2d')
  g.scale(2, 2)
  const puffs = 6 + Math.floor(rnd() * 3)
  const baseY = h * 0.62
  g.fillStyle = 'rgba(148, 178, 216, 0.30)'
  g.beginPath()
  g.ellipse(w * 0.5, baseY + h * 0.10, w * 0.36, h * 0.16, 0, 0, Math.PI * 2)
  g.fill()
  for (let i = 0; i < puffs; i++) {
    const px = w * (0.14 + 0.72 * (i / (puffs - 1))) + (rnd() - 0.5) * w * 0.06
    const pr = h * (0.26 + rnd() * 0.24) * (1 - Math.abs(i / (puffs - 1) - 0.5) * 0.7)
    const py = baseY - pr * 0.55 - (i === Math.floor(puffs / 2) ? h * 0.14 : 0)
    const grad = g.createRadialGradient(px, py - pr * 0.25, pr * 0.2, px, py, pr)
    grad.addColorStop(0, 'rgba(255, 255, 255, 0.98)')
    grad.addColorStop(1, 'rgba(244, 249, 255, 0.88)')
    g.fillStyle = grad
    g.beginPath()
    g.arc(px, py, pr, 0, Math.PI * 2)
    g.fill()
  }
  return c
}

/** 预渲染太阳：亮核 + 双层光晕 */
function makeSunSprite(size) {
  const c = document.createElement('canvas')
  c.width = c.height = size * 2
  const g = c.getContext('2d')
  g.scale(2, 2)
  const r = size / 2
  const halo = g.createRadialGradient(r, r, r * 0.1, r, r, r)
  halo.addColorStop(0, 'rgba(255, 252, 235, 0.95)')
  halo.addColorStop(0.25, 'rgba(255, 238, 180, 0.55)')
  halo.addColorStop(0.6, 'rgba(255, 224, 130, 0.16)')
  halo.addColorStop(1, 'rgba(255, 224, 130, 0)')
  g.fillStyle = halo
  g.fillRect(0, 0, size, size)
  return c
}

function buildDayScene() {
  const rnd = mulberry32(20261011)
  clouds = []
  birds = []
  motes = []
  // 三层视差云：远（小而慢）→ 近（大而快）
  const layers = [
    { n: 3, w: [180, 260], h: [52, 76], speed: [7, 10], ys: [0.04, 0.30], alpha: 0.72 },
    { n: 3, w: [280, 400], h: [80, 112], speed: [13, 17], ys: [0.10, 0.42], alpha: 0.88 },
    { n: 3, w: [380, 540], h: [108, 150], speed: [20, 26], ys: [0.05, 0.38], alpha: 1 },
  ]
  for (const layer of layers) {
    for (let i = 0; i < layer.n; i++) {
      const w = layer.w[0] + rnd() * (layer.w[1] - layer.w[0])
      const h = layer.h[0] + rnd() * (layer.h[1] - layer.h[0])
      clouds.push({
        sprite: makeCloudSprite(rnd, w, h),
        w, h,
        x: rnd() * dayW,
        y: dayH * (layer.ys[0] + rnd() * (layer.ys[1] - layer.ys[0])),
        speed: layer.speed[0] + rnd() * (layer.speed[1] - layer.speed[0]),
        alpha: layer.alpha * (0.85 + rnd() * 0.15),
      })
    }
  }
  sunSprite = makeSunSprite(Math.min(300, dayW * 0.28))
  for (let i = 0; i < 16; i++) {
    motes.push({
      x: rnd() * dayW,
      y: rnd() * dayH,
      r: 1.2 + rnd() * 2.6,
      vy: 6 + rnd() * 10,
      wob: rnd() * Math.PI * 2,
      wobSpeed: 0.4 + rnd() * 0.8,
      alpha: 0.12 + rnd() * 0.2,
      hue: rnd() < 0.5 ? '2, 132, 199' : '124, 58, 237',
    })
  }
}

function resizeDay() {
  const canvas = dayCanvasRef.value
  if (!canvas) return
  dayDpr = Math.min(window.devicePixelRatio || 1, 2)
  dayW = window.innerWidth
  dayH = window.innerHeight
  canvas.width = dayW * dayDpr
  canvas.height = dayH * dayDpr
  canvas.style.width = dayW + 'px'
  canvas.style.height = dayH + 'px'
  dayCtx = canvas.getContext('2d')
  dayCtx.setTransform(dayDpr, 0, 0, dayDpr, 0, 0)
  buildDayScene()
}

function spawnBirds() {
  const dir = Math.random() < 0.5 ? 1 : -1
  const n = 3 + Math.floor(Math.random() * 3)
  const y = dayH * (0.10 + Math.random() * 0.16)
  const size = 7 + Math.random() * 5
  for (let i = 0; i < n; i++) {
    birds.push({
      x: dir > 0 ? -40 - i * 26 - Math.random() * 20 : dayW + 40 + i * 26 + Math.random() * 20,
      y: y + (Math.random() - 0.5) * 34,
      size,
      speed: (52 + Math.random() * 22) * dir,
      dir,
      phase: Math.random() * Math.PI * 2,
      flap: 7 + Math.random() * 4,
    })
  }
}

function drawBird(g, b, ts) {
  const flap = Math.sin(b.phase + ts * 0.001 * b.flap)
  const wing = b.size * (0.55 + 0.35 * Math.sin(b.phase + ts * 0.001 * b.flap * 2))
  g.strokeStyle = 'rgba(51, 65, 85, 0.78)'
  g.lineWidth = Math.max(1.4, b.size * 0.16)
  g.lineCap = 'round'
  const x = b.x, y = b.y + Math.sin(ts * 0.0012 + b.phase) * 4
  g.beginPath()
  g.moveTo(x - b.size, y + wing * 0.35 * flap)
  g.quadraticCurveTo(x - b.size * 0.4, y - wing * 0.5, x, y)
  g.quadraticCurveTo(x + b.size * 0.4, y - wing * 0.5, x + b.size, y + wing * 0.35 * flap)
  g.stroke()
}

function dayTick(ts) {
  const g = dayCtx
  if (!g) return
  const dt = Math.min(0.05, (ts - lastTs) / 1000 || 0.016)
  lastTs = ts
  drawDayFrame(dt)
}

function drawDayFrame(dt) {
  const g = dayCtx
  if (!g) return

  // 天空渐变
  const sky = g.createLinearGradient(0, 0, 0, dayH)
  sky.addColorStop(0, '#d8ecfb')
  sky.addColorStop(0.45, '#eaf3fc')
  sky.addColorStop(1, '#f6f9fd')
  g.fillStyle = sky
  g.fillRect(0, 0, dayW, dayH)

  // 太阳（缓慢呼吸）
  const sunX = dayW * 0.82, sunY = dayH * 0.14
  const breathe = 1 + Math.sin(performance.now() * 0.0004) * 0.04
  const sw = sunSprite.width / 2 * breathe
  g.drawImage(sunSprite, sunX - sw / 2, sunY - sw / 2, sw, sw)

  // 视差云
  for (const c of clouds) {
    c.x += c.speed * dt
    if (c.x > dayW + c.w * 0.2) c.x = -c.w - 20
    g.globalAlpha = c.alpha
    g.drawImage(c.sprite, c.x, c.y, c.w, c.h)
  }
  g.globalAlpha = 1

  // 鸟群：偶尔飞过一群
  if (birds.length === 0 && Math.random() < dt * 0.06) spawnBirds()
  birds = birds.filter((b) => b.x > -80 && b.x < dayW + 80)
  for (const b of birds) {
    b.x += b.speed * dt
    drawBird(g, b, ts)
  }

  // 上浮光尘（左右轻摆）
  for (const m of motes) {
    m.y -= m.vy * dt
    m.wob += m.wobSpeed * dt
    if (m.y < -10) { m.y = dayH + 10; m.x = Math.random() * dayW }
    const x = m.x + Math.sin(m.wob) * 18
    g.beginPath()
    g.arc(x, m.y, m.r, 0, Math.PI * 2)
    g.fillStyle = `rgba(${m.hue}, ${m.alpha})`
    g.fill()
  }
}

function startDay() {
  if (dayRunning || !dayCanvasRef.value) return
  dayRunning = true
  resizeDay()
  lastTs = performance.now()
  // 立即画第一帧：切到白天主题的瞬间场景就在（窗口无焦点/动画被挂起时也不空白）
  dayTick(lastTs)
  const loop = (ts) => {
    if (!dayRunning) return
    dayTick(ts)
    dayRaf = requestAnimationFrame(loop)
  }
  dayRaf = requestAnimationFrame(loop)
}

function stopDay() {
  dayRunning = false
  if (dayRaf) cancelAnimationFrame(dayRaf)
  dayRaf = 0
  const canvas = dayCanvasRef.value
  if (canvas && dayCtx) dayCtx.clearRect(0, 0, canvas.width, canvas.height)
}

/* ═══════════ 主题切换：只在白天主题运行白天场景 ═══════════ */
let themeObserver = null

function currentTheme() {
  return document.documentElement.dataset.theme === 'light' ? 'light' : 'dark'
}

function applyThemeLayers() {
  if (currentTheme() === 'light') startDay()
  else stopDay()
}

onMounted(() => {
  const canvas = canvasRef.value
  ctx = canvas.getContext('2d')
  resize()
  window.addEventListener('resize', resize)
  nextMeteorAt = performance.now() + 1200
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (!reduced) raf = requestAnimationFrame(tick)

  applyThemeLayers()
  // 主题切换由 App.vue 直接改 data-theme，这里观察它来启停白天场景
  themeObserver = new MutationObserver(applyThemeLayers)
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
  // 页面不可见时暂停白天场景，回来继续
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stopDay()
    else applyThemeLayers()
  })
})

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  stopDay()
  window.removeEventListener('resize', resize)
  if (themeObserver) themeObserver.disconnect()
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
    var(--bg);
}

.bg-canvas,
.day-canvas {
  position: absolute;
  inset: 0;
}

.day-canvas { display: none; }
html[data-theme="light"] .day-canvas { display: block; }
html[data-theme="light"] .bg-canvas,
html[data-theme="light"] .bg-glow,
html[data-theme="light"] .bg-aurora,
html[data-theme="light"] .bg-grid,
html[data-theme="light"] .grid-floor,
html[data-theme="light"] .scanline,
html[data-theme="light"] .vignette { display: none; }

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
</style>
