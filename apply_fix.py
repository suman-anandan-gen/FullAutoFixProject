import os
import re
import requests

SOURCE_DIR = "CourseApp"
LOG_FILE = os.path.join(SOURCE_DIR, "logs", "errors.log")
MAX_CONTEXT_LINES = 10
MODEL_NAME = "mistralai/Mixtral-8x7B-Instruct-v0.1"

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

def call_together_ai(file_path, code_context, error_line, exception, message):
    prompt = f"""
You're a senior C# engineer. A file `{file_path}` has an error at line {error_line}:

Exception: {exception}
Message: {message}

Here is the code context:

{code_context}

Return the corrected version of this code block only — no explanation.
"""
    response = requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers=HEADERS,
        json={
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that fixes C# bugs."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 512,
        },
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

def parse_log_line(line):
    match = re.match(r'\[ERROR\] \[(.*?)\] \[(.*?):(\d+)\] (\w+): (.*)', line)
    if match:
        _, file_name, line_num, ex_type, message = match.groups()
        return file_name, int(line_num), ex_type, message
    return None

def get_code_context_lines(file_path, error_line, context_lines=MAX_CONTEXT_LINES):
    with open(file_path, "r") as f:
        lines = f.readlines()
    start = max(0, error_line - context_lines // 2 - 1)
    end = min(len(lines), error_line + context_lines // 2)
    return lines, start, end, lines[start:end]

def apply_patch(file_path, start, end, replacement_block):
    replacement_lines = [line + "\n" if not line.endswith("\n") else line for line in replacement_block.strip().splitlines()]
    with open(file_path, "r") as f:
        lines = f.readlines()
    backup_path = file_path + ".bak"
    with open(backup_path, "w") as f:
        f.writelines(lines)
    updated = lines[:start] + replacement_lines + lines[end:]
    with open(file_path, "w") as f:
        f.writelines(updated)
    print(f"\n✅ Patch applied to {file_path}")
    print(f"📦 Backup saved to: {backup_path}")

def analyze_and_patch():
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()

    last_error = lines[-1].strip()
    result = parse_log_line(last_error)

    if not result:
        print("❌ No valid error log found.")
        return

    file_name, line_num, exception, message = result
    source_path = os.path.join(SOURCE_DIR, file_name)

    if not os.path.exists(source_path):
        print(f"❌ File not found: {source_path}")
        return

    lines, start, end, code_context_lines = get_code_context_lines(source_path, line_num)
    code_context = "".join(code_context_lines)

    print(f"\n🔍 Error in {file_name}:{line_num} — {exception}")
    print("Calling Together AI...\n")

    try:
        ai_patch = call_together_ai(file_name, code_context, line_num, exception, message)
        print("✅ AI Suggestion:\n")
        print(ai_patch)
    except Exception as e:
        print("❌ Error from Together AI:", e)
        return

    print("\n🔧 Applying patch...")
    apply_patch(source_path, start, end, ai_patch)

if __name__ == "__main__":
    if not TOGETHER_API_KEY:
        print("❌ TOGETHER_API_KEY environment variable not set.")
    else:
        analyze_and_patch()