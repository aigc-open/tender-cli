"""
MCP 服务器主类
"""

from typing import Dict, Any, List, Optional
import asyncio
import concurrent.futures
from pathlib import Path

from .file_tools import FileTools
from .tender_tools import TenderTools
from .content_tools import ContentTools
from .document_tools import DocumentTools
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MCPServer:
    """MCP 服务器 - 集成所有工具"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_workers = config.get("max_workers", 24)
        self.timeout = config.get("timeout", 30)
        
        # 初始化工具集
        self.file_tools = FileTools()
        self.tender_tools = TenderTools()
        self.content_tools = ContentTools()
        self.document_tools = DocumentTools()
        
        # 线程池
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        )
        
        logger.info(f"MCP Server initialized with {self.max_workers} workers")
    
    # 文件操作工具
    def read_file(self, path: str) -> str:
        """读取文件内容"""
        return self.file_tools.read_file(path)
    
    def write_file(self, path: str, content: str) -> bool:
        """写入文件"""
        return self.file_tools.write_file(path, content)
    
    def list_files(self, directory: str) -> List[str]:
        """列出目录文件"""
        return self.file_tools.list_files(directory)
    
    def create_directory(self, path: str) -> bool:
        """创建目录"""
        return self.file_tools.create_directory(path)
    
    def delete_file(self, path: str) -> bool:
        """删除文件"""
        return self.file_tools.delete_file(path)
    
    def read_subsection_file(self, section: str, subsection: str) -> str:
        """读取三级标题内容文件"""
        return self.file_tools.read_subsection_file(section, subsection)
    
    def write_subsection_file(self, section: str, subsection: str, content: str) -> bool:
        """写入三级标题内容"""
        return self.file_tools.write_subsection_file(section, subsection, content)
    
    def list_subsection_files(self, section: str) -> List[str]:
        """列出章节下所有三级标题文件"""
        return self.file_tools.list_subsection_files(section)
    
    def get_section_structure(self) -> Dict[str, Any]:
        """获取完整的章节结构"""
        return self.file_tools.get_section_structure()
    
    # 招标文件处理工具
    def extract_pdf_content(self, file_path: str) -> str:
        """提取PDF文本内容"""
        return self.tender_tools.extract_pdf_content(file_path)
    
    def parse_tender_requirements(self, content: str) -> Dict[str, Any]:
        """解析招标要求"""
        return self.tender_tools.parse_tender_requirements(content)
    
    def extract_key_info(self, content: str) -> Dict[str, Any]:
        """提取关键信息"""
        return self.tender_tools.extract_key_info(content)
    
    def analyze_scoring_criteria(self, content: str) -> Dict[str, Any]:
        """分析评分标准"""
        return self.tender_tools.analyze_scoring_criteria(content)
    
    def detect_tender_type(self, content: str) -> str:
        """识别招标类型"""
        return self.tender_tools.detect_tender_type(content)
    
    # 大纲生成工具
    def generate_outline(self, requirements: str, tender_type: str) -> Dict[str, Any]:
        """生成标书大纲"""
        return self.content_tools.generate_outline(requirements, tender_type)
    
    def validate_outline(self, outline: Dict[str, Any]) -> Dict[str, Any]:
        """验证大纲完整性"""
        return self.content_tools.validate_outline(outline)
    
    def suggest_improvements(self, outline: Dict[str, Any]) -> List[str]:
        """建议大纲优化"""
        return self.content_tools.suggest_improvements(outline)
    
    def expand_section(self, section_title: str) -> Dict[str, Any]:
        """展开章节详情"""
        return self.content_tools.expand_section(section_title)
    
    # 内容生成工具
    def generate_subsection_content(self, section: str, subsection: str, 
                                  requirements: Dict[str, Any]) -> str:
        """生成三级标题内容"""
        return self.content_tools.generate_subsection_content(
            section, subsection, requirements
        )
    
    def parallel_generate_subsections(self, subsections_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """多线程并行生成所有三级内容"""
        return self._run_parallel_tasks(
            self._generate_subsection_task,
            subsections_list
        )
    
    def generate_section_outline(self, section_title: str) -> Dict[str, Any]:
        """生成章节的三级标题大纲"""
        return self.content_tools.generate_section_outline(section_title)
    
    def refine_subsection_content(self, section: str, subsection: str, 
                                instructions: str) -> str:
        """优化三级标题内容"""
        return self.content_tools.refine_subsection_content(
            section, subsection, instructions
        )
    
    def generate_technical_solution(self, requirements: Dict[str, Any]) -> str:
        """生成技术方案"""
        return self.content_tools.generate_technical_solution(requirements)
    
    def create_project_timeline(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """创建项目时间表"""
        return self.content_tools.create_project_timeline(requirements)
    
    def generate_budget_breakdown(self, amount: float, items: List[str]) -> Dict[str, Any]:
        """生成预算分解"""
        return self.content_tools.generate_budget_breakdown(amount, items)
    
    def batch_update_subsections(self, updates_dict: Dict[str, str]) -> Dict[str, Any]:
        """批量更新多个三级标题"""
        return self.content_tools.batch_update_subsections(updates_dict)
    
    # 文档处理工具
    def convert_to_docx(self, markdown_content: str) -> str:
        """转换为Word文档"""
        return self.document_tools.convert_to_docx(markdown_content)
    
    def one_click_docx_export(self) -> Dict[str, Any]:
        """一键导出完整Word标书"""
        return self.document_tools.one_click_docx_export()
    
    def merge_subsections_to_docx(self) -> Dict[str, Any]:
        """合并所有三级标题内容为Word"""
        return self.document_tools.merge_subsections_to_docx()
    
    def assemble_section_from_subsections(self, section: str) -> str:
        """组装章节从三级标题文件"""
        return self.document_tools.assemble_section_from_subsections(section)
    
    def apply_template(self, content: str, template: str) -> str:
        """应用文档模板"""
        return self.document_tools.apply_template(content, template)
    
    def format_tables(self, data: List[List[str]]) -> str:
        """格式化表格"""
        return self.document_tools.format_tables(data)
    
    def insert_charts(self, data: Dict[str, Any], chart_type: str) -> str:
        """插入图表"""
        return self.document_tools.insert_charts(data, chart_type)
    
    def export_pdf(self, docx_path: str) -> str:
        """导出PDF"""
        return self.document_tools.export_pdf(docx_path)
    
    def batch_format_docx(self, subsections: List[str]) -> Dict[str, Any]:
        """批量格式化三级标题内容"""
        return self.document_tools.batch_format_docx(subsections)
    
    # 并行处理辅助方法
    def _run_parallel_tasks(self, task_func, task_list: List[Any]) -> Dict[str, Any]:
        """运行并行任务"""
        results = {}
        
        try:
            # 提交所有任务
            future_to_task = {
                self.executor.submit(task_func, task): task 
                for task in task_list
            }
            
            # 收集结果
            completed = 0
            total = len(task_list)
            
            for future in concurrent.futures.as_completed(future_to_task, timeout=self.timeout):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results[str(task)] = {
                        "success": True,
                        "content": result,
                        "error": None
                    }
                except Exception as e:
                    results[str(task)] = {
                        "success": False,
                        "content": None,
                        "error": str(e)
                    }
                
                completed += 1
                logger.info(f"Task completed: {completed}/{total}")
            
            return {
                "total_tasks": total,
                "completed": completed,
                "results": results,
                "success_rate": sum(1 for r in results.values() if r["success"]) / total
            }
            
        except concurrent.futures.TimeoutError:
            logger.error("Parallel task execution timed out")
            return {
                "total_tasks": len(task_list),
                "completed": len(results),
                "results": results,
                "error": "Timeout"
            }
    
    def _generate_subsection_task(self, task_info: Dict[str, Any]) -> str:
        """单个小节生成任务"""
        section = task_info.get("section")
        subsection = task_info.get("subsection")
        requirements = task_info.get("requirements", {})
        
        return self.generate_subsection_content(section, subsection, requirements)
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True) 