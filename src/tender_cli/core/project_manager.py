"""
项目管理模块
"""

import json
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import uuid

from .config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ProjectManager:
    """项目管理器"""
    
    def __init__(self, config: Config, project_path: Optional[str] = None):
        self.config = config
        self.workspace_dir = config.workspace_dir
        self.current_project: Optional[Path] = None
        self.current_project_name: Optional[str] = None
        
        # 如果指定了项目路径，尝试加载
        if project_path:
            self.load_project(project_path)
    
    def create_project(self, name: str) -> Path:
        """创建新项目"""
        # 清理项目名称
        safe_name = self._sanitize_name(name)
        project_dir = self.workspace_dir / safe_name
        
        # 检查项目是否已存在
        if project_dir.exists():
            raise ValueError(f"项目 '{name}' 已存在")
        
        # 创建项目目录结构
        project_dir.mkdir(parents=True)
        
        # 创建标准目录结构
        directories = [
            "sections",  # 章节内容目录
            "assets",    # 资源文件
            "output",    # 输出文件
            "backup",    # 备份文件
            "temp"       # 临时文件
        ]
        
        for dir_name in directories:
            (project_dir / dir_name).mkdir()
        
        # 创建项目配置文件
        project_config = {
            "name": name,
            "id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "description": "",
            "tender_info": {},
            "outline": {},
            "settings": {
                "auto_save": True,
                "backup_enabled": True
            }
        }
        
        config_file = project_dir / "project.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(project_config, f, ensure_ascii=False, indent=2)
        
        # 创建README文件
        readme_content = f"""# {name}

## 项目信息
- 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 项目ID: {project_config['id']}

## 目录结构
```
{safe_name}/
├── sections/          # 章节内容
├── assets/           # 资源文件
├── output/           # 输出文件
├── backup/           # 备份文件
├── temp/             # 临时文件
├── project.json      # 项目配置
└── README.md         # 项目说明
```

## 使用说明
使用 Tender AI 智能助手进行标书制作。
"""
        
        readme_file = project_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # 设置为当前项目
        self.current_project = project_dir
        self.current_project_name = name
        
        logger.info(f"Created project: {name} at {project_dir}")
        return project_dir
    
    def load_project(self, project_path: str) -> bool:
        """加载项目"""
        project_dir = Path(project_path)
        
        if not project_dir.exists():
            # 尝试在工作目录中查找
            project_dir = self.workspace_dir / project_path
        
        if not project_dir.exists():
            raise ValueError(f"项目不存在: {project_path}")
        
        config_file = project_dir / "project.json"
        if not config_file.exists():
            raise ValueError(f"无效的项目目录: {project_dir}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                project_config = json.load(f)
            
            self.current_project = project_dir
            self.current_project_name = project_config.get("name", project_dir.name)
            
            logger.info(f"Loaded project: {self.current_project_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            return False
    
    def switch_project(self, name: str):
        """切换项目"""
        project_dir = self.workspace_dir / self._sanitize_name(name)
        
        if not project_dir.exists():
            raise ValueError(f"项目不存在: {name}")
        
        self.load_project(str(project_dir))
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """列出所有项目"""
        projects = []
        
        if not self.workspace_dir.exists():
            return projects
        
        for item in self.workspace_dir.iterdir():
            if item.is_dir():
                config_file = item / "project.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        projects.append({
                            "name": config.get("name", item.name),
                            "path": str(item),
                            "created_time": config.get("created_at", ""),
                            "updated_time": config.get("updated_at", ""),
                            "is_current": item == self.current_project
                        })
                    except Exception:
                        continue
        
        return sorted(projects, key=lambda x: x["updated_time"], reverse=True)
    
    def save_outline(self, outline: Dict[str, Any]):
        """保存大纲"""
        if not self.current_project:
            raise ValueError("没有活动项目")
        
        # 更新项目配置
        self._update_project_config({"outline": outline})
        
        # 创建章节目录结构
        sections_dir = self.current_project / "sections"
        
        for i, section in enumerate(outline.get("sections", []), 1):
            section_name = f"{i:02d}-{self._sanitize_name(section.get('title', ''))}"
            section_dir = sections_dir / section_name
            section_dir.mkdir(exist_ok=True)
            
            # 创建小节文件占位符
            for j, subsection in enumerate(section.get("subsections", []), 1):
                subsection_name = f"{i}.{j}-{self._sanitize_name(subsection)}"
                subsection_file = section_dir / f"{subsection_name}.md"
                
                if not subsection_file.exists():
                    subsection_file.write_text(
                        f"# {subsection}\n\n<!-- 内容待生成 -->\n",
                        encoding='utf-8'
                    )
    
    def save_subsection(self, section: str, subsection: str, content: str):
        """保存小节内容"""
        if not self.current_project:
            raise ValueError("没有活动项目")
        
        sections_dir = self.current_project / "sections"
        
        # 查找对应的文件
        section_dir = None
        for dir_item in sections_dir.iterdir():
            if dir_item.is_dir() and section.lower() in dir_item.name.lower():
                section_dir = dir_item
                break
        
        if not section_dir:
            raise ValueError(f"找不到章节目录: {section}")
        
        # 查找小节文件
        subsection_file = None
        for file_item in section_dir.iterdir():
            if file_item.is_file() and subsection.lower() in file_item.name.lower():
                subsection_file = file_item
                break
        
        if not subsection_file:
            # 创建新文件
            safe_name = self._sanitize_name(subsection)
            subsection_file = section_dir / f"{safe_name}.md"
        
        # 保存内容
        subsection_file.write_text(content, encoding='utf-8')
        
        # 更新项目时间
        self._update_project_config({"updated_at": datetime.now().isoformat()})
    
    def get_section_structure(self, section: str) -> Dict[str, Any]:
        """获取章节结构"""
        if not self.current_project:
            raise ValueError("没有活动项目")
        
        sections_dir = self.current_project / "sections"
        
        # 查找章节目录
        section_dir = None
        for dir_item in sections_dir.iterdir():
            if dir_item.is_dir() and section.lower() in dir_item.name.lower():
                section_dir = dir_item
                break
        
        if not section_dir:
            return {"files": []}
        
        files = []
        for file_item in section_dir.iterdir():
            if file_item.is_file() and file_item.suffix == '.md':
                content = file_item.read_text(encoding='utf-8')
                files.append({
                    "name": file_item.name,
                    "path": str(file_item),
                    "exists": True,
                    "size": len(content),
                    "word_count": len(content.replace('#', '').replace('-', '').split())
                })
        
        return {"files": files}
    
    def get_project_structure(self) -> Dict[str, Any]:
        """获取项目结构"""
        if not self.current_project:
            return {}
        
        sections_dir = self.current_project / "sections"
        structure = {"sections": []}
        
        if sections_dir.exists():
            for section_dir in sorted(sections_dir.iterdir()):
                if section_dir.is_dir():
                    section_info = {
                        "name": section_dir.name,
                        "files": []
                    }
                    
                    for file_item in sorted(section_dir.iterdir()):
                        if file_item.is_file() and file_item.suffix == '.md':
                            content = file_item.read_text(encoding='utf-8')
                            section_info["files"].append({
                                "name": file_item.name,
                                "size": len(content),
                                "exists": "<!-- 内容待生成 -->" not in content
                            })
                    
                    structure["sections"].append(section_info)
        
        return structure
    
    def backup_current_project(self) -> str:
        """备份当前项目"""
        if not self.current_project:
            raise ValueError("没有活动项目")
        
        backup_dir = self.current_project / "backup"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = backup_dir / backup_name
        
        # 创建备份
        shutil.copytree(
            self.current_project / "sections",
            backup_path / "sections"
        )
        
        # 复制项目配置
        shutil.copy2(
            self.current_project / "project.json",
            backup_path / "project.json"
        )
        
        return str(backup_path)
    
    def _sanitize_name(self, name: str) -> str:
        """清理名称，移除非法字符"""
        # 移除或替换非法字符
        safe_name = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "_-")
        return safe_name[:50]  # 限制长度
    
    def _update_project_config(self, updates: Dict[str, Any]):
        """更新项目配置"""
        if not self.current_project:
            return
        
        config_file = self.current_project / "project.json"
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            config.update(updates)
            config["updated_at"] = datetime.now().isoformat()
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to update project config: {e}")
    
    @property
    def sections_dir(self) -> Optional[Path]:
        """获取章节目录"""
        if self.current_project:
            return self.current_project / "sections"
        return None
    
    @property
    def output_dir(self) -> Optional[Path]:
        """获取输出目录"""
        if self.current_project:
            return self.current_project / "output"
        return None 