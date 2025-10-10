// 布局控制工具

// 切换侧边栏（移动端）
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');
}

// 更新面包屑
function updateBreadcrumb(items) {
    const breadcrumb = document.getElementById('breadcrumb');
    if (!breadcrumb) return;

    const ul = breadcrumb.querySelector('ul');
    if (!ul) return;

    ul.innerHTML = items.map(item => `<li>${item}</li>`).join('');
}

// 更新菜单激活状态
function updateActiveMenu() {
    const hash = window.location.hash.slice(1) || '/sessions';
    const menuLinks = document.querySelectorAll('#sidebar .menu a');

    menuLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href.includes(hash.split('/')[1] || 'sessions')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// 监听路由变化更新菜单
window.addEventListener('hashchange', () => {
    updateActiveMenu();

    // 移动端自动关闭侧边栏
    if (window.innerWidth < 1024) {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        sidebar?.classList.remove('active');
        overlay?.classList.remove('active');
    }
});

// 页面加载时初始化
window.addEventListener('load', () => {
    updateActiveMenu();
});
