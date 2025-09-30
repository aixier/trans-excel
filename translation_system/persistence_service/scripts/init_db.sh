#!/bin/bash
# ============================================================================
# Persistence Service - Initialize Database Script
# ============================================================================

echo "Initializing database schema..."

# Change to project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Check if schema file exists
if [ ! -f "database/schema.sql" ]; then
    echo "ERROR: Schema file not found: database/schema.sql"
    exit 1
fi

# Prompt for database credentials
read -p "MySQL Host [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "MySQL Port [3306]: " DB_PORT
DB_PORT=${DB_PORT:-3306}

read -p "MySQL User [root]: " DB_USER
DB_USER=${DB_USER:-root}

read -sp "MySQL Password: " DB_PASSWORD
echo

# Execute schema
echo "Executing schema..."
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" < database/schema.sql

if [ $? -eq 0 ]; then
    echo "Database schema initialized successfully!"
else
    echo "ERROR: Failed to initialize database schema"
    exit 1
fi