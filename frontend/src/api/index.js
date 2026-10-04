import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// 常用接口快捷方法（挂到实例上，实例本身的 get/post/put/delete 依旧可用）
api.meta = () => api.get('/meta')
api.generate = (data) => api.post('/sentences/generate', data)
api.listSentences = (params) => api.get('/sentences', { params })
api.sentenceTopics = () => api.get('/sentences/topics')
api.randomSentences = (params) => api.get('/sentences/random', { params })
api.deleteSentence = (id) => api.delete(`/sentences/${id}`)
api.setMastered = (id, mastered) => api.post(`/sentences/${id}/mastered`, { mastered })
api.checkAnswer = (data) => api.post('/quiz/check', data)
api.nextQuiz = (params) => api.get('/quiz/next', { params })
api.submitQuiz = (data) => api.post('/quiz/submit', data)
api.stats = () => api.get('/stats')
api.deleteWrong = (id) => api.delete(`/stats/wrong/${id}`)
api.getSettings = () => api.get('/settings')
api.putSettings = (data) => api.put('/settings', data)

export default api
