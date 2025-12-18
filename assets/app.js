/**
 * app.js
 * 前端应用主入口
 */
import { checkPendingToast } from './js/utils.js';
import { updateAuthUI, initAuthListeners, checkTokenValidity } from './js/auth.js';
import { initPostListeners } from './js/post.js';
import { initEditor } from './js/editor.js';

document.addEventListener('DOMContentLoaded', () => {
    // 1. 检查并显示挂起的消息
    checkPendingToast();

    // 2. 检查用户 Token 是否有效 (异步执行，不阻塞 UI 初始化)
    // 只有已登录用户才会发起请求，若 Token 失效则会自动刷新页面
    checkTokenValidity();

    // 3. 初始化认证模块 (立即执行，确保按钮可点击)
    updateAuthUI();
    initAuthListeners();

    // 4. 初始化文章管理模块
    initPostListeners();

    // 5. 初始化编辑器 (如果存在)
    initEditor();
});