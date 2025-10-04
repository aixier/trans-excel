// UI辅助工具类
class UIHelper {
    // 显示Toast提示
    static showToast(message, type = 'info', duration = APP_CONFIG.UI.TOAST_DURATION) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const alertTypes = {
            success: 'alert-success',
            error: 'alert-error',
            warning: 'alert-warning',
            info: 'alert-info'
        };

        const icons = {
            success: 'bi-check-circle-fill',
            error: 'bi-x-circle-fill',
            warning: 'bi-exclamation-triangle-fill',
            info: 'bi-info-circle-fill'
        };

        const alert = document.createElement('div');
        alert.className = `alert ${alertTypes[type]} shadow-lg`;
        alert.innerHTML = `
            <i class="bi ${icons[type]}"></i>
            <span>${message}</span>
        `;

        container.appendChild(alert);

        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                container.removeChild(alert);
            }, 300);
        }, duration);
    }

    // 显示对话框
    static showDialog(options) {
        const {
            type = 'info',
            title,
            message,
            details,
            blocking = false,
            actions = []
        } = options;

        // 创建模态框
        const modal = document.createElement('dialog');
        modal.className = 'modal modal-open';
        modal.innerHTML = `
            <div class="modal-box">
                <h3 class="font-bold text-lg">
                    ${this.getDialogIcon(type)} ${title}
                </h3>
                <p class="py-4">${message}</p>
                ${details ? `<div class="text-sm opacity-70">${details}</div>` : ''}
                <div class="modal-action">
                    ${actions.map(action => `
                        <button class="btn ${action.className || 'btn-primary'}"
                                data-action="${action.label}">
                            ${action.label}
                        </button>
                    `).join('')}
                    ${!blocking ? '<button class="btn" data-action="close">关闭</button>' : ''}
                </div>
            </div>
            ${!blocking ? '<form method="dialog" class="modal-backdrop"><button>关闭</button></form>' : ''}
        `;

        document.body.appendChild(modal);

        // 绑定按钮事件
        modal.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', () => {
                const actionLabel = btn.dataset.action;
                const action = actions.find(a => a.label === actionLabel);

                if (action && action.action) {
                    action.action();
                }

                if (!blocking || actionLabel !== 'close') {
                    document.body.removeChild(modal);
                }
            });
        });

        // 点击背景关闭
        if (!blocking) {
            modal.querySelector('.modal-backdrop').addEventListener('click', () => {
                document.body.removeChild(modal);
            });
        }
    }

    static getDialogIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || '';
    }

    // 显示Loading
    static showLoading(show = true) {
        const loading = document.getElementById('globalLoading');
        if (loading) {
            if (show) {
                loading.classList.remove('hidden');
            } else {
                loading.classList.add('hidden');
            }
        }
    }

    // 更新进度条
    static updateProgress(progressId, value, max = 100) {
        const progressBar = document.getElementById(progressId);
        if (progressBar) {
            const percentage = (value / max) * 100;
            progressBar.style.width = `${percentage}%`;
            progressBar.setAttribute('aria-valuenow', value);
            progressBar.setAttribute('aria-valuemax', max);

            // 更新百分比文本
            const progressText = progressBar.querySelector('.progress-text');
            if (progressText) {
                progressText.textContent = `${Math.round(percentage)}%`;
            }
        }
    }

    // 更新全局进度指示器
    static updateGlobalProgress(currentStep) {
        const steps = document.querySelectorAll('#globalProgress .step');
        steps.forEach((step, index) => {
            const stepNum = parseInt(step.dataset.step);

            if (stepNum < currentStep) {
                step.classList.add('step-primary');
            } else if (stepNum === currentStep) {
                step.classList.add('step-primary');
            } else {
                step.classList.remove('step-primary');
            }
        });

        // 显示进度指示器
        const progressContainer = document.getElementById('globalProgress');
        if (progressContainer) {
            progressContainer.classList.remove('hidden');
        }
    }

    // 创建文件选择器
    static createFileInput(accept, onChange) {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = accept;
        input.style.display = 'none';

        input.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                onChange(e.target.files[0]);
            }
        });

        document.body.appendChild(input);
        input.click();
        document.body.removeChild(input);
    }

    // 下载文件
    static downloadFile(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    }

    // 格式化文件大小
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    // 格式化时间
    static formatTime(seconds) {
        if (seconds < 60) {
            return `${seconds}秒`;
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            return `${minutes}分${remainingSeconds}秒`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}小时${minutes}分`;
        }
    }

    // 防抖函数
    static debounce(func, delay) {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }

    // 节流函数
    static throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // 切换主题
    static toggleTheme() {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        html.setAttribute('data-theme', newTheme);

        const preferences = Storage.getPreferences();
        preferences.theme = newTheme;
        Storage.savePreferences(preferences);
    }

    // 初始化主题
    static initTheme() {
        const preferences = Storage.getPreferences();
        document.documentElement.setAttribute('data-theme', preferences.theme);

        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.checked = preferences.theme === 'dark';
            themeToggle.addEventListener('change', () => this.toggleTheme());
        }
    }
}