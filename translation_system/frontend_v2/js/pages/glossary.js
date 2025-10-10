// 术语管理页
class GlossaryPage {
    constructor() {
        this.glossaries = [];
        this.expandedId = null;
    }

    async render() {
        const html = `
            <div class="max-w-6xl mx-auto">
                <!-- 页面标题 -->
                <div class="flex justify-between items-center mb-6">
                    <div>
                        <h1 class="text-3xl font-bold">
                            <i class="bi bi-book"></i>
                            术语管理
                        </h1>
                        <p class="text-base-content/70 mt-1">管理游戏翻译术语表</p>
                    </div>
                    <button class="btn btn-ghost" onclick="router.navigate('/sessions')">
                        <i class="bi bi-arrow-left"></i>
                        返回任务列表
                    </button>
                </div>

                <!-- 上传区域 -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <!-- 下载模板 -->
                    <div class="card bg-base-100 shadow-xl">
                        <div class="card-body">
                            <h3 class="card-title text-lg">
                                <i class="bi bi-download"></i>
                                下载术语模板
                            </h3>
                            <p class="text-sm text-base-content/70">
                                下载标准Excel模板，填充术语后导入
                            </p>
                            <button class="btn btn-outline btn-sm mt-2" onclick="glossaryPage.downloadTemplate()">
                                <i class="bi bi-file-earmark-excel"></i>
                                下载Excel模板
                            </button>
                        </div>
                    </div>

                    <!-- 导入术语表 -->
                    <div class="card bg-base-100 shadow-xl">
                        <div class="card-body">
                            <h3 class="card-title text-lg">
                                <i class="bi bi-upload"></i>
                                导入术语表
                            </h3>
                            <div id="dropZone"
                                 class="border-2 border-dashed border-base-300 rounded-lg p-6 text-center hover:border-primary hover:bg-base-200 cursor-pointer transition-all"
                                 onclick="document.getElementById('glossaryFile').click()"
                                 ondrop="glossaryPage.handleDrop(event)"
                                 ondragover="event.preventDefault()"
                                 ondragleave="event.target.classList.remove('border-primary', 'bg-base-200')">
                                <i class="bi bi-cloud-upload text-4xl text-base-content/30"></i>
                                <p class="mt-2 text-sm">点击或拖拽Excel文件到这里</p>
                                <p class="text-xs text-base-content/50 mt-1">支持 .xlsx 格式</p>
                            </div>
                            <input type="file" id="glossaryFile" accept=".xlsx,.xls"
                                   class="hidden" onchange="glossaryPage.handleFileSelect(event)">
                        </div>
                    </div>
                </div>

                <!-- 术语表列表 -->
                <div class="mb-4">
                    <h2 class="text-2xl font-bold mb-4">
                        已有术语表 (<span id="glossaryCount">0</span>个)
                    </h2>
                </div>

                <div id="glossariesList" class="space-y-4">
                    <div class="text-center py-12">
                        <span class="loading loading-spinner loading-lg"></span>
                        <p class="mt-4 text-base-content/70">加载中...</p>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('pageContent').innerHTML = html;
        await this.loadGlossaries();
    }

    async loadGlossaries() {
        try {
            const response = await fetch(`${APP_CONFIG.API_BASE_URL}/api/glossaries/list`, {
                headers: { 'Authorization': `Bearer ${authManager.getToken()}` }
            });

            if (!response.ok) throw new Error('Failed to load glossaries');

            const data = await response.json();
            this.glossaries = data.glossaries || [];

            document.getElementById('glossaryCount').textContent = this.glossaries.length;
            this.displayGlossaries();

        } catch (error) {
            logger.error('Failed to load glossaries:', error);
            UIHelper.showToast('加载术语表失败', 'error');
            this.displayError();
        }
    }

    displayGlossaries() {
        const container = document.getElementById('glossariesList');

        if (this.glossaries.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12">
                    <i class="bi bi-inbox text-6xl text-base-content/30"></i>
                    <p class="mt-4 text-base-content/70">暂无术语表</p>
                    <p class="text-sm text-base-content/50 mt-2">点击上方导入术语表或下载模板开始</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.glossaries.map(g => this.renderGlossaryCard(g)).join('');
    }

    renderGlossaryCard(glossary) {
        const isExpanded = this.expandedId === glossary.id;
        const isDefault = glossary.id === 'default';

        return `
            <div class="card bg-base-100 shadow-xl ${isDefault ? 'border-2 border-primary' : ''}">
                <div class="card-body">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <h3 class="card-title">
                                ${glossary.name}
                                ${isDefault ? '<span class="badge badge-primary badge-sm">默认</span>' : ''}
                            </h3>
                            <p class="text-sm text-base-content/70 mt-1">
                                <i class="bi bi-tag"></i> ${glossary.term_count} 条术语
                                • ${glossary.languages.join(', ')}
                                ${glossary.version ? `• v${glossary.version}` : ''}
                            </p>
                            ${glossary.description ? `
                                <p class="text-xs text-base-content/50 mt-1">${glossary.description}</p>
                            ` : ''}
                        </div>
                        <div class="dropdown dropdown-end">
                            <label tabindex="0" class="btn btn-ghost btn-sm btn-circle">
                                <i class="bi bi-three-dots-vertical"></i>
                            </label>
                            <ul tabindex="0" class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52">
                                <li><a onclick="glossaryPage.viewDetails('${glossary.id}')">
                                    <i class="bi bi-eye"></i> 查看详情
                                </a></li>
                                <li><a onclick="glossaryPage.downloadGlossary('${glossary.id}')">
                                    <i class="bi bi-download"></i> 下载Excel
                                </a></li>
                                ${!isDefault ? `
                                    <li><a onclick="glossaryPage.deleteGlossary('${glossary.id}')" class="text-error">
                                        <i class="bi bi-trash"></i> 删除
                                    </a></li>
                                ` : ''}
                            </ul>
                        </div>
                    </div>

                    <!-- 快速预览前5个术语 -->
                    <div class="mt-3 flex flex-wrap gap-2" id="preview_${glossary.id}">
                        <span class="loading loading-dots loading-xs"></span>
                    </div>

                    <!-- 展开详情区域 -->
                    <div id="detail_${glossary.id}" class="hidden mt-4">
                        <div class="divider"></div>
                        <div class="max-h-96 overflow-y-auto">
                            <div class="space-y-2" id="terms_${glossary.id}">
                                <span class="loading loading-spinner loading-sm"></span> 加载中...
                            </div>
                        </div>
                    </div>

                    <div class="card-actions justify-end mt-4">
                        <button class="btn btn-sm btn-ghost" onclick="glossaryPage.toggleExpand('${glossary.id}')">
                            <i class="bi bi-chevron-${isExpanded ? 'up' : 'down'}"></i>
                            ${isExpanded ? '收起' : '查看全部'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    async viewDetails(glossaryId) {
        // 加载术语详情
        try {
            const response = await fetch(
                `${APP_CONFIG.API_BASE_URL}/api/glossaries/${glossaryId}`,
                { headers: { 'Authorization': `Bearer ${authManager.getToken()}` } }
            );

            if (!response.ok) throw new Error('Failed to load glossary');

            const glossary = await response.json();

            // 显示预览（前5个术语）
            const previewContainer = document.getElementById(`preview_${glossaryId}`);
            if (previewContainer && glossary.terms) {
                const preview = glossary.terms.slice(0, 5).map(term =>
                    `<span class="badge badge-outline">${term.source}</span>`
                ).join('');
                previewContainer.innerHTML = preview +
                    (glossary.terms.length > 5 ? ` <span class="text-xs text-base-content/50">+${glossary.terms.length - 5}条</span>` : '');
            }

        } catch (error) {
            logger.error('Failed to load glossary details:', error);
        }
    }

    async toggleExpand(glossaryId) {
        const detailDiv = document.getElementById(`detail_${glossaryId}`);
        const wasExpanded = !detailDiv.classList.contains('hidden');

        if (wasExpanded) {
            // 收起
            detailDiv.classList.add('hidden');
            this.expandedId = null;
        } else {
            // 展开
            detailDiv.classList.remove('hidden');
            this.expandedId = glossaryId;

            // 加载完整术语列表
            await this.loadTermsDetail(glossaryId);
        }

        // 重新渲染（更新按钮）
        await this.loadGlossaries();
    }

    async loadTermsDetail(glossaryId) {
        try {
            const response = await fetch(
                `${APP_CONFIG.API_BASE_URL}/api/glossaries/${glossaryId}`,
                { headers: { 'Authorization': `Bearer ${authManager.getToken()}` } }
            );

            if (!response.ok) throw new Error('Failed to load terms');

            const glossary = await response.json();
            const termsContainer = document.getElementById(`terms_${glossaryId}`);

            if (termsContainer && glossary.terms) {
                termsContainer.innerHTML = glossary.terms.map(term => `
                    <div class="alert">
                        <div class="flex-1">
                            <div class="font-bold">${term.source}</div>
                            <div class="text-sm mt-1 flex flex-wrap gap-2">
                                ${Object.entries(term.translations || {}).map(([lang, trans]) =>
                                    `<span class="badge badge-sm">${lang}: ${trans}</span>`
                                ).join('')}
                            </div>
                            ${term.category ? `<div class="text-xs text-base-content/50 mt-1">分类: ${term.category}</div>` : ''}
                        </div>
                    </div>
                `).join('');
            }

        } catch (error) {
            logger.error('Failed to load terms detail:', error);
            const termsContainer = document.getElementById(`terms_${glossaryId}`);
            if (termsContainer) {
                termsContainer.innerHTML = '<div class="text-error">加载失败</div>';
            }
        }
    }

    handleDrop(event) {
        event.preventDefault();
        event.stopPropagation();
        event.target.classList.remove('border-primary', 'bg-base-200');

        const files = event.dataTransfer.files;
        if (files.length > 0) {
            this.uploadFile(files[0]);
        }
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.uploadFile(file);
        }
    }

    async uploadFile(file) {
        // 验证文件类型
        if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
            UIHelper.showToast('请上传Excel文件(.xlsx)', 'error');
            return;
        }

        try {
            UIHelper.showLoading(true);

            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(
                `${APP_CONFIG.API_BASE_URL}/api/glossaries/upload`,
                {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${authManager.getToken()}` },
                    body: formData
                }
            );

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '上传失败');
            }

            const result = await response.json();

            UIHelper.showToast(
                `✅ 导入成功！${result.term_count}条术语`,
                'success'
            );

            // 重新加载列表
            await this.loadGlossaries();

        } catch (error) {
            logger.error('Upload failed:', error);
            UIHelper.showToast(`导入失败：${error.message}`, 'error');
        } finally {
            UIHelper.showLoading(false);
            // 清空文件选择
            document.getElementById('glossaryFile').value = '';
        }
    }

    downloadTemplate() {
        // 创建模板数据
        const template = [
            ['术语', 'EN', 'TH', 'PT', 'VN', '分类', '优先级', '备注'],
            ['攻击力', 'ATK', 'พลังโจมตี', 'Ataque', 'Sức công', '属性', '10', '基础属性'],
            ['生命值', 'HP', 'พลังชีวิต', 'Vida', 'Sinh lực', '属性', '10', '基础属性'],
            ['防御力', 'DEF', 'พลังป้องกัน', 'Defesa', 'Phòng thủ', '属性', '10', '基础属性'],
            ['技能', 'Skill', 'ทักษะ', 'Habilidade', 'Kỹ năng', '战斗', '9', ''],
            ['装备', 'Equipment', 'อุปกรณ์', 'Equipamento', 'Trang bị', '道具', '9', '']
        ];

        // 转换为CSV（简单实现）
        const csv = template.map(row => row.join('\t')).join('\n');
        const blob = new Blob(['\ufeff' + csv], { type: 'text/tab-separated-values;charset=utf-8;' });

        // 下载
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = '术语表模板.xlsx';
        link.click();

        UIHelper.showToast('模板已下载，用Excel打开编辑后上传', 'success');
    }

    async downloadGlossary(glossaryId) {
        try {
            UIHelper.showLoading(true);

            const response = await fetch(
                `${APP_CONFIG.API_BASE_URL}/api/glossaries/${glossaryId}`,
                { headers: { 'Authorization': `Bearer ${authManager.getToken()}` } }
            );

            if (!response.ok) throw new Error('Failed to download');

            const glossary = await response.json();

            // 转换为Excel格式
            const rows = [
                ['术语', 'EN', 'TH', 'PT', 'VN', '分类', '优先级']
            ];

            glossary.terms.forEach(term => {
                rows.push([
                    term.source,
                    term.translations.EN || '',
                    term.translations.TH || '',
                    term.translations.PT || '',
                    term.translations.VN || '',
                    term.category || '',
                    term.priority || '5'
                ]);
            });

            // 转换为TSV
            const tsv = rows.map(row => row.join('\t')).join('\n');
            const blob = new Blob(['\ufeff' + tsv], { type: 'text/tab-separated-values;charset=utf-8;' });

            // 下载
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `${glossary.name}.xlsx`;
            link.click();

            UIHelper.showToast('术语表已下载', 'success');

        } catch (error) {
            logger.error('Download failed:', error);
            UIHelper.showToast('下载失败', 'error');
        } finally {
            UIHelper.showLoading(false);
        }
    }

    async deleteGlossary(glossaryId) {
        const glossary = this.glossaries.find(g => g.id === glossaryId);
        if (!glossary) return;

        const confirmed = confirm(`确定要删除"${glossary.name}"吗？\n此操作无法撤销。`);
        if (!confirmed) return;

        try {
            UIHelper.showLoading(true);

            // 使用session delete API的模式（后端需要添加glossary delete）
            const response = await fetch(
                `${APP_CONFIG.API_BASE_URL}/api/glossaries/${glossaryId}`,
                {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${authManager.getToken()}` }
                }
            );

            if (!response.ok) throw new Error('Delete failed');

            UIHelper.showToast('术语表已删除', 'success');
            await this.loadGlossaries();

        } catch (error) {
            logger.error('Delete failed:', error);
            UIHelper.showToast('删除失败，请刷新后重试', 'error');
        } finally {
            UIHelper.showLoading(false);
        }
    }

    displayError() {
        const container = document.getElementById('glossariesList');
        container.innerHTML = `
            <div class="alert alert-error">
                <i class="bi bi-exclamation-triangle-fill"></i>
                <div>
                    <h3 class="font-bold">加载失败</h3>
                    <p>无法获取术语表列表</p>
                </div>
                <button class="btn btn-sm" onclick="glossaryPage.loadGlossaries()">重试</button>
            </div>
        `;
    }

    cleanup() {
        // 页面清理
    }
}

// 创建页面实例
const glossaryPage = new GlossaryPage();
