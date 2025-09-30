-- ============================================================================
-- Persistence Service - Database Schema
-- Phase 1: Translation Data Persistence
-- ============================================================================

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS ai_terminal
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE ai_terminal;

-- ============================================================================
-- Table: translation_sessions
-- Description: Stores translation session metadata
-- ============================================================================

CREATE TABLE IF NOT EXISTS translation_sessions (
    -- Primary Key
    session_id VARCHAR(36) PRIMARY KEY COMMENT '会话ID (UUID)',

    -- File Information
    filename VARCHAR(255) NOT NULL COMMENT '文件名',
    file_path VARCHAR(512) NOT NULL COMMENT '文件路径',

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态: pending, processing, completed, failed',

    -- Game Information (JSON)
    game_info JSON COMMENT '游戏信息 (game_name, source_language, target_language)',

    -- LLM Configuration
    llm_provider VARCHAR(50) NOT NULL COMMENT 'LLM提供商: openai, qwen, etc.',

    -- Metadata (JSON)
    metadata JSON COMMENT '元数据 (其他自定义字段)',

    -- Task Statistics
    total_tasks INT DEFAULT 0 COMMENT '总任务数',
    completed_tasks INT DEFAULT 0 COMMENT '已完成任务数',
    failed_tasks INT DEFAULT 0 COMMENT '失败任务数',
    processing_tasks INT DEFAULT 0 COMMENT '处理中任务数',

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- Indexes
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at),
    INDEX idx_llm_provider (llm_provider)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='翻译会话表';


-- ============================================================================
-- Table: translation_tasks
-- Description: Stores individual translation task details
-- ============================================================================

CREATE TABLE IF NOT EXISTS translation_tasks (
    -- Primary Key
    task_id VARCHAR(64) PRIMARY KEY COMMENT '任务ID',

    -- Foreign Key
    session_id VARCHAR(36) NOT NULL COMMENT '会话ID',

    -- Task Identification
    batch_id VARCHAR(64) NOT NULL COMMENT '批次ID',
    sheet_name VARCHAR(255) NOT NULL COMMENT '工作表名称',
    row_index INT NOT NULL COMMENT '行索引',
    column_name VARCHAR(255) NOT NULL COMMENT '列名',

    -- Text Content
    source_text TEXT NOT NULL COMMENT '源文本',
    target_text TEXT COMMENT '翻译结果',
    context TEXT COMMENT '上下文信息',

    -- Status and Quality
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态: pending, processing, completed, failed',
    confidence DECIMAL(5,4) COMMENT '置信度 (0-1)',
    error_message TEXT COMMENT '错误信息',
    retry_count INT DEFAULT 0 COMMENT '重试次数',

    -- Timing
    start_time TIMESTAMP NULL COMMENT '开始时间',
    end_time TIMESTAMP NULL COMMENT '结束时间',
    duration_ms INT COMMENT '耗时 (毫秒)',

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- Foreign Key Constraint
    FOREIGN KEY (session_id) REFERENCES translation_sessions(session_id) ON DELETE CASCADE,

    -- Indexes
    INDEX idx_session_id (session_id),
    INDEX idx_batch_id (batch_id),
    INDEX idx_status (status),
    INDEX idx_session_status (session_id, status),
    INDEX idx_sheet_name (sheet_name),
    INDEX idx_created_at (created_at)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='翻译任务表';


-- ============================================================================
-- Create Views for Common Queries
-- ============================================================================

-- View: Session summary with task statistics
CREATE OR REPLACE VIEW v_session_summary AS
SELECT
    s.session_id,
    s.filename,
    s.status,
    s.llm_provider,
    s.total_tasks,
    s.completed_tasks,
    s.failed_tasks,
    s.processing_tasks,
    ROUND(s.completed_tasks * 100.0 / NULLIF(s.total_tasks, 0), 2) AS completion_percentage,
    s.created_at,
    s.updated_at,
    TIMESTAMPDIFF(SECOND, s.created_at, COALESCE(s.updated_at, NOW())) AS duration_seconds
FROM translation_sessions s;


-- View: Task statistics by session
CREATE OR REPLACE VIEW v_task_statistics AS
SELECT
    t.session_id,
    COUNT(*) AS total_tasks,
    SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) AS completed_count,
    SUM(CASE WHEN t.status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
    SUM(CASE WHEN t.status = 'processing' THEN 1 ELSE 0 END) AS processing_count,
    SUM(CASE WHEN t.status = 'pending' THEN 1 ELSE 0 END) AS pending_count,
    AVG(t.confidence) AS avg_confidence,
    AVG(t.duration_ms) AS avg_duration_ms,
    SUM(t.duration_ms) AS total_duration_ms
FROM translation_tasks t
GROUP BY t.session_id;


-- ============================================================================
-- Sample Queries (for reference)
-- ============================================================================

-- Query: Get incomplete sessions
-- SELECT * FROM translation_sessions WHERE status IN ('pending', 'processing') ORDER BY created_at DESC;

-- Query: Get session with task counts
-- SELECT s.*, v.* FROM translation_sessions s LEFT JOIN v_task_statistics v ON s.session_id = v.session_id;

-- Query: Get failed tasks for a session
-- SELECT * FROM translation_tasks WHERE session_id = ? AND status = 'failed';

-- Query: Calculate session progress
-- SELECT
--     session_id,
--     completed_tasks,
--     total_tasks,
--     ROUND(completed_tasks * 100.0 / total_tasks, 2) AS progress_percentage
-- FROM translation_sessions
-- WHERE total_tasks > 0;


-- ============================================================================
-- Performance Optimization Notes
-- ============================================================================

-- 1. Indexes are created on frequently queried columns:
--    - status (for filtering incomplete sessions/tasks)
--    - session_id (for joins and lookups)
--    - created_at/updated_at (for time-based queries and sorting)

-- 2. Foreign key with CASCADE DELETE ensures referential integrity
--    and automatic cleanup of tasks when session is deleted

-- 3. JSON columns (game_info, metadata) provide flexibility
--    without requiring schema changes

-- 4. Composite index (session_id, status) optimizes queries like:
--    "Get all pending tasks for a session"

-- 5. Views provide convenient access to computed statistics
--    without duplicating SQL logic


-- ============================================================================
-- Data Cleanup (Optional - for maintenance)
-- ============================================================================

-- Cleanup old completed sessions (older than 90 days)
-- DELETE FROM translation_sessions
-- WHERE status = 'completed' AND created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);

-- Cleanup old failed sessions (older than 30 days)
-- DELETE FROM translation_sessions
-- WHERE status = 'failed' AND created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);


-- ============================================================================
-- End of Schema
-- ============================================================================