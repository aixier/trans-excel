/**
 * API封装层 - 统一的HTTP请求处理
 *
 * @class API
 * @description
 * 封装所有后端API调用，提供统一的错误处理、请求拦截、响应缓存
 *
 * @example
 * const api = new API();
 * const sessions = await api.getSessions();
 */
class API {
  /**
   * 创建API实例
   *
   * @param {string} baseURL - API基础URL
   */
  constructor(baseURL = 'http://localhost:8013') {
    /** @type {string} API基础URL */
    this.baseURL = baseURL;

    /** @type {string|null} 认证Token */
    this.token = null;

    /** @type {number} 请求超时时间(ms) */
    this.timeout = 30000;

    /** @type {Map} 请求缓存 */
    this.cache = new Map();

    /** @type {number} 缓存TTL(ms) */
    this.cacheTTL = 60000; // 1分钟
  }

  /**
   * 设置认证Token
   *
   * @param {string} token - 认证Token
   */
  setToken(token) {
    this.token = token;
  }

  /**
   * 设置API基础URL
   *
   * @param {string} url - 基础URL
   */
  setBaseURL(url) {
    this.baseURL = url;
  }

  /**
   * 通用请求方法
   *
   * @param {string} endpoint - API端点
   * @param {Object} options - 请求选项
   * @param {boolean} useCache - 是否使用缓存（默认false）
   * @returns {Promise<any>} 响应数据
   *
   * @private
   */
  async request(endpoint, options = {}, useCache = false) {
    const url = `${this.baseURL}${endpoint}`;

    // 检查缓存
    if (useCache && options.method === 'GET') {
      const cached = this.getCache(url);
      if (cached) {
        return cached;
      }
    }

    // 默认请求头
    const headers = {
      ...options.headers
    };

    // 如果不是FormData，设置Content-Type
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    // 添加认证Token
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    // 请求配置
    const config = {
      ...options,
      headers
    };

    // 设置超时
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);
    config.signal = controller.signal;

    try {
      const response = await fetch(url, config);
      clearTimeout(timeoutId);

      // 处理响应
      const data = await this.handleResponse(response);

      // 缓存GET请求结果
      if (useCache && options.method === 'GET') {
        this.setCache(url, data);
      }

      return data;
    } catch (error) {
      clearTimeout(timeoutId);
      throw this.handleError(error);
    }
  }

  /**
   * 处理响应
   *
   * @param {Response} response - Fetch响应对象
   * @returns {Promise<any>} 响应数据
   *
   * @private
   */
  async handleResponse(response) {
    // 处理非JSON响应（如文件下载）
    const contentType = response.headers.get('content-type');
    if (contentType && !contentType.includes('application/json')) {
      if (response.ok) {
        return response;
      } else {
        throw new Error(`HTTP Error: ${response.status} ${response.statusText}`);
      }
    }

    // 解析JSON
    const data = await response.json();

    // 处理错误响应
    if (!response.ok) {
      throw {
        status: response.status,
        statusText: response.statusText,
        message: data.detail || data.message || 'Request failed',
        data: data
      };
    }

    return data;
  }

  /**
   * 处理错误
   *
   * @param {Error} error - 错误对象
   * @returns {Error} 格式化的错误对象
   *
   * @private
   */
  handleError(error) {
    // 网络错误
    if (error.name === 'AbortError') {
      return new Error('请求超时，请检查网络连接');
    }

    if (!navigator.onLine) {
      return new Error('网络连接已断开');
    }

    // API错误
    if (error.status) {
      const statusMessages = {
        400: '请求参数错误',
        401: '未授权，请重新登录',
        403: '没有权限访问',
        404: '请求的资源不存在',
        500: '服务器内部错误',
        502: '网关错误',
        503: '服务暂时不可用'
      };

      const message = statusMessages[error.status] || error.message;
      return new Error(message);
    }

    // 其他错误
    return error;
  }

  /**
   * GET请求
   */
  async get(endpoint, useCache = false) {
    return this.request(endpoint, { method: 'GET' }, useCache);
  }

  /**
   * POST请求
   */
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: data instanceof FormData ? data : JSON.stringify(data)
    });
  }

  /**
   * PUT请求
   */
  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  /**
   * DELETE请求
   */
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // ==================== 缓存管理 ====================

  /**
   * 获取缓存
   * @private
   */
  getCache(key) {
    const cached = this.cache.get(key);
    if (!cached) return null;

    // 检查是否过期
    if (Date.now() - cached.timestamp > this.cacheTTL) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  }

  /**
   * 设置缓存
   * @private
   */
  setCache(key, data) {
    this.cache.set(key, {
      data: data,
      timestamp: Date.now()
    });
  }

  /**
   * 清除缓存
   */
  clearCache(key = null) {
    if (key) {
      this.cache.delete(key);
    } else {
      this.cache.clear();
    }
  }

  // ==================== 任务拆分 API ====================

  /**
   * 上传文件并拆分任务
   *
   * @param {File} file - Excel文件
   * @param {Object} config - 拆分配置
   * @returns {Promise<Object>} Session信息
   */
  async uploadFile(file, config = {}) {
    const formData = new FormData();
    formData.append('file', file);

    if (config.target_langs) {
      formData.append('target_langs', JSON.stringify(config.target_langs));
    }
    if (config.rule_set) {
      formData.append('rule_set', config.rule_set);
    }
    if (config.extract_context !== undefined) {
      formData.append('extract_context', config.extract_context);
    }

    return this.post('/api/tasks/split', formData);
  }

  /**
   * 使用Parent Session拆分任务
   *
   * @param {string} parentSessionId - 父Session ID
   * @param {Object} config - 拆分配置
   * @returns {Promise<Object>} Session信息
   */
  async splitFromParent(parentSessionId, config = {}) {
    const formData = new FormData();
    formData.append('parent_session_id', parentSessionId);

    if (config.target_langs) {
      formData.append('target_langs', JSON.stringify(config.target_langs));
    }
    if (config.rule_set) {
      formData.append('rule_set', config.rule_set);
    }
    if (config.extract_context !== undefined) {
      formData.append('extract_context', config.extract_context);
    }

    return this.post('/api/tasks/split', formData);
  }

  /**
   * 获取任务拆分状态
   *
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} 拆分状态
   */
  async getSplitStatus(sessionId) {
    return this.get(`/api/tasks/split/status/${sessionId}`);
  }

  /**
   * 导出任务表
   *
   * @param {string} sessionId - Session ID
   * @param {string} exportType - 导出类型 ('tasks' | 'input')
   * @returns {Promise<Response>} 文件响应
   */
  async exportTasks(sessionId, exportType = 'tasks') {
    return this.get(`/api/tasks/export/${sessionId}?export_type=${exportType}`);
  }

  // ==================== 任务执行 API ====================

  /**
   * 开始执行任务
   *
   * @param {string} sessionId - Session ID
   * @param {Object} options - 执行选项
   * @returns {Promise<Object>} 执行状态
   */
  async startExecution(sessionId, options = {}) {
    return this.post('/api/execute/start', {
      session_id: sessionId,
      processor: options.processor || 'llm_qwen',
      max_workers: options.max_workers || 10,
      ...options
    });
  }

  /**
   * 暂停执行
   *
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} 响应
   */
  async pauseExecution(sessionId) {
    return this.post('/api/execute/pause', { session_id: sessionId });
  }

  /**
   * 恢复执行
   *
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} 响应
   */
  async resumeExecution(sessionId) {
    return this.post('/api/execute/resume', { session_id: sessionId });
  }

  /**
   * 停止执行
   *
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} 响应
   */
  async stopExecution(sessionId) {
    return this.post('/api/execute/stop', { session_id: sessionId });
  }

  /**
   * 获取执行进度
   *
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} 执行进度
   */
  async getExecutionProgress(sessionId) {
    return this.get(`/api/execute/progress/${sessionId}`);
  }

  /**
   * 获取执行状态
   *
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} 执行状态
   */
  async getExecutionStatus(sessionId) {
    return this.get(`/api/execute/status/${sessionId}`);
  }

  // ==================== 下载 API ====================

  /**
   * 下载Session结果
   *
   * @param {string} sessionId - Session ID
   * @returns {Promise<Blob>} 文件Blob
   */
  async downloadSession(sessionId) {
    const response = await this.get(`/api/download/${sessionId}`);
    return response.blob();
  }

  /**
   * 下载Input Excel
   *
   * @param {string} sessionId - Session ID
   * @returns {Promise<Blob>} 文件Blob
   */
  async downloadInput(sessionId) {
    const response = await this.get(`/api/download/${sessionId}/input`);
    return response.blob();
  }

  /**
   * 获取下载信息
   *
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} 下载信息
   */
  async getDownloadInfo(sessionId) {
    return this.get(`/api/download/${sessionId}/info`);
  }

  /**
   * 获取翻译摘要
   *
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} 翻译摘要
   */
  async getSummary(sessionId) {
    return this.get(`/api/download/${sessionId}/summary`);
  }

  // ==================== 会话管理 API ====================

  /**
   * 获取所有会话列表
   *
   * @returns {Promise<Array>} 会话列表
   */
  async getSessions() {
    const response = await this.get('/api/sessions', true); // 使用缓存
    // API返回 {sessions: [...], count: N, filter: '...'}, 我们只需要sessions数组
    const sessions = response.sessions || [];

    // 转换字段名从snake_case到camelCase，并转换时间字符串为时间戳
    return sessions.map(session => ({
      sessionId: session.session_id,
      filename: session.filename || 'unknown.xlsx',
      createdAt: new Date(session.created_at).getTime(),
      lastAccessed: new Date(session.last_accessed).getTime(),
      updatedAt: new Date(session.last_accessed).getTime(), // 使用last_accessed作为updatedAt
      stage: session.stage,
      hasTasks: session.has_tasks,
      progress: session.progress,
      status: session.status,
      isRunning: session.is_running,
      canResume: session.can_resume,
      canDownload: session.can_download
    }));
  }

  /**
   * 获取会话详情
   *
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} 会话详情
   */
  async getSessionDetail(sessionId) {
    return this.get(`/api/sessions/detail/${sessionId}`);
  }

  /**
   * 删除会话
   *
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} 响应
   */
  async deleteSession(sessionId) {
    return this.delete(`/api/sessions/${sessionId}`);
  }

  // ==================== 术语库 API ====================

  /**
   * 获取术语库列表
   *
   * @returns {Promise<Array>} 术语库列表
   */
  async getGlossaries() {
    const response = await this.get('/api/glossaries/list', true);
    // API返回 {glossaries: [...], count: N}, 我们只需要glossaries数组
    return response.glossaries || [];
  }

  /**
   * 获取术语库详情
   *
   * @param {string} id - 术语库ID
   * @returns {Promise<Object>} 术语库详情
   */
  async getGlossary(id) {
    return this.get(`/api/glossaries/${id}`);
  }

  /**
   * 创建术语库
   *
   * @param {Object} data - 术语库数据
   * @returns {Promise<Object>} 创建的术语库
   */
  async createGlossary(data) {
    return this.post('/api/glossaries', data);
  }

  /**
   * 更新术语库
   *
   * @param {string} id - 术语库ID
   * @param {Object} data - 更新数据
   * @returns {Promise<Object>} 更新后的术语库
   */
  async updateGlossary(id, data) {
    return this.put(`/api/glossaries/${id}`, data);
  }

  /**
   * 删除术语库
   *
   * @param {string} id - 术语库ID
   * @returns {Promise<Object>} 响应
   */
  async deleteGlossary(id) {
    return this.delete(`/api/glossaries/${id}`);
  }

  /**
   * 导入术语
   *
   * @param {string} glossaryId - 术语库ID
   * @param {Array} terms - 术语列表
   * @returns {Promise<Object>} 响应
   */
  async importTerms(glossaryId, terms) {
    return this.post(`/api/glossaries/${glossaryId}/terms/import`, { terms });
  }

  /**
   * 获取术语列表
   *
   * @param {string} glossaryId - 术语库ID
   * @param {number} page - 页码
   * @param {number} pageSize - 每页数量
   * @returns {Promise<Object>} 术语列表和分页信息
   */
  async getTerms(glossaryId, page = 1, pageSize = 20) {
    return this.get(`/api/glossaries/${glossaryId}/terms?page=${page}&page_size=${pageSize}`);
  }

  // ==================== 统计 API ====================

  /**
   * 获取统计数据
   *
   * @param {Object} params - 查询参数
   * @returns {Promise<Object>} 统计数据
   */
  async getAnalytics(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.get(`/api/analytics?${query}`, true);
  }
}

// 创建全局API实例
const api = new API();

// ES6 模块导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = API;
  module.exports.api = api;
}
