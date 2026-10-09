<template>
  <div class="page">
    <div class="section-tag">// 02 · QUIZ</div>
    <h1 class="hero-title">知识库抽考 · 听写辨句</h1>
    <p class="hero-sub mono">LIBRARY DRILL — <span class="hl-green">PLAY</span> · <span class="hl-cyan">TYPE</span> · <span class="hl-purple">CHECK</span><span class="cursor">▮</span></p>

    <div class="card" style="margin-bottom:20px">
      <el-form inline>
        <el-form-item label="难度">
          <el-select v-model="form.difficulty" v-touch-open placeholder="不限" style="width:170px">
            <el-option label="不限（全部难度）" :value="null" />
            <el-option v-for="d in difficulties" :key="d.code"
              :label="`${d.code} ${d.label}（雅思 ${d.ielts} / ${d.cefr}）`" :value="d.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="form.count" :min="1" :max="5" />
        </el-form-item>
        <el-form-item label="循环">
          <LoopPill :model-value="store.loop" @update:model-value="store.setLoop" />
        </el-form-item>
        <el-form-item>
          <SkyButton :loading="loading" :delay="0.4" @click="draw">抽取句子</SkyButton>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.includeMastered">包含已掌握的</el-checkbox>
        </el-form-item>
        <el-form-item>
          <SkyButton size="small" variant="ghost" @click="clearAll">清空重来</SkyButton>
        </el-form-item>
      </el-form>
      <div class="hint">
        玩法：点播放听句子 → 把你听到的句子打在下面的输入框里 → 回车提交。
        <span class="hl">完全正确</span>的句子会被标记「已掌握」，以后抽题默认不再出现。
      </div>
    </div>

    <el-empty v-if="!items.length && !loading" description="还没有抽取句子，点上面「抽取句子」从知识库抽一批" />

    <div v-for="s in items" :key="s.id" class="card" style="margin-bottom:16px">
      <div class="mono" style="color:var(--accent-2);font-size:12px;margin-bottom:8px">
        {{ s.difficulty }} · {{ s.topic }} · #{{ s.id }}
        <span v-if="results[s.id] && results[s.id].mastered" class="mastered-tag">已掌握</span>
      </div>

      <AudioPlayer :sentence-id="s.id" :rate="store.rate" :loop="store.loop"
                   @update:loop="store.setLoop" />

      <!-- 作答区 -->
      <div class="answer-row" style="margin-top:14px;display:flex;gap:8px">
        <el-input v-model="answers[s.id]" class="mono" style="flex:1"
                  placeholder="把你听到的句子打在这里，回车提交"
                  @keyup.enter="submit(s)" />
        <SkyButton :loading="checking === s.id" :delay="1.2" @click="submit(s)">提交</SkyButton>
      </div>
      <div class="hint">大小写和标点不影响判定，但要求逐词一致。</div>

      <!-- 判定结果 -->
      <div v-if="results[s.id]" class="reveal-area" style="margin-top:12px">
        <p v-if="results[s.id].correct" style="color:var(--accent);margin:0 0 8px">
          ✓ 完全正确 —— 已标记「已掌握」，下次抽题不会再出现
        </p>
        <!-- 答错：不给任何提示（不显示原文、相似度、错词、少几个词），自己再听一遍 -->
        <p v-else style="color:#f56c6c;margin:0 0 4px">✗ 不对，再听一遍试试</p>

        <!-- 原文/翻译：答对自动显示；答错要点「看答案」 -->
        <template v-if="results[s.id].correct || revealed[s.id]">
          <p class="mono" style="color:var(--text-strong);margin:10px 0 0">原文：{{ results[s.id].expected }}</p>
          <p style="color:var(--text-dim);margin:4px 0 0">{{ results[s.id].translation }}</p>
          <template v-if="!results[s.id].correct">
            <p class="mono" style="margin:6px 0 0;line-height:1.9">
              <span style="color:var(--text-dim)">你的输入：</span>
              <span v-for="(g, i) in results[s.id].segments" :key="i"
                    :style="{ color: g.status === 'ok' ? 'var(--accent)' : '#f56c6c' }">{{ g.v }} </span>
            </p>
            <p v-if="results[s.id].missing.length" class="mono" style="color:#e6a23c;margin:4px 0 0">
              漏掉：{{ results[s.id].missing.join(' ') }}</p>
            <p v-if="wrongDetail(s.id)" class="mono" style="color:var(--text-dim);margin:4px 0 0">
              写错：{{ wrongDetail(s.id) }}</p>
          </template>
        </template>
        <SkyButton v-else size="small" variant="primary" style="margin-top:6px"
                   @click="revealed[s.id] = true">看答案（放弃这次）</SkyButton>
      </div>

      <!-- 没作答时也可以直接看原文（等于放弃这次听写） -->
      <div v-else class="reveal-area" style="margin-top:12px">
        <SkyButton v-if="!revealed[s.id]" size="small" variant="ghost" :delay="0.8"
                   @click="revealed[s.id] = true">看原文 / 翻译（放弃这次）</SkyButton>
        <template v-else>
          <p class="mono" style="color:var(--text-strong);font-size:16px">{{ s.text }}</p>
          <p style="color:var(--text-dim)">{{ s.translation }}</p>
          <SkyButton size="small" variant="ghost" @click="revealed[s.id] = false">藏起来</SkyButton>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from '../utils/message'
import api from '../api'
import AudioPlayer from '../components/AudioPlayer.vue'
import LoopPill from '../components/LoopPill.vue'
import SkyButton from '../components/SkyButton.vue'
import { useSettingsStore } from '../stores/settings'
import { useViewState } from '../composables/useViewState'

const store = useSettingsStore()
// 首帧同步用缓存的难度配置，完整文案立刻可显示（后台再刷新）
const difficulties = ref((() => {
  try { return JSON.parse(localStorage.getItem('el-meta-cache'))?.difficulties || [] } catch { return [] }
})())
const form = reactive({ difficulty: null, count: 1, includeMastered: false })
const items = ref([])
const revealed = reactive({})
const answers = reactive({})   // sentence_id -> 用户输入
const results = reactive({})   // sentence_id -> 判定结果
const checking = ref(null)
const loading = ref(false)

// 切菜单 / 刷新后，抽到的句子、你打的内容、判定结果都还在
const viewState = useViewState('el-quiz-state-v1',
  () => ({ form: { ...form }, items: items.value, answers: { ...answers },
           results: { ...results }, revealed: { ...revealed } }),
  (saved) => {
    Object.assign(form, saved.form || {})
    if (Array.isArray(saved.items)) items.value = saved.items
    Object.assign(answers, saved.answers || {})
    Object.assign(results, saved.results || {})
    Object.assign(revealed, saved.revealed || {})
  })

// 首帧同步恢复：进入页面直接就是上次的内容，不会先显示默认值再跳变
viewState.restore()

onMounted(async () => {
  const meta = (await api.meta()).data
  difficulties.value = meta.difficulties
  try { localStorage.setItem('el-meta-cache', JSON.stringify(meta)) } catch (e) { /* 忽略 */ }
  await store.load()
})

function clearAll() {
  items.value = []
  Object.keys(answers).forEach(k => delete answers[k])
  Object.keys(results).forEach(k => delete results[k])
  Object.keys(revealed).forEach(k => delete revealed[k])
  viewState.clear()
  ElMessage.success('已清空，重新抽题吧')
}

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
.hint .hl { color: var(--accent); }
.reveal-area .sky-button { margin-top: 8px; }
</style>
