"""
配置管理模块
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()


class Config:
    """配置管理类"""
    
    def __init__(self, config_path: Optional[str] = None, debug: bool = False):
        self.debug = debug
        self.config_path = Path(config_path) if config_path else self._get_default_config_path()
        self.config_dir = self.config_path.parent
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self._config: Dict[str, Any] = {}
        self._load_env_file()  # 首先加载 .env 文件
        self._load_config()
    
    def _load_env_file(self):
        """加载 .env 文件"""
        env_files = [
            Path.cwd() / ".env",
            Path.home() / ".env",
            self.config_dir / ".env"
        ]
        
        for env_file in env_files:
            if env_file.exists():
                try:
                    with open(env_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                os.environ[key.strip()] = value.strip().strip('"\'')
                    if self.debug:
                        console.print(f"[dim]Loaded .env from: {env_file}[/dim]")
                    break
                except Exception as e:
                    if self.debug:
                        console.print(f"[yellow]Warning: Failed to load {env_file}: {e}[/yellow]")
    
    def _get_default_config_path(self) -> Path:
        """获取默认配置文件路径"""
        home = Path.home()
        return home / ".tender" / "config.yaml"
    
    def _load_config(self):
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if self.config_path.suffix.lower() == '.json':
                        self._config = json.load(f)
                    else:
                        self._config = yaml.safe_load(f) or {}
            except Exception as e:
                console.print(f"[red]配置文件加载失败: {e}[/red]")
                self._config = {}
        else:
            self._config = self._get_default_config()
        
        # 从环境变量覆盖配置
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        env_mappings = {
            "OPENAI_API_KEY": "ai.api_key",
            "OPENAI_BASE_URL": "ai.base_url",
            "OPENAI_MODEL": "ai.model",
            "AI_PROVIDER": "ai.provider",
            "TENDER_WORKSPACE": "project.default_workspace",
            "TENDER_DEBUG": "debug"
        }
        
        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value:
                self._set_nested_config(config_key, env_value)
                if self.debug:
                    console.print(f"[dim]Loaded {config_key} from env: {env_key}[/dim]")
    
    def _set_nested_config(self, key: str, value: Any):
        """设置嵌套配置值"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 类型转换
        if keys[-1] == "debug" and isinstance(value, str):
            value = value.lower() in ('true', '1', 'yes', 'on')
        
        config[keys[-1]] = value
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "ai": {
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "",
                "base_url": "",
                "temperature": 0.7,
                "max_tokens": 4000
            },
            "project": {
                "default_workspace": str(Path.home() / "tender_projects"),
                "auto_backup": True,
                "backup_interval": 3600  # 1小时
            },
            "document": {
                "default_template": "standard",
                "font_family": "宋体",
                "font_size": 12,
                "line_spacing": 1.5
            },
            "mcp": {
                "server_port": 8080,
                "timeout": 30,
                "max_workers": 24
            }
        }
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
        except Exception as e:
            console.print(f"[red]配置文件保存失败: {e}[/red]")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        api_key = self.get("ai.api_key")
        # 如果有API密钥或者有base_url（自定义端点），认为已配置
        base_url = self.get("ai.base_url")
        return bool((api_key and api_key.strip()) or (base_url and base_url.strip()))
    
    def setup_interactive(self):
        """交互式配置设置"""
        console.print("[bold blue]🔧 Tender AI 初始配置[/bold blue]\n")
        
        # 检查是否已有环境变量配置
        if os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_BASE_URL"):
            console.print("[green]✅ 检测到环境变量配置，跳过交互式配置[/green]")
            return
        
        # AI 配置
        console.print("[yellow]1. AI 服务配置[/yellow]")
        
        provider = Prompt.ask(
            "选择 AI 服务提供商",
            choices=["openai", "azure", "claude", "local"],
            default="openai"
        )
        self.set("ai.provider", provider)
        
        if provider == "openai":
            api_key = Prompt.ask("请输入 OpenAI API Key (可选，如使用自定义端点)", password=True, default="")
            if api_key:
                self.set("ai.api_key", api_key)
            
            base_url = Prompt.ask(
                "API Base URL (可选，用于代理或自定义端点)",
                default=""
            )
            if base_url:
                self.set("ai.base_url", base_url)
            
            model = Prompt.ask(
                "选择模型",
                default="gpt-4"
            )
            self.set("ai.model", model)
        
        # 项目配置
        console.print("\n[yellow]2. 项目配置[/yellow]")
        
        workspace = Prompt.ask(
            "默认工作目录",
            default=str(Path.home() / "tender_projects")
        )
        self.set("project.default_workspace", workspace)
        
        # 创建工作目录
        workspace_path = Path(workspace).expanduser()
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        auto_backup = Confirm.ask("启用自动备份", default=True)
        self.set("project.auto_backup", auto_backup)
        
        console.print("\n[green]✅ 配置完成！[/green]")
        console.print(f"配置文件保存在: {self.config_path}")
    
    @property
    def workspace_dir(self) -> Path:
        """获取工作目录"""
        workspace = self.get("project.default_workspace")
        path = Path(workspace).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def ai_config(self) -> Dict[str, Any]:
        """获取AI配置"""
        return self.get("ai", {})
    
    @property
    def project_config(self) -> Dict[str, Any]:
        """获取项目配置"""
        return self.get("project", {})
    
    @property
    def document_config(self) -> Dict[str, Any]:
        """获取文档配置"""
        return self.get("document", {})
    
    @property
    def mcp_config(self) -> Dict[str, Any]:
        """获取MCP配置"""
        return self.get("mcp", {}) 