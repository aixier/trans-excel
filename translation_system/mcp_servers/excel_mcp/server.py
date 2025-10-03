#!/usr/bin/env python3
"""Excel MCP Server - stdio and HTTP entry point."""

import asyncio
import json
import sys
import logging
from typing import Any, Dict
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from aiohttp import web
import aiohttp_cors

from mcp_tools import get_tool_list
from mcp_handler import mcp_handler
from utils.session_manager import session_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/excel_mcp.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Create MCP server
app = Server("excel-mcp")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools."""
    tools = get_tool_list()

    mcp_tools = []
    for tool in tools:
        mcp_tools.append(
            types.Tool(
                name=tool["name"],
                description=tool["description"],
                inputSchema=tool["inputSchema"]
            )
        )

    return mcp_tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool calls."""
    try:
        logger.info(f"Tool called: {name}")

        # Handle tool call
        result = await mcp_handler.handle_tool_call(name, arguments)

        # Format response
        response_text = json.dumps(result, indent=2)

        return [
            types.TextContent(
                type="text",
                text=response_text
            )
        ]

    except Exception as e:
        logger.error(f"Error handling tool call {name}: {e}")
        error_response = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }
        return [
            types.TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )
        ]


async def cleanup_task():
    """Background task to clean up expired sessions."""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            session_manager.cleanup_expired_sessions(timeout_hours=8)
            logger.info("Session cleanup completed")
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")


async def http_tool_handler(request: web.Request) -> web.Response:
    """HTTP endpoint for MCP tool calls."""
    try:
        data = await request.json()
        tool_name = data.get('tool')
        arguments = data.get('arguments', {})

        if not tool_name:
            return web.json_response({'error': 'Missing tool name'}, status=400)

        logger.info(f"HTTP call to tool: {tool_name}")
        result = await mcp_handler.handle_tool_call(tool_name, arguments)
        return web.json_response(result)

    except Exception as e:
        logger.error(f"HTTP handler error: {e}", exc_info=True)
        return web.json_response({'error': str(e)}, status=500)


async def http_health(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({
        'status': 'healthy',
        'service': 'excel_mcp',
        'sessions': session_manager.get_session_count()
    })


async def http_redirect(request: web.Request) -> web.Response:
    """Redirect root to test page."""
    raise web.HTTPFound('/static/index.html')


async def run_http_server(port: int = 8889):
    """Run HTTP server for web testing."""
    http_app = web.Application()

    # Setup routes
    http_app.router.add_post('/mcp/tool', http_tool_handler)
    http_app.router.add_get('/health', http_health)
    http_app.router.add_get('/', http_redirect)

    # Serve static files
    static_dir = Path(__file__).parent / 'static'
    http_app.router.add_static('/static', static_dir, name='static')

    # Serve exported files
    exports_dir = Path(__file__).parent / 'exports'
    exports_dir.mkdir(exist_ok=True)
    http_app.router.add_static('/static/exports', exports_dir, name='exports')

    # Setup CORS
    cors = aiohttp_cors.setup(http_app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })

    for route in list(http_app.router.routes()):
        if not isinstance(route.resource, web.StaticResource):
            cors.add(route)

    # Start server
    runner = web.AppRunner(http_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    logger.info(f"HTTP Gateway started at http://localhost:{port}")
    logger.info(f"Test page: http://localhost:{port}/static/index.html")

    return runner


async def main():
    """Main entry point."""
    # Check if running in HTTP mode
    http_mode = '--http' in sys.argv or '-h' in sys.argv
    port = 8021  # Default port for excel_mcp

    # Parse port if provided
    for arg in sys.argv:
        if arg.startswith('--port='):
            port = int(arg.split('=')[1])

    logger.info(f"Starting Excel MCP Server (mode: {'HTTP' if http_mode else 'stdio'})...")

    # Start cleanup task
    cleanup_task_handle = asyncio.create_task(cleanup_task())

    try:
        if http_mode:
            # Run HTTP server
            runner = await run_http_server(port)
            await asyncio.Event().wait()  # Keep running
        else:
            # Run stdio server (for Claude Desktop)
            async with stdio_server() as (read_stream, write_stream):
                logger.info("Excel MCP Server is ready (stdio mode)")
                await app.run(
                    read_stream,
                    write_stream,
                    app.create_initialization_options()
                )
    finally:
        cleanup_task_handle.cancel()
        logger.info("Excel MCP Server stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
