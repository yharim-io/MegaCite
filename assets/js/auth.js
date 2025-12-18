import { showToast } from './utils.js';

// 检查 Token 有效性
export async function checkTokenValidity() {
    const token = localStorage.getItem('mc_token');
    if (!token) return;

    try {
        const res = await fetch('/api/user/info', {
            headers: { 'Authorization': token }
        });
        
        if (res.status === 401 || res.status === 403) {
            console.log("Token expired, clearing session...");
            localStorage.removeItem('mc_token');
            localStorage.removeItem('mc_username');
            document.cookie = "mc_token=; path=/; max-age=0";
            
            localStorage.setItem('mc_pending_toast', '会话已过期，请重新登录');
            location.reload();
        }
    } catch (e) {
        console.error("Token validity check error:", e);
    }
}

let currentSessionId = null;
let authEventSource = null;
let isRegisterMode = false;
let countdownTimer = null;

// ... (window.unbindAuth, window.startAuth, updateBindings, fetchUserProfile 等函数保持不变) ...
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
                showToast('无法连接到本地客户端，请确保客户端正在运行');
                if (authEventSource) authEventSource.close();
            }
        }, 500);
    } catch (e) {
        showToast('错误: ' + e.message);
    }
};

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

async function fetchUserProfile() {
    const userProfile = document.getElementById('user-profile');
    const userProfileLoading = document.getElementById('user-profile-loading');
    const profileUsername = document.getElementById('profile-username');
    const profileEmail = document.getElementById('profile-email');
    const profileDate = document.getElementById('profile-date');
    if (!userProfile) return; 
    if (userProfileLoading) userProfileLoading.style.display = 'block';
    try {
        const res = await fetch('/api/user/info', {
            headers: { 'Authorization': localStorage.getItem('mc_token') }
        });
        if (res.ok) {
            const data = await res.json();
            if (userProfileLoading) userProfileLoading.style.display = 'none';
            if (userProfile) userProfile.style.display = 'block';
            if (profileUsername) profileUsername.textContent = data.username;
            if (profileEmail) profileEmail.textContent = data.email;
            if (profileDate) profileDate.textContent = data.created_at;
        } else {
            if (userProfileLoading) userProfileLoading.textContent = "加载失败";
        }
    } catch (e) {
        if (userProfileLoading) userProfileLoading.textContent = "加载错误";
    }
}

// 更新全局 UI 状态
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
    const publicToggleContainer = document.getElementById('public-toggle-container'); 
    
    const btnGetStarted = document.getElementById('btn-get-started');
    const btnDashboard = document.getElementById('btn-dashboard');

    if (isLoggedIn) {
        if(guestArea) guestArea.style.display = 'none';
        if(userArea) userArea.style.display = 'flex';
        if(usernameDisplay) usernameDisplay.textContent = username;
        if(linkMyHome) linkMyHome.href = `/${username}/index.html`;
        
        // 登录后隐藏 Get Started，显示 Dashboard
        if(btnGetStarted) btnGetStarted.style.display = 'none';
        if(btnDashboard) {
            btnDashboard.style.display = 'inline-block';
            btnDashboard.href = `/${username}/index.html`;
        }
        
        // ... (其他 meta 检查逻辑保持不变)
        const pageOwnerMeta = document.querySelector('meta[name="page-owner"]');
        if (pageOwnerMeta) {
            const pageOwner = pageOwnerMeta.getAttribute('content');
            if (pageOwner === username) {
                if(dashboardActions) dashboardActions.style.display = 'flex';
                document.querySelectorAll('.post-item-controls').forEach(el => {
                    el.style.display = 'flex';
                });
            }
        }

        const postAuthorMeta = document.querySelector('meta[name="post-author"]');
        if (postAuthorMeta) {
            const postAuthor = postAuthorMeta.getAttribute('content');
            if (postAuthor === username) {
                if (btnEditTrigger) btnEditTrigger.style.display = 'inline-flex';
                const btnDeletePage = document.getElementById('btn-delete-current-post');
                if (btnDeletePage) btnDeletePage.style.display = 'inline-flex';
                if (publicToggleContainer) publicToggleContainer.style.display = 'flex';
                
                const cid = document.querySelector('meta[name="post-cid"]').getAttribute('content');
                if (btnEditTrigger) {
                    btnEditTrigger.onclick = () => {
                        window.location.href = `/edit.html?cid=${cid}`;
                    };
                }
            }
        }

        if (document.getElementById('platform-list')) {
            updateBindings();
            fetchUserProfile();
        }
    } else {
        if(guestArea) guestArea.style.display = 'inline-block';
        if(userArea) userArea.style.display = 'none';
        if(dashboardActions) dashboardActions.style.display = 'none';
        
        if(btnGetStarted) btnGetStarted.style.display = 'inline-block';
        // 未登录时隐藏 Dashboard
        if(btnDashboard) btnDashboard.style.display = 'none';
    }
}

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
    const btnGetStarted = document.getElementById('btn-get-started');
    // const btnDashboard = document.getElementById('btn-dashboard'); // 不再需要监听点击，因为未登录不显示

    const rowEmail = document.getElementById('row-email');
    const rowCode = document.getElementById('row-code');
    const inpEmail = document.getElementById('inp-email');
    const inpCode = document.getElementById('inp-code');
    const btnGetCode = document.getElementById('btn-get-code');

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

    const toggleMode = (register) => {
        isRegisterMode = register;
        if (register) {
            tabRegister.classList.add('active'); 
            tabLogin.classList.remove('active'); 
            btnSubmit.textContent = '注册并登录';
            if (rowEmail) rowEmail.style.display = 'block';
            if (rowCode) rowCode.style.display = 'flex';
        } else {
            tabLogin.classList.add('active'); 
            tabRegister.classList.remove('active'); 
            btnSubmit.textContent = '立即登录';
            if (rowEmail) rowEmail.style.display = 'none';
            if (rowCode) rowCode.style.display = 'none';
        }
    };

    if (tabLogin) tabLogin.onclick = () => toggleMode(false);
    if (tabRegister) tabRegister.onclick = () => toggleMode(true);

    const openModal = () => { if(modalOverlay) { modalOverlay.classList.add('open'); inpUser.focus(); } };
    const closeModal = () => { if(modalOverlay) modalOverlay.classList.remove('open'); };
    
    document.querySelectorAll('#btn-login-trigger').forEach(b => b.addEventListener('click', openModal));
    if (btnGetStarted) btnGetStarted.addEventListener('click', openModal);
    
    // Dashboard 按钮不需要专门的监听器，因为未登录不显示，已登录直接是链接跳转

    if (btnCancel) btnCancel.addEventListener('click', closeModal);
    if (modalOverlay) modalOverlay.addEventListener('click', (e) => { if (e.target === modalOverlay) closeModal(); });

    if (btnGetCode) {
        btnGetCode.addEventListener('click', async () => {
            const email = inpEmail.value.trim();
            const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
            if (!email) return showToast('请输入邮箱地址');
            if (!emailRegex.test(email)) return showToast('邮箱格式不正确');
            btnGetCode.disabled = true;
            btnGetCode.textContent = '发送中...';
            try {
                const res = await fetch('/api/auth/send_code', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });
                if (res.ok) {
                    showToast('验证码已发送，请查收邮件');
                    let timeLeft = 60;
                    btnGetCode.textContent = `${timeLeft}s`;
                    countdownTimer = setInterval(() => {
                        timeLeft--;
                        if (timeLeft <= 0) {
                            clearInterval(countdownTimer);
                            btnGetCode.disabled = false;
                            btnGetCode.textContent = '获取验证码';
                        } else {
                            btnGetCode.textContent = `${timeLeft}s`;
                        }
                    }, 1000);
                } else {
                    const data = await res.json();
                    showToast(data.error || '发送失败');
                    btnGetCode.disabled = false;
                    btnGetCode.textContent = '获取验证码';
                }
            } catch (e) {
                showToast('网络错误');
                btnGetCode.disabled = false;
                btnGetCode.textContent = '获取验证码';
            }
        });
    }

    if (btnSubmit) {
        btnSubmit.addEventListener('click', async () => {
            const u = inpUser.value.trim();
            const p = inpPass.value.trim();
            if (!u || !p) return showToast('请输入账号密码');
            try {
                if (isRegisterMode) {
                    const email = inpEmail.value.trim();
                    const code = inpCode.value.trim();
                    if (!email) return showToast('请输入邮箱');
                    if (!code) return showToast('请输入验证码');
                    const res = await fetch('/api/register', { 
                        method: 'POST', 
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username: u, password: p, email: email, code: code }) 
                    });
                    if (!res.ok) {
                        const data = await res.json();
                        throw new Error(data.error || '注册失败');
                    }
                    const data = await res.json();
                    if (data.token) {
                        localStorage.setItem('mc_token', data.token);
                        localStorage.setItem('mc_username', u);
                        document.cookie = `mc_token=${data.token}; path=/; max-age=86400`;
                        closeModal();
                        showToast('注册并登录成功');
                        setTimeout(() => window.location.href = `/${u}/index.html`, 800);
                    }
                } else {
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
                }
            } catch (e) { showToast(e.message); }
        });
    }

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