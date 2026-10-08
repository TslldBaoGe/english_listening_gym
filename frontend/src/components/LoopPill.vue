<template>
  <button class="loop-pill" :class="{ on: modelValue }" :aria-pressed="modelValue"
          @click="$emit('update:modelValue', !modelValue)">
    <SkyBackdrop :delay="2.6" />
    <span class="loop-inner">
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
    </span>
  </button>
</template>

<script setup>
import SkyBackdrop from './SkyBackdrop.vue'

defineProps({ modelValue: { type: Boolean, default: false } })
defineEmits(['update:modelValue'])
</script>

<style scoped>
/* 循环开关：和播放键/倍速键同一套「夜空玻璃」外观 */
.loop-pill {
  position: relative;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(16, 22, 36, .92), rgba(9, 13, 22, .96));
  color: var(--text-dim);
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  font-size: 12.5px;
  letter-spacing: 1px;
  cursor: pointer;
  transition: color .18s, border-color .18s, background .18s, box-shadow .2s;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}

.loop-inner {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 6px;
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
  border-color: rgba(56, 189, 248, .5);
  background: linear-gradient(180deg, rgba(24, 40, 62, .95), rgba(14, 22, 38, .96));
  box-shadow: inset 0 0 14px rgba(56, 189, 248, .16);
}

/* 状态靠描边和淡底区分，不做持续呼吸发光（长时间盯着累眼） */

/* 手机/平板：加大点击区域，样式不变 */
@media (max-width: 900px) {
  .loop-pill {
    height: 34px;
    padding: 0 14px;
    font-size: 13px;
  }
}
</style>
