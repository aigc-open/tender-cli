#!/usr/bin/env python3
"""
Example MCP Math Server using the BaseMCPTools class
"""

import sys
import os

# Add the src directory to the path so we can import tender_cli
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tender_cli.mcp_tools.base import MCPMathTools

def main():
    """Run the math MCP server"""
    # Create math tools instance
    math_tools = MCPMathTools()
    
    # Create and configure the MCP server
    server = math_tools.create_mcp_server()
    
    # Run the server with stdio transport
    print("Starting Math MCP Server...")
    math_tools.run_mcp_server(transport="stdio")

if __name__ == "__main__":
    main() 