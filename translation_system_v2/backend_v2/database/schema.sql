-- Translation System Database Schema
-- MySQL database schema for translation task persistence

-- Using existing ai_terminal database
-- CREATE DATABASE IF NOT EXISTS ai_terminal;
USE ai_terminal;

-- Translation sessions table
CREATE TABLE IF NOT EXISTS translation_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    status ENUM('created', 'analyzing', 'splitting', 'executing', 'completed', 'failed', 'cancelled') DEFAULT 'created',
    total_tasks INT DEFAULT 0,
    completed_tasks INT DEFAULT 0,
    failed_tasks INT DEFAULT 0,
    processing_tasks INT DEFAULT 0,
    game_info JSON,
    llm_provider VARCHAR(50),
    metadata JSON,
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Translation tasks table
CREATE TABLE IF NOT EXISTS translation_tasks (
    task_id VARCHAR(20) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    batch_id VARCHAR(20),
    group_id VARCHAR(20),
    sheet_name VARCHAR(100),
    row_index INT,
    col_index INT,
    source_text TEXT,
    source_lang VARCHAR(10),
    target_lang VARCHAR(10),
    source_context TEXT,
    result TEXT,
    status ENUM('pending', 'processing', 'completed', 'failed', 'skipped') DEFAULT 'pending',
    confidence FLOAT,
    token_count INT DEFAULT 0,
    cost DECIMAL(10, 6) DEFAULT 0,
    llm_model VARCHAR(50),
    error_message TEXT,
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    duration_ms INT,
    is_final BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (session_id) REFERENCES translation_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_batch (session_id, batch_id),
    INDEX idx_session_status (session_id, status),
    INDEX idx_status (status),
    INDEX idx_batch_id (batch_id),
    INDEX idx_group_id (group_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Execution logs table
CREATE TABLE IF NOT EXISTS execution_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(10),
    message TEXT,
    details JSON,
    component VARCHAR(50),
    INDEX idx_session_time (session_id, timestamp),
    INDEX idx_level (level),
    INDEX idx_component (component),
    FOREIGN KEY (session_id) REFERENCES translation_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Checkpoints table for resuming interrupted sessions
CREATE TABLE IF NOT EXISTS checkpoints (
    checkpoint_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    checkpoint_type ENUM('auto', 'manual', 'error') DEFAULT 'auto',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    task_df_path VARCHAR(500),
    excel_df_path VARCHAR(500),
    progress_data JSON,
    metadata JSON,
    is_latest BOOLEAN DEFAULT TRUE,
    INDEX idx_session_latest (session_id, is_latest),
    FOREIGN KEY (session_id) REFERENCES translation_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    metric_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metric_type VARCHAR(50),
    metric_value DECIMAL(15, 4),
    unit VARCHAR(20),
    details JSON,
    INDEX idx_session_metric (session_id, metric_type, timestamp),
    INDEX idx_timestamp (timestamp),
    FOREIGN KEY (session_id) REFERENCES translation_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Cost tracking table
CREATE TABLE IF NOT EXISTS cost_tracking (
    cost_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    batch_id VARCHAR(20),
    provider VARCHAR(50),
    model VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    cost_usd DECIMAL(10, 6),
    cost_cny DECIMAL(10, 6),
    exchange_rate DECIMAL(10, 4),
    INDEX idx_session_cost (session_id, timestamp),
    INDEX idx_provider_model (provider, model),
    FOREIGN KEY (session_id) REFERENCES translation_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create indexes for performance
CREATE INDEX idx_tasks_processing ON translation_tasks(session_id, status, batch_id) WHERE status = 'processing';
CREATE INDEX idx_tasks_pending ON translation_tasks(session_id, status, group_id) WHERE status = 'pending';

-- Stored procedures for common operations

DELIMITER //

-- Update session statistics
CREATE PROCEDURE UpdateSessionStatistics(IN p_session_id VARCHAR(36))
BEGIN
    UPDATE translation_sessions s
    SET 
        s.total_tasks = (SELECT COUNT(*) FROM translation_tasks WHERE session_id = p_session_id),
        s.completed_tasks = (SELECT COUNT(*) FROM translation_tasks WHERE session_id = p_session_id AND status = 'completed'),
        s.failed_tasks = (SELECT COUNT(*) FROM translation_tasks WHERE session_id = p_session_id AND status = 'failed'),
        s.processing_tasks = (SELECT COUNT(*) FROM translation_tasks WHERE session_id = p_session_id AND status = 'processing'),
        s.updated_at = CURRENT_TIMESTAMP
    WHERE s.session_id = p_session_id;
END//

-- Clean up old sessions
CREATE PROCEDURE CleanupOldSessions(IN p_days_old INT)
BEGIN
    DELETE FROM translation_sessions 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL p_days_old DAY)
    AND status IN ('completed', 'failed', 'cancelled');
END//

-- Get session progress summary
CREATE PROCEDURE GetSessionProgress(IN p_session_id VARCHAR(36))
BEGIN
    SELECT 
        s.session_id,
        s.filename,
        s.status AS session_status,
        s.total_tasks,
        s.completed_tasks,
        s.failed_tasks,
        s.processing_tasks,
        (s.completed_tasks * 100.0 / NULLIF(s.total_tasks, 0)) AS completion_rate,
        s.created_at,
        s.updated_at,
        COUNT(DISTINCT t.batch_id) AS total_batches,
        COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.batch_id END) AS completed_batches
    FROM translation_sessions s
    LEFT JOIN translation_tasks t ON s.session_id = t.session_id
    WHERE s.session_id = p_session_id
    GROUP BY s.session_id;
END//

DELIMITER ;

-- Views for reporting

-- Session summary view
CREATE VIEW session_summary AS
SELECT 
    s.session_id,
    s.filename,
    s.status,
    s.total_tasks,
    s.completed_tasks,
    s.failed_tasks,
    (s.completed_tasks * 100.0 / NULLIF(s.total_tasks, 0)) AS completion_rate,
    s.llm_provider,
    s.created_at,
    s.updated_at,
    TIMESTAMPDIFF(SECOND, s.created_at, s.updated_at) AS duration_seconds
FROM translation_sessions s;

-- Cost summary view
CREATE VIEW cost_summary AS
SELECT 
    c.session_id,
    s.filename,
    c.provider,
    c.model,
    SUM(c.total_tokens) AS total_tokens,
    SUM(c.cost_usd) AS total_cost_usd,
    SUM(c.cost_cny) AS total_cost_cny,
    COUNT(*) AS api_calls,
    AVG(c.total_tokens) AS avg_tokens_per_call
FROM cost_tracking c
JOIN translation_sessions s ON c.session_id = s.session_id
GROUP BY c.session_id, c.provider, c.model;

-- Task performance view
CREATE VIEW task_performance AS
SELECT 
    t.session_id,
    t.batch_id,
    COUNT(*) AS task_count,
    AVG(t.duration_ms) AS avg_duration_ms,
    MIN(t.duration_ms) AS min_duration_ms,
    MAX(t.duration_ms) AS max_duration_ms,
    AVG(t.token_count) AS avg_tokens,
    SUM(t.cost) AS total_cost
FROM translation_tasks t
WHERE t.status = 'completed'
GROUP BY t.session_id, t.batch_id;