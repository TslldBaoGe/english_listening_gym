<template>
  <div class="page">
    <div class="section-tag">// 03 · STATS</div>
    <h2 style="color:#e6edf3;margin:0 0 20px">学习统计</h2>

    <!-- 总览 -->
    <div class="grid">
      <div class="card mono stat">
        <div class="stat-label">句子总数</div>
        <div class="stat-num" style="color:var(--accent)">{{ s.total_sentences || 0 }}</div>
        <div class="stat-sub">知识库里的全部句子</div>
      </div>
      <div class="card mono stat">
        <div class="stat-label">已掌握</div>
        <div class="stat-num" style="color:#7dd3fc">
          {{ s.mastered_sentences || 0 }}<span class="stat-pct">{{ masteredPct }}%</span>
        </div>
        <div class="stat-sub">答对过，测验不再抽到</div>
      </div>
      <div class="card mono stat">
        <div class="stat-label">练习次数</div>
        <div class="stat-num" style="color:var(--accent-2)">{{ s.total_attempts || 0 }}</div>
        <div class="stat-sub">练过 {{ s.studied_sentences || 0 }} 句 · 错题 {{ s.wrong_total || 0 }} 句</div>
      </div>
      <div class="card mono stat">
        <div class="stat-label">正确率</div>
        <div class="stat-num">
          {{ s.correct_rate == null ? '—' : (s.correct_rate * 100).toFixed(0) + '%' }}
        </div>
        <div class="stat-sub">答对 {{ s.correct_attempts || 0 }} / {{ s.total_attempts || 0 }} 次</div>
      </div>
    </div>

    <!-- 最近 7 天 -->
    <div class="card" style="margin-bottom:20px">
      <div class="section-tag">最近 7 天练习量</div>
      <div class="bars">
        <div v-for="d in s.recent_7days || []" :key="d.date" class="bar-col"
             :title="`${d.date} ${d.weekday}：练习 ${d.count} 次，答对 ${d.correct} 次`">
          <div class="bar-num mono">{{ d.count || '' }}</div>
          <div class="bar-track" :class="{ today: d.is_today }">
            <div class="bar-fill" :class="{ zero: !d.count }"
                 :style="{ height: barHeight(d.count) }"></div>
          </div>
          <div class="bar-week mono" :style="d.is_today ? 'color:var(--accent)' : ''">
            {{ d.is_today ? '今天' : d.weekday }}</div>
          <div class="bar-date mono">{{ d.date.slice(5) }}</div>
        </div>
      </div>
    </div>

    <!-- 难度分布 -->
    <div class="card" style="margin-bottom:20px">
      <div class="section-tag">难度分布</div>
      <div v-for="d in s.by_difficulty || []" :key="d.code" class="diff-row">
        <div class="diff-name">
          <span class="mono" style="color:var(--accent-2)">{{ d.code }}</span>
          <span style="color:#e6edf3;margin-left:6px">{{ d.label || '—' }}</span>
          <span v-if="d.ielts" class="mono diff-ielts">IELTS {{ d.ielts }}</span>
        </div>
        <div class="diff-bar">
          <div class="diff-fill" :style="{ width: diffPct(d.count) }"></div>
        </div>
        <div class="mono diff-count">{{ d.count }} 句</div>
        <div class="diff-tags">
          <span v-if="d.mastered" class="tag tag-ok mono">已掌握 {{ d.mastered }}</span>
          <span v-if="d.wrong" class="tag tag-bad mono">错题 {{ d.wrong }}</span>
        </div>
      </div>
    </div>

    <!-- 错题 TOP 10 -->
    <div class="card">
      <div class="section-tag">错题 TOP 10（按错误次数）</div>
      <div class="hint" style="margin:-2px 0 10px">
        「移除」只清掉错误次数，句子和音频仍留在 04 知识库。
      </div>
      <div v-for="w in s.worst_sentences || []" :key="w.id" class="wrong-row">
        <div class="wrong-badge mono">✗{{ w.wrong_count }}</div>
        <div class="wrong-text">
          <div class="mono" style="color:#e6edf3;font-size:14px">{{ w.text }}</div>
          <div class="wrong-sub">{{ w.translation }}</div>
        </div>
        <span class="tag mono" style="color:var(--text-dim);border-color:var(--border)">
          {{ w.difficulty_code }}</span>
        <SkyButton size="small" variant="danger" :loading="deleting === w.id"
                   :delay="0.5" @click="removeWrong(w)">移除</SkyButton>
      </div>
      <el-empty v-if="!(s.worst_sentences || []).length" description="还没有错题，继续加油"
                :image-size="60" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from '../utils/message'
import SkyButton from '../components/SkyButton.vue'
import api from '../api'

const s = ref({})
const deleting = ref(0)

const masteredPct = computed(() => {
  const total = s.value.total_sentences || 0
  return total ? Math.round((s.value.mastered_sentences || 0) / total * 100) : 0
})

/** 柱高按这段时间里的最大值归一化，0 次留一条底线 */
function barHeight(n) {
  const list = s.value.recent_7days || []
  const max = Math.max(1, ...list.map(d => d.count || 0))
  return n ? Math.max(6, Math.round(n / max * 100)) + '%' : '3px'
}

function diffPct(n) {
  const list = s.value.by_difficulty || []
  const max = Math.max(1, ...list.map(d => d.count || 0))
  return Math.max(2, Math.round((n || 0) / max * 100)) + '%'
}

async function load() {
  s.value = (await api.stats()).data
}

onMounted(load)

async function removeWrong(w) {
  try {
    await ElMessageBox.confirm(
      '把这道错题从错题本移除（错误次数清零）？句子和音频仍保留在 04 知识库。',
      '移除错题', { type: 'warning', confirmButtonText: '移除', cancelButtonText: '取消' })
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
.grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 16px; margin-bottom: 20px;
}
.stat { padding: 16px 18px; }
.stat-label { color: var(--text-dim); font-size: 13px; letter-spacing: .5px; }
.stat-num { font-size: 32px; line-height: 1.3; color: #e6edf3; }
.stat-pct { font-size: 13px; color: var(--text-dim); margin-left: 6px; }
.stat-sub { color: var(--text-dim); font-size: 12px; }

/* 最近 7 天柱状图 */
.bars { display: flex; align-items: flex-end; gap: 10px; padding: 6px 0 0; }
.bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.bar-num { font-size: 12px; color: var(--text-dim); height: 15px; }
.bar-track {
  width: 100%; height: 88px; display: flex; align-items: flex-end;
  background: rgba(255, 255, 255, .03); border: 1px solid transparent;
  border-radius: 8px; overflow: hidden;
}
.bar-track.today { border-color: rgba(34, 211, 238, .45); }
.bar-fill {
  width: 100%; border-radius: 8px 8px 0 0;
  background: linear-gradient(180deg, var(--accent), rgba(34, 211, 238, .22));
  transition: height .3s ease;
}
.bar-fill.zero { background: rgba(255, 255, 255, .12); border-radius: 0; }
.bar-week { font-size: 12px; color: var(--text-dim); }
.bar-date { font-size: 11px; color: var(--text-dim); opacity: .55; }

/* 难度分布 */
.diff-row {
  display: flex; align-items: center; gap: 12px;
  padding: 9px 0; border-bottom: 1px solid var(--border);
}
.diff-row:last-child { border-bottom: none; }
.diff-name { width: 210px; font-size: 13px; flex-shrink: 0; }
.diff-ielts { color: var(--text-dim); font-size: 11px; margin-left: 8px; }
.diff-bar {
  flex: 1; height: 8px; background: rgba(255, 255, 255, .05);
  border-radius: 999px; overflow: hidden; min-width: 60px;
}
.diff-fill {
  height: 100%; border-radius: 999px;
  background: linear-gradient(90deg, var(--accent-2), var(--accent));
}
.diff-count { width: 60px; text-align: right; color: #e6edf3; font-size: 13px; }
.diff-tags { width: 190px; display: flex; gap: 6px; justify-content: flex-end; }

.tag {
  font-size: 11px; padding: 1px 7px; border-radius: 999px;
  border: 1px solid var(--border); white-space: nowrap;
}
.tag-ok { color: #7dd3fc; border-color: rgba(125, 211, 252, .4); }
.tag-bad { color: #f56c6c; border-color: rgba(245, 108, 108, .4); }

/* 错题 */
.wrong-row {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 0; border-bottom: 1px solid var(--border);
}
.wrong-row:last-child { border-bottom: none; }
.wrong-badge {
  color: #f56c6c; font-size: 13px; min-width: 36px; text-align: center;
  border: 1px solid rgba(245, 108, 108, .35); border-radius: 6px;
  padding: 2px 4px; flex-shrink: 0;
}
.wrong-text { flex: 1; min-width: 0; word-break: break-word; }
.wrong-sub { color: var(--text-dim); font-size: 12px; margin-top: 2px; }

@media (max-width: 720px) {
  .diff-name { width: 120px; }
  .diff-tags { width: auto; }
  .bar-date { display: none; }
}
</style>
