import os
import re
import requests

SOURCE_DIR = "CourseApp"
LOG_FILE = os.path.join(SOURCE_DIR, "logs", "errors.log")
MAX_CONTEXT_LINES = 20
MODEL_NAME = "mistralai/Mixtral-8x7B-Instruct-v0.1"
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

def extract_code_block(text):
    # Extract code between triple backticks or fallback to C#-like lines
    code_blocks = re.findall(r"``````", text, re.IGNORECASE)
    if code_blocks:
        return code_blocks[0].strip()
    lines = text.splitlines()
    code_lines = [
        line for line in lines if line.strip()
        and not line.strip().startswith("//")
        and not re.match(r'^[A-Za-z ]+:', line.strip())
    ]
    return "\n".join(code_lines).strip()

def call_together_ai(file_path, method_context, error_line, exception, message):
    prompt = f"""
You're a senior C# engineer. A file `{file_path}` has an error at line {error_line}.

Exception: {exception}
Message: {message}

Here is the full code of the method containing the error:
{method_context}

Return ONLY the fixed code for the entire method — just the method, no comments/headers/markdown.
"""
    response = requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers=HEADERS,
        json={
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that fixes C# code bugs."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 512,
        },
        timeout=60,
    )
    response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"].strip()
    return extract_code_block(raw)

def parse_log_line(line):
    match = re.match(
        r'\[ERROR\] \[(.*?)\] \[(.*?):(\d+)\] (\w+): (.*)', line
    )
    if match:
        _, file_name, line_num, ex_type, message = match.groups()
        return file_name, int(line_num), ex_type, message
    return None

def find_method_bounds(lines, error_line_num):
    # Try to find the method boundaries around error_line_num (1-based)
    method_start = None
    method_end = None
    open_braces = 0

    # Scan upwards for method start (detect signature line)
    for idx in range(error_line_num - 1, -1, -1):
        line = lines[idx].strip()
        # Heuristic: method signature likely
        if (re.match(r'(public|private|protected|internal)?\s*\w[\w\s<>,]*\s+\w+\s*\([^)]*\)\s*{', line)):
            method_start = idx
            break
        # Or first line that opens a brace
        if "{" in line and open_braces == 0:
            method_start = idx
            break

    if method_start is None:
        return None, None

    # Scan down to find method end (match braces)
    open_braces = 0
    for idx in range(method_start, len(lines)):
        line = lines[idx]
        open_braces += line.count('{')
        open_braces -= line.count('}')
        if open_braces == 0 and idx > method_start:
            method_end = idx
            break

    if method_end is None:
        return None, None
    return method_start, method_end+1  # end is exclusive

def has_balanced_braces(code):
    stack = []
    for c in code:
        if c == '{':
            stack.append('{')
        elif c == '}':
            if not stack:
                return False
            stack.pop()
    return not stack

def apply_method_patch(file_path, method_start, method_end, fixed_method_code):
    backup_dir = os.path.join(SOURCE_DIR, "backup")
    os.makedirs(backup_dir, exist_ok=True)
    with open(file_path, "r") as f:
        lines = f.readlines()
    backup_path = os.path.join(backup_dir, os.path.basename(file_path))
    with open(backup_path, "w") as f:
        f.writelines(lines)
    fixed_lines = [line if line.endswith('\n') else line + '\n' for line in fixed_method_code.strip().splitlines()]
    # Check brace balance before patch
    pre_code = "".join(lines[:method_start] + lines[method_end:])
    pre_balanced = has_balanced_braces(pre_code)
    post_code = "".join(lines[:method_start] + fixed_lines + lines[method_end:])
    post_balanced = has_balanced_braces(post_code)
    if not (pre_balanced and post_balanced):
        print(f"❗ Unbalanced braces after patch in {file_path}. Skip this patch.")
        return False
    # Apply patch
    updated = lines[:method_start] + fixed_lines + lines[method_end:]
    with open(file_path, "w") as f:
        f.writelines(updated)
    print(f"✅ Patched method in {file_path} (backup at {backup_path})")
    return True

def analyze_and_patch_all():
    if not os.path.exists(LOG_FILE):
        print(f"❌ Log file not found: {LOG_FILE}")
        return
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
    error_lines = []
    seen_errors = set()
    for line in lines:
        line = line.strip()
        if line and "[ERROR]" in line:
            result = parse_log_line(line)
            if result:
                file_name, line_num, exception, message = result
                error_key = f"{file_name}:{line_num}:{exception}"
                if error_key not in seen_errors:
                    error_lines.append(line)
                    seen_errors.add(error_key)
    if not error_lines:
        print("No valid error logs found.")
        return
    print(f"📋 Found {len(error_lines)} unique errors to fix\n")
    for index, error_line in enumerate(error_lines, 1):
        result = parse_log_line(error_line)
        if not result:
            continue
        file_name, line_num, exception, message = result
        source_path = os.path.join(SOURCE_DIR, file_name)
        if not os.path.exists(source_path):
            print(f"❌ File not found: {source_path}")
            continue
        with open(source_path, "r") as f:
            src_lines = f.readlines()
        method_start, method_end = find_method_bounds(src_lines, line_num)
        if method_start is None or method_end is None:
            print(f"❗ Could not find method bounds for {file_name}:{line_num} — skipping.")
            continue
        method_context = "".join(src_lines[method_start:method_end])
        print(f"\n🔍 [{index}/{len(error_lines)}] Analyzing {file_name}:{line_num} — {exception}")
        print(f"Message: {message}")
        try:
            ai_patch = call_together_ai(file_name, method_context, line_num, exception, message)
            print("✅ AI Suggestion:\n")
            print(ai_patch)
            print("\n🔧 Applying patch...\n")
            success = apply_method_patch(source_path, method_start, method_end, ai_patch)
            if not success:
                print(f"⏭️ Patch for {file_name}:{line_num} skipped due to structure error.\n")
            print("\n" + "="*50 + "\n")
        except Exception as e:
            print(f"❌ Error from Together AI: {e}\n")

if __name__ == "__main__":
    if not TOGETHER_API_KEY:
        print("❌ TOGETHER_API_KEY environment variable not set.")
    else:
        analyze_and_patch_all()
