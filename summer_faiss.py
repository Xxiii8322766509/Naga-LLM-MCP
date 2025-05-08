from summer.embedding import Emb
from summer.faiss_index import FIndex
from config import LOG_DIR
from config import SIM_THRESHOLD
import json,os,hashlib
import time
from concurrent.futures import ThreadPoolExecutor

faiss_dir=f'{LOG_DIR}/faiss'
meta=f'{faiss_dir}/faiss_metadata.json'
usage_file=f'{faiss_dir}/faiss_usage.json'

executor = ThreadPoolExecutor(max_workers=4)

def log_retrieve(query,theme,hit,keys):
 fn=f"logs/retrieve_{time.strftime('%Y%m')}.log"
 with open(fn,'a',encoding='utf-8')as f:
  t=time.strftime('%Y-%m-%d %H:%M:%S')
  f.write(f"{t}\t主题:{theme}\t命中:{hit}\tquery:{query}\tkeys:{','.join(keys)}\n")

def faiss_recall(q,k=3):
 def _recall(q,k):
  v=Emb().enc([q])
  f=FIndex();f.load()
  D,I=f.search(v,k)
  try:m=json.load(open(meta,encoding='utf-8'))
  except:m={}
  try:usage=json.load(open(usage_file,encoding='utf-8'))
  except:usage={}
  chunks=[]
  for key in m:
   for fn in os.listdir(LOG_DIR):
    if not fn.endswith('.txt'):continue
    with open(f'{LOG_DIR}/{fn}',encoding='utf-8')as r:
     t=None
     for l in r:
      if l.strip().startswith('时间:'):t=l.split(':',1)[1].strip()
      for role in['用户','user','娜迦','ai']:
       if l.strip().startswith(f'{role}:'):
        txt=l.split(':',1)[1].strip()
        ck=hashlib.md5(f'{fn}_{t}_{role}_{txt}'.encode()).hexdigest()
        if ck==key:chunks+=[{'role':'user'if'用户'in role else'ai','text':txt,'time':t,'file':fn,'key':ck}]
  res=[chunks[i] for i in I[0] if i>=0 and i<len(chunks) and D[0][list(I[0]).index(i)]>=SIM_THRESHOLD]
  for c in res:
   k=c['key']
   usage[k]=time.time()
   if k in m:m[k]["weight"]=m[k].get("weight",1)+1
  json.dump(usage,open(usage_file,'w',encoding='utf-8'),ensure_ascii=0,indent=1)
  json.dump(m,open(meta,'w',encoding='utf-8'),ensure_ascii=0,indent=1)
  log_retrieve(q,'*',len(res),[c['key'] for c in res])
  return sorted(res,key=lambda x:(-m.get(x['key'],{}).get('weight',1)))
 return executor.submit(_recall,q,k)

def faiss_add(chunks):
 def _add(chunks):
  for t in set(c.get('theme','default') for c in chunks):
   cs=[c for c in chunks if c.get('theme','default')==t]
   if not cs:continue
   fn='_'.join(t.split('/')) if t else 'default'
   idx=f'{faiss_dir}/{fn}.index'
   mfile=f'{faiss_dir}/{fn}_meta.json'
   vs=Emb().enc([c['text']for c in cs])
   f=FIndex();
   if os.path.exists(idx):f.load(idx)
   f.add(vs)
   f.save(idx)
   try:m=json.load(open(mfile,encoding='utf-8'))
   except:m={}
   for c in cs:
    k=hashlib.md5(f"{c.get('file','')}_{c.get('time','')}_{c.get('role','')}_{c['text']}".encode()).hexdigest()
    if k not in m:m[k]={'weight':1}
    else:m[k]['weight']=m[k].get('weight',1)
   json.dump(m,open(mfile,'w',encoding='utf-8'),ensure_ascii=0,indent=1)
 return executor.submit(_add,chunks)

def faiss_recall_by_theme(q,theme,k=3):
 def _recall_theme(q,theme,k):
  fn='_'.join(theme.split('/')) if theme else 'default'
  idx=f'{faiss_dir}/{fn}.index'
  mfile=f'{faiss_dir}/{fn}_meta.json'
  v=Emb().enc([q])
  f=FIndex();f.load(idx)
  D,I=f.search(v,k)
  try:m=json.load(open(mfile,encoding='utf-8'))
  except:m={}
  chunks=[]
  for key in m:
   for fn in os.listdir(LOG_DIR):
    if not fn.endswith('.txt'):continue
    with open(f'{LOG_DIR}/{fn}',encoding='utf-8')as r:
     t=None
     for l in r:
      if l.strip().startswith('时间:'):t=l.split(':',1)[1].strip()
      for role in['用户','user','娜迦','ai']:
       if l.strip().startswith(f'{role}:'):
        txt=l.split(':',1)[1].strip()
        ck=hashlib.md5(f'{fn}_{t}_{role}_{txt}'.encode()).hexdigest()
        if ck==key:chunks+=[{'role':'user'if'用户'in role else'ai','text':txt,'time':t,'file':fn,'key':ck}]
  res=[chunks[i] for i in I[0] if i>=0 and i<len(chunks) and D[0][list(I[0]).index(i)]>=SIM_THRESHOLD]
  for c in res:
   k=c['key']
   if k in m:m[k]["weight"]=m[k].get("weight",1)+1
  json.dump(m,open(mfile,'w',encoding='utf-8'),ensure_ascii=0,indent=1)
  log_retrieve(q,theme,len(res),[c['key'] for c in res])
  return sorted(res,key=lambda x:(-m.get(x['key'],{}).get('weight',1)))
 return executor.submit(_recall_theme,q,theme,k)

def faiss_fuzzy_recall(q,k=3):
 def _fuzzy(q,k):
  v=Emb().enc([q])
  res=[]
  for f in os.listdir(faiss_dir):
   if not f.endswith('.index'):continue
   idx=os.path.join(faiss_dir,f)
   mfile=idx.replace('.index','_meta.json')
   if not os.path.exists(mfile):continue
   fidx=FIndex();fidx.load(idx)
   D,I=fidx.search(v,k)
   try:m=json.load(open(mfile,encoding='utf-8'))
   except:m={}
   chunks=[]
   for key in m:
    for fn in os.listdir(LOG_DIR):
     if not fn.endswith('.txt'):continue
     with open(f'{LOG_DIR}/{fn}',encoding='utf-8')as r:
      t=None
      for l in r:
       if l.strip().startswith('时间:'):t=l.split(':',1)[1].strip()
       for role in['用户','user','娜迦','ai']:
        if l.strip().startswith(f'{role}:'):
         txt=l.split(':',1)[1].strip()
         ck=hashlib.md5(f'{fn}_{t}_{role}_{txt}'.encode()).hexdigest()
         if ck==key:chunks+=[{'role':'user'if'用户'in role else'ai','text':txt,'time':t,'file':fn,'key':ck}]
   for i in I[0]:
    if i>=0 and i<len(chunks) and D[0][list(I[0]).index(i)]>=SIM_THRESHOLD:
     res+=[chunks[i]]
  return sorted(res,key=lambda x:-x.get('weight',1))[:k]
 return executor.submit(_fuzzy,q,k) 