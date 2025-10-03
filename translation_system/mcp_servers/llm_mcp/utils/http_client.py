"""
HTTP Client Utilities for LLM MCP Server
"""

import aiohttp
import asyncio
import logging
from pathlib import Path
from typing import Optional
import tempfile

logger = logging.getLogger(__name__)


async def download_file(url: str, timeout: int = 60) -> Path:
    """Download file from URL and save to temporary location."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()

                # Create temporary file
                suffix = Path(url).suffix or '.xlsx'
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                    tmp_path = Path(tmp_file.name)

                    # Download in chunks
                    chunk_size = 8192
                    async for chunk in response.content.iter_chunked(chunk_size):
                        tmp_file.write(chunk)

                logger.info(f"Downloaded file from {url} to {tmp_path}")
                return tmp_path

    except aiohttp.ClientError as e:
        logger.error(f"Failed to download file from {url}: {e}")
        raise Exception(f"Download failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error downloading file: {e}")
        raise