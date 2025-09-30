# Persistence Service - Quick Start Guide

## Prerequisites

- Python 3.10+
- MySQL 8.0+
- 2GB+ Memory

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database

Copy the example configuration:

```bash
cp config/config.yaml.example config/config.yaml
```

Edit `config/config.yaml` with your database settings:

```yaml
database:
  host: "localhost"
  port: 3306
  user: "root"
  password: "your_password"
  database: "ai_terminal"
  pool_size: 10
```

### 3. Initialize Database Schema

Run the initialization script:

```bash
bash scripts/init_db.sh
```

Or manually execute:

```bash
mysql -u root -p ai_terminal < database/schema.sql
```

### 4. Start the Service

Using the start script:

```bash
bash scripts/start.sh
```

Or manually:

```bash
python main.py
```

The service will start on `http://localhost:8001`

## Verify Installation

### Health Check

```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "healthy",
  "buffer": {
    "sessions_count": 0,
    "tasks_count": 0,
    ...
  }
}
```

### API Documentation

Open your browser and visit:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Basic Usage

### 1. Persist a Session

```bash
curl -X POST "http://localhost:8001/api/v1/translation/sessions/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "sessions": [{
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "test.xlsx",
      "file_path": "/uploads/test.xlsx",
      "status": "processing",
      "llm_provider": "openai",
      "total_tasks": 100
    }]
  }'
```

### 2. Query Sessions

```bash
curl "http://localhost:8001/api/v1/translation/sessions?page=1&page_size=20"
```

### 3. Force Flush Buffer

```bash
curl -X POST "http://localhost:8001/api/v1/translation/flush"
```

### 4. Get Statistics

```bash
curl "http://localhost:8001/api/v1/translation/stats"
```

## Configuration

### Buffer Settings

Adjust buffer settings in `config/config.yaml`:

```yaml
buffer:
  max_buffer_size: 1000  # Auto-flush after 1000 items
  flush_interval: 30     # Auto-flush every 30 seconds
```

### Logging

Configure logging in `config/config.yaml`:

```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "logs/persistence_service.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5
```

## Troubleshooting

### Database Connection Error

If you see database connection errors:

1. Verify MySQL is running:
   ```bash
   systemctl status mysql
   ```

2. Check database credentials in `config/config.yaml`

3. Test connection manually:
   ```bash
   mysql -h localhost -u root -p
   ```

### Port Already in Use

If port 8001 is already in use, change it in `config/config.yaml`:

```yaml
service:
  port: 8002  # Change to another port
```

### Logs Not Created

Ensure the logs directory exists:

```bash
mkdir -p logs
```

## Stopping the Service

```bash
bash scripts/stop.sh
```

Or press `Ctrl+C` if running in foreground.

## Next Steps

- Read the [API Documentation](docs/TRANSLATION_API.md) for detailed API usage
- Read the [Architecture Document](docs/ARCHITECTURE_V2.md) for system design
- Read the [Task List](docs/TASKLIST.md) for development progress

## Support

For issues and questions, please refer to:
- [Requirements Document](docs/REQUIREMENTS_V2.md)
- [Project Roadmap](docs/ROADMAP.md)
- README.md