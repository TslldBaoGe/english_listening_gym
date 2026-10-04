<template>
  <div class="page">
    <div class="section-tag">// 05 · SETTINGS</div>
    <h2 style="color:#e6edf3;margin:0 0 20px">设置</h2>

    <!-- 模型服务配置 -->
    <div class="card" style="max-width:680px;margin-bottom:20px">
      <div class="section-tag">模型服务（OpenAI 兼容 / v1/chat/completions）</div>

      <!-- 已保存的模型配置：可命名、可切换、可删除 -->
      <div v-if="configs.length" class="cfg-list">
        <div v-for="c in configs" :key="c.id" class="cfg-row" :class="{ on: c.id === activeId }">
          <div class="cfg-info">
            <div class="cfg-name">
              {{ c.name }}
              <el-tag v-if="c.id === activeId" size="small" type="primary" effect="dark">当前使用</el-tag>
              <el-tag v-if="c.no_proxy" size="small" type="info" effect="plain">直连</el-tag>
            </div>
            <div class="cfg-sub mono">{{ c.model || '未填模型' }} · {{ c.base_url || '未填 Base URL' }}</div>
          </div>
          <div class="cfg-ops">
            <el-button size="small" plain @click="editConfig(c)">编辑</el-button>
            <el-button v-if="c.id !== activeId" size="small" plain
                       style="color:var(--accent);border-color:var(--accent)"
                       @click="activateConfig(c)">设为当前</el-button>
            <el-button size="small" plain type="danger" @click="removeConfig(c)">删除</el-button>
          </div>
        </div>
      </div>
      <div v-else class="cfg-empty mono">还没有配置，填下面的表单保存一条即可</div>

      <el-form label-width="110px" style="margin-top:14px">
        <el-form-item label="名称">
          <el-input v-model="llm.name" class="mono" placeholder="自己起名，例如：我的中转 / 智谱GLM" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="llm.provider" style="width:100%">
            <el-option v-for="(p, key) in providers" :key="key"
              :label="p.label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="llm.base_url" class="mono"
                    placeholder="https://.../v1" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="llm.api_key" class="mono" show-password
                    placeholder="sk-..." />
        </el-form-item>
        <el-form-item label="模型">
          <div style="display:flex;gap:8px;width:100%">
            <el-select v-if="modelList.length" v-model="llm.model" filterable allow-create
                       class="mono" style="flex:1" placeholder="选择或输入模型">
              <el-option v-for="m in modelList" :key="m" :label="m" :value="m" class="mono" />
            </el-select>
            <el-input v-else v-model="llm.model" class="mono" style="flex:1"
                      placeholder="glm-4-flash / gpt-4o-mini ... 或点击右侧获取" />
            <el-button plain :loading="fetchingModels" style="color:var(--accent-2);border-color:var(--accent-2)"
                       @click="fetchModels">获取模型</el-button>
          </div>
        </el-form-item>
        <el-form-item label="网络">
          <el-checkbox v-model="llm.no_proxy">不使用系统代理（直连）</el-checkbox>
          <div class="cfg-hint">开着代理软件时，有些中转会拒绝代理出口 IP 并返回 403 拦截页，勾上这个可绕过；被拦截时程序也会自动直连重试一次。</div>
        </el-form-item>
        <el-form-item>
          <el-button class="glow-btn" type="primary" plain :loading="saving" @click="saveLlm">
            {{ llm.id ? '保存修改' : '新增配置' }}</el-button>
          <el-button plain :loading="testing" style="color:var(--accent-2);border-color:var(--accent-2)"
                     @click="testLlm">测试连接</el-button>
          <el-button v-if="llm.id" plain @click="resetForm">取消编辑</el-button>
          <span v-if="testMsg" :style="{color: testOk ? 'var(--accent)' : '#f56c6c', marginLeft:'10px', fontSize:'13px'}">
            {{ testMsg }}</span>
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" title="配置保存在本地数据库，仅本机使用"
                description="类型只保留「自定义（OpenAI 兼容）」：Base URL、API Key、模型名都由你填写；可保存多条、随时切换或删除。" />
    </div>

    <!-- 练习默认参数 -->
    <div class="card" style="max-width:560px">
      <div class="section-tag">练习默认参数</div>
      <el-form label-width="110px">
        <el-form-item label="默认难度">
          <el-select v-model="form.difficulty">
            <el-option v-for="d in difficulties" :key="d.code"
              :label="`${d.code} ${d.label}（雅思 ${d.ielts}）`" :value="d.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="默认主题">
          <el-input v-model="form.topic" />
        </el-form-item>
        <el-form-item label="默认声音">
          <el-radio-group v-model="form.voice">
            <el-radio value="aria">Aria（女）</el-radio>
            <el-radio value="guy">Guy（男）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="默认语速">
          <el-radio-group v-model="form.rate">
            <el-radio-button v-for="r in [1.0, 0.85, 0.75, 0.5]" :key="r" :value="r"
                             class="mono">{{ r }}x</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <el-button class="glow-btn" type="primary" plain @click="saveDefaults">保存</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import { useSettingsStore } from '../stores/settings'

const store = useSettingsStore()
const difficulties = ref([])
const providers = ref({})
const configs = ref([])
const activeId = ref('')
const form = reactive({ difficulty: 'L1', topic: 'daily life', voice: 'aria', rate: 1.0 })
const llm = reactive({ id: '', name: '', provider: 'custom', base_url: '', api_key: '',
                       model: '', no_proxy: false })
const saving = ref(false)
const testing = ref(false)
const testMsg = ref('')
const testOk = ref(false)
const modelList = ref([])
const fetchingModels = ref(false)

onMounted(async () => {
  difficulties.value = (await api.meta()).data.difficulties
  providers.value = (await api.get('/settings/llm/providers')).data
  await store.load()
  Object.assign(form, { difficulty: store.difficulty, topic: store.topic,
                        voice: store.voice, rate: store.rate })
  await loadConfigs()
})

async function loadConfigs() {
  const { data } = await api.get('/settings/llm/configs')
  configs.value = data.items
  activeId.value = data.active_id
}

function resetForm() {
  Object.assign(llm, { id: '', name: '', provider: 'custom',
                       base_url: '', api_key: '', model: '', no_proxy: false })
  modelList.value = []
  testMsg.value = ''
}

function editConfig(c) {
  Object.assign(llm, { id: c.id, name: c.name, provider: 'custom',
                       base_url: c.base_url, api_key: c.api_key, model: c.model,
                       no_proxy: !!c.no_proxy })
  modelList.value = []   // 换配置后旧模型列表失效
  testMsg.value = ''
}

async function saveLlm() {
  if (!llm.name.trim()) return ElMessage.warning('请先给这条配置起个名称')
  if (!llm.base_url.trim()) return ElMessage.warning('请填写 Base URL')
  saving.value = true
  try {
    const { data } = await api.post('/settings/llm/configs', {
      id: llm.id || undefined, name: llm.name, base_url: llm.base_url,
      api_key: llm.api_key, model: llm.model, no_proxy: llm.no_proxy,
      make_active: true,
    })
    configs.value = data.items
    activeId.value = data.active_id
    const saved = data.items.find(i => i.id === data.focus_id)
    if (saved) editConfig(saved)   // 回填脱敏后的 key，便于继续测试
    ElMessage.success(`「${saved ? saved.name : llm.name}」已保存并设为当前使用`)
  } catch (e) {
    ElMessage.error(netErr(e, '保存失败'))
  } finally { saving.value = false }
}

async function activateConfig(c) {
  const { data } = await api.post(`/settings/llm/configs/${c.id}/activate`)
  configs.value = data.items
  activeId.value = data.active_id
  ElMessage.success(`已切换为「${c.name}」`)
}

async function removeConfig(c) {
  try {
    await ElMessageBox.confirm(`确定删除配置「${c.name}」？删除后无法恢复。`, '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }   // 用户取消
  const { data } = await api.delete(`/settings/llm/configs/${c.id}`)
  configs.value = data.items
  activeId.value = data.active_id
  if (llm.id === c.id) resetForm()
  ElMessage.success('已删除')
}

function netErr(e, fallback) {
  if (!e.response) return '无法连接后端服务，请确认后端已启动（8000 端口）'
  return e.response?.data?.detail || fallback
}

async function testLlm() {
  testing.value = true
  testMsg.value = ''
  try {
    const { data } = await api.post('/settings/llm/test', llm)
    testOk.value = data.ok
    testMsg.value = data.msg
  } catch (e) {
    testOk.value = false
    testMsg.value = netErr(e, '请求失败')
  } finally { testing.value = false }
}

async function fetchModels() {
  fetchingModels.value = true
  try {
    const { data } = await api.post('/settings/llm/models', llm)
    if (data.ok) {
      modelList.value = data.models
      ElMessage.success(data.msg)
      if (data.models.length && !data.models.includes(llm.model)) llm.model = data.models[0]
    } else {
      ElMessage.error(data.msg)
    }
  } catch (e) {
    ElMessage.error(netErr(e, '获取模型失败'))
  } finally { fetchingModels.value = false }
}

async function saveDefaults() {
  await api.putSettings(form)
  await store.load()
  ElMessage.success('已保存')
}
</script>

<style scoped>
.cfg-list { display: flex; flex-direction: column; gap: 8px; }
.cfg-row {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px; border-radius: 10px;
  border: 1px solid var(--border); background: rgba(148, 163, 184, .04);
  transition: border-color .2s, background .2s;
}
.cfg-row.on { border-color: rgba(56, 189, 248, .45); background: rgba(56, 189, 248, .07); }
.cfg-info { flex: 1; min-width: 0; }
.cfg-name { display: flex; align-items: center; gap: 8px; color: #e6edf3; font-size: 14px; }
.cfg-sub {
  margin-top: 2px; font-size: 12px; color: var(--text-dim);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.cfg-ops { display: flex; gap: 6px; flex-shrink: 0; }
.cfg-empty { color: var(--text-dim); font-size: 13px; padding: 6px 0 0; }
.cfg-hint { color: var(--text-dim); font-size: 12px; line-height: 1.6; margin-top: 2px; }
@media (max-width: 720px) {
  .cfg-row { flex-direction: column; align-items: stretch; }
  .cfg-ops { justify-content: flex-end; }
}
</style>
