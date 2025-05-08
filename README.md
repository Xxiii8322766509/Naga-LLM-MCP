# NagaAgent 2.1

> 智能对话助手，支持多MCP服务、流式语音交互、主题树检索、极致精简代码风格。

## ⚡ 快速开始
1. 克隆项目
   ```powershell
   git clone [项目地址]
   cd NagaAgent/2.0
   ```
2. 一键配置
   ```powershell
   .\setup.ps1
   ```
   - 自动创建虚拟环境并安装依赖
   - 检查/下载中文向量模型
   - 配置支持toolcall的LLM，推荐DeepSeekV3
3. 启动
   ```powershell
   .\start.bat
   ```

## 🖥️ 系统要求
- Windows 10/11
- Python 3.13+
- PowerShell 5.1+

## 🛠️ 依赖安装与环境配置
- 所有依赖见`requirements.txt`
- 如遇`greenlet`、`pyaudio`等安装失败，需先装[Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)，勾选C++ build tools，重启命令行后再`pip install -r requirements.txt`
- 浏览器自动化需`playwright`，首次用需`python -m playwright install chromium`
- 依赖安装命令：
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate
  pip install -r requirements.txt
  python -m playwright install chromium
  ```

## 🌟 主要特性
- 全局变量/路径/密钥统一`config.py`管理，支持.env和环境变量
- DeepSeek流式对话，支持上下文召回与主题树分片检索
- faiss向量数据库，HNSW+PQ混合索引，异步加速，动态调整深度，权重动态调整，自动清理
- MCP服务集成，Agent Handoff智能分发，支持自定义过滤器与回调
- 代码极简，变量唯一，注释全中文，组件解耦，便于扩展
- PyQt5动画与UI，支持PNG序列帧，loading动画极快
- 日志/检索/索引/主题/参数全部自动管理

## 🔊 流式语音交互
- 支持语音输入（流式识别，自动转文字）与语音输出（流式合成，边播边出）
- 启用方法：
  1. 编辑`voice/voice_config.py`，将`ENABLED=True`
  2. `config.py`配置`DEEPSEEK_API_KEY`
  3. 运行主程序，空输入自动语音识别，AI回复自动语音播报
- 依赖：`sounddevice`、`soundfile`、`pyaudio`、`openai`等
- 语音配置参数：
  ```python
  # voice/voice_config.py
  STT_MODEL = "whisper-1" # 语音识别模型
  TTS_MODEL = "tts-1"     # 语音合成模型
  TTS_VOICE = "alloy"     # 合成声音
  SAMPLE_RATE = 16000      # 采样率
  CHUNK_SIZE = 4096        # 音频块大小
  ENABLED = True           # 启用语音
  ```

## 🧠 主题树与faiss检索
- 对话自动归一主题树，分片写入faiss索引，支持多级主题归一与自由扩展
- 检索结果优先返回高权重内容，低权重内容自动清理
- 检索日志自动记录，参数可调
- faiss配置示例：
  ```python
  # config.py
  EMBEDDING_MODEL = BASE_DIR / 'models/text2vec-base-chinese'
  FAISS_INDEX_PATH = BASE_DIR / 'logs/faiss/faiss.index'
  FAISS_DIM = 768
  HNSW_M = 32
  PQ_M = 16
  SIM_THRESHOLD = 0.3
  ```

## 🌐 浏览器自动化与MCP服务
- 直接对话如"打开bilibili"，自动handoff到浏览器Agent
- 支持chromium/firefox/webkit，窗口/无头可选
- MCP服务配置：
  ```python
  # config.py
  MCP_SERVICES = {
    "playwright": {
      "enabled": True,
      "name": "Playwright浏览器",
      "description": "网页浏览与内容提取",
      "type": "python",
      "script_path": str(BASE_DIR / "mcpserver" / "agent_playwright_master" / "playwright.py")
    }
  }
  ```
- Handoff机制：主Agent只分发任务，具体操作由子Agent完成

### 🚀 全自动化热插件注册
- 所有MCP服务代码放在`mcpserver/`目录，类名以`Agent`或`Tool`结尾，系统自动扫描注册，无需手动import。
- 新增/删除MCP服务只需增删py文件，**即插即用、热插拔**，无需重启主程序。
- 注册表见`mcpserver/mcp_registry.py`，全局自动管理。
- **只有`__init__`无参数（可无参实例化）的Agent/Tool类会被自动注册，带参数的类会自动跳过。**

## 📚 目录结构
```
2.0/
├── main.py           # 主入口
├── config.py         # 全局配置
├── conversation_core.py # 对话核心
├── mcp_manager.py    # MCP服务管理
├── requirements.txt  # 依赖
├── voice/            # 语音相关
│   ├── voice_config.py
│   └── voice_handler.py
├── logs/             # 日志
├── summer/           # faiss与向量相关
└── ...
```

## ❓ 常见问题
- Python版本/依赖/虚拟环境/浏览器驱动等问题，详见`setup.ps1`与本README
- IDE报import错误，重启并选择正确解释器
- 语音依赖安装失败，先装C++ Build Tools
- 浏览器无法启动，检查playwright安装与网络
- 主题树/索引/参数/密钥全部在`config.py`统一管理

## 📝 开发模式
- 聊天输入`#devmode`进入开发者模式，后续对话不写入faiss，仅用于MCP测试

## 📝 许可证
MIT License

---

如需详细功能/API/扩展说明，见各模块注释与代码，所有变量唯一、注释中文、极致精简。

## 聊天窗口自定义
1. 聊天窗口背景透明度由`config.BG_ALPHA`统一控制，取值0~1，默认0.4。
2. 用户名自动识别电脑名，变量`config.USER_NAME`，如需自定义可直接修改该变量。

## 智能历史召回机制
1. 默认按主题分片检索历史，极快且相关性高。
2. 若分片查不到，自动兜底遍历所有主题分片模糊检索（faiss_fuzzy_recall），话题跳跃也能召回历史。
3. faiss_fuzzy_recall支持直接调用，返回全局最相关历史。
4. 兜底逻辑已集成主流程，无需手动切换。

