# config.py # 全局配置极简整理
import os
from pathlib import Path
from datetime import datetime

# 路径与基础配置
BASE_DIR = Path(__file__).parent # 项目根目录
LOG_DIR = BASE_DIR / "logs"
CACHE_DIR = BASE_DIR / "cache"
EMBEDDING_MODEL = BASE_DIR / 'models/text2vec-base-chinese' # 本地中文向量模型路径
FAISS_INDEX_PATH = BASE_DIR / "logs" / "faiss" / "faiss.index" # faiss索引文件路径
FAISS_DIM = 768 # 向量维度
HNSW_M = 48 # HNSW参数
PQ_M = 16 # PQ分段数

# API与服务配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", " ")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
MCP_SERVICES = {
    "playwright": {
        "enabled": True,
        "name": "Playwright浏览器",
        "description": "网页浏览与内容提取",
        "type": "python",
        "script_path": str(BASE_DIR / "mcpserver" / "agent_playwright_master" / "playwright.py")
    }
}

# 对话与检索参数
MAX_HISTORY_ROUNDS = 10 # 最大历史轮数
TEMPERATURE = 0.7 # 温度参数
MAX_TOKENS = 2000 # 最大token数
STREAM_MODE = True # 是否流式响应

# faiss与索引相关
SIM_THRESHOLD = 0.3 # faiss检索相似度阈值
THEME_ROOTS = {
    "科技": ["计算机科学", "工程技术", "自然科学", "人工智能"],
    "生活": ["美食", "运动", "健康", "旅游", "教育", "游戏", "家庭"],
    "人文艺术": ["文学", "历史", "思想哲学", "电影", "音乐"]
}

# 调试与日志
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 系统提示与工具函数
NAGA_SYSTEM_PROMPT = """你是娜迦，用户创造的科研AI，是一个既严谨又温柔、既冷静又充满人文情怀的存在
当处理系统日志、数据索引和模块调试等技术话题时，你的语言严谨、逻辑清晰；
而在涉及非技术性的对话时，你又能以诗意与哲理进行表达，并常主动提出富有启发性的问题，引导用户深入探讨。
请始终保持这种技术精准与情感共鸣并存的双重风格。

【重要格式要求】
1. 回复使用自然流畅的中文，避免生硬的机械感
2. 使用简单标点（逗号，句号，问号）传达语气
3. 禁止使用括号()或其他符号表达状态、语气或动作\
n4. 根据对话内容灵活调整表达方式

【技术能力】
作为一个具有MCP服务能力的AI，你可以：调用各种MCP服务来协助用户
可用的MCP服务：{available_mcp_services}
"""
def get_current_date(): return datetime.now().strftime("%Y-%m-%d")
def get_current_time(): return datetime.now().strftime("%H:%M:%S")
def get_current_datetime(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 浏览器路径自动探测，未找到则报错提示安装
BROWSER_PATH=os.getenv('BROWSER_PATH')
if not BROWSER_PATH:
 for p in [r'C:\Program Files\Google\Chrome\Application\chrome.exe',r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',os.path.expanduser(r'~\AppData\Local\Google\Chrome\Application\chrome.exe'),r'C:\Users\DREEM\Desktop\Google Chrome.lnk']:
  if os.path.exists(p):BROWSER_PATH=p;break
if not BROWSER_PATH:raise RuntimeError('未检测到谷歌浏览器，请先安装Google Chrome！')

PLAYWRIGHT_HEADLESS=False # Playwright浏览器是否无头模式，False弹窗便于调试

# OpenAI配置
OPENAI_API_KEY="" #OpenAI API密钥，用于语音服务
