<template>
  <span class="sky" aria-hidden="true">
    <span class="sky-stars sky-stars-a"></span>
    <span class="sky-stars sky-stars-b"></span>
    <span class="sky-shoot" :style="{ animationDelay: `${delay}s` }"></span>
  </span>
</template>

<script setup>
defineProps({ delay: { type: Number, default: 0 } })
</script>

<style scoped>
/* 按钮内的迷你夜空：星点闪烁 + 偶尔划过的流星。
   纯 CSS，不用 canvas，几十个按钮同时也不会掉帧。 */
.sky {
  position: absolute;
  inset: 0;
  overflow: hidden;
  border-radius: inherit;
  pointer-events: none;
  z-index: 0;
}

.sky-stars {
  position: absolute;
  inset: -30%;
  background-repeat: no-repeat;
}

.sky-stars-a {
  background-image:
    radial-gradient(1.1px 1.1px at 14% 26%, rgba(255, 255, 255, .9), transparent),
    radial-gradient(1px 1px at 62% 18%, rgba(186, 230, 253, .85), transparent),
    radial-gradient(1px 1px at 82% 62%, rgba(255, 255, 255, .75), transparent),
    radial-gradient(1.3px 1.3px at 36% 74%, rgba(186, 230, 253, .8), transparent),
    radial-gradient(1px 1px at 52% 46%, rgba(255, 255, 255, .7), transparent);
  animation: twinkleA 3.6s ease-in-out infinite alternate;
}

.sky-stars-b {
  background-image:
    radial-gradient(1px 1px at 24% 58%, rgba(216, 180, 254, .8), transparent),
    radial-gradient(1.2px 1.2px at 72% 34%, rgba(255, 255, 255, .8), transparent),
    radial-gradient(1px 1px at 44% 12%, rgba(186, 230, 253, .75), transparent),
    radial-gradient(1px 1px at 90% 80%, rgba(255, 255, 255, .65), transparent);
  animation: twinkleB 5.2s ease-in-out infinite alternate,
             drift 16s linear infinite;
}

@keyframes twinkleA {
  from { opacity: .35; }
  to   { opacity: .95; }
}

@keyframes twinkleB {
  from { opacity: .9; }
  to   { opacity: .4; }
}

@keyframes drift {
  from { transform: translate3d(-6%, 0, 0); }
  to   { transform: translate3d(6%, 2%, 0); }
}

/* 流星：斜向下划过，大部分时间在休息 */
.sky-shoot {
  position: absolute;
  top: -40%;
  left: -50%;
  width: 45%;
  height: 1.5px;
  background: linear-gradient(90deg, transparent, rgba(186, 230, 253, .9));
  transform: rotate(24deg);
  opacity: 0;
  animation: shoot 7.5s linear infinite;
}

@keyframes shoot {
  0%   { transform: translate3d(0, 0, 0) rotate(24deg); opacity: 0; }
  6%   { opacity: .85; }
  26%  { transform: translate3d(260%, 190%, 0) rotate(24deg); opacity: 0; }
  100% { transform: translate3d(260%, 190%, 0) rotate(24deg); opacity: 0; }
}

@media (prefers-reduced-motion: reduce) {
  .sky-stars-a, .sky-stars-b, .sky-shoot { animation: none; }
}
</style>
