<template>
  <div class="page">
    <div class="section-tag">// 05 · SETTINGS</div>
    <h2 style="color:#e6edf3;margin:0 0 20px">设置</h2>

    <!-- 模型服务配置 -->
    <div class="card" style="max-width:560px;margin-bottom:20px">
      <div class="section-tag">模型服务（OpenAI 兼容 / v1/chat/completions）</div>
      <el-form label-width="110px">
        <el-form-item label="服务商">
          <el-select v-model="llm.provider" @change="onProviderChange" style="width:100%">
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
            <el-select v-if="modelList.length" v-model="llm.model" filterable
                       class="mono" style="flex:1" placeholder="选择模型">
              <el-option v-for="m in modelList" :key="m" :label="m" :value="m" class="mono" />
            </el-select>
            <el-input v-else v-model="llm.model" class="mono" style="flex:1"
                      placeholder="glm-4-flash / gpt-4o-mini ... 或点击右侧获取" />
            <el-button plain :loading="fetchingModels" style="color:var(--accent-2);border-color:var(--accent-2)"
                       @click="fetchModels">获取模型</el-button>
          </div>
        </el-form-item>
        <el-form-item>
          <el-button class="glow-btn" type="primary" plain :loading="saving" @click="saveLlm">保存配置</el-button>
          <el-button plain :loading="testing" style="color:var(--accent-2);border-color:var(--accent-2)"
                     @click="testLlm">测试连接</el-button>
          <span v-if="testMsg" :style="{color: testOk ? 'var(--accent)' : '#f56c6c', marginLeft:'10px', fontSize:'13px'}">
            {{ testMsg }}</span>
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" title="配置保存在本地数据库，仅本机使用"
                description="支持任何 OpenAI 兼容协议的服务：智谱、OpenAI、DeepSeek、Anthropic 兼容网关、自建中转等。" />
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
import { ElMessage } from 'element-plus'
import api from '../api'
import { useSettingsStore } from '../stores/settings'

const store = useSettingsStore()
const difficulties = ref([])
const providers = ref({})
const form = reactive({ difficulty: 'L1', topic: 'daily life', voice: 'aria', rate: 1.0 })
const llm = reactive({ provider: 'zhipu', base_url: '', api_key: '', model: '' })
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
  const { data } = await api.getSettings()
  llm.provider = data.llm_provider || 'zhipu'
  llm.base_url = data.llm_base_url || ''
  llm.api_key = data.llm_api_key || ''
  llm.model = data.llm_model || ''
})

function onProviderChange(key) {
  const p = providers.value[key]
  if (p) { llm.base_url = p.base_url; llm.model = p.model }
  modelList.value = []  // 切换服务商后旧模型列表失效
}

async function saveLlm() {
  saving.value = true
  try {
    await api.putSettings({ llm_provider: llm.provider, llm_base_url: llm.base_url,
                            llm_api_key: llm.api_key, llm_model: llm.model })
    ElMessage.success('模型配置已保存')
  } finally { saving.value = false }
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
