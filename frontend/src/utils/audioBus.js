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
