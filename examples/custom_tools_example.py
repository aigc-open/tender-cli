#!/usr/bin/env python3
"""
Example of creating custom MCP tools by extending BaseMCPTools
"""

import sys
import os
import datetime
import json

# Add the src directory to the path so we can import tender_cli
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tender_cli.mcp_tools.base import BaseMCPTools

class CustomUtilityTools(BaseMCPTools):
    """Custom utility tools for various operations"""
    
    def __init__(self):
        super().__init__(name="Utility Tools", model_name="gpt-4")
    
    def _register_tools(self):
        """Register custom utility tools"""
        
        @self.mcp_server.tool()
        def get_current_time() -> str:
            """Get the current date and time"""
            return datetime.datetime.now().isoformat()
        
        @self.mcp_server.tool()
        def format_json(data: str) -> str:
            """Format a JSON string with proper indentation"""
            try:
                parsed = json.loads(data)
                return json.dumps(parsed, indent=2, ensure_ascii=False)
            except json.JSONDecodeError as e:
                return f"Invalid JSON: {str(e)}"
        
        @self.mcp_server.tool()
        def count_words(text: str) -> int:
            """Count the number of words in a text"""
            return len(text.split())
        
        @self.mcp_server.tool()
        def reverse_text(text: str) -> str:
            """Reverse the given text"""
            return text[::-1]
        
        @self.mcp_server.tool()
        def calculate_age(birth_year: int) -> int:
            """Calculate age based on birth year"""
            current_year = datetime.datetime.now().year
            return current_year - birth_year
        
        @self.mcp_server.tool()
        def generate_password(length: int = 12) -> str:
            """Generate a simple password (for demo purposes only)"""
            import string
            import random
            
            if length < 4:
                length = 4
            if length > 50:
                length = 50
                
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            return ''.join(random.choice(chars) for _ in range(length))
        
        # Store in registry
        self._tools_registry.update({
            'get_current_time': get_current_time,
            'format_json': format_json,
            'count_words': count_words,
            'reverse_text': reverse_text,
            'calculate_age': calculate_age,
            'generate_password': generate_password,
        })

def main():
    """Run the custom utility MCP server"""
    # Create custom tools instance
    utility_tools = CustomUtilityTools()
    
    # Create and configure the MCP server
    server = utility_tools.create_mcp_server()
    
    # Print available tools
    print("Available tools:")
    for tool_name in utility_tools.get_tools().keys():
        print(f"  - {tool_name}")
    
    print("\nStarting Custom Utility MCP Server...")
    utility_tools.run_mcp_server(transport="stdio")

if __name__ == "__main__":
    main() 