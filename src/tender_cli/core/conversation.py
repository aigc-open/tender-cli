"""
对话管理模块
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class ConversationManager:
    """对话管理器"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.messages: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """添加消息到对话历史"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.messages.append(message)
        
        # 保持历史记录在限制范围内
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取最近的消息"""
        return self.messages[-count:]
    
    def get_context_for_ai(self) -> str:
        """获取用于AI的上下文"""
        recent_messages = self.get_recent_messages(5)
        
        context_parts = []
        for msg in recent_messages:
            role = msg["role"]
            content = msg["content"]
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def set_context(self, key: str, value: Any):
        """设置上下文信息"""
        self.context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文信息"""
        return self.context.get(key, default)
    
    def clear_history(self):
        """清空对话历史"""
        self.messages.clear()
    
    def save_to_file(self, file_path: Path):
        """保存对话到文件"""
        data = {
            "messages": self.messages,
            "context": self.context,
            "saved_at": datetime.now().isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, file_path: Path):
        """从文件加载对话"""
        if not file_path.exists():
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.messages = data.get("messages", [])
            self.context = data.get("context", {})
        except Exception as e:
            # 如果加载失败，保持当前状态
            pass
    
    def get_summary(self) -> Dict[str, Any]:
        """获取对话摘要"""
        total_messages = len(self.messages)
        user_messages = len([m for m in self.messages if m["role"] == "user"])
        assistant_messages = len([m for m in self.messages if m["role"] == "assistant"])
        
        return {
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "start_time": self.messages[0]["timestamp"] if self.messages else None,
            "last_time": self.messages[-1]["timestamp"] if self.messages else None
        } 