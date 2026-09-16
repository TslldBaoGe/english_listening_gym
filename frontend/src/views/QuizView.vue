<template>
  <div class="page">
    <div class="section-tag">// 02 · QUIZ</div>
    <h1 class="hero-title">知识库抽考 · 听音辨句</h1>
    <p class="hero-sub mono">LIBRARY DRILL — <span class="hl-green">PLAY</span> · <span class="hl-cyan">RECALL</span> · <span class="hl-purple">CHECK</span><span class="cursor">▮</span></p>

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
      </el-form>
    </div>

    <el-empty v-if="!items.length && !loading" description="还没有抽取句子，点上面「抽取句子」从知识库抽一批" />

    <div v-for="s in items" :key="s.id" class="card" style="margin-bottom:16px">
      <div class="mono" style="color:var(--accent-2);font-size:12px;margin-bottom:8px">
        {{ s.difficulty }} · {{ s.topic }} · #{{ s.id }}
      </div>
      <AudioPlayer :sentence-id="s.id" :rate="store.rate" />
      <div style="margin-top:14px">
        <el-button v-if="!revealed[s.id]" size="small" text style="color:var(--accent)"
                   @click="revealed[s.id] = true">显示原文 / 翻译</el-button>
        <template v-else>
          <p class="mono" style="color:#e6edf3;font-size:16px">{{ s.text }}</p>
          <p style="color:var(--text-dim)">{{ s.translation }}</p>
          <el-button size="small" text style="color:var(--text-dim)"
                     @click="revealed[s.id] = false">隐藏原文 / 翻译</el-button>
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
const form = reactive({ difficulty: null, count: 1 })
const items = ref([])
const revealed = reactive({})
const loading = ref(false)

onMounted(async () => {
  difficulties.value = (await api.meta()).data.difficulties
  await store.load()
})

// 从知识库随机抽 count 条（/sentences/random，直接返回原文与翻译）
async function draw() {
  loading.value = true
  try {
    const { data } = await api.randomSentences({
      count: form.count,
      difficulty: form.difficulty || undefined,
    })
    const seen = new Set(items.value.map(s => s.id))
    const fresh = data.sentences.filter(s => !seen.has(s.id) && seen.add(s.id))
    items.value = [...fresh, ...items.value]
    fresh.forEach(s => (revealed[s.id] = false))
    if (!fresh.length) ElMessage.warning('抽到的都是已展示的句子，再试一次')
    else ElMessage.success(`已抽取 ${fresh.length} 句`)
  } catch (e) {
    if (e.response?.status === 404) ElMessage.warning('知识库为空，请先到练习页生成句子')
    else ElMessage.error(e.response?.data?.detail || '抽题失败')
  } finally {
    loading.value = false
  }
}
</script>
