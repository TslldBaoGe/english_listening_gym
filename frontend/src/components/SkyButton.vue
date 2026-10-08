<template>
  <button class="sky-button" :class="[`v-${variant}`, `s-${size}`, { 'is-loading': loading }]"
          :disabled="disabled || loading" @click="$emit('click', $event)">
    <SkyBackdrop :delay="delay" />
    <span class="sb-inner">
      <svg v-if="loading" class="sb-spin" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2.4"
                stroke-linecap="round" stroke-dasharray="42 14" />
      </svg>
      <slot />
    </span>
  </button>
</template>

<script setup>
import SkyBackdrop from './SkyBackdrop.vue'

defineProps({
  variant: { type: String, default: 'primary' },   // primary | ghost | danger
  size: { type: String, default: 'normal' },       // normal | small
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  delay: { type: Number, default: 0 },
})
defineEmits(['click'])
</script>

<style scoped>
/* 全站操作按钮：和播放器控件同一套「夜空玻璃」外观 */
.sky-button {
  position: relative;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(16, 22, 36, .92), rgba(9, 13, 22, .96));
  color: var(--text);
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  letter-spacing: 1px;
  padding: 0 18px;
  height: 38px;
  cursor: pointer;
  transition: color .18s, border-color .18s, box-shadow .2s, transform .16s;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}

.sky-button:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(56, 189, 248, .5);
  color: var(--accent);
  box-shadow: 0 4px 14px rgba(0, 0, 0, .35);
}

.sky-button:active:not(:disabled) {
  transform: translateY(0) scale(.98);
}

.sky-button:disabled {
  opacity: .55;
  cursor: not-allowed;
}

.sb-inner {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.sb-spin {
  width: 15px;
  height: 15px;
  display: block;
  animation: sbSpin 1s linear infinite;
}

@keyframes sbSpin {
  to { transform: rotate(360deg); }
}

/* 主操作：霓虹蓝描边 + 内发光 */
.v-primary {
  color: var(--accent);
  border-color: rgba(56, 189, 248, .45);
  box-shadow: inset 0 0 16px rgba(56, 189, 248, .10);
}

.v-primary:hover:not(:disabled) {
  border-color: rgba(56, 189, 248, .72);
  box-shadow: inset 0 0 20px rgba(56, 189, 248, .16);
}

/* 次要：中性 */
.v-ghost {
  color: var(--text-dim);
}

/* 危险：红 */
.v-danger {
  color: #f87171;
  border-color: rgba(245, 108, 108, .4);
}

.v-danger:hover:not(:disabled) {
  color: #fca5a5;
  border-color: rgba(245, 108, 108, .7);
}

.s-small {
  height: 30px;
  padding: 0 13px;
  font-size: 12.5px;
  border-radius: 8px;
}

@media (prefers-reduced-motion: reduce) {
  .sb-spin { animation: none; }
}

/* 手机/平板：加大点击区域 */
@media (max-width: 720px) {
  .sky-button {
    height: 44px;
    font-size: 15px;
  }
  .s-small {
    height: 36px;
    font-size: 13px;
  }
}
</style>
