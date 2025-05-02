import sys,os;sys.path.insert(0,os.path.abspath(os.path.dirname(__file__)+'/..'))
from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from conversation_core import NagaConversation
import uvicorn
app=FastAPI()
app.mount("/static",StaticFiles(directory=os.path.dirname(__file__)),name="static")
n=NagaConversation()
history=[]
HTML_TEMPLATE="""
<!DOCTYPE html><html lang=zh><head>
<meta charset=UTF-8><title>娜迦直播间</title>
<style>
body{margin:0;padding:0;background:#000 url('/static/loading.gif') center/cover no-repeat;height:100vh;}
#chat{position:relative;max-width:700px;margin:0 auto;padding-bottom:80px;min-height:100vh;}
#history{padding:30px 0 100px 0;}
.msg{margin:10px 0;word-break:break-all;}
.user{color:#fff;font-weight:bold;}
.ai{color:#fff;}
.bubble{background:rgba(0,0,0,0.7);border-radius:16px;padding:12px 18px;display:inline-block;max-width:80%;}
.user-bubble{border:1px solid #0078d7;float:right;clear:both;}
.ai-bubble{border:1px solid #e67e22;float:left;clear:both;}
#inputbar{position:fixed;bottom:0;left:0;width:100%;background:rgba(0,0,0,0.85);padding:16px 0;z-index:10;}
#f{display:flex;justify-content:center;align-items:center;}
#msg{width:60%;font-size:1.1em;padding:10px;border-radius:8px;border:none;background:#222;color:#fff;}
button{margin-left:10px;padding:10px 24px;border-radius:8px;border:none;background:#e67e22;color:#fff;font-size:1.1em;cursor:pointer;}
::-webkit-scrollbar{width:8px;background:#222;}::-webkit-scrollbar-thumb{background:#444;}
</style>
</head><body>
<div id=chat>
  <div id=history>
    {% for u,a in history %}
      <div class="msg"><span class="bubble user-bubble user">{{u}}</span></div>
      <div class="msg"><span class="bubble ai-bubble ai">{{a}}</span></div>
    {% endfor %}
  </div>
</div>
<div id=inputbar>
  <form id=f method=post action="/chat" autocomplete=off style="width:100%;text-align:center;">
    <input name=msg id=msg autocomplete=off placeholder="和娜迦对话..." autofocus>
    <button type=submit>发送</button>
  </form>
</div>
<script>
window.onload=function(){var h=document.getElementById('history');h.scrollTop=h.scrollHeight;}
document.getElementById('f').onsubmit=function(e){e.preventDefault();var m=document.getElementById('msg');if(m.value.trim()=="")return;fetch('/chat',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'msg='+encodeURIComponent(m.value)}).then(r=>r.text()).then(html=>{document.body.innerHTML=html;window.scrollTo(0,document.body.scrollHeight);});}
</script>
</body></html>
"""
@app.get("/",response_class=HTMLResponse)
def index():return HTML_TEMPLATE.replace('{% for u,a in history %}','').replace('{% endfor %}','').replace('{{u}}','').replace('{{a}}','')
@app.post("/chat",response_class=HTMLResponse)
def chat(req:Request):
 import asyncio
 form=asyncio.run(req.form()) if hasattr(req,'form') else req.form()
 u=form['msg'] if 'msg'in form else''
 a=n.process(u)
 history.append((u,a))
 h=''.join([f'<div class="msg"><span class="bubble user-bubble user">{u}</span></div><div class="msg"><span class="bubble ai-bubble ai">{a}</span></div>'for u,a in history])
 return HTML_TEMPLATE.replace('{% for u,a in history %}','').replace('{% endfor %}','').replace('{{u}}','').replace('{{a}}','').replace('<div id=history>','<div id=history>'+h)
if __name__=="__main__":
 import webbrowser
 webbrowser.open("http://127.0.0.1:7860")
 uvicorn.run(app,host="0.0.0.0",port=7860)
