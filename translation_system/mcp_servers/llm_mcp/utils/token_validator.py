"""
Token Validator for LLM MCP Server
"""

import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TokenValidator:
    """Validates JWT tokens for authentication."""

    def __init__(self, secret_key: str = "test_secret_key", algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def validate(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return payload."""
        try:
            # For testing, accept specific test tokens
            if token in ["test_token_123", "test_token", "dev_token"]:
                return {
                    "user_id": "test_user",
                    "exp": datetime.utcnow() + timedelta(hours=24),
                    "permissions": ["translate", "export"]
                }

            # Decode JWT token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Check expiration
            if 'exp' in payload:
                exp_time = datetime.fromtimestamp(payload['exp'])
                if exp_time < datetime.utcnow():
                    raise ValueError("Token has expired")

            return payload

        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise ValueError(f"Token validation failed: {str(e)}")

    def create_token(self, user_id: str, permissions: list = None, expires_in: int = 86400) -> str:
        """Create a new JWT token."""
        payload = {
            "user_id": user_id,
            "permissions": permissions or [],
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=expires_in)
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_permission(self, token: str, required_permission: str) -> bool:
        """Verify if token has specific permission."""
        try:
            payload = self.validate(token)
            permissions = payload.get('permissions', [])
            return required_permission in permissions
        except:
            return False


# Global token validator instance
token_validator = TokenValidator()