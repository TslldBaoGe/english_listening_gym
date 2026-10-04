<template>
  <div class="page">
    <div class="section-tag">// 02 · QUIZ</div>
    <h1 class="hero-title">知识库抽考 · 听写辨句</h1>
    <p class="hero-sub mono">LIBRARY DRILL — <span class="hl-green">PLAY</span> · <span class="hl-cyan">TYPE</span> · <span class="hl-purple">CHECK</span><span class="cursor">▮</span></p>

    <div class="card" style="margin-bottom:20px">
      <el-form inline>
        <el-form-item label="难度">
          <el-select v-model="form.difficulty" clearable placeholder="不限" style="width:160px">
            <el-option v-for="d in difficulties" :key="d.code" :label="d.code + ' ' + d.label" :value="d.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="form.count" :min="1" :max="5" />
        </el-form-item>
        <el-form-item>
          <el-button class="glow-btn" type="primary" plain :loading="loading" @click="draw">抽取句子</el-button>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.includeMastered">包含已掌握的</el-checkbox>
        </el-form-item>
      </el-form>
      <div class="hint">
        玩法：点播放听句子 → 把你听到的句子打在下面的输入框里 → 回车提交。
        <b>完全正确</b>的句子会被标记「已掌握」，以后抽题默认不再出现。
      </div>
    </div>

    <el-empty v-if="!items.length && !loading" description="还没有抽取句子，点上面「抽取句子」从知识库抽一批" />

    <div v-for="s in items" :key="s.id" class="card" style="margin-bottom:16px">
      <div class="mono" style="color:var(--accent-2);font-size:12px;margin-bottom:8px">
        {{ s.difficulty }} · {{ s.topic }} · #{{ s.id }}
        <el-tag v-if="results[s.id] && results[s.id].mastered" size="small"
                type="success" effect="dark" style="margin-left:8px">已掌握</el-tag>
      </div>

      <AudioPlayer :sentence-id="s.id" :rate="store.rate" />

      <!-- 作答区 -->
      <div style="margin-top:14px;display:flex;gap:8px">
        <el-input v-model="answers[s.id]" class="mono" style="flex:1"
                  placeholder="把你听到的句子打在这里，回车提交"
                  @keyup.enter="submit(s)" />
        <el-button class="glow-btn" type="primary" plain :loading="checking === s.id"
                   @click="submit(s)">提交</el-button>
      </div>
      <div class="hint">大小写和标点不影响判定，但要求逐词一致。</div>

      <!-- 判定结果 -->
      <div v-if="results[s.id]" style="margin-top:12px">
        <p v-if="results[s.id].correct" style="color:var(--accent);margin:0 0 8px">
          ✓ 完全正确 —— 已标记「已掌握」，下次抽题不会再出现
        </p>
        <p v-else style="color:#f56c6c;margin:0 0 8px">
          ✗ 和原文有出入（相似度 {{ Math.round(results[s.id].similarity * 100) }}%），再听一遍改改看
        </p>

        <!-- 错在哪：只标你自己写的词，绝不显示原文 -->
        <template v-if="!results[s.id].correct">
          <p class="mono" style="margin:0 0 6px;line-height:1.9">
            <span style="color:var(--text-dim)">你的输入：</span>
            <span v-for="(g, i) in results[s.id].segments" :key="i"
                  :style="{ color: g.status === 'ok' ? 'var(--accent)' : '#f56c6c' }">{{ g.v }} </span>
          </p>
          <p class="hint" style="margin:0">
            <span style="color:#f56c6c">红色</span>标出来的词不对<template
              v-if="results[s.id].missing.length">；另外少了 {{ results[s.id].missing.length }} 个词</template>。
            <template v-if="!revealed[s.id]">（答案先不给你，自己再听一遍 🙂）</template>
          </p>
        </template>

        <!-- 原文/翻译：答对自动显示；答错要点「看答案」 -->
        <template v-if="results[s.id].correct || revealed[s.id]">
          <p class="mono" style="color:#e6edf3;margin:10px 0 0">原文：{{ results[s.id].expected }}</p>
          <p style="color:var(--text-dim);margin:4px 0 0">{{ results[s.id].translation }}</p>
          <template v-if="!results[s.id].correct">
            <p v-if="results[s.id].missing.length" class="mono" style="color:#e6a23c;margin:6px 0 0">
              漏掉：{{ results[s.id].missing.join(' ') }}</p>
            <p v-if="wrongDetail(s.id)" class="mono" style="color:var(--text-dim);margin:4px 0 0">
              写错：{{ wrongDetail(s.id) }}</p>
          </template>
        </template>
        <el-button v-else size="small" text style="color:var(--accent);padding-left:0;margin-top:4px"
                   @click="revealed[s.id] = true">看答案（放弃这次）</el-button>
      </div>

      <!-- 没作答时也可以直接看原文（等于放弃这次听写） -->
      <div v-else style="margin-top:12px">
        <el-button v-if="!revealed[s.id]" size="small" text style="color:var(--text-dim)"
                   @click="revealed[s.id] = true">看原文 / 翻译（放弃这次）</el-button>
        <template v-else>
          <p class="mono" style="color:#e6edf3;font-size:16px">{{ s.text }}</p>
          <p style="color:var(--text-dim)">{{ s.translation }}</p>
          <el-button size="small" text style="color:var(--text-dim)"
                     @click="revealed[s.id] = false">藏起来</el-button>
        </template>
      </div>
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
const form = reactive({ difficulty: null, count: 1, includeMastered: false })
const items = ref([])
const revealed = reactive({})
const answers = reactive({})   // sentence_id -> 用户输入
const results = reactive({})   // sentence_id -> 判定结果
const checking = ref(null)
const loading = ref(false)

onMounted(async () => {
  difficulties.value = (await api.meta()).data.difficulties
  await store.load()
})

// 从知识库随机抽 count 条（默认跳过已掌握的）
async function draw() {
  loading.value = true
  try {
    const { data } = await api.randomSentences({
      count: form.count,
      difficulty: form.difficulty || undefined,
      include_mastered: form.includeMastered,
    })
    const seen = new Set(items.value.map(s => s.id))
    const fresh = data.sentences.filter(s => !seen.has(s.id) && seen.add(s.id))
    items.value = [...fresh, ...items.value]
    fresh.forEach(s => { revealed[s.id] = false })
    if (!fresh.length) ElMessage.warning('抽到的都是已展示的句子，再试一次')
    else ElMessage.success(`已抽取 ${fresh.length} 句`)
  } catch (e) {
    if (e.response?.status === 404) ElMessage.warning(e.response.data.detail)
    else ElMessage.error(e.response?.data?.detail || '抽题失败')
  } finally {
    loading.value = false
  }
}

async function submit(s) {
  const text = (answers[s.id] || '').trim()
  if (!text) return ElMessage.warning('先把你听到的句子打进来')
  checking.value = s.id
  try {
    const { data } = await api.checkAnswer({ sentence_id: s.id, text })
    results[s.id] = data
    if (data.correct) {
      revealed[s.id] = true          // 答对了才把原文亮出来
      ElMessage.success('完全正确，已掌握 ✅')
    }
    // 答错时不动 revealed：默认不显示原文，避免直接看到答案
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '判定失败，请重试')
  } finally {
    checking.value = null
  }
}

// 看答案时才列出来（默认不显示，否则等于给答案）
function wrongDetail(id) {
  const segs = (results[id] && results[id].segments) || []
  return segs.filter(g => g.status === 'bad')
    .map(g => (g.want ? `${g.v} → ${g.want}` : `${g.v}（多余）`))
    .join('，')
}
</script>

<style scoped>
.hint { color: var(--text-dim); font-size: 12px; line-height: 1.7; margin-top: 6px; }
.hint b { color: #e6edf3; }
</style>
