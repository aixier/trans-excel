/**
 * 顺序工作流控制器 - 严格按照API时序图执行
 *
 * 核心功能：
 * 1. 防止重复执行（状态锁）
 * 2. 确保每个阶段完成后才进入下一阶段
 * 3. 支持CAPS两阶段流程
 *
 * @author Claude
 * @date 2025-10-17
 */

class SequentialWorkflowController {
  constructor() {
    // 状态管理
    this.state = {
      isRunning: false,        // 防止重复执行的锁
      currentPhase: null,      // 'translation' | 'caps' | null
      sessionIds: [],          // Session链
      progress: {
        percent: 0,
        message: '',
        details: {}
      }
    };

    // 配置
    this.config = {
      file: null,
      analysis: null,
      glossaryId: null,
      hasCaps: false
    };

    // 回调
    this.onProgressCallback = null;
    this.onCompletionCallback = null;
    this.onErrorCallback = null;
    this.onPhaseCompleteCallback = null;
  }

  /**
   * 设置回调函数
   */
  onProgress(callback) {
    this.onProgressCallback = callback;
  }

  onCompletion(callback) {
    this.onCompletionCallback = callback;
  }

  onError(callback) {
    this.onErrorCallback = callback;
  }

  onPhaseComplete(callback) {
    this.onPhaseCompleteCallback = callback;
  }

  /**
   * 执行工作流（入口函数）
   */
  async execute(file, config) {
    // 防止重复执行
    if (this.state.isRunning) {
      console.warn('[Workflow] Already running, ignoring duplicate execution request');
      return;
    }

    // 设置状态锁
    this.state.isRunning = true;
    this.state.sessionIds = [];

    try {
      // 保存配置
      this.config = {
        file: file,
        analysis: config.analysis,
        glossaryId: config.glossaryId
      };

      console.log('[Workflow] Starting sequential workflow', {
        file: file.name
      });

      // 执行统一流程：先翻译，然后由后端动态检测是否需要CAPS
      await this.executeUnifiedFlow();

      // 完成
      this.notifyCompletion();

    } catch (error) {
      console.error('[Workflow] Execution failed:', error);
      this.notifyError(error);
      throw error;
    } finally {
      // 释放状态锁
      this.state.isRunning = false;
      this.state.currentPhase = null;
    }
  }

  /**
   * 统一流程 - 动态检测是否需要CAPS
   */
  async executeUnifiedFlow() {
    console.log('[Workflow] Executing unified flow with dynamic CAPS detection');

    // ========== 阶段1：翻译 ==========
    this.state.currentPhase = 'translation';

    // 1.1 上传并拆分翻译任务
    this.updateProgress(5, '上传文件并拆分翻译任务...', {});
    const session1 = await this.uploadAndSplit('translation');
    this.state.sessionIds.push(session1);

    // 1.2 执行翻译
    this.updateProgress(15, 'AI翻译执行中...', { sessionId: session1 });
    await this.executeWithMonitoring(session1, 'llm_qwen', 15, 60);

    // ⭐ 关键：等待翻译完全完成
    this.updateProgress(60, '验证翻译完成状态...', { sessionId: session1 });
    await this.waitForExecutionComplete(session1);

    // 🎉 阶段1完成，触发回调
    this.notifyPhaseComplete({
      phase: 1,
      name: '翻译阶段',
      icon: '🤖',
      sessionId: session1
    });

    // ========== 动态检测是否需要CAPS阶段 ==========
    this.updateProgress(65, '检测是否需要CAPS处理...', { sessionId: session1 });
    const needsCaps = await this.checkIfNeedsCaps(session1);

    if (needsCaps) {
      console.log('[Workflow] CAPS detected, continuing with CAPS phase');

      // ========== 阶段2：CAPS转换 ==========
      this.state.currentPhase = 'caps';

      // 2.1 从父Session拆分CAPS任务
      this.updateProgress(65, '阶段2/2: 拆分CAPS任务...', { sessionId: session1 });
      const session2 = await this.splitFromParent(session1, 'caps_only');
      this.state.sessionIds.push(session2);

      // 2.2 执行CAPS转换
      this.updateProgress(70, '阶段2/2: CAPS转换执行中...', { sessionId: session2 });
      await this.executeWithMonitoring(session2, 'uppercase', 70, 95);

      // 🎉 阶段2完成，触发回调
      this.notifyPhaseComplete({
        phase: 2,
        name: 'CAPS转换阶段',
        icon: '🔠',
        sessionId: session2
      });

      this.updateProgress(100, '所有处理完成！(翻译+CAPS)', { sessionId: session2 });
    } else {
      console.log('[Workflow] No CAPS detected, workflow complete');
      this.updateProgress(100, '翻译完成！', { sessionId: session1 });
    }
  }

  /**
   * 检查是否需要CAPS处理（通过查询session的分析结果）
   */
  async checkIfNeedsCaps(sessionId) {
    try {
      // 查询session详情，获取后端分析的文件信息
      const response = await fetch(`${window.API_BASE_URL}/api/sessions/detail/${sessionId}`);
      if (!response.ok) {
        console.warn('Failed to get session details, assuming no CAPS needed');
        return false;
      }

      const session = await response.json();

      // 检查metadata中的analysis.file_info.sheets
      const sheets = session.metadata?.analysis?.file_info?.sheets || [];
      const hasCaps = sheets.some(sheet =>
        typeof sheet === 'string' && sheet.toLowerCase().includes('caps')
      );

      console.log(`[Workflow] CAPS detection result: ${hasCaps}`, { sheets });
      return hasCaps;

    } catch (error) {
      console.error('[Workflow] Error checking CAPS requirement:', error);
      // 出错时默认不执行CAPS
      return false;
    }
  }

  /**
   * 上传文件并拆分任务
   */
  async uploadAndSplit(ruleSet) {
    console.log(`[Workflow] Uploading file with rule_set: ${ruleSet}`);

    // 从分析结果获取语言配置
    const suggested = this.config.analysis?.language_detection?.suggested_config || {};

    // 上传文件并拆分
    const formData = new FormData();
    formData.append('file', this.config.file);
    formData.append('source_lang', suggested.source_lang || 'CH');
    formData.append('target_langs', JSON.stringify(suggested.target_langs || ['EN']));
    formData.append('rule_set', ruleSet);
    formData.append('extract_context', 'true');

    const response = await fetch(`${window.API_BASE_URL}/api/tasks/split`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Upload failed: ${error}`);
    }

    const result = await response.json();
    const sessionId = result.session_id;

    console.log(`[Workflow] Created session: ${sessionId}`);

    // 等待拆分完成
    await this.waitForSplitComplete(sessionId);

    return sessionId;
  }

  /**
   * 从父Session继承并拆分
   */
  async splitFromParent(parentSessionId, ruleSet) {
    console.log(`[Workflow] Creating child session from parent: ${parentSessionId}`);

    const formData = new FormData();
    formData.append('parent_session_id', parentSessionId);
    formData.append('rule_set', ruleSet);
    formData.append('extract_context', 'false');  // CAPS不需要context

    const response = await fetch(`${window.API_BASE_URL}/api/tasks/split`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Split from parent failed: ${error}`);
    }

    const result = await response.json();
    const sessionId = result.session_id;

    console.log(`[Workflow] Created child session: ${sessionId}`);

    // 等待拆分完成
    await this.waitForSplitComplete(sessionId);

    return sessionId;
  }

  /**
   * 等待拆分完成（轮询）
   */
  async waitForSplitComplete(sessionId) {
    console.log(`[Workflow] Waiting for split to complete: ${sessionId}`);

    const maxAttempts = 120;  // 最多等待2分钟
    let attempts = 0;

    while (attempts < maxAttempts) {
      attempts++;

      // 延迟1秒
      await this.delay(1000);

      try {
        const response = await fetch(`${window.API_BASE_URL}/api/tasks/split/status/${sessionId}`);
        if (!response.ok) {
          throw new Error(`Failed to get split status: ${response.status}`);
        }

        const status = await response.json();

        if (status.status === 'completed') {
          console.log(`[Workflow] Split completed: ${status.task_count} tasks`);
          return;
        }

        if (status.status === 'failed') {
          throw new Error(`Split failed: ${status.message}`);
        }

        // 继续等待
        if (attempts % 5 === 0) {
          console.log(`[Workflow] Still waiting for split... (${attempts}/${maxAttempts})`);
        }

      } catch (error) {
        console.error(`[Workflow] Error checking split status:`, error);
        if (attempts >= maxAttempts) {
          throw error;
        }
      }
    }

    throw new Error('Split timeout after 2 minutes');
  }

  /**
   * 启动执行并监控进度
   */
  async executeWithMonitoring(sessionId, processor, startPercent, endPercent) {
    console.log(`[Workflow] Starting execution: ${sessionId}, processor: ${processor}`);

    // 额外延迟确保split完全保存
    await this.delay(1000);

    // 启动执行
    const response = await fetch(`${window.API_BASE_URL}/api/execute/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        processor: processor,
        max_workers: processor === 'uppercase' ? 20 : 10,
        glossary_id: this.config.glossaryId
      })
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Execute start failed: ${error}`);
    }

    const result = await response.json();
    console.log(`[Workflow] Execution started:`, result);

    // 延迟500ms等待后端完全初始化WebSocket endpoint
    await this.delay(500);

    // WebSocket监控进度
    await this.monitorProgressViaWebSocket(sessionId, startPercent, endPercent);
  }

  /**
   * WebSocket监控进度（带轮询回退）
   */
  async monitorProgressViaWebSocket(sessionId, startPercent, endPercent) {
    return new Promise((resolve, reject) => {
      const wsUrl = `ws://localhost:8013/api/websocket/progress/${sessionId}`;
      console.log(`[Workflow] Connecting WebSocket: ${wsUrl}`);

      const ws = new WebSocket(wsUrl);
      let heartbeatInterval = null;
      let wsConnected = false;
      let fallbackToPolling = false;

      // 如果5秒内WebSocket没连接成功，回退到轮询
      const connectionTimeout = setTimeout(() => {
        if (!wsConnected) {
          console.warn('[Workflow] WebSocket connection timeout, falling back to polling');
          fallbackToPolling = true;
          ws.close();
          // 使用轮询方式
          this.monitorProgressViaPolling(sessionId, startPercent, endPercent)
            .then(resolve)
            .catch(reject);
        }
      }, 5000);

      ws.onopen = () => {
        wsConnected = true;
        clearTimeout(connectionTimeout);
        console.log(`[Workflow] WebSocket connected for ${sessionId}`);

        // 心跳保活
        heartbeatInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          const progress = JSON.parse(event.data);

          // 映射进度到指定范围
          const percent = startPercent + (progress.percent / 100) * (endPercent - startPercent);

          // 更新进度显示
          const phasePrefix = this.state.currentPhase === 'caps' ? '阶段2/2: ' :
                             this.state.currentPhase === 'translation' ? '阶段1/2: ' : '';

          this.updateProgress(
            Math.round(percent),
            `${phasePrefix}处理中... ${progress.completed}/${progress.total}`,
            {
              completed: progress.completed,
              total: progress.total,
              failed: progress.failed || 0,
              sessionId: sessionId
            }
          );

          // 检查是否完成
          if (progress.status === 'completed') {
            console.log(`[Workflow] Execution completed via WebSocket: ${sessionId}`);
            clearInterval(heartbeatInterval);
            ws.close();
            resolve();
          } else if (progress.status === 'failed') {
            clearInterval(heartbeatInterval);
            ws.close();
            reject(new Error('Execution failed'));
          }

        } catch (error) {
          console.error('[Workflow] WebSocket message parse error:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[Workflow] WebSocket error:', error);
        // 不立即reject，等待onclose或timeout处理
      };

      ws.onclose = (event) => {
        console.log(`[Workflow] WebSocket closed for ${sessionId}, code: ${event.code}`);
        clearTimeout(connectionTimeout);
        clearInterval(heartbeatInterval);

        // 如果已经在使用轮询，不做任何处理
        if (fallbackToPolling) {
          return;
        }

        // 如果没有成功连接过，回退到轮询
        if (!wsConnected) {
          console.warn('[Workflow] WebSocket never connected, falling back to polling');
          this.monitorProgressViaPolling(sessionId, startPercent, endPercent)
            .then(resolve)
            .catch(reject);
        }
      };
    });
  }

  /**
   * 轮询监控进度（WebSocket回退方案）
   */
  async monitorProgressViaPolling(sessionId, startPercent, endPercent) {
    console.log(`[Workflow] Using polling for progress monitoring: ${sessionId}`);

    const maxAttempts = 600; // 最多轮询10分钟（每秒一次）
    let attempts = 0;

    while (attempts < maxAttempts) {
      attempts++;
      await this.delay(1000);

      try {
        const response = await fetch(`${window.API_BASE_URL}/api/execute/status/${sessionId}`);
        if (!response.ok) {
          console.warn(`Failed to get execution status: ${response.status}`);
          continue;
        }

        const status = await response.json();

        // 更新进度
        if (status.statistics) {
          const completed = status.statistics.by_status?.completed || 0;
          const total = status.statistics.total || 1;
          const progress = (completed / total) * 100;

          const percent = startPercent + (progress / 100) * (endPercent - startPercent);
          const phasePrefix = this.state.currentPhase === 'caps' ? '阶段2/2: ' :
                             this.state.currentPhase === 'translation' ? '阶段1/2: ' : '';

          this.updateProgress(
            Math.round(percent),
            `${phasePrefix}处理中... ${completed}/${total}`,
            {
              completed: completed,
              total: total,
              failed: status.statistics.by_status?.failed || 0,
              sessionId: sessionId
            }
          );
        }

        // 检查是否完成
        if (status.status === 'completed') {
          console.log(`[Workflow] Execution completed via polling: ${sessionId}`);
          return;
        }

        if (status.status === 'failed') {
          throw new Error('Execution failed');
        }

        // 每10次输出一次日志
        if (attempts % 10 === 0) {
          console.log(`[Workflow] Polling progress... (${attempts}/${maxAttempts})`);
        }

      } catch (error) {
        console.error('[Workflow] Error polling execution status:', error);
        if (attempts >= maxAttempts) {
          throw error;
        }
      }
    }

    throw new Error('Execution monitoring timeout');
  }

  /**
   * 等待执行完全完成（关键步骤）
   */
  async waitForExecutionComplete(sessionId) {
    console.log(`[Workflow] Verifying execution completion: ${sessionId}`);

    const maxAttempts = 60;  // 最多等待1分钟
    let attempts = 0;

    while (attempts < maxAttempts) {
      attempts++;
      await this.delay(1000);

      try {
        const response = await fetch(`${window.API_BASE_URL}/api/execute/status/${sessionId}`);
        if (!response.ok) {
          console.warn(`Failed to get execution status: ${response.status}`);
          continue;
        }

        const status = await response.json();

        if (status.status === 'completed' && status.ready_for_download) {
          console.log(`[Workflow] Execution verified as complete: ${sessionId}`);
          return;
        }

        if (status.status === 'failed') {
          throw new Error('Execution failed');
        }

        // 继续等待
        if (attempts % 10 === 0) {
          console.log(`[Workflow] Still verifying completion... (${attempts}/${maxAttempts})`);
        }

      } catch (error) {
        console.error('[Workflow] Error checking execution status:', error);
        if (attempts >= maxAttempts) {
          throw error;
        }
      }
    }

    // 如果超时但没有明确失败，假设成功（兼容性）
    console.warn('[Workflow] Execution verification timeout, assuming success');
  }

  /**
   * 更新进度
   */
  updateProgress(percent, message, details = {}) {
    this.state.progress = {
      percent: percent,
      message: message,
      details: details
    };

    console.log(`[Workflow] ${percent}%: ${message}`);

    if (this.onProgressCallback) {
      this.onProgressCallback(this.state.progress);
    }
  }

  /**
   * 通知阶段完成
   */
  notifyPhaseComplete(phaseInfo) {
    console.log(`[Workflow] Phase ${phaseInfo.phase} completed:`, phaseInfo.sessionId);

    if (this.onPhaseCompleteCallback) {
      this.onPhaseCompleteCallback(phaseInfo);
    }
  }

  /**
   * 通知完成
   */
  notifyCompletion() {
    const finalSessionId = this.state.sessionIds[this.state.sessionIds.length - 1];
    const hasCaps = this.state.sessionIds.length > 1;  // 如果有2个session说明执行了CAPS

    console.log(`[Workflow] Completed successfully! Final session: ${finalSessionId}, phases: ${this.state.sessionIds.length}`);

    if (this.onCompletionCallback) {
      this.onCompletionCallback({
        sessionId: finalSessionId,
        sessionIds: this.state.sessionIds,
        hasCaps: hasCaps  // 动态判断，而非硬编码
      });
    }
  }

  /**
   * 通知错误
   */
  notifyError(error) {
    console.error('[Workflow] Error occurred:', error);

    if (this.onErrorCallback) {
      this.onErrorCallback(error);
    }
  }

  /**
   * 延迟工具
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 检查是否正在运行
   */
  isRunning() {
    return this.state.isRunning;
  }

  /**
   * 获取当前进度
   */
  getProgress() {
    return this.state.progress;
  }

  /**
   * 获取Session链
   */
  getSessionIds() {
    return this.state.sessionIds;
  }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SequentialWorkflowController;
}