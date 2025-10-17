/**
 * 自动工作流编排器
 *
 * 负责协调整个翻译流程，自动处理标准翻译和CAPS转换
 *
 * @author 工程师B
 * @date 2025-10-17
 */

class AutoWorkflowOrchestrator {
  constructor() {
    this.currentWorkflow = null; // 'standard' or 'with_caps'
    this.sessionIds = []; // Session链
    this.analysis = null;
    this.glossaryId = null;
    this.progressCallback = null;
    this.completionCallback = null;
  }

  /**
   * 设置进度回调
   */
  onProgress(callback) {
    this.progressCallback = callback;
  }

  /**
   * 设置完成回调
   */
  onCompletion(callback) {
    this.completionCallback = callback;
  }

  /**
   * 更新进度
   */
  updateProgress(message, percent, details = {}) {
    console.log(`[Workflow] ${percent}%: ${message}`);
    if (this.progressCallback) {
      this.progressCallback({ message, percent, ...details });
    }
  }

  /**
   * 执行完整工作流
   */
  async execute(file, config) {
    const { analysis, glossaryId, glossaryFile } = config;

    this.analysis = analysis;
    this.glossaryId = glossaryId;

    try {
      // 如果需要上传术语库
      if (glossaryFile) {
        this.updateProgress('上传术语库中...', 2);
        await this.uploadGlossary(glossaryFile);
      }

      // 判断工作流类型
      const hasCaps = this.analysis.file_info.sheets.some(
        sheet => sheet.toLowerCase().includes('caps')
      );

      if (hasCaps) {
        this.currentWorkflow = 'with_caps';
        await this.executeWithCapsWorkflow(file);
      } else {
        this.currentWorkflow = 'standard';
        await this.executeStandardWorkflow(file);
      }

      // 完成回调
      if (this.completionCallback) {
        const finalSessionId = this.sessionIds[this.sessionIds.length - 1];
        this.completionCallback({ sessionId: finalSessionId });
      }

    } catch (error) {
      console.error('[Workflow] Execution failed:', error);
      this.updateProgress('执行失败: ' + error.message, 0, { error: true });
      throw error;
    }
  }

  /**
   * 标准工作流（无CAPS）
   */
  async executeStandardWorkflow(file) {
    const suggested = this.analysis.language_detection.suggested_config;

    // 步骤1: 上传文件并拆分任务
    this.updateProgress('上传文件并拆分任务...', 5);

    const splitResponse = await window.api.uploadFile(file, {
      source_lang: suggested.source_lang,
      target_langs: suggested.target_langs,
      rule_set: 'translation',
      extract_context: true
    });

    this.sessionIds.push(splitResponse.session_id);

    // 等待拆分完成
    this.updateProgress('拆分任务中...', 10);
    await this.waitForSplit(splitResponse.session_id);

    // 步骤2: 执行翻译
    this.updateProgress('AI翻译执行中...', 20);
    await this.executeTranslation(splitResponse.session_id, 20, 90);

    // 步骤3: 完成
    this.updateProgress('生成下载文件...', 95);
    await this.delay(1000);
    this.updateProgress('翻译完成！', 100);
  }

  /**
   * 带CAPS的工作流
   */
  async executeWithCapsWorkflow(file) {
    const suggested = this.analysis.language_detection.suggested_config;

    // === 阶段1: 标准翻译 ===
    this.updateProgress('阶段1/2: 上传文件并拆分翻译任务...', 5);

    const splitResponse = await window.api.uploadFile(file, {
      source_lang: suggested.source_lang,
      target_langs: suggested.target_langs,
      rule_set: 'translation', // 排除CAPS
      extract_context: true
    });

    this.sessionIds.push(splitResponse.session_id);

    // 等待拆分完成
    this.updateProgress('阶段1/2: 拆分任务中...', 10);
    await this.waitForSplit(splitResponse.session_id);

    // 执行翻译（占用10-60%的进度）
    this.updateProgress('阶段1/2: AI翻译执行中...', 15);
    await this.executeTranslation(splitResponse.session_id, 15, 60);

    // === 阶段2: CAPS转换 ===
    this.updateProgress('阶段2/2: 拆分CAPS任务...', 65);

    // 从父Session继承
    const capsResponse = await window.api.splitFromParent(splitResponse.session_id, {
      rule_set: 'caps_only'
    });

    this.sessionIds.push(capsResponse.session_id);

    // 等待拆分完成
    await this.waitForSplit(capsResponse.session_id);

    // 执行CAPS转换（占用70-95%的进度）
    this.updateProgress('阶段2/2: CAPS转换执行中...', 70);
    await this.executeTransformation(capsResponse.session_id, 70, 95);

    // 完成
    this.updateProgress('生成下载文件...', 97);
    await this.delay(1000);
    this.updateProgress('所有处理完成！', 100);
  }

  /**
   * 上传术语库
   */
  async uploadGlossary(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', file.name.replace('.xlsx', ''));

      const glossary = await window.api.createGlossary(formData);
      this.glossaryId = glossary.id;

      console.log('[Workflow] Glossary uploaded:', glossary.id);
    } catch (error) {
      console.warn('[Workflow] Failed to upload glossary:', error);
      // 不阻塞主流程
    }
  }

  /**
   * 等待拆分完成（参考测试页面的稳定实现）
   */
  async waitForSplit(sessionId) {
    const maxAttempts = 120; // 最多等待2分钟（每次1秒）
    let attempts = 0;

    while (attempts < maxAttempts) {
      attempts++;
      await this.delay(1000); // 每秒检查一次（测试页面的节奏）

      try {
        const status = await window.api.getSplitStatus(sessionId);

        if (status.status === 'completed') {
          console.log(`[Workflow] Split completed: ${status.task_count} tasks`);
          return; // 成功完成，返回
        }

        if (status.status === 'failed') {
          throw new Error(`Split failed: ${status.message || 'Unknown error'}`);
        }

        // 其他状态（processing, not_started等）继续等待
        if (status.progress !== undefined) {
          console.log(`[Workflow] Split in progress... ${status.progress}% (attempt ${attempts}/${maxAttempts})`);
        } else {
          console.log(`[Workflow] Waiting for split... ${status.status} (attempt ${attempts}/${maxAttempts})`);
        }

      } catch (error) {
        // 如果是明确的失败错误（含"Split failed"或"404"），立即抛出
        if (error.message && (error.message.includes('Split failed') || error.message.includes('404') || error.message.includes('not found'))) {
          console.error('[Workflow] Split failed with error:', error.message);
          throw error;
        }

        // 网络临时错误，记录但继续重试
        console.warn(`[Workflow] Temporary error checking split status (attempt ${attempts}):`, error.message);

        // 如果已经重试很多次仍然失败，抛出错误
        if (attempts >= maxAttempts) {
          throw new Error(`Split status check failed after ${maxAttempts} attempts: ${error.message}`);
        }
      }
    }

    // 超时
    throw new Error(`Split timeout after ${maxAttempts} seconds. Split did not complete.`);
  }

  /**
   * 执行翻译（LLM）
   */
  async executeTranslation(sessionId, startPercent, endPercent) {
    // 额外延迟，确保split完全保存
    await this.delay(1000);

    // 启动执行
    await window.api.startExecution(sessionId, {
      processor: 'llm_qwen',
      max_workers: 10,
      glossary_id: this.glossaryId
    });

    // 监控进度
    await this.monitorProgress(sessionId, startPercent, endPercent);
  }

  /**
   * 执行转换（CAPS uppercase）
   */
  async executeTransformation(sessionId, startPercent, endPercent) {
    // 额外延迟，确保split完全保存
    await this.delay(1000);

    // 启动执行
    await window.api.startExecution(sessionId, {
      processor: 'uppercase',
      max_workers: 20
    });

    // 监控进度
    await this.monitorProgress(sessionId, startPercent, endPercent);
  }

  /**
   * 监控执行进度（WebSocket）
   */
  async monitorProgress(sessionId, startPercent, endPercent) {
    return new Promise((resolve, reject) => {
      const wsUrl = `ws://localhost:8013/api/websocket/progress/${sessionId}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[Workflow] WebSocket connected:', sessionId);
      };

      ws.onmessage = (event) => {
        try {
          const progress = JSON.parse(event.data);

          // 映射到整体进度范围
          const percent = startPercent + (progress.percent / 100) * (endPercent - startPercent);

          this.updateProgress(
            `处理中... ${progress.completed}/${progress.total}`,
            Math.round(percent),
            {
              completed: progress.completed,
              total: progress.total,
              failed: progress.failed || 0
            }
          );

          if (progress.status === 'completed') {
            ws.close();
            console.log('[Workflow] Execution completed:', sessionId);
            resolve();
          } else if (progress.status === 'failed') {
            ws.close();
            reject(new Error('Execution failed'));
          }
        } catch (error) {
          console.error('[Workflow] WebSocket message error:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[Workflow] WebSocket error:', error);
        // 不立即拒绝，可能是暂时性错误
      };

      ws.onclose = () => {
        console.log('[Workflow] WebSocket closed:', sessionId);
      };

      // 超时保护（10分钟）
      setTimeout(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
          reject(new Error('Execution timeout'));
        }
      }, 10 * 60 * 1000);
    });
  }

  /**
   * 延迟工具函数
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AutoWorkflowOrchestrator;
}
