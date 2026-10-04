import { watch } from 'vue'

/**
 * 页面状态的临时持久化：切菜单、刷新、重新打开网站后，上次的内容还在。
 *
 * @param {string} key       localStorage 的键，每个页面一个
 * @param {() => object} snapshot  返回要保存的普通对象（需可 JSON 序列化）
 * @param {(saved: object) => void} apply  把保存的值写回响应式状态
 *
 * 用法：在组件里 const vs = useViewState(...)；然后在自己的 onMounted
 * 最后一行调用 vs.restore()（放最后，避免被页面里的默认值覆盖）。
 */
export function useViewState(key, snapshot, apply) {
  watch(snapshot, (val) => {
    try {
      localStorage.setItem(key, JSON.stringify(val))
    } catch (e) {
      /* 隐私模式等场景写不了就算了，不影响使用 */
    }
  }, { deep: true })

  return {
    restore() {
      try {
        const raw = localStorage.getItem(key)
        if (!raw) return
        const saved = JSON.parse(raw)
        if (saved && typeof saved === 'object') apply(saved)
      } catch (e) {
        /* 存的内容坏了就忽略，按空状态开始 */
      }
    },
    clear() {
      try {
        localStorage.removeItem(key)
      } catch (e) { /* 忽略 */ }
    },
  }
}
