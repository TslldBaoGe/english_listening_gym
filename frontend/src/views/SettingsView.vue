<template>
  <div class="page">
    <div class="section-tag">// 05 · SETTINGS</div>
    <h2 style="color:#e6edf3;margin:0 0 20px">设置</h2>

    <!-- 模型服务配置 -->
    <div class="card" style="max-width:680px;margin-bottom:20px">
      <div class="section-tag">模型服务（OpenAI 兼容 / v1/chat/completions）</div>

      <!-- 模型配置：下拉框选择 + 新增 -->
      <el-form label-width="110px">
        <el-form-item label="模型配置">
          <div style="display:flex;gap:8px;width:100%">
            <el-select v-model="pickedId" style="flex:1" placeholder="下拉选择一个配置"
                       @change="onPick">
              <el-option v-for="c in configs" :key="c.id" :value="c.id"
                         :label="c.name + (c.id === activeId ? '　·　当前使用' : '')" />
            </el-select>
            <el-button plain style="color:var(--accent);border-color:var(--accent)"
                       @click="newConfig">＋ 新增</el-button>
            <el-button v-if="pickedId" plain type="danger" @click="removeConfig">删除</el-button>
          </div>
        </el-form-item>

        <template v-if="editing">
          <el-form-item label="名称">
            <el-input v-model="llm.name" class="mono" placeholder="自己起名，例如：我的中转 / DeepSeek" />
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="llm.provider" style="width:100%">
              <el-option v-for="(p, key) in providers" :key="key"
                :label="p.label" :value="key" />
            </el-select>
          </el-form-item>
          <el-form-item label="Base URL">
            <el-input v-model="llm.base_url" class="mono" placeholder="https://.../v1" />
          </el-form-item>
          <el-form-item label="API Key">
            <el-input v-model="llm.api_key" class="mono" show-password placeholder="sk-..." />
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
          <el-form-item>
            <el-button class="glow-btn" type="primary" plain :loading="saving" @click="saveLlm">
              {{ llm.id ? '保存修改' : '新增配置' }}</el-button>
            <el-button plain :loading="testing" style="color:var(--accent-2);border-color:var(--accent-2)"
                       @click="testLlm">测试连接</el-button>
            <el-button plain @click="cancelEdit">取消</el-button>
            <span v-if="testMsg" :style="{color: testOk ? 'var(--accent)' : '#f56c6c', marginLeft:'10px', fontSize:'13px'}">
              {{ testMsg }}</span>
          </el-form-item>
        </template>

        <el-form-item v-else>
          <div class="cfg-hint">
            还没有模型配置，点上方「＋ 新增」自己建一条（名称、Base URL、API Key、模型名全部由你填）。
            <template v-if="legacy.has_key">
              <br />检测到旧的单条配置（{{ legacy.model || '未填模型' }}），
              <a class="link" @click="importLegacy">点这里导入</a> 就能变成一条可管理的配置。
            </template>
          </div>
        </el-form-item>
      </el-form>

      <el-alert type="info" :closable="false" title="配置保存在本地数据库，仅本机使用"
                description="下拉框选中哪条，练习/测验就用哪条；类型固定为「自定义（OpenAI 兼容）」，可随时新增、改名或删除。" />
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
          <div style="display:flex;gap:8px;width:100%">
            <el-select v-model="form.topic" filterable style="flex:1" placeholder="下拉选择一个主题">
              <el-option v-for="t in topicOptions" :key="t" :label="t" :value="t" />
            </el-select>
            <el-button plain style="color:var(--accent);border-color:var(--accent)"
                       @click="addTopic">＋ 新增</el-button>
            <el-button v-if="canDeleteTopic" plain type="danger" @click="removeTopic">删除</el-button>
          </div>
          <div class="cfg-hint">下拉里选中哪个，练习页默认就用哪个；主题可以自己新增、删除。</div>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from '../utils/message'
import api from '../api'
import { useSettingsStore } from '../stores/settings'

const store = useSettingsStore()
const difficulties = ref([])
const providers = ref({})
const configs = ref([])
const activeId = ref('')
const pickedId = ref('')          // 下拉框选中的配置 id
const editing = ref(false)        // 是否展开编辑表单
const legacy = ref({})            // 旧的单条配置（列表为空时可一键导入）
const form = reactive({ difficulty: 'L1', topic: 'daily life', voice: 'aria', rate: 1.0 })
const llm = reactive({ id: '', name: '', provider: 'custom', base_url: '', api_key: '',
                       model: '' })
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

async function loadConfigs(pickAfter = true) {
  const { data } = await api.get('/settings/llm/configs')
  configs.value = data.items
  activeId.value = data.active_id
  legacy.value = data.legacy || {}
  if (pickAfter) pickCurrent()
}

/** 下拉框默认停在「当前使用」那条；一条都没有就收起表单 */
function pickCurrent() {
  if (!configs.value.length) {
    pickedId.value = ''
    editing.value = false
    resetForm()
    return
  }
  onPick(activeId.value || configs.value[0].id)
}

/** 下拉框选择：载入表单编辑，并且「选它就用它」 */
function onPick(id) {
  const c = configs.value.find(x => x.id === id)
  if (!c) return
  pickedId.value = id
  editing.value = true
  fill(c)
  if (c.id !== activeId.value) activateConfig(c)
}

function fill(c) {
  Object.assign(llm, { id: c.id, name: c.name, provider: 'custom', base_url: c.base_url,
                       api_key: c.api_key, model: c.model })
  modelList.value = []   // 换配置后旧模型列表失效
  testMsg.value = ''
}

function resetForm() {
  Object.assign(llm, { id: '', name: '', provider: 'custom',
                       base_url: '', api_key: '', model: '' })
  modelList.value = []
  testMsg.value = ''
}

/** 新增：清空表单，保存时会创建一条新配置 */
function newConfig() {
  resetForm()
  pickedId.value = ''
  editing.value = true
}

/** 把旧的单条配置（Base URL / 模型 / 脱敏 key）填进新增表单，保存即成为可管理的配置 */
function importLegacy() {
  resetForm()
  pickedId.value = ''
  editing.value = true
  llm.name = '我的配置'
  llm.base_url = legacy.value.base_url || ''
  llm.model = legacy.value.model || ''
  llm.api_key = legacy.value.api_key || ''
}

function cancelEdit() {
  pickCurrent()
}

async function saveLlm() {
  if (!llm.name.trim()) return ElMessage.warning('请先给这条配置起个名称')
  if (!llm.base_url.trim()) return ElMessage.warning('请填写 Base URL')
  saving.value = true
  try {
    const { data } = await api.post('/settings/llm/configs', {
      id: llm.id || undefined, name: llm.name, base_url: llm.base_url,
      api_key: llm.api_key, model: llm.model,
      make_active: true,
    })
    configs.value = data.items
    activeId.value = data.active_id
    legacy.value = data.legacy || {}
    const saved = data.items.find(i => i.id === data.focus_id)
    if (saved) { pickedId.value = saved.id; editing.value = true; fill(saved) }
    ElMessage.success(`「${saved ? saved.name : llm.name}」已保存并设为当前使用`)
  } catch (e) {
    ElMessage.error(netErr(e, '保存失败'))
  } finally { saving.value = false }
}

async function activateConfig(c) {
  const { data } = await api.post(`/settings/llm/configs/${c.id}/activate`)
  configs.value = data.items
  activeId.value = data.active_id
}

async function removeConfig() {
  const c = configs.value.find(x => x.id === pickedId.value)
  if (!c) return
  try {
    await ElMessageBox.confirm(`确定删除配置「${c.name}」？删除后无法恢复。`, '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }   // 用户取消
  const { data } = await api.delete(`/settings/llm/configs/${c.id}`)
  configs.value = data.items
  activeId.value = data.active_id
  legacy.value = data.legacy || {}
  pickedId.value = ''
  pickCurrent()
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
  // 用 store.save 而不是裸 PUT：保存后 store 会同步刷新（load 有 loaded 短路，不会重新拉）
  await store.save(form)
  ElMessage.success('已保存')
}

// ── 主题下拉框：可新增、可删除 ──────────────────────────────
const topicOptions = computed(() => {
  const list = [...(store.topics || [])]
  if (form.topic && !list.includes(form.topic)) list.unshift(form.topic)  // 旧值不在列表里也要能显示
  return list
})
const canDeleteTopic = computed(() => (store.topics || []).includes(form.topic))

/** 主题列表一改就落库（页面上的「保存」按钮仍只管默认参数） */
async function saveTopics(list, patch = {}) {
  await store.save({ topics: list, ...patch })
}

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
  await saveTopics([...(store.topics || []), value])
  form.topic = value
  ElMessage.success(`已新增主题「${value}」`)
}

async function removeTopic() {
  const name = form.topic
  if (!(store.topics || []).includes(name)) return
  if (store.topics.length <= 1) return ElMessage.warning('至少要留一个主题')
  try {
    await ElMessageBox.confirm(`确定删除主题「${name}」？`, '删除主题',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }   // 取消
  const left = store.topics.filter(t => t !== name)
  // 删掉的正好是当前默认主题，就顺手把默认主题改成剩下的第一个
  await saveTopics(left, name === store.topic ? { topic: left[0] } : {})
  form.topic = store.topic || left[0]
  ElMessage.success(`已删除主题「${name}」`)
}
</script>

<style scoped>
.cfg-hint { color: var(--text-dim); font-size: 12px; line-height: 1.8; margin-top: 2px; }
.link { color: var(--accent); cursor: pointer; text-decoration: underline; }
.link:hover { color: #7dd3fc; }
</style>
