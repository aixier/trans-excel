#!/usr/bin/env python3
"""Initialize database tables for translation system."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.mysql_connector import MySQLConnector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables(connector: MySQLConnector):
    """Create all required database tables."""

    # Read schema file
    schema_file = Path(__file__).parent / 'schema.sql'
    if not schema_file.exists():
        logger.error(f"Schema file not found: {schema_file}")
        return False

    with open(schema_file, 'r') as f:
        schema_sql = f.read()

    # Split by semicolon and execute each statement
    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]

    async with connector.get_connection() as cursor:
        for statement in statements:
            if statement:
                try:
                    await cursor.execute(statement)
                    logger.info(f"Executed: {statement[:50]}...")
                except Exception as e:
                    logger.error(f"Failed to execute statement: {e}")
                    logger.error(f"Statement: {statement[:100]}...")

    return True


async def verify_connection():
    """Verify database connection and create tables."""
    connector = MySQLConnector()

    try:
        await connector.initialize()
        logger.info("Database connection successful")

        # Test query
        async with connector.get_connection() as cursor:
            await cursor.execute("SELECT VERSION()")
            version = await cursor.fetchone()
            logger.info(f"MySQL version: {version[0]}")

            # Show current database
            await cursor.execute("SELECT DATABASE()")
            db = await cursor.fetchone()
            logger.info(f"Current database: {db[0]}")

            # List existing tables
            await cursor.execute("SHOW TABLES")
            tables = await cursor.fetchall()
            if tables:
                logger.info("Existing tables:")
                for table in tables:
                    logger.info(f"  - {table[0]}")
            else:
                logger.info("No existing tables found")

        # Create tables
        logger.info("Creating/updating database tables...")
        success = await create_tables(connector)

        if success:
            logger.info("Database initialization completed successfully")
        else:
            logger.error("Database initialization failed")

        await connector.close()

    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.error("Please check your database configuration in .env file")
        sys.exit(1)


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"Loaded configuration from {env_file}")

    # Show configuration (without password)
    logger.info(f"Database configuration:")
    logger.info(f"  Host: {os.getenv('MYSQL_HOST')}")
    logger.info(f"  Port: {os.getenv('MYSQL_PORT')}")
    logger.info(f"  User: {os.getenv('MYSQL_USER')}")
    logger.info(f"  Database: {os.getenv('MYSQL_DATABASE')}")

    # Run verification
    asyncio.run(verify_connection())