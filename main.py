import threading
from conversation_core import NagaConversation
import os,asyncio
import sys
sys.path.append(os.path.dirname(__file__))
from ui.pyqt_chat_window import ChatWindow
from PyQt5.QtWidgets import QApplication
n=NagaConversation()
def show_help():print('系统命令: 清屏, 查看索引, 帮助, 退出')
def show_index():print('主题分片索引已集成，无需单独索引查看')
def clear():os.system('cls'if os.name=='nt'else'clear')
with open('./ui/progress.txt','w')as f:f.write('0')
os.system('python clean_faiss.py')
print('='*30+'\n娜迦对话系统已启动\n'+'='*30)
show_help()
loop=asyncio.new_event_loop()
threading.Thread(target=loop.run_forever,daemon=True).start()
class NagaAgentAdapter:
 def __init__(s):s.naga=NagaConversation()
 async def respond_stream(s,txt):resp=await s.naga.process(txt);yield "娜迦",resp,None,True,False
if __name__=="__main__":
 app=QApplication(sys.argv)
 win=ChatWindow()
 win.show()
 sys.exit(app.exec_())
