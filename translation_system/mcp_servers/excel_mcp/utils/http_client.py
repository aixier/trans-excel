"""HTTP client for downloading files from URLs."""

import requests
import logging
from typing import Optional, Dict, Any
from io import BytesIO

logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client for downloading files."""

    def __init__(self, timeout: int = 60):
        """
        Initialize HTTP client.

        Args:
            timeout: Request timeout in seconds (default: 60)
        """
        self.timeout = timeout
        self.session = requests.Session()

    def download_file(self, url: str, headers: Optional[Dict[str, str]] = None) -> BytesIO:
        """
        Download file from URL and return as BytesIO.

        Args:
            url: URL to download from
            headers: Optional HTTP headers

        Returns:
            BytesIO containing file data

        Raises:
            Exception: If download fails
        """
        try:
            logger.info(f"Downloading file from URL: {url}")

            response = self.session.get(
                url,
                headers=headers,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()

            # Read content into BytesIO
            file_data = BytesIO(response.content)
            file_data.seek(0)

            logger.info(f"Successfully downloaded file ({len(response.content)} bytes)")
            return file_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download file from {url}: {e}")
            raise Exception(f"Download failed: {str(e)}")

    def validate_url(self, url: str) -> Dict[str, Any]:
        """
        Validate URL accessibility without downloading.

        Args:
            url: URL to validate

        Returns:
            Dictionary with validation results
        """
        try:
            response = self.session.head(url, timeout=10, allow_redirects=True)
            return {
                'valid': response.status_code < 400,
                'status_code': response.status_code,
                'content_type': response.headers.get('Content-Type'),
                'content_length': response.headers.get('Content-Length')
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }

    def close(self):
        """Close the session."""
        self.session.close()


# Global HTTP client instance
http_client = HTTPClient()
