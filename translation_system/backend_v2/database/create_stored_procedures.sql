-- 创建存储过程的SQL脚本
-- 如果需要在数据库中创建存储过程，可以运行此脚本
-- 注意：当前代码已经使用Python实现了相同功能，不再依赖存储过程

DELIMITER //

-- 更新会话统计信息
DROP PROCEDURE IF EXISTS UpdateSessionStatistics//
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

-- 清理旧会话
DROP PROCEDURE IF EXISTS CleanupOldSessions//
CREATE PROCEDURE CleanupOldSessions(IN p_days_old INT)
BEGIN
    DELETE FROM translation_sessions
    WHERE created_at < DATE_SUB(NOW(), INTERVAL p_days_old DAY)
    AND status IN ('completed', 'failed', 'cancelled');
END//

-- 获取会话进度摘要
DROP PROCEDURE IF EXISTS GetSessionProgress//
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
        ROUND((s.completed_tasks / NULLIF(s.total_tasks, 0)) * 100, 2) AS completion_rate,
        s.created_at,
        s.updated_at,
        COUNT(DISTINCT t.batch_id) AS total_batches,
        AVG(CASE WHEN t.status = 'completed' THEN t.confidence END) AS avg_confidence
    FROM translation_sessions s
    LEFT JOIN translation_tasks t ON s.session_id = t.session_id
    WHERE s.session_id = p_session_id
    GROUP BY s.session_id;
END//

DELIMITER ;

-- 使用方法：
-- mysql -u username -p database_name < create_stored_procedures.sql