# gen_frames.py # 纯黑白动画白底无描边
from PIL import Image,ImageSequence
import os
gif='loading.gif';scale=0.3;bg='#FFFFFF';out='frames'
os.makedirs(out,exist_ok=1)
im=Image.open(gif)
w,h=int(im.width*scale),int(im.height*scale)
for i,f in enumerate(ImageSequence.Iterator(im)):
 fr=f.convert('RGBA').resize((w,h),Image.LANCZOS)
 d=fr.load()
 for x in range(w):
  for y in range(h):
   if d[x,y][3]<128:d[x,y]=(*d[x,y][:3],0) # 半透明像素设为全透明
 fr.save(f'{out}/frame_{i}.png')
