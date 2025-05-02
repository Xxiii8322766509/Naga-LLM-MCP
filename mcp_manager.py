import asyncio
import logging
import inspect
from typing import Dict, Optional, List, Any, Callable, Awaitable, Generic, TypeVar, Union, cast
from contextlib import AsyncExitStack
import sys
from pydantic import BaseModel, TypeAdapter
from dataclasses import dataclass
import json
from datetime import datetime

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config import MCP_SERVICES, DEBUG, LOG_LEVEL

# 配置日志
logging.basicConfig(
    level=logging.DEBUG if DEBUG else getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MCPManager")

_builtin_print=print
print=lambda *a,**k:sys.stderr.write('[print] '+(' '.join(map(str,a)))+'\n')

TContext = TypeVar("TContext")
THandoffInput = TypeVar("THandoffInput")

class HandoffError(Exception):
    """Handoff基础异常类"""
    pass

class ModelBehaviorError(HandoffError):
    """模型行为异常"""
    pass

class HandoffValidationError(HandoffError):
    """Handoff数据验证异常"""
    pass

class HandoffConnectionError(HandoffError):
    """Handoff连接异常"""
    pass

@dataclass
class HandoffInputData:
    """Handoff输入数据结构"""
    input_history: Union[str, tuple[Any, ...]] #历史输入
    pre_handoff_items: tuple[Any, ...] #handoff前的items
    new_items: tuple[Any, ...] #当前turn生成的items
    context: Optional[Dict[str, Any]] = None #上下文数据
    metadata: Optional[Dict[str, Any]] = None #元数据

    @classmethod
    def create(cls, 
        input_history: Any = None,
        pre_items: Any = None,
        new_items: Any = None,
        context: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> 'HandoffInputData':
        """创建HandoffInputData实例"""
        return cls(
            input_history=input_history if input_history is not None else (),
            pre_handoff_items=pre_items if pre_items is not None else (),
            new_items=new_items if new_items is not None else (),
            context=context,
            metadata=metadata
        )

def remove_tools_filter(messages: list) -> list:
    """移除工具调用的过滤器函数"""
    return [
        msg for msg in messages
        if not any(tool in str(msg) for tool in ["[tool]", "[handoff]"])
    ]

@dataclass
class Handoff(Generic[TContext]):
    """Handoff配置类"""
    tool_name: str
    tool_description: str
    input_json_schema: dict[str, Any]
    agent_name: str
    on_invoke_handoff: Callable[[Any, str], Awaitable[Any]]
    strict_json_schema: bool = True
    
    async def invoke(self, ctx: Any, input_json: Optional[str] = None) -> Any:
        """执行handoff调用"""
        if self.input_json_schema and not input_json:
            raise ModelBehaviorError("Handoff需要输入但未提供")
            
        try:
            if input_json:
                # 验证输入
                type_adapter = TypeAdapter(dict[str, Any])
                validated_input = type_adapter.validate_json(
                    input_json,
                    strict=self.strict_json_schema
                )
            else:
                validated_input = None
                
            # 验证回调函数签名
            sig = inspect.signature(self.on_invoke_handoff)
            if len(sig.parameters) != 2:
                raise HandoffValidationError(
                    "Handoff回调函数必须接受两个参数(context, input)"
                )
                
            return await self.on_invoke_handoff(ctx, validated_input)
        except Exception as e:
            if isinstance(e, HandoffError):
                raise
            raise HandoffError(f"Handoff执行失败: {str(e)}")

class MCPManager:
    """MCP服务管理器，负责管理所有MCP服务的连接和调用"""
    
    def __init__(self):
        """初始化MCP管理器"""
        self.services = {}
        self.tools_cache = {}
        self.exit_stack = AsyncExitStack()
        self.handoffs = {} # 服务对应的handoff对象
        self.handoff_filters = {} # 服务对应的handoff过滤器
        self.handoff_callbacks = {} # 服务对应的handoff回调
        self.logger = logging.getLogger("MCPManager")
        sys.stderr.write("MCPManager初始化\n")
        
    def register_handoff(
        self,
        service_name: str,
        tool_name: str,
        tool_description: str,
        input_schema: dict,
        agent_name: str,
        filters=None,
        strict_schema=False
    ):
        """注册handoff服务"""
        sys.stderr.write(f"注册服务: {service_name}, agent: {agent_name}\n")
        self.services[service_name] = {
            "tool_name": tool_name,
            "tool_description": tool_description,
            "input_schema": input_schema,
            "agent_name": agent_name,
            "filter_fn": remove_tools_filter,  # 使用函数而不是类实例
            "strict_schema": strict_schema
        }
        sys.stderr.write(f"当前已注册服务: {list(self.services.keys())}\n")
        
    async def _default_handoff_callback(
        self,
        ctx: Any,
        input_json: Optional[str]
    ) -> Any:
        """默认的handoff回调处理"""
        return None
            
    async def handoff(
        self,
        service_name: str,
        task: dict,
        input_history: Any = None,
        pre_items: Any = None,
        new_items: Any = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """执行handoff"""
        try:
            sys.stderr.write(f"执行handoff: service={service_name}, task={json.dumps(task, ensure_ascii=False)}\n")
            
            if service_name not in self.services:
                raise ValueError(f"未注册的服务: {service_name}")
                
            service = self.services[service_name]
            # 只打印服务配置中的安全字段
            safe_service_info = {
                "name": service.get("name", ""),
                "description": service.get("description", ""),
                "agent_name": service.get("agent_name", ""),
                "strict_schema": service.get("strict_schema", False)
            }
            sys.stderr.write(f"找到服务配置: {json.dumps(safe_service_info, ensure_ascii=False)}\n")
            
            # 简单验证必需字段
            if service["strict_schema"]:
                required_fields = service["input_schema"].get("required", [])
                for field in required_fields:
                    if field not in task:
                        raise ValueError(f"缺少必需字段: {field}")
                
            # 应用过滤器函数
            if "messages" in task and service["filter_fn"]:
                try:
                    task["messages"] = service["filter_fn"](task["messages"])
                except Exception as e:
                    sys.stderr.write(f"消息过滤失败: {e}\n")
                    # 继续执行，使用原始消息
                
            # 创建代理实例
            agent_class = self._get_agent_class(service["agent_name"])
            if not agent_class:
                raise ValueError(f"找不到代理类: {service['agent_name']}")
                
            sys.stderr.write(f"创建代理实例: {service['agent_name']}\n")
            agent = agent_class()
            
            # 执行handoff
            sys.stderr.write("开始执行代理handoff\n")
            result = await agent.handle_handoff(task)
            sys.stderr.write(f"代理handoff执行结果: {result}\n")
            
            return result
            
        except Exception as e:
            error_msg = f"Handoff执行失败: {str(e)}"
            sys.stderr.write(f"{error_msg}\n")
            import traceback
            traceback.print_exc(file=sys.stderr)
            return json.dumps({
                "status": "error",
                "message": error_msg
            }, ensure_ascii=False)
            
    def _get_agent_class(self, agent_name: str):
        """获取代理类"""
        # 导入代理类
        try:
            from mcpserver.agent_playwright_master import PlaywrightAgent
            
            agent_map = {
                "Playwright Browser Agent": PlaywrightAgent
            }
            
            return agent_map.get(agent_name)
            
        except ImportError as e:
            sys.stderr.write(f"导入代理类失败: {e}\n")
            return None
            
    async def connect_service(self, service_name: str) -> Optional[ClientSession]:
        """连接到指定的MCP服务
        
        Args:
            service_name: MCP服务名称
            
        Returns:
            Optional[ClientSession]: 成功返回会话对象，失败返回None
        """
        # 检查服务是否存在且启用
        if service_name not in MCP_SERVICES or not MCP_SERVICES[service_name]["enabled"]:
            logger.warning(f"MCP服务 {service_name} 不存在或未启用")
            return None
            
        # 如果已连接，直接返回会话
        if service_name in self.services:
            return self.services[service_name]
            
        service_config = MCP_SERVICES[service_name]
        command = "python" if service_config["type"] == "python" else "node"
        
        try:
            logger.info(f"正在连接MCP服务: {service_name}")
            server_params = StdioServerParameters(
                command=command,
                args=[service_config["script_path"]],
                env=None
            )
            
            # 创建服务连接
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport
            
            # 创建并初始化会话
            session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )
            await session.initialize()
            
            # 缓存会话
            self.services[service_name] = session
            logger.info(f"MCP服务 {service_name} 连接成功")
            return session
            
        except Exception as e:
            logger.error(f"连接MCP服务 {service_name} 失败: {str(e)}")
            import traceback;traceback.print_exc(file=sys.stderr)
            return None
            
    async def get_service_tools(self, service_name: str) -> list:
        """获取指定MCP服务的可用工具列表
        
        Args:
            service_name: MCP服务名称
            
        Returns:
            list: 工具列表
        """
        # 检查缓存
        if service_name in self.tools_cache:
            return self.tools_cache[service_name]
            
        session = await self.connect_service(service_name)
        if not session:
            return []
            
        try:
            response = await session.list_tools()
            tools = response.tools
            # 缓存工具列表
            self.tools_cache[service_name] = tools
            return tools
        except Exception as e:
            logger.error(f"获取服务 {service_name} 的工具列表失败: {str(e)}")
            import traceback;traceback.print_exc(file=sys.stderr)
            return []
            
    async def call_service_tool(self, service_name: str, tool_name: str, args: dict):
        """调用指定MCP服务的工具
        
        Args:
            service_name: MCP服务名称
            tool_name: 工具名称
            args: 工具参数
            
        Returns:
            工具调用结果
        """
        session = await self.connect_service(service_name)
        if not session:
            return None
            
        try:
            logger.debug(f"调用工具: {service_name}.{tool_name} 参数: {args}")
            result = await session.call_tool(tool_name, args)
            logger.debug(f"工具调用结果: {result}")
            return result
        except Exception as e:
            logger.error(f"调用工具 {service_name}.{tool_name} 失败: {str(e)}")
            import traceback;traceback.print_exc(file=sys.stderr)
            return None
            
    def get_available_services(self) -> list:
        """获取所有可用的MCP服务列表
        
        Returns:
            list: 可用服务列表
        """
        return [
            {"name": c["name"], "description": c["description"], "id": k}
            for k, c in MCP_SERVICES.items() if c["enabled"]
        ]
            
    def format_available_services(self) -> str:
        """格式化可用服务列表为字符串
        
        Returns:
            str: 格式化后的服务列表字符串
        """
        return "\n".join([
            f"- {name}: {info['tool_description']}"
            for name, info in self.services.items()
        ])
            
    async def cleanup(self):
        """清理所有MCP服务连接"""
        logger.info("正在清理MCP服务连接...")
        try:
            await self.exit_stack.aclose()
            self.services.clear();self.tools_cache.clear()
            logger.info("MCP服务连接清理完成")
        except Exception as e:
            logger.error(f"清理MCP服务连接时出错: {str(e)}")
            import traceback;traceback.print_exc(file=sys.stderr) 