from conversation_core import NagaConversation
import os,asyncio
n=NagaConversation()
def show_help():print('系统命令: 清屏, 查看索引, 帮助, 退出')
def show_index():print('主题分片索引已集成，无需单独索引查看')
def clear():os.system('cls'if os.name=='nt'else'clear')
with open('./ui/progress.txt','w')as f:f.write('0')
os.system('python clean_faiss.py')
print('='*30+'\n娜迦对话系统已启动\n'+'='*30)
show_help()
async def main():
 while 1:
  u=input('\n用户:').strip()
  if u in['exit','退出','quit']:break
  if u in['清屏','clear','cls']:clear();continue
  if u in['帮助','help']:show_help();continue
  if u in['查看索引','show index','显示索引']:show_index();continue
  a=await n.process(u)
  print('娜迦:',a)
asyncio.run(main())
