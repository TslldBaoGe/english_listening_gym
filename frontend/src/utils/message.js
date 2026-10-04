import { ElMessage as RawMessage, ElMessageBox } from 'element-plus'

// 提示停留时间：Element Plus 默认 3000ms，太久会挡着操作，这里改短
const OK_MS = 1200      // 成功/普通提示
const PROBLEM_MS = 2200 // 警告/报错，稍微多留一点时间看

function make(type, duration) {
  return (msg, opts = {}) => {
    const base = typeof msg === 'string' ? { message: msg } : { ...(msg || {}) }
    return RawMessage({ type, duration, ...base, ...opts })
  }
}

// 用法和原来完全一样：ElMessage.success('...')，只是停留时间变短了
const ElMessage = (opts) => RawMessage(opts)
ElMessage.success = make('success', OK_MS)
ElMessage.info = make('info', OK_MS)
ElMessage.warning = make('warning', PROBLEM_MS)
ElMessage.error = make('error', PROBLEM_MS)
ElMessage.closeAll = RawMessage.closeAll

export { ElMessage, ElMessageBox }
