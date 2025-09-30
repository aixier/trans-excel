#!/usr/bin/env python3
"""
初始化数据库表脚本
检查并创建系统所需的所有数据库表
"""

import asyncio
import aiomysql
from pathlib import Path
import sys

# 数据库配置
DB_CONFIG = {
    'host': 'rm-bp13t8tx0697ewx4wpo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'chenyang',
    'password': 'mRA9ycdvj8NW71qG5Dnajq',
    'db': 'ai_terminal',
    'charset': 'utf8mb4'
}


async def check_and_create_tables():
    """检查并创建所有必需的表"""

    print("=" * 60)
    print("开始初始化数据库表...")
    print("=" * 60)

    try:
        # 连接数据库
        conn = await aiomysql.connect(**DB_CONFIG)
        cursor = await conn.cursor()

        # 1. 检查现有表
        print("\n1. 检查现有表...")
        await cursor.execute("SHOW TABLES")
        existing_tables = [row[0] for row in await cursor.fetchall()]
        print(f"   现有表: {existing_tables if existing_tables else '无'}")

        # 2. 读取schema.sql
        schema_file = Path(__file__).parent / "schema.sql"
        print(f"\n2. 读取schema文件: {schema_file}")

        if not schema_file.exists():
            print(f"   ❌ Schema文件不存在: {schema_file}")
            return False

        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # 3. 拆分SQL语句（按分号分割，但要处理存储过程）
        print("\n3. 执行SQL语句...")

        # 移除注释
        lines = []
        for line in schema_sql.split('\n'):
            line = line.strip()
            if line and not line.startswith('--'):
                lines.append(line)

        sql_content = '\n'.join(lines)

        # 分割语句（处理DELIMITER）
        in_procedure = False
        statements = []
        current_statement = []

        for line in sql_content.split('\n'):
            if 'DELIMITER //' in line:
                in_procedure = True
                continue
            elif 'DELIMITER ;' in line:
                in_procedure = False
                if current_statement:
                    statements.append('\n'.join(current_statement))
                    current_statement = []
                continue

            current_statement.append(line)

            if not in_procedure and line.strip().endswith(';'):
                statements.append('\n'.join(current_statement))
                current_statement = []

        if current_statement:
            statements.append('\n'.join(current_statement))

        # 执行每个语句
        created_count = 0
        error_count = 0

        for i, statement in enumerate(statements):
            statement = statement.strip()
            if not statement or statement == 'USE ai_terminal;':
                continue

            try:
                # 检查是否是CREATE TABLE语句
                if 'CREATE TABLE' in statement.upper():
                    # 提取表名
                    import re
                    match = re.search(r'CREATE TABLE.*?`?(\w+)`?', statement, re.IGNORECASE)
                    if match:
                        table_name = match.group(1)
                        if table_name in existing_tables:
                            print(f"   ⏭️  表已存在: {table_name}")
                            continue

                await cursor.execute(statement)
                await conn.commit()

                if 'CREATE TABLE' in statement.upper():
                    created_count += 1
                    match = re.search(r'CREATE TABLE.*?`?(\w+)`?', statement, re.IGNORECASE)
                    if match:
                        print(f"   ✅ 创建表: {match.group(1)}")
                elif 'CREATE PROCEDURE' in statement.upper():
                    match = re.search(r'CREATE PROCEDURE\s+(\w+)', statement, re.IGNORECASE)
                    if match:
                        print(f"   ✅ 创建存储过程: {match.group(1)}")
                elif 'CREATE VIEW' in statement.upper():
                    match = re.search(r'CREATE VIEW\s+(\w+)', statement, re.IGNORECASE)
                    if match:
                        print(f"   ✅ 创建视图: {match.group(1)}")
                elif 'CREATE INDEX' in statement.upper():
                    print(f"   ✅ 创建索引")

            except aiomysql.Error as e:
                # 忽略"已存在"错误
                if 'already exists' in str(e) or 'Duplicate' in str(e):
                    print(f"   ⏭️  对象已存在，跳过")
                else:
                    print(f"   ❌ 执行失败: {e}")
                    error_count += 1

        # 4. 验证表创建
        print("\n4. 验证表结构...")
        await cursor.execute("SHOW TABLES")
        final_tables = [row[0] for row in await cursor.fetchall()]

        required_tables = [
            'translation_sessions',
            'translation_tasks',
            'execution_logs',
            'checkpoints',
            'performance_metrics',
            'cost_tracking'
        ]

        print(f"   当前表列表: {final_tables}")

        missing_tables = [t for t in required_tables if t not in final_tables]
        if missing_tables:
            print(f"\n   ⚠️  缺失的表: {missing_tables}")
        else:
            print(f"\n   ✅ 所有必需的表都已创建")

        # 5. 检查表结构
        print("\n5. 检查关键表结构...")
        for table in ['translation_sessions', 'translation_tasks']:
            if table in final_tables:
                await cursor.execute(f"DESCRIBE {table}")
                columns = await cursor.fetchall()
                print(f"\n   {table} 表字段:")
                for col in columns[:5]:  # 只显示前5个字段
                    print(f"     - {col[0]}: {col[1]}")
                if len(columns) > 5:
                    print(f"     ... 共 {len(columns)} 个字段")

        # 关闭连接
        await cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print(f"✅ 数据库初始化完成！")
        print(f"   创建对象数: {created_count}")
        print(f"   错误数: {error_count}")
        print("=" * 60)

        return error_count == 0

    except Exception as e:
        print(f"\n❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_connection():
    """测试数据库连接"""
    print("测试数据库连接...")
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        cursor = await conn.cursor()
        await cursor.execute("SELECT VERSION()")
        version = await cursor.fetchone()
        print(f"✅ 数据库连接成功！MySQL版本: {version[0]}")
        await cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


async def main():
    """主函数"""
    # 测试连接
    if not await test_connection():
        print("\n请检查数据库配置和网络连接")
        sys.exit(1)

    print()

    # 创建表
    success = await check_and_create_tables()

    if success:
        print("\n✅ 可以启动后端服务了: python3 main.py")
    else:
        print("\n⚠️  部分表创建失败，请检查错误日志")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())