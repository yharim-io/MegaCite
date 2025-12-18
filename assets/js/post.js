/**
 * post.js
 * 文章管理模块 (创建, 删除, 迁移)
 */
import { showToast } from './utils.js';

let migrateAbortController = null;
let deleteTargetCid = null;

export function initPostListeners() {
    const btnCreatePost = document.getElementById('btn-create-post');
    const btnMigrateTrigger = document.getElementById('btn-migrate-trigger');
    const migrateModal = document.getElementById('migrate-modal');
    const btnStartMigrate = document.getElementById('btn-start-migrate');
    const btnCancelMigrate = document.getElementById('btn-cancel-migrate');
    const btnStopMigrate = document.getElementById('btn-stop-migrate');
    const btnCloseMigrate = document.getElementById('btn-close-migrate');
    const inpMigrateUrl = document.getElementById('inp-migrate-url');
    const migrateInputArea = document.getElementById('migrate-input-area');
    const migrateProgressArea = document.getElementById('migrate-progress-area');
    const migrateLogs = document.getElementById('migrate-logs');

    const deleteModal = document.getElementById('delete-modal');
    const btnConfirmDelete = document.getElementById('btn-confirm-delete');
    const btnCancelDelete = document.getElementById('btn-cancel-delete');

    // --- 创建文章 ---
    if (btnCreatePost) {
        btnCreatePost.addEventListener('click', async () => {
            if (btnCreatePost.disabled) return;
            const originalText = btnCreatePost.textContent;
            btnCreatePost.disabled = true;
            btnCreatePost.textContent = '创建中...';
            
            const startTime = Date.now();
            let success = false;
            try {
                const res = await fetch('/api/post/create', {
                    method: 'POST',
                    headers: { 'Authorization': localStorage.getItem('mc_token') }
                });
                const elapsed = Date.now() - startTime;
                if (elapsed < 1000) await new Promise(resolve => setTimeout(resolve, 1000 - elapsed));

                if (res.ok) {
                    success = true;
                    localStorage.setItem('mc_pending_toast', '文章创建成功！');
                    location.reload(); 
                } else {
                    showToast('创建失败');
                }
            } catch (e) {
                const elapsed = Date.now() - startTime;
                if (elapsed < 1000) await new Promise(resolve => setTimeout(resolve, 1000 - elapsed));
                showToast('网络错误');
            } finally {
                if (!success) {
                    btnCreatePost.disabled = false;
                    btnCreatePost.textContent = originalText;
                }
            }
        });
    }

    // --- 删除文章 ---
    document.querySelectorAll('.btn-delete-post').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation(); 
            deleteTargetCid = btn.dataset.cid;
            if(deleteModal) deleteModal.classList.add('open');
        });
    });

    if (btnCancelDelete) {
        btnCancelDelete.addEventListener('click', () => {
            if(deleteModal) deleteModal.classList.remove('open');
            deleteTargetCid = null;
        });
    }

    if (btnConfirmDelete) {
        btnConfirmDelete.addEventListener('click', async () => {
            if (!deleteTargetCid) return;
            btnConfirmDelete.textContent = '删除中...';
            btnConfirmDelete.disabled = true;

            try {
                const res = await fetch('/api/post/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': localStorage.getItem('mc_token')
                    },
                    body: JSON.stringify({ cid: deleteTargetCid })
                });

                if (res.ok) {
                    localStorage.setItem('mc_pending_toast', '文章已删除');
                    location.reload();
                } else {
                    const data = await res.json();
                    showToast('删除失败: ' + (data.error || '未知错误'));
                    btnConfirmDelete.textContent = '确认删除';
                    btnConfirmDelete.disabled = false;
                    deleteModal.classList.remove('open');
                }
            } catch (e) {
                showToast('网络错误');
                btnConfirmDelete.textContent = '确认删除';
                btnConfirmDelete.disabled = false;
                deleteModal.classList.remove('open');
            }
        });
    }

    // --- 迁移文章 ---
    if (btnMigrateTrigger) {
        btnMigrateTrigger.addEventListener('click', () => {
            if (migrateModal) {
                migrateModal.classList.add('open');
                migrateInputArea.style.display = 'block';
                migrateProgressArea.style.display = 'none';
                migrateLogs.innerHTML = '';
                inpMigrateUrl.value = '';
                btnCloseMigrate.style.display = 'none';
                if (btnStopMigrate) btnStopMigrate.style.display = 'block';
            }
        });
    }

    if (btnCancelMigrate) {
        btnCancelMigrate.addEventListener('click', () => {
            if (migrateModal) migrateModal.classList.remove('open');
        });
    }

    if (btnStopMigrate) {
        btnStopMigrate.addEventListener('click', () => {
            if (migrateAbortController) {
                migrateAbortController.abort();
                const line = document.createElement('div');
                line.textContent = `> [操作] 用户已中止迁移。`;
                line.style.color = '#ef4444';
                migrateLogs.appendChild(line);
                migrateLogs.scrollTop = migrateLogs.scrollHeight;
                
                btnStopMigrate.style.display = 'none';
                
                const closeBtn = document.createElement('button');
                closeBtn.className = 'btn-action cancel'; 
                closeBtn.style.flex = '1';
                closeBtn.textContent = '关闭';
                closeBtn.onclick = () => location.reload();
                
                const actionContainer = btnCloseMigrate.parentElement;
                actionContainer.innerHTML = ''; 
                actionContainer.appendChild(closeBtn);
            }
        });
    }

    if (btnStartMigrate) {
        btnStartMigrate.addEventListener('click', async () => {
            const url = inpMigrateUrl.value.trim();
            if (!url) return showToast('请输入链接');

            migrateInputArea.style.display = 'none';
            migrateProgressArea.style.display = 'block';
            if (btnStopMigrate) btnStopMigrate.style.display = 'block';
            
            const log = (msg) => {
                const line = document.createElement('div');
                line.textContent = `> ${msg}`;
                migrateLogs.appendChild(line);
                migrateLogs.scrollTop = migrateLogs.scrollHeight;
            };

            log(`开始连接服务器...`);

            migrateAbortController = new AbortController();

            try {
                const response = await fetch('/api/post/migrate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': localStorage.getItem('mc_token')
                    },
                    body: JSON.stringify({ url }),
                    signal: migrateAbortController.signal
                });

                const reader = response.body.getReader();
                const decoder = new TextDecoder("utf-8");
                let buffer = "";

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split("\n\n");
                    buffer = lines.pop(); 

                    for (const line of lines) {
                        if (line.startsWith("data: ")) {
                            try {
                                const data = JSON.parse(line.substring(6));
                                if (data.step) {
                                    log(data.step);
                                } else if (data.success) {
                                    log(`[成功] 文章已创建 (CID: ${data.cid})`);
                                    if (btnStopMigrate) btnStopMigrate.style.display = 'none';
                                    btnCloseMigrate.style.display = 'block';
                                } else if (data.error) {
                                    log(`[错误] ${data.error}`);
                                    log(`操作已终止。`);
                                    if (btnStopMigrate) btnStopMigrate.style.display = 'none';
                                    
                                    const retryBtn = document.createElement('button');
                                    retryBtn.className = 'btn-action cancel';
                                    retryBtn.style.flex = '1';
                                    retryBtn.textContent = '关闭';
                                    retryBtn.onclick = () => location.reload();
                                    
                                    const actionContainer = btnCloseMigrate.parentElement;
                                    actionContainer.innerHTML = '';
                                    actionContainer.appendChild(retryBtn);
                                }
                            } catch (e) {
                                console.error("Parse Error", e);
                            }
                        }
                    }
                }
            } catch (e) {
                if (e.name !== 'AbortError') {
                    log(`[网络错误] ${e.message}`);
                }
            } finally {
                migrateAbortController = null;
            }
        });
    }
}