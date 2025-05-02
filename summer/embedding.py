from sentence_transformers import SentenceTransformer # 向量模型
import numpy as np # 数值计算
from config import EMBEDDING_MODEL # 配置导入
import logging # 日志
from tqdm import tqdm # 进度条

# 配置根日志级别
logging.basicConfig(level=logging.INFO)

# 自定义日志格式
class CustomFormatter(logging.Formatter):
    """自定义日志格式器"""
    def format(self, record):
        if record.levelname == 'INFO':
            if 'device_name' in record.msg:
                return f"[夏园系统] 正在使用 {record.msg.split(': ')[1]} 进行推理"
            elif 'Load pretrained SentenceTransformer' in record.msg:
                return "" # 不显示模型加载日志
        return ""

# 配置自定义日志处理
st_logger = logging.getLogger('sentence_transformers.SentenceTransformer')
st_logger.setLevel(logging.INFO)  # 确保INFO级别的日志可以显示
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter('%(message)s'))
st_logger.handlers = [handler]
st_logger.propagate = False  # 防止日志传递到父logger

# 禁用httpx的日志
logging.getLogger('httpx').setLevel(logging.WARNING)

# 自定义进度条格式
tqdm.monitor_interval = 0
class CustomTqdm(tqdm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.desc = "[夏园系统] 正在写入向量数据库"
        self.bar_format = "{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [速度:{rate_fmt}]"

class Emb: # 向量化工具类
    def __init__(s):
        s.m = SentenceTransformer(str(EMBEDDING_MODEL)) # 初始化模型
        # 替换sentence_transformers内部的tqdm
        import sentence_transformers.models
        sentence_transformers.models.Transformer.tqdm = CustomTqdm
    
    def enc(s, txts):
        vectors = s.m.encode(txts, normalize_embeddings=True)
        return np.array(vectors) # 文本转归一化向量