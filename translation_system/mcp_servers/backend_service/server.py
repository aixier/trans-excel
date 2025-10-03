#!/usr/bin/env python3
"""Backend Service - Authentication and Infrastructure (Port 9000)."""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Backend Service",
    description="Authentication and Infrastructure Service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load token configuration
TOKEN_CONFIG_PATH = Path(__file__).parent / "tokens.json"
token_config = {}

def load_token_config():
    """Load token configuration from JSON file."""
    global token_config
    try:
        with open(TOKEN_CONFIG_PATH, 'r', encoding='utf-8') as f:
            token_config = json.load(f)
        logger.info(f"Loaded token configuration from {TOKEN_CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Failed to load token config: {e}")
        token_config = {
            "secret_key": "dev-secret-key-change-in-production",
            "tokens": {}
        }

load_token_config()


# ============================================================================
# Models
# ============================================================================

class TokenValidateRequest(BaseModel):
    """Token validation request."""
    token: str


class TokenValidateResponse(BaseModel):
    """Token validation response."""
    valid: bool
    payload: dict = None
    error: str = None


class TokenGenerateRequest(BaseModel):
    """Token generation request."""
    token_id: str


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "backend_service",
        "port": 9000,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/auth/validate", response_model=TokenValidateResponse)
async def validate_token(request: TokenValidateRequest):
    """
    Validate token (supports both fixed tokens and JWT tokens).

    This is the unified token validation service used by all MCP servers.
    """
    try:
        token = request.token

        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]

        # First, check if it's a fixed token
        fixed_tokens = token_config.get('fixed_tokens', {})
        if token in fixed_tokens:
            payload = fixed_tokens[token].copy()
            logger.info(f"Fixed token validated successfully for user: {payload.get('user_id', 'unknown')}")
            return TokenValidateResponse(
                valid=True,
                payload=payload
            )

        # If not a fixed token, try JWT validation
        try:
            secret_key = token_config.get('secret_key', 'dev-secret-key-change-in-production')
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=["HS256"]
            )

            # Check expiration
            if 'exp' in payload:
                exp_timestamp = payload['exp']
                if datetime.utcnow().timestamp() > exp_timestamp:
                    return TokenValidateResponse(
                        valid=False,
                        error="Token has expired"
                    )

            logger.info(f"JWT token validated successfully for user: {payload.get('user_id', 'unknown')}")

            return TokenValidateResponse(
                valid=True,
                payload=payload
            )

        except jwt.ExpiredSignatureError:
            return TokenValidateResponse(
                valid=False,
                error="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            return TokenValidateResponse(
                valid=False,
                error=f"Invalid token: {str(e)}"
            )

    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return TokenValidateResponse(
            valid=False,
            error=f"Validation failed: {str(e)}"
        )


@app.post("/auth/generate")
async def generate_token(request: TokenGenerateRequest):
    """
    Generate JWT token from token configuration.

    Args:
        token_id: Token ID from tokens.json

    Returns:
        JWT token string
    """
    try:
        token_id = request.token_id

        # Check if token_id exists in config
        if token_id not in token_config.get('tokens', {}):
            raise HTTPException(status_code=404, detail=f"Token ID '{token_id}' not found in configuration")

        # Get token configuration
        token_data = token_config['tokens'][token_id]
        secret_key = token_config.get('secret_key', 'dev-secret-key-change-in-production')

        # Calculate expiration time
        expires_days = token_data.get('expires_days', 7)
        exp_time = datetime.utcnow() + timedelta(days=expires_days)

        # Create JWT payload
        payload = {
            'user_id': token_data['user_id'],
            'tenant_id': token_data['tenant_id'],
            'username': token_data['username'],
            'permissions': token_data['permissions'],
            'resources': token_data['resources'],
            'quota': token_data['quota'],
            'exp': exp_time.timestamp()
        }

        # Generate JWT token
        token = jwt.encode(payload, secret_key, algorithm='HS256')

        logger.info(f"Generated token for {token_id} (user: {token_data['user_id']})")

        return {
            'token': token,
            'bearer_token': f'Bearer {token}',
            'expires_at': exp_time.isoformat(),
            'user_id': token_data['user_id'],
            'tenant_id': token_data['tenant_id']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/token_ids")
async def list_token_ids():
    """List available token IDs from configuration."""
    return {
        'token_ids': list(token_config.get('tokens', {}).keys())
    }


@app.post("/auth/reload_config")
async def reload_config():
    """Reload token configuration from file."""
    try:
        load_token_config()
        return {
            'success': True,
            'message': 'Token configuration reloaded',
            'token_count': len(token_config.get('tokens', {}))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    logger.info("Starting Backend Service on port 9000...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    )
