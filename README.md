# 英语听力训练营 (english-listening-gym)

AI 驱动的英语听力训练工具:用 LLM 生成场景化例句 → Edge-TTS 合成地道美音 → 听音选句测验 → 按掌握度加权复习。支持手机(PWA)和电脑网页同时使用。

## 功能

- **AI 造句**:输入任意话题,LLM 生成地道英文句子,并自动检测近重复(向量 + 文本双重去重),避免知识库堆满换词模板句
- **地道发音**:Edge-TTS 合成美音(Aria / Guy),可调语速,支持逐句反复听
- **听力测验**:四选一听音辨句;干扰项由 LLM 生成,失败时自动回退到本地规则引擎,永远可做题
- **科学复习**:答对/答错动态调整句子权重,错题更常出现
- **学习统计**:总句数、掌握度分布、每日学习曲线
- **手机可用**:PWA 一键添加到主屏幕,电脑和手机在同一 Wi-Fi 下用浏览器访问即可

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI · SQLAlchemy 2 · SQLite · ChromaDB(向量去重) · edge-tts |
| 前端 | Vue 3 · Vite · Element Plus · Pinia |
| LLM | OpenAI 兼容接口(DeepSeek / 智谱 / OpenAI 等均可,网页设置里配置) |

## 快速开始

```bash
# 1. 后端(Python 3.10+)
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2. 前端
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173,进「设置」页填入 LLM 的 API Key 即可开始。

### Windows 一键启动

双击 `start.bat`(自动构建前端并启动前后端,还会打印手机访问地址);`stop.bat` 停止。

### 手机访问

手机与电脑连同一 Wi-Fi,浏览器打开 `start.bat` 启动时列出的地址(如 `http://192.168.x.x:5173`),然后「添加到主屏幕」即可像 App 一样使用。

## 目录结构

```
backend/
  app/
    config.py          # 配置与路径
    main.py            # FastAPI 入口
    routers/           # sentences / quiz / stats / settings / audio
    services/          # llm / tts / vector_store / dedup / distractors
    db/                # SQLAlchemy 模型与连接
    data/              # 运行时数据(app.db / audio / chroma),已 gitignore,含密钥勿传
frontend/
  src/
    views/             # 练习 / 测验 / 统计 / 知识库 / 设置
    components/        # AudioPlayer 等
    stores/            # Pinia
docs/                  # 需求与设计文档
```

## 隐私说明

- 你的 LLM API Key 只保存在本机 `backend/data/app.db`,**不会**被 git 提交或上传
- 句子、音频、学习记录全部存在本地

## License

[MIT](LICENSE)
