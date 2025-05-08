import logging,os,asyncio # 日志与系统
from datetime import datetime # 时间
from config import LOG_DIR,DEEPSEEK_API_KEY,DEEPSEEK_MODEL,TEMPERATURE,MAX_TOKENS,get_current_datetime,THEME_ROOTS,DEEPSEEK_BASE_URL,NAGA_SYSTEM_PROMPT,VOICE_ENABLED # 配置
from summer_faiss import faiss_recall,faiss_add,faiss_recall_by_theme,faiss_fuzzy_recall # faiss检索与入库
from mcp_manager import MCPManager, remove_tools_filter, HandoffInputData # 多功能管理
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX # handoff提示词
from mcpserver.agent_playwright_master import PlaywrightAgent, extract_url # 导入浏览器相关类
import openai # LLM
import difflib # 模糊匹配
import sys,json,traceback
from voice.voice_config import config as vcfg # 语音配置
from voice.voice_handler import VoiceHandler # 语音处理
_builtin_print=print
print=lambda *a,**k:sys.stderr.write('[print] '+(' '.join(map(str,a)))+'\n')

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("NagaConversation")

class NagaConversation: # 对话主类
 def __init__(s):
  s.mcp=MCPManager()
  s.messages=[]
  s.dev_mode=False
  s.voice=VoiceHandler() if vcfg.ENABLED else None
  # 注册handoff处理器
  try:
    logger.info("开始注册Playwright handoff处理器...")
    s.mcp.register_handoff(
     service_name="playwright",
     tool_name="browser_handoff",
     tool_description="处理所有浏览器相关操作",
     input_schema={
         "type": "object",
         "properties": {
             "url": {"type": "string", "description": "要访问的URL"},
             "query": {"type": "string", "description": "原始查询文本"},
             "messages": {"type": "array", "description": "对话历史"},
             "source": {"type": "string", "description": "请求来源"}
         },
         "required": ["query", "messages"]
     },
     agent_name="Playwright Browser Agent",
     strict_schema=False
    )
    logger.info("成功注册Playwright handoff处理器")
  except Exception as e:
    logger.error(f"注册Playwright handoff处理器失败: {e}")
    traceback.print_exc(file=sys.stderr)
 def save_log(s,u,a): # 保存对话日志
  if s.dev_mode:return # 开发者模式不写日志
  d=datetime.now().strftime('%Y-%m-%d')
  t=datetime.now().strftime('%H:%M:%S')
  f=os.path.join(LOG_DIR,f'{d}.txt')
  with open(f,'a',encoding='utf-8')as w:w.write(f'-'*50+f'\n时间: {d} {t}\n用户: {u}\n娜迦: {a}\n\n')
 def get_theme(s,u): # LLM主题树判定
  r=openai.chat.completions.create(model=DEEPSEEK_MODEL,messages=[{"role":"system","content":"请用/分隔输出本轮对话主题树，如'科技/人工智能/大模型'，只输出主题树，不要多余内容。"},{"role":"user","content":u}],temperature=0.2,max_tokens=20).choices[0].message.content
  theme=r.strip().replace(' ','') # 去空格
  theme=s.normalize_theme(theme) # 归一化
  return theme
 def normalize_theme(s,raw): # 主题归一化
  seg=raw.split('/')
  root=difflib.get_close_matches(seg[0],THEME_ROOTS.keys(),n=1,cutoff=0.6)
  root=root[0] if root else list(THEME_ROOTS.keys())[0]
  if len(seg)>1:
    sub=difflib.get_close_matches(seg[1],THEME_ROOTS[root],n=1,cutoff=0.6)
    sub=sub[0] if sub else THEME_ROOTS[root][0]
    return '/'.join([root,sub]+seg[2:])
  return root
 async def process(s,u):
  try:
   # 检查是否需要浏览器操作
   if any(x in u.lower() for x in ["bilibili","b站","浏览器","网站","打开","访问","youtube","谷歌","百度","github"]):
    logger.info(f"检测到浏览器操作请求: {u}")
    
    # 检查MCP服务
    logger.info(f"当前可用服务: {s.mcp.format_available_services()}")
    
    # 构造handoff数据
    messages = s.messages[-5:] + [{"role": "user", "content": u}]
    task_data = {
       "messages": messages,
       "query": u,
       "url": extract_url(u),
       "source": "conversation"
    }
    logger.info(f"构造的task数据: {json.dumps(task_data, ensure_ascii=False)}")
    
    try:
        logger.info("开始执行handoff操作...")
        result = await s.mcp.handoff(
         service_name="playwright",
         task=task_data,
         input_history=messages,
         pre_items=s.messages[:-5] if len(s.messages) > 5 else [],
         new_items=[{"role": "user", "content": u}],
         metadata={
             "type": "browser_request",
             "timestamp": datetime.now().isoformat(),
             "source": "conversation",
             "dev_mode": s.dev_mode
         }
        )
        logger.info(f"handoff返回结果: {result}")
        
        if result:
            try:
                response = json.loads(result) if isinstance(result, str) else result
                logger.debug(f"解析的响应: {json.dumps(response, ensure_ascii=False)}")
                
                # 检查过滤后的消息
                filtered_messages = response.get("filtered_messages", {})
                if filtered_messages:
                    logger.info(f"过滤后的消息统计: {filtered_messages.get('metadata', {})}")
                
                if response.get("status") == "ok":
                    return "已成功打开网页"
                else:
                    error_msg = f"打开网页失败: {response.get('message', '未知错误')}"
                    logger.error(error_msg)
                    return error_msg
            except json.JSONDecodeError as e:
                error_msg = f"解析响应失败: {str(e)}, 原始响应: {result}"
                logger.error(error_msg)
                return error_msg
            except Exception as e:
                error_msg = f"处理响应时发生异常: {str(e)}"
                logger.error(error_msg)
                traceback.print_exc(file=sys.stderr)
                return error_msg
        else:
            logger.error("handoff返回空结果")
            return "浏览器操作失败: 未收到响应"
    except Exception as e:
        error_msg = f"执行handoff时发生异常: {str(e)}"
        logger.error(error_msg)
        traceback.print_exc(file=sys.stderr)
        return error_msg
   
   if u.strip()=="#devmode":s.dev_mode=True;return "已进入开发者模式，后续对话不写入向量库"
   theme=None
   recall=faiss_recall_by_theme(u,theme,3)
   if hasattr(recall,'result'):recall=recall.result()
   if not recall:
    recall=faiss_fuzzy_recall(u,3)
    if hasattr(recall,'result'):recall=recall.result()
   ctx='\n'.join([f"[历史][{c['time']}][{c['role']}]:{c['text']}"for c in recall]) if recall else ''
   
   # 添加handoff提示词
   system_prompt = f"{RECOMMENDED_PROMPT_PREFIX}\n{NAGA_SYSTEM_PROMPT}"
   sysmsg={"role":"system","content":f"历史相关内容召回:\n{ctx}\n\n{system_prompt.format(available_mcp_services=s.mcp.format_available_services())}"} if ctx else {"role":"system","content":system_prompt.format(available_mcp_services=s.mcp.format_available_services())}
   
   msgs=[sysmsg] if sysmsg else[]
   msgs+=s.messages[-20:]+[{"role":"user","content":u}]
   
   openai.api_key=DEEPSEEK_API_KEY
   openai.base_url=DEEPSEEK_BASE_URL.rstrip('/')+'/'
   theme=s.get_theme(u)
   a=openai.chat.completions.create(model=DEEPSEEK_MODEL,messages=msgs,temperature=TEMPERATURE,max_tokens=MAX_TOKENS).choices[0].message.content
   
   # 检查LLM是否建议handoff
   if "[handoff]" in a:
    service = a.split("[handoff]")[1].strip().split()[0]
    return await s.mcp.handoff(
     service,
     task={
       "messages": s.messages[-5:],
       "query": u,
       "url": extract_url(u),
       "source": "llm",
       "input_type": "browser"
     }
    )
   
   s.messages+=[{"role":"user","content":u},{"role":"assistant","content":a}]
   s.save_log(u,a)
   if not s.dev_mode:
    faiss_add([
     {'role':'user','text':u,'time':get_current_datetime(),'file':datetime.now().strftime('%Y-%m-%d')+'.txt','theme':theme},
     {'role':'ai','text':a,'time':get_current_datetime(),'file':datetime.now().strftime('%Y-%m-%d')+'.txt','theme':theme}
    ])
   return a
  except Exception as e:
   import traceback;traceback.print_exc(file=sys.stderr)
   return f"[MCP异常]: {e}" 

async def process_user_message(s,msg):
    if vcfg.ENABLED and not msg: #无文本输入时启动语音识别
        async for text in s.voice.stt_stream():
            if text:msg=text;break
    return await s.process(msg)

async def send_ai_message(s,msg):
    if vcfg.ENABLED: #启用语音时转换为语音
        async for _ in s.voice.tts_stream(msg):pass
    return msg 
