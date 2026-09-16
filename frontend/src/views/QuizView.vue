<template>
  <div class="page">
    <div class="section-tag">// 02 · QUIZ</div>
    <h2 style="color:#e6edf3;margin:0 0 20px">随机抽考 · 听音选句</h2>

    <div class="card">
      <el-form inline v-if="!current">
        <el-form-item label="难度">
          <el-select v-model="filter.difficulty" clearable placeholder="不限" style="width:160px">
            <el-option v-for="d in difficulties" :key="d.code" :label="d.code + ' ' + d.label" :value="d.code" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button class="glow-btn" type="primary" plain :loading="loading" @click="next">开始测验</el-button>
        </el-form-item>
      </el-form>

      <template v-if="current">
        <div class="mono" style="color:var(--accent-2);font-size:12px;margin-bottom:12px">
          {{ current.difficulty }} · {{ current.topic }}
        </div>
        <AudioPlayer :sentence-id="current.sentenceId" :rate="store.rate" />
        <div style="margin-top:20px;display:flex;flex-direction:column;gap:10px">
          <div v-for="(opt, i) in current.options" :key="i"
               class="option mono"
               :class="{ chosen: chosen === opt && !result, right: result && opt === result.original,
                         wrong: result && chosen === opt && opt !== result.original }"
               @click="choose(opt)">
            <span style="color:var(--accent)">{{ 'ABCD'[i] }}</span>&nbsp; {{ opt }}
          </div>
        </div>
        <div v-if="result" style="margin-top:18px">
          <el-alert :type="result.correct ? 'success' : 'error'" :closable="false"
            :title="result.correct ? '✓ 回答正确' : '✗ 回答错误'" />
          <p class="mono" style="color:#e6edf3">{{ result.original }}</p>
          <p style="color:var(--text-dim)">{{ result.translation }}</p>
          <el-button class="glow-btn" plain style="margin-top:10px" :loading="loading" @click="next">下一题</el-button>
        </div>
      </template>
      <el-empty v-else-if="emptyMsg" :description="emptyMsg" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'
import AudioPlayer from '../components/AudioPlayer.vue'
import { useSettingsStore } from '../stores/settings'

const store = useSettingsStore()
const difficulties = ref([])
const filter = reactive({ difficulty: null })
const current = ref(null)
const chosen = ref('')
const result = ref(null)
const loading = ref(false)
const emptyMsg = ref('')

onMounted(async () => {
  const { data } = await api.meta()
  difficulties.value = data.difficulties
  store.load()
})

async function next() {
  loading.value = true
  result.value = null
  chosen.value = ''
  try {
    const { data } = await api.nextQuiz({ difficulty: filter.difficulty || undefined })
    current.value = {
      quiz_id: data.quiz_id, options: data.options,
      sentenceId: Number(data.audio_url.split('/').pop()),
      difficulty: data.difficulty, topic: data.topic,
    }
  } catch (e) {
    if (e.response?.status === 404) emptyMsg.value = '知识库为空，请先到练习页生成句子'
    else ElMessage.error(e.response?.data?.detail || '抽题失败')
    if (!current.value) current.value = null
  } finally {
    loading.value = false
  }
}

async function choose(opt) {
  if (result.value || !current.value) return
  chosen.value = opt
  const { data } = await api.submitQuiz({ quiz_id: current.value.quiz_id, chosen_text: opt })
  result.value = data
}
</script>

<style scoped>
.option {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 16px;
  cursor: pointer;
  color: var(--text);
  transition: all .15s;
}
.option:hover { border-color: var(--accent); }
.option.right { border-color: var(--accent); background: rgba(0,255,156,.08); }
.option.wrong { border-color: #f56c6c; background: rgba(245,108,108,.08); }
</style>
