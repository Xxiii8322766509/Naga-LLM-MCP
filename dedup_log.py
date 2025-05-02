# 日志全局去重脚本 #
import os,json
from pathlib import Path
LOG_DIR="logs" # 如有不同请改为你的LOG_DIR
for f in Path(LOG_DIR).glob("*.json"):
    with open(f,"r",encoding="utf-8") as h:d=json.load(h)
    s,r=set(),[]
    for x in d:
        k=json.dumps(x,sort_keys=1,ensure_ascii=0)
        if k not in s:s.add(k);r.append(x)
    if len(r)<len(d):
        with open(f,"w",encoding="utf-8") as h:json.dump(r,h,ensure_ascii=0,indent=2)
        print(f"{f}: 去重{len(d)-len(r)}条") 