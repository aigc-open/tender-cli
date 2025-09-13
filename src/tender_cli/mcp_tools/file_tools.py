"""
文件操作工具
"""

import os
from pathlib import Path
from typing import List, Dict, Any
import json

from ..utils.logger import get_logger

logger = get_logger(__name__)


class FileTools:
    """文件操作工具集"""
    
    def __init__(self):
        self.current_project_dir = None
    
    def set_project_dir(self, project_dir: Path):
        """设置当前项目目录"""
        self.current_project_dir = project_dir
    
    def read_file(self, path: str) -> str:
        """读取文件内容"""
        try:
            file_path = Path(path)
            if not file_path.is_absolute() and self.current_project_dir:
                file_path = self.current_project_dir / path
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            raise
    
    def write_file(self, path: str, content: str) -> bool:
        """写入文件"""
        try:
            file_path = Path(path)
            if not file_path.is_absolute() and self.current_project_dir:
                file_path = self.current_project_dir / path
            
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"File written: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            return False
    
    def list_files(self, directory: str) -> List[str]:
        """列出目录文件"""
        try:
            dir_path = Path(directory)
            if not dir_path.is_absolute() and self.current_project_dir:
                dir_path = self.current_project_dir / directory
            
            if not dir_path.exists():
                return []
            
            files = []
            for item in dir_path.iterdir():
                if item.is_file():
                    files.append(str(item.relative_to(dir_path)))
                elif item.is_dir():
                    files.append(f"{item.name}/")
            
            return sorted(files)
        except Exception as e:
            logger.error(f"Failed to list files in {directory}: {e}")
            return []
    
    def create_directory(self, path: str) -> bool:
        """创建目录"""
        try:
            dir_path = Path(path)
            if not dir_path.is_absolute() and self.current_project_dir:
                dir_path = self.current_project_dir / path
            
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory created: {dir_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False
    
    def delete_file(self, path: str) -> bool:
        """删除文件"""
        try:
            file_path = Path(path)
            if not file_path.is_absolute() and self.current_project_dir:
                file_path = self.current_project_dir / path
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted: {file_path}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            return False
    
    def read_subsection_file(self, section: str, subsection: str) -> str:
        """读取三级标题内容文件"""
        if not self.current_project_dir:
            raise ValueError("No project directory set")
        
        sections_dir = self.current_project_dir / "sections"
        
        # 查找章节目录
        section_dir = self._find_section_dir(sections_dir, section)
        if not section_dir:
            raise ValueError(f"Section not found: {section}")
        
        # 查找小节文件
        subsection_file = self._find_subsection_file(section_dir, subsection)
        if not subsection_file:
            raise ValueError(f"Subsection not found: {subsection}")
        
        return self.read_file(str(subsection_file))
    
    def write_subsection_file(self, section: str, subsection: str, content: str) -> bool:
        """写入三级标题内容"""
        if not self.current_project_dir:
            raise ValueError("No project directory set")
        
        sections_dir = self.current_project_dir / "sections"
        
        # 查找或创建章节目录
        section_dir = self._find_section_dir(sections_dir, section)
        if not section_dir:
            # 创建新的章节目录
            safe_section = self._sanitize_name(section)
            section_dir = sections_dir / safe_section
            section_dir.mkdir(parents=True, exist_ok=True)
        
        # 查找或创建小节文件
        subsection_file = self._find_subsection_file(section_dir, subsection)
        if not subsection_file:
            safe_subsection = self._sanitize_name(subsection)
            subsection_file = section_dir / f"{safe_subsection}.md"
        
        return self.write_file(str(subsection_file), content)
    
    def list_subsection_files(self, section: str) -> List[str]:
        """列出章节下所有三级标题文件"""
        if not self.current_project_dir:
            return []
        
        sections_dir = self.current_project_dir / "sections"
        section_dir = self._find_section_dir(sections_dir, section)
        
        if not section_dir:
            return []
        
        files = []
        for item in section_dir.iterdir():
            if item.is_file() and item.suffix == '.md':
                files.append(item.name)
        
        return sorted(files)
    
    def get_section_structure(self) -> Dict[str, Any]:
        """获取完整的章节结构"""
        if not self.current_project_dir:
            return {}
        
        sections_dir = self.current_project_dir / "sections"
        if not sections_dir.exists():
            return {}
        
        structure = {"sections": []}
        
        for section_dir in sorted(sections_dir.iterdir()):
            if section_dir.is_dir():
                section_info = {
                    "name": section_dir.name,
                    "path": str(section_dir),
                    "subsections": []
                }
                
                for file_item in sorted(section_dir.iterdir()):
                    if file_item.is_file() and file_item.suffix == '.md':
                        content = file_item.read_text(encoding='utf-8')
                        section_info["subsections"].append({
                            "name": file_item.name,
                            "path": str(file_item),
                            "size": len(content),
                            "word_count": len(content.split()),
                            "has_content": "<!-- 内容待生成 -->" not in content
                        })
                
                structure["sections"].append(section_info)
        
        return structure
    
    def _find_section_dir(self, sections_dir: Path, section: str) -> Path:
        """查找章节目录"""
        if not sections_dir.exists():
            return None
        
        section_lower = section.lower()
        
        for item in sections_dir.iterdir():
            if item.is_dir():
                if (section_lower in item.name.lower() or 
                    item.name.lower() in section_lower):
                    return item
        
        return None
    
    def _find_subsection_file(self, section_dir: Path, subsection: str) -> Path:
        """查找小节文件"""
        if not section_dir.exists():
            return None
        
        subsection_lower = subsection.lower()
        
        for item in section_dir.iterdir():
            if item.is_file() and item.suffix == '.md':
                if (subsection_lower in item.name.lower() or 
                    item.name.lower() in subsection_lower):
                    return item
        
        return None
    
    def _sanitize_name(self, name: str) -> str:
        """清理文件名"""
        safe_name = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "_-.")
        return safe_name[:100]  # 限制长度 