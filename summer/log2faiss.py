from os import listdir,makedirs # 文件操作
from re import findall # 正则
from datetime import datetime # 时间
from config import LOG_DIR,THEME_ROOTS # 日志目录
from summer.embedding import Emb # 向量
from summer.faiss_index import FIndex # faiss
import json,hashlib,os # json与hash
import difflib

def normalize_theme(raw): # 主题归一化
 seg=raw.split('/')
 root=difflib.get_close_matches(seg[0],THEME_ROOTS.keys(),n=1,cutoff=0.6)
 root=root[0] if root else list(THEME_ROOTS.keys())[0]
 if len(seg)>1:
  sub=difflib.get_close_matches(seg[1],THEME_ROOTS[root],n=1,cutoff=0.6)
  sub=sub[0] if sub else THEME_ROOTS[root][0]
  return '/'.join([root,sub]+seg[2:])
 return root 

p=LOG_DIR # 日志目录
faiss_dir=f'{p}/faiss'
os.makedirs(faiss_dir,exist_ok=True) # 自动创建目录
fs=sorted([f for f in listdir(p) if f.endswith('.txt')]) # 所有对话文件
if not fs:exit() # 无文件退出
# 主题分片批量入库
chunks_by_theme={}
for f in fs[-1:]: # 只处理最新文件，如需全量改为fs
 with open(f'{p}/{f}',encoding='utf-8')as r:
  t=None
  for l in r:
   m1=findall(r'时间[:：]\s*(.*)',l)
   if m1:t=m1[0]
   for role in['用户','user','娜迦','ai']:
    if l.strip().startswith(f'{role}:'):
     txt=l.split(':',1)[1].strip()
     # 主题判定（可自定义，这里用正则或关键词极简归类）
     # 示例：如内容含"人工智能"归为科技/人工智能，否则默认科技/计算机科学
     if '人工智能' in txt:
      theme='科技/人工智能'
     else:
      theme='科技/计算机科学'
     theme=normalize_theme(theme)
     k=hashlib.md5(f'{f}_{t}_{role}_{txt}'.encode()).hexdigest()
     if theme not in chunks_by_theme:chunks_by_theme[theme]=[]
     chunks_by_theme[theme]+=[{'role':'user'if'用户'in role else'ai','text':txt,'time':t,'key':k,'theme':theme}]
for theme,chunks in chunks_by_theme.items():
 fn='_'.join(theme.split('/'))
 idx=f'{faiss_dir}/{fn}.index'
 mfile=f'{faiss_dir}/{fn}_meta.json'
 try:m=json.load(open(mfile,encoding='utf-8'))
 except:m={}
 vs=Emb().enc([c['text']for c in chunks])
 f=FIndex();
 if os.path.exists(idx):f.load(idx)
 f.add(vs)
 f.save(idx)
 for c in chunks:
  if c['key'] not in m:m[c['key']]={'weight':1}
 json.dump(m,open(mfile,'w',encoding='utf-8'),ensure_ascii=0,indent=1)
print(f'已分片入库{sum(len(v) for v in chunks_by_theme.values())}条新对话') 