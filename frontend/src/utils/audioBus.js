/**
 * 全站音频总线：模块级单例，所有 AudioPlayer 实例共用。
 *
 * 关键点：组件里 <script setup> 的顶层变量是「每个实例一份」的，
 * 所以缓存和「当前在播」必须放在这个独立模块里，卡片之间才能互相叫停。
 */
const CACHE_MAX = 40
const cache = new Map()      // url -> HTMLAudioElement
let current = null           // 当前正在播的元素（全站唯一）

/** 取（或创建）某个音频 URL 对应的元素；同一 URL 只下载/缓冲一次 */
export function getAudio(url, loop) {
  let el = cache.get(url)
  if (!el) {
    el = new Audio(url)
    el.preload = 'auto'
    el.loop = !!loop
    cache.set(url, el)
    if (cache.size > CACHE_MAX) {            // 超出上限释放最旧的一个
      const [oldUrl, oldEl] = cache.entries().next().value
      if (oldEl !== current) { oldEl.src = ''; cache.delete(oldUrl) }
    }
  } else if (el.loop !== !!loop) {
    el.loop = !!loop
  }
  return el
}

/** 认领播放权：把上一个还在播的元素停掉 */
export function claim(el) {
  if (current && current !== el) {
    try { current.pause(); current.currentTime = 0 } catch (e) { /* 忽略 */ }
  }
  current = el
  return el
}

/** 主动停止时释放（暂停/结束/卸载） */
export function release(el) {
  if (current === el) current = null
}

/** 循环开关变化：同步到所有已缓存元素 */
export function setLoopAll(v) {
  cache.forEach(el => { el.loop = !!v })
  if (current) current.loop = !!v
}

export function currentAudio() {
  return current
}

/**
 * 音频解锁：在用户手势里同步播一小段静音，把浏览器的自动播放权限"热"出来。
 * iOS Safari 等严格浏览器要求首次 play() 必须在手势内，异步调用会被拦。
 */
let unlockedEl = null
function silentWavUrl() {
  const sr = 8000, n = sr / 4
  const buf = new ArrayBuffer(44 + n * 2)
  const v = new DataView(buf)
  const w = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)) }
  w(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); w(8, 'WAVE')
  w(12, 'fmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true)
  v.setUint32(24, sr, true); v.setUint32(28, sr * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true)
  w(36, 'data'); v.setUint32(40, n * 2, true)
  return URL.createObjectURL(new Blob([buf], { type: 'audio/wav' }))
}

export function prewarm() {
  try {
    if (!unlockedEl) unlockedEl = new Audio()
    unlockedEl.src = silentWavUrl()
    unlockedEl.volume = 1
    const p = unlockedEl.play()
    if (p && typeof p.catch === 'function') p.catch(() => { /* 静音解锁失败就靠用户再点 */ })
  } catch (e) { /* 忽略 */ }
}

/**
 * 共享的 WebAudio 上下文：给播放器做软件增益用。
 * 必须在用户手势里创建/恢复；返回 null 表示当前环境不允许（此时走原生音量）。
 */
export function ensureAudioContext() {
  try {
    if (!window.__elAudioCtx) {
      const AC = window.AudioContext || window.webkitAudioContext
      if (!AC) return null
      window.__elAudioCtx = new AC()
    }
    if (window.__elAudioCtx.state === 'suspended') window.__elAudioCtx.resume()
    return window.__elAudioCtx.state === 'running' ? window.__elAudioCtx : window.__elAudioCtx
  } catch (e) {
    return null
  }
}
