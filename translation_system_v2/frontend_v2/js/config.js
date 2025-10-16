// 应用配置
const APP_CONFIG = {
    // API基础路径
    API_BASE_URL: '',  // 使用相对路径，避免跨域问题

    // WebSocket路径
    WS_BASE_URL: `ws://${window.location.host}`,

    // 会话超时时间（8小时）
    SESSION_TIMEOUT: 8 * 60 * 60 * 1000,

    // 会话警告时间（30分钟）
    SESSION_WARNING_TIME: 30 * 60 * 1000,

    // 文件上传限制
    MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
    ALLOWED_EXTENSIONS: ['.xlsx', '.xls'],

    // 轮询间隔
    POLL_INTERVAL: 2000, // 2秒
    SPLIT_POLL_INTERVAL: 1000, // 1秒

    // WebSocket重连配置
    WS_MAX_RECONNECT_ATTEMPTS: 3,
    WS_RECONNECT_DELAY: 1000, // 初始重连延迟

    // 支持的语言
    LANGUAGES: {
        source: {
            'auto': '自动检测',
            'CH': '中文',
            'EN': '英文'
        },
        target: {
            'CH': '中文',
            'EN': '英文',
            'TR': '土耳其语',
            'TH': '泰语',
            'PT': '葡萄牙语',
            'VN': '越南语',
            'IND': '印尼语',
            'ES': '西班牙语'
        }
    },

    // 默认配置
    DEFAULT_CONFIG: {
        source_lang: null, // 自动检测
        target_langs: [],
        extract_context: true,
        context_options: {
            game_info: true,
            comments: true,
            neighbors: true,
            content_analysis: true,
            sheet_type: true
        }
    },

    // UI配置
    UI: {
        TOAST_DURATION: 3000, // 提示持续时间
        ANIMATION_DURATION: 300, // 动画持续时间
        DEBOUNCE_DELAY: 300, // 防抖延迟
    },

    // 调试模式
    DEBUG: true
};

// 日志工具
const logger = {
    log: (...args) => {
        if (APP_CONFIG.DEBUG) {
            console.log('[APP]', ...args);
        }
    },
    error: (...args) => {
        console.error('[APP ERROR]', ...args);
    },
    warn: (...args) => {
        if (APP_CONFIG.DEBUG) {
            console.warn('[APP WARN]', ...args);
        }
    }
};