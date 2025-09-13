#!/usr/bin/env python3
"""
Example MCP Math Client using the BaseMCPTools class
"""

import asyncio
import sys
import os

# Add the src directory to the path so we can import tender_cli
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tender_cli.mcp_tools.base import BaseMCPTools

class MathClient(BaseMCPTools):
    """Client for interacting with math MCP server"""
    
    def __init__(self):
        super().__init__(name="Math Client", model_name="gpt-4")
    
    def _register_tools(self):
        """No tools to register for client"""
        pass

async def main():
    """Run the math client example"""
    # Check dependencies
    missing_deps = BaseMCPTools.check_dependencies()
    if missing_deps:
        print(f"Missing dependencies: {', '.join(missing_deps)}")
        return
    
    # Create client instance
    client = MathClient()
    
    # Initialize async LLM (you'll need to set OPENAI_API_KEY and optionally OPENAI_BASE_URL)
    try:
        client.init_async_llm()
    except ValueError as e:
        print(f"Error initializing LLM: {e}")
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    # Path to the math server script
    server_script = os.path.join(os.path.dirname(__file__), "math_server_example.py")
    
    # Test questions
    questions = [
        "what's (3 + 5) x 12?",
        "Calculate 15 divided by 3, then multiply by 7",
        "What is 100 - 25 + 10?",
    ]
    
    for question in questions:
        try:
            print(f"\n{'='*50}")
            print(f"Question: {question}")
            print(f"{'='*50}")
            
            result = await client.run_with_mcp_stdio(
                server_script=server_script,
                message=question,
                instructions="Use the math tools to calculate the answer step by step. Show your work."
            )
            
            print(f"Answer: {result}")
            
        except Exception as e:
            print(f"Error processing question '{question}': {e}")

if __name__ == "__main__":
    asyncio.run(main()) 