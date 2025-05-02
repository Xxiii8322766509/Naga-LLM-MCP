# loading.py # 启动加载动画
from tkinter import *;from PIL import ImageTk;import os,glob
FRAMES=sorted(glob.glob(os.path.join(os.path.dirname(__file__),'frames/frame_*.png')))
def show_loading():
 w=Tk();w.overrideredirect(1);w.attributes('-topmost',1);w.config(bg='#123456');w.wm_attributes('-transparentcolor','#123456')
 im=ImageTk.PhotoImage(file=FRAMES[0]);w_,h_=im.width(),im.height()
 sw,sh=w.winfo_screenwidth(),w.winfo_screenheight();w.geometry(f'{w_}x{h_}+{(sw-w_)//2}+{(sh-h_)//2}')
 c=Canvas(w,width=w_,height=h_,bg='#123456',highlightthickness=0);c.pack()
 frames=[ImageTk.PhotoImage(file=f)for f in FRAMES]
 lbl=c.create_image(w_//2,h_//2,image=frames[0])
 def play(i=0):c.itemconfig(lbl,image=frames[i%len(frames)]);w.after(50,lambda:play(i+1))
 def close():w.destroy();w.quit() # 关闭窗口函数
 w.bind('<Escape>',lambda e:close()) # ESC键退出
 Button(w,text='关闭',command=close,bg='#123456',fg='white',bd=0).place(x=w_-50,y=10) # 添加关闭按钮
 w.after(0,play) # 立即播放动画
 w.mainloop()
if __name__=='__main__':
 try:show_loading()
 except Exception as e:
  import traceback;traceback.print_exc();input('按任意键退出...')