/**
 * auth.js
 * 认证与用户状态管理模块
 */
import { showToast } from './utils.js';

let currentSessionId = null;
let authEventSource = null;
let isRegisterMode = false;

// 更新全局 UI 状态 (登录/未登录视图切换)
export function updateAuthUI() {
    const token = localStorage.getItem('mc_token');
    const username = localStorage.getItem('mc_username');
    const isLoggedIn = token && username;
    
    const guestArea = document.getElementById('auth-guest');
    const userArea = document.getElementById('auth-user');
    const usernameDisplay = document.getElementById('username-display');
    const linkMyHome = document.getElementById('link-my-home');
    const dashboardActions = document.getElementById('dashboard-actions');
    const btnEditTrigger = document.getElementById('btn-edit-trigger');
    
    // [新增] 首页 Get Started 按钮控制
    const landingAction = document.getElementById('landing-action');

    if (isLoggedIn) {
        if(guestArea) guestArea.style.display = 'none';
        if(userArea) userArea.style.display = 'flex';
        if(usernameDisplay) usernameDisplay.textContent = username;
        if(linkMyHome) linkMyHome.href = `/${username}/index.html`;
        
        // 如果已登录，隐藏首页的 Get Started 按钮
        if(landingAction) landingAction.style.display = 'none';
        
        // 1. 首页控制台逻辑
        const pageOwnerMeta = document.querySelector('meta[name="page-owner"]');
        if (pageOwnerMeta && dashboardActions) {
            const pageOwner = pageOwnerMeta.getAttribute('content');
            if (pageOwner === username) {
                dashboardActions.style.display = 'flex';
                document.querySelectorAll('.btn-delete-post').forEach(btn => {
                    btn.style.display = 'block';
                });
            }
        }

        // 2. 文章页编辑按钮逻辑
        const postAuthorMeta = document.querySelector('meta[name="post-author"]');
        if (postAuthorMeta && btnEditTrigger) {
            const postAuthor = postAuthorMeta.getAttribute('content');
            if (postAuthor === username) {
                btnEditTrigger.style.display = 'inline-flex';
                const cid = document.querySelector('meta[name="post-cid"]').getAttribute('content');
                btnEditTrigger.onclick = () => {
                    window.location.href = `/edit.html?cid=${cid}`;
                };
            }
        }

        // 如果在设置页，更新绑定列表
        if (document.getElementById('platform-list')) {
            updateBindings();
        }
    } else {
        if(guestArea) guestArea.style.display = 'inline-block';
        if(userArea) userArea.style.display = 'none';
        if(dashboardActions) dashboardActions.style.display = 'none';
        
        // 如果未登录，显示首页的 Get Started 按钮
        if(landingAction) landingAction.style.display = 'block';
    }
}

// 初始化认证相关的事件监听
export function initAuthListeners() {
    const btnLogout = document.getElementById('btn-logout');
    const modalOverlay = document.getElementById('login-modal');
    const btnCancel = document.getElementById('btn-cancel-login');
    const btnSubmit = document.getElementById('btn-submit-auth');
    const inpUser = document.getElementById('inp-username');
    const inpPass = document.getElementById('inp-password');
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const settingsForm = document.getElementById('settings-form');
    
    // [新增] Get Started 按钮
    const btnGetStarted = document.getElementById('btn-get-started');

    // 密码可见性切换
    const iconEye = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>';
    const iconEyeOff = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>';

    document.querySelectorAll('.password-toggle').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const input = toggle.previousElementSibling;
            if (!input) return;
            if (input.type === 'password') {
                input.type = 'text';
                toggle.innerHTML = iconEye;
            } else {
                input.type = 'password';
                toggle.innerHTML = iconEyeOff;
            }
        });
    });

    if (inpPass) {
        inpPass.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                btnSubmit.click();
            }
        });
    }

    // 登出逻辑
    if (btnLogout) {
        btnLogout.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('mc_token');
            localStorage.removeItem('mc_username');
            document.cookie = "mc_token=; path=/; max-age=0";
            
            if (window.location.pathname.includes('settings') || window.location.pathname.includes('edit')) {
                window.location.href = '/';
            } else {
                location.reload();
            }
        });
    }

    // 模态框逻辑
    const openModal = () => { if(modalOverlay) { modalOverlay.classList.add('open'); inpUser.focus(); } };
    const closeModal = () => { if(modalOverlay) modalOverlay.classList.remove('open'); };
    
    document.querySelectorAll('#btn-login-trigger').forEach(b => b.addEventListener('click', openModal));
    
    // [新增] 绑定 Get Started 按钮点击事件
    if (btnGetStarted) {
        btnGetStarted.addEventListener('click', openModal);
    }

    if (btnCancel) btnCancel.addEventListener('click', closeModal);
    if (modalOverlay) modalOverlay.addEventListener('click', (e) => { if (e.target === modalOverlay) closeModal(); });

    // 登录/注册提交
    if (btnSubmit) {
        btnSubmit.addEventListener('click', async () => {
            const u = inpUser.value.trim(), p = inpPass.value.trim();
            if (!u || !p) return showToast('请输入账号密码');
            
            try {
                if (isRegisterMode) {
                    await fetch('/api/register', { 
                        method: 'POST', 
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({username:u, password:p}) 
                    });
                }
                const res = await fetch('/api/login', { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({username:u, password:p}) 
                });
                if (res.ok) {
                    const data = await res.json();
                    localStorage.setItem('mc_token', data.token);
                    localStorage.setItem('mc_username', u);
                    document.cookie = `mc_token=${data.token}; path=/; max-age=86400`;
                    
                    closeModal();
                    showToast('登录成功');
                    setTimeout(() => window.location.href = `/${u}/index.html`, 800);
                } else throw new Error('登录失败');
            } catch (e) { showToast(e.message); }
        });
    }

    if (tabLogin) {
        tabLogin.onclick = () => { isRegisterMode = false; tabLogin.classList.add('active'); tabRegister.classList.remove('active'); btnSubmit.textContent = '立即登录'; };
        tabRegister.onclick = () => { isRegisterMode = true; tabRegister.classList.add('active'); tabLogin.classList.remove('active'); btnSubmit.textContent = '注册并登录'; };
    }

    // 修改密码表单
    if (settingsForm) {
        settingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const inpOldPass = document.getElementById('inp-old-pass');
            const inpNewPass = document.getElementById('inp-new-pass');
            try {
                const res = await fetch('/api/change_password', {
                    method: 'POST',
                    headers: { 
                        'Authorization': localStorage.getItem('mc_token'),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        old_password: inpOldPass.value, 
                        new_password: inpNewPass.value 
                    })
                });
                if (res.ok) { 
                    showToast('密码修改成功'); 
                    inpOldPass.value=''; 
                    inpNewPass.value=''; 
                } else {
                    const errData = await res.json();
                    showToast(errData.error || '修改失败');
                }
            } catch (e) { showToast('网络错误: ' + e.message); }
        });
    }
}

// 获取并更新绑定状态
async function updateBindings() {
    try {
        const res = await fetch('/api/auth/bindings', {
            headers: { 'Authorization': localStorage.getItem('mc_token') }
        });
        const data = await res.json();
        const boundPlatforms = new Set(data.bindings || []);

        document.querySelectorAll('.btn-bind').forEach(btn => {
            const platform = btn.dataset.platform;
            if (!platform) return;
            btn.classList.remove('status-loading', 'status-bound', 'status-unbound');
            
            if (boundPlatforms.has(platform)) {
                btn.textContent = '更新'; 
                btn.classList.add('status-bound'); 
            } else {
                btn.textContent = '绑定'; 
                btn.classList.add('status-unbound'); 
            }
            btn.disabled = false;
        });

        document.querySelectorAll('.btn-unbind').forEach(btn => {
            const platform = btn.dataset.platform;
            if (boundPlatforms.has(platform)) {
                btn.style.display = 'inline-block';
            } else {
                btn.style.display = 'none';
            }
        });
    } catch (e) {
        console.error("Failed to fetch bindings", e);
    }
}

// 暴露给全局的绑定操作 (因为 HTML onclick 属性调用)
window.unbindAuth = async (platform) => {
    if (!confirm(`确定要解除 ${platform} 的绑定吗？这意味着您将无法自动同步该平台的文章。`)) return;

    try {
        const res = await fetch('/api/auth/unbind', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': localStorage.getItem('mc_token')
            },
            body: JSON.stringify({ platform })
        });
        
        if (res.ok) {
            showToast('已解除绑定');
            updateBindings();
        } else {
            showToast('解绑失败');
        }
    } catch (e) {
        showToast('网络错误');
    }
};

window.startAuth = async (platform) => {
    try {
        const token = localStorage.getItem('mc_token');
        const initRes = await fetch('/api/auth/init', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': token 
            },
            body: JSON.stringify({ platform })
        });
        
        if (!initRes.ok) throw new Error('启动失败');

        const initData = await initRes.json();
        currentSessionId = initData.session_id;
        
        showToast('正在启动验证客户端...');
        
        if (authEventSource) authEventSource.close();
        
        authEventSource = new EventSource(`/api/auth/watch?session_id=${currentSessionId}`);
        
        authEventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.status === 'authenticated') {
                authEventSource.close();
                authEventSource = null;
                localStorage.setItem('mc_pending_toast', '绑定成功！');
                location.reload();
            } else if (data.status === 'failed') {
                authEventSource.close();
                authEventSource = null;
                showToast('绑定失败: ' + (data.error || '未知错误'));
            }
        };

        const clientUrl = 'http://127.0.0.1:9999/verify';
        
        setTimeout(async () => {
            try {
                await fetch(clientUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: currentSessionId,
                        platform: platform,
                        server_url: window.location.origin
                    })
                });
                showToast('验证客户端已启动，请在浏览器中完成登录');
            } catch (e) {
                showToast('无法连接到本地客户端，请确保客户端正在运行\n' + 
                          '启动方式: python client/verifier.py --server ' + window.location.origin);
                if (authEventSource) authEventSource.close();
            }
        }, 500);

    } catch (e) {
        showToast('错误: ' + e.message);
    }
};