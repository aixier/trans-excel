# Project Structure

## Directory Organization

```
backend_spec/
├── .claude/                    # Claude Code configuration
│   ├── commands/              # Slash command definitions
│   ├── specs/                 # Feature specifications
│   │   └── {feature-name}/
│   │       ├── requirements.md
│   │       ├── design.md
│   │       └── tasks.md
│   ├── bugs/                  # Bug reports and fixes
│   ├── steering/             # Project guidance documents
│   └── templates/            # Document templates
│
├── api/                       # API layer (FastAPI routers)
│   ├── __init__.py
│   ├── analyze_api.py        # File analysis endpoints
│   ├── task_api.py           # Task management endpoints
│   ├── execute_api.py        # Execution control endpoints
│   ├── monitor_api.py        # Monitoring endpoints
│   └── websocket_api.py      # WebSocket connections
│
├── models/                    # Data models and schemas
│   ├── __init__.py
│   ├── schemas.py            # Pydantic models for API
│   ├── dataframes.py         # DataFrame definitions
│   ├── entities.py           # Database entities
│   └── enums.py              # Enum definitions
│
├── services/                  # Business logic layer
│   ├── __init__.py
│   ├── analyzer/             # Analysis services
│   ├── executor/             # Execution services
│   ├── translator/           # Translation services
│   └── monitor/              # Monitoring services
│
├── database/                  # Database layer
│   ├── __init__.py
│   ├── connection.py         # Database connection
│   ├── repositories/         # Repository pattern
│   └── models.py            # SQLAlchemy models
│
├── tests/                     # Test files
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
│
├── main.py                  # Application entry point
├── requirements.txt         # Dependencies
└── README.md               # Documentation
```

## Naming Conventions

- **Files**: snake_case.py
- **Classes**: PascalCase
- **Functions**: snake_case
- **Constants**: UPPER_CASE

## Import Order

1. Standard library imports
2. Third-party imports
3. Local application imports

## Development Workflow

Features are developed using spec-driven approach:
1. Create spec in `.claude/specs/{feature}/`
2. Implement following TDD
3. Test and validate
4. Document changes
