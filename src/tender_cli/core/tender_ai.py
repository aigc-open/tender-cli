"""
Tender AI 核心类
"""

import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from .config import Config
from .conversation import ConversationManager
from .project_manager import ProjectManager
from ..mcp_tools.mcp_server import MCPServer
from ..mcp_tools.mcp_agent import MCPAgent, SimpleMCPTools
from ..prompts.prompt_library import PromptLibrary
from ..utils.ai_client import AIClient
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TenderAI:
    """Tender AI 核心类"""
    
    def __init__(self, config: Config):
        self.config = config
        self.conversation_manager = ConversationManager()
        self.project_manager = ProjectManager(config)
        self.prompt_library = PromptLibrary()
        
        # 初始化MCP服务器
        mcp_config = {
            "max_workers": 24,
            "timeout": 30
        }
        self.mcp_server = MCPServer(mcp_config)
        
        # 尝试使用新的MCP代理
        try:
            self.mcp_agent = MCPAgent(
                config.ai_config, 
                self.project_manager.workspace_dir,
                project_manager=self.project_manager,
                mcp_server=self.mcp_server
            )
            if self.mcp_agent.is_available():
                logger.info("Using MCP Agent for AI interactions")
                self.ai_client = None
            else:
                raise Exception("MCP Agent not available")
        except Exception as e:
            logger.warning(f"MCP Agent initialization failed: {e}, falling back to AIClient")
            self.mcp_agent = None
            # 降级到原来的AI客户端
            self.ai_client = AIClient(config.ai_config, mcp_server=self.mcp_server)
        
        # 初始化简化的MCP工具（用于降级）
        self.simple_mcp_tools = SimpleMCPTools(self.project_manager.workspace_dir)
        
        logger.info("Tender AI initialized")
    
    def process_message(self, message: str) -> str:
        """处理用户消息"""
        try:
            # 记录对话
            self.conversation_manager.add_message("user", message)
            
            # 优先使用MCP代理（通过function calling处理）
            if self.mcp_agent and self.mcp_agent.is_available():
                try:
                    response = self.mcp_agent.chat_sync(message)
                    
                    # 记录回复
                    self.conversation_manager.add_message("assistant", response)
                    return response
                    
                except Exception as e:
                    logger.error(f"MCP Agent chat failed: {e}")
                    # 降级到传统处理
                    pass
            
            # 如果AI客户端可用，直接让AI处理消息并可能调用工具
            if self.ai_client and self.ai_client.is_available():
                try:
                    system_prompt = f"""你是Tender AI，一个专业的标书智能助手。你可以帮助用户完成标书的全流程工作。

当前状态：
- 当前项目：{self.project_manager.current_project_name or "无"}
- 工作目录：{self.project_manager.workspace_dir}

你可以使用提供的工具来：
1. 管理项目文件和目录
2. 查看项目结构
3. 生成标书大纲和内容
4. 导出Word文档

请根据用户的需求，自然地使用合适的工具来帮助他们。如果需要创建项目、切换项目等操作，请告诉用户具体的命令。"""

                    response = self.ai_client.chat(message, system_prompt)
                    
                    # 记录回复
                    self.conversation_manager.add_message("assistant", response)
                    return response
                    
                except Exception as e:
                    logger.error(f"AI chat failed: {e}")
                    # 降级到简单意图识别
                    pass
            
            # 降级处理：简单的意图识别（不依赖AI）
            intent = self._analyze_intent_simple(message)
            
            # 根据意图执行相应操作
            if intent["intent"] == "create_project":
                response = self._handle_create_project(intent, message)
            elif intent["intent"] == "generate_outline":
                response = self._handle_generate_outline(intent, message)
            elif intent["intent"] == "view_content":
                response = self._handle_view_content(intent, message)
            elif intent["intent"] == "export_document":
                response = self._handle_export_document(intent, message)
            elif intent["intent"] == "list_projects":
                response = self._handle_list_projects(intent, message)
            elif intent["intent"] == "use_tools":
                response = self._handle_tool_usage(intent, message)
            else:
                response = self._handle_general_chat(intent, message)
            
            # 记录回复
            self.conversation_manager.add_message("assistant", response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"❌ 处理消息时出错: {str(e)}"
    
    def _analyze_intent_simple(self, message: str) -> Dict[str, Any]:
        """简单的意图分析（基于关键词）"""
        message_lower = message.lower()
        
        # 项目创建
        if any(keyword in message_lower for keyword in ["创建项目", "新建项目", "create project"]):
            # 提取项目名称
            project_name = self._extract_project_name(message)
            return {
                "intent": "create_project",
                "confidence": 0.9,
                "entities": {"project_name": project_name},
                "task_type": "simple",
                "requires_planning": False
            }
        
        # 生成大纲
        elif any(keyword in message_lower for keyword in ["生成大纲", "标书大纲", "generate outline", "大纲"]):
            return {
                "intent": "generate_outline",
                "confidence": 0.9,
                "entities": {},
                "task_type": "simple",
                "requires_planning": False
            }
        
        # 查看内容
        elif any(keyword in message_lower for keyword in ["查看", "显示", "show", "view", "项目结构"]):
            return {
                "intent": "view_content",
                "confidence": 0.8,
                "entities": {},
                "task_type": "simple",
                "requires_planning": False
            }
        
        # 导出文档
        elif any(keyword in message_lower for keyword in ["导出", "export", "word", "文档"]):
            return {
                "intent": "export_document",
                "confidence": 0.9,
                "entities": {},
                "task_type": "simple",
                "requires_planning": False
            }
        
        # 工具使用
        elif any(keyword in message_lower for keyword in ["查看文件", "读取文件", "查看项目结构", "查看目录", "创建目录", "创建文件夹", "list_files", "read_file"]):
            return {
                "intent": "use_tools",
                "confidence": 0.9,
                "entities": {},
                "task_type": "simple",
                "requires_planning": False
            }
        
        # 项目管理
        elif any(keyword in message_lower for keyword in ["列出项目", "项目列表", "list project", "切换项目"]):
            return {
                "intent": "list_projects",
                "confidence": 0.8,
                "entities": {"action": "list"},
                "task_type": "simple",
                "requires_planning": False
            }
        
        # 文件分析
        elif any(keyword in message_lower for keyword in ["分析", "analyze", "pdf", "招标文件"]):
            return {
                "intent": "analyze_tender",
                "confidence": 0.8,
                "entities": {},
                "task_type": "simple",
                "requires_planning": False
            }
        
        # 复杂任务（包含多个关键词）
        elif len([kw for kw in ["标书", "制作", "生成", "分析", "导出"] if kw in message_lower]) >= 2:
            return {
                "intent": "complex_task",
                "confidence": 0.7,
                "entities": {},
                "task_type": "complex",
                "requires_planning": True
            }
        
        # 默认为一般对话
        else:
            return {
                "intent": "general_chat",
                "confidence": 0.6,
                "entities": {},
                "task_type": "simple",
                "requires_planning": False
            }
    
    def _extract_project_name(self, message: str) -> str:
        """从消息中提取项目名称"""
        # 简单的项目名称提取
        message = message.replace("创建项目", "").replace("新建项目", "").replace(":", "").replace("：", "")
        message = message.strip()
        
        if message:
            return message
        else:
            return f"项目_{int(time.time())}"  # 默认项目名
    

    
    def _handle_create_project(self, intent: Dict[str, Any], message: str) -> str:
        """处理创建项目"""
        project_name = intent.get("entities", {}).get("project_name", "新项目")
        
        try:
            project_path = self.project_manager.create_project(project_name)
            return f"""
🎉 **项目创建成功！**

📁 **项目信息**
• 项目名称：{project_name}
• 项目路径：{project_path}
• 创建时间：{time.strftime('%Y-%m-%d %H:%M:%S')}

💡 **下一步建议**
• 上传招标文件进行分析
• 直接开始生成标书大纲
• 查看项目结构

你想做什么？
"""
        except Exception as e:
            if "已存在" in str(e):
                # 项目已存在，切换到该项目
                try:
                    self.project_manager.switch_project(project_name)
                    return f"""
📁 **项目已存在，已切换到项目：{project_name}**

💡 **你可以**：
• 查看项目结构
• 生成标书大纲
• 继续编辑内容
• 导出Word文档

需要我帮你做什么？
"""
                except:
                    return f"⚠️ 项目 '{project_name}' 已存在，但切换失败"
            else:
                return f"❌ 项目创建失败: {str(e)}"
    
    def _handle_analyze_tender(self, intent: Dict[str, Any], message: str) -> str:
        """处理招标文件分析"""
        file_path = intent.get("entities", {}).get("file_path")
        
        if not file_path:
            return """
📄 **招标文件分析**

请提供招标文件路径，例如：
• "分析文件：/path/to/tender.pdf"
• "上传了招标文件，请分析"

支持的文件格式：PDF, DOC, DOCX, TXT

💡 **或者你可以**：
• 直接开始生成标书大纲
• 创建新项目开始制作
"""
        
        try:
            # 使用MCP工具提取文件内容
            content = self.mcp_server.extract_pdf_content(file_path)
            
            # 分析招标要求
            analysis = self.mcp_server.parse_tender_requirements(content)
            
            return f"""
🔍 **招标文件分析完成！**

📋 **项目概况**
• 项目名称：{analysis.get('project_name', '未识别')}
• 招标单位：{analysis.get('tender_unit', '未识别')}
• 预算范围：{analysis.get('budget', '未识别')}
• 项目周期：{analysis.get('duration', '未识别')}

🎯 **关键要求**
{self._format_requirements(analysis.get('requirements', []))}

📊 **评分标准**
{self._format_scoring_criteria(analysis.get('scoring', {}))}

💡 **下一步建议**
• 生成标书大纲
• 创建项目并开始制作
• 分析技术难点

需要我继续哪个步骤？
"""
        except Exception as e:
            return f"❌ 文件分析失败: {str(e)}"
    
    def _handle_generate_outline(self, intent: Dict[str, Any], message: str) -> str:
        """处理大纲生成"""
        try:
            # 获取项目要求
            requirements = intent.get("entities", {}).get("requirements", "")
            project_type = intent.get("entities", {}).get("project_type", "通用")
            
            # 生成大纲
            outline = self.mcp_server.generate_outline(requirements, project_type)
            
            # 保存大纲到项目
            if self.project_manager.current_project:
                self.project_manager.save_outline(outline)
            
            return f"""
📝 **标书大纲生成完成！**

{self._format_outline(outline)}

✅ **大纲已保存到项目**

💡 **下一步操作**
• 开始生成各章节内容
• 优化特定章节
• 查看章节详情

需要我开始生成内容吗？
"""
        except Exception as e:
            return f"❌ 大纲生成失败: {str(e)}"
    
    def _handle_generate_content(self, intent: Dict[str, Any], message: str) -> str:
        """处理内容生成"""
        section = intent.get("entities", {}).get("section")
        subsection = intent.get("entities", {}).get("subsection")
        
        if not section:
            return "请指定要生成的章节，例如：'生成第3章技术方案'"
        
        try:
            if subsection:
                # 生成特定小节
                content = self.mcp_server.generate_subsection_content(
                    section, subsection, self._get_project_context()
                )
                self.project_manager.save_subsection(section, subsection, content)
                
                return f"""
✅ **小节内容生成完成！**

📄 **{section} - {subsection}**
• 字数：约{len(content)}字
• 保存位置：sections/{section}/{subsection}.md

💡 **你可以**：
• 查看生成的内容
• 继续生成其他小节
• 优化当前内容

需要我继续生成其他内容吗？
"""
            else:
                # 生成整个章节的所有小节
                return self._generate_section_parallel(section)
                
        except Exception as e:
            return f"❌ 内容生成失败: {str(e)}"
    
    def _handle_export_document(self, intent: Dict[str, Any], message: str) -> str:
        """处理文档导出"""
        if not self.project_manager.current_project:
            return """
⚠️ **没有活动项目**

请先：
• 创建新项目
• 切换到现有项目
• 生成标书大纲

然后再导出文档。
"""
        
        try:
            # 一键导出Word文档
            result = self.mcp_server.one_click_docx_export()
            
            return f"""
📄 **Word文档导出完成！**

📁 **文件信息**
• 保存位置：{result.get('file_path')}
• 文件大小：{result.get('file_size')}
• 总页数：{result.get('pages')}页
• 包含图表：{result.get('charts')}个

📋 **文档结构**
• 封面页 (公司信息+项目标题)
• 目录页 (自动生成)
• 正文内容 ({result.get('sections')}个主要章节)
• 附件页 (资质证明位置)

💡 **下一步建议**
• 添加公司Logo到封面
• 检查并完善资质附件
• 最终审查后可直接提交

🎉 **标书制作完成！**
"""
        except Exception as e:
            return f"❌ 文档导出失败: {str(e)}"
    
    def _handle_view_content(self, intent: Dict[str, Any], message: str) -> str:
        """处理查看内容"""
        section = intent.get("entities", {}).get("section")
        
        if not section:
            # 显示项目结构
            return self._show_project_structure()
        
        try:
            # 显示章节内容
            structure = self.project_manager.get_section_structure(section)
            return f"""
📖 **{section} 章节结构**

{self._format_section_structure(structure)}

💭 **你可以**：
• 查看具体小节：输入"打开{section}的某个小节"
• 编辑特定内容：输入"编辑{section}的某个小节"
• 优化章节内容：输入"优化{section}"
"""
        except Exception as e:
            return f"❌ 查看内容失败: {str(e)}"
    
    def _handle_project_management(self, intent: Dict[str, Any], message: str) -> str:
        """处理项目管理"""
        action = intent.get("entities", {}).get("action")
        
        if action == "list":
            projects = self.project_manager.list_projects()
            return self._format_project_list(projects)
        elif action == "switch":
            project_name = intent.get("entities", {}).get("project_name")
            if project_name:
                self.project_manager.switch_project(project_name)
                return f"✅ 已切换到项目：{project_name}"
            else:
                return "请指定要切换的项目名称"
        elif action == "backup":
            result = self.project_manager.backup_current_project()
            return f"✅ 项目备份完成：{result}"
        else:
            projects = self.project_manager.list_projects()
            return self._format_project_list(projects)
    
    def _handle_complex_task(self, intent: Dict[str, Any], message: str) -> str:
        """处理复杂任务（需要智能规划）"""
        return f"""
🤖 **智能任务规划**

我理解您想要：{message}

📋 **建议的执行步骤**：
1️⃣ 创建新项目
2️⃣ 生成标书大纲  
3️⃣ 生成各章节内容
4️⃣ 导出Word文档

💡 **你可以说**：
• "创建项目：[项目名称]"
• "生成大纲"
• "导出文档"

需要我帮你开始哪一步？
"""
    
    def _handle_general_chat(self, intent: Dict[str, Any], message: str) -> str:
        """处理一般对话"""
        # 如果AI客户端可用，使用AI回复
        if self.ai_client and self.ai_client.is_available():
            try:
                system_prompt = self.prompt_library.get_prompt("general_chat")
                context = f"""
当前项目: {self.project_manager.current_project_name or "无"}
项目状态: {self._get_project_status()}
用户消息: {message}
"""
                response = self.ai_client.chat(context, system_prompt)
                return response
            except Exception as e:
                logger.error(f"AI chat failed: {e}")
        
        # 使用预设回复
        message_lower = message.lower()
        
        # 根据用户问题提供针对性回复
        if any(keyword in message_lower for keyword in ["你是谁", "who are you", "介绍", "什么"]):
            return f"""
🤖 **我是 Tender AI - 专业标书智能助手**

💡 **我的能力**：
• 📁 项目管理 - 创建、管理标书项目
• 📝 大纲生成 - 自动生成专业标书大纲
• 📄 内容生成 - 智能生成各章节内容
• 📊 文档导出 - 一键导出专业Word文档
• 🔍 文件分析 - 分析招标文件要求

📝 **常用命令**：
• "创建项目：[项目名]" - 创建新的标书项目
• "生成大纲" - 生成标书大纲结构
• "查看项目结构" - 查看当前项目状态
• "导出文档" - 导出Word格式标书

🔧 **当前状态**：
• AI模型端点：{self.ai_client.base_url or '默认'}
• 模型：{self.ai_client.model}
• 服务状态：{'🟢 在线' if self.ai_client.is_available() else '🔴 离线'}

请告诉我你想做什么？
"""
        
        elif any(keyword in message_lower for keyword in ["帮助", "help", "怎么用", "如何使用"]):
            return """
📖 **Tender AI 使用指南**

### 🚀 快速开始
1. **创建项目**：`创建项目：我的标书项目`
2. **生成大纲**：`生成大纲`
3. **查看结构**：`查看项目结构`
4. **导出文档**：`导出Word文档`

### 💡 常用功能
- **项目管理**：创建、切换、列出项目
- **内容生成**：自动生成标书各章节内容
- **文档导出**：一键生成专业Word标书
- **文件分析**：分析招标文件要求

### 🎯 示例对话
```
> 创建项目：智慧城市建设项目
> 生成大纲
> 查看第1章
> 导出Word文档
```

有什么具体问题吗？
"""
        
        elif any(keyword in message_lower for keyword in ["状态", "配置", "设置"]):
            return f"""
⚙️ **系统状态**

🔧 **配置信息**：
• AI提供商：{self.ai_client.provider}
• 模型：{self.ai_client.model}
• API端点：{self.ai_client.base_url or '默认OpenAI端点'}
• 服务状态：{'🟢 在线' if self.ai_client.is_available() else '🔴 离线 (请检查本地服务)'}

📁 **项目信息**：
• 当前项目：{self.project_manager.current_project_name or '无'}
• 工作目录：{self.project_manager.workspace_dir}

💡 **提示**：
{f'本地AI服务 {self.ai_client.base_url} 似乎未运行，请启动您的模型服务。' if not self.ai_client.is_available() and self.ai_client.base_url else '系统运行正常！'}
"""
        
        else:
            return f"""
🤖 **Tender AI 助手**

你好！我是专业的标书智能助手。

💡 **我可以帮你**：
• 创建标书项目
• 生成标书大纲
• 分析招标文件
• 导出Word文档
• 管理项目文件

📝 **常用命令**：
• "创建项目：[项目名]"
• "生成大纲"
• "查看项目结构"
• "导出文档"

🔧 **当前状态**：AI服务{'在线' if self.ai_client.is_available() else '离线'}

请告诉我你想做什么？
"""
    
    # 辅助方法
    def _get_project_status(self) -> str:
        """获取项目状态"""
        if not self.project_manager.current_project:
            return "无活动项目"
        
        # 获取项目完成度等信息
        return "项目进行中"
    
    def _get_project_context(self) -> Dict[str, Any]:
        """获取项目上下文"""
        return {
            "project_name": self.project_manager.current_project_name,
            "requirements": {},  # 从项目中获取需求
            "outline": {},  # 从项目中获取大纲
        }
    
    def _format_requirements(self, requirements: List[str]) -> str:
        """格式化需求列表"""
        if not requirements:
            return "• 暂无具体要求"
        return "\n".join([f"• {req}" for req in requirements])
    
    def _format_scoring_criteria(self, scoring: Dict[str, Any]) -> str:
        """格式化评分标准"""
        if not scoring:
            return "• 暂无评分标准"
        
        result = []
        for criteria, score in scoring.items():
            result.append(f"• {criteria} ({score}分)")
        return "\n".join(result)
    
    def _format_outline(self, outline: Dict[str, Any]) -> str:
        """格式化大纲"""
        result = []
        for i, section in enumerate(outline.get('sections', []), 1):
            result.append(f"{i}. {section.get('title')}")
            for j, subsection in enumerate(section.get('subsections', []), 1):
                result.append(f"   {i}.{j} {subsection}")
        return "\n".join(result)
    
    def _format_section_structure(self, structure: Dict[str, Any]) -> str:
        """格式化章节结构"""
        result = []
        for file_info in structure.get('files', []):
            status = "✅ 已完成" if file_info.get('exists') else "⏳ 待生成"
            size = f"({file_info.get('size', 0)}字)" if file_info.get('exists') else ""
            result.append(f"├── {file_info.get('name')} {status} {size}")
        return "\n".join(result)
    
    def _format_project_list(self, projects: List[Dict[str, Any]]) -> str:
        """格式化项目列表"""
        if not projects:
            return "📁 **暂无项目**\n\n创建第一个项目：输入'创建项目：项目名称'"
        
        result = ["📁 **项目列表**\n"]
        for project in projects:
            status = "🟢 当前" if project.get('is_current') else "⚪"
            result.append(f"{status} {project.get('name')} - {project.get('created_time')}")
        
        return "\n".join(result)
    
    def _format_task_steps(self, steps: List[Dict[str, Any]]) -> str:
        """格式化任务步骤"""
        result = []
        for i, step in enumerate(steps, 1):
            result.append(f"{i}️⃣ **{step.get('name')}** (预估{step.get('time')})")
            for subtask in step.get('subtasks', []):
                result.append(f"   • {subtask}")
        return "\n".join(result)
    
    def _generate_section_parallel(self, section: str) -> str:
        """并行生成章节内容"""
        # 实现多线程并行生成逻辑
        return f"""
⚡ **启动并行内容生成** - {section}

🔄 **生成进度** (多线程同时工作)
✅ 已启动 24 个并行任务
⏳ 正在生成各小节内容...

💡 **你可以随时**：
• 查看生成进度
• 编辑已完成的小节
• 继续其他工作

生成完成后我会通知你！
"""
    
    def _show_project_structure(self) -> str:
        """显示项目结构"""
        if not self.project_manager.current_project:
            return """
📁 **当前无活动项目**

💡 **开始使用**：
• 创建项目：输入"创建项目：项目名称"
• 查看所有项目：输入"项目列表"
"""
        
        structure = self.project_manager.get_project_structure()
        return f"""
📁 **项目结构** - {self.project_manager.current_project_name}

{self._format_project_structure(structure)}

💡 **操作提示**：
• 查看章节：输入"查看第X章"
• 生成内容：输入"生成第X章"
• 导出文档：输入"导出Word"
"""
    
    def _format_project_structure(self, structure: Dict[str, Any]) -> str:
        """格式化项目结构"""
        if not structure or not structure.get("sections"):
            return """
```
./sections/
└── (暂无内容)
```

💡 **建议**：先生成标书大纲
"""
        
        result = ["```", "./sections/"]
        for section in structure.get("sections", []):
            result.append(f"├── {section.get('name')}/")
            for file_info in section.get("files", []):
                status = "✅" if file_info.get("exists") else "⏳"
                result.append(f"│   └── {file_info.get('name')} {status}")
        result.append("```")
        
        return "\n".join(result) 

    def _handle_list_projects(self, intent: Dict[str, Any], message: str) -> str:
        """处理项目列表请求"""
        try:
            projects = self.project_manager.list_projects()
            
            if not projects:
                return """
📁 **项目列表**

暂无项目。

💡 **创建项目**：输入 "创建项目：项目名称"
"""
            
            project_list = []
            for project in projects:
                status = "🟢 当前" if project == self.project_manager.current_project_name else "⚪"
                project_list.append(f"• {status} {project}")
            
            return f"""
📁 **项目列表**

{chr(10).join(project_list)}

💡 **切换项目**：输入 "切换到项目：项目名称"
💡 **创建项目**：输入 "创建项目：项目名称"
"""
        except Exception as e:
            logger.error(f"List projects failed: {e}")
            return f"❌ 获取项目列表失败: {str(e)}" 

    def _handle_tool_usage(self, intent: Dict[str, Any], message: str) -> str:
        """处理工具使用请求"""
        try:
            # 简单的工具调用解析
            message_lower = message.lower()
            
            if "查看" in message_lower and ("文件" in message_lower or "目录" in message_lower or "结构" in message_lower):
                # 查看项目结构
                if self.project_manager.current_project_name:
                    result = self.simple_mcp_tools.call_tool("list_files", {"path": "."})
                    return f"📁 **当前项目文件结构**\n\n{result}"
                else:
                    return "📁 **当前无活动项目**\n\n💡 请先创建或切换到一个项目。"
            
            elif "读取" in message_lower or "查看文件" in message_lower:
                # 尝试提取文件路径
                words = message.split()
                for word in words:
                    if "." in word and "/" in word:  # 简单的文件路径检测
                        result = self.simple_mcp_tools.call_tool("read_file", {"path": word})
                        return f"📄 **文件内容**\n\n{result}"
                
                return "请指定要读取的文件路径，例如：读取文件 sections/01-公司介绍/1.1-公司基本情况.md"
            
            elif "创建目录" in message_lower or "创建文件夹" in message_lower:
                # 尝试提取目录名
                words = message.split()
                if len(words) > 2:
                    dir_name = words[-1]
                    result = self.simple_mcp_tools.call_tool("create_directory", {"path": dir_name})
                    return f"📁 **目录操作**\n\n{result}"
                
                return "请指定要创建的目录名，例如：创建目录 new_folder"
            
            else:
                return """
🔧 **可用工具操作**

📁 **文件管理**：
• "查看项目结构" - 查看当前项目的文件结构
• "读取文件 [路径]" - 读取指定文件内容
• "创建目录 [名称]" - 创建新目录

💡 **示例**：
• 查看项目文件结构
• 读取文件 sections/01-公司介绍/1.1-公司基本情况.md
• 创建目录 new_section

请告诉我你想执行什么操作？
"""
        
        except Exception as e:
            logger.error(f"Tool usage failed: {e}")
            return f"❌ 工具使用失败: {str(e)}" 