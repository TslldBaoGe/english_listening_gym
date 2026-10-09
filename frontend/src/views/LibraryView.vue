<template>
  <div class="page">
    <div class="section-tag">// 04 · LIBRARY</div>
    <h2 style="color:var(--text-strong);margin:0 0 20px">知识库</h2>

    <div class="card" style="margin-bottom:16px">
      <el-form inline>
        <el-form-item label="难度">
          <el-select v-model="q.difficulty" v-touch-open placeholder="不限" style="width:150px"
                     @change="search">
            <el-option label="不限（全部难度）" :value="null" />
            <el-option v-for="d in difficulties" :key="d.code"
              :label="`${d.code} ${d.label}`" :value="d.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="主题">
          <el-select v-touch-open v-model="q.topic" clearable placeholder="不限"
                     style="width:150px" @change="search">
            <el-option v-for="t in topicOptions" :key="t.topic"
                       :label="`${t.topic}（${t.count}）`" :value="t.topic" />
          </el-select>
        </el-form-item>
        <el-form-item label="掌握情况">
          <el-select v-touch-open v-model="q.mastered" clearable placeholder="不限" style="width:110px"
                     @change="search">
            <el-option label="已掌握" :value="true" />
            <el-option label="未掌握" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="q.keyword" placeholder="搜索英文" style="width:180px" @keyup.enter="search" />
        </el-form-item>
        <el-form-item>
          <SkyButton size="small" variant="primary" :delay="0.3" @click="search">搜索</SkyButton>
        </el-form-item>
      </el-form>
    </div>

    <div class="card">
      <p class="mono" style="color:var(--text-dim)">共 {{ total }} 句</p>
      <div v-for="it in items" :key="it.id" style="padding:12px 0;border-bottom:1px solid var(--border)">
        <div class="mono" style="color:var(--accent-2);font-size:12px">
          {{ it.difficulty }} · {{ it.topic }} · 错{{ it.wrong_count }}/共{{ it.total_count }}
          <span v-if="it.mastered" class="mastered-tag">已掌握</span>
        </div>
        <p class="mono" style="color:var(--text-strong);margin:6px 0">{{ it.text }}</p>
        <p style="color:var(--text-dim);margin:4px 0">{{ it.translation }}</p>
        <div style="display:flex;gap:10px;align-items:center">
          <AudioPlayer :sentence-id="it.id" :rate="1.0" />
          <SkyButton v-if="it.mastered" size="small" variant="ghost" :delay="0.6"
                     @click="setMastered(it, false)">重新加入测验</SkyButton>
          <SkyButton v-else size="small" variant="ghost" :delay="0.6"
                     @click="setMastered(it, true)">标记已掌握</SkyButton>
          <SkyButton size="small" variant="danger" @click="del(it.id)">删除</SkyButton>
        </div>
      </div>
      <el-pagination v-if="total > q.size" layout="prev, pager, next" :total="total"
        :page-size="q.size" v-model:current-page="q.page" @current-change="load"
        style="margin-top:16px" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from '../utils/message'
import api from '../api'
import AudioPlayer from '../components/AudioPlayer.vue'
import SkyButton from '../components/SkyButton.vue'
import { useViewState } from '../composables/useViewState'

// 首帧同步用缓存的难度配置，完整文案立刻可显示（后台再刷新）
const difficulties = ref((() => {
  try { return JSON.parse(localStorage.getItem('el-meta-cache'))?.difficulties || [] } catch { return [] }
})())
const items = ref([])
const total = ref(0)
const topicList = ref([])      // 知识库里实际有的主题 + 句数
const q = reactive({ page: 1, size: 20, difficulty: null, topic: null,
                     keyword: '', mastered: '' })

// 主题下拉：用知识库里真实存在的主题（都带句数）；当前筛选项若不在其中也补上
const topicOptions = computed(() => {
  const list = [...topicList.value]
  if (q.topic && !list.some(t => t.topic === q.topic)) list.unshift({ topic: q.topic, count: 0 })
  return list
})

// 筛选条件也记住：切菜单/刷新后回来还是刚才的筛选和页码
const viewState = useViewState('el-library-query-v1',
  () => ({ ...q }),
  (saved) => { Object.assign(q, saved) })

onMounted(async () => {
  const meta = (await api.meta()).data
  difficulties.value = meta.difficulties
  try { localStorage.setItem('el-meta-cache', JSON.stringify(meta)) } catch (e) { /* 忽略 */ }
  viewState.restore()
  load()
})

/** 换筛选条件时回到第 1 页，避免停在空页上 */
function search() {
  q.page = 1
  load()
}

/** 「不限」时把参数去掉（clearable 清空后可能是 '' 或 undefined） */
function masteredParam() {
  return (q.mastered === true || q.mastered === false) ? q.mastered : undefined
}

async function load() {
  const [{ data }, topics] = await Promise.all([
    api.listSentences({
      page: q.page, size: q.size,
      difficulty: q.difficulty || undefined, topic: q.topic || undefined,
      keyword: q.keyword || undefined, mastered: masteredParam() }),
    api.sentenceTopics(),
  ])
  items.value = data.items
  total.value = data.total
  topicList.value = topics.data.items
}

async function del(id) {
  await ElMessageBox.confirm('删除后无法恢复（含向量与音频）', '确认删除', { type: 'warning' })
  await api.deleteSentence(id)
  ElMessage.success('已删除')
  load()
}

async function setMastered(it, mastered) {
  await api.setMastered(it.id, mastered)
  it.mastered = mastered
  ElMessage.success(mastered ? '已标记为掌握，测验不再抽到它' : '已重新加入测验')
  // 正在按掌握情况筛选时重新拉一次，行会随之移出/移入列表
  if (masteredParam() !== undefined) load()
}
</script>
