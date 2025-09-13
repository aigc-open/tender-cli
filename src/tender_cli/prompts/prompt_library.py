"""
提示词库
"""

from typing import Dict, Any


class PromptLibrary:
    """提示词库管理类"""
    
    def __init__(self):
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, str]:
        """加载所有提示词"""
        return {
            "system": self._get_system_prompt(),
            "analyze_intent": self._get_analyze_intent_prompt(),
            "analyze_tender": self._get_analyze_tender_prompt(),
            "generate_outline": self._get_generate_outline_prompt(),
            "generate_content": self._get_generate_content_prompt(),
            "optimize_content": self._get_optimize_content_prompt(),
            "task_planning": self._get_task_planning_prompt(),
            "general_chat": self._get_general_chat_prompt(),
            "export_docx": self._get_export_docx_prompt()
        }
    
    def get_prompt(self, prompt_name: str) -> str:
        """获取指定提示词"""
        return self.prompts.get(prompt_name, "")
    
    def _get_system_prompt(self) -> str:
        """系统提示词"""
        return """
你是一个专业的标书智能体助手，具备以下能力：
1. 深度理解招标文件内容和要求
2. 生成符合招标要求的专业标书
3. 提供标书写作的专业建议
4. 协助完成标书的全流程管理

请始终保持专业、准确、高效的工作风格。
"""
    
    def _get_analyze_intent_prompt(self) -> str:
        """意图分析提示词"""
        return """
请分析用户的意图并返回JSON格式的结果。

意图类型包括：
- create_project: 创建项目
- analyze_tender: 分析招标文件
- generate_outline: 生成大纲
- generate_content: 生成内容
- export_document: 导出文档
- view_content: 查看内容
- project_management: 项目管理
- complex_task: 复杂任务（需要智能规划）
- general_chat: 一般对话

返回格式：
{
    "intent": "意图类型",
    "confidence": 0.8,
    "entities": {
        "project_name": "项目名称",
        "file_path": "文件路径",
        "section": "章节名称",
        "subsection": "小节名称"
    },
    "task_type": "simple|complex",
    "requires_planning": false
}
"""
    
    def _get_analyze_tender_prompt(self) -> str:
        """招标文件分析提示词"""
        return """
分析以下招标文件，提取关键信息：
- 招标单位和项目名称
- 项目预算和周期
- 技术要求和标准
- 评分标准和权重
- 投标截止时间
- 特殊要求和注意事项

招标文件内容：{content}
"""
    
    def _get_generate_outline_prompt(self) -> str:
        """大纲生成提示词"""
        return """
根据以下招标要求生成专业标书大纲：

招标要求：{requirements}
项目类型：{project_type}
预算范围：{budget}

请生成包含以下标准章节的大纲：
1. 公司介绍和资质
2. 项目理解和需求分析
3. 技术方案和实施计划
4. 项目管理和质量保证
5. 预算报价和成本分析
6. 售后服务和支持方案
"""
    
    def _get_generate_content_prompt(self) -> str:
        """内容生成提示词"""
        return """
为标书章节"{section_title}"生成专业内容：

章节要求：{section_requirements}
项目背景：{project_context}
技术要求：{technical_requirements}

请确保内容：
- 符合招标要求
- 突出技术优势
- 体现专业水准
- 逻辑清晰完整
"""
    
    def _get_optimize_content_prompt(self) -> str:
        """内容优化提示词"""
        return """
请优化以下标书内容：

原始内容：{original_content}
优化要求：{optimization_requirements}

优化方向：
- 提高专业性和说服力
- 增强逻辑性和条理性
- 突出竞争优势
- 符合评分标准
"""
    
    def _get_task_planning_prompt(self) -> str:
        """智能任务规划提示词"""
        return """
根据用户需求自动制定标书制作计划：

用户输入：{user_message}
项目背景：{project_context}
当前状态：{current_state}

规划要素：
- 任务分解：将复杂需求拆分为具体可执行的子任务
- 优先级排序：根据重要性和依赖关系排序
- 时间估算：预估每个任务的执行时间
- 资源分配：合理分配AI处理资源
- 里程碑设置：设定关键检查点
- 风险识别：预判可能的问题和解决方案

输出格式：
1. 📋 任务概览 (总体目标和范围)
2. 🎯 执行计划 (分步骤详细计划)  
3. ⏰ 时间安排 (预估完成时间)
4. 💡 建议优化 (提升效率的建议)

请返回JSON格式的详细计划。
"""
    
    def _get_general_chat_prompt(self) -> str:
        """一般对话提示词"""
        return """
你是一个专业的标书智能助手。请根据用户的问题提供有帮助的回答。

如果用户询问标书相关问题，请提供专业建议。
如果用户需要帮助，请指导他们如何使用系统功能。
保持友好、专业的语调。
"""
    
    def _get_export_docx_prompt(self) -> str:
        """Word导出提示词"""
        return """
将当前标书项目一键导出为专业Word文档：

项目信息：{project_info}
章节列表：{sections_list}
格式要求：{format_requirements}

导出配置：
- 使用标准标书模板
- 自动生成目录和页码
- 统一字体和格式
- 插入公司Logo和签章位置
- 生成封面和声明页
- 优化表格和图表显示
""" 