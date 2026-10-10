<template>
  <div class="page">
    <div class="section-tag">// 01 · PRACTICE</div>
    <h1 class="hero-title">生成新句子 · 练听力</h1>
    <p class="hero-sub mono">AI SPEECH TRAINER — <span class="hl-green">LISTEN</span> · <span class="hl-cyan">RECALL</span> · <span class="hl-purple">REPEAT</span><span class="cursor">▮</span></p>

    <div class="card" style="margin-bottom:20px">
      <el-form inline>
        <el-form-item label="难度">
          <el-select v-model="form.difficulty" v-touch-open style="width:200px">
            <el-option v-for="d in difficulties" :key="d.code"
              :label="`${d.code} ${d.label}（雅思 ${d.ielts} / ${d.cefr}）`" :value="d.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="主题">
          <div style="display:flex;gap:8px">
            <el-select v-touch-open v-model="form.topic" style="width:180px" placeholder="下拉选择一个主题">
              <el-option v-for="t in topicOptions" :key="t" :label="t" :value="t" />
            </el-select>
            <SkyButton size="small" variant="ghost" @click="addTopic">＋ 新增</SkyButton>
          </div>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="form.count" :min="1" :max="3" />
        </el-form-item>
        <el-form-item label="声音">
          <el-radio-group v-model="form.voice">
            <el-radio value="aria">Aria（女）</el-radio>
            <el-radio value="guy">Guy（男）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="循环">
          <LoopPill :model-value="store.loop" @update:model-value="store.setLoop" />
        </el-form-item>
        <el-form-item>
          <SkyButton :loading="generating" :delay="0.4" @click="generate">生成并朗读</SkyButton>
        </el-form-item>
        <el-form-item>
          <SkyButton size="small" variant="ghost" @click="clearAll">清空列表</SkyButton>
        </el-form-item>
      </el-form>
      <div class="hint" style="margin-top:-6px">
        难度 / 主题 / 声音 / 语速 取 05 设置里的默认值；主题只能从下拉里选，
        要加新主题点旁边的「＋ 新增」（主题列表与 05 设置共用）。
      </div>
    </div>

    <el-empty v-if="!items.length && !generating" description="还没有句子，先生成一批吧" />

    <div v-for="s in items" :key="s.id" class="card" style="margin-bottom:16px">
      <div class="mono" style="color:var(--accent-2);font-size:12px;margin-bottom:8px">
        {{ s.difficulty }} · {{ s.topic }} · #{{ s.id }}
      </div>
      <AudioPlayer :ref="el => setPlayerRef(s.id, el)" :sentence-id="s.id" :rate="store.rate"
                   :loop="store.loop" @update:loop="store.setLoop" />
      <div class="reveal-area" style="margin-top:14px">
        <SkyButton v-if="!revealed[s.id]" size="small" variant="primary" :delay="0.8"
                   @click="revealed[s.id] = true">显示原文 / 翻译</SkyButton>
        <template v-else>
          <p class="mono" style="color:var(--text-strong);font-size:16px">{{ s.text }}</p>
          <p style="color:var(--text-dim)">{{ s.translation }}</p>
          <SkyButton size="small" variant="ghost" @click="revealed[s.id] = false">隐藏原文 / 翻译</SkyButton>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from '../utils/message'
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
const form = reactive({ difficulty: 'L1', topic: 'daily life', count: 1, voice: 'aria' })
const items = ref([])
const revealed = reactive({})
const generating = ref(false)

// 记住上次的一切：难度/主题/声音/数量/已生成的句子/展开状态。
// 05 设置里的默认值只在第一次访问（还没有历史记录）时生效。
const viewState = useViewState('el-practice-state-v1',
  () => ({ count: form.count, difficulty: form.difficulty, topic: form.topic,
           voice: form.voice, items: items.value, revealed: { ...revealed } }),
  (saved) => {
    if (saved.difficulty) form.difficulty = saved.difficulty
    if (saved.topic) form.topic = saved.topic
    if (saved.voice) form.voice = saved.voice
    if (saved.count) form.count = saved.count
    if (Array.isArray(saved.items)) items.value = saved.items
    Object.assign(revealed, saved.revealed || {})
  })

// 关键：在首次渲染前就同步恢复，页面上不会先闪一下默认值再跳变
const hasHistory = viewState.restore()

onMounted(async () => {
  const { data } = await api.meta()
  difficulties.value = data.difficulties
  try { localStorage.setItem('el-meta-cache', JSON.stringify(data)) } catch (e) { /* 忽略 */ }
  await store.load()
  // 没有历史记录（第一次用）才用设置页的默认值
  if (!hasHistory) {
    Object.assign(form, { difficulty: store.difficulty, topic: store.topic, voice: store.voice })
  }
})

function clearAll() {
  items.value = []
  Object.keys(revealed).forEach(k => delete revealed[k])
  viewState.clear()
  ElMessage.success('列表已清空（知识库里的句子不受影响）')
}

// 主题下拉：和 05 设置共用同一份列表；当前值不在列表里也要能显示
const topicOptions = computed(() => {
  const list = [...(store.topics || [])]
  if (form.topic && !list.includes(form.topic)) list.unshift(form.topic)
  return list
})

/** 新增主题：和 05 设置走同一份数据，加完立刻选中 */
async function addTopic() {
  let value = ''
  try {
    const { value: input } = await ElMessageBox.prompt(
      '新主题名称（英文更贴合提示词，例如 job interview）', '新增主题',
      { confirmButtonText: '新增', cancelButtonText: '取消', inputPlaceholder: 'job interview' })
    value = (input || '').trim()
  } catch { return }   // 取消
  if (!value) return ElMessage.warning('主题名不能为空')
  if ((store.topics || []).includes(value)) {
    form.topic = value
    return ElMessage.info('这个主题已经有了，已帮你选中')
  }
  await store.save({ topics: [...(store.topics || []), value] })
  form.topic = value
  ElMessage.success(`已新增主题「${value}」`)
}

async function generate() {
  generating.value = true
  try {
    // 老数据里可能留着不在列表中的主题，顺手记进去（失败不影响生成）
    try { await store.rememberTopic(form.topic) } catch (e) { /* 忽略 */ }
    const { data } = await api.generate(form)
    items.value = [...data.sentences, ...items.value]
    data.sentences.forEach(s => (revealed[s.id] = false))
    ElMessage.success(`已生成 ${data.sentences.length} 句并入库`)
    // 按钮是「生成并朗读」：生成完直接把第一句念出来
    autoplayFirst(data.sentences[0]?.id)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '生成失败，请重试')
  } finally {
    generating.value = false
  }
}

// 卡片里的播放器实例，按句子 id 存起来，方便生成后自动播放
const playerRefs = new Map()
function setPlayerRef(id, el) {
  if (el) playerRefs.set(id, el)
  else playerRefs.delete(id)
}

/** 等新卡片渲染出来后，播放指定句子（浏览器若拦截，播放器会自己给出再点一次的提示） */
async function autoplayFirst(id) {
  if (!id) return
  await nextTick()
  playerRefs.get(id)?.play()
}
</script>
