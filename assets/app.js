/**
 * app.js
 * 前端应用主入口
 */
import { checkPendingToast } from './js/utils.js';
import { updateAuthUI, initAuthListeners } from './js/auth.js';
import { initPostListeners } from './js/post.js';
import { initEditor } from './js/editor.js';

document.addEventListener('DOMContentLoaded', () => {
    // 1. 检查并显示挂起的消息
    checkPendingToast();

    // 2. 初始化认证模块
    updateAuthUI();
    initAuthListeners();

    // 3. 初始化文章管理模块
    initPostListeners();

    // 4. 初始化编辑器 (如果存在)
    initEditor();
});