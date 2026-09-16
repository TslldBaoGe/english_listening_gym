<template>
  <div class="page">
    <div class="section-tag">// 04 · LIBRARY</div>
    <h2 style="color:#e6edf3;margin:0 0 20px">知识库</h2>

    <div class="card" style="margin-bottom:16px">
      <el-form inline>
        <el-form-item label="难度">
          <el-select v-model="q.difficulty" clearable placeholder="不限" style="width:140px">
            <el-option v-for="d in difficulties" :key="d.code" :label="d.code" :value="d.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="q.keyword" placeholder="搜索英文" style="width:200px" @keyup.enter="load" />
        </el-form-item>
        <el-form-item>
          <el-button class="glow-btn" plain @click="load">搜索</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card">
      <p class="mono" style="color:var(--text-dim)">共 {{ total }} 句</p>
      <div v-for="it in items" :key="it.id" style="padding:12px 0;border-bottom:1px solid var(--border)">
        <div class="mono" style="color:var(--accent-2);font-size:12px">
          {{ it.difficulty }} · {{ it.topic }} · 错{{ it.wrong_count }}/共{{ it.total_count }}
        </div>
        <p class="mono" style="color:#e6edf3;margin:6px 0">{{ it.text }}</p>
        <p style="color:var(--text-dim);margin:4px 0">{{ it.translation }}</p>
        <div style="display:flex;gap:10px">
          <AudioPlayer :sentence-id="it.id" :rate="1.0" />
          <el-button text type="danger" size="small" @click="del(it.id)">删除</el-button>
        </div>
      </div>
      <el-pagination v-if="total > q.size" layout="prev, pager, next" :total="total"
        :page-size="q.size" v-model:current-page="q.page" @current-change="load"
        style="margin-top:16px" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import AudioPlayer from '../components/AudioPlayer.vue'

const difficulties = ref([])
const items = ref([])
const total = ref(0)
const q = reactive({ page: 1, size: 20, difficulty: null, keyword: '' })

onMounted(async () => {
  difficulties.value = (await api.meta()).data.difficulties
  load()
})

async function load() {
  const { data } = await api.listSentences({
    page: q.page, size: q.size,
    difficulty: q.difficulty || undefined, keyword: q.keyword || undefined })
  items.value = data.items
  total.value = data.total
}

async function del(id) {
  await ElMessageBox.confirm('删除后无法恢复（含向量与音频）', '确认删除', { type: 'warning' })
  await api.deleteSentence(id)
  ElMessage.success('已删除')
  load()
}
</script>
