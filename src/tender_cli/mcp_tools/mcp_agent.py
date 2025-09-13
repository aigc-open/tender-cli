"""
MCP Agent - 使用真正的MCP协议集成工具
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic_ai import Agent, RunContext
from pydantic_ai.tools import Tool

from ..utils.logger import get_logger

logger = get_logger(__name__)


class MCPAgent:
    """使用MCP协议的AI代理"""
    
    def __init__(self, config: Dict[str, Any], workspace_dir: Path, project_manager=None, mcp_server=None):
        self.config = config
        self.workspace_dir = workspace_dir
        self.project_manager = project_manager
        self.mcp_server = mcp_server
        self.agent = None
        
        # 初始化代理
        self._init_agent()
    
    def _init_agent(self):
        """初始化AI代理"""
        try:
            # 构建模型配置
            model_config = self.config.get("model", "gpt-4")
            
            # 创建代理时需要传入完整的模型配置
            from pydantic_ai.models.openai import OpenAIChatModel
            from pydantic_ai.providers.openai import OpenAIProvider
            
            # 如果有自定义端点，创建自定义模型
            if self.config.get("base_url"):
                # 创建自定义provider
                provider = OpenAIProvider(
                    api_key=self.config.get("api_key", "sk-placeholder"),
                    base_url=self.config.get("base_url")
                )
                model = OpenAIChatModel(
                    model_name=self.config.get("model", "gpt-4"),
                    provider=provider
                )
            else:
                model = model_config
            
            # 创建代理
            self.agent = Agent(
                model=model,
                instructions=f"""你是Tender AI，一个专业的标书智能助手。

当前工作目录：{self.workspace_dir}

你可以帮助用户：
1. 管理标书项目（创建、切换、列出项目）
2. 生成标书大纲和内容
3. 管理项目文件和目录
4. 导出专业文档

重要：当用户提出需求时，你必须主动使用相应的工具来完成任务。

如果function calling不可用，请在回复中使用以下格式来调用工具：
TOOL_CALL: tool_name(参数名=参数值)

可用工具：
- create_project(name="项目名称") - 创建新项目
- list_projects() - 列出所有项目
- switch_project(name="项目名称") - 切换项目
- get_project_structure() - 查看项目结构
- generate_outline(requirements="需求", tender_type="类型") - 生成大纲
- read_file(path="文件路径") - 读取文件
- write_file(path="文件路径", content="内容") - 写入文件
- list_files(path="目录路径") - 列出文件
- create_directory(path="目录路径") - 创建目录
- export_docx() - 导出Word文档

例如：
用户："做一个智能汽车标书"
回复："我将为您创建智能汽车标书项目。
TOOL_CALL: create_project(name="智能汽车标书")
项目创建完成后，我们可以继续生成大纲。"

请根据用户需求，立即执行相应的操作。"""
            )
            
            # 注册工具
            self._register_tools()
            
            logger.info("Agent initialized successfully with tools")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            self.agent = None
    
    def _register_tools(self):
        """注册工具到代理"""
        if not self.agent:
            return
        
        # 保存self引用以便在嵌套函数中使用
        project_manager = self.project_manager
        mcp_server = self.mcp_server
        workspace_dir = self.workspace_dir
        
        # 项目管理工具
        @self.agent.tool
        def create_project(ctx: RunContext, name: str) -> str:
            """创建新的标书项目"""
            try:
                if project_manager:
                    project_manager.create_project(name)
                    return f"✅ 项目 '{name}' 创建成功！"
                else:
                    return "❌ 项目管理器未初始化"
            except Exception as e:
                if "已存在" in str(e):
                    try:
                        project_manager.switch_project(name)
                        return f"✅ 项目 '{name}' 已存在，已切换到该项目。"
                    except:
                        return f"❌ 项目 '{name}' 已存在但切换失败"
                return f"❌ 创建项目失败: {str(e)}"
        
        @self.agent.tool
        def list_projects(ctx: RunContext) -> str:
            """列出所有项目"""
            try:
                if project_manager:
                    projects = project_manager.list_projects()
                    if not projects:
                        return "📁 暂无项目"
                    
                    current = project_manager.current_project_name
                    project_list = []
                    for project in projects:
                        status = "🟢 当前" if project == current else "⚪"
                        project_list.append(f"• {status} {project}")
                    
                    return f"📁 项目列表:\n{chr(10).join(project_list)}"
                else:
                    return "❌ 项目管理器未初始化"
            except Exception as e:
                return f"❌ 获取项目列表失败: {str(e)}"
        
        @self.agent.tool
        def switch_project(ctx: RunContext, name: str) -> str:
            """切换到指定项目"""
            try:
                if project_manager:
                    project_manager.switch_project(name)
                    return f"✅ 已切换到项目 '{name}'"
                else:
                    return "❌ 项目管理器未初始化"
            except Exception as e:
                return f"❌ 切换项目失败: {str(e)}"
        
        @self.agent.tool
        def get_project_structure(ctx: RunContext) -> str:
            """获取当前项目的文件结构"""
            try:
                if project_manager and project_manager.current_project_name:
                    structure = project_manager.get_project_structure()
                    return f"📁 项目结构 - {project_manager.current_project_name}:\n{structure}"
                else:
                    return "📁 当前无活动项目"
            except Exception as e:
                return f"❌ 获取项目结构失败: {str(e)}"
        
        # 大纲生成工具
        @self.agent.tool
        def generate_outline(ctx: RunContext, requirements: str = "标准标书", tender_type: str = "综合类") -> str:
            """生成标书大纲"""
            try:
                if mcp_server:
                    result = mcp_server.generate_outline(requirements, tender_type)
                    
                    # 保存大纲到项目
                    if project_manager and project_manager.current_project_name:
                        project_manager.save_outline(result)
                    
                    # 格式化输出
                    outline_text = []
                    for i, section in enumerate(result.get("sections", []), 1):
                        outline_text.append(f"{i}. {section['title']}")
                        for j, subsection in enumerate(section.get("subsections", []), 1):
                            outline_text.append(f"  {i}.{j} {subsection}")
                    
                    return f"📝 标书大纲生成完成！\n\n{chr(10).join(outline_text)}\n\n✅ 大纲已保存到项目"
                else:
                    return "❌ MCP服务器未初始化"
            except Exception as e:
                return f"❌ 生成大纲失败: {str(e)}"
        
        # 文件操作工具
        @self.agent.tool
        def read_file(ctx: RunContext, path: str) -> str:
            """读取文件内容"""
            try:
                full_path = workspace_dir / path
                if not full_path.exists():
                    return f"❌ 文件不存在: {path}"
                
                content = full_path.read_text(encoding='utf-8')
                return f"📄 文件内容 ({path}):\n{content}"
            except Exception as e:
                return f"❌ 读取文件失败: {str(e)}"
        
        @self.agent.tool
        def write_file(ctx: RunContext, path: str, content: str) -> str:
            """写入文件内容"""
            try:
                full_path = workspace_dir / path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding='utf-8')
                return f"✅ 文件写入成功: {path}"
            except Exception as e:
                return f"❌ 写入文件失败: {str(e)}"
        
        @self.agent.tool
        def list_files(ctx: RunContext, path: str = ".") -> str:
            """列出目录中的文件"""
            try:
                full_path = workspace_dir / path
                if not full_path.exists():
                    return f"❌ 目录不存在: {path}"
                
                if full_path.is_file():
                    return f"📄 {path} 是一个文件"
                
                files = []
                for item in full_path.iterdir():
                    if item.is_dir():
                        files.append(f"📁 {item.name}/")
                    else:
                        files.append(f"📄 {item.name}")
                
                if not files:
                    return f"📁 目录为空: {path}"
                
                return f"📁 目录内容 ({path}):\n" + "\n".join(files)
            except Exception as e:
                return f"❌ 列出文件失败: {str(e)}"
        
        @self.agent.tool
        def create_directory(ctx: RunContext, path: str) -> str:
            """创建目录"""
            try:
                full_path = workspace_dir / path
                full_path.mkdir(parents=True, exist_ok=True)
                return f"✅ 目录创建成功: {path}"
            except Exception as e:
                return f"❌ 创建目录失败: {str(e)}"
        
        # 文档导出工具
        @self.agent.tool
        def export_docx(ctx: RunContext) -> str:
            """导出Word文档"""
            try:
                if mcp_server:
                    result = mcp_server.one_click_docx_export()
                    if result.get("success"):
                        return f"✅ Word文档导出成功！\n文件路径: {result.get('file_path', '未知')}"
                    else:
                        return f"❌ 导出失败: {result.get('error', '未知错误')}"
                else:
                    return "❌ MCP服务器未初始化"
            except Exception as e:
                return f"❌ 导出文档失败: {str(e)}"
        
        # 内容生成工具
        @self.agent.tool
        def generate_section_content(ctx: RunContext, section: str, subsection: str, requirements: str = "") -> str:
            """生成章节内容"""
            try:
                if mcp_server:
                    req_dict = {"requirements": requirements} if requirements else {}
                    content = mcp_server.generate_subsection_content(section, subsection, req_dict)
                    
                    # 保存内容到文件
                    if project_manager and project_manager.current_project_name:
                        project_manager.save_subsection(section, subsection, content)
                    
                    return f"✅ 章节内容生成完成！\n\n{content[:200]}...\n\n已保存到项目文件"
                else:
                    return "❌ MCP服务器未初始化"
            except Exception as e:
                return f"❌ 生成内容失败: {str(e)}"
    
    async def chat(self, message: str) -> str:
        """与AI代理对话"""
        if not self.agent:
            return "⚠️ AI代理未初始化，请检查配置。"
        
        try:
            # 运行代理
            result = await self.agent.run(message)
            # pydantic-ai的结果对象使用output属性
            response = str(result.output) if hasattr(result, 'output') else str(result)
            
            # 处理文本中的工具调用（降级方案）
            response = self._process_text_tool_calls(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return f"⚠️ 对话失败: {str(e)}"
    
    def _process_text_tool_calls(self, text: str) -> str:
        """处理文本中的工具调用指令"""
        if "TOOL_CALL:" not in text:
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
            tool_result = self._call_tool_directly(tool_name, arguments)
            
            # 替换工具调用为结果
            tool_call_text = f"TOOL_CALL: {tool_name}({args_str})"
            text = text.replace(tool_call_text, f"\n\n**{tool_name} 执行结果：**\n{tool_result}")
        
        return text
    
    def _call_tool_directly(self, tool_name: str, arguments: dict) -> str:
        """直接调用工具函数"""
        try:
            if tool_name == "create_project":
                name = arguments.get("name", "新项目")
                if self.project_manager:
                    self.project_manager.create_project(name)
                    return f"✅ 项目 '{name}' 创建成功！"
                else:
                    return "❌ 项目管理器未初始化"
                    
            elif tool_name == "list_projects":
                if self.project_manager:
                    projects = self.project_manager.list_projects()
                    if not projects:
                        return "📁 暂无项目"
                    
                    current = self.project_manager.current_project_name
                    project_list = []
                    for project in projects:
                        status = "🟢 当前" if project == current else "⚪"
                        project_list.append(f"• {status} {project}")
                    
                    return f"📁 项目列表:\n{chr(10).join(project_list)}"
                else:
                    return "❌ 项目管理器未初始化"
                    
            elif tool_name == "switch_project":
                name = arguments.get("name", "")
                if self.project_manager and name:
                    self.project_manager.switch_project(name)
                    return f"✅ 已切换到项目 '{name}'"
                else:
                    return "❌ 项目管理器未初始化或项目名为空"
                    
            elif tool_name == "get_project_structure":
                if self.project_manager and self.project_manager.current_project_name:
                    structure = self.project_manager.get_project_structure()
                    return f"📁 项目结构 - {self.project_manager.current_project_name}:\n{structure}"
                else:
                    return "📁 当前无活动项目"
                    
            elif tool_name == "generate_outline":
                requirements = arguments.get("requirements", "标准标书")
                tender_type = arguments.get("tender_type", "综合类")
                if self.mcp_server:
                    result = self.mcp_server.generate_outline(requirements, tender_type)
                    
                    # 保存大纲到项目
                    if self.project_manager and self.project_manager.current_project_name:
                        self.project_manager.save_outline(result)
                    
                    # 格式化输出
                    outline_text = []
                    for i, section in enumerate(result.get("sections", []), 1):
                        outline_text.append(f"{i}. {section['title']}")
                        for j, subsection in enumerate(section.get("subsections", []), 1):
                            outline_text.append(f"  {i}.{j} {subsection}")
                    
                    return f"📝 标书大纲生成完成！\n\n{chr(10).join(outline_text)}\n\n✅ 大纲已保存到项目"
                else:
                    return "❌ MCP服务器未初始化"
                    
            elif tool_name == "read_file":
                path = arguments.get("path", "")
                if path:
                    full_path = self.workspace_dir / path
                    if full_path.exists():
                        content = full_path.read_text(encoding='utf-8')
                        return f"📄 文件内容 ({path}):\n{content}"
                    else:
                        return f"❌ 文件不存在: {path}"
                else:
                    return "❌ 文件路径为空"
                    
            elif tool_name == "list_files":
                path = arguments.get("path", ".")
                full_path = self.workspace_dir / path
                if full_path.exists():
                    if full_path.is_file():
                        return f"📄 {path} 是一个文件"
                    
                    files = []
                    for item in full_path.iterdir():
                        if item.is_dir():
                            files.append(f"📁 {item.name}/")
                        else:
                            files.append(f"📄 {item.name}")
                    
                    if not files:
                        return f"📁 目录为空: {path}"
                    
                    return f"📁 目录内容 ({path}):\n" + "\n".join(files)
                else:
                    return f"❌ 目录不存在: {path}"
                    
            elif tool_name == "export_docx":
                if self.mcp_server:
                    result = self.mcp_server.one_click_docx_export()
                    if result.get("success"):
                        return f"✅ Word文档导出成功！\n文件路径: {result.get('file_path', '未知')}"
                    else:
                        return f"❌ 导出失败: {result.get('error', '未知错误')}"
                else:
                    return "❌ MCP服务器未初始化"
                    
            else:
                return f"❌ 未知工具: {tool_name}"
                
        except Exception as e:
            logger.error(f"Direct tool call failed: {tool_name} - {e}")
            return f"❌ 工具调用失败: {str(e)}"
    
    def chat_sync(self, message: str) -> str:
        """同步版本的对话方法"""
        try:
            return asyncio.run(self.chat(message))
        except Exception as e:
            logger.error(f"Sync chat failed: {e}")
            return f"⚠️ 对话失败: {str(e)}"
    
    def is_available(self) -> bool:
        """检查代理是否可用"""
        return self.agent is not None


# 保留简化的MCP工具作为降级选项
class SimpleMCPTools:
    """简化的MCP工具集合"""
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """调用工具"""
        try:
            if tool_name == "read_file":
                return self._read_file(arguments["path"])
            elif tool_name == "write_file":
                return self._write_file(arguments["path"], arguments["content"])
            elif tool_name == "list_files":
                return self._list_files(arguments.get("path", "."))
            elif tool_name == "create_directory":
                return self._create_directory(arguments["path"])
            else:
                return f"未知工具: {tool_name}"
        except Exception as e:
            logger.error(f"Tool call failed: {tool_name} - {e}")
            return f"工具调用失败: {str(e)}"
    
    def _read_file(self, path: str) -> str:
        """读取文件"""
        try:
            full_path = self.workspace_dir / path
            if not full_path.exists():
                return f"文件不存在: {path}"
            
            content = full_path.read_text(encoding='utf-8')
            return f"文件内容 ({path}):\n{content}"
        except Exception as e:
            return f"读取文件失败: {str(e)}"
    
    def _write_file(self, path: str, content: str) -> str:
        """写入文件"""
        try:
            full_path = self.workspace_dir / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            return f"文件写入成功: {path}"
        except Exception as e:
            return f"写入文件失败: {str(e)}"
    
    def _list_files(self, path: str) -> str:
        """列出文件"""
        try:
            full_path = self.workspace_dir / path
            if not full_path.exists():
                return f"目录不存在: {path}"
            
            if full_path.is_file():
                return f"{path} 是一个文件"
            
            files = []
            for item in full_path.iterdir():
                if item.is_dir():
                    files.append(f"📁 {item.name}/")
                else:
                    files.append(f"📄 {item.name}")
            
            if not files:
                return f"目录为空: {path}"
            
            return f"目录内容 ({path}):\n" + "\n".join(files)
        except Exception as e:
            return f"列出文件失败: {str(e)}"
    
    def _create_directory(self, path: str) -> str:
        """创建目录"""
        try:
            full_path = self.workspace_dir / path
            full_path.mkdir(parents=True, exist_ok=True)
            return f"目录创建成功: {path}"
        except Exception as e:
            return f"创建目录失败: {str(e)}" 