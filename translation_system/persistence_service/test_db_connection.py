#!/usr/bin/env python3
"""
Test database connection
Quick script to verify MySQL connection before starting the service
"""
import asyncio
import aiomysql
from config.settings import settings

async def test_connection():
    """Test MySQL connection"""
    print("=" * 60)
    print("Testing MySQL Connection")
    print("=" * 60)
    print(f"Host: {settings.database.host}")
    print(f"Port: {settings.database.port}")
    print(f"User: {settings.database.user}")
    print(f"Database: {settings.database.database}")
    print("=" * 60)

    try:
        print("\nAttempting to connect...")

        # Try to create connection
        conn = await aiomysql.connect(
            host=settings.database.host,
            port=settings.database.port,
            user=settings.database.user,
            password=settings.database.password,
            db=settings.database.database,
            charset='utf8mb4'
        )

        print("✅ Connection successful!")

        # Test query
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT VERSION()")
            version = await cursor.fetchone()
            print(f"✅ MySQL Version: {version[0]}")

            await cursor.execute("SELECT DATABASE()")
            db = await cursor.fetchone()
            print(f"✅ Current Database: {db[0]}")

            # Check if tables exist
            await cursor.execute("SHOW TABLES")
            tables = await cursor.fetchall()
            print(f"✅ Tables in database: {len(tables)}")
            for table in tables:
                print(f"   - {table[0]}")

        conn.close()

        print("\n" + "=" * 60)
        print("✅ Database connection test PASSED")
        print("=" * 60)
        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ Database connection test FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        print("\nPlease check:")
        print("1. Database host is accessible")
        print("2. Database credentials are correct")
        print("3. Database 'ai_terminal' exists")
        print("4. Network/firewall allows connection")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)