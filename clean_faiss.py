# clean_faiss.py # 启动自动清理faiss
import json,os,time
from config import LOG_DIR
from summer.faiss_index import FIndex
from summer.embedding import Emb
faiss_dir=f'{LOG_DIR}/faiss'
meta=f'{faiss_dir}/faiss_metadata.json'
index_path=f'{faiss_dir}/faiss.index'
if not os.path.exists(meta):json.dump({},open(meta,'w',encoding='utf-8'))
m=json.load(open(meta,encoding='utf-8'))
chunks=[]
for key in m:
 for fn in os.listdir(LOG_DIR):
  if fn.endswith('.txt'):
   with open(f'{LOG_DIR}/{fn}',encoding='utf-8')as r:
    t=None
    for l in r:
     if l.strip().startswith('时间:'):t=l.split(':',1)[1].strip()
     for role in['用户','user','娜迦','ai']:
      if l.strip().startswith(f'{role}:'):
       txt=l.split(':',1)[1].strip()
       k=__import__('hashlib').md5(f'{fn}_{t}_{role}_{txt}'.encode()).hexdigest()
       if k==key:chunks+=[{'role':role,'text':txt,'time':t,'file':fn,'key':k}]
usage_file=f'{faiss_dir}/faiss_usage.json'
usage=json.load(open(usage_file,encoding='utf-8')) if os.path.exists(usage_file) else{}
now=time.time()
unused={k for k in m if (k not in usage or now-usage[k]>30*86400) and m[k].get('weight',1)<=1}
vecs=Emb().enc([c['text']for c in chunks])
del_dup=set()
import numpy as np
for i in range(len(vecs)):
 for j in range(i+1,len(vecs)):
  if np.dot(vecs[i],vecs[j])/(np.linalg.norm(vecs[i])*np.linalg.norm(vecs[j]))>0.98:
   del_dup.add(chunks[j]['key'])
remove=unused|del_dup
keep=[c for c in chunks if c['key']not in remove]
if keep:
 vs=Emb().enc([c['text']for c in keep])
 f=FIndex();f.add(vs);f.save()
for k in remove:m.pop(k,None)
json.dump(m,open(meta,'w',encoding='utf-8'),ensure_ascii=0,indent=1)
print(f'[夏园]：已清理{len(remove)}条无用/冗余向量') 