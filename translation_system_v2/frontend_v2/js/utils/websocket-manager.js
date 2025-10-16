// WebSocket管理器（优化断开体验）
class WebSocketManager {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = APP_CONFIG.WS_MAX_RECONNECT_ATTEMPTS;
        this.isPolling = false;
        this.pollingInterval = null;
        this.messageHandler = null;
        this.messageCount = 0; // 🔍 消息计数器
    }

    // 连接WebSocket
    connect(onMessage) {
        this.messageHandler = onMessage;

        try {
            const wsUrl = `${APP_CONFIG.WS_BASE_URL}/ws/progress/${this.sessionId}`;
            console.log('🔌 [WebSocket] Connecting to:', wsUrl);
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('✅ [WebSocket] Connected successfully');
                console.log('✅ [WebSocket] Ready state:', this.ws.readyState, '(1=OPEN)');
                logger.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.messageCount = 0; // 重置计数器
                this.stopPolling();
                this.updateConnectionStatus('connected');

                // 🔍 定期检查WebSocket状态并发送心跳
                this.startHeartbeat();
            };

            this.ws.onmessage = (event) => {
                try {
                    this.messageCount++;
                    const message = JSON.parse(event.data);
                    console.log(`🔌 [WebSocket #${this.messageCount}] Raw message received:`, event.data);
                    console.log(`🔌 [WebSocket #${this.messageCount}] Parsed message:`, message);
                    this.handleMessage(message);
                } catch (error) {
                    logger.error('Failed to parse WebSocket message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('❌ [WebSocket] Error occurred:', error);
                console.error('❌ [WebSocket] Ready state:', this.ws?.readyState);
                logger.error('WebSocket error:', error);
                this.handleDisconnect();
            };

            this.ws.onclose = (event) => {
                console.warn('⚠️ [WebSocket] Connection closed');
                console.warn('⚠️ [WebSocket] Code:', event.code, 'Reason:', event.reason);
                console.warn('⚠️ [WebSocket] Total messages received:', this.messageCount);
                logger.log('WebSocket closed');
                this.handleDisconnect();
            };

        } catch (error) {
            logger.error('Failed to create WebSocket:', error);
            this.handleDisconnect();
        }
    }

    // 处理断开连接
    handleDisconnect() {
        this.updateConnectionStatus('disconnected');

        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            // 尝试重连
            this.reconnectAttempts++;
            const delay = Math.pow(2, this.reconnectAttempts) * APP_CONFIG.WS_RECONNECT_DELAY;

            logger.log(`Reconnecting in ${delay}ms... (attempt ${this.reconnectAttempts})`);

            setTimeout(() => this.connect(this.messageHandler), delay);
        } else {
            // 切换到HTTP轮询模式
            this.switchToPolling();
        }
    }

    // 切换到轮询模式
    switchToPolling() {
        if (this.isPolling) return;

        this.isPolling = true;
        this.updateConnectionStatus('polling');

        UIHelper.showToast('已切换到兼容模式，继续获取进度更新', 'info');

        // 立即执行一次轮询
        this.pollStatus();

        // 设置轮询间隔
        this.pollingInterval = setInterval(() => {
            this.pollStatus();
        }, APP_CONFIG.POLL_INTERVAL);

        // 后台继续尝试WebSocket重连
        this.backgroundReconnect();
    }

    // 轮询状态
    async pollStatus() {
        try {
            const data = await API.getExecutionProgress(this.sessionId);
            this.handleMessage({
                type: 'progress',
                data: data.progress
            });
        } catch (error) {
            logger.error('Polling error:', error);
        }
    }

    // 后台重连WebSocket
    backgroundReconnect() {
        setTimeout(() => {
            if (this.isPolling) {
                logger.log('Attempting WebSocket reconnection...');

                const wsUrl = `${APP_CONFIG.WS_BASE_URL}/ws/progress/${this.sessionId}`;
                const testWs = new WebSocket(wsUrl);

                testWs.onopen = () => {
                    // 重连成功
                    this.stopPolling();
                    this.ws = testWs;
                    this.isPolling = false;
                    this.reconnectAttempts = 0;
                    this.updateConnectionStatus('connected');

                    UIHelper.showToast('已恢复实时连接', 'success');

                    // 设置消息处理
                    testWs.onmessage = (event) => {
                        const message = JSON.parse(event.data);
                        this.handleMessage(message);
                    };

                    testWs.onerror = () => this.handleDisconnect();
                    testWs.onclose = () => this.handleDisconnect();
                };

                testWs.onerror = () => {
                    testWs.close();
                    // 失败了，稍后再试
                    this.backgroundReconnect();
                };
            }
        }, 30000); // 30秒后重试
    }

    // 停止轮询
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        this.isPolling = false;
    }

    // 处理消息
    handleMessage(message) {
        if (this.messageHandler) {
            this.messageHandler(message);
        }
    }

    // 更新连接状态显示
    updateConnectionStatus(status) {
        const indicator = document.getElementById('connectionStatus');
        const badge = document.getElementById('connectionBadge');
        const text = document.getElementById('connectionText');

        if (!indicator) return;

        indicator.classList.remove('hidden');

        switch (status) {
            case 'connected':
                badge.className = 'badge badge-success badge-lg';
                text.innerHTML = '<i class="bi bi-wifi mr-1"></i>实时连接';
                break;
            case 'polling':
                badge.className = 'badge badge-warning badge-lg';
                text.innerHTML = '<i class="bi bi-arrow-repeat mr-1"></i>兼容模式';
                break;
            case 'disconnected':
                badge.className = 'badge badge-error badge-lg';
                text.innerHTML = '<i class="bi bi-wifi-off mr-1"></i>连接中...';
                break;
        }
    }

    // 断开连接
    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
        this.stopPolling();
        this.stopHeartbeat();
        this.updateConnectionStatus('disconnected');

        const indicator = document.getElementById('connectionStatus');
        if (indicator) {
            indicator.classList.add('hidden');
        }
    }

    // 发送消息
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
            return true;
        }
        return false;
    }

    // 🔍 启动心跳检测
    startHeartbeat() {
        // 清除旧的心跳定时器
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }

        let lastMessageCount = 0;
        let noMessageCount = 0;

        this.heartbeatInterval = setInterval(() => {
            console.log(`💓 [Heartbeat] State: ${this.ws?.readyState}, Messages: ${this.messageCount}, Last: ${lastMessageCount}`);

            // 检查是否有新消息
            if (this.messageCount === lastMessageCount) {
                noMessageCount++;
                console.warn(`⚠️ [Heartbeat] No new messages for ${noMessageCount * 5}s`);

                // 超过15秒没有新消息且执行中，切换到轮询
                if (noMessageCount >= 3) {
                    console.error('❌ [Heartbeat] WebSocket appears stuck, switching to polling');
                    this.stopHeartbeat();
                    this.switchToPolling();
                }
            } else {
                noMessageCount = 0;
            }

            lastMessageCount = this.messageCount;

            // 发送ping保持连接
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.send({ type: 'ping' });
            }
        }, 5000); // 每5秒检查一次
    }

    // 停止心跳检测
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
}