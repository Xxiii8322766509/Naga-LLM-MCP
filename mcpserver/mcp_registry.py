# mcp_registry.py # 自动注册所有MCP服务
import importlib,inspect,os
from pathlib import Path

MCP_REGISTRY={} # 全局MCP服务池

def auto_register_mcp(mcp_dir='mcpserver'):
 d=Path(mcp_dir)
 for f in d.glob('**/*.py'):
  if f.stem.startswith('__'):continue
  m=importlib.import_module(f'{f.parent.as_posix().replace("/", ".")}.{f.stem}')
  for n,o in inspect.getmembers(m,inspect.isclass):
   if n.endswith('Agent') or n.endswith('Tool'):
    try:
     MCP_REGISTRY[n]=o() # 只注册能无参实例化的
    except Exception: pass # 跳过需要参数的

auto_register_mcp() 