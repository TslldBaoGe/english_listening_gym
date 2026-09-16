<template>
  <div class="page">
    <div class="section-tag">// 03 · STATS</div>
    <h2 style="color:#e6edf3;margin:0 0 20px">学习统计</h2>

    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:20px">
      <div class="card mono">
        <div style="color:var(--text-dim);font-size:13px">TOTAL SENTENCES</div>
        <div style="color:var(--accent);font-size:32px">{{ s.total_sentences || 0 }}</div>
      </div>
      <div class="card mono">
        <div style="color:var(--text-dim);font-size:13px">ATTEMPTS</div>
        <div style="color:var(--accent-2);font-size:32px">{{ s.total_attempts || 0 }}</div>
      </div>
      <div class="card mono">
        <div style="color:var(--text-dim);font-size:13px">CORRECT RATE</div>
        <div style="color:#e6edf3;font-size:32px">
          {{ s.correct_rate == null ? '—' : (s.correct_rate * 100).toFixed(0) + '%' }}</div>
      </div>
    </div>

    <div class="card" style="margin-bottom:20px">
      <div class="section-tag">难度分布</div>
      <el-progress v-for="(v, k) in s.by_difficulty" :key="k"
        :percentage="Math.round(v / (s.total_sentences || 1) * 100)"
        :format="() => `${k}: ${v} 句`" style="margin:8px 0" />
      <el-empty v-if="!Object.keys(s.by_difficulty || {}).length" description="暂无数据" :image-size="60" />
    </div>

    <div class="card">
      <div class="section-tag">错题 TOP 10</div>
      <div v-for="w in s.worst_sentences || []" :key="w.id" style="padding:8px 0;border-bottom:1px solid var(--border)">
        <span class="mono" style="color:#f56c6c">✗{{ w.wrong_count }}</span>
        <span class="mono" style="margin-left:10px">{{ w.text }}</span>
      </div>
      <el-empty v-if="!(s.worst_sentences || []).length" description="还没有错题，继续加油" :image-size="60" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
const s = ref({})
onMounted(async () => { s.value = (await api.stats()).data })
</script>
