"""JWT token validator for excel_mcp (calls backend_service)."""

import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TokenValidator:
    """Token validator that calls unified backend_service API."""

    def __init__(self, backend_url: str = "http://localhost:9000"):
        """
        Initialize token validator.

        Args:
            backend_url: Backend service URL
        """
        self.backend_url = backend_url
        self.validate_endpoint = f"{backend_url}/auth/validate"

    def validate(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token by calling backend_service API.

        Args:
            token: JWT token string (with or without 'Bearer ' prefix)

        Returns:
            Token payload dictionary

        Raises:
            Exception: If token is invalid or expired
        """
        try:
            # Call backend_service validation API
            response = requests.post(
                self.validate_endpoint,
                json={"token": token},
                timeout=5
            )

            if response.status_code != 200:
                raise Exception(f"Backend service error: {response.status_code}")

            result = response.json()

            if not result.get('valid'):
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Token validation failed: {error_msg}")
                raise Exception(error_msg)

            payload = result.get('payload')
            if not payload:
                raise Exception("No payload returned from backend service")

            logger.info(f"Token validated successfully for user: {payload.get('user_id', 'unknown')}")
            return payload

        except requests.RequestException as e:
            logger.error(f"Failed to connect to backend_service: {e}")
            raise Exception(f"Token validation service unavailable: {str(e)}")
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            raise Exception(f"Token validation failed: {str(e)}")

    def check_permission(self, payload: Dict[str, Any], permission: str) -> bool:
        """
        Check if token has specific permission.

        Args:
            payload: Token payload
            permission: Permission to check (e.g., 'excel:analyze')

        Returns:
            True if permission granted, False otherwise
        """
        permissions = payload.get('permissions', {})
        return permissions.get(permission, False)

    def get_user_info(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract user information from token payload.

        Args:
            payload: Token payload

        Returns:
            User information dictionary
        """
        return {
            'user_id': payload.get('user_id'),
            'tenant_id': payload.get('tenant_id'),
            'username': payload.get('username'),
            'permissions': payload.get('permissions', {}),
            'resources': payload.get('resources', {})
        }


# Global token validator instance
token_validator = TokenValidator()
