#!/usr/bin/env python3
"""Generate a test JWT token for excel_mcp development."""

import jwt
from datetime import datetime, timedelta
import json

def generate_test_token():
    """Generate a test JWT token."""
    payload = {
        "user_id": "dev_001",
        "tenant_id": "tenant_dev",
        "username": "dev@test.com",
        "permissions": {
            "storage:read": True,
            "storage:write": True,
            "excel:analyze": True,
            "llm:translate": True
        },
        "resources": {
            "oss": {
                "provider": "local",
                "bucket": "test-bucket",
                "prefix": "tenants/dev/users/001/"
            },
            "mysql": {
                "schema": "tenant_dev"
            },
            "redis": {
                "prefix": "dev:001:"
            }
        },
        "quota": {
            "llm_credits": 100000,
            "storage_mb": 5000
        },
        "exp": (datetime.utcnow() + timedelta(days=7)).timestamp()
    }

    secret_key = "dev-secret-key-change-in-production"
    token = jwt.encode(payload, secret_key, algorithm="HS256")

    return token


if __name__ == "__main__":
    token = generate_test_token()
    print("\n" + "=" * 80)
    print("Excel MCP Server - Test Token Generator")
    print("=" * 80)
    print(f"\nGenerated Token (valid for 7 days):\n")
    print(f"Bearer {token}")
    print(f"\n{'=' * 80}\n")
    print("Use this token for testing excel_mcp tools.")
    print("\nExample usage:")
    print("""
{
  "tool": "excel_analyze",
  "arguments": {
    "token": "Bearer YOUR_TOKEN_HERE",
    "file_url": "https://example.com/file.xlsx"
  }
}
    """)
    print("=" * 80 + "\n")

    # Also save to file for convenience
    with open('/tmp/excel_mcp_test_token.txt', 'w') as f:
        f.write(f"Bearer {token}\n")
    print(f"Token also saved to: /tmp/excel_mcp_test_token.txt\n")
