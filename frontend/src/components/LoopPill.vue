<template>
  <button class="loop-pill" :class="{ on: modelValue }" :aria-pressed="modelValue"
          @click="$emit('update:modelValue', !modelValue)">
    <svg class="loop-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 9.5A4.5 4.5 0 0 1 8.5 5h9.2" fill="none" stroke="currentColor"
            stroke-width="1.9" stroke-linecap="round" />
      <path d="M15.4 2.6 18.8 5l-3.4 2.4" fill="none" stroke="currentColor"
            stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M20 14.5A4.5 4.5 0 0 1 15.5 19H6.3" fill="none" stroke="currentColor"
            stroke-width="1.9" stroke-linecap="round" />
      <path d="M8.6 21.4 5.2 19l3.4-2.4" fill="none" stroke="currentColor"
            stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
    <span>{{ modelValue ? '循环中' : '循环' }}</span>
  </button>
</template>

<script setup>
defineProps({ modelValue: { type: Boolean, default: false } })
defineEmits(['update:modelValue'])
</script>

<style scoped>
/* 循环开关：全站唯一实现，播放器里和设置区共用，长相绝对一致 */
.loop-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-dim);
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  font-size: 12.5px;
  letter-spacing: 1px;
  cursor: pointer;
  transition: color .18s, border-color .18s, background .18s, box-shadow .2s;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}

.loop-icon {
  width: 16px;
  height: 16px;
  display: block;
}

.loop-pill:hover {
  color: var(--accent);
  border-color: rgba(56, 189, 248, .5);
}

.loop-pill.on {
  color: var(--accent);
  border-color: var(--accent);
  background: radial-gradient(circle at 30% 50%, rgba(56, 189, 248, .22), rgba(168, 85, 247, .12));
  box-shadow: 0 0 16px rgba(56, 189, 248, .35);
  animation: loopGlow 2.4s ease-in-out infinite;
}

@keyframes loopGlow {
  0%, 100% { box-shadow: 0 0 12px rgba(56, 189, 248, .28); }
  50%      { box-shadow: 0 0 22px rgba(168, 85, 247, .45); }
}

@media (prefers-reduced-motion: reduce) {
  .loop-pill.on { animation: none; }
}

/* 手机/平板：加大点击区域，样式不变 */
@media (max-width: 900px) {
  .loop-pill {
    height: 34px;
    padding: 0 14px;
    font-size: 13px;
  }
}
</style>
