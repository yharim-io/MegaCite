/**
 * editor.js
 * Monaco 编辑器逻辑 (初始化, 同步滚动, 保存)
 */
import { showToast } from './utils.js';
import { enableMarkdownExtensions } from './monaco-markdown-extension.js';

let editorInstance = null;
let isEditorDirty = false;

function markDirty() {
    if (!isEditorDirty) {
        isEditorDirty = true;
        document.title = "编辑器 * - MegaCite";
    }
}

function markClean() {
    isEditorDirty = false;
    document.title = "编辑器 - MegaCite";
}

export function initEditor() {
    const monacoContainer = document.getElementById('monaco-container');
    if (!monacoContainer) return; // 不在编辑器页面

    require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' }});

    const editTitle = document.getElementById('edit-title');
    const editDescription = document.getElementById('edit-description');
    const editCategorySelect = document.getElementById('edit-category-select');
    const editCategoryInput = document.getElementById('edit-category-input');
    const editPreview = document.getElementById('edit-preview');
    const btnSavePost = document.getElementById('btn-save');
    const btnBack = document.getElementById('btn-back');

    const params = new URLSearchParams(window.location.search);
    const cid = params.get('cid');
    
    if (!cid) {
        showToast('参数错误: 缺少 CID');
        return;
    }

    // 监听基础输入变化
    editTitle.addEventListener('input', markDirty);
    if (editDescription) editDescription.addEventListener('input', markDirty);
    editCategorySelect.addEventListener('change', markDirty);
    editCategoryInput.addEventListener('input', markDirty);

    // 拦截退出
    window.addEventListener('beforeunload', (e) => {
        if (isEditorDirty) {
            e.preventDefault();
            e.returnValue = ''; 
        }
    });

    // 返回按钮逻辑
    btnBack.addEventListener('click', () => {
        if (isEditorDirty && !confirm("您有未保存的更改，确定要离开吗？")) return;
        window.history.back();
    });

    // 加载 Monaco
    require(['vs/editor/editor.main'], async () => {
        try {
            // 获取数据
            const [postRes, catRes] = await Promise.all([
                fetch(`/api/post/detail?cid=${cid}`, { headers: { 'Authorization': localStorage.getItem('mc_token') } }),
                fetch('/api/categories')
            ]);
            
            if (!postRes.ok) throw new Error("加载文章失败");
            
            const postData = await postRes.json();
            const catData = await catRes.json();

            // 填充分类 Select
            const categories = catData.categories || [];
            const validCats = categories.filter(c => c !== 'Default' && c !== '__NEW__');
            
            editCategorySelect.innerHTML = `<option value="Default">Default</option>`;
            validCats.forEach(cat => {
                const opt = document.createElement('option');
                opt.value = cat;
                opt.textContent = cat;
                editCategorySelect.appendChild(opt);
            });
            editCategorySelect.innerHTML += `<option value="__NEW__" style="font-weight:bold;color:var(--vp-c-brand)">+ 新建分类...</option>`;

            // 设置初始值
            editTitle.value = postData.title || '';
            if (editDescription) editDescription.value = postData.description || '';
            
            if (validCats.includes(postData.category)) {
                editCategorySelect.value = postData.category;
            } else if (postData.category !== 'Default') {
                const opt = document.createElement('option');
                opt.value = postData.category;
                opt.textContent = postData.category;
                editCategorySelect.insertBefore(opt, editCategorySelect.lastElementChild);
                editCategorySelect.value = postData.category;
            } else {
                editCategorySelect.value = 'Default';
            }

            // 初始化编辑器
            editorInstance = monaco.editor.create(monacoContainer, {
                value: postData.context || '',
                language: 'markdown',
                theme: 'vs', 
                automaticLayout: true,
                wordWrap: 'on',
                minimap: { enabled: false },
                fontSize: 14,
                padding: { top: 20, bottom: 20 },
                scrollBeyondLastLine: false,
                fontFamily: "'Roboto Mono', 'Menlo', 'Monaco', 'Courier New', monospace",
                
                // [新增] 关闭 Unicode 高亮 (解决中文全角符号报错)
                unicodeHighlight: {
                    ambiguousCharacters: false,
                    invisibleCharacters: false,
                },
                // [新增] 关闭内置的验证 (Markdown 通常不需要，但以防万一)
                quickSuggestions: false,
                renderValidationDecorations: 'off'
            });

            // [新增] 启用 Markdown 扩展 (列表补全、智能包裹)
            enableMarkdownExtensions(editorInstance, monaco);

            // 初始预览
            if (window.marked) editPreview.innerHTML = marked.parse(postData.context || '');

            // 实时预览与脏标记
            editorInstance.onDidChangeModelContent(() => {
                markDirty();
                const newVal = editorInstance.getValue();
                if (window.marked) editPreview.innerHTML = marked.parse(newVal);
            });

            // 滚动同步 (Throttle)
            const syncPreviewScroll = _.throttle(() => {
                const editorScrollTop = editorInstance.getScrollTop();
                const editorScrollHeight = editorInstance.getScrollHeight();
                const editorViewportHeight = editorInstance.getLayoutInfo().height;
                const scrollPercentage = editorScrollTop / (editorScrollHeight - editorViewportHeight);
                const previewScrollHeight = editPreview.scrollHeight;
                const previewViewportHeight = editPreview.clientHeight;
                editPreview.scrollTop = scrollPercentage * (previewScrollHeight - previewViewportHeight);
            }, 20); 

            const syncEditorScroll = _.throttle(() => {
                const previewScrollTop = editPreview.scrollTop;
                const previewScrollHeight = editPreview.scrollHeight;
                const previewViewportHeight = editPreview.clientHeight;
                const scrollPercentage = previewScrollTop / (previewScrollHeight - previewViewportHeight);
                const editorScrollHeight = editorInstance.getScrollHeight();
                const editorViewportHeight = editorInstance.getLayoutInfo().height;
                editorInstance.setScrollTop(scrollPercentage * (editorScrollHeight - editorViewportHeight));
            }, 20);

            let isEditorScrolling = false, isPreviewScrolling = false;

            editorInstance.onDidScrollChange((e) => {
                if (!e.scrollTopChanged || isPreviewScrolling) return;
                isEditorScrolling = true;
                syncPreviewScroll();
                setTimeout(() => isEditorScrolling = false, 50);
            });

            editPreview.addEventListener('scroll', () => {
                if (isEditorScrolling) return;
                isPreviewScrolling = true;
                syncEditorScroll();
                setTimeout(() => isPreviewScrolling = false, 50);
            });

        } catch (e) {
            console.error(e);
            showToast(e.message);
            setTimeout(() => window.location.href = '/', 1500);
        }
    });

    // 分类输入切换
    editCategorySelect.addEventListener('change', () => {
        if (editCategorySelect.value === '__NEW__') {
            editCategorySelect.style.display = 'none';
            editCategoryInput.style.display = 'block';
            editCategoryInput.focus();
        }
    });

    editCategoryInput.addEventListener('blur', () => {
        if (!editCategoryInput.value.trim()) {
            editCategoryInput.style.display = 'none';
            editCategorySelect.style.display = 'block';
            editCategorySelect.value = 'Default';
        }
    });

    // 保存逻辑
    btnSavePost.addEventListener('click', async () => {
        if (!editorInstance) return;

        const title = editTitle.value.trim();
        const description = editDescription ? editDescription.value.trim() : '';
        const context = editorInstance.getValue();
        let category = editCategorySelect.value;
        
        if (editCategoryInput.style.display !== 'none') {
            category = editCategoryInput.value.trim();
        }

        if (!title) return showToast('标题不能为空');
        if (category === '__NEW__' || !category) category = 'Default';

        btnSavePost.textContent = '保存中...';
        btnSavePost.disabled = true;

        try {
            const res = await fetch('/api/post/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': localStorage.getItem('mc_token')
                },
                body: JSON.stringify({
                    cid: cid,
                    title: title,
                    category: category,
                    context: context,
                    description: description
                })
            });

            if (res.ok) {
                const data = await res.json();
                markClean();
                showToast('保存成功，正在跳转...');
                setTimeout(() => {
                    if (data.url) window.location.href = data.url;
                    else window.location.href = `/${localStorage.getItem('mc_username')}/index.html`; 
                }, 1000);
            } else {
                const err = await res.json();
                showToast('保存失败: ' + (err.error || '未知错误'));
            }
        } catch (e) {
            showToast('网络错误');
        } finally {
            if (btnSavePost.textContent === '保存中...') {
                btnSavePost.textContent = '保存文章';
                btnSavePost.disabled = false;
            }
        }
    });
}