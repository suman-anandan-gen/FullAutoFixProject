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
    # Extract code between triple backticks
    code_blocks = re.findall(r"```(?:csharp)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if code_blocks:
        return code_blocks[0].strip()

    # Fallback: Keep only lines that resemble C# code
    lines = text.splitlines()
    code_lines = [line for line in lines if line.strip() and not line.strip().startswith("//") and not re.match(r'^[A-Za-z ]+:', line.strip())]
    return "\n".join(code_lines).strip()

def call_together_ai(file_path, code_context, error_line, exception, message):
    prompt = f"""
You're a senior C# engineer. A file `{file_path}` has an error at line {error_line}:

Exception: {exception}
Message: {message}

Here is the code context:

{code_context}

Please return ONLY the corrected code block — no explanation, no markdown, no headers, no comments. Just the fixed code lines that can be pasted directly.
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
    raw = response.json()["choices"][0]["message"]["content"].strip()
    return extract_code_block(raw)


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
    backup_dir = os.path.join(SOURCE_DIR, "backup")
    os.makedirs(backup_dir, exist_ok=True)

    # Backup file path is CourseApp/backup/<original_filename>
    backup_path = os.path.join(backup_dir, os.path.basename(file_path))
    with open(backup_path, "w") as f:
        f.writelines(lines)

    with open(backup_path, "w") as f:
        f.writelines(lines)
    updated = lines[:start] + replacement_lines + lines[end:]
    with open(file_path, "w") as f:
        f.writelines(updated)
    print(f"\n✅ Patch applied to {file_path}")
    print(f"📦 Backup saved to: {backup_path}")

def analyze_and_patch_all():
    if not os.path.exists(LOG_FILE):
        print(f"❌ Log file not found: {LOG_FILE}")
        return

    with open(LOG_FILE, "r") as f:
        lines = f.readlines()

    # Filter only error lines and remove duplicates
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

        lines, start, end, code_context_lines = get_code_context_lines(source_path, line_num)
        code_context = "".join(code_context_lines)

        print(f"\n🔍 [{index}/{len(error_lines)}] Analyzing {file_name}:{line_num} — {exception}")
        print(f"Message: {message}")
        print("Calling Together AI...\n")

        try:
            ai_patch = call_together_ai(file_name, code_context, line_num, exception, message)
            print("✅ AI Suggestion:\n")
            print(ai_patch)
            
            print("\n🔧 Applying patch...\n")
            apply_patch(source_path, start, end, ai_patch)
            
            # Ask for confirmation before applying patch
            # response = input("\n⚠️ Apply this patch? (y/n): ").lower().strip()
            # if response == 'y':
            #     print("\n🔧 Applying patch...")
            #     apply_patch(source_path, start, end, ai_patch)
            # else:
            #     print("\n⏭️ Skipping this patch...")
            
            print("\n" + "="*50 + "\n")
            
        except Exception as e:
            print(f"❌ Error from Together AI: {e}\n")

if __name__ == "__main__":
    if not TOGETHER_API_KEY:
        print("❌ TOGETHER_API_KEY environment variable not set.")
    else:
        analyze_and_patch_all()  # Changed from analyze_and_patch()