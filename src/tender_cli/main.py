#!/usr/bin/env python3
"""
Tender CLI - 主入口文件
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.markdown import Markdown
import sys
import os
from pathlib import Path

from .core.tender_ai import TenderAI
from .core.config import Config
from .utils.logger import setup_logger

console = Console()
logger = setup_logger()


def print_welcome():
    """显示欢迎界面"""
    welcome_text = Text()
    welcome_text.append("🎯 Tender AI - 标书智能体助手 v1.0.0\n\n", style="bold blue")
    welcome_text.append("👋 你好！我是你的标书智能助手，可以帮你完成标书的全流程工作。\n\n", style="green")
    welcome_text.append("💡 你可以：\n", style="yellow")
    welcome_text.append("• 上传招标文件让我分析\n", style="white")
    welcome_text.append("• 创建新的标书项目\n", style="white")
    welcome_text.append("• 继续之前的项目工作\n", style="white")
    welcome_text.append("• 询问标书相关问题\n\n", style="white")
    welcome_text.append("请告诉我你想做什么？", style="cyan")
    
    panel = Panel(
        welcome_text,
        title="[bold green]Tender AI Assistant[/bold green]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)


@click.command()
@click.option('--config', '-c', help='配置文件路径')
@click.option('--project', '-p', help='项目目录路径')
@click.option('--debug', '-d', is_flag=True, help='启用调试模式')
@click.version_option(version='1.0.0')
def main(config: str, project: str, debug: bool):
    """
    🎯 Tender AI - 智能标书助手
    
    通过自然语言对话完成标书的全流程生成和管理
    """
    try:
        # 初始化配置
        config_obj = Config(config_path=config, debug=debug)
        
        # 检查配置
        if not config_obj.is_configured():
            console.print("[yellow]首次使用需要配置 API 密钥...[/yellow]")
            config_obj.setup_interactive()
        
        # 初始化 AI 助手
        ai = TenderAI(config=config_obj)
        
        # 显示欢迎界面
        print_welcome()
        
        # 启动对话循环
        start_conversation(ai)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 再见！感谢使用 Tender AI[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]❌ 启动失败: {e}[/red]")
        if debug:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


def start_conversation(ai: TenderAI):
    """启动对话循环"""
    console.print("\n[dim]输入 'exit' 或 'quit' 退出，输入 'help' 查看帮助[/dim]\n")
    
    while True:
        try:
            # 获取用户输入
            user_input = Prompt.ask("[bold cyan]>[/bold cyan]", default="").strip()
            
            if not user_input:
                continue
                
            # 处理特殊命令
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("[yellow]👋 再见！[/yellow]")
                break
            elif user_input.lower() in ['help', 'h']:
                show_help()
                continue
            elif user_input.lower() == 'clear':
                console.clear()
                print_welcome()
                continue
            
            # 处理用户消息
            with console.status("[bold green]🤖 思考中...[/bold green]"):
                response = ai.process_message(user_input)
            
            # 显示回复
            if response:
                console.print()
                console.print(Markdown(response))
                console.print()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]👋 再见！[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]❌ 处理消息时出错: {e}[/red]")
            logger.error(f"Error processing message: {e}", exc_info=True)


def show_help():
    """显示帮助信息"""
    help_text = """
## 🎯 Tender AI 使用指南

### 基本命令
- `help` - 显示此帮助信息
- `clear` - 清屏
- `exit` / `quit` - 退出程序

### 常用对话示例

#### 📁 项目管理
- "创建新项目"
- "列出所有项目" 
- "切换到项目XXX"
- "备份当前项目"

#### 📄 文件处理
- "分析这个招标文件: /path/to/file.pdf"
- "上传招标文件让我分析"
- "提取PDF内容"

#### 📝 内容生成
- "生成标书大纲"
- "写第3章技术方案"
- "优化公司介绍部分"
- "生成项目时间表"

#### 📊 文档导出
- "导出Word文档"
- "一键生成标书"
- "转换为PDF"

#### 🔍 查看内容
- "查看第2章"
- "显示项目结构"
- "打开技术方案章节"

### 💡 提示
- 使用自然语言描述你的需求
- 可以随时中断和继续任务
- 支持多轮对话完成复杂任务
"""
    
    console.print(Markdown(help_text))


if __name__ == "__main__":
    main() 