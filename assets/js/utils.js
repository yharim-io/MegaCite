/**
 * utils.js
 * 通用工具函数模块
 */

// 显示 Toast 提示
export function showToast(message) {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 检查并显示挂起的 Toast (用于跨页面刷新后的提示)
export function checkPendingToast() {
    const pendingToast = localStorage.getItem('mc_pending_toast');
    if (pendingToast) {
        showToast(pendingToast);
        localStorage.removeItem('mc_pending_toast');
    }
}