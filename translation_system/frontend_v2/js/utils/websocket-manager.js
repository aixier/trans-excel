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
    }

    // 连接WebSocket
    connect(onMessage) {
        this.messageHandler = onMessage;

        try {
            const wsUrl = `${APP_CONFIG.WS_BASE_URL}/ws/progress/${this.sessionId}`;
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                logger.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.stopPolling();
                this.updateConnectionStatus('connected');
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                } catch (error) {
                    logger.error('Failed to parse WebSocket message:', error);
                }
            };

            this.ws.onerror = (error) => {
                logger.error('WebSocket error:', error);
                this.handleDisconnect();
            };

            this.ws.onclose = () => {
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
}