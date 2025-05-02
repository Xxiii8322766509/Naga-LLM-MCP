from summer.embedding import Emb # 向量
from summer.faiss_index import FIndex # faiss
from config import LOG_DIR,THEME_ROOTS # 日志目录
import json,os
q=input('请输入检索内容:') # 用户输入
theme=input('主题路径(如科技/人工智能,留空查全部):').strip() # 主题输入
if theme:
 fn='_'.join(theme.split('/'))
 idx=f'{LOG_DIR}/faiss/{fn}.index'
 meta=f'{LOG_DIR}/faiss/{fn}_meta.json'
 f=FIndex();f.load(idx)
 try:m=json.load(open(meta,encoding='utf-8'))
 except:m={}
else:
 idx=f'{LOG_DIR}/faiss/faiss.index'
 meta=f'{LOG_DIR}/faiss/faiss_metadata.json'
 f=FIndex();f.load()
 try:m=json.load(open(meta,encoding='utf-8'))
 except:m={}
v=Emb().enc([q]) # 编码
D,I=f.search(v,5) # 检索
chunks=[]
for k in m:
 for fn in os.listdir(LOG_DIR):
  if not fn.endswith('.txt'):continue
  with open(f'{LOG_DIR}/{fn}',encoding='utf-8')as r:
   t=None
   for l in r:
    if l.strip().startswith('时间:'):t=l.split(':',1)[1].strip()
    for role in['用户','user','娜迦','ai']:
     if l.strip().startswith(f'{role}:'):
      txt=l.split(':',1)[1].strip()
      ck=__import__('hashlib').md5(f'{fn}_{t}_{role}_{txt}'.encode()).hexdigest()
      if ck==k:chunks+=[{'role':'user'if'用户'in role else'ai','text':txt,'time':t,'file':fn}]
for i in I[0]:
 if i<len(chunks):c=chunks[i];print(f"[{c['time']}][{c['role']}]:{c['text']}") # 输出
# 附带主题摘要
sfile=f'{LOG_DIR}/chat_summary.txt'
if os.path.exists(sfile):
 print('\n主题摘要:')
 print(open(sfile,encoding='utf-8').read()) # 摘要 