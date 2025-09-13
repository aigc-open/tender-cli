"""
内容生成工具
"""

from typing import Dict, Any, List
from ..utils.logger import get_logger
from mcp.server.fastmcp import FastMCP

logger = get_logger(__name__)


class ContentTools:
    """内容生成工具集"""
    
    def generate_outline(self, requirements: str, tender_type: str) -> Dict[str, Any]:
        """生成标书大纲"""
        # 基础大纲模板
        outline = {
            "title": f"{tender_type}标书大纲",
            "sections": [
                {
                    "title": "公司介绍及资质证明",
                    "subsections": [
                        "公司基本情况",
                        "资质证书",
                        "技术团队介绍",
                        "公司业绩"
                    ]
                },
                {
                    "title": "项目需求理解与分析",
                    "subsections": [
                        "招标需求分析",
                        "技术难点识别",
                        "解决方案概述"
                    ]
                },
                {
                    "title": "总体技术方案设计",
                    "subsections": [
                        "方案概述",
                        "核心技术架构",
                        "技术选型说明",
                        "安全保障体系"
                    ]
                },
                {
                    "title": "系统架构与技术选型",
                    "subsections": [
                        "系统总体架构",
                        "数据库设计",
                        "接口设计",
                        "性能优化方案"
                    ]
                },
                {
                    "title": "项目实施计划与管理",
                    "subsections": [
                        "项目实施计划",
                        "项目管理方法",
                        "质量保证措施",
                        "风险控制方案"
                    ]
                },
                {
                    "title": "运维服务与技术支持",
                    "subsections": [
                        "运维服务方案",
                        "技术支持体系",
                        "培训计划",
                        "应急响应机制"
                    ]
                },
                {
                    "title": "项目预算与报价分析",
                    "subsections": [
                        "成本构成分析",
                        "报价明细",
                        "性价比分析"
                    ]
                }
            ]
        }
        
        return outline
    
    def validate_outline(self, outline: Dict[str, Any]) -> Dict[str, Any]:
        """验证大纲完整性"""
        issues = []
        suggestions = []
        
        # 检查必要章节
        required_sections = ["公司介绍", "技术方案", "项目管理", "预算报价"]
        sections = [s.get("title", "") for s in outline.get("sections", [])]
        
        for required in required_sections:
            if not any(required in section for section in sections):
                issues.append(f"缺少必要章节: {required}")
        
        # 检查章节数量
        section_count = len(outline.get("sections", []))
        if section_count < 5:
            suggestions.append("建议增加更多章节以提高标书完整性")
        elif section_count > 10:
            suggestions.append("章节过多，建议合并相关内容")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "score": max(0, 100 - len(issues) * 20 - len(suggestions) * 5)
        }
    
    def suggest_improvements(self, outline: Dict[str, Any]) -> List[str]:
        """建议大纲优化"""
        suggestions = []
        
        sections = outline.get("sections", [])
        
        # 检查各种改进建议
        if len(sections) < 6:
            suggestions.append("建议增加'售后服务'章节")
        
        # 检查是否有创新点
        innovation_keywords = ["创新", "特色", "优势", "亮点"]
        has_innovation = any(
            any(keyword in s.get("title", "") for keyword in innovation_keywords)
            for s in sections
        )
        
        if not has_innovation:
            suggestions.append("建议增加技术创新或方案亮点章节")
        
        return suggestions
    
    def expand_section(self, section_title: str) -> Dict[str, Any]:
        """展开章节详情"""
        # 根据章节标题返回详细的小节建议
        section_templates = {
            "公司介绍": {
                "subsections": [
                    "公司基本情况",
                    "组织架构",
                    "资质证书",
                    "技术团队",
                    "成功案例"
                ],
                "description": "全面展示公司实力和资质"
            },
            "技术方案": {
                "subsections": [
                    "技术架构设计",
                    "核心技术选型",
                    "系统功能设计",
                    "性能保障措施",
                    "安全防护体系"
                ],
                "description": "详细的技术实现方案"
            }
        }
        
        # 模糊匹配
        for key, template in section_templates.items():
            if key in section_title:
                return template
        
        # 默认模板
        return {
            "subsections": ["概述", "详细方案", "实施计划"],
            "description": "章节详细内容"
        }
    
    def generate_subsection_content(self, section: str, subsection: str, 
                                  requirements: Dict[str, Any]) -> str:
        """生成三级标题内容"""
        # 这里应该调用AI生成具体内容
        # 目前返回模板内容
        
        content_template = f"""# {subsection}

## 概述
本节将详细介绍{subsection}的相关内容。

## 详细方案
根据项目需求，我们制定了以下方案：

1. **方案要点一**
   - 具体实施措施
   - 预期效果

2. **方案要点二**
   - 具体实施措施
   - 预期效果

## 实施计划
- 第一阶段：准备工作
- 第二阶段：具体实施
- 第三阶段：验收交付

## 质量保证
我们将采用以下措施确保质量：
- 质量控制流程
- 测试验证方法
- 风险防控措施

---
*本内容由 Tender AI 智能生成*
"""
        
        return content_template
    
    def generate_section_outline(self, section_title: str) -> Dict[str, Any]:
        """生成章节的三级标题大纲"""
        return self.expand_section(section_title)
    
    def refine_subsection_content(self, section: str, subsection: str, 
                                instructions: str) -> str:
        """优化三级标题内容"""
        # 这里应该基于指令优化现有内容
        return f"# {subsection}\n\n根据优化指令：{instructions}\n\n优化后的内容..."
    
    def generate_technical_solution(self, requirements: Dict[str, Any]) -> str:
        """生成技术方案"""
        return "# 技术方案\n\n详细的技术实现方案..."
    
    def create_project_timeline(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """创建项目时间表"""
        return {
            "phases": [
                {"name": "需求分析", "duration": "2周", "tasks": []},
                {"name": "系统设计", "duration": "3周", "tasks": []},
                {"name": "开发实施", "duration": "8周", "tasks": []},
                {"name": "测试验收", "duration": "2周", "tasks": []}
            ],
            "total_duration": "15周"
        }
    
    def generate_budget_breakdown(self, amount: float, items: List[str]) -> Dict[str, Any]:
        """生成预算分解"""
        return {
            "total_amount": amount,
            "breakdown": [
                {"item": "软件开发", "amount": amount * 0.6, "percentage": 60},
                {"item": "硬件设备", "amount": amount * 0.2, "percentage": 20},
                {"item": "实施服务", "amount": amount * 0.15, "percentage": 15},
                {"item": "其他费用", "amount": amount * 0.05, "percentage": 5}
            ]
        }
    
    def batch_update_subsections(self, updates_dict: Dict[str, str]) -> Dict[str, Any]:
        """批量更新多个三级标题"""
        results = {}
        
        for key, content in updates_dict.items():
            try:
                # 这里应该实际更新文件
                results[key] = {"success": True, "message": "更新成功"}
            except Exception as e:
                results[key] = {"success": False, "message": str(e)}
        
        return results 