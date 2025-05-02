import faiss,os,numpy as np # faiss为向量库
from config import FAISS_DIM,FAISS_INDEX_PATH,HNSW_M,PQ_M

class FIndex: # Faiss索引管理类
 def __init__(s,d=FAISS_DIM):
  s.d=d
  s.i=s._create_index() # 创建并预热索引
  
 def _create_index(s): # 创建索引
  i=faiss.IndexHNSWPQ(s.d,HNSW_M,PQ_M,8)
  if not i.is_trained: # 未训练则预热
   train_data=np.random.randn(10000,s.d).astype('float32')
   i.train(train_data)
  return i
  
 def add(s,vecs,batch_size=1024): # 批量添加向量
  for i in range(0,len(vecs),batch_size):
   s.i.add(vecs[i:i+batch_size])
   
 def save(s,p=FAISS_INDEX_PATH):faiss.write_index(s.i,str(p)) # 保存索引
 
 def load(s,p=FAISS_INDEX_PATH): # 加载索引
  if not os.path.exists(p):s.i=s._create_index()
  else:s.i=faiss.read_index(str(p))
  
 def search(s,v,k=5): # 智能检索
  if k<=10: # 小规模搜索
   s.i.hnsw.efSearch=64
   s.i.nprobe=8
  elif k<=50: # 中等规模
   s.i.hnsw.efSearch=128
   s.i.nprobe=16
  else: # 大规模搜索
   s.i.hnsw.efSearch=256
   s.i.nprobe=32
  D,I=s.i.search(v,k)
  return D,I