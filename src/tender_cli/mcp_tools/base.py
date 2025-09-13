import os
import asyncio
import shutil
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

from openai import OpenAI, AsyncOpenAI
from mcp.server.fastmcp import FastMCP

try:
    from agents import (
        Agent, Runner, gen_trace_id, trace, function_tool,
        set_default_openai_api, set_default_openai_client, set_tracing_disabled
    )
    from agents.mcp import MCPServer, MCPServerStdio
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    print("Warning: agents library not available. Some functionality will be limited.")


class BaseMCPTools(ABC):
    """Base class for MCP (Model Context Protocol) tools and servers"""
    
    def __init__(self, name: str = "MCP Tools", model_name: str = "gpt-4"):
        self.name = name
        self.model_name = model_name
        self.llm = None
        self.async_llm = None
        self.mcp_server = None
        self.agent = None
        self._tools_registry = {}
        
    def init_llm(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize synchronous OpenAI client"""
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        base_url = base_url or os.getenv("OPENAI_BASE_URL")
        
        if not api_key:
            raise ValueError("OpenAI API key is required")
            
        self.llm = OpenAI(api_key=api_key, base_url=base_url)
        
    def init_async_llm(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize asynchronous OpenAI client"""
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        base_url = base_url or os.getenv("OPENAI_BASE_URL")
        
        if not api_key:
            raise ValueError("OpenAI API key is required")
            
        self.async_llm = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        if AGENTS_AVAILABLE:
            set_default_openai_client(client=self.async_llm, use_for_tracing=False)
            set_default_openai_api("chat_completions")
            set_tracing_disabled(disabled=True)

    def create_mcp_server(self) -> FastMCP:
        """Create and configure MCP server with registered tools"""
        self.mcp_server = FastMCP(self.name)
        self._register_tools()
        return self.mcp_server
        
    @abstractmethod
    def _register_tools(self):
        """Register tools with the MCP server. Must be implemented by subclasses."""
        pass
    
    def register_tool(self, func, name: Optional[str] = None):
        """Register a tool function with the MCP server"""
        if not self.mcp_server:
            raise RuntimeError("MCP server not initialized. Call create_mcp_server() first.")
            
        tool_name = name or func.__name__
        self._tools_registry[tool_name] = func
        return self.mcp_server.tool()(func)
    
    async def create_agent(self, 
                          instructions: str = "Use the tools to answer questions.",
                          mcp_servers: Optional[List[MCPServer]] = None) -> Optional[Agent]:
        """Create an agent with MCP server integration"""
        if not AGENTS_AVAILABLE:
            print("Warning: agents library not available. Cannot create agent.")
            return None
            
        if not self.async_llm:
            self.init_async_llm()
            
        mcp_servers = mcp_servers or []
        
        self.agent = Agent(
            name=self.name,
            instructions=instructions,
            mcp_servers=mcp_servers,
            model=self.model_name,
        )
        return self.agent
    
    async def run_with_mcp_stdio(self, 
                                server_script: str,
                                message: str,
                                instructions: str = "Use the tools to answer questions.",
                                server_args: Optional[List[str]] = None) -> str:
        """Run agent with MCP server via stdio"""
        if not AGENTS_AVAILABLE:
            raise RuntimeError("agents library not available")
            
        if not self.async_llm:
            self.init_async_llm()
        
        server_args = server_args or []
        
        async with MCPServerStdio(
            name=f"{self.name} server",
            params={
                "command": "python3",
                "args": [server_script] + server_args,
            },
        ) as server:
            agent = await self.create_agent(instructions=instructions, mcp_servers=[server])
            
            trace_id = gen_trace_id()
            with trace(workflow_name=f"{self.name} Example", trace_id=trace_id):
                print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
                print(f"Running: {message}")
                
                result = await Runner.run(starting_agent=agent, input=message)
                return result.final_output
    
    async def run_agent(self, message: str) -> str:
        """Run the agent with a message"""
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call create_agent() first.")
            
        result = await Runner.run(starting_agent=self.agent, input=message)
        return result.final_output
    
    def run_mcp_server(self, transport: str = "stdio"):
        """Run the MCP server"""
        if not self.mcp_server:
            raise RuntimeError("MCP server not initialized. Call create_mcp_server() first.")
            
        self.mcp_server.run(transport=transport)
    
    def get_tools(self) -> Dict[str, Any]:
        """Get registered tools"""
        return self._tools_registry.copy()

    def get_tool_by_name(self, name: str) -> Optional[Any]:
        """Get a specific tool by name"""
        return self._tools_registry.get(name)
    
    @staticmethod
    def check_dependencies():
        """Check if required dependencies are available"""
        missing = []
        
        if not shutil.which("python3"):
            missing.append("python3")
            
        if not AGENTS_AVAILABLE:
            missing.append("agents library")
            
        return missing


class MCPMathTools(BaseMCPTools):
    """Example implementation of MCP tools for math operations"""
    
    def __init__(self):
        super().__init__(name="Math", model_name="gpt-4")
    
    def _register_tools(self):
        """Register math tools"""
        @self.mcp_server.tool()
        def add(a: int, b: int) -> int:
            """Add two numbers"""
            return a + b
        
        @self.mcp_server.tool()
        def multiply(a: int, b: int) -> int:
            """Multiply two numbers"""
            return a * b
        
        @self.mcp_server.tool()
        def subtract(a: int, b: int) -> int:
            """Subtract two numbers"""
            return a - b
        
        @self.mcp_server.tool()
        def divide(a: float, b: float) -> float:
            """Divide two numbers"""
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b
        
        # Store in registry
        self._tools_registry.update({
            'add': add,
            'multiply': multiply,
            'subtract': subtract,
            'divide': divide
        })