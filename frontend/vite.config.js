import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发期请求日志：排查手机等外部设备访问问题
const requestLogger = {
  name: 'el-request-logger',
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      const ip = (req.socket.remoteAddress || '').replace('::ffff:', '')
      const host = req.headers.host || ''
      res.on('finish', () => {
        console.log(`[访问] ${ip} host=${host} ${req.method} ${req.url} -> ${res.statusCode}`)
      })
      next()
    })
  },
  configurePreviewServer(server) {
    server.middlewares.use((req, res, next) => {
      const ip = (req.socket.remoteAddress || '').replace('::ffff:', '')
      const host = req.headers.host || ''
      res.on('finish', () => {
        console.log(`[访问] ${ip} host=${host} ${req.method} ${req.url} -> ${res.statusCode}`)
      })
      next()
    })
  }
}

export default defineConfig({
  plugins: [vue(), requestLogger],
  server: {
    // 监听所有网卡，手机等同一局域网设备才能访问
    host: '0.0.0.0',
    port: 5173,
    // 允许用主机名访问（IP 会随换网络变化，主机名不会）
    allowedHosts: ['tslldtyrone', 'tslldtyrone.local', '.local'],
    proxy: {
      '/api': 'http://127.0.0.1:8000'
    }
  },
  // 生产构建预览（npm run build && npm run preview），同样监听局域网
  preview: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: ['tslldtyrone', 'tslldtyrone.local', '.local'],
    proxy: {
      '/api': 'http://127.0.0.1:8000'
    }
  }
})
