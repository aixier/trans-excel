#!/usr/bin/env python3
"""
LLM MCP Server - Translation Execution Engine
Supports both stdio (MCP) and HTTP modes
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from aiohttp import web
import aiohttp_cors

from mcp.server import Server
from mcp.server.stdio import stdio_server

from mcp_tools import get_llm_tools
from mcp_handler import MCPHandler
from utils.session_manager import session_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/llm_mcp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global MCP handler instance
mcp_handler = MCPHandler()


async def run_stdio_server():
    """Run the MCP stdio server."""
    logger.info("Starting LLM MCP stdio server...")

    # Create MCP server
    server = Server("llm-mcp")

    # Register tools
    tools = get_llm_tools()
    for tool in tools:
        server.add_tool(tool)

    # Register tool handler
    @server.tool_handler
    async def handle_tool(name: str, arguments: dict):
        logger.info(f"MCP tool called: {name}")
        try:
            result = await mcp_handler.handle_tool_call(name, arguments)
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return {"error": str(e)}

    # Start server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("LLM MCP stdio server is running")

        # Start background cleanup task
        asyncio.create_task(session_cleanup_task())

        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


async def session_cleanup_task():
    """Background task to cleanup expired sessions."""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            expired = session_manager.cleanup_expired()
            if expired > 0:
                logger.info(f"Cleaned up {expired} expired sessions")
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")


async def http_tool_handler(request: web.Request) -> web.Response:
    """Handle HTTP tool calls."""
    try:
        logger.info("=" * 80)
        logger.info(f"HTTP Request received from {request.remote}")
        data = await request.json()
        tool_name = data.get('tool')
        arguments = data.get('arguments', {})
        logger.info(f"Tool: {tool_name}")
        logger.info(f"Arguments keys: {list(arguments.keys())}")

        if not tool_name:
            return web.json_response(
                {'error': 'Missing tool name'},
                status=400
            )

        logger.info(f"Dispatching to MCP handler...")
        result = await mcp_handler.handle_tool_call(tool_name, arguments)
        logger.info(f"MCP handler returned result")
        logger.info(f"Result: {result}")
        logger.info("=" * 80)
        return web.json_response(result)

    except Exception as e:
        logger.error(f"HTTP handler error: {e}", exc_info=True)
        return web.json_response({'error': str(e)}, status=500)


async def http_health(request: web.Request) -> web.Response:
    """Health check endpoint."""
    # Get available providers from config
    from utils.config_loader import config_loader
    providers_config = config_loader.get_config().get('providers', {})
    enabled_providers = [
        name for name, config in providers_config.items()
        if config.get('enabled', True)
    ]

    return web.json_response({
        'status': 'healthy',
        'service': 'llm_mcp',
        'version': '1.0.0',
        'sessions': session_manager.get_session_count(),
        'providers': enabled_providers,
        'default_provider': config_loader.get_default_provider()
    })


async def http_progress(request: web.Request) -> web.Response:
    """SSE endpoint for progress updates."""
    session_id = request.match_info.get('session_id')

    if not session_id:
        return web.json_response({'error': 'Missing session_id'}, status=400)

    # Setup SSE response
    response = web.StreamResponse()
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    await response.prepare(request)

    # Send progress updates
    try:
        while True:
            session = session_manager.get_session(session_id)
            if not session:
                await response.write(b'event: error\ndata: {"error": "Session not found"}\n\n')
                break

            progress_data = {
                'session_id': session_id,
                'status': session.status.value,
                'progress': session.progress,
                'stats': session.translation_stats
            }

            await response.write(
                f'event: progress\ndata: {json.dumps(progress_data)}\n\n'.encode()
            )

            if session.status in ['completed', 'failed']:
                await response.write(b'event: complete\ndata: {"status": "done"}\n\n')
                break

            await asyncio.sleep(1)  # Send updates every second

    except asyncio.CancelledError:
        pass
    finally:
        await response.write_eof()

    return response


async def http_redirect(request: web.Request) -> web.Response:
    """Redirect root to test page."""
    raise web.HTTPFound('/static/index.html')


async def run_http_server(port: int = 8023):
    """Run HTTP server for web testing."""
    http_app = web.Application()

    # Setup routes
    http_app.router.add_post('/mcp/tool', http_tool_handler)
    http_app.router.add_get('/health', http_health)
    http_app.router.add_get('/sse/progress/{session_id}', http_progress)
    http_app.router.add_get('/', http_redirect)

    # Serve static files (test page)
    static_dir = Path(__file__).parent / 'static'
    static_dir.mkdir(exist_ok=True)
    http_app.router.add_static('/static', static_dir, name='static')

    # Serve exported files (独立路由)
    exports_dir = Path(__file__).parent / 'exports'
    exports_dir.mkdir(exist_ok=True)
    http_app.router.add_static('/exports', exports_dir, name='exports')

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
        cors.add(route)

    # Start background cleanup task
    asyncio.create_task(session_cleanup_task())

    # Start server
    runner = web.AppRunner(http_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    logger.info(f"LLM MCP HTTP server running on port {port}")
    logger.info(f"Test page: http://localhost:{port}/")
    logger.info(f"Health check: http://localhost:{port}/health")

    # Keep server running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down HTTP server...")
    finally:
        await runner.cleanup()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='LLM MCP Server')
    parser.add_argument(
        '--http',
        action='store_true',
        help='Run in HTTP mode instead of stdio mode'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8023,
        help='HTTP port (default: 8023)'
    )

    args = parser.parse_args()

    if args.http:
        await run_http_server(args.port)
    else:
        await run_stdio_server()


if __name__ == '__main__':
    try:
        import json  # Import for SSE
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)