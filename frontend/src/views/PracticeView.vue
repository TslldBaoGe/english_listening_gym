<template>
  <div class="page">
    <div class="section-tag">// 01 · PRACTICE</div>
    <h1 class="hero-title">生成新句子 · 练听力</h1>
    <p class="hero-sub mono">AI SPEECH TRAINER — <span class="hl-green">LISTEN</span> · <span class="hl-cyan">RECALL</span> · <span class="hl-purple">REPEAT</span><span class="cursor">▮</span></p>

    <div class="card" style="margin-bottom:20px">
      <el-form inline>
        <el-form-item label="难度">
          <el-select v-model="form.difficulty" style="width:200px">
            <el-option v-for="d in difficulties" :key="d.code"
              :label="`${d.code} ${d.label}（雅思 ${d.ielts} / ${d.cefr}）`" :value="d.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="主题">
          <el-input v-model="form.topic" placeholder="如 travel / campus / tech" style="width:200px" />
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
        <el-form-item>
          <el-button class="glow-btn" type="primary" plain :loading="generating"
                     @click="generate">生成并朗读</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-empty v-if="!items.length && !generating" description="还没有句子，先生成一批吧" />

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
const form = reactive({ difficulty: 'L1', topic: 'daily life', count: 1, voice: 'aria' })
const items = ref([])
const revealed = reactive({})
const generating = ref(false)

onMounted(async () => {
  const { data } = await api.meta()
  difficulties.value = data.difficulties
  await store.load()
  Object.assign(form, { difficulty: store.difficulty, topic: store.topic, voice: store.voice })
})

async function generate() {
  generating.value = true
  try {
    const { data } = await api.generate(form)
    items.value = [...data.sentences, ...items.value]
    data.sentences.forEach(s => (revealed[s.id] = false))
    ElMessage.success(`已生成 ${data.sentences.length} 句并入库`)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '生成失败，请重试')
  } finally {
    generating.value = false
  }
}
</script>
