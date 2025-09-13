"""
基本功能测试
"""

import pytest
import tempfile
from pathlib import Path

from tender_cli.core.config import Config
from tender_cli.core.project_manager import ProjectManager
from tender_cli.mcp_tools.file_tools import FileTools


class TestConfig:
    """配置测试"""
    
    def test_config_creation(self):
        """测试配置创建"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            config = Config(config_path=str(config_path))
            
            assert config.get("ai.provider") == "openai"
            assert config.get("ai.model") == "gpt-4"


class TestProjectManager:
    """项目管理测试"""
    
    def test_project_creation(self):
        """测试项目创建"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config()
            config.set("project.default_workspace", temp_dir)
            
            pm = ProjectManager(config)
            project_path = pm.create_project("测试项目")
            
            assert project_path.exists()
            assert (project_path / "project.json").exists()
            assert (project_path / "sections").exists()
    
    def test_project_listing(self):
        """测试项目列表"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config()
            config.set("project.default_workspace", temp_dir)
            
            pm = ProjectManager(config)
            pm.create_project("项目1")
            pm.create_project("项目2")
            
            projects = pm.list_projects()
            assert len(projects) == 2


class TestFileTools:
    """文件工具测试"""
    
    def test_file_operations(self):
        """测试文件操作"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tools = FileTools()
            tools.set_project_dir(Path(temp_dir))
            
            # 测试写入文件
            success = tools.write_file("test.txt", "测试内容")
            assert success
            
            # 测试读取文件
            content = tools.read_file("test.txt")
            assert content == "测试内容"
            
            # 测试目录创建
            success = tools.create_directory("test_dir")
            assert success
            assert (Path(temp_dir) / "test_dir").exists()


if __name__ == "__main__":
    pytest.main([__file__]) 