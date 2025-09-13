"""
招标文件处理工具
"""

import re
from pathlib import Path
from typing import Dict, Any, List
import PyPDF2
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TenderTools:
    """招标文件处理工具集"""
    
    def extract_pdf_content(self, file_path: str) -> str:
        """提取PDF文本内容"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text.strip()
        except Exception as e:
            logger.error(f"Failed to extract PDF content: {e}")
            return ""
    
    def parse_tender_requirements(self, content: str) -> Dict[str, Any]:
        """解析招标要求"""
        result = {
            "project_name": self._extract_project_name(content),
            "tender_unit": self._extract_tender_unit(content),
            "budget": self._extract_budget(content),
            "duration": self._extract_duration(content),
            "requirements": self._extract_requirements(content),
            "scoring": self._extract_scoring_criteria(content)
        }
        
        return result
    
    def extract_key_info(self, content: str) -> Dict[str, Any]:
        """提取关键信息"""
        return {
            "deadline": self._extract_deadline(content),
            "contact_info": self._extract_contact_info(content),
            "technical_specs": self._extract_technical_specs(content),
            "qualification_requirements": self._extract_qualification_requirements(content)
        }
    
    def analyze_scoring_criteria(self, content: str) -> Dict[str, Any]:
        """分析评分标准"""
        scoring = {}
        
        # 常见评分标准模式
        patterns = {
            "技术方案": r"技术方案.*?(\d+)分",
            "商务报价": r"商务报价.*?(\d+)分",
            "公司资质": r"公司资质.*?(\d+)分",
            "项目经验": r"项目经验.*?(\d+)分",
            "实施方案": r"实施方案.*?(\d+)分",
            "售后服务": r"售后服务.*?(\d+)分"
        }
        
        for criteria, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                scoring[criteria] = int(matches[0])
        
        return scoring
    
    def detect_tender_type(self, content: str) -> str:
        """识别招标类型"""
        content_lower = content.lower()
        
        # 定义关键词映射
        type_keywords = {
            "软件开发": ["软件开发", "系统开发", "应用开发", "程序开发"],
            "系统集成": ["系统集成", "集成项目", "信息化建设"],
            "智慧城市": ["智慧城市", "智能城市", "城市大脑"],
            "网络建设": ["网络建设", "网络工程", "通信工程"],
            "数据中心": ["数据中心", "机房建设", "服务器"],
            "安防监控": ["安防", "监控", "视频监控"],
            "通用项目": []  # 默认类型
        }
        
        for tender_type, keywords in type_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return tender_type
        
        return "通用项目"
    
    def _extract_project_name(self, content: str) -> str:
        """提取项目名称"""
        patterns = [
            r"项目名称[：:]\s*(.+?)(?:\n|。|，)",
            r"招标项目[：:]\s*(.+?)(?:\n|。|，)",
            r"项目[：:]\s*(.+?)(?:\n|。|，)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        return "未识别"
    
    def _extract_tender_unit(self, content: str) -> str:
        """提取招标单位"""
        patterns = [
            r"招标人[：:]\s*(.+?)(?:\n|。|，)",
            r"采购人[：:]\s*(.+?)(?:\n|。|，)",
            r"招标单位[：:]\s*(.+?)(?:\n|。|，)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        return "未识别"
    
    def _extract_budget(self, content: str) -> str:
        """提取预算信息"""
        patterns = [
            r"预算[：:]?\s*([0-9,，.万元千百十亿]+)",
            r"投资额[：:]?\s*([0-9,，.万元千百十亿]+)",
            r"最高限价[：:]?\s*([0-9,，.万元千百十亿]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        return "未识别"
    
    def _extract_duration(self, content: str) -> str:
        """提取项目周期"""
        patterns = [
            r"工期[：:]?\s*(\d+[个月天年]+)",
            r"项目周期[：:]?\s*(\d+[个月天年]+)",
            r"建设周期[：:]?\s*(\d+[个月天年]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        return "未识别"
    
    def _extract_requirements(self, content: str) -> List[str]:
        """提取技术要求"""
        requirements = []
        
        # 查找技术要求相关段落
        tech_sections = re.findall(
            r"(?:技术要求|功能要求|性能要求)[：:]?(.*?)(?=\n\n|\n[一二三四五六七八九十]|$)",
            content, re.DOTALL
        )
        
        for section in tech_sections:
            # 提取列表项
            items = re.findall(r"[0-9]+[.、]\s*(.+?)(?=\n|$)", section)
            requirements.extend([item.strip() for item in items if item.strip()])
        
        return requirements[:10]  # 限制数量
    
    def _extract_scoring_criteria(self, content: str) -> Dict[str, int]:
        """提取评分标准"""
        return self.analyze_scoring_criteria(content)
    
    def _extract_deadline(self, content: str) -> str:
        """提取投标截止时间"""
        patterns = [
            r"投标截止时间[：:]?\s*(\d{4}年\d{1,2}月\d{1,2}日)",
            r"递交投标文件截止时间[：:]?\s*(\d{4}年\d{1,2}月\d{1,2}日)",
            r"投标文件递交截止时间[：:]?\s*(\d{4}年\d{1,2}月\d{1,2}日)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        return "未识别"
    
    def _extract_contact_info(self, content: str) -> Dict[str, str]:
        """提取联系信息"""
        contact = {}
        
        # 联系人
        contact_pattern = r"联系人[：:]?\s*(.+?)(?:\n|电话|手机)"
        match = re.search(contact_pattern, content)
        if match:
            contact["person"] = match.group(1).strip()
        
        # 电话
        phone_pattern = r"(?:电话|联系电话)[：:]?\s*([0-9\-]+)"
        match = re.search(phone_pattern, content)
        if match:
            contact["phone"] = match.group(1).strip()
        
        return contact
    
    def _extract_technical_specs(self, content: str) -> List[str]:
        """提取技术规格"""
        specs = []
        
        # 查找技术规格相关内容
        spec_patterns = [
            r"技术规格[：:]?(.*?)(?=\n\n|\n[一二三四五六七八九十]|$)",
            r"技术参数[：:]?(.*?)(?=\n\n|\n[一二三四五六七八九十]|$)",
            r"性能指标[：:]?(.*?)(?=\n\n|\n[一二三四五六七八九十]|$)"
        ]
        
        for pattern in spec_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                items = re.findall(r"[0-9]+[.、]\s*(.+?)(?=\n|$)", match)
                specs.extend([item.strip() for item in items if item.strip()])
        
        return specs[:15]  # 限制数量
    
    def _extract_qualification_requirements(self, content: str) -> List[str]:
        """提取资质要求"""
        qualifications = []
        
        # 查找资质要求相关内容
        qual_patterns = [
            r"资质要求[：:]?(.*?)(?=\n\n|\n[一二三四五六七八九十]|$)",
            r"投标人资格[：:]?(.*?)(?=\n\n|\n[一二三四五六七八九十]|$)",
            r"资格条件[：:]?(.*?)(?=\n\n|\n[一二三四五六七八九十]|$)"
        ]
        
        for pattern in qual_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                items = re.findall(r"[0-9]+[.、]\s*(.+?)(?=\n|$)", match)
                qualifications.extend([item.strip() for item in items if item.strip()])
        
        return qualifications[:10]  # 限制数量 