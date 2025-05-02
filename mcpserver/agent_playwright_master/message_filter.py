from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import json

@dataclass
class HandoffMessage:
    """Handoff消息结构"""
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class FilteredMessages:
    """过滤后的消息结构"""
    messages: List[HandoffMessage]
    metadata: Dict[str, Any]

def filter_messages(messages: List[Dict[str, Any]], filter_type: str = "browser") -> str:
    """过滤消息的便捷函数
    
    Args:
        messages: 要过滤的消息列表
        filter_type: 过滤器类型，默认为"browser"
        
    Returns:
        str: JSON格式的过滤结果
    """
    filtered = []
    metadata = {
        "type": f"{filter_type}_messages",
        "total_messages": len(messages),
        "filtered_count": 0
    }
    
    # 浏览器相关关键词
    browser_keywords = [
        "bilibili", "b站", "浏览器", "网站", "打开", "访问",
        "youtube", "谷歌", "百度", "github"
    ]
    
    for msg in messages:
        if not isinstance(msg, dict):
            continue
            
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        # 跳过空消息
        if not role or not content:
            continue
            
        # 提取元数据
        msg_metadata = {
            k: v for k, v in msg.items() 
            if k not in ["role", "content"]
        }
        
        # 检查是否需要过滤
        should_include = True
        if filter_type == "browser":
            should_include = any(
                keyword in content.lower() 
                for keyword in browser_keywords
            )
            
        if should_include:
            metadata["filtered_count"] += 1
            msg_metadata["is_filtered"] = True
            
            # 创建消息对象
            filtered.append(HandoffMessage(
                role=role,
                content=content,
                metadata=msg_metadata
            ))
    
    # 转换为JSON格式
    result = FilteredMessages(messages=filtered, metadata=metadata)
    return json.dumps({
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                **(msg.metadata or {})
            }
            for msg in result.messages
        ],
        "metadata": result.metadata
    }, ensure_ascii=False) 