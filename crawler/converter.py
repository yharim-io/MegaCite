import re
from openai import OpenAI
from core.config import OPENAI_CONFIG

def convert_html_to_markdown(html_source: str) -> dict:
    client = OpenAI(
        api_key=OPENAI_CONFIG["api_key"],
        base_url=OPENAI_CONFIG["base_url"]
    )

    # 1. 记忆阶段
    CHUNK_SIZE = 10000 
    chunks = [html_source[i:i+CHUNK_SIZE] for i in range(0, len(html_source), CHUNK_SIZE)]
    total_parts = len(chunks)
    
    # [System Prompt] 强调排版专家身份
    messages = [
        {"role": "system", "content": (
            "You are a strict HTML to Markdown converter and a typography expert. "
            "You strictly enforce Markdown syntax rules, especially regarding spacing, lists, and structure."
        )}
    ]

    for i, chunk in enumerate(chunks[:-1]):
        part_num = i + 1
        user_msg = (
            f"[Part {part_num}/{total_parts} of HTML Source]\n"
            f"```html\n{chunk}\n```\n\n"
            f"Instruction: Read and memorize this HTML content. Reply 'ACK'."
        )
        messages.append({"role": "user", "content": user_msg})
        
        print(f"[*] Loading Part {part_num}...")
        client.chat.completions.create(
            model=OPENAI_CONFIG["model"],
            messages=messages,
            temperature=0.1
        )
        messages.append({"role": "assistant", "content": "ACK"})

    # 2. 初始指令
    final_chunk = chunks[-1]
    
    initial_prompt = """
Role: You are a **ZERO-TOLERANCE** Strict HTML-to-Markdown Compiler. You do NOT "write" content; you compile input code into output code.
**WARNING**: Any deviation from the syntax rules below is considered a SYSTEM FAILURE.

--- 1. THE "TWO BLANK LINES" RULE (HIGHEST PRIORITY) ---
Definition: "Block Element" includes: Paragraphs (<p>), Headers (h1-h6), Lists (ul/ol), Code Blocks (pre), Blockquotes, Tables, and HR.

RULE: Between ANY two Block Elements, you MUST insert strictly **TWO BLANK LINES**.
(Visually, this looks like a large gap. Technically, it is 3 newline characters `\n\n\n`).

[Example of CORRECT Spacing]:
Paragraph text ends here.
(Blank Line 1)
(Blank Line 2)

  - List item starts here.

[Example of WRONG Spacing]:
Paragraph text ends here.

  - List item starts here.

--- 2. SYNTAX MAPPING TABLE (STRICT ENUMERATION) ---

Process the input HTML tag by tag using this exact mapping:

**A. BLOCK STRUCTURES (Apply "Two Blank Lines" Rule around these)**

1.  `<h1>` -> ` #  `
2.  `<h2>` -> ` ##  `
3.  `<h3>` -> ` ###  ` (Scale up to h6)
    *CONSTRAINT*: Never convert bold text (`<b>`) to headers. Only use `#` if the input is `<h>`.
4.  `<ul>` -> List items use ` -  ` (hyphen + space).
5.  `<ol>` -> List items use ` 1.  ` (number + dot + space).
    *NESTING*: Indent nested `<li>` content by 4 spaces.
6.  `<blockquote>` -> ` >  ` (followed by space).
7.  `<pre><code>` -> Fenced Code Block:
      * **FATAL ERROR PREVENTION**:
      * **RULE**: You MUST Output BOTH the opening ` ``` ` AND the closing ` ``` `.
      * **FORBIDDEN**: Leaving a code block open (e.g., printing the start ` ``` ` without the end ` ``` `).
      * **Format**:
        ```language
        code content
        ```
8.  `<hr>` -> `---`
9.  `<table>` -> Convert to Markdown Table `| col | col |`.

**B. INLINE STYLES (Do NOT add newlines around these)**

1.  `<b>` or `<strong>` -> `**content**` (Standard Markdown Bold)
    *CRITICAL*: No space between `**` and the text.
    (Good: `**Text**`, Bad: `** Text **`)
2.  `<i>` or `<em>` -> `*content*` (Italic)
3.  `<s>` or `<del>` -> `~~content~~` (Strikethrough)
4.  `<code>` (Inline) -> Backticks: `` `code` ``
    *Example*: `Use the <code>print()</code> function` -> ` Use the  `print()`  function `.
5.  `<a href="...">` -> `[Text](URL)`
6.  `<img src="...">` -> `![Alt](URL)`
7.  `<br>` -> Insert a single newline `\n`.

--- 3. TEXT PROCESSING (PAN GU ZHI BAI) ---

1.  **Spacing**: Insert exactly ONE space between:
      - Chinese and English (e.g., `数据 AI` not `数据AI`)
      - Chinese and Numbers (e.g., `版本 5.0` not `版本5.0`)
2.  **Exceptions**: DO NOT add spaces inside code blocks, URLs, or between text and punctuation.

--- 4. CONTENT FILTERING (REDUNDANCY CHECK) ---

1.  **Header Check**: Check the text inside the first `===CONTENT===`.
2.  **Remove**: If the first paragraph/header is a duplicate of the Article Title, DELETE it.
3.  **Start**: Begin output with the first unique line of content.

--- 5. OUTPUT FORMAT STRUCTURE ---
output exactly in this format:

===TITLE===
[Article Title]
**CRITICAL RULE FOR TITLE**: This line must be **PLAIN TEXT ONLY**. strictly **NO** Markdown formatting.

  - **NO** Hash marks (`#`). Even if the source is `<h1>`, strip the tags and output only the text.
  - **NO** Bolding (`**`) or Italics.
  - **VIOLATION**: Outputting `# Title` here is strictly prohibited. Output `Title` only.

===SUMMARY===
[One sentence summary]

===CONTENT===
[Markdown Body with PERFECT 2-BLANK-LINE Spacing]

**FINAL INTEGRITY CHECK**:
Before finishing, verify that every single Code Block (`<pre>`) has a CLOSING triple-backtick (` ``` `). Unclosed code blocks are unacceptable.
"""
    
    user_msg_final = (
        f"[Part {total_parts}/{total_parts} of HTML Source]\n"
        f"```html\n{final_chunk}\n```\n\n"
        f"Instruction: {initial_prompt}"
    )
    
    messages.append({"role": "user", "content": user_msg_final})
    
    print(f"[*] Starting Generation...")
    
    full_raw_text = ""
    loop_count = 0
    max_loops = 20 
    
    while loop_count < max_loops:
        loop_count += 1
        
        response = client.chat.completions.create(
            model=OPENAI_CONFIG["model"],
            messages=messages,
            temperature=0.1
        )

        content = response.choices[0].message.content
        messages.append({"role": "assistant", "content": content})
        
        if "===END===" in content:
            clean_part = content.replace("===END===", "")
            full_raw_text += clean_part
            print(f"    -> Segment {loop_count}: '===END===' detected. Done.")
            break
        else:
            full_raw_text += content
            
            # 锚点逻辑
            anchor_length = 200
            anchor_text = content[-anchor_length:] if len(content) > anchor_length else content
            
            print(f"    -> Segment {loop_count}: Continuing from anchor...")
            
            continuation_prompt = f"""
I received your output ending with:
--- BEGIN SNIPPET ---
{anchor_text}
--- END SNIPPET ---

**SYSTEM INSTRUCTION**:
1. **Contextual & Exact Continuity**: Review the conversation history to understand the context. Continue converting/generating **EXACTLY** after the last character of the snippet above. Do not repeat the snippet text itself.
2. **Code Block Integrity**: Check if the snippet ends inside an open code block.
   - If the code block should have ended but was cut off, output the closing ` ``` ` immediately.
   - If the code is incomplete, continue the code logic seamlessly.
3. **Strictly enforce List Spacing**: Ensure a blank line exists before starting a list.
4. **Strictly enforce Chinese-English Spacing**: Add space between Hanzi and English/Numbers.
5. Only output `===END===` when the entire task is completely finished.
"""            
            messages.append({"role": "user", "content": continuation_prompt})

    # 3. 解析结果
    print(f"[*] Stitching complete. Total length: {len(full_raw_text)} chars.")
    
    clean_text = full_raw_text
    # clean_text = re.sub(r"^```(markdown|text)?", "", clean_text, flags=re.IGNORECASE)
    # clean_text = re.sub(r"```$", "", clean_text)
    
    try:
        title_match = re.search(r"===TITLE===\s*(.*?)\s*(?:===SUMMARY===|$)", clean_text, re.DOTALL)
        title = title_match.group(1).strip() if title_match else "Untitled"
        
        summary_match = re.search(r"===SUMMARY===\s*(.*?)\s*(?:===CONTENT===|$)", clean_text, re.DOTALL)
        description = summary_match.group(1).strip() if summary_match else "No description"
        
        content_match = re.search(r"===CONTENT===\s*(.*)", clean_text, re.DOTALL)
        context = content_match.group(1).strip() if content_match else clean_text
        
        if not content_match and "===CONTENT===" not in clean_text:
            context = clean_text

    except Exception as e:
        print(f"[-] Parsing Error: {e}. Returning raw text.")
        title = "Parse Error"
        description = "Error"
        context = clean_text

    return {
        "title": title,
        "description": description,
        "context": context
    }