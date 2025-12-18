/**
 * monaco-markdown-extension.js
 * 为 Monaco Editor 提供 Markdown 语法扩展：
 * 1. 列表/引用自动补全 (Enter 键)
 * 2. 选中文字智能包裹 (*, _, ~, `, [ 等符号)
 */

export function enableMarkdownExtensions(editor, monaco) {
    // 注册 Enter 键行为 (自动补全列表/引用)
    editor.addCommand(monaco.KeyCode.Enter, () => {
        const model = editor.getModel();
        const position = editor.getPosition();
        const lineContent = model.getLineContent(position.lineNumber);
        
        // 正则匹配：
        // 1. 无序列表 (*, -, +)
        // 2. 有序列表 (1.)
        // 3. 引用 (>)
        // 4. 任务列表 (- [ ] 或 - [x])
        const listRegex = /^(\s*)([*+-]|\d+\.)(\s+)(\[[ x]\]\s+)?/;
        const quoteRegex = /^(\s*)(>+)(\s+)/;
        
        const listMatch = lineContent.match(listRegex);
        const quoteMatch = lineContent.match(quoteRegex);
        
        const match = listMatch || quoteMatch;
        
        if (match) {
            // 如果当前行只有前缀（用户想结束列表），则删除前缀并换行
            if (lineContent.trim() === match[0].trim()) {
                editor.executeEdits('markdown-ext', [{
                    range: new monaco.Range(position.lineNumber, 1, position.lineNumber, lineContent.length + 1),
                    text: '',
                    forceMoveMarkers: true
                }]);
                // 触发默认换行，实际上因为删除了内容，这里需要手动插入换行
                editor.trigger('keyboard', 'type', { text: '\n' });
                return;
            }

            // 构建下一行的前缀
            let prefix = match[1] + match[2] + match[3];
            
            // 如果是有序列表，数字加 1
            if (/^\d+\.$/.test(match[2])) {
                const num = parseInt(match[2]);
                prefix = match[1] + (num + 1) + '.' + match[3];
            }
            
            // 如果是任务列表，新行应该是未选中状态
            if (match[4]) {
                prefix += '[ ] ';
            }
            
            // 插入换行和前缀
            editor.executeEdits('markdown-ext', [{
                range: new monaco.Range(position.lineNumber, position.column, position.lineNumber, position.column),
                text: '\n' + prefix,
                forceMoveMarkers: true
            }]);
            
            // 滚动到光标处
            editor.revealPosition(editor.getPosition());
        } else {
            // 普通换行
            editor.trigger('keyboard', 'type', { text: '\n' });
        }
    });

    // 注册智能包裹行为
    const wrapChars = {
        '*': '*',  // 加粗/斜体
        '_': '_',  // 斜体
        '~': '~',  // 删除线
        '`': '`',  // 代码块
        '[': ']',  // 链接
        '(': ')',  // 括号
        '{': '}',  // 花括号
        '"': '"',  // 双引号
        "'": "'"   // 单引号
    };

    // 监听按键事件用于处理包裹逻辑
    editor.onKeyDown((e) => {
        // 忽略组合键
        if (e.ctrlKey || e.altKey || e.metaKey) return;

        const selection = editor.getSelection();
        // 如果没有选中文本，不处理
        if (selection.isEmpty()) return;

        // 获取按下的字符
        // 注意：Monaco 的 e.browserEvent.key 获取的是实际字符，兼容性较好
        const key = e.browserEvent.key;
        
        if (wrapChars[key]) {
            e.preventDefault();
            e.stopPropagation();

            const startChar = key;
            const endChar = wrapChars[key];
            const model = editor.getModel();
            const selectedText = model.getValueInRange(selection);

            editor.executeEdits('markdown-wrap', [{
                range: selection,
                text: startChar + selectedText + endChar,
                forceMoveMarkers: true
            }]);

            // 保持选中状态（选中包裹后的文本内部，或者整个包裹文本？VSCode 默认是选中原来的文本，这里我们选中原来的文本）
            // 修正选中范围：包裹后，开始位置+1，结束位置+1
            editor.setSelection(new monaco.Range(
                selection.startLineNumber,
                selection.startColumn + 1,
                selection.endLineNumber,
                selection.endColumn + 1
            ));
        }
    });
}