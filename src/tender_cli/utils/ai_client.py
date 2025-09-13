"""
AI 客户端
"""

import json
import re
from openai import OpenAI
from typing import Dict, Any, Optional, List, Callable
from .logger import get_logger

logger = get_logger(__name__)


class AIClient:
    """AI 客户端类"""
    
    def __init__(self, config: Dict[str, Any], mcp_server=None):
        self.config = config
        self.provider = config.get("provider", "openai")
        self.model = config.get("model", "gpt-4")
        self.api_key = config.get("api_key", "").strip()
        self.base_url = config.get("base_url", "").strip()
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4000)
        
        # MCP服务器
        self.mcp_server = mcp_server
        
        # 模拟模式标志 - 只有在既没有API密钥又没有base_url时才启用模拟模式
        self.mock_mode = not (bool(self.api_key) or bool(self.base_url))
        
        logger.info(f"AI Client initialized - API Key: {'***' if self.api_key else 'None'}, Base URL: {self.base_url or 'Default'}, Mock Mode: {self.mock_mode}, MCP: {'Yes' if mcp_server else 'No'}")
        
        # 初始化客户端
        if not self.mock_mode:
            self._init_client()
        
        # 注册MCP工具
        self._register_mcp_tools()
    
    def _init_client(self):
        """初始化AI客户端"""
        if self.provider == "openai":
            # 使用新版本的OpenAI客户端
            client_kwargs = {}
            
            # 如果有API密钥，使用它
            if self.api_key:
                client_kwargs["api_key"] = self.api_key
            else:
                # 如果没有API密钥但有自定义端点，使用一个占位符密钥
                client_kwargs["api_key"] = "sk-placeholder"
            
            # 如果有自定义base_url，使用它
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            
            self.client = OpenAI(**client_kwargs)
            logger.info(f"OpenAI client initialized with base_url: {self.base_url or 'default'}")
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")
    
    def _register_mcp_tools(self):
        """注册MCP工具"""
        if not self.mcp_server:
            self.available_tools = []
            return
        
        self.available_tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "读取文件内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "文件路径"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "write_file",
                    "description": "写入文件内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "文件路径"},
                            "content": {"type": "string", "description": "文件内容"}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "列出目录中的文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {"type": "string", "description": "目录路径"}
                        },
                        "required": ["directory"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_section_structure",
                    "description": "获取项目的章节结构",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_outline",
                    "description": "生成标书大纲",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "requirements": {"type": "string", "description": "招标要求"},
                            "tender_type": {"type": "string", "description": "招标类型"}
                        },
                        "required": ["requirements", "tender_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_subsection_content",
                    "description": "生成章节子内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "section": {"type": "string", "description": "章节名称"},
                            "subsection": {"type": "string", "description": "子章节名称"},
                            "requirements": {"type": "object", "description": "要求信息"}
                        },
                        "required": ["section", "subsection", "requirements"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "one_click_docx_export",
                    "description": "一键导出Word文档",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
        
        logger.info(f"Registered {len(self.available_tools)} MCP tools")
    
    def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """调用MCP工具"""
        if not self.mcp_server:
            return "MCP服务器未初始化"
        
        try:
            if tool_name == "read_file":
                result = self.mcp_server.read_file(arguments["path"])
            elif tool_name == "write_file":
                result = self.mcp_server.write_file(arguments["path"], arguments["content"])
            elif tool_name == "list_files":
                result = self.mcp_server.list_files(arguments["directory"])
            elif tool_name == "get_section_structure":
                result = self.mcp_server.get_section_structure()
            elif tool_name == "generate_outline":
                result = self.mcp_server.generate_outline(arguments["requirements"], arguments["tender_type"])
            elif tool_name == "generate_subsection_content":
                result = self.mcp_server.generate_subsection_content(
                    arguments["section"], arguments["subsection"], arguments["requirements"]
                )
            elif tool_name == "one_click_docx_export":
                result = self.mcp_server.one_click_docx_export()
            else:
                return f"未知的工具: {tool_name}"
            
            return json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, (dict, list)) else str(result)
            
        except Exception as e:
            logger.error(f"MCP tool call failed: {tool_name} - {e}")
            return f"工具调用失败: {str(e)}"
    
    def chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """发送聊天请求"""
        # 如果是模拟模式，返回模拟响应
        if self.mock_mode:
            return self._get_mock_response(prompt, system_prompt)
        
        try:
            messages = []
            
            if system_prompt:
                # 如果有MCP工具，在系统提示中说明可用工具
                if self.available_tools:
                    tool_descriptions = []
                    for tool in self.available_tools:
                        func = tool["function"]
                        tool_descriptions.append(f"- {func['name']}: {func['description']}")
                    
                    enhanced_system_prompt = f"""{system_prompt}

你可以使用以下工具来帮助用户：
{chr(10).join(tool_descriptions)}

当需要使用工具时，请在回复中包含类似这样的格式：
TOOL_CALL: tool_name(参数)

例如：
- TOOL_CALL: get_section_structure()
- TOOL_CALL: read_file(path="/path/to/file")
- TOOL_CALL: generate_outline(requirements="需求", tender_type="类型")"""
                    messages.append({"role": "system", "content": enhanced_system_prompt})
                else:
                    messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            if self.provider == "openai":
                logger.info(f"Sending request to model: {self.model}")
                
                # 构建请求参数
                request_params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "stream": False
                }
                
                # 尝试使用function calling
                if self.available_tools:
                    try:
                        request_params["tools"] = self.available_tools
                        request_params["tool_choice"] = "auto"
                        
                        response = self.client.chat.completions.create(**request_params)
                        message = response.choices[0].message
                        
                        # 如果AI想要调用工具
                        if hasattr(message, 'tool_calls') and message.tool_calls:
                            tool_results = []
                            
                            for tool_call in message.tool_calls:
                                tool_name = tool_call.function.name
                                try:
                                    arguments = json.loads(tool_call.function.arguments)
                                except json.JSONDecodeError:
                                    arguments = {}
                                
                                logger.info(f"AI calling tool: {tool_name} with args: {arguments}")
                                
                                # 调用MCP工具
                                tool_result = self._call_mcp_tool(tool_name, arguments)
                                tool_results.append(f"工具 {tool_name} 执行结果:\n{tool_result}")
                            
                            # 将工具结果添加到对话中，让AI生成最终回复
                            messages.append({
                                "role": "assistant", 
                                "content": message.content or "我将使用工具来帮助您。"
                            })
                            
                            for i, tool_call in enumerate(message.tool_calls):
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": tool_results[i]
                                })
                            
                            # 再次请求AI生成最终回复
                            final_response = self.client.chat.completions.create(
                                model=self.model,
                                messages=messages,
                                temperature=self.temperature,
                                max_tokens=self.max_tokens
                            )
                            
                            result = final_response.choices[0].message.content.strip()
                            logger.info(f"Received response from AI model (length: {len(result)})")
                            return result
                        else:
                            # 没有工具调用，检查文本中是否有工具调用指令
                            result = message.content.strip()
                            return self._process_text_tool_calls(result)
                    
                    except Exception as e:
                        logger.warning(f"Function calling failed, falling back to text parsing: {e}")
                        # 降级到普通聊天
                        request_params.pop("tools", None)
                        request_params.pop("tool_choice", None)
                
                # 普通聊天请求
                response = self.client.chat.completions.create(**request_params)
                result = response.choices[0].message.content.strip()
                
                # 检查文本中是否有工具调用指令
                result = self._process_text_tool_calls(result)
                
                logger.info(f"Received response from AI model (length: {len(result)})")
                return result
            
        except Exception as e:
            logger.error(f"AI chat request failed: {e}")
            if "api_key" in str(e).lower() or "authentication" in str(e).lower():
                return "⚠️ API密钥认证失败，请检查配置。"
            elif "connection" in str(e).lower() or "network" in str(e).lower():
                return f"⚠️ 网络连接失败，请检查端点 {self.base_url} 是否可访问。"
            else:
                return f"⚠️ AI服务调用失败: {str(e)}"
    
    def _process_text_tool_calls(self, text: str) -> str:
        """处理文本中的工具调用指令"""
        if not self.available_tools or "TOOL_CALL:" not in text:
            return text
        
        # 查找工具调用指令
        import re
        tool_call_pattern = r'TOOL_CALL:\s*(\w+)\((.*?)\)'
        matches = re.findall(tool_call_pattern, text)
        
        if not matches:
            return text
        
        result_parts = [text]
        
        for tool_name, args_str in matches:
            logger.info(f"Text-based tool call detected: {tool_name}({args_str})")
            
            # 解析参数
            arguments = {}
            if args_str.strip():
                try:
                    # 简单的参数解析
                    for arg in args_str.split(','):
                        if '=' in arg:
                            key, value = arg.split('=', 1)
                            key = key.strip().strip('"\'')
                            value = value.strip().strip('"\'')
                            arguments[key] = value
                except Exception as e:
                    logger.warning(f"Failed to parse arguments: {args_str}, error: {e}")
            
            # 调用工具
            tool_result = self._call_mcp_tool(tool_name, arguments)
            
            # 添加工具结果到回复中
            result_parts.append(f"\n\n**{tool_name} 执行结果：**\n{tool_result}")
        
        return "\n".join(result_parts)
    
    def _get_mock_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """获取模拟响应"""
        prompt_lower = prompt.lower()
        
        # 意图分析的模拟响应
        if "分析用户的意图" in prompt or "analyze" in prompt_lower:
            if "创建项目" in prompt or "create" in prompt_lower:
                return '''
{
    "intent": "create_project",
    "confidence": 0.9,
    "entities": {
        "project_name": "智慧城市建设项目"
    },
    "task_type": "simple",
    "requires_planning": false
}
'''
            elif "生成大纲" in prompt or "outline" in prompt_lower:
                return '''
{
    "intent": "generate_outline",
    "confidence": 0.9,
    "entities": {},
    "task_type": "simple",
    "requires_planning": false
}
'''
            elif "查看" in prompt or "view" in prompt_lower:
                return '''
{
    "intent": "view_content",
    "confidence": 0.8,
    "entities": {},
    "task_type": "simple",
    "requires_planning": false
}
'''
            elif "导出" in prompt or "export" in prompt_lower:
                return '''
{
    "intent": "export_document",
    "confidence": 0.9,
    "entities": {},
    "task_type": "simple",
    "requires_planning": false
}
'''
        
        # 一般对话的模拟响应
        return """
🤖 **模拟模式运行中**

由于未配置 API 密钥，当前运行在模拟模式下。

💡 **配置 API 密钥**：
1. 运行 `tender` 命令
2. 按提示输入 OpenAI API Key
3. 完成配置后即可使用完整功能

📝 **当前功能**：
- ✅ 项目管理（创建、列表、切换）
- ✅ 文件操作（读写、目录管理）
- ✅ 大纲生成（使用内置模板）
- ✅ Word文档导出
- ⚠️ AI内容生成（需要API密钥）

🚀 **开始使用**：即使在模拟模式下，您也可以体验大部分功能！
"""
    
    def generate_content(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """生成内容"""
        full_prompt = prompt
        
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            full_prompt = f"{context_str}\n\n{prompt}"
        
        return self.chat(full_prompt)
    
    def analyze_text(self, text: str, analysis_type: str = "general") -> Dict[str, Any]:
        """分析文本"""
        prompt = f"""
请分析以下文本并返回JSON格式的结果：

分析类型：{analysis_type}
文本内容：{text}

请提取关键信息并结构化返回。
"""
        
        response = self.chat(prompt)
        
        try:
            import json
            return json.loads(response)
        except:
            return {"raw_response": response}
    
    def is_available(self) -> bool:
        """检查AI服务是否可用"""
        if self.mock_mode:
            return True  # 模拟模式总是可用
        
        try:
            # 发送一个简单的测试请求
            test_response = self.chat("Hello", "You are a helpful assistant. Please respond with 'OK'.")
            is_ok = bool(test_response) and "⚠️" not in test_response and len(test_response.strip()) > 0
            logger.info(f"AI availability test: {'PASS' if is_ok else 'FAIL'} - Response: {test_response[:50]}...")
            return is_ok
        except Exception as e:
            logger.error(f"AI availability test failed: {e}")
            return False 