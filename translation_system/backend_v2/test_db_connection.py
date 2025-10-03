#!/usr/bin/env python3
"""Test database connection with the configured credentials."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database.mysql_connector import MySQLConnector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_connection():
    """Test database connection."""
    connector = MySQLConnector()

    try:
        # Initialize connection
        logger.info("Initializing database connection...")
        await connector.initialize()
        logger.info("✅ Database connection pool initialized successfully")

        # Test query
        async with connector.get_connection() as cursor:
            # Check MySQL version
            await cursor.execute("SELECT VERSION()")
            version = await cursor.fetchone()
            logger.info(f"✅ MySQL version: {version[0]}")

            # Check current database
            await cursor.execute("SELECT DATABASE()")
            db = await cursor.fetchone()
            logger.info(f"✅ Current database: {db[0]}")

            # Check tables
            await cursor.execute("SHOW TABLES")
            tables = await cursor.fetchall()

            if tables:
                logger.info(f"✅ Found {len(tables)} existing tables:")
                for table in tables:
                    await cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = await cursor.fetchone()
                    logger.info(f"   - {table[0]}: {count[0]} rows")
            else:
                logger.info("⚠️  No tables found in database")

            # Test write permission
            try:
                await cursor.execute("""
                    CREATE TEMPORARY TABLE test_write (
                        id INT PRIMARY KEY,
                        test_value VARCHAR(100)
                    )
                """)
                await cursor.execute("DROP TEMPORARY TABLE test_write")
                logger.info("✅ Write permission verified")
            except Exception as e:
                logger.warning(f"⚠️  Write permission test failed: {e}")

        # Close connection
        await connector.close()
        logger.info("✅ Database connection closed successfully")

        logger.info("\n" + "="*50)
        logger.info("Database connection test completed successfully!")
        logger.info("="*50)

    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        logger.error("\nPlease check:")
        logger.error("1. Database credentials in .env file")
        logger.error("2. Database server is accessible")
        logger.error("3. User has proper permissions")
        sys.exit(1)


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'

    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"Loaded configuration from {env_file}")
    else:
        logger.warning(f"⚠️  .env file not found at {env_file}")
        logger.info("Using default configuration or environment variables")

    # Show configuration (without password)
    import os
    logger.info("\n" + "="*50)
    logger.info("Database Configuration:")
    logger.info(f"  Host: {os.getenv('MYSQL_HOST')}")
    logger.info(f"  Port: {os.getenv('MYSQL_PORT')}")
    logger.info(f"  User: {os.getenv('MYSQL_USER')}")
    logger.info(f"  Database: {os.getenv('MYSQL_DATABASE')}")
    logger.info(f"  Password: {'*' * 10} (hidden)")
    logger.info("="*50 + "\n")

    # Run test
    asyncio.run(test_connection())