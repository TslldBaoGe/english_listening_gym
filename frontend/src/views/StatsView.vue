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
      <div v-for="w in s.worst_sentences || []" :key="w.id" class="wrong-row">
        <div class="wrong-text">
          <span class="mono" style="color:#f56c6c">✗{{ w.wrong_count }}</span>
          <span class="mono" style="margin-left:10px">{{ w.text }}</span>
        </div>
        <el-button size="small" plain type="danger" :loading="deleting === w.id"
                   @click="removeWrong(w)">删除</el-button>
      </div>
      <el-empty v-if="!(s.worst_sentences || []).length" description="还没有错题，继续加油" :image-size="60" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from '../utils/message'
import api from '../api'
const s = ref({})
const deleting = ref(0)

async function load() {
  s.value = (await api.stats()).data
}

onMounted(load)

async function removeWrong(w) {
  try {
    await ElMessageBox.confirm(
      '把这道错题从错题本移除（错误次数清零）？句子和音频仍保留在 04 知识库。',
      '删除错题', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }   // 用户取消
  deleting.value = w.id
  try {
    await api.deleteWrong(w.id)
    await load()
    ElMessage.success('已移出错题本')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  } finally { deleting.value = 0 }
}
</script>

<style scoped>
.wrong-row {
  display: flex; align-items: center; gap: 12px;
  padding: 8px 0; border-bottom: 1px solid var(--border);
}
.wrong-text { flex: 1; min-width: 0; word-break: break-word; }
</style>
