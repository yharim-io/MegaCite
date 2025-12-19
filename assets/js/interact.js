import { escapeHtml, showToast } from './utils.js';

let postCid = null;
let els = {};

export function initInteractListeners() {
    // 场景 1: 列表页批量更新 (控制台 & 广场)
    // 查找所有需要显示统计数据的列表项
    const statElements = document.querySelectorAll('.meta-stat[data-cid]');
    if (statElements.length > 0) {
        updateListStats();
    }

    // 场景 2: 文章详情页交互
    const interactSection = document.getElementById('interaction-section');
    if (!interactSection) return;

    postCid = document.querySelector('meta[name="post-cid"]')?.content;
    if (!postCid) return;

    els = {
        btnLike: document.getElementById('btn-like'),
        likeCount: document.getElementById('like-count'),
        commentCount: document.getElementById('comment-count'),
        commentList: document.getElementById('comment-list'),
        inputArea: document.getElementById('comment-input-area'),
        inpComment: document.getElementById('inp-comment'),
        btnSubmit: document.getElementById('btn-submit-comment')
    };

    loadStats();
    loadComments();
    bindEvents();
}

/**
 * 批量更新列表页的统计数据
 */
async function updateListStats() {
    const statElements = document.querySelectorAll('.meta-stat[data-cid]');
    if (statElements.length === 0) return;

    // 收集所有唯一的 CID
    const cids = new Set();
    statElements.forEach(el => cids.add(el.dataset.cid));
    
    if (cids.size === 0) return;

    try {
        const cidsParam = Array.from(cids).join(',');
        const res = await fetch(`/api/interact/batch_stats?cids=${cidsParam}`);
        if (!res.ok) return;

        const data = await res.json();
        
        // 更新 DOM
        statElements.forEach(el => {
            const cid = el.dataset.cid;
            const type = el.dataset.type; // 'like' or 'comment'
            const stats = data[cid];
            
            if (stats) {
                if (type === 'like') {
                    // 更新点赞数，保留图标
                    const icon = el.querySelector('svg').outerHTML;
                    el.innerHTML = `${icon} ${stats.likes}`;
                } else if (type === 'comment') {
                    // 更新评论数，保留图标
                    const icon = el.querySelector('svg').outerHTML;
                    el.innerHTML = `${icon} ${stats.comments}`;
                }
            }
        });
    } catch (e) {
        console.error("Batch stats update failed:", e);
    }
}

async function loadStats() {
    try {
        const res = await fetch(`/api/interact/stats?post_cid=${postCid}`);
        if (!res.ok) {
            console.error('Stats load failed:', res.status, res.statusText);
            return;
        }
        
        const data = await res.json();
        
        els.likeCount.textContent = data.likes;
        els.commentCount.textContent = `(${data.comments})`;
        
        if (data.liked_by_me) {
            els.btnLike.classList.add('active');
        } else {
            els.btnLike.classList.remove('active');
        }

        if (data.current_user_id) {
            els.inputArea.style.display = 'block';
        } else {
            els.inputArea.style.display = 'none';
        }
    } catch (e) {
        console.error("Load Stats Error:", e);
    }
}

async function loadComments() {
    try {
        const res = await fetch(`/api/interact/comments?post_cid=${postCid}`);
        if (!res.ok) return;

        const data = await res.json();
        
        els.commentList.innerHTML = '';
        if (!data.comments || data.comments.length === 0) {
            els.commentList.innerHTML = '<div class="no-comments">暂无评论</div>';
            return;
        }

        data.comments.forEach(c => {
            const div = document.createElement('div');
            div.className = 'comment-item';
            
            let deleteBtn = '';
            if (c.can_delete) {
                deleteBtn = `<span class="comment-delete" data-id="${c.id}">删除</span>`;
            }

            div.innerHTML = `
                <div class="comment-header">
                    <span class="comment-user">${c.username}</span>
                    <span class="comment-date">${c.created_at}</span>
                    ${deleteBtn}
                </div>
                <div class="comment-body">${escapeHtml(c.content)}</div>
            `;
            els.commentList.appendChild(div);
        });
    } catch (e) {
        console.error("Load Comments Error:", e);
    }
}

function bindEvents() {
    if (els.btnLike) {
        els.btnLike.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/interact/like', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ post_cid: postCid })
                });
                
                if (res.status === 401) {
                    showToast('请先登录');
                    const btnLogin = document.getElementById('btn-login-trigger');
                    if (btnLogin) btnLogin.click();
                    return;
                }
                
                const data = await res.json();
                if (data.error) {
                    showToast(data.error);
                    return;
                }
                
                els.likeCount.textContent = data.count;
                if (data.action === 'added') {
                    els.btnLike.classList.add('active');
                } else {
                    els.btnLike.classList.remove('active');
                }
            } catch (e) {
                console.error(e);
            }
        });
    }

    if (els.btnSubmit) {
        els.btnSubmit.addEventListener('click', async () => {
            const content = els.inpComment.value.trim();
            if (!content) return;

            els.btnSubmit.disabled = true;

            try {
                const res = await fetch('/api/interact/comment', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ post_cid: postCid, content: content })
                });

                if (res.ok) {
                    els.inpComment.value = '';
                    await loadStats();
                    await loadComments();
                } else {
                    const err = await res.json();
                    showToast(err.error || '评论失败');
                }
            } catch (e) {
                console.error(e);
            } finally {
                els.btnSubmit.disabled = false;
            }
        });
    }

    if (els.commentList) {
        els.commentList.addEventListener('click', async (e) => {
            if (e.target.classList.contains('comment-delete')) {
                const id = e.target.getAttribute('data-id');
                if (confirm('确认删除此评论？')) {
                    try {
                        const res = await fetch(`/api/interact/comment?id=${id}`, {
                            method: 'DELETE'
                        });
                        if (res.ok) {
                            await loadStats();
                            await loadComments();
                        } else {
                            const err = await res.json();
                            showToast(err.error || '删除失败');
                        }
                    } catch (e) {
                        console.error(e);
                    }
                }
            }
        });
    }
}