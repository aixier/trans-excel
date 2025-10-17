/**
 * WebSocket管理器 - 实时进度推送
 *
 * @class WebSocketManager
 * @description
 * 管理WebSocket连接，支持心跳检测、断线重连、消息分发
 *
 * @example
 * const wsManager = new WebSocketManager();
 * wsManager.connect(sessionId, {
 *   onProgress: (data) => console.log('Progress:', data),
 *   onTaskUpdate: (data) => console.log('Task:', data),
 *   onError: (error) => console.error('Error:', error)
 * });
 */
class WebSocketManager {
  /**
   * 创建WebSocketManager实例
   *
   * @param {string} baseURL - WebSocket基础URL
   */
  constructor(baseURL = 'ws://localhost:8013') {
    /** @type {string} WebSocket基础URL */
    this.baseURL = baseURL;

    /** @type {Map<string, Object>} 连接映射表 */
    this.connections = new Map();

    /** @type {number} 心跳间隔(ms) */
    this.heartbeatInterval = 30000; // 30秒

    /** @type {number} 重连间隔(ms) */
    this.reconnectInterval = 3000; // 3秒

    /** @type {number} 最大重连次数 */
    this.maxReconnectAttempts = 3;

    /** @type {boolean} 是否启用调试日志 */
    this.debug = false;
  }

  /**
   * 连接WebSocket
   *
   * @param {string} sessionId - Session ID
   * @param {Object} callbacks - 回调函数
   * @param {Function} callbacks.onProgress - 进度更新回调
   * @param {Function} callbacks.onTaskUpdate - 任务更新回调
   * @param {Function} callbacks.onComplete - 完成回调
   * @param {Function} callbacks.onError - 错误回调
   * @param {Function} callbacks.onClose - 连接关闭回调
   * @returns {WebSocket} WebSocket实例
   *
   * @example
   * wsManager.connect('session-123', {
   *   onProgress: (data) => {
   *     console.log(`Progress: ${data.progress}%`);
   *   },
   *   onTaskUpdate: (data) => {
   *     console.log(`Task ${data.task_id}: ${data.status}`);
   *   }
   * });
   */
  connect(sessionId, callbacks = {}) {
    // 如果已存在连接，先断开
    if (this.connections.has(sessionId)) {
      this.disconnect(sessionId);
    }

    const url = `${this.baseURL}/api/websocket/progress/${sessionId}`;
    this.log(`Connecting to: ${url}`);

    const ws = new WebSocket(url);
    const connection = {
      ws: ws,
      sessionId: sessionId,
      callbacks: callbacks,
      heartbeatTimer: null,
      reconnectAttempts: 0,
      isManualClose: false
    };

    // 连接打开
    ws.onopen = () => {
      this.log(`WebSocket connected: ${sessionId}`);
      connection.reconnectAttempts = 0;
      this._setupHeartbeat(connection);

      if (callbacks.onOpen) {
        callbacks.onOpen();
      }
    };

    // 接收消息
    ws.onmessage = (event) => {
      this._handleMessage(connection, event);
    };

    // 连接错误
    ws.onerror = (error) => {
      this.log(`WebSocket error: ${sessionId}`, error);

      if (callbacks.onError) {
        callbacks.onError(error);
      }
    };

    // 连接关闭
    ws.onclose = (event) => {
      this.log(`WebSocket closed: ${sessionId}`, event);

      // 清除心跳
      this._clearHeartbeat(connection);

      // 触发关闭回调
      if (callbacks.onClose) {
        callbacks.onClose(event);
      }

      // 自动重连（非手动关闭且未超过重连次数）
      if (!connection.isManualClose && connection.reconnectAttempts < this.maxReconnectAttempts) {
        this._handleReconnect(connection);
      } else {
        this.connections.delete(sessionId);
      }
    };

    this.connections.set(sessionId, connection);
    return ws;
  }

  /**
   * 断开WebSocket连接
   *
   * @param {string} sessionId - Session ID
   */
  disconnect(sessionId) {
    const connection = this.connections.get(sessionId);
    if (!connection) {
      this.log(`No connection found for: ${sessionId}`);
      return;
    }

    this.log(`Disconnecting: ${sessionId}`);

    // 标记为手动关闭
    connection.isManualClose = true;

    // 清除心跳
    this._clearHeartbeat(connection);

    // 关闭连接
    if (connection.ws.readyState === WebSocket.OPEN) {
      connection.ws.close(1000, 'Manual close');
    }

    this.connections.delete(sessionId);
  }

  /**
   * 断开所有连接
   */
  disconnectAll() {
    this.log(`Disconnecting all connections`);

    this.connections.forEach((connection, sessionId) => {
      this.disconnect(sessionId);
    });
  }

  /**
   * 发送消息
   *
   * @param {string} sessionId - Session ID
   * @param {any} message - 消息内容
   */
  send(sessionId, message) {
    const connection = this.connections.get(sessionId);
    if (!connection) {
      throw new Error(`No connection found for: ${sessionId}`);
    }

    if (connection.ws.readyState !== WebSocket.OPEN) {
      throw new Error(`WebSocket not open for: ${sessionId}`);
    }

    const data = typeof message === 'string' ? message : JSON.stringify(message);
    connection.ws.send(data);
    this.log(`Sent message to ${sessionId}:`, data);
  }

  /**
   * 处理收到的消息
   *
   * @param {Object} connection - 连接对象
   * @param {MessageEvent} event - 消息事件
   *
   * @private
   */
  _handleMessage(connection, event) {
    try {
      const data = JSON.parse(event.data);
      this.log(`Received message from ${connection.sessionId}:`, data);

      // 心跳响应
      if (data.type === 'pong') {
        this.log(`Heartbeat response from ${connection.sessionId}`);
        return;
      }

      // 根据消息类型分发到对应回调
      const { type, ...payload } = data;

      switch (type) {
        case 'progress':
          if (connection.callbacks.onProgress) {
            connection.callbacks.onProgress(payload);
          }
          break;

        case 'task_update':
          if (connection.callbacks.onTaskUpdate) {
            connection.callbacks.onTaskUpdate(payload);
          }
          break;

        case 'batch_complete':
          if (connection.callbacks.onBatchComplete) {
            connection.callbacks.onBatchComplete(payload);
          }
          break;

        case 'complete':
          if (connection.callbacks.onComplete) {
            connection.callbacks.onComplete(payload);
          }
          break;

        case 'error':
          if (connection.callbacks.onError) {
            connection.callbacks.onError(new Error(payload.message || 'Unknown error'));
          }
          break;

        case 'status':
          if (connection.callbacks.onStatus) {
            connection.callbacks.onStatus(payload);
          }
          break;

        default:
          this.log(`Unknown message type: ${type}`, payload);
          if (connection.callbacks.onMessage) {
            connection.callbacks.onMessage(data);
          }
      }
    } catch (error) {
      this.log(`Failed to parse message:`, error);

      if (connection.callbacks.onError) {
        connection.callbacks.onError(error);
      }
    }
  }

  /**
   * 设置心跳检测
   *
   * @param {Object} connection - 连接对象
   *
   * @private
   */
  _setupHeartbeat(connection) {
    // 清除已有心跳
    this._clearHeartbeat(connection);

    // 设置新的心跳
    connection.heartbeatTimer = setInterval(() => {
      if (connection.ws.readyState === WebSocket.OPEN) {
        try {
          connection.ws.send(JSON.stringify({ type: 'ping' }));
          this.log(`Sent heartbeat to ${connection.sessionId}`);
        } catch (error) {
          this.log(`Heartbeat failed for ${connection.sessionId}:`, error);
        }
      }
    }, this.heartbeatInterval);
  }

  /**
   * 清除心跳检测
   *
   * @param {Object} connection - 连接对象
   *
   * @private
   */
  _clearHeartbeat(connection) {
    if (connection.heartbeatTimer) {
      clearInterval(connection.heartbeatTimer);
      connection.heartbeatTimer = null;
    }
  }

  /**
   * 处理断线重连
   *
   * @param {Object} connection - 连接对象
   *
   * @private
   */
  _handleReconnect(connection) {
    connection.reconnectAttempts++;

    this.log(
      `Reconnecting ${connection.sessionId} (attempt ${connection.reconnectAttempts}/${this.maxReconnectAttempts})`
    );

    // 使用指数退避策略
    const delay = this.reconnectInterval * Math.pow(2, connection.reconnectAttempts - 1);

    setTimeout(() => {
      if (!connection.isManualClose) {
        this.connect(connection.sessionId, connection.callbacks);
      }
    }, delay);
  }

  /**
   * 获取连接状态
   *
   * @param {string} sessionId - Session ID
   * @returns {string|null} 连接状态 ('CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED')
   */
  getConnectionState(sessionId) {
    const connection = this.connections.get(sessionId);
    if (!connection) {
      return null;
    }

    const states = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'];
    return states[connection.ws.readyState];
  }

  /**
   * 检查连接是否存在
   *
   * @param {string} sessionId - Session ID
   * @returns {boolean} 是否存在连接
   */
  isConnected(sessionId) {
    const connection = this.connections.get(sessionId);
    return connection && connection.ws.readyState === WebSocket.OPEN;
  }

  /**
   * 设置基础URL
   *
   * @param {string} url - WebSocket基础URL
   */
  setBaseURL(url) {
    this.baseURL = url;
  }

  /**
   * 启用/禁用调试日志
   *
   * @param {boolean} enabled - 是否启用
   */
  setDebug(enabled) {
    this.debug = enabled;
  }

  /**
   * 打印日志
   *
   * @param {...any} args - 日志参数
   *
   * @private
   */
  log(...args) {
    if (this.debug) {
      console.log('[WebSocketManager]', ...args);
    }
  }
}

// 创建全局WebSocketManager实例
const wsManager = new WebSocketManager();

// ES6 模块导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = WebSocketManager;
  module.exports.wsManager = wsManager;
}
