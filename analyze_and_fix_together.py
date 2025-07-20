import os
import re
import requests

# CONFIGURATION
SOURCE_DIR = "CourseApp"
LOG_FILE = os.path.join(SOURCE_DIR, "logs", "errors.log")
MAX_CONTEXT_LINES = 10

TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
MODEL_NAME = "deepseek-coder-33b-instruct"

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

```
{code_context}
```

Please return the fixed version of this block. Don't explain anything — just return the corrected code.
"""
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that fixes C# code bugs."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 512,
        "stop": None
    }

    response = requests.post(TOGETHER_API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]

def parse_log_line(line):
    match = re.match(
        r'\[ERROR\] \[(.*?)\] \[(.*?):(\d+)\] (\w+): (.*)',
        line
    )
    if match:
        _, file_name, line_num, ex_type, message = match.groups()
        return file_name, int(line_num), ex_type, message
    return None

def get_code_context(file_path, error_line, context_lines=MAX_CONTEXT_LINES):
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
            start = max(0, error_line - context_lines // 2 - 1)
            end = min(len(lines), error_line + context_lines // 2)
            return "".join(lines[start:end])
    except FileNotFoundError:
        return ""

def analyze_latest_error():
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()

    last_error = lines[-1].strip()
    result = parse_log_line(last_error)

    if not result:
        print("No valid log entry found.")
        return

    file_name, line_num, exception, message = result
    source_path = os.path.join(SOURCE_DIR, file_name)

    if not os.path.exists(source_path):
        print(f"Source file not found: {source_path}")
        return

    context = get_code_context(source_path, line_num)

    print(f"\n🔍 Analyzing {file_name}:{line_num} — {exception}")
    print("Querying Together AI...\n")

    suggestion = call_together_ai(file_name, context, line_num, exception, message)
    print("✅ AI Suggestion:\n")
    print(suggestion)

if __name__ == "__main__":
    if not TOGETHER_API_KEY:
        print("❌ TOGETHER_API_KEY is not set in environment.")
    else:
        analyze_latest_error()
