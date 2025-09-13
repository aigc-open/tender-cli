#!/usr/bin/env python3
"""
Tender CLI 基本使用示例
"""

import sys
from pathlib import Path

# 添加项目路径到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from tender_cli.core.config import Config
from tender_cli.core.tender_ai import TenderAI


def main():
    """基本使用示例"""
    print("🎯 Tender AI 基本使用示例\n")
    
    # 1. 初始化配置
    print("1. 初始化配置...")
    config = Config()
    
    # 2. 创建 AI 助手实例
    print("2. 创建 AI 助手...")
    ai = TenderAI(config)
    
    # 3. 模拟对话
    print("3. 开始对话示例...\n")
    
    # 示例对话
    messages = [
        "创建新项目：智慧城市建设项目",
        "生成标书大纲",
        "查看项目结构",
        "导出Word文档"
    ]
    
    for message in messages:
        print(f"👤 用户: {message}")
        try:
            response = ai.process_message(message)
            print(f"🤖 助手: {response}\n")
        except Exception as e:
            print(f"❌ 错误: {e}\n")
    
    print("✅ 示例完成！")


if __name__ == "__main__":
    main() 