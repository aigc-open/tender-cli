# MCP Base Class Usage Guide

This guide shows how to use the enhanced `BaseMCPTools` class to create MCP (Model Context Protocol) servers and clients.

## Overview

The `BaseMCPTools` class provides a foundation for creating MCP tools with the following features:

- **Async/Sync OpenAI client support**
- **MCP server creation and management**
- **Agent integration with tracing**
- **Tool registration and management**
- **Stdio transport support**

## Quick Start

### 1. Create a Custom MCP Server

```python
from tender_cli.mcp_tools.base import BaseMCPTools

class MyCustomTools(BaseMCPTools):
    def __init__(self):
        super().__init__(name="My Tools", model_name="gpt-4")
    
    def _register_tools(self):
        @self.mcp_server.tool()
        def my_function(param: str) -> str:
            """Description of my function"""
            return f"Processed: {param}"
        
        # Store in registry
        self._tools_registry['my_function'] = my_function

# Usage
tools = MyCustomTools()
server = tools.create_mcp_server()
tools.run_mcp_server()  # Runs with stdio transport
```

### 2. Create a Client to Use MCP Server

```python
import asyncio
from tender_cli.mcp_tools.base import BaseMCPTools

class MyClient(BaseMCPTools):
    def __init__(self):
        super().__init__(name="My Client")
    
    def _register_tools(self):
        pass  # No tools for client

async def main():
    client = MyClient()
    client.init_async_llm()  # Requires OPENAI_API_KEY
    
    result = await client.run_with_mcp_stdio(
        server_script="my_server.py",
        message="Hello, use my tools!",
        instructions="Use the available tools to help the user."
    )
    print(result)

asyncio.run(main())
```

## Examples

### Math Server Example

See `math_server_example.py` and `math_client_example.py` for a complete working example with:
- Addition, subtraction, multiplication, division tools
- Client that asks math questions
- Error handling and dependency checking

### Custom Utility Tools

See `custom_tools_example.py` for examples of:
- Time/date functions
- Text processing tools
- JSON formatting
- Password generation

## Environment Setup

### Required Environment Variables

```bash
export OPENAI_API_KEY="your-api-key-here"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # Optional
```

### Dependencies

The base class requires:
- `openai` - OpenAI Python client
- `mcp` - Model Context Protocol library
- `agents` - OpenAI agents library (optional, for advanced features)

Install with:
```bash
pip install openai mcp-server agents
```

## Key Methods

### BaseMCPTools Methods

| Method | Description |
|--------|-------------|
| `init_llm()` | Initialize synchronous OpenAI client |
| `init_async_llm()` | Initialize asynchronous OpenAI client |
| `create_mcp_server()` | Create FastMCP server with registered tools |
| `run_mcp_server()` | Run the MCP server (stdio transport) |
| `create_agent()` | Create an agent with MCP integration |
| `run_with_mcp_stdio()` | Run agent with external MCP server |
| `get_tools()` | Get dictionary of registered tools |
| `check_dependencies()` | Check for required system dependencies |

### Abstract Methods

You must implement:
- `_register_tools()` - Register your custom tools with the MCP server

## Advanced Usage

### Custom Agent Instructions

```python
await client.run_with_mcp_stdio(
    server_script="server.py",
    message="Calculate something complex",
    instructions="""
    You are a math expert. Always:
    1. Show your work step by step
    2. Verify calculations
    3. Explain the reasoning
    """
)
```

### Multiple MCP Servers

```python
# Create agent with multiple MCP servers
agent = await client.create_agent(
    instructions="Use all available tools",
    mcp_servers=[math_server, utility_server, file_server]
)
```

### Error Handling

```python
# Check dependencies before running
missing = BaseMCPTools.check_dependencies()
if missing:
    print(f"Missing: {', '.join(missing)}")
    return

# Handle LLM initialization errors
try:
    client.init_async_llm()
except ValueError as e:
    print(f"LLM setup failed: {e}")
```

## Best Practices

1. **Always implement `_register_tools()`** - This is where you define your MCP tools
2. **Set environment variables** - Ensure `OPENAI_API_KEY` is set
3. **Check dependencies** - Use `check_dependencies()` before running
4. **Handle errors gracefully** - Wrap async operations in try/catch
5. **Use descriptive tool docstrings** - They become part of the tool schema
6. **Store tools in registry** - Update `self._tools_registry` for tool management

## Troubleshooting

### Common Issues

1. **"agents library not available"** - Install with `pip install agents`
2. **"OpenAI API key is required"** - Set `OPENAI_API_KEY` environment variable
3. **"python3 not found"** - Ensure Python 3 is installed and in PATH
4. **Server connection issues** - Check that server script path is correct

### Debug Tips

- Enable tracing by setting appropriate environment variables
- Check server logs for tool registration issues
- Verify tool function signatures match expected types
- Test tools individually before integrating with agents 