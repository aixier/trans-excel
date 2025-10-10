// 术语管理页
class GlossaryPage {
    constructor() {
        this.glossaries = [];
        this.expandedId = null;
    }

    async render() {
        // 更新面包屑
        updateBreadcrumb(['首页', '资源管理', '术语管理']);

        const html = `
            <div class="h-full">
                <!-- 页面标题 -->
                <div class="mb-6">
                    <h1 class="text-2xl font-bold">术语管理</h1>
                    <p class="text-sm text-base-content/70 mt-1">管理游戏翻译术语表，保证术语一致性</p>
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
                <div class="card bg-base-100 shadow-xl">
                    <div class="card-body">
                        <div class="flex justify-between items-center mb-4">
                            <h2 class="card-title">术语表列表</h2>
                            <div class="text-sm text-base-content/70">
                                共 <span id="glossaryCount" class="font-bold text-primary">0</span> 个术语表
                            </div>
                        </div>

                        <!-- 表格 -->
                        <div class="overflow-x-auto">
                            <table class="table table-zebra table-sm">
                                <thead>
                                    <tr>
                                        <th>术语表名称</th>
                                        <th>术语数量</th>
                                        <th>支持语言</th>
                                        <th>版本</th>
                                        <th>描述</th>
                                        <th class="text-center">操作</th>
                                    </tr>
                                </thead>
                                <tbody id="glossariesTable">
                                    <tr>
                                        <td colspan="6" class="text-center py-8">
                                            <span class="loading loading-spinner loading-lg"></span>
                                            <p class="mt-2 text-base-content/70">加载中...</p>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
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
        const tbody = document.getElementById('glossariesTable');

        if (this.glossaries.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-12">
                        <i class="bi bi-inbox text-4xl text-base-content/30"></i>
                        <p class="mt-2 text-base-content/70">暂无术语表</p>
                        <p class="text-xs text-base-content/50 mt-1">点击上方导入术语表或下载模板开始</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.glossaries.map(g => this.renderGlossaryRow(g)).join('');
    }

    renderGlossaryRow(glossary) {
        const isDefault = glossary.id === 'default';
        const uploadDate = new Date().toLocaleDateString('zh-CN'); // TODO: 从metadata获取实际日期

        return `
            <tr class="hover">
                <td>
                    <div class="flex items-center gap-2">
                        <i class="bi bi-book text-primary"></i>
                        <span class="font-semibold">${glossary.name}</span>
                        ${isDefault ? '<span class="badge badge-primary badge-xs">默认</span>' : ''}
                    </div>
                </td>
                <td>
                    <span class="badge badge-ghost">${glossary.term_count} 条</span>
                </td>
                <td>
                    <div class="flex gap-1">
                        ${glossary.languages.map(lang =>
                            `<span class="badge badge-outline badge-xs">${lang}</span>`
                        ).join('')}
                    </div>
                </td>
                <td>
                    <span class="text-sm">${glossary.version || '1.0'}</span>
                </td>
                <td>
                    <span class="text-sm text-base-content/70">${glossary.description || '-'}</span>
                </td>
                <td class="text-center">
                    <div class="flex gap-1 justify-center">
                        <button class="btn btn-ghost btn-xs" onclick="glossaryPage.viewGlossary('${glossary.id}')" title="查看详情">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-ghost btn-xs" onclick="glossaryPage.downloadGlossary('${glossary.id}')" title="下载">
                            <i class="bi bi-download"></i>
                        </button>
                        ${!isDefault ? `
                            <button class="btn btn-ghost btn-xs text-error" onclick="glossaryPage.deleteGlossary('${glossary.id}')" title="删除">
                                <i class="bi bi-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    }

    async viewGlossary(glossaryId) {
        // 打开模态框显示术语详情
        try {
            UIHelper.showLoading(true);

            const response = await fetch(
                `${APP_CONFIG.API_BASE_URL}/api/glossaries/${glossaryId}`,
                { headers: { 'Authorization': `Bearer ${authManager.getToken()}` } }
            );

            if (!response.ok) throw new Error('Failed to load glossary');

            const glossary = await response.json();

            // 显示模态框
            this.showGlossaryModal(glossary);

        } catch (error) {
            logger.error('Failed to load glossary:', error);
            UIHelper.showToast('加载失败', 'error');
        } finally {
            UIHelper.showLoading(false);
        }
    }

    showGlossaryModal(glossary) {
        const modal = document.createElement('div');
        modal.className = 'modal modal-open';
        modal.innerHTML = `
            <div class="modal-box max-w-4xl">
                <h3 class="font-bold text-lg mb-4">
                    ${glossary.name}
                    <span class="badge badge-ghost ml-2">${glossary.terms?.length || 0}条术语</span>
                </h3>

                <!-- 搜索框 -->
                <div class="form-control mb-4">
                    <input type="text" placeholder="搜索术语..." class="input input-bordered input-sm"
                           oninput="this.nextElementSibling.querySelectorAll('tr').forEach(tr => {
                               tr.style.display = tr.textContent.toLowerCase().includes(this.value.toLowerCase()) ? '' : 'none';
                           })">
                </div>

                <!-- 术语表格 -->
                <div class="overflow-x-auto max-h-96">
                    <table class="table table-zebra table-xs">
                        <thead class="sticky top-0 bg-base-100">
                            <tr>
                                <th>术语</th>
                                <th>EN</th>
                                <th>TH</th>
                                <th>PT</th>
                                <th>VN</th>
                                <th>分类</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${glossary.terms?.map(term => `
                                <tr>
                                    <td class="font-semibold">${term.source}</td>
                                    <td>${term.translations?.EN || '-'}</td>
                                    <td>${term.translations?.TH || '-'}</td>
                                    <td>${term.translations?.PT || '-'}</td>
                                    <td>${term.translations?.VN || '-'}</td>
                                    <td><span class="badge badge-sm">${term.category || '-'}</span></td>
                                </tr>
                            `).join('') || '<tr><td colspan="6" class="text-center">无数据</td></tr>'}
                        </tbody>
                    </table>
                </div>

                <div class="modal-action">
                    <button class="btn btn-sm" onclick="this.closest('.modal').remove()">关闭</button>
                    <button class="btn btn-sm btn-primary" onclick="glossaryPage.downloadGlossary('${glossary.id}'); this.closest('.modal').remove()">
                        <i class="bi bi-download"></i> 下载Excel
                    </button>
                </div>
            </div>
            <div class="modal-backdrop" onclick="this.parentElement.remove()"></div>
        `;

        document.body.appendChild(modal);
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
        const tbody = document.getElementById('glossariesTable');
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-8">
                    <div class="alert alert-error inline-flex">
                        <i class="bi bi-exclamation-triangle-fill"></i>
                        <span>加载失败</span>
                        <button class="btn btn-xs" onclick="glossaryPage.loadGlossaries()">重试</button>
                    </div>
                </td>
            </tr>
        `;
    }

    cleanup() {
        // 页面清理
    }
}

// 创建页面实例
const glossaryPage = new GlossaryPage();
